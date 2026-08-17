"""Aggregate the probabilistic and operating-point metrics the protocol collects.

Table 2 lists PR-AUC, Brier, ECE and FPR@95%TPR as part of the evaluation protocol, but
the results sections only ever reported macro-F1, MCC and ROC-AUC. Every one of these is
already recorded per run in transfer_matrix.json; this collapses them to the in-domain and
external means the manuscript needs, so the table has a result file behind it like every
other table in the paper.

    python scripts/aggregate_operating_point.py
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS

MODELS = ["LogisticRegression", "RandomForest", "XGBoost", "LightGBM"]
FIELDS = ["pr_auc", "brier", "ece", "macro_f1", "roc_auc"]


def main() -> int:
    rows = json.loads((RESULTS / "transfer_matrix.json").read_text(encoding="utf-8"))["rows"]

    out: dict[str, dict] = {"per_model": {}, "pooled": {}}
    for model in MODELS + ["__all__"]:
        sel = [r for r in rows if model == "__all__" or r["model"] == model]
        block: dict[str, dict] = {}
        for kind in ("in_domain", "external"):
            k = [r for r in sel if r["kind"] == kind]
            if not k:
                continue
            entry = {"n": len(k)}
            for f in FIELDS:
                entry[f] = st.fmean(r["metrics"][f] for r in k)
            # stored at top level of the run record, not under metrics
            fpr = [r["fpr_at_95tpr"] for r in k if r.get("fpr_at_95tpr") is not None]
            entry["fpr_at_95tpr"] = st.fmean(fpr) if fpr else None
            block[kind] = entry
        key = "pooled" if model == "__all__" else model
        (out["pooled"] if model == "__all__" else out["per_model"]).update(
            block if model == "__all__" else {model: block}
        )

    dest = RESULTS / "operating_point_metrics.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {dest}")
    for kind, v in out["pooled"].items():
        print(f"  pooled {kind:<10} n={v['n']:<4} PR-AUC {v['pr_auc']:.4f}  "
              f"Brier {v['brier']:.4f}  ECE {v['ece']:.4f}  FPR@95 {v['fpr_at_95tpr']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
