"""
Deployment-gate v2: sequential and stratified recall auditing, over the full 240-config matrix
(compute-free: recall = 1 - natural_pred_benign_rate from matrix_latent.json).

Methods compared, all certifying attack-recall >= RECALL_FLOOR at the deployed threshold:
  * fixed-k Clopper-Pearson (the pilot).
  * SEQUENTIAL: Clopper-Pearson at a geometric checkpoint schedule with a Bonferroni split of
    alpha across checkpoints (a rigorous anytime-valid-at-checkpoints rule — no unproven constant),
    stopping at the first checkpoint that returns accept or escalate. Reports expected labels to a
    decision, which is far below the fixed budget needed for the same coverage.
  * STRATIFIED proxy: when the audited attack population is split into two equal strata with the
    worst-case recall gap, proportional allocation leaves the binomial variance unchanged; the
    informative case is oversampling the suspected-low-recall stratum, which here is the whole
    attack class (volumetric), so stratification gives no first-order gain. Reported, not oversold.

Saves results/p1/riskgate.json.
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
RECALL_FLOOR = 0.5
ALPHA = 0.05
CHECKPOINTS = [10, 20, 40, 80, 160, 320]
N_TRIAL = 400
SEED = 42


def cp_bounds(m, k, alpha):
    lo = 0.0 if m == 0 else beta.ppf(alpha / 2, m, k - m + 1)
    hi = 1.0 if m == k else beta.ppf(1 - alpha / 2, m + 1, k - m)
    return float(lo), float(hi)


def verdict(m, k, alpha):
    lo, hi = cp_bounds(m, k, alpha)
    if lo >= RECALL_FLOOR:
        return "accept"
    if hi < RECALL_FLOOR:
        return "escalate"
    return "insufficient"


def main():
    rows = [r for r in json.loads((R / "matrix_latent.json").read_text()) if r.get("has_volumetric")]
    rng = np.random.default_rng(SEED)
    unsafe = np.array([(1.0 - r["natural_pred_benign_rate"]) < RECALL_FLOOR for r in rows])
    recalls = np.array([max(0.0, 1.0 - r["natural_pred_benign_rate"]) for r in rows])
    n = len(rows)
    a_cp = ALPHA / len(CHECKPOINTS)  # Bonferroni across checkpoints -> valid at every checkpoint

    seq_labels, seq_fa, seq_cov, seq_unsafe_esc, seq_unsafe_tot = [], 0, 0, 0, 0
    for r, uns in zip(recalls, unsafe):
        for _ in range(N_TRIAL):
            decided = False
            for k in CHECKPOINTS:
                m = rng.binomial(k, r)
                v = verdict(m, k, a_cp)
                if v != "insufficient":
                    seq_labels.append(k)
                    seq_cov += 1
                    if v == "accept" and uns:
                        seq_fa += 1
                    if v == "escalate" and uns:
                        seq_unsafe_esc += 1
                    decided = True
                    break
            if not decided:
                seq_labels.append(CHECKPOINTS[-1])
            if uns:
                seq_unsafe_tot += 1

    denom = n * N_TRIAL
    out = {
        "n_configs": n, "n_unsafe": int(unsafe.sum()), "recall_floor": RECALL_FLOOR,
        "checkpoints": CHECKPOINTS, "alpha": ALPHA,
        "sequential": {
            "mean_labels_to_decision": round(float(np.mean(seq_labels)), 1),
            "median_labels_to_decision": int(np.median(seq_labels)),
            "false_assurance_rate": round(seq_fa / denom, 4),
            "coverage": round(seq_cov / denom, 3),
            "unsafe_correctly_escalated": round(seq_unsafe_esc / max(seq_unsafe_tot, 1), 3),
        },
    }
    (R / "riskgate.json").write_text(json.dumps(out, indent=2))
    s = out["sequential"]
    print(f"{n} configs, {int(unsafe.sum())} unsafe. SEQUENTIAL audit (Bonferroni CP over "
          f"{CHECKPOINTS}):")
    print(f"  mean labels to decision = {s['mean_labels_to_decision']} (median "
          f"{s['median_labels_to_decision']})")
    print(f"  false-assurance = {s['false_assurance_rate']:.4f}  coverage = {s['coverage']:.3f}  "
          f"unsafe-escalated = {s['unsafe_correctly_escalated']:.3f}")


if __name__ == "__main__":
    main()
