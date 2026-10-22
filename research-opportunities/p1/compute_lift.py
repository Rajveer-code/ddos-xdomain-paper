"""
Honesty decomposition of the high-confidence-miss rate into three apples-to-apples pieces, so
the paper never conflates "clip a real flow into the source box" with "adversarial evasion"
(the defect an audit caught in the first draft).

For each config, on the real target DoS flows:
  * latent_hcm_rate  real flows, NO attacker constraints: fraction already predicted benign at
                     confidence >= tau. The detector's default exposure. Feasibility is an
                     attacker constraint, NOT a validity test for real wire-valid traffic, so it
                     is deliberately omitted here.
  * projected_hcmr   project real flows into the source box with NO search, then apply the full
                     (feasible+functional) success test. The attacker's floor: what merely
                     producing a feasible flow already achieves.
  * searched_hcmr    the full score-only search (from attack_results.json).
  * search_lift      searched_hcmr - projected_hcmr: the search's OWN contribution, isolated
                     from the projection step. This is the only honest "lift".

Saves results/p1/lift.json.
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


def latent_rate(fit, X, thr, tau):
    """Real flows, no attacker box: already benign at high confidence."""
    p = score_flows(fit, X)
    conf = np.maximum(p, 1 - p)
    return float(((p < thr) & (conf >= tau)).mean())


def projected_hcmr(fit, X, b, thr, tau):
    """Project into the source box, no search, then the full success test."""
    best = C.project(X, X, b)
    bp = score_flows(fit, best)
    sf = E.success_flags(best, bp, X, b, thr, tau)
    return float(sf["high_conf_miss"].mean())


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
                thr = F.fit.threshold
                tau = tau_accept_from(F.srcval_proba, F.srcval_y)
                lat = latent_rate(F.fit, Xatk, thr, tau)
                proj = projected_hcmr(F.fit, Xatk, b, thr, tau)
                rec = [r for r in atk if r["source"] == source and r["model"] == model
                       and r["seed"] == seed][0]
                searched = rec["score"]["hcmr"]
                out.append({"source": source, "model": model, "seed": seed,
                            "latent_hcm_rate": lat, "projected_hcmr": proj,
                            "searched_hcmr": searched, "search_lift": searched - proj})
    (OUT / "lift.json").write_text(json.dumps(out, indent=2))
    by = {}
    for r in out:
        by.setdefault((r["source"], r["model"]), []).append(r)
    print("source/model: latent | projected | searched | search_lift")
    for (s, m), rs in by.items():
        lat = np.mean([x["latent_hcm_rate"] for x in rs])
        proj = np.mean([x["projected_hcmr"] for x in rs])
        se = np.mean([x["searched_hcmr"] for x in rs])
        print(f"  {s[:11]:11s} {m:18s} {lat:.3f} | {proj:.3f} | {se:.3f} | {se-proj:+.3f}")


if __name__ == "__main__":
    main()
