"""
Loading, harmonisation and labelling.

Two dataset families are handled:

* **netflow_v2** — the Sarhan et al. (2021) quartet. All four ship the *same* 43 columns,
  so the shared feature space is a published standard rather than an artefact of
  intersecting column names. This is the primary study.
* **cicflowmeter** — CIC-DDoS2019 / CICIDS2017 / DistriNet-corrected CICIDS2017. Column
  names drift between releases (leading spaces, a duplicated `Fwd Header Length.1`), so
  these need real harmonisation. Kept as the secondary study.

Labelling policy, stated once here and reported in the paper:

* positive class = any DoS or DDoS flow;
* negative class = benign;
* attacks that are neither DoS nor DDoS (Exploits, Fuzzers, PortScan, ...) are
  **not silently discarded**. `other_policy` makes the choice explicit and every mode
  records how many rows it moved, because dropping them changes the base rate and the
  base rate drives precision.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    BENIGN_LABELS,
    DATASETS,
    FAMILY_PATTERNS,
    FAMILY_PRECEDENCE,
    LEAKY_COLS,
    Dataset,
)

# Labels that mark a DoS/DDoS flow. Longest-first matching, applied to the lowercased
# label string. Anything unmatched is reported, never bucketed by accident.
DDOS_MARKERS: tuple[str, ...] = tuple(
    sorted({m for pats in FAMILY_PATTERNS.values() for m in pats}, key=len, reverse=True)
)

BENIGN = 0
DDOS = 1
OTHER_ATTACK = -1


@dataclass
class LoadReport:
    """Everything a reviewer needs to reconstruct what this loader did."""

    key: str
    rows_raw: int = 0
    rows_out: int = 0
    n_features: int = 0
    dropped_leaky: list[str] = field(default_factory=list)
    label_map: dict[str, int] = field(default_factory=dict)
    family_map: dict[str, str] = field(default_factory=dict)
    class_counts: dict[str, int] = field(default_factory=dict)
    other_attack_rows: int = 0
    other_policy: str = ""
    n_duplicates: int = 0
    duplicate_fraction: float = 0.0
    n_contradictory_groups: int = 0
    n_inf_coerced: int = 0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# ------------------------------------------------------------------------- labelling


def family_of(label: str) -> str:
    """
    Attack family for one raw label. 'benign' for benign, 'other' for non-DoS attacks.

    The longest matching pattern across *all* families wins; ties break on
    FAMILY_PRECEDENCE. A first-family-wins rule would misfile "DoS slowloris" as
    volumetric because "dos" matches before "slowloris" is ever tested.
    """
    low = str(label).strip().lower()
    if low in BENIGN_LABELS:
        return "benign"

    best: tuple[int, int, str] | None = None
    for fam, patterns in FAMILY_PATTERNS.items():
        rank = FAMILY_PRECEDENCE.index(fam)
        for pat in patterns:
            if pat in low:
                # longer pattern wins; on a tie, lower precedence rank wins
                cand = (len(pat), -rank, fam)
                if best is None or cand[:2] > best[:2]:
                    best = cand
    return best[2] if best else "other"


def label_of(label: str) -> int:
    """BENIGN / DDOS / OTHER_ATTACK for one raw label."""
    fam = family_of(label)
    if fam == "benign":
        return BENIGN
    return OTHER_ATTACK if fam == "other" else DDOS


def build_label_maps(labels: pd.Series) -> tuple[dict[str, int], dict[str, str]]:
    """Full raw-label -> class and raw-label -> family maps. Goes in the appendix."""
    vocab = sorted({str(v) for v in labels.unique()})
    return {v: label_of(v) for v in vocab}, {v: family_of(v) for v in vocab}


# ---------------------------------------------------------------------------- loading


def _read_parquet_dir(root: Path) -> pd.DataFrame:
    files = sorted(glob.glob(str(root / "**" / "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(
            f"No .parquet under {root}. Run: python scripts/download_data.py --only {root.name}"
        )
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _harmonize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Strip header whitespace, drop duplicated and identity-leaking columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    # CICIDS2017 ships a duplicated 'Fwd Header Length.1'.
    df = df.drop(columns=[c for c in df.columns if c.endswith(".1")], errors="ignore")
    label_cols = {"label", "attack", "class"}
    leaky = [c for c in df.columns if c.lower() in LEAKY_COLS and c.lower() not in label_cols]
    df = df.drop(columns=leaky, errors="ignore")
    return df, leaky


def _find_label_col(df: pd.DataFrame, preferred: str) -> str:
    for cand in (preferred, "Attack", "Label", "label", "Class", "class"):
        if cand in df.columns:
            return cand
    raise KeyError(f"No label column found; columns start with {list(df.columns)[:8]}")


def load(
    key: str,
    other_policy: str = "drop",
    dedup: bool = True,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, LoadReport]:
    """
    Load one dataset.

    Args:
        key: dataset key from `config.DATASETS`.
        other_policy: what to do with attacks that are neither DoS nor DDoS.
            ``"drop"``   remove them (the literature's usual choice; changes the base rate)
            ``"benign"`` treat them as negatives (tests false positives on other attacks)
            ``"keep"``   leave them labelled OTHER_ATTACK for the caller to handle
        dedup: drop exact duplicate feature rows. Duplicates straddling a split leak.

    Returns:
        ``(X, y, families, report)`` — features, binary target, attack family per row.
    """
    if other_policy not in {"drop", "benign", "keep"}:
        raise ValueError(f"other_policy must be drop|benign|keep, got {other_policy!r}")

    ds: Dataset = DATASETS[key]
    raw = _read_parquet_dir(ds.path)
    rep = LoadReport(key=key, rows_raw=len(raw), other_policy=other_policy)

    # The textual attack column carries the family; the numeric Label column does not.
    label_col = _find_label_col(raw, ds.label_col)

    # Resolve labels through the *vocabulary*, not row by row. These datasets have ~15
    # distinct labels across up to 18.9M rows, so `.astype(str).map(fn)` would build
    # millions of Python string objects and push the machine into swap. Categorical codes
    # plus a lookup table make it an O(n) numpy gather instead.
    labels_cat = raw[label_col].astype("category")
    vocab = [str(c) for c in labels_cat.cat.categories]
    rep.label_map = {v: label_of(v) for v in vocab}
    rep.family_map = {v: family_of(v) for v in vocab}

    codes = labels_cat.cat.codes.to_numpy()
    class_lut = np.array([rep.label_map[v] for v in vocab], dtype=np.int8)
    fam_lut = np.array(["other"] + [rep.family_map[v] for v in vocab], dtype=object)
    del labels_cat

    df, rep.dropped_leaky = _harmonize_columns(raw)
    del raw
    # Drop every label-ish column from the feature matrix.
    df = df.drop(columns=[c for c in ("Label", "label", "Attack", "Class", "class")
                          if c in df.columns], errors="ignore")

    X = df.select_dtypes(include=[np.number])
    del df

    # Count infinities column by column. Materialising the whole frame as float64 to call
    # np.isinf once needs ~5.9 GB on the 18.9M-row datasets and sends the machine to swap;
    # integer columns cannot hold an infinity at all, so they are skipped outright.
    n_inf = 0
    for col in X.columns:
        if X[col].dtype.kind == "f":
            n_inf += int(np.isinf(X[col].to_numpy(dtype=np.float64, na_value=np.nan)).sum())
    rep.n_inf_coerced = n_inf
    if n_inf:
        X = X.replace([np.inf, -np.inf], np.nan)

    # codes == -1 marks a NaN label; fam_lut is offset by one so that maps to "other".
    y = pd.Series(np.where(codes >= 0, class_lut[codes], OTHER_ATTACK), name="y")
    fam = pd.Series(fam_lut[codes + 1], name="family")
    rep.other_attack_rows = int((y == OTHER_ATTACK).sum())

    if other_policy == "drop":
        keep = y != OTHER_ATTACK
        X, y, fam = X[keep], y[keep], fam[keep]
    elif other_policy == "benign":
        y = y.replace(OTHER_ATTACK, BENIGN)

    if dedup:
        before = len(X)
        # Duplicates are measured in the feature space the model actually sees, i.e. after
        # socket columns are dropped. Two flows differing only in source port are one
        # example to a model that never sees the port, and letting such a pair straddle a
        # train/test split is leakage.
        # Hash rows once and work on 64-bit keys. drop_duplicates over an 18.9M x 39 frame
        # is minutes; hashing is seconds and gives the same counts.
        row_hash = pd.util.hash_pandas_object(X, index=False)
        dup_mask = row_hash.duplicated(keep="first")

        # Feature vectors that appear with more than one label are a data-quality defect,
        # not a nuisance: the Bayes error on those rows is nonzero by construction. Count
        # them, because this bounds every in-domain score reported later.
        n_groups = row_hash.nunique()
        n_groups_with_label = len(
            pd.DataFrame({"h": row_hash.to_numpy(), "y": y.to_numpy()}).drop_duplicates()
        )
        rep.n_contradictory_groups = int(n_groups_with_label - n_groups)

        X, y, fam = X[~dup_mask], y[~dup_mask], fam[~dup_mask]
        rep.n_duplicates = before - len(X)
        rep.duplicate_fraction = round(rep.n_duplicates / max(before, 1), 4)

    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    fam = fam.reset_index(drop=True)

    rep.rows_out = len(X)
    rep.n_features = X.shape[1]
    rep.class_counts = {
        "benign": int((y == BENIGN).sum()),
        "ddos": int((y == DDOS).sum()),
        "other_attack": int((y == OTHER_ATTACK).sum()),
    }
    return X, y, fam, rep


# ------------------------------------------------------------------- shared features


def netflow_common_features(keys: list[str] | None = None) -> list[str]:
    """
    The shared NetFlow v2 feature space, asserted identical across the quartet.

    Sarhan et al. built these datasets so this assertion holds; checking it is how the
    paper earns the right to claim its transfer results are not a harmonisation artefact.
    """
    from src.config import NETFLOW_V2

    keys = keys or [d.key for d in NETFLOW_V2]
    per_key: dict[str, set[str]] = {}
    for k in keys:
        raw = _read_parquet_dir(DATASETS[k].path).head(1)
        cols, _ = _harmonize_columns(raw)
        cols = cols.drop(columns=[c for c in ("Label", "Attack") if c in cols.columns],
                         errors="ignore")
        per_key[k] = set(cols.select_dtypes(include=[np.number]).columns)

    shared = set.intersection(*per_key.values())
    union = set.union(*per_key.values())
    if shared != union:
        raise AssertionError(
            "NetFlow v2 feature spaces are not identical across datasets; "
            f"asymmetric columns: {sorted(union - shared)}"
        )
    return sorted(shared)
