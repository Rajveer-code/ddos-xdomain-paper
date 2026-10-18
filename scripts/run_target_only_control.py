"""
Target-only control for the label-budget experiment (manuscript §4.12).

The label-budget result says that retraining on the source plus k balanced labelled target
flows recovers most of the transfer gap. That credits the *source* only if a model trained
on the same k target flows alone does worse. This script measures that model.

It reproduces run_label_budget.py's design exactly, without training any source model:
the same stratified cap (n_per_class, seed), the same disjoint adaptation pool / evaluation
split (train_test_split, train_size=0.5, random_state=seed, stratified), and the same
balanced label draws (rng seeded seed * 1000 + draw). The pool, the draws and the evaluation
set depend only on (target, seed), so each target-only score applies to every source paired
with that target, and is compared draw-for-draw with label_budget_v2.json.

Three target-only learners, so the control is not decided by one model's small-sample
behaviour:
    lgbm   the LightGBM configuration used everywhere else (unchanged; with very few rows
           its minimum-leaf-size default limits splitting, which is part of what it measures)
    logreg logistic regression, class-balanced, on log1p features standardised on the k flows
    nn1    1-nearest-neighbour on the same transformed features (hard labels)
LightGBM and logistic regression take their threshold on the k labelled flows with the same
best_threshold rule as the fine-tune arm.

Writes results/label_budget_target_only.json.

    python scripts/run_target_only_control.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

from src.config import NETFLOW_V2, RESULTS
from src.data import netflow_common_features
from src.metrics import best_threshold
from src.pipeline import get_domain, make_models, stratified_cap

K_BUDGETS = [10, 50, 100, 500, 1000]
ADAPT_FRACTION = 0.5
ARMS = ["lgbm", "logreg", "nn1"]
MACRO_F1 = lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0)


def draw_labels(y_pool: np.ndarray, k: int, rng) -> np.ndarray:
    """Identical to run_label_budget.draw_labels: k/2 per class from the pool."""
    per = max(k // 2, 1)
    idx = []
    for c in (0, 1):
        pool = np.flatnonzero(y_pool == c)
        if len(pool) == 0:
            continue
        idx.append(rng.choice(pool, min(per, len(pool)), replace=False))
    return np.concatenate(idx) if idx else np.array([], dtype=int)


def small_sample_prep():
    # log1p tames the 1e300-scale rate artefacts (§3.4); all NetFlow v2 features are >= 0.
    return [SimpleImputer(strategy="median"),
            FunctionTransformer(lambda a: np.log1p(np.clip(a, 0, None))),
            StandardScaler()]


def score_arms(Xk, yk, X_eval, y_eval, seed: int) -> dict[str, float]:
    out = {}
    lgbm = make_models(seed)["LightGBM"]
    lgbm.fit(Xk, yk, sample_weight=compute_sample_weight("balanced", yk))
    thr = best_threshold(yk, lgbm.predict_proba(Xk)[:, 1])
    out["lgbm"] = MACRO_F1(y_eval, lgbm.predict_proba(X_eval)[:, 1] >= thr)

    lr = make_pipeline(*small_sample_prep(),
                       LogisticRegression(max_iter=2000, class_weight="balanced"))
    lr.fit(Xk, yk)
    thr = best_threshold(yk, lr.predict_proba(Xk)[:, 1])
    out["logreg"] = MACRO_F1(y_eval, lr.predict_proba(X_eval)[:, 1] >= thr)

    nn = make_pipeline(*small_sample_prep(), KNeighborsClassifier(n_neighbors=1))
    nn.fit(Xk, yk)
    out["nn1"] = MACRO_F1(y_eval, nn.predict(X_eval))
    return out


def summarize(rows: list[dict], budget_rows: list[dict]) -> dict:
    """Pair each source+k score with the target-only score from the same (target, seed, k, draw)."""
    to = {(r["target"], r["seed"], r["k"], r["draw"]): r for r in rows}
    per_k: dict[str, dict] = {}
    by_k = defaultdict(list)
    for b in budget_rows:
        if b["k"] == 0:
            continue
        t = to.get((b["target"], b["seed"], b["k"], b["draw"]))
        if t is not None:
            by_k[b["k"]].append((b, t))
    for k, pairs in sorted(by_k.items()):
        ft = np.array([b["f1_finetune"] for b, _ in pairs])
        entry = {"n": len(pairs), "source_plus_k_median": float(np.median(ft))}
        for arm in ARMS:
            v = np.array([t[f"f1_{arm}"] for _, t in pairs])
            diff = ft - v
            entry[arm] = {
                "median": float(np.median(v)), "p5": float(np.percentile(v, 5)),
                "p95": float(np.percentile(v, 95)), "mean": float(v.mean()),
                "median_paired_source_benefit": float(np.median(diff)),
                "share_source_plus_k_better": float((diff > 0).mean()),
            }
        best = np.array([max(t[f"f1_{a}"] for a in ARMS) for _, t in pairs])
        diff = ft - best
        entry["best_of_three"] = {
            "median": float(np.median(best)),
            "median_paired_source_benefit": float(np.median(diff)),
            "share_source_plus_k_better": float((diff > 0).mean()),
        }
        per_k[str(k)] = entry
    return per_k


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=25_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43])
    ap.add_argument("--draws", type=int, default=10)
    ap.add_argument("--budget-file", default="label_budget_v2.json")
    ap.add_argument("--out", default="label_budget_target_only.json")
    args = ap.parse_args()

    budget = json.loads((RESULTS / args.budget_file).read_text(encoding="utf-8"))
    bcfg = budget["config"]
    assert (bcfg["n_per_class"], bcfg["seeds"], bcfg["draws"]) == (
        args.n_per_class, args.seeds, args.draws), "settings must match the label-budget run"
    # n_pool / n_eval per (target, seed) recorded by the label-budget run, for a split check.
    recorded = {(r["target"], r["seed"]): (r["n_pool"], r["n_eval"])
                for r in budget["rows"] if r["k"] == 0}

    features = netflow_common_features()
    rows: list[dict] = []
    t0 = time.perf_counter()
    for seed in args.seeds:
        for tgt in [d.key for d in NETFLOW_V2]:
            dom = get_domain(tgt)
            Xt, y_all, _ = stratified_cap(dom.X, dom.y, dom.fam, args.n_per_class, seed)
            Xt = Xt[features].reset_index(drop=True)
            pool_i, eval_i = train_test_split(
                np.arange(len(y_all)), train_size=ADAPT_FRACTION,
                random_state=seed, stratify=y_all)
            assert recorded[(tgt, seed)] == (len(pool_i), len(eval_i)), \
                f"split differs from label-budget run for {tgt} seed {seed}"
            y_pool, y_eval = y_all[pool_i], y_all[eval_i]
            X_eval = Xt.iloc[eval_i]
            for k in K_BUDGETS:
                for d in range(args.draws):
                    rng = np.random.default_rng(seed * 1000 + d)
                    sel = draw_labels(y_pool, k, rng)
                    if len(sel) == 0 or len(np.unique(y_pool[sel])) < 2:
                        continue
                    g = pool_i[sel]
                    f1 = score_arms(Xt.iloc[g], y_all[g], X_eval, y_eval, seed)
                    rows.append({"target": tgt, "seed": seed, "k": k, "draw": d,
                                 **{f"f1_{a}": v for a, v in f1.items()},
                                 "n_labels_used": int(len(sel))})
            print(f"{tgt:20s} s{seed} done ({(time.perf_counter() - t0) / 60:.1f} min)", flush=True)

    per_k = summarize(rows, budget["rows"])
    payload = {"config": {**vars(args), "adapt_fraction": ADAPT_FRACTION, "arms": ARMS,
                          "label_composition": "balanced, k/2 per class",
                          "features": "39 shared NetFlow v2, raw for lgbm, "
                                      "median-impute + log1p + standardise for logreg/nn1"},
               "per_k": per_k, "rows": rows}
    (RESULTS / args.out).write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"\n{'k':>5} {'src+k':>7} " + " ".join(f"{a:>8}" for a in ARMS) + "  share src+k > best-of-3")
    for k, e in per_k.items():
        print(f"{k:>5} {e['source_plus_k_median']:7.4f} "
              + " ".join(f"{e[a]['median']:8.4f}" for a in ARMS)
              + f"  {e['best_of_three']['share_source_plus_k_better']:.2f}")
    print(f"wrote results/{args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
