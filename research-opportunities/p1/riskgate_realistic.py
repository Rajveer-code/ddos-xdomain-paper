"""
Honest accounting of what a recall audit costs — the sampling design the review flagged.

The pilot (riskgate_pilot.py / riskgate.py) draws k *labelled attack* flows. That is an
ATTACK-REFERENCE (active) audit: the auditor must be able to produce known attacks (replay the
source-network attacks the detector was trained on, a red-team, or honeypot captures). It is
realistic for a defender who HAS source attacks, and it certifies recall *against that reference
attack distribution* — not against unknown zero-days. It does NOT assume the operator can label
target-native attacks for free.

If instead the auditor PASSIVELY labels random target traffic at base rate pi, getting k attacks
costs ~k/pi labels in expectation (negative binomial). At NIDS base rates this is large. This
script states both costs honestly so no headline conflates them.

Compute-free: uses the per-config recall from matrix_latent.json and stated base rates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import RESULTS  # noqa: E402

R = RESULTS / "p1"
BASE_RATES = [0.10, 0.01, 0.001]     # operational attack prevalence scenarios
K_ATTACKS = [10, 25, 50]             # labelled ATTACKS needed by the active audit


def main():
    rows = [r for r in json.loads((R / "matrix_latent.json").read_text()) if r.get("has_volumetric")]
    recalls = np.array([max(0.0, 1.0 - r["natural_pred_benign_rate"]) for r in rows])

    out = {
        "audit_sampling": "active / attack-reference (k labelled ATTACK flows); certifies recall "
                          "against the reference attack distribution, not unknown attacks",
        "active_cost_labels_per_attack": 1,
        "passive_cost": {},
        "note": "passive cost = expected random target labels to observe k attacks = k/pi "
                "(negative binomial). Active auditing (replaying known/source attacks) avoids this "
                "and is the regime the pilot assumes.",
    }
    for pi in BASE_RATES:
        out["passive_cost"][str(pi)] = {str(k): int(round(k / pi)) for k in K_ATTACKS}

    # sanity: the recall values themselves are an attack-only quantity, so the gate's verdicts are
    # unchanged; only the LABEL COST interpretation changes. Report the recall distribution.
    out["recall_distribution"] = {
        "mean": round(float(recalls.mean()), 3),
        "frac_below_0.5": round(float((recalls < 0.5).mean()), 3),
        "frac_below_0.1": round(float((recalls < 0.1).mean()), 3),
    }
    (R / "riskgate_realistic.json").write_text(json.dumps(out, indent=2))
    print("ACTIVE (attack-reference) audit: 1 label per attack; k attacks -> k labels.")
    print("PASSIVE (random target labelling) cost to observe k attacks = k/pi:")
    for pi in BASE_RATES:
        print(f"  base rate {pi:>6}: " +
              ", ".join(f"k={k}->{out['passive_cost'][str(pi)][str(k)]} labels" for k in K_ATTACKS))
    print(f"recall: mean {out['recall_distribution']['mean']}, "
          f"frac<0.5 {out['recall_distribution']['frac_below_0.5']}, "
          f"frac<0.1 {out['recall_distribution']['frac_below_0.1']}")


if __name__ == "__main__":
    main()
