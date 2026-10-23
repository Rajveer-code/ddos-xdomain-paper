"""
Check 2 (pre-declared protocol in DECISION.md): validate the PASSIVE-sampling audit instead of
relying on the k/pi expected-cost calculation.

For attack prevalences pi in {0.1, 0.01, 0.001} and labelling budgets N in {100, 1000}, simulate
random target labelling (each drawn flow is attack w.p. pi, caught w.p. the config's true recall)
and report, over the 240 configs x trials:
  (a) negative-binomial labels to observe k=10 attacks (median, 90th pct) vs the k/pi mean;
  (b) P(fewer than 10 attacks within budget N);
  (c) the gate's false-certification / escalation behaviour under passive sampling;
  (d) whether 10 labelled ATTACKS can certify SAFE (recall>=0.5) at 95% one-sided (from CP math).

Compute-free: recall per config = 1 - natural_pred_benign_rate (matrix_latent.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta, nbinom, binom

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import RESULTS  # noqa: E402

R = RESULTS / "p1"
PIS = [0.10, 0.01, 0.001]
BUDGETS = [100, 1000]
RECALL_FLOOR = 0.5
ALPHA = 0.05
K = 10
N_TRIAL = 300
SEED = 42


def cp_lower(m, k, alpha=ALPHA):
    return 0.0 if m == 0 else float(beta.ppf(alpha, m, k - m + 1))


def cp_upper(m, k, alpha=ALPHA):
    return 1.0 if m == k else float(beta.ppf(1 - alpha, m + 1, k - m))


def main():
    rows = [r for r in json.loads((R / "matrix_latent.json").read_text()) if r.get("has_volumetric")]
    recalls = np.array([max(0.0, 1.0 - r["natural_pred_benign_rate"]) for r in rows])
    unsafe = recalls < RECALL_FLOOR
    rng = np.random.default_rng(SEED)

    # (d) minimum caught-of-10 to certify safe at 95% one-sided
    min_m_safe = next((m for m in range(K + 1) if cp_lower(m, K) >= RECALL_FLOOR), None)

    out = {"recall_floor": RECALL_FLOOR, "alpha": ALPHA, "k_attacks": K,
           "min_caught_of_10_to_certify_safe": min_m_safe,
           "cp_lower_at_m": {str(m): round(cp_lower(m, K), 3) for m in range(6, 11)},
           "passive": {}}

    for pi in PIS:
        # (a) negative-binomial labels to see k attacks: number of trials = k successes
        # nbinom(k, pi) counts failures before k successes; labels = failures + k
        med = int(nbinom.ppf(0.5, K, pi) + K)
        p90 = int(nbinom.ppf(0.9, K, pi) + K)
        rec = {"mean_labels_k_pi": int(round(K / pi)), "median_labels_for_10_attacks": med,
               "p90_labels_for_10_attacks": p90, "by_budget": {}}
        for N in BUDGETS:
            p_too_few = float(binom.cdf(K - 1, N, pi))  # P(<10 attacks in N draws)
            # simulate gate under passive sampling
            fa = esc = insuf = nodata = 0
            for r, uns in zip(recalls, unsafe):
                for _ in range(N_TRIAL):
                    a = rng.binomial(N, pi)               # attacks observed
                    if a == 0:
                        nodata += 1
                        continue
                    m = rng.binomial(a, r)                # caught among observed attacks
                    lo, hi = cp_lower(m, a), cp_upper(m, a)
                    if lo >= RECALL_FLOOR:
                        if uns:
                            fa += 1
                    elif hi < RECALL_FLOOR:
                        if uns:
                            esc += 1
                    else:
                        insuf += 1
            denom = len(rows) * N_TRIAL
            rec["by_budget"][str(N)] = {
                "P_fewer_than_10_attacks": round(p_too_few, 3),
                "false_assurance_rate": round(fa / denom, 4),
                "insufficient_rate": round(insuf / denom, 3),
                "no_attack_sample_rate": round(nodata / denom, 3),
            }
        out["passive"][str(pi)] = rec

    (R / "audit_passive.json").write_text(json.dumps(out, indent=2))
    print(f"min caught-of-10 to certify SAFE (recall>=0.5) at 95% one-sided: {min_m_safe}/10 "
          f"(CP lower at 9/10 = {cp_lower(9,10):.3f}, at 8/10 = {cp_lower(8,10):.3f})")
    for pi in PIS:
        r = out["passive"][str(pi)]
        print(f"pi={pi}: ~{r['mean_labels_k_pi']} labels for 10 attacks (median {r['median_labels_for_10_attacks']}); "
              f"N=100 P(<10 attacks)={r['by_budget']['100']['P_fewer_than_10_attacks']}, "
              f"N=1000 P(<10)={r['by_budget']['1000']['P_fewer_than_10_attacks']}")


if __name__ == "__main__":
    main()
