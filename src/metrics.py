"""
Metrics, calibration and the statistics used on the generalization gap.

Two things here are deliberately different from common practice in this literature:

1. **The gap is the estimand.** Reporting a CI on in-domain score and another on external
   score says nothing about the CI of their difference. `paired_gap_ci` resamples the two
   test sets jointly, so the reported gap carries its own interval and p-value.
2. **Ranking loss and threshold loss are separated.** A detector can preserve its ability
   to rank attacks above benign traffic (AUC holds) while the operating threshold chosen
   in-domain becomes meaningless (F1 collapses). Aggregating those into one number hides
   which failure occurred, and they call for completely different fixes.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ------------------------------------------------------------------- point estimates


def expected_calibration_error(y_true, proba, n_bins: int = 15) -> float:
    """Equal-width-bin ECE. Reported because a NIDS deploys a threshold, not a ranking."""
    y_true = np.asarray(y_true)
    proba = np.asarray(proba, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(proba, edges[1:-1], right=False), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = idx == b
        if not m.any():
            continue
        ece += (m.sum() / len(proba)) * abs(y_true[m].mean() - proba[m].mean())
    return float(ece)


def binary_metrics(y_true, y_pred, proba) -> dict[str, float]:
    """Full suite for one (model, dataset, threshold)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    both = len(np.unique(y_true)) > 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, proba)) if both else float("nan"),
        "pr_auc": float(average_precision_score(y_true, proba)) if both else float("nan"),
        "fpr": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "fnr": float(fn / (fn + tp)) if (fn + tp) else 0.0,
        "brier": float(brier_score_loss(y_true, proba)) if both else float("nan"),
        "ece": expected_calibration_error(y_true, proba),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


# ------------------------------------------------------------------------ thresholds


def best_threshold(y_true, proba, metric: str = "macro_f1", tol: float = 1e-9) -> float:
    """
    Threshold maximising `metric` on labelled data. The oracle a deployment lacks.

    Takes the midpoint of the **widest tied plateau** rather than argmax. When a model
    separates its own test set perfectly -- routine in-domain here, where AUC reaches
    1.0000 -- every threshold across a wide interval scores identically and argmax
    returns whichever endpoint the candidate grid happened to visit first. That endpoint
    sits flush against the score distribution, so it is maximally fragile under any
    shift, and choosing it would manufacture threshold loss that reflects an arbitrary
    tie-break rather than the domain gap.
    """
    y_true = np.asarray(y_true)
    proba = np.asarray(proba, dtype=float)

    # Candidates are midpoints *between* consecutive observed score levels. A grid drawn
    # from the observed scores themselves can only ever propose a value some sample
    # already takes, so with two well-separated clusters at 0.1 and 0.9 it can never
    # offer 0.5 -- it must pick one cluster's own value and sit flush against it.
    levels = np.unique(np.quantile(proba, np.linspace(0.0, 1.0, 401)))
    cands = (levels[:-1] + levels[1:]) / 2.0 if len(levels) > 1 else levels

    fn = (lambda t: f1_score(y_true, proba >= t, average="macro", zero_division=0)) \
        if metric == "macro_f1" else (lambda t: matthews_corrcoef(y_true, proba >= t))
    scores = np.array([fn(t) for t in cands], dtype=float)

    at_max = scores >= scores.max() - tol
    # Longest run of consecutive tied-optimal candidates.
    best_run, run_start, best_start, best_len = 0, 0, 0, 0
    for i, ok in enumerate(at_max):
        if ok:
            if i == 0 or not at_max[i - 1]:
                run_start = i
            run_len = i - run_start + 1
            if run_len > best_len:
                best_len, best_start = run_len, run_start
    best_run = best_start + best_len - 1
    return float((cands[best_start] + cands[best_run]) / 2.0)


def benign_quantile_threshold(proba_benign, target_fpr: float = 0.01) -> float:
    """
    Threshold from *unlabelled-attack* target traffic.

    An operator does not have attack labels for their own network, but they do have
    traffic they believe is benign. Setting the threshold at the (1 - target_fpr)
    quantile of scores on that traffic is a recalibration that needs no attack labels,
    and it is the practical remedy the paper evaluates.
    """
    return float(np.quantile(np.asarray(proba_benign, dtype=float), 1.0 - target_fpr))


def fpr_at_tpr(y_true, proba, target_tpr: float = 0.95) -> float:
    """FPR at a fixed detection rate — the operating point a SOC actually cares about."""
    from sklearn.metrics import roc_curve

    fpr, tpr, _ = roc_curve(np.asarray(y_true), np.asarray(proba, dtype=float))
    idx = np.searchsorted(tpr, target_tpr, side="left")
    return float(fpr[min(idx, len(fpr) - 1)])


def alerts_per_hour(fpr: float, recall: float, flows_per_hour: float,
                    base_rate: float) -> float:
    """
    Expected alert volume at a realistic base rate.

    Balanced-test-set F1 flatters every NIDS in this literature. At a 0.1% attack base
    rate a 1% FPR buries the analyst, and that is the number an operator budgets staff
    against (the base-rate fallacy, Axelsson 2000).
    """
    tp = flows_per_hour * base_rate * recall
    fp = flows_per_hour * (1.0 - base_rate) * fpr
    return float(tp + fp)


