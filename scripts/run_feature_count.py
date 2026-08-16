"""
Does feature-set *size* predict transferability, independently of which features?

The manuscript currently claims a size effect from the semantic ablation: the smallest
sets transfer best, and a one-feature set beats all 39. That design confounds the two
things it needs to separate. A one-bit DNS indicator and a four-feature throughput block
differ in identity as well as in dimensionality, so the observed ordering is equally
consistent with "fewer features transfer better" and with "those particular features
transfer better".

This samples random subsets at controlled k, holding splits, seeds, model and targets
fixed. If external performance declines with k across randomly chosen subsets, the size
effect is real. If it does not, the earlier result was about feature identity, and the
manuscript's mechanism paragraph has to be rewritten.

Checkpointed: completed (seed, source, k, subset) units are flushed as they finish and
skipped on resume.

Writes results/feature_count_random.json.
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

from src.config import NETFLOW_V2, RESULTS
from src.features import all_features
from src.pipeline import apply_to, fit_source

K_GRID = [1, 2, 3, 5, 7, 10, 15, 20, 30, 39]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=25_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43])
    ap.add_argument("--subsets", type=int, default=8, help="random subsets per k")
    ap.add_argument("--model", default="LightGBM")
    ap.add_argument("--out", default="feature_count_random.json")
    args = ap.parse_args()

    feats = all_features()
    sources = [d.key for d in NETFLOW_V2]
    out_path = RESULTS / args.out
    t0 = time.perf_counter()

    rows: list[dict] = []
    done: set[tuple] = set()
    if out_path.exists():
        try:
            rows = json.loads(out_path.read_text(encoding="utf-8"))["rows"]
            done = {(r["seed"], r["source"], r["k"], r["subset"]) for r in rows}
            print(f"resuming: {len(done)} units complete")
        except (json.JSONDecodeError, KeyError):
            rows, done = [], set()

    def flush():
        out_path.write_text(json.dumps(
            {"config": {**vars(args), "k_grid": K_GRID, "n_features_total": len(feats)},
             "rows": rows}, indent=1, default=float), encoding="utf-8")

    total = len(args.seeds) * len(sources) * sum(
        1 if k >= len(feats) else args.subsets for k in K_GRID)
    n = 0
    for seed in args.seeds:
        for src in sources:
            for k in K_GRID:
                # k = 39 is the full set: one subset only, since there is just one.
                n_subsets = 1 if k >= len(feats) else args.subsets
                for si in range(n_subsets):
                    n += 1
                    if (seed, src, k, si) in done:
                        continue
                    rng = np.random.default_rng(seed * 10_000 + k * 100 + si)
                    sub = (list(feats) if k >= len(feats)
                           else [str(f) for f in rng.choice(feats, k, replace=False)])
                    fit = fit_source(src, args.model, seed=seed, features=sub,
                                     n_per_class=args.n_per_class)
                    ext_f1, ext_auc = [], []
                    for tgt in sources:
                        if tgt == src:
                            continue
                        r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                        ext_f1.append(r["external"]["macro_f1"])
                        ext_auc.append(r["external"]["roc_auc"])
                    rows.append({
                        "seed": seed, "source": src, "k": k, "subset": si,
                        "features": sub,
                        "indomain_macro_f1": fit.indomain["macro_f1"],
                        "indomain_auc": fit.indomain["roc_auc"],
                        "external_macro_f1": float(np.mean(ext_f1)),
                        "external_auc": float(np.nanmean(ext_auc)),
                    })
                    done.add((seed, src, k, si))
                    flush()
                    print(f"[{n}/{total}] {src:20s} s{seed} k={k:2d} #{si} | "
                          f"in {fit.indomain['macro_f1']:.4f} "
                          f"ext {rows[-1]['external_macro_f1']:.4f} "
                          f"AUC {rows[-1]['external_auc']:.4f}", flush=True)

    flush()
    print(f"\nwrote {out_path} ({len(rows)} rows) in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
