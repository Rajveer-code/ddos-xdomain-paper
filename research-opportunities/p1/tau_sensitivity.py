"""
Robustness of the high-confidence-miss finding to the auto-accept operating point.

The pre-registration fixes tau_accept at a 1% benign-review budget and lists a 5% budget as a
secondary. This re-runs the score-only search on the two representative pairs x 4 models x 5
seeds and reports HCMR at BOTH budgets. A 5% budget escalates MORE benign flows (the operator
reviews more), so tau_accept = the 5th percentile of benign confidence is HIGHER than the 1st
percentile, i.e. the auto-accept bar is STRICTER and HCMR can only fall. The informative question
is which cells fall: a cell whose misses are at confidence ~1.0 is insensitive to the budget,
which is the worst case for an operator who hoped a stricter monitor would help. Saves
results/p1/tau_sensitivity.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import RESULTS  # noqa: E402
import constraints as C  # noqa: E402
import evade as E  # noqa: E402
from p1common import build_fit, read_capped  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"), ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
SEEDS = [42, 43, 44, 45, 46]
FAMILY = "volumetric"
BUDGET = 200
ATTACK_CAP = 2000
OUT = RESULTS / "p1"


def tau_at(srcval_proba, srcval_y, budget):
    conf = np.maximum(srcval_proba, 1 - srcval_proba)
    ben = conf[np.asarray(srcval_y) == 0]
    return float(np.quantile(ben if len(ben) else conf, budget))


def main():
    bounds = json.loads((OUT / "constraints.json").read_text())
    rows = []
    for source, target in PAIRS:
        b = C.Bounds.from_json(bounds[source][FAMILY])
        for seed in SEEDS:
            Xa, _, _ = read_capped(target, 0, ATTACK_CAP, seed, family=FAMILY)
            Xatk = Xa.to_numpy(float)
            for model in MODELS:
                F = build_fit(source, model, seed)
                thr = F.fit.threshold
                tau1 = tau_at(F.srcval_proba, F.srcval_y, 0.01)
                tau5 = tau_at(F.srcval_proba, F.srcval_y, 0.05)
                best, bp = E.search(F.fit, Xatk, b, BUDGET, np.random.default_rng(1000 + seed),
                                    mode="score")
                pred_benign = bp < thr
                conf = np.maximum(bp, 1 - bp)
                feas = C.feasible(best, Xatk, b) & C.functional(best, b)
                hcmr1 = float((pred_benign & (conf >= tau1) & feas).mean())
                hcmr5 = float((pred_benign & (conf >= tau5) & feas).mean())
                rows.append({"source": source, "model": model, "seed": seed,
                             "tau_1pct": tau1, "tau_5pct": tau5,
                             "hcmr_1pct": hcmr1, "hcmr_5pct": hcmr5})
    (OUT / "tau_sensitivity.json").write_text(json.dumps(rows, indent=2))
    by = {}
    for r in rows:
        by.setdefault((r["source"], r["model"]), []).append(r)
    print("source/model: HCMR @1% | @5%")
    for (s, m), rs in sorted(by.items()):
        print(f"  {s[:11]:11s} {m:18s} {np.mean([r['hcmr_1pct'] for r in rs]):.3f} | "
              f"{np.mean([r['hcmr_5pct'] for r in rs]):.3f}")


if __name__ == "__main__":
    main()
