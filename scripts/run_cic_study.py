"""
Secondary study — the conventional CICFlowMeter pairing, plus label-noise isolation.

Two questions the NetFlow v2 quartet cannot answer:

1. **Does the conclusion survive the feature space the literature actually uses?**
   CIC-DDoS2019 and CICIDS2017 are the standard pairing, harmonised the standard way:
   intersect the column names and hope. Both directions are run.

2. **How much of the gap is label error rather than domain shift?**
   CICIDS2017 has documented label defects (Engelen et al., WTMC 2021; Lanvin et al.,
   CRiSIS 2022). Running the identical source model against the original labels and
   against the DistriNet-corrected release isolates the two: the difference between
   those two external scores is attributable to labelling, not to the network.

Writes results/cic_pair.json and results/label_noise.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS
from src.data import _harmonize_columns, _read_parquet_dir
from src.config import DATASETS
from src.metrics import decompose_gap, paired_gap_ci
from src.pipeline import apply_to, fit_source


def cic_shared_features(keys: list[str]) -> list[str]:
    """Numeric columns common to the given CICFlowMeter datasets, after harmonisation."""
    per: dict[str, set[str]] = {}
    for k in keys:
        raw = _read_parquet_dir(DATASETS[k].path).head(200)
        cols, _ = _harmonize_columns(raw)
        cols = cols.drop(columns=[c for c in ("Label", "Attack", "Class")
                                  if c in cols.columns], errors="ignore")
        per[k] = set(cols.select_dtypes(include=[np.number]).columns)
    shared = sorted(set.intersection(*per.values()))
    for k, s in per.items():
        dropped = sorted(s - set(shared))
        if dropped:
            print(f"  {k}: {len(dropped)} column(s) not shared -> {dropped[:6]}"
                  f"{' ...' if len(dropped) > 6 else ''}")
    return shared


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=100_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44, 45, 46])
    ap.add_argument("--models", nargs="*",
                    default=["LightGBM", "XGBoost", "RandomForest", "LogisticRegression"])
    args = ap.parse_args()

    keys = ["cic_ddos2019", "cic_ids2017", "cic_ids2017_fixed"]
    print("Resolving the shared CICFlowMeter feature space (the ad-hoc way):")
    feats = cic_shared_features(keys)
    print(f"  shared numeric features: {len(feats)}\n")

    pair_rows, noise_rows = [], []
    t0 = time.perf_counter()

    # ---- 1. the conventional pairing, both directions ------------------------------
    for src, tgt in [("cic_ddos2019", "cic_ids2017"), ("cic_ids2017", "cic_ddos2019")]:
        for model in args.models:
            for seed in args.seeds:
                fit = fit_source(src, model, seed=seed, features=feats,
                                 n_per_class=args.n_per_class)
                r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                pred_in = fit.proba_test >= fit.threshold
                pred_ex = r["proba"] >= fit.threshold
                row = {
                    "source": src, "target": tgt, "model": model, "seed": seed,
                    "n_features": len(feats),
                    "indomain": fit.indomain, "external": r["external"],
                    "decomposition": decompose_gap(fit.y_test, fit.proba_test,
                                                   r["y"], r["proba"], fit.threshold),
                }
                if model == "LightGBM":
                    row["gap_stats"] = paired_gap_ci(fit.y_test, pred_in, r["y"],
                                                     pred_ex, n_boot=1000, seed=seed)
                pair_rows.append(row)
                print(f"{src} -> {tgt} | {model:20s} s{seed} | "
                      f"in {fit.indomain['macro_f1']:.4f} ext {r['external']['macro_f1']:.4f} "
                      f"AUC {r['external']['roc_auc']:.4f}", flush=True)

    # ---- 2. label-noise isolation ---------------------------------------------------
    print("\nLabel-noise isolation: identical model, original vs corrected CICIDS2017")
    for model in args.models:
        for seed in args.seeds:
            fit = fit_source("cic_ddos2019", model, seed=seed, features=feats,
                             n_per_class=args.n_per_class)
            orig = apply_to(fit, "cic_ids2017", n_per_class=args.n_per_class)
            fixed = apply_to(fit, "cic_ids2017_fixed", n_per_class=args.n_per_class)
            d_f1 = fixed["external"]["macro_f1"] - orig["external"]["macro_f1"]
            d_auc = fixed["external"]["roc_auc"] - orig["external"]["roc_auc"]
            noise_rows.append({
                "source": "cic_ddos2019", "model": model, "seed": seed,
                "external_original": orig["external"],
                "external_corrected": fixed["external"],
                "delta_macro_f1": d_f1, "delta_auc": d_auc,
            })
            print(f"  {model:20s} s{seed} | orig {orig['external']['macro_f1']:.4f} "
                  f"corrected {fixed['external']['macro_f1']:.4f} "
                  f"delta {d_f1:+.4f} (AUC {d_auc:+.4f})", flush=True)

    for name, rows in [("cic_pair", pair_rows), ("label_noise", noise_rows)]:
        (RESULTS / f"{name}.json").write_text(
            json.dumps({"config": {**vars(args), "features": feats}, "rows": rows},
                       indent=1, default=float), encoding="utf-8")
        print(f"wrote {RESULTS / f'{name}.json'} ({len(rows)} rows)")
    print(f"done in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
