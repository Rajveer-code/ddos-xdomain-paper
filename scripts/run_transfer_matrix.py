"""
The full ordered transfer matrix over the NetFlow v2 quartet.

For every (source, model, seed) the model is fitted once and then applied to the source's
own held-out split and to all three other domains. Each ordered pair records:

* in-domain and external metrics at the source-tuned threshold;
* the ranking/threshold decomposition, which says *how* the pair failed;
* per-attack-family recall, because dataset-level numbers hide the mechanism;
* a paired bootstrap CI and p-value on the gap itself (primary model only, for cost).

Writes results/transfer_matrix.json.

    python scripts/run_transfer_matrix.py
    python scripts/run_transfer_matrix.py --n-per-class 20000 --seeds 42 --models LightGBM
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

from src.config import NETFLOW_V2, RESULTS, SEEDS
from src.metrics import decompose_gap, fpr_at_tpr, paired_gap_ci
from src.pipeline import apply_to, fit_source

PRIMARY_MODEL = "LightGBM"
ALL_MODELS = ["LightGBM", "XGBoost", "RandomForest", "LogisticRegression"]


def family_recall(y: np.ndarray, pred: np.ndarray, fam: np.ndarray) -> dict[str, dict]:
    """Recall per attack family, plus the benign-side false positive rate."""
    out: dict[str, dict] = {}
    for f in np.unique(fam):
        m = fam == f
        if not m.any():
            continue
        if f == "benign":
            out[f] = {"n": int(m.sum()), "fpr": float(pred[m].mean())}
        else:
            out[f] = {"n": int(m.sum()), "recall": float(pred[m].mean())}
    return out


def run(sources: list[str], models: list[str], seeds: list[int],
        n_per_class: int | None, boot: int) -> list[dict]:
    rows: list[dict] = []
    total = len(sources) * len(models) * len(seeds)
    done = 0
    t_start = time.perf_counter()

    for src in sources:
        for model_name in models:
            for seed in seeds:
                done += 1
                fit = fit_source(src, model_name, seed=seed, n_per_class=n_per_class)
                pred_in = fit.proba_test >= fit.threshold
                print(
                    f"[{done}/{total}] {src} | {model_name} | seed {seed} | "
                    f"in-domain macro-F1 {fit.indomain['macro_f1']:.4f} "
                    f"AUC {fit.indomain['roc_auc']:.4f} thr {fit.threshold:.4f} "
                    f"({fit.train_seconds:.1f}s)",
                    flush=True,
                )

                # The source's own held-out split is the in-domain reference row.
                rows.append({
                    "source": src, "target": src, "kind": "in_domain",
                    "model": model_name, "seed": seed,
                    "n": fit.n_test, "threshold": fit.threshold,
                    "metrics": fit.indomain,
                    "family": family_recall(fit.y_test, pred_in, fit.fam_test),
                    "fpr_at_95tpr": fpr_at_tpr(fit.y_test, fit.proba_test, 0.95),
                    "train_seconds": fit.train_seconds,
                })

                for tgt in sources:
                    if tgt == src:
                        continue
                    r = apply_to(fit, tgt, n_per_class=n_per_class)
                    y_ex, p_ex, fam_ex = r["y"], r["proba"], r["fam"]
                    pred_ex = p_ex >= fit.threshold

                    row = {
                        "source": src, "target": tgt, "kind": "external",
                        "model": model_name, "seed": seed,
                        "n": r["n_target"],
                        "target_base_rate": r["target_base_rate"],
                        "rows_outside_train_range": r["rows_outside_train_range"],
                        "threshold": fit.threshold,
                        "metrics": r["external"],
                        "family": family_recall(y_ex, pred_ex, fam_ex),
                        "fpr_at_95tpr": fpr_at_tpr(y_ex, p_ex, 0.95),
                        "decomposition": decompose_gap(
                            fit.y_test, fit.proba_test, y_ex, p_ex, fit.threshold),
                    }

                    # The paired CI is the expensive part; run it for the primary model.
                    if model_name == PRIMARY_MODEL:
                        row["gap_stats"] = paired_gap_ci(
                            fit.y_test, pred_in, y_ex, pred_ex,
                            n_boot=boot, seed=seed)

                    d = row["decomposition"]
                    print(
                        f"      -> {tgt:20s} macro-F1 {r['external']['macro_f1']:.4f} "
                        f"MCC {r['external']['mcc']:+.4f} AUC {r['external']['roc_auc']:.4f} "
                        f"| ranking_loss {d['ranking_loss']:+.4f} "
                        f"threshold_loss {d['threshold_loss']:+.4f}",
                        flush=True,
                    )
                    rows.append(row)

    print(f"\nmatrix complete in {(time.perf_counter() - t_start) / 60:.1f} min")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=100_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=list(SEEDS))
    ap.add_argument("--models", nargs="*", default=ALL_MODELS)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--out", default="transfer_matrix.json")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    print(f"sources={sources}\nmodels={args.models}\nseeds={args.seeds}\n"
          f"n_per_class={args.n_per_class}\n")

    rows = run(sources, args.models, args.seeds, args.n_per_class, args.boot)

    payload = {
        "config": {
            "sources": sources, "models": args.models, "seeds": args.seeds,
            "n_per_class": args.n_per_class, "n_boot": args.boot,
            "feature_space": "netflow_v2_shared_39",
            "other_policy": "drop", "scaler": "minmax", "clip": True,
        },
        "rows": rows,
    }
    out = RESULTS / args.out
    out.write_text(json.dumps(payload, indent=1, default=float), encoding="utf-8")
    print(f"wrote {out}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
