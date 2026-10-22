"""
Shared helpers for P-1 (Phases 2-4), written to stay inside a small RAM budget.

This machine (16 GB, ~1.5 GB free under load) cannot afford src.pipeline.get_domain, which
reads a whole 17-30M-row parquet into pandas before capping (a 6-8 GB spike). So data loading
here streams the parquet with pyarrow ``iter_batches`` (columns-only, two-pass Bernoulli
downsample per class), keeping the peak to one ~100 MB batch. The *ML* logic is unchanged and
still comes from src: ``make_models``, ``make_scaler`` (MinMax), ``best_threshold``,
``binary_metrics``, and the exact fit_source order (dedup within the sample -> split -> scale
on train only -> median-fill -> balanced weights). Ledgered as a memory deviation in STATUS.md.
"""

from __future__ import annotations

import glob
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sklearn.model_selection import train_test_split  # noqa: E402

from src.config import DATASETS, TEST_SIZE  # noqa: E402
from src.data import family_of, label_of  # noqa: E402
from src.metrics import best_threshold, binary_metrics  # noqa: E402
from src.pipeline import make_models, make_scaler  # noqa: E402
import constraints as C  # noqa: E402

FEATURES = C.FEATURES
CAP_PER_CLASS = 200_000      # full frozen spec (pilot used 50_000)
_BATCH = 300_000


def _parquet_path(key: str) -> str:
    return glob.glob(str(DATASETS[key].path / "**" / "*.parquet"), recursive=True)[0]


def _label_lut(f: str, label_col: str) -> tuple[dict, dict]:
    """Map every distinct textual label to its binary class and family (small vocab)."""
    uniq: set[str] = set()
    for b in pq.ParquetFile(f).iter_batches(batch_size=_BATCH, columns=[label_col]):
        uniq.update(str(v) for v in pd.unique(b.to_pandas()[label_col]))
    return {v: label_of(v) for v in uniq}, {v: family_of(v) for v in uniq}


