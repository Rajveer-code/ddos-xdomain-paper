"""
B1 — the central experiment: which features cause the collapse?

Trains the primary model on each source under every feature set in the taxonomy and
applies it to all three other domains. The quantity of interest is not either score
alone but the *trade-off*: how much in-domain performance a feature class buys, against
how much external performance it costs.

If dropping the capacity classes (rate, duration, volume) costs little in-domain and
recovers external performance, the standard feature set is fitting the measurement
apparatus rather than the attack.

`only_identifier` is the calibrated null. DNS_QUERY_ID is a random transaction ID, so
whatever in-domain score it reaches alone is the score memorisation can produce from
noise on these datasets.

Writes results/feature_ablation.json.

    python scripts/run_feature_ablation.py
    python scripts/run_feature_ablation.py --n-per-class 20000 --seeds 42
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

from src.config import NETFLOW_V2, RESULTS
from src.features import ablation_sets
from src.metrics import decompose_gap
from src.pipeline import apply_to, fit_source


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=50_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--model", default="LightGBM")
    ap.add_argument("--scaler", default="minmax", choices=["minmax", "quantile"])
    ap.add_argument("--out", default="feature_ablation.json")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    sets = ablation_sets()
    print(f"{len(sets)} feature sets x {len(sources)} sources x {len(args.seeds)} seeds "
          f"= {len(sets) * len(sources) * len(args.seeds)} fits\n")

    rows: list[dict] = []
    t0 = time.perf_counter()
    n = 0
    for set_name, feats in sets.items():
        for src in sources:
            for seed in args.seeds:
                n += 1
                fit = fit_source(src, args.model, seed=seed, features=feats,
                                 scaler_kind=args.scaler, n_per_class=args.n_per_class)
                ext_f1, ext_auc = [], []
                per_target = {}
                for tgt in sources:
                    if tgt == src:
                        continue
                    r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                    d = decompose_gap(fit.y_test, fit.proba_test,
                                      r["y"], r["proba"], fit.threshold)
                    per_target[tgt] = {"metrics": r["external"], "decomposition": d}
                    ext_f1.append(r["external"]["macro_f1"])
                    ext_auc.append(r["external"]["roc_auc"])

                row = {
                    "feature_set": set_name, "n_features": len(feats),
                    "source": src, "seed": seed, "model": args.model,
                    "scaler": args.scaler,
                    "indomain": fit.indomain,
                    "external_mean_macro_f1": float(np.mean(ext_f1)),
                    "external_mean_auc": float(np.mean(ext_auc)),
                    "per_target": per_target,
                }
                rows.append(row)
                print(
                    f"[{n}] {set_name:24s} k={len(feats):2d} {src:20s} s{seed} | "
                    f"in {fit.indomain['macro_f1']:.4f} | "
                    f"ext {row['external_mean_macro_f1']:.4f} "
                    f"(AUC {row['external_mean_auc']:.4f})",
                    flush=True,
                )

    payload = {
        "config": {
            "model": args.model, "seeds": args.seeds, "sources": sources,
            "n_per_class": args.n_per_class, "scaler": args.scaler,
            "feature_sets": {k: v for k, v in sets.items()},
        },
        "rows": rows,
    }
    out = RESULTS / args.out
    out.write_text(json.dumps(payload, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {out} ({len(rows)} rows) in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
