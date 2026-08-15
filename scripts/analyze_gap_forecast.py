"""
B2 analysis — can an unlabelled target predict how much performance will be lost?

Regresses the observed gap on each label-free divergence measure and, critically,
evaluates with **leave-one-pair-out** cross-validation. In-sample correlation over 12
pairs is easy to obtain and means little; the question an operator has is whether a
measure fitted on other people's transfers predicts theirs.

Baseline is the mean gap. A predictor that cannot beat "assume the average drop" is not
useful, however impressive its correlation.

Writes results/gap_forecast.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS

PREDICTORS = [
    "proxy_a_distance", "domain_clf_error",
    "wasserstein_sum", "wasserstein_mean", "wasserstein_max",
    "mmd_rbf",
    "mean_confidence_target", "mean_confidence_drop", "atc_estimated_accuracy",
]
TARGETS = ["gap_macro_f1", "external_macro_f1", "external_auc", "external_accuracy"]


def bootstrap_spearman(x, y, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    n = len(x)
    rs = [spearmanr(x[i], y[i]).statistic
          for i in (rng.integers(0, n, n) for _ in range(n_boot))]
    rs = np.array([r for r in rs if np.isfinite(r)])
    return float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))


def lopo_mae(pairs, x, y):
    """Leave-one-PAIR-out MAE for a univariate OLS fit. All seeds of a pair held out together."""
    errs = []
    for held in sorted(set(pairs)):
        tr = pairs != held
        te = ~tr
        if tr.sum() < 3 or te.sum() == 0:
            continue
        b, a = np.polyfit(x[tr], y[tr], 1)
        errs.extend(np.abs((a + b * x[te]) - y[te]))
    return float(np.mean(errs)) if errs else float("nan")


def main() -> int:
    d = json.loads((RESULTS / "divergence.json").read_text(encoding="utf-8"))
    rows = d["rows"]
    pairs = np.array([f"{r['source']}->{r['target']}" for r in rows])
    print(f"{len(rows)} pair-seed observations over {len(set(pairs))} ordered pairs\n")

    out = {}
    for tgt in TARGETS:
        y = np.array([r[tgt] for r in rows], dtype=float)
        base_mae = float(np.mean([
            np.abs(y[pairs != h].mean() - y[pairs == h]).mean()
            for h in sorted(set(pairs))
        ]))
        print("=" * 74)
        print(f"TARGET: {tgt}    (leave-one-pair-out baseline MAE = {base_mae:.4f})")
        print(f"{'predictor':26s} {'spearman':>9s} {'95% CI':>18s} {'LOPO MAE':>9s} {'vs base':>8s}")
        res = {}
        for p in PREDICTORS:
            x = np.array([r[p] for r in rows], dtype=float)
            ok = np.isfinite(x) & np.isfinite(y)
            if ok.sum() < 6:
                continue
            rho = spearmanr(x[ok], y[ok]).statistic
            lo, hi = bootstrap_spearman(x[ok], y[ok])
            mae = lopo_mae(pairs[ok], x[ok], y[ok])
            print(f"{p:26s} {rho:+9.3f} [{lo:+.3f}, {hi:+.3f}] {mae:9.4f} "
                  f"{(mae - base_mae):+8.4f}")
            res[p] = {"spearman": float(rho), "ci_lo": lo, "ci_hi": hi,
                      "lopo_mae": mae, "baseline_mae": base_mae,
                      "beats_baseline": bool(mae < base_mae)}
        out[tgt] = res
        print()

    (RESULTS / "gap_forecast.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"wrote {RESULTS / 'gap_forecast.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