# ------------------------------------------------------------------------ statistics


def bootstrap_ci(values, alpha: float = 0.05) -> tuple[float, float]:
    v = np.asarray(values, dtype=float)
    return float(np.percentile(v, 100 * alpha / 2)), float(np.percentile(v, 100 * (1 - alpha / 2)))


def paired_gap_ci(
    y_in, pred_in, y_ex, pred_ex,
    metric_fn=lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0),
    n_boot: int = 2000,
    seed: int = 42,
) -> dict[str, float]:
    """
    Bootstrap CI and permutation p-value for (in-domain metric − external metric).

    The two test sets are resampled jointly on each draw, so the interval is on the
    difference itself rather than being eyeballed from two separate intervals.
    """
    rng = np.random.default_rng(seed)
    y_in, pred_in = np.asarray(y_in), np.asarray(pred_in)
    y_ex, pred_ex = np.asarray(y_ex), np.asarray(pred_ex)
    n_i, n_e = len(y_in), len(y_ex)

    gaps = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        i = rng.integers(0, n_i, n_i)
        e = rng.integers(0, n_e, n_e)
        gaps[b] = metric_fn(y_in[i], pred_in[i]) - metric_fn(y_ex[e], pred_ex[e])

    observed = metric_fn(y_in, pred_in) - metric_fn(y_ex, pred_ex)
    lo, hi = bootstrap_ci(gaps)
    # Two-sided bootstrap p-value for H0: gap == 0.
    p = float(2 * min((gaps <= 0).mean(), (gaps >= 0).mean()))
    return {
        "gap": float(observed),
        "gap_ci_lo": lo,
        "gap_ci_hi": hi,
        "gap_se": float(gaps.std(ddof=1)),
        "p_value": min(p, 1.0),
        "n_boot": n_boot,
    }


def decompose_gap(y_in, proba_in, y_ex, proba_ex, threshold_in: float) -> dict[str, float]:
    """
    Split the external drop into ranking loss and threshold loss.

    ranking_loss   = in-domain AUC − external AUC
                     (the representation genuinely stopped separating the classes)
    threshold_loss = external macro-F1 at the target-optimal threshold
                     − external macro-F1 at the in-domain threshold
                     (the representation was fine; the operating point was stale)

    If threshold_loss dominates, the failure is recoverable without retraining — which is
    a very different engineering conclusion from "the model does not transfer".
    """
    f1 = lambda yt, yp: f1_score(np.asarray(yt), yp, average="macro", zero_division=0)
    t_ex = best_threshold(y_ex, proba_ex)

    auc_in = roc_auc_score(y_in, proba_in)
    auc_ex = roc_auc_score(y_ex, proba_ex)
    f1_in = f1(y_in, np.asarray(proba_in) >= threshold_in)
    f1_ex_stale = f1(y_ex, np.asarray(proba_ex) >= threshold_in)
    f1_ex_oracle = f1(y_ex, np.asarray(proba_ex) >= t_ex)

    return {
        "auc_in": float(auc_in),
        "auc_external": float(auc_ex),
        "ranking_loss": float(auc_in - auc_ex),
        "f1_in": float(f1_in),
        "f1_external_stale_threshold": float(f1_ex_stale),
        "f1_external_oracle_threshold": float(f1_ex_oracle),
        "threshold_loss": float(f1_ex_oracle - f1_ex_stale),
        "total_f1_gap": float(f1_in - f1_ex_stale),
        "threshold_in": float(threshold_in),
        "threshold_external_oracle": float(t_ex),
    }


def _self_check() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 4000)
    p = np.clip(y * 0.7 + rng.normal(0, 0.2, 4000), 0.001, 0.999)

    m = binary_metrics(y, p >= 0.5, p)
    assert 0.0 <= m["ece"] <= 1.0 and m["roc_auc"] > 0.9

    # A perfectly calibrated score must have near-zero ECE.
    q = rng.random(20000)
    yq = (rng.random(20000) < q).astype(int)
    assert expected_calibration_error(yq, q) < 0.02

    # A gap against itself is zero and its CI must bracket zero.
    r = paired_gap_ci(y, p >= 0.5, y, p >= 0.5, n_boot=200)
    assert r["gap"] == 0.0 and r["gap_ci_lo"] <= 0.0 <= r["gap_ci_hi"]

    # Pure threshold failure: identical ranking, stale operating point.
    d = decompose_gap(y, p, y, p, threshold_in=0.999)
    assert abs(d["ranking_loss"]) < 1e-9, "identical scores must show no ranking loss"
    assert d["threshold_loss"] > 0.1, "a stale threshold must show threshold loss"

    assert alerts_per_hour(0.01, 1.0, 1_000_000, 0.001) > 9000

    # Perfectly separable scores: every threshold in the gap is optimal, and the chosen
    # one must sit in the middle of that gap rather than flush against either class.
    ysep = np.r_[np.zeros(500, int), np.ones(500, int)]
    psep = np.r_[np.full(500, 0.10), np.full(500, 0.90)]
    t = best_threshold(ysep, psep)
    assert 0.3 < t < 0.7, f"plateau midpoint expected near 0.5, got {t}"
    assert f1_score(ysep, psep >= t, average="macro") == 1.0
    print("metrics self-check passed")


if __name__ == "__main__":
    _self_check()
