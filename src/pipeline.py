"""
Leakage-safe training and cross-dataset evaluation.

Order of operations, which is the whole point of this module:

    de-duplicate  ->  split  ->  fit scaler on SOURCE-TRAIN ONLY  ->  transform everything

De-duplication happens in `data.load`, before any split, so an exact duplicate flow can
never straddle train and test. The scaler never observes the source test set or any
target dataset. Class imbalance is handled with balanced sample weights, not resampling:
SMOTE applied before a split leaks synthetic neighbours across it.

One source is fitted once per (model, seed) and then evaluated against every target, so
the transfer matrix costs 4 sources x 4 models x 5 seeds of fitting rather than one fit
per ordered pair.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer
from sklearn.utils.class_weight import compute_sample_weight

import lightgbm as lgb
import xgboost as xgb

from src.config import SAMPLE_N_PER_CLASS, SEED, TEST_SIZE
from src.data import load
from src.metrics import binary_metrics, best_threshold

# --------------------------------------------------------------------------- models


def make_models(seed: int) -> dict[str, object]:
    """The four classifiers, fixed seeds, no tuning on target data."""
    return {
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05, num_leaves=64,
            subsample=0.8, colsample_bytree=0.8,
            random_state=seed, n_jobs=-1, verbose=-1),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=8,
            subsample=0.8, colsample_bytree=0.8, tree_method="hist",
            eval_metric="logloss", random_state=seed, n_jobs=-1, verbosity=0),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, n_jobs=-1, random_state=seed),
        "LogisticRegression": LogisticRegression(
            max_iter=2000, random_state=seed, n_jobs=-1),
    }


def make_scaler(kind: str, seed: int):
    """
    MinMax is what this literature uses. Quantile is the alternative the paper tests:
    CICFlowMeter and NetFlow rate features are heavy-tailed, and a MinMax fit to one
    testbed's maximum throughput maps another testbed's traffic into a sliver of [0,1].
    """
    if kind == "minmax":
        return MinMaxScaler()
    if kind == "quantile":
        return QuantileTransformer(
            n_quantiles=1000, output_distribution="uniform",
            subsample=200_000, random_state=seed)
    raise ValueError(f"unknown scaler {kind!r}")


# ----------------------------------------------------------------------------- data


@dataclass
class Domain:
    """One dataset, loaded once and reused across seeds."""

    key: str
    X: pd.DataFrame
    y: np.ndarray
    fam: np.ndarray
    report: dict = field(default_factory=dict)


_CACHE: dict[tuple[str, str], Domain] = {}

#: Ceiling on rows held per class in the in-memory cache.
#:
#: The transfer matrix needs all four domains resident at once. Caching them at full
#: size needs more than this machine's 15.6 GB, and Windows pages the process out rather
#: than failing, so a run appears alive while crawling at 23% CPU. The ceiling is 5x the
#: largest per-class sample any experiment draws, so it never binds on the experiments
#: themselves; the reservoir below is stratified and seeded, so it is reproducible.
#: Full-data confirmation runs pass cache_cap=None explicitly.
CACHE_CAP_PER_CLASS = 1_000_000


#: Free-memory floor, in GB. Below this the domain cache is evicted before loading
#: anything further.
#:
#: This machine has 15.6 GB and has twice died mid-run with the cache resident and free
#: memory around 2 GB. Evicting is safe rather than merely expedient: the cache is a speed
#: optimisation, and reloading is deterministic because the reservoir is seeded, so an
#: evicted domain reloads to exactly the same rows. The cost of being wrong is ~50s of
#: reloading; the cost of not doing it is losing the run and the machine.
MIN_FREE_GB = 3.0


def _free_gb() -> float:
    """Free physical memory in GB; returns inf if it cannot be determined."""
    try:
        import psutil

        return psutil.virtual_memory().available / 1e9
    except Exception:
        return float("inf")


def evict_domains() -> None:
    """Drop every cached domain and collect."""
    import gc

    n = len(_CACHE)
    _CACHE.clear()
    gc.collect()
    if n:
        print(f"  [mem] evicted {n} cached domain(s), free now {_free_gb():.1f} GB",
              flush=True)


def get_domain(key: str, other_policy: str = "drop",
               cache_cap: int | None = CACHE_CAP_PER_CLASS) -> Domain:
    """Load and cache a dataset. Loading NF-CSE-CIC-IDS2018 costs ~50s; do it once."""
    ck = (key, other_policy)
    if ck not in _CACHE and _free_gb() < MIN_FREE_GB:
        evict_domains()
    if ck not in _CACHE:
        X, y, fam, report = load(key, other_policy=other_policy, dedup=True)
        y_arr, fam_arr = y.to_numpy(), fam.to_numpy()
        rep = report.to_dict()

        if cache_cap is not None:
            X, y_arr, fam_arr = stratified_cap(X, y_arr, fam_arr, cache_cap, seed=0)
            rep["cache_cap_per_class"] = cache_cap
            rep["rows_cached"] = len(X)

        # float32 throughout: several NetFlow columns arrive as int64, and the cache must
        # hold four domains at once.
        X = X.astype(np.float32).reset_index(drop=True)
        _CACHE[ck] = Domain(key, X, y_arr, fam_arr, rep)
    return _CACHE[ck]


def stratified_cap(
    X: pd.DataFrame, y: np.ndarray, fam: np.ndarray,
    n_per_class: int | None, seed: int,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Cap each class at `n_per_class` rows.

    A memory guard, not a class-balancing step: capping the majority class changes the
    base rate, so every run records the cap and the resulting balance, and the paper
    reports operating-point metrics that do not silently depend on it.
    """
    if n_per_class is None:
        return X, y, fam
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for cls in np.unique(y):
        idx = np.flatnonzero(y == cls)
        if len(idx) > n_per_class:
            idx = rng.choice(idx, n_per_class, replace=False)
        keep.append(idx)
    sel = np.sort(np.concatenate(keep))
    return X.iloc[sel], y[sel], fam[sel]


