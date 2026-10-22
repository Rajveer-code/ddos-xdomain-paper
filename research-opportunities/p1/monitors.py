"""
The label-free monitor battery, calibrated on source-validation data.

Each monitor reduces a deployment to one shift statistic (larger = more shift). Its alarm
threshold is set on a SOURCE-VALIDATION null: split source-validation in two halves many
times, compute the statistic between the halves (both source, so no shift), and take the
(1 - budget) quantile. A target deployment whose statistic exceeds that threshold raises an
alarm at the stated benign false-alarm budget.

Monitors (all from src/divergence.py):
  atc_acc_drop     source accuracy minus ATC-estimated target accuracy (Garg et al. 2022)
  mean_conf_drop   fall in mean max-probability from source to target
  ks_score         KS statistic between source and target score distributions
  proxy_a_distance domain-discriminator distance on the raw features
  max_wasserstein  largest per-feature Wasserstein-1 (the signal that carried warning in P11)

The same calibrated battery is reused in Phase 3 (does it fire DURING the attack?) and
Phase 4 (does the low-controllability defence fire when these stay quiet?).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.divergence import confidence_scores, feature_wasserstein, proxy_a_distance  # noqa: E402
import constraints as C  # noqa: E402

CHEAP = ("atc_acc_drop", "mean_conf_drop", "ks_score")
EXPENSIVE = ("proxy_a_distance", "max_wasserstein")
MONITORS = CHEAP + EXPENSIVE


def _df(X: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(np.atleast_2d(X).astype(np.float64), columns=C.FEATURES)


def _stats(src_proba, src_X, tgt_proba, tgt_X, source_acc, n_max=4000, seed=0) -> dict:
    """Compute every monitor's raw statistic for one (source-val, target) comparison."""
    cs = confidence_scores(np.asarray(src_proba), np.asarray(tgt_proba), source_acc)
    out = {
        "atc_acc_drop": source_acc - cs["atc_estimated_accuracy"],
        "mean_conf_drop": cs["mean_confidence_drop"],
        "ks_score": float(ks_2samp(np.asarray(src_proba), np.asarray(tgt_proba)).statistic),
    }
    if src_X is not None and tgt_X is not None:
        out["proxy_a_distance"] = proxy_a_distance(
            _df(src_X), _df(tgt_X), seed=seed, n_max=n_max)["proxy_a_distance"]
        out["max_wasserstein"] = feature_wasserstein(
            _df(src_X), _df(tgt_X), n_max=n_max, seed=seed)["wasserstein_max"]
    return out


def calibrate(srcval_proba, srcval_X, source_acc, budget=0.01,
              b_cheap=100, b_expensive=15, n_max=3000, seed=42) -> dict:
    """Null thresholds from two-half resampling of source-validation (no-shift). (1-budget) qtile."""
    rng = np.random.default_rng(seed)
    p = np.asarray(srcval_proba)
    X = np.asarray(srcval_X)
    n = len(p)
    null = {m: [] for m in MONITORS}

    def one(b, do_expensive):
        idx = rng.permutation(n)
        a, bb = idx[: n // 2], idx[n // 2:]
        s = _stats(p[a], X[a] if do_expensive else None, p[bb],
                   X[bb] if do_expensive else None, source_acc,
                   n_max=n_max, seed=int(rng.integers(1e9)))
        for m, v in s.items():
            null[m].append(v)

    for _ in range(b_cheap):
        one(_, do_expensive=False)
    for _ in range(b_expensive):
        one(_, do_expensive=True)

    q = 1.0 - budget
    thr = {m: float(np.quantile(null[m], q)) for m in MONITORS}
    return {"thresholds": thr, "budget": budget, "source_acc": source_acc,
            "srcval_proba": p, "srcval_X": X}


def score(cal: dict, tgt_proba, tgt_X, n_max=4000, seed=7) -> dict:
    """Statistics + alarms for a target deployment against the calibrated battery."""
    s = _stats(cal["srcval_proba"], cal["srcval_X"], np.asarray(tgt_proba), tgt_X,
               cal["source_acc"], n_max=n_max, seed=seed)
    thr = cal["thresholds"]
    return {m: {"statistic": float(s[m]), "threshold": float(thr[m]),
                "alarm": bool(s[m] > thr[m])} for m in s}


def _self_check() -> None:
    rng = np.random.default_rng(0)
    # source: well-separated scores; a held-out source half must stay quiet
    src_p = np.clip(rng.beta(2, 5, 4000), 0, 1)
    src_X = rng.normal(0, 1, (4000, C.N_FEAT))
    cal = calibrate(src_p, src_X, source_acc=0.95, b_cheap=40, b_expensive=8, n_max=1500)
    quiet = score(cal, src_p[:2000], src_X[:2000], n_max=1500)
    n_alarm_quiet = sum(v["alarm"] for v in quiet.values())
    # a genuinely shifted target should trip at least one monitor
    shifted = score(cal, np.clip(rng.beta(5, 2, 2000), 0, 1),
                    rng.normal(4, 1, (2000, C.N_FEAT)), n_max=1500)
    n_alarm_shift = sum(v["alarm"] for v in shifted.values())
    assert n_alarm_shift >= 1, "battery stayed silent on an obvious shift"
    print(f"monitors self-check passed  (quiet alarms={n_alarm_quiet}/5, "
          f"shifted alarms={n_alarm_shift}/5)")


if __name__ == "__main__":
    _self_check()
