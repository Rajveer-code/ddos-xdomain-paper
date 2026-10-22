"""
Deployment-gate pilot: a budgeted target-label audit is the minimal evidence that recovers the
recall a score-only monitor cannot certify (the forced corollary of the §4.5 recall-invisibility
proposition).

Compute-free: reads results/p1/matrix_latent.json. For each (source,target,model,seed) with
volumetric target flows, the detector's true recall at its deployed threshold is
recall = 1 - natural_pred_benign_rate (every such flow is an attack). We compare, across all 240
configurations:

  * SCORE-ONLY verdict: accept iff neither ATC nor confidence-drop fires (what an operator relying
    on the label-free confidence monitors would do).
  * AUDIT-GATE verdict at budget k: draw k labelled target attack flows, observe caught count
    m ~ Binomial(k, recall), form a Clopper-Pearson 95% lower bound on recall, and
       accept   if recall_LB >= RECALL_FLOOR   (certified safe)
       escalate if recall_UB <  RECALL_FLOOR   (certified unsafe)
       else "insufficient evidence".

A configuration is UNSAFE if its true recall < RECALL_FLOOR. The headline is the false-assurance
rate (accepting an unsafe config) for each method, and the audit gate's coverage (fraction of
configs it can call accept/escalate rather than insufficient) as k grows.

Saves results/p1/riskgate_pilot.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import RESULTS  # noqa: E402

R = RESULTS / "p1"
RECALL_FLOOR = 0.5        # operator requires attack recall >= 0.5 (FNR <= 0.5)
BUDGETS = [10, 25, 50, 100, 250]
ALPHA = 0.05
N_TRIAL = 400             # audit simulations per config (random labelled draws)
SEED = 42


def cp_bounds(m: int, k: int):
    """Clopper-Pearson (1-ALPHA) interval on a binomial rate m/k."""
    lo = 0.0 if m == 0 else beta.ppf(ALPHA / 2, m, k - m + 1)
    hi = 1.0 if m == k else beta.ppf(1 - ALPHA / 2, m + 1, k - m)
    return float(lo), float(hi)


def main():
    rows = [r for r in json.loads((R / "matrix_latent.json").read_text()) if r.get("has_volumetric")]
    rng = np.random.default_rng(SEED)

    n = len(rows)
    unsafe = np.array([(1.0 - r["natural_pred_benign_rate"]) < RECALL_FLOOR for r in rows])
    # score-only: accept iff no model-monitor fires
    so_accept = np.array([not (r["atc_alarm"] or r["conf_drop_alarm"]) for r in rows])
    so_false_assurance = float((so_accept & unsafe).mean())

    out = {"n_configs": n, "recall_floor": RECALL_FLOOR, "n_unsafe": int(unsafe.sum()),
           "score_only": {"false_assurance_rate": round(so_false_assurance, 3),
                          "accept_rate": round(float(so_accept.mean()), 3)},
           "audit_gate": {}}

    for k in BUDGETS:
        fa = cov = correct_esc = 0
        total_unsafe_calls = 0
        for r, uns in zip(rows, unsafe):
            recall = max(0.0, 1.0 - r["natural_pred_benign_rate"])
            m = rng.binomial(k, recall, N_TRIAL)
            for mi in m:
                lo, hi = cp_bounds(int(mi), k)
                if lo >= RECALL_FLOOR:
                    verdict = "accept"
                elif hi < RECALL_FLOOR:
                    verdict = "escalate"
                else:
                    verdict = "insufficient"
                cov += (verdict != "insufficient")
                if verdict == "accept" and uns:
                    fa += 1
                if uns:
                    total_unsafe_calls += 1
                    correct_esc += (verdict == "escalate")
        denom = n * N_TRIAL
        out["audit_gate"][str(k)] = {
            "false_assurance_rate": round(fa / denom, 4),
            "coverage": round(cov / denom, 3),
            "unsafe_correctly_escalated": round(correct_esc / max(total_unsafe_calls, 1), 3),
        }

    (R / "riskgate_pilot.json").write_text(json.dumps(out, indent=2))
    print(f"{n} configs, {int(unsafe.sum())} unsafe (true recall < {RECALL_FLOOR})")
    print(f"SCORE-ONLY false-assurance rate: {so_false_assurance:.3f} "
          f"(accepts {so_accept.mean():.2f} of configs)")
    print("AUDIT-GATE by budget k:  false-assurance | coverage | unsafe-escalated")
    for k in BUDGETS:
        g = out["audit_gate"][str(k)]
        print(f"  k={k:3d}: {g['false_assurance_rate']:.4f} | {g['coverage']:.3f} | "
              f"{g['unsafe_correctly_escalated']:.3f}")


if __name__ == "__main__":
    main()