# ------------------------------------------------------------------------- fit / eval


@dataclass
class SourceFit:
    """A model trained on one source domain, plus everything needed to apply it."""

    source: str
    model_name: str
    seed: int
    model: object
    scaler: object
    features: list[str]
    threshold: float                 # tuned on the SOURCE test split only
    indomain: dict[str, float]
    y_test: np.ndarray
    proba_test: np.ndarray
    fam_test: np.ndarray
    train_seconds: float
    n_train: int
    n_test: int


def fit_source(
    source: str,
    model_name: str,
    seed: int = SEED,
    features: list[str] | None = None,
    scaler_kind: str = "minmax",
    n_per_class: int | None = SAMPLE_N_PER_CLASS,
    other_policy: str = "drop",
    label_mode: str = "normal",
) -> SourceFit:
    """
    Train one model on one source domain and score its held-out source test split.

    `label_mode` alters only the **training** labels, for the controls in §4.3:
        ``normal``    as labelled
        ``permuted``  training labels shuffled, destroying the relationship. A correct
                      pipeline must then land at chance externally with no systematic sign;
                      anything else would mean the pipeline itself manufactures below-chance
                      results.
        ``reversed``  training labels inverted. External AUC should mirror the normal run
                      about 0.5, confirming the sign is carried by the learned relationship.
    Test and target labels are never altered.
    """
    dom = get_domain(source, other_policy)
    X, y, fam = stratified_cap(dom.X, dom.y, dom.fam, n_per_class, seed)
    if features is not None:
        X = X[features]
    feats = list(X.columns)

    X_tr, X_te, y_tr, y_te, _f_tr, f_te = train_test_split(
        X, y, fam, test_size=TEST_SIZE, random_state=seed, stratify=y)

    # Fitted on source-train only. This is the line that makes the whole study honest.
    scaler = make_scaler(scaler_kind, seed).fit(X_tr)
    X_tr_s = pd.DataFrame(scaler.transform(X_tr), columns=feats)
    X_te_s = pd.DataFrame(scaler.transform(X_te), columns=feats)

    # Median imputation, also learned on source-train only.
    med = X_tr_s.median()
    X_tr_s = X_tr_s.fillna(med)
    X_te_s = X_te_s.fillna(med)

    if label_mode == "permuted":
        y_tr = np.random.default_rng(seed).permutation(y_tr)
    elif label_mode == "reversed":
        y_tr = 1 - y_tr
    elif label_mode != "normal":
        raise ValueError(f"label_mode must be normal|permuted|reversed, got {label_mode!r}")

    model = make_models(seed)[model_name]
    t0 = time.perf_counter()
    model.fit(X_tr_s, y_tr, sample_weight=compute_sample_weight("balanced", y_tr))
    train_seconds = time.perf_counter() - t0

    proba = model.predict_proba(X_te_s)[:, 1]
    thr = best_threshold(y_te, proba)
    indomain = binary_metrics(y_te, proba >= thr, proba)

    fit = SourceFit(
        source=source, model_name=model_name, seed=seed, model=model, scaler=scaler,
        features=feats, threshold=thr, indomain=indomain,
        y_test=y_te, proba_test=proba, fam_test=f_te,
        train_seconds=train_seconds, n_train=len(X_tr), n_test=len(X_te),
    )
    fit._median = med  # type: ignore[attr-defined]
    return fit


