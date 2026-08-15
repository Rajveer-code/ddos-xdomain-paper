"""
Controls establishing that below-chance transfer is structured inversion, not an artefact.

The paper's central claim is that some transfers produce a systematically reversed
ranking. Three things could produce a sub-0.5 AUC without that being true: a pipeline bug
that flips labels somewhere, ordinary noise around 0.5 in small or degenerate evaluations,
or an evaluation quirk of one model family. Each gets a control.

    permutation   Source labels are shuffled before training. A pipeline that manufactures
                  below-chance AUC will still do so; a correct one lands at 0.5 with no
                  systematic sign.
    reversal      Source labels are inverted before training. External AUC should land near
                  1 - AUC of the original run, confirming the sign is carried by the
                  learned relationship rather than by the evaluation.
    separation    Mean target score for attack minus for benign. Under inversion this is
                  negative, which states the phenomenon directly in score space rather
                  than through a rank statistic.
    negation      For every below-chance transfer, 1 - AUC, i.e. what the same detector
                  would score with its output negated. Reported as a distribution.

Writes results/inversion_controls.json.
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

from sklearn.metrics import roc_auc_score

from src.config import NETFLOW_V2, RESULTS
from src.pipeline import apply_to, fit_source

MODELS = ["LightGBM", "XGBoost", "RandomForest", "LogisticRegression"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=25_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--models", nargs="*", default=MODELS)
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    rows: list[dict] = []
    t0 = time.perf_counter()

    for mode in ("normal", "permuted", "reversed"):
        for model in args.models:
            # Only the primary model needs the controls; the others establish that the
            # phenomenon is not specific to one family, which needs the normal mode only.
            if mode != "normal" and model != "LightGBM":
                continue
            for seed in args.seeds:
                for src in sources:
                    fit = fit_source(src, model, seed=seed,
                                     n_per_class=args.n_per_class, label_mode=mode)
                    for tgt in sources:
                        if tgt == src:
                            continue
                        r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                        y, p = r["y"], r["proba"]
                        if len(np.unique(y)) < 2:
                            continue
                        auc = roc_auc_score(y, p)
                        sep = float(p[y == 1].mean() - p[y == 0].mean())
                        rows.append({
                            "mode": mode, "model": model, "seed": seed,
                            "source": src, "target": tgt,
                            "external_auc": float(auc),
                            "auc_if_negated": float(1.0 - auc),
                            "score_separation": sep,
                            "below_chance": bool(auc < 0.5),
                        })
                    print(f"  {mode:9s} {model:20s} {src:20s} s{seed} done", flush=True)

    (RESULTS / "inversion_controls.json").write_text(
        json.dumps({"config": vars(args), "rows": rows}, indent=1, default=float),
        encoding="utf-8")

    def summarise(sel, label):
        a = np.array([r["external_auc"] for r in sel])
        if not len(a):
            return
        below = (a < 0.5).mean()
        print(f"{label:28s} n={len(a):3d}  mean AUC {a.mean():.4f}  "
              f"median {np.median(a):.4f}  below-chance {below:6.1%}")

    print("\n" + "=" * 78)
    summarise([r for r in rows if r["mode"] == "normal" and r["model"] == "LightGBM"],
              "normal (LightGBM)")
    summarise([r for r in rows if r["mode"] == "permuted"], "permuted source labels")
    summarise([r for r in rows if r["mode"] == "reversed"], "reversed source labels")
    print()
    for m in args.models:
        summarise([r for r in rows if r["mode"] == "normal" and r["model"] == m],
                  f"normal ({m})")

    # reversal check: reversed-label AUC should mirror the normal run
    norm = {(r["source"], r["target"], r["seed"]): r["external_auc"]
            for r in rows if r["mode"] == "normal" and r["model"] == "LightGBM"}
    diffs = [abs((1 - r["external_auc"]) - norm[(r["source"], r["target"], r["seed"])])
             for r in rows if r["mode"] == "reversed"
             if (r["source"], r["target"], r["seed"]) in norm]
    if diffs:
        print(f"\nreversal mirror check: mean |(1-AUC_reversed) - AUC_normal| = "
              f"{np.mean(diffs):.4f} (0 = perfect mirror)")

    inv = [r for r in rows if r["mode"] == "normal" and r["below_chance"]]
    if inv:
        neg = np.array([r["auc_if_negated"] for r in inv])
        sep = np.array([r["score_separation"] for r in inv])
        print(f"below-chance transfers: n={len(inv)}, negated AUC median {np.median(neg):.4f} "
              f"[{neg.min():.4f}, {neg.max():.4f}], score separation median {np.median(sep):+.4f}")
    print(f"\ndone in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
