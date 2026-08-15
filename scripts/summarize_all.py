"""
Persist every aggregate the manuscript quotes.

The raw result files hold per-seed, per-pair records. The manuscript quotes means over
seeds. Those means were previously computed in ad-hoc analysis and typed into the text,
which breaks the project's rule that every number regenerates from results/ --
check_numbers.py flagged 23 such values.

This writes them out, so the manuscript's aggregates are artefacts like everything else.

    python scripts/summarize_all.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS


def load(name):
    p = RESULTS / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def m(v):
    a = np.asarray([x for x in v if x is not None and np.isfinite(x)], dtype=float)
    return float(a.mean()) if len(a) else None


def sd(v):
    a = np.asarray([x for x in v if x is not None and np.isfinite(x)], dtype=float)
    return float(a.std(ddof=1)) if len(a) > 1 else 0.0


def main() -> int:
    out: dict[str, dict] = {}

    # ---- feature ablation: per feature set, means over sources and seeds -------------
    abl = load("feature_ablation")
    if abl:
        agg = defaultdict(lambda: defaultdict(list))
        for r in abl["rows"]:
            a = agg[r["feature_set"]]
            a["k"] = r["n_features"]
            a["indomain_macro_f1"].append(r["indomain"]["macro_f1"])
            a["external_macro_f1"].append(r["external_mean_macro_f1"])
            a["external_auc"].append(r["external_mean_auc"])
        base_i = m(agg["all"]["indomain_macro_f1"])
        base_e = m(agg["all"]["external_macro_f1"])
        out["feature_ablation"] = {
            name: {
                "k": a["k"],
                "indomain_macro_f1": m(a["indomain_macro_f1"]),
                "indomain_sd": sd(a["indomain_macro_f1"]),
                "external_macro_f1": m(a["external_macro_f1"]),
                "external_sd": sd(a["external_macro_f1"]),
                "external_auc": m(a["external_auc"]),
                "delta_indomain_vs_all": m(a["indomain_macro_f1"]) - base_i,
                "delta_external_vs_all": m(a["external_macro_f1"]) - base_e,
            }
            for name, a in agg.items()
        }

    # ---- calibration: per pair, means over seeds ------------------------------------
    cal = load("calibration")
    if cal:
        agg = defaultdict(lambda: defaultdict(list))
        for r in cal["rows"]:
            a = agg[f"{r['source']}|{r['target']}"]
            for f in ("f1_source_threshold", "f1_benign_quantile", "f1_oracle_threshold",
                      "auc_external", "ece_external", "ece_in", "brier_external"):
                a[f].append(r[f])
        per = {}
        for k, a in agg.items():
            src, bq, orc = (m(a["f1_source_threshold"]), m(a["f1_benign_quantile"]),
                            m(a["f1_oracle_threshold"]))
            head = orc - src
            per[k] = {f: m(v) for f, v in a.items()}
            per[k]["headroom"] = head
            per[k]["headroom_recovered_fraction"] = (bq - src) / head if abs(head) > 1e-9 else None
        out["calibration"] = {
            "per_pair": per,
            "mean_ece_in": m([r["ece_in"] for r in cal["rows"]]),
            "mean_ece_external": m([r["ece_external"] for r in cal["rows"]]),
        }

    # ---- label budget: per k, means over pairs and seeds ----------------------------
    bud = load("label_budget")
    if bud:
        agg = defaultdict(lambda: defaultdict(list))
        for r in bud["rows"]:
            a = agg[r["k"]]
            a["rethreshold"].append(r["f1_rethreshold"])
            a["finetune"].append(r["f1_finetune"])
            a["benign_quantile"].append(r["f1_benign_quantile"])
            a["coral"].append(r["f1_coral"])
        out["label_budget"] = {
            str(k): {f: m(v) for f, v in a.items()} for k, a in sorted(agg.items())
        }

    # ---- CIC secondary study ---------------------------------------------------------
    cic = load("cic_pair")
    if cic:
        agg = defaultdict(lambda: defaultdict(list))
        for r in cic["rows"]:
            a = agg[f"{r['source']}|{r['target']}|{r['model']}"]
            a["indomain_macro_f1"].append(r["indomain"]["macro_f1"])
            a["external_macro_f1"].append(r["external"]["macro_f1"])
            a["external_auc"].append(r["external"]["roc_auc"])
            a["external_mcc"].append(r["external"]["mcc"])
            a["ranking_loss"].append(r["decomposition"]["ranking_loss"])
            a["threshold_loss"].append(r["decomposition"]["threshold_loss"])
        gaps = [r["gap_stats"] for r in cic["rows"] if "gap_stats" in r]
        out["cic_pair"] = {
            "per_config": {k: {f: m(v) for f, v in a.items()} for k, a in agg.items()},
            "n_features": cic["rows"][0]["n_features"],
            "mean_paired_gap": m([g["gap"] for g in gaps]),
            "n_gap_significant": sum(g["p_value"] < 0.05 for g in gaps),
            "n_gap_total": len(gaps),
        }

    # ---- label noise -----------------------------------------------------------------
    noise = load("label_noise")
    if noise:
        agg = defaultdict(lambda: defaultdict(list))
        for r in noise["rows"]:
            a = agg[r["model"]]
            a["original_macro_f1"].append(r["external_original"]["macro_f1"])
            a["corrected_macro_f1"].append(r["external_corrected"]["macro_f1"])
            a["delta_macro_f1"].append(r["delta_macro_f1"])
            a["delta_auc"].append(r["delta_auc"])
        out["label_noise"] = {
            "per_model": {k: {f: m(v) for f, v in a.items()} for k, a in agg.items()},
            "mean_abs_delta_macro_f1": m([abs(r["delta_macro_f1"]) for r in noise["rows"]]),
        }

    path = RESULTS / "paper_aggregates.json"
    path.write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"wrote {path}")
    for k, v in out.items():
        print(f"  {k}: {len(v)} group(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