def read_capped(key: str, cap_benign: int, cap_attack: int, seed: int,
                family: str | None = None) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Memory-bounded load of benign + DoS flows from one dataset.

    `family=None` keeps every DoS/DDoS flow (label==1); a family name keeps only that family.
    Two passes: pass 1 counts the qualifying rows per class (streaming the label column only);
    pass 2 keeps each qualifying row with probability cap/count, so the result is ~cap per class
    and unbiased. Dedup (exact, in feature space) is applied to the small accumulated sample.
    """
    f = _parquet_path(key)
    label_col = DATASETS[key].label_col
    cls_lut, fam_lut = _label_lut(f, label_col)
    rng = np.random.default_rng(seed)

    def qualifies(label: str) -> int:
        """0 benign keep-for-benign, 1 attack keep-for-attack, -1 drop."""
        c = cls_lut[label]
        if c == 0:
            return 0
        if c == 1 and (family is None or fam_lut[label] == family):
            return 1
        return -1

    # pass 1: counts
    n_b = n_a = 0
    for b in pq.ParquetFile(f).iter_batches(batch_size=_BATCH, columns=[label_col]):
        lab = b.to_pandas()[label_col].astype(str).to_numpy()
        q = np.array([qualifies(x) for x in lab])
        n_b += int((q == 0).sum())
        n_a += int((q == 1).sum())
    p_b = min(1.0, cap_benign / max(n_b, 1))
    p_a = min(1.0, cap_attack / max(n_a, 1))

    # pass 2: Bernoulli keep
    cols = FEATURES + [label_col]
    Xs, ys, fs = [], [], []
    for b in pq.ParquetFile(f).iter_batches(batch_size=_BATCH, columns=cols):
        df = b.to_pandas()
        lab = df[label_col].astype(str).to_numpy()
        q = np.array([qualifies(x) for x in lab])
        keep = np.zeros(len(df), dtype=bool)
        u = rng.random(len(df))
        keep |= (q == 0) & (u < p_b)
        keep |= (q == 1) & (u < p_a)
        if keep.any():
            sub = df.loc[keep]
            Xs.append(sub[FEATURES].to_numpy(dtype=np.float32))
            ys.append(np.where(q[keep] == 1, 1, 0).astype(np.int8))
            fs.append(np.array([fam_lut[x] for x in lab[keep]], dtype=object))

    X = np.vstack(Xs) if Xs else np.empty((0, len(FEATURES)), np.float32)
    y = np.concatenate(ys) if ys else np.empty(0, np.int8)
    fam = np.concatenate(fs) if fs else np.empty(0, object)

    # Sanitise non-finite rate features exactly as src.data.load does: the per-second rate
    # columns divide bytes by near-zero durations and overflow float32 to +/-inf. Set them to
    # NaN so the downstream median-fill handles them; leaving inf poisons scaler/median/model.
    if len(X):
        X[~np.isfinite(X)] = np.nan

    # exact dedup in feature space (cheap on the small sample); drops leakage-prone repeats
    if len(X):
        Xdf = pd.DataFrame(X, columns=FEATURES)
        dup = Xdf.duplicated(keep="first").to_numpy()
        X, y, fam = X[~dup], y[~dup], fam[~dup]
    return pd.DataFrame(X, columns=FEATURES), y, fam


@dataclass
class FitObj:
    """Minimal source-trained detector; carries exactly what score_flows / apply need."""

    source: str
    model_name: str
    seed: int
    model: object
    scaler: object
    features: list[str]
    threshold: float
    indomain: dict
    _median: pd.Series = field(repr=False, default=None)


@dataclass
class Fit:
    fit: FitObj
    srcval_X: np.ndarray
    srcval_proba: np.ndarray
    srcval_y: np.ndarray
    source_acc: float


_SRC_CACHE: dict[tuple[str, int, int], tuple[pd.DataFrame, np.ndarray]] = {}


def _source_sample(source: str, seed: int, cap: int):
    """Capped source sample, cached per (source, seed) so both models reuse one stream."""
    key = (source, seed, cap)
    if key not in _SRC_CACHE:
        if len(_SRC_CACHE) > 2:          # keep the cache tiny
            _SRC_CACHE.clear()
        Xdf, y, _fam = read_capped(source, cap_benign=cap, cap_attack=cap, seed=seed, family=None)
        _SRC_CACHE[key] = (Xdf, y)
    return _SRC_CACHE[key]


def build_fit(source: str, model_name: str, seed: int, cap: int = CAP_PER_CLASS) -> Fit:
    """Leakage-safe train on a capped source sample, mirroring src.pipeline.fit_source."""
    Xdf, y = _source_sample(source, seed, cap)
    X = Xdf[FEATURES]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=seed, stratify=y)

    scaler = make_scaler("minmax", seed).fit(X_tr)
    X_tr_s = pd.DataFrame(scaler.transform(X_tr), columns=FEATURES)
    X_te_s = pd.DataFrame(scaler.transform(X_te), columns=FEATURES)
    med = X_tr_s.median()
    X_tr_s = X_tr_s.fillna(med)
    X_te_s = X_te_s.fillna(med)

    from sklearn.utils.class_weight import compute_sample_weight
    model = make_models(seed)[model_name]
    model.fit(X_tr_s, y_tr, sample_weight=compute_sample_weight("balanced", y_tr))

    proba = model.predict_proba(X_te_s)[:, 1]
    thr = best_threshold(y_te, proba)
    indomain = binary_metrics(y_te, proba >= thr, proba)

    fit = FitObj(source=source, model_name=model_name, seed=seed, model=model, scaler=scaler,
                 features=FEATURES, threshold=float(thr), indomain=indomain, _median=med)
    return Fit(fit=fit, srcval_X=X_te.to_numpy(dtype=np.float64),
               srcval_proba=proba, srcval_y=y_te, source_acc=float(indomain["accuracy"]))


def score_flows(fit: FitObj, X_raw: np.ndarray) -> np.ndarray:
    """P(attack) for raw flows, via the identical transform path as src.pipeline.apply_to."""
    X = pd.DataFrame(np.atleast_2d(X_raw).astype(np.float64), columns=FEATURES)
    Xs = pd.DataFrame(fit.scaler.transform(X[fit.features]), columns=fit.features)
    Xs = Xs.clip(lower=0.0, upper=1.0).fillna(fit._median)
    return fit.model.predict_proba(Xs)[:, 1]


def external_metrics(fit: FitObj, X_raw: np.ndarray, y: np.ndarray) -> dict:
    proba = score_flows(fit, X_raw)
    return binary_metrics(y, proba >= fit.threshold, proba), proba
