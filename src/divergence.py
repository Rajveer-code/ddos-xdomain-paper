"""
Label-free divergence measures between a source and a target domain.

Every quantity here is computable by an operator who has traffic from their own network
but no attack labels for it. That constraint is the point: if one of these predicts how
much performance a detector will lose, it becomes a pre-deployment check rather than a
post-mortem.

Measures fall into two groups:

*Distribution-based* — how far apart the two feature distributions are, ignoring the
model entirely: proxy A-distance, summed Wasserstein-1, MMD.

*Model-based* — what the trained detector's own outputs say about the target, without
consulting labels: mean confidence, and Average Thresholded Confidence (Garg et al.,
2022), which estimates target accuracy from the source-calibrated score distribution.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_predict


def proxy_a_distance(Xs: pd.DataFrame, Xt: pd.DataFrame, seed: int = 42,
                     n_max: int = 20_000) -> dict[str, float]:
    """
    Proxy A-distance: train a discriminator to tell source from target.

    d_A = 2(1 - 2*err). A discriminator that cannot separate the domains (err -> 0.5)
    gives d_A -> 0; a perfectly separable pair gives d_A -> 2. Error is taken from
    cross-validated predictions so it reflects generalisation, not memorisation.
    """
    rng = np.random.default_rng(seed)
    cols = list(Xs.columns)
    a = Xs.to_numpy(dtype=np.float32, na_value=np.nan)
    b = Xt[cols].to_numpy(dtype=np.float32, na_value=np.nan)
    if len(a) > n_max:
        a = a[rng.choice(len(a), n_max, replace=False)]
    if len(b) > n_max:
        b = b[rng.choice(len(b), n_max, replace=False)]

    X = np.vstack([a, b])
    y = np.concatenate([np.zeros(len(a), dtype=np.int8), np.ones(len(b), dtype=np.int8)])
    clf = HistGradientBoostingClassifier(max_iter=150, random_state=seed)
    pred = cross_val_predict(clf, X, y, cv=3, n_jobs=-1)
    err = float((pred != y).mean())
    return {"domain_clf_error": err, "proxy_a_distance": float(2 * (1 - 2 * err))}


def feature_wasserstein(Xs: pd.DataFrame, Xt: pd.DataFrame,
                        n_max: int = 50_000, seed: int = 42) -> dict[str, float]:
    """
    Per-feature Wasserstein-1 on rank-normalised marginals, summed and averaged.

    Features are mapped to their source quantiles first so the distance is unitless and
    a throughput column measured in bytes/s cannot dominate a TTL column by scale alone.
    """
    rng = np.random.default_rng(seed)
    cols = list(Xs.columns)
    s = Xs
    t = Xt[cols]
    if len(s) > n_max:
        s = s.iloc[rng.choice(len(s), n_max, replace=False)]
    if len(t) > n_max:
        t = t.iloc[rng.choice(len(t), n_max, replace=False)]

    per: dict[str, float] = {}
    for c in cols:
        a = s[c].to_numpy(dtype=np.float64, na_value=np.nan)
        b = t[c].to_numpy(dtype=np.float64, na_value=np.nan)
        a = a[np.isfinite(a)]
        b = b[np.isfinite(b)]
        if len(a) < 2 or len(b) < 2:
            per[c] = 0.0
            continue
        # Rank-normalise both against the source's empirical CDF.
        lo, hi = np.nanpercentile(a, [0.5, 99.5])
        rng_span = max(hi - lo, 1e-9)
        per[c] = float(wasserstein_distance(
            np.clip((a - lo) / rng_span, -1, 2), np.clip((b - lo) / rng_span, -1, 2)))

    vals = np.array(list(per.values()))
    return {
        "wasserstein_sum": float(vals.sum()),
        "wasserstein_mean": float(vals.mean()),
        "wasserstein_max": float(vals.max()),
        "per_feature": per,
    }


def mmd_rbf(Xs: pd.DataFrame, Xt: pd.DataFrame, n_max: int = 4000,
            seed: int = 42) -> float:
    """Unbiased MMD^2 with an RBF kernel; bandwidth from the median heuristic."""
    rng = np.random.default_rng(seed)
    cols = list(Xs.columns)
    a = np.nan_to_num(Xs.to_numpy(dtype=np.float64, na_value=0.0))
    b = np.nan_to_num(Xt[cols].to_numpy(dtype=np.float64, na_value=0.0))
    if len(a) > n_max:
        a = a[rng.choice(len(a), n_max, replace=False)]
    if len(b) > n_max:
        b = b[rng.choice(len(b), n_max, replace=False)]

    def sq(u, v):
        return np.maximum(
            (u * u).sum(1)[:, None] + (v * v).sum(1)[None, :] - 2 * u @ v.T, 0.0)

    d_ab = sq(a, b)
    med = np.median(d_ab)
    gamma = 1.0 / max(med, 1e-9)
    k = lambda d: np.exp(-gamma * d)

    n, m = len(a), len(b)
    kaa, kbb = k(sq(a, a)), k(sq(b, b))
    np.fill_diagonal(kaa, 0.0)
    np.fill_diagonal(kbb, 0.0)
    return float(
        kaa.sum() / (n * (n - 1)) + kbb.sum() / (m * (m - 1)) - 2 * k(d_ab).mean()
    )


def confidence_scores(proba_source: np.ndarray, proba_target: np.ndarray,
                      acc_source: float) -> dict[str, float]:
    """
    Model-based, label-free signals.

    ``mean_confidence_drop`` is the fall in mean max-probability from source to target;
    an overconfident model on shifted data shows little drop, which is itself diagnostic.

    ``atc_estimated_accuracy`` implements Average Thresholded Confidence (Garg et al.,
    2022): pick the confidence threshold at which the source's *own* fraction of
    below-threshold points equals its error rate, then apply that threshold to the target.
    The fraction of target points above it estimates target accuracy with no target labels.
    """
    cs = np.maximum(proba_source, 1 - proba_source)
    ct = np.maximum(proba_target, 1 - proba_target)
    q = float(np.quantile(cs, np.clip(1.0 - acc_source, 0.0, 1.0)))
    return {
        "mean_confidence_source": float(cs.mean()),
        "mean_confidence_target": float(ct.mean()),
        "mean_confidence_drop": float(cs.mean() - ct.mean()),
        "atc_threshold": q,
        "atc_estimated_accuracy": float((ct >= q).mean()),
    }


def _self_check() -> None:
    rng = np.random.default_rng(0)
    cols = [f"f{i}" for i in range(6)]
    A = pd.DataFrame(rng.normal(0, 1, (3000, 6)), columns=cols)
    same = pd.DataFrame(rng.normal(0, 1, (3000, 6)), columns=cols)
    far = pd.DataFrame(rng.normal(6, 1, (3000, 6)), columns=cols)

    d_same = proxy_a_distance(A, same, n_max=3000)["proxy_a_distance"]
    d_far = proxy_a_distance(A, far, n_max=3000)["proxy_a_distance"]
    assert d_same < 0.5 < d_far, f"A-distance failed to order domains: {d_same} vs {d_far}"

    w_same = feature_wasserstein(A, same)["wasserstein_sum"]
    w_far = feature_wasserstein(A, far)["wasserstein_sum"]
    assert w_same < w_far, "Wasserstein failed to order domains"

    m_same = mmd_rbf(A, same, n_max=1500)
    m_far = mmd_rbf(A, far, n_max=1500)
    assert m_same < m_far, "MMD failed to order domains"

    # ATC on a well-calibrated source should recover roughly the source accuracy.
    p = rng.random(5000)
    c = confidence_scores(p, p, acc_source=0.9)
    assert 0.8 < c["atc_estimated_accuracy"] < 1.0

    print(f"divergence self-check passed  (d_A same={d_same:.3f} far={d_far:.3f}, "
          f"W same={w_same:.3f} far={w_far:.3f}, MMD same={m_same:.4f} far={m_far:.4f})")


if __name__ == "__main__":
    _self_check()
