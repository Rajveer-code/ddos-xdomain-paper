"""
Empirical illustration of the confidence-functional blindness proposition (manuscript §4.5).

On the dangerous cell (BoT-IoT→CSE-CIC / LogisticRegression) the adversarial deployment
(target benign + searched attack flows) has a collapsed attack recall, yet ATC — a functional
of the score distribution alone — reports an estimated accuracy at the source level, because
accuracy at the operational base rate is dominated by benign traffic and is invariant to the
relabelling the adversary performs. The operationally relevant quantity (attack recall) is not a
functional of the score distribution and is therefore invisible to the monitor.

Saves results/p1/theory_illustration.json (mean over 5 seeds).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import RESULTS  # noqa: E402
from src.divergence import confidence_scores  # noqa: E402
import constraints as C  # noqa: E402
import evade as E  # noqa: E402
from p1common import build_fit, read_capped, score_flows  # noqa: E402

SOURCE, TARGET, MODEL = "nf_bot_iot", "nf_cse_cic_ids2018", "LogisticRegression"
SEEDS = [42, 43, 44, 45, 46]
OUT = RESULTS / "p1"


def main():
    b = C.Bounds.from_json(json.loads((OUT / "constraints.json").read_text())[SOURCE]["volumetric"])
    rows = []
    for seed in SEEDS:
        F = build_fit(SOURCE, MODEL, seed)
        thr = F.fit.threshold
        Xb, yb, _ = read_capped(TARGET, 20000, 0, seed, family=None)
        Xben = Xb.to_numpy(float)[yb == 0]
        Xa, _, _ = read_capped(TARGET, 0, 2000, seed, family="volumetric")
        best, bp = E.search(F.fit, Xa.to_numpy(float), b, 200, np.random.default_rng(1000 + seed),
                            mode="score")
        pben = score_flows(F.fit, Xben)
        proba = np.concatenate([pben, bp])
        y = np.concatenate([np.zeros(len(pben)), np.ones(len(bp))])
        true_acc = float(((proba >= thr).astype(int) == y).mean())
        atc = confidence_scores(F.srcval_proba, proba, F.source_acc)["atc_estimated_accuracy"]
        recall = float((bp >= thr).mean())
        rows.append({"seed": seed, "source_acc": F.source_acc, "atc_estimated_accuracy": atc,
                     "true_accuracy": true_acc, "attack_recall": recall})
    agg = {k: round(float(np.mean([r[k] for r in rows])), 3)
           for k in ("source_acc", "atc_estimated_accuracy", "true_accuracy", "attack_recall")}
    agg["cell"] = f"{SOURCE}->{TARGET}/{MODEL}"
    agg["per_seed"] = rows
    (OUT / "theory_illustration.json").write_text(json.dumps(agg, indent=2))
    print(f"[{agg['cell']}] source_acc={agg['source_acc']:.3f} "
          f"ATC_est_acc={agg['atc_estimated_accuracy']:.3f} "
          f"true_acc={agg['true_accuracy']:.3f} attack_recall={agg['attack_recall']:.3f}")


if __name__ == "__main__":
    main()
