"""
HCMR as a function of the score-only query budget (pre-registered: report at {50,100,200}).

If HCMR is flat across budgets, the finding is that search power is not the lever — the flows
sit a thin margin from the confidence threshold and a few queries suffice (consistent with the
small per-flow P-drop and the small search lift). Saves results/p1/budget_curve.json.
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
from run_phase3 import tau_accept_from  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"), ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
SEEDS = [42, 43, 44, 45, 46]
BUDGETS = [50, 100, 200]
FAMILY = "volumetric"
ATTACK_CAP = 2000
OUT = RESULTS / "p1"


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
                thr, tau = F.fit.threshold, tau_accept_from(F.srcval_proba, F.srcval_y)
                for budget in BUDGETS:
                    rng = np.random.default_rng(1000 + seed)
                    best, bp = E.search(F.fit, Xatk, b, budget, rng, mode="score")
                    sf = E.success_flags(best, bp, Xatk, b, thr, tau)
                    rows.append({"source": source, "model": model, "seed": seed,
                                 "budget": budget, "hcmr": float(sf["high_conf_miss"].mean())})
    (OUT / "budget_curve.json").write_text(json.dumps(rows, indent=2))
    # summary per (pair, model, budget)
    import itertools
    print("pair/model: HCMR at budgets", BUDGETS)
    for (s, m) in itertools.product([p[0] for p in PAIRS], MODELS):
        line = []
        for bud in BUDGETS:
            vals = [r["hcmr"] for r in rows if r["source"] == s and r["model"] == m and r["budget"] == bud]
            line.append(f"{np.mean(vals):.3f}" if vals else "-")
        print(f"  {s[:11]:11s} {m:18s} " + " ".join(line))


if __name__ == "__main__":
    main()
