"""
Measure what DNS_QUERY_ID carries in each NetFlow v2 dataset (manuscript Table 9).

For each dataset, after the paper's own preparation (identifier columns dropped, exact
duplicates removed, non-DoS attacks dropped), reports:
    P(attack | id == 0) and P(attack | id != 0)
    ROC-AUC of the raw id value and of the zero/nonzero bit against the label
    ROC-AUC of the raw id among nonzero rows only (does the value itself carry anything?)

Produces results/dns_query_id.json. No model is trained.

    python scripts/analyze_dns_query_id.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import NETFLOW_V2, RESULTS
from src.data import load

FIELD = "DNS_QUERY_ID"


def auc(y: np.ndarray, s: np.ndarray) -> float | None:
    return float(roc_auc_score(y, s)) if len(np.unique(y)) == 2 else None


def main() -> int:
    out = {}
    for ds in NETFLOW_V2:
        X, y, _, _ = load(ds.key, other_policy="drop", dedup=True)
        ident = X[FIELD].to_numpy(dtype=float)
        lab = y.to_numpy()
        zero = ident == 0
        nz = ~zero
        out[ds.key] = {
            "n": int(len(lab)), "n_id_zero": int(zero.sum()), "n_id_nonzero": int(nz.sum()),
            "p_attack_given_zero": float(lab[zero].mean()) if zero.any() else None,
            "p_attack_given_nonzero": float(lab[nz].mean()) if nz.any() else None,
            "auc_raw_value": auc(lab, ident),
            "auc_nonzero_bit": auc(lab, nz.astype(float)),
            "auc_raw_value_among_nonzero": auc(lab[nz], ident[nz]) if nz.any() else None,
        }
        print(ds.key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out[ds.key].items()})
    payload = {"preparation": "src.data.load(other_policy='drop', dedup=True)", "field": FIELD,
               "datasets": out}
    (RESULTS / "dns_query_id.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote results/dns_query_id.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