def apply_to(
    fit: SourceFit,
    target: str,
    n_per_class: int | None = SAMPLE_N_PER_CLASS,
    other_policy: str = "drop",
    clip: bool = True,
) -> dict:
    """
    Apply a source-trained model to a target domain.

    `clip` bounds scaled target features to the range the scaler saw. Rate features blow
    up on near-zero-duration flows (Engelen et al., 2021) and land far outside [0,1],
    which dominates linear models. Clipping is standard external-validation practice and
    is ablated rather than assumed.
    """
    dom = get_domain(target, other_policy)
    X, y, fam = stratified_cap(dom.X, dom.y, dom.fam, n_per_class, fit.seed)
    X = X[fit.features]

    Xs = pd.DataFrame(fit.scaler.transform(X), columns=fit.features)
    n_out = int(((Xs < 0) | (Xs > 1)).to_numpy().any(axis=1).sum()) if clip else 0
    if clip:
        Xs = Xs.clip(lower=0.0, upper=1.0)
    Xs = Xs.fillna(fit._median)  # type: ignore[attr-defined]

    proba = fit.model.predict_proba(Xs)[:, 1]
    ext = binary_metrics(y, proba >= fit.threshold, proba)

    return {
        "source": fit.source, "target": target, "model": fit.model_name, "seed": fit.seed,
        "n_target": len(y), "target_base_rate": float((y == 1).mean()),
        "rows_outside_train_range": n_out,
        "clip": clip,
        "external": ext,
        "y": y, "proba": proba, "fam": fam,
    }


def _self_check() -> None:
    """Assert the leakage guarantees hold on synthetic data with a known answer."""
    rng = np.random.default_rng(0)
    n = 2000
    X = pd.DataFrame(rng.normal(size=(n, 4)), columns=list("abcd"))
    y = (X["a"] + rng.normal(0, 0.3, n) > 0).astype(int).to_numpy()
    fam = np.where(y == 1, "volumetric", "benign")

    X_tr, X_te = X.iloc[:1600], X.iloc[1600:]
    sc = make_scaler("minmax", 0).fit(X_tr)
    # A scaler fitted on train alone must map train into [0,1] exactly, and is free to
    # map unseen test rows outside it. If test rows never exceed the range, the scaler
    # saw them.
    assert sc.transform(X_tr).min() >= -1e-9 and sc.transform(X_tr).max() <= 1 + 1e-9
    assert (sc.transform(X_te) > 1).any() or (sc.transform(X_te) < 0).any()

    Xc, yc, fc = stratified_cap(X, y, fam, 100, seed=0)
    assert (yc == 0).sum() <= 100 and (yc == 1).sum() <= 100
    assert len(Xc) == len(yc) == len(fc)
    print("pipeline self-check passed")


if __name__ == "__main__":
    _self_check()
