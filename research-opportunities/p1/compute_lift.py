"""
Honesty metric: how much of the high-confidence-miss rate is LATENT (present with no attack)
versus EARNED by the adaptive search. Natural HCMR evaluates the original target attack flows
through the same success definition; adversarial lift = HCMR(after search) - natural HCMR.

Saves results/p1/lift.json. This is the number that keeps the paper honest: if the lift is
small, the finding is "the monitored detector is already wide open", not "the adversary is
powerful".
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
from p1common import build_fit, read_capped, score_flows  # noqa: E402
from run_phase3 import tau_accept_from  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"), ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression"]
SEEDS = [42, 43, 44]
FAMILY = "volumetric"
ATTACK_CAP = 2000
OUT = RESULTS / "p1"


def nat_hcmr(fit, X, b, thr, tau):
    p = score_flows(fit, X)
    conf = np.maximum(p, 1 - p)
    return float(((p < thr) & (conf >= tau) & C.feasible(X, X, b) & C.functional(X, b)).mean())


def main():
    bounds = json.loads((OUT / "constraints.json").read_text())
    atk = json.loads((OUT / "attack_results.json").read_text())
    out = []
    for source, target in PAIRS:
        b = C.Bounds.from_json(bounds[source][FAMILY])
        for seed in SEEDS:
            Xa, _ya, _ = read_capped(target, 0, ATTACK_CAP, seed, family=FAMILY)
            Xatk = Xa.to_numpy(float)
            for model in MODELS:
                F = build_fit(source, model, seed)
                tau = tau_accept_from(F.srcval_proba, F.srcval_y)
                nat = nat_hcmr(F.fit, Xatk, b, F.fit.threshold, tau)
                rec = [r for r in atk if r["source"] == source and r["model"] == model
                       and r["seed"] == seed][0]
                out.append({"source": source, "model": model, "seed": seed,
                            "natural_hcmr": nat, "attack_hcmr": rec["score"]["hcmr"],
                            "adversarial_lift": rec["score"]["hcmr"] - nat})
    (OUT / "lift.json").write_text(json.dumps(out, indent=2))
    print("source/model: natural_HCMR -> attack_HCMR  (lift)")
    by = {}
    for r in out:
        by.setdefault((r["source"], r["model"]), []).append(r)
    for (s, m), rs in by.items():
        nat = np.mean([x["natural_hcmr"] for x in rs])
        att = np.mean([x["attack_hcmr"] for x in rs])
        print(f"  {s[:11]:11s} {m:18s} {nat:.3f} -> {att:.3f}  (lift {att-nat:+.3f})")


if __name__ == "__main__":
    main()
