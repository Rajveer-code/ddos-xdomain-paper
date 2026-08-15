"""
Aggregate the transfer matrix into the tables the manuscript reports.

Reads results/transfer_matrix.json, writes results/matrix_summary.json and prints the
headline tables. Aggregation is over seeds; the spread across seeds is reported
separately from sampling error, because they answer different questions.

    python scripts/summarize_matrix.py
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

SHORT = {
    "nf_cse_cic_ids2018": "IDS2018",
    "nf_bot_iot": "BoT-IoT",
    "nf_ton_iot": "ToN-IoT",
    "nf_unsw_nb15": "UNSW",
}


def mstd(vals: list[float]) -> tuple[float, float]:
    a = np.asarray(vals, dtype=float)
    a = a[np.isfinite(a)]
    return (float(a.mean()), float(a.std(ddof=1) if len(a) > 1 else 0.0)) if len(a) else (float("nan"), 0.0)


def main() -> int:
    payload = json.loads((RESULTS / "transfer_matrix.json").read_text(encoding="utf-8"))
    rows = payload["rows"]

    # ---------------------------------------------------------------- in-domain table
    ind: dict[tuple[str, str], list] = defaultdict(list)
    for r in rows:
        if r["kind"] == "in_domain":
            ind[(r["source"], r["model"])].append(r)

    print("=" * 78)
    print("IN-DOMAIN (source's own held-out split), mean +/- sd over seeds")
    print("=" * 78)
    print(f"{'source':10s} {'model':20s} {'macro-F1':>16s} {'MCC':>16s} {'AUC':>10s}")
    indomain_out = {}
    for (src, model), rs in sorted(ind.items()):
        f1m, f1s = mstd([x["metrics"]["macro_f1"] for x in rs])
        mcm, mcs = mstd([x["metrics"]["mcc"] for x in rs])
        aum, _ = mstd([x["metrics"]["roc_auc"] for x in rs])
        print(f"{SHORT[src]:10s} {model:20s} {f1m:.4f}+/-{f1s:.4f} {mcm:.4f}+/-{mcs:.4f} {aum:10.4f}")
        indomain_out[f"{src}|{model}"] = {"macro_f1": f1m, "macro_f1_sd": f1s,
                                          "mcc": mcm, "mcc_sd": mcs, "roc_auc": aum}

    # ------------------------------------------------------------------ external table
    ext: dict[tuple[str, str, str], list] = defaultdict(list)
    for r in rows:
        if r["kind"] == "external":
            ext[(r["source"], r["target"], r["model"])].append(r)

    print()
    print("=" * 78)
    print("EXTERNAL TRANSFER, mean over seeds  (all 4 models)")
    print("=" * 78)
    print(f"{'pair':22s} {'model':20s} {'macro-F1':>9s} {'MCC':>8s} {'AUC':>8s} "
          f"{'rankLoss':>9s} {'thrLoss':>8s}")
    external_out = {}
    for (src, tgt, model), rs in sorted(ext.items()):
        f1m, f1s = mstd([x["metrics"]["macro_f1"] for x in rs])
        mcm, _ = mstd([x["metrics"]["mcc"] for x in rs])
        aum, _ = mstd([x["metrics"]["roc_auc"] for x in rs])
        rlm, _ = mstd([x["decomposition"]["ranking_loss"] for x in rs])
        tlm, _ = mstd([x["decomposition"]["threshold_loss"] for x in rs])
        pair = f"{SHORT[src]}->{SHORT[tgt]}"
        print(f"{pair:22s} {model:20s} {f1m:9.4f} {mcm:+8.4f} {aum:8.4f} "
              f"{rlm:+9.4f} {tlm:+8.4f}")
        external_out[f"{src}|{tgt}|{model}"] = {
            "macro_f1": f1m, "macro_f1_sd": f1s, "mcc": mcm, "roc_auc": aum,
            "ranking_loss": rlm, "threshold_loss": tlm,
        }

    # ------------------------------------------------------- headline aggregate claims
    prim = [r for r in rows if r["model"] == "LightGBM"]
    ind_f1 = [r["metrics"]["macro_f1"] for r in prim if r["kind"] == "in_domain"]
    ext_f1 = [r["metrics"]["macro_f1"] for r in prim if r["kind"] == "external"]
    ext_auc = [r["metrics"]["roc_auc"] for r in prim if r["kind"] == "external"]
    ext_mcc = [r["metrics"]["mcc"] for r in prim if r["kind"] == "external"]

    all_ext = [r for r in rows if r["kind"] == "external"]
    below_chance = [r for r in all_ext if r["metrics"]["roc_auc"] < 0.5]
    neg_mcc = [r for r in all_ext if r["metrics"]["mcc"] < 0]

    # Which failure mode dominates, per pair (primary model, averaged over seeds).
    modes = {}
    for (src, tgt, model), rs in ext.items():
        if model != "LightGBM":
            continue
        rl, _ = mstd([x["decomposition"]["ranking_loss"] for x in rs])
        tl, _ = mstd([x["decomposition"]["threshold_loss"] for x in rs])
        auc, _ = mstd([x["metrics"]["roc_auc"] for x in rs])
        modes[f"{SHORT[src]}->{SHORT[tgt]}"] = {
            "ranking_loss": rl, "threshold_loss": tl, "auc": auc,
            "dominant": "ranking" if rl > tl else "threshold",
        }

    # Gap CIs from the paired bootstrap (primary model only).
    gaps = [r for r in prim if r["kind"] == "external" and "gap_stats" in r]
    gvals = [r["gap_stats"]["gap"] for r in gaps]
    sig = [r for r in gaps if r["gap_stats"]["p_value"] < 0.05]

    print()
    print("=" * 78)
    print("HEADLINE (primary model = LightGBM unless stated)")
    print("=" * 78)
    print(f"in-domain macro-F1      : {np.mean(ind_f1):.4f}  "
          f"[min {np.min(ind_f1):.4f}, max {np.max(ind_f1):.4f}]")
    print(f"external  macro-F1      : {np.mean(ext_f1):.4f}  "
          f"[min {np.min(ext_f1):.4f}, max {np.max(ext_f1):.4f}]")
    print(f"external  AUC           : {np.mean(ext_auc):.4f}  "
          f"[min {np.min(ext_auc):.4f}, max {np.max(ext_auc):.4f}]")
    print(f"external  MCC           : {np.mean(ext_mcc):+.4f} "
          f"[min {np.min(ext_mcc):+.4f}, max {np.max(ext_mcc):+.4f}]")
    print(f"mean paired gap (F1)    : {np.mean(gvals):.4f}  over {len(gaps)} pair-seeds")
    print(f"gaps significant p<0.05 : {len(sig)}/{len(gaps)}")
    print(f"external runs AUC < 0.5 : {len(below_chance)}/{len(all_ext)} "
          f"(all models, all seeds)  <- ranks attacks BELOW benign")
    print(f"external runs MCC < 0   : {len(neg_mcc)}/{len(all_ext)}")

    print()
    print("FAILURE MODE PER PAIR (LightGBM, mean over seeds)")
    print(f"{'pair':22s} {'AUC':>8s} {'rankLoss':>9s} {'thrLoss':>8s}  dominant")
    for k, v in sorted(modes.items(), key=lambda kv: -kv[1]["ranking_loss"]):
        print(f"{k:22s} {v['auc']:8.4f} {v['ranking_loss']:+9.4f} "
              f"{v['threshold_loss']:+8.4f}  {v['dominant']}")

    out = {
        "in_domain": indomain_out,
        "external": external_out,
        "failure_modes": modes,
        "headline": {
            "indomain_macro_f1_mean": float(np.mean(ind_f1)),
            "external_macro_f1_mean": float(np.mean(ext_f1)),
            "external_auc_mean": float(np.mean(ext_auc)),
            "external_mcc_mean": float(np.mean(ext_mcc)),
            "mean_paired_gap": float(np.mean(gvals)),
            "n_gap_pairseeds": len(gaps),
            "n_gap_significant": len(sig),
            "n_external_runs": len(all_ext),
            "n_auc_below_chance": len(below_chance),
            "n_mcc_negative": len(neg_mcc),
        },
    }
    (RESULTS / "matrix_summary.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"\nwrote {RESULTS / 'matrix_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
