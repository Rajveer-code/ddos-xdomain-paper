"""
B4, rebuilt: how many labelled target flows are needed, measured without leakage.

The first implementation of this experiment drew k labelled target flows, fine-tuned on
them, and then evaluated on the whole target set, which still contained those same k rows.
The threshold was tuned on them too. At k=1000 against a 100k target that is roughly 1%
contamination, small but indefensible, and it inflates exactly the number the paper leans
on hardest.

Here the target is split once per (pair, seed) into a disjoint adaptation pool and
evaluation set. Labels are drawn only from the pool; every score is computed only on the
evaluation set. The zero-label baselines are evaluated on the same evaluation set so the
comparison is like for like.

Sampling variance at k=10 is the dominant uncertainty, so each budget is repeated over
N_DRAWS independent label draws and reported as a median with a percentile interval
rather than a single mean.

Writes results/label_budget_v2.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight

from src.config import NETFLOW_V2, RESULTS
from src.metrics import benign_quantile_threshold, best_threshold
from src.pipeline import apply_to, fit_source, get_domain, make_models, stratified_cap

K_BUDGETS = [0, 10, 50, 100, 500, 1000]
N_DRAWS = 20
ADAPT_FRACTION = 0.5
MACRO_F1 = lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0)


def draw_labels(y_pool: np.ndarray, k: int, rng) -> np.ndarray:
    """
    Balanced draw of k labelled flows from the adaptation pool.

    Balanced rather than prevalence-proportional: at a 1.3% base rate a random draw of ten
    flows usually contains no attack at all, which measures the base rate rather than the
    value of supervision. The composition is stated so the result is not read as ten
    arbitrary labels.
    """
    per = max(k // 2, 1)
    idx = []
    for c in (0, 1):
        pool = np.flatnonzero(y_pool == c)
        if len(pool) == 0:
            continue
        idx.append(rng.choice(pool, min(per, len(pool)), replace=False))
    return np.concatenate(idx) if idx else np.array([], dtype=int)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=50_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    ap.add_argument("--model", default="LightGBM")
    ap.add_argument("--out", default="label_budget_v2.json")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    rows: list[dict] = []
    t0 = time.perf_counter()

    for seed in args.seeds:
        for src in sources:
            fit = fit_source(src, args.model, seed=seed, n_per_class=args.n_per_class)
            dom_s = get_domain(src)
            Xs_c, ys_c, _ = stratified_cap(dom_s.X, dom_s.y, dom_s.fam,
                                           args.n_per_class, seed)
            Xtr_s = pd.DataFrame(fit.scaler.transform(Xs_c[fit.features]),
                                 columns=fit.features).clip(0, 1).fillna(fit._median)

            for tgt in sources:
                if tgt == src:
                    continue
                r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                y_all, p_all = r["y"], r["proba"]

                dom_t = get_domain(tgt)
                Xt, yt_all, _ = stratified_cap(dom_t.X, dom_t.y, dom_t.fam,
                                               args.n_per_class, seed)
                Xt_s = pd.DataFrame(fit.scaler.transform(Xt[fit.features]),
                                    columns=fit.features).clip(0, 1).fillna(fit._median)

                # One disjoint split per (pair, seed). Everything below respects it.
                pool_i, eval_i = train_test_split(
                    np.arange(len(y_all)), train_size=ADAPT_FRACTION,
                    random_state=seed, stratify=y_all)
                y_pool, y_eval = y_all[pool_i], y_all[eval_i]
                p_eval = p_all[eval_i]
                Xt_eval = Xt_s.iloc[eval_i]

                # ---- zero-label references, on the evaluation set only ----------------
                f1_src = MACRO_F1(y_eval, p_eval >= fit.threshold)
                thr_bq = benign_quantile_threshold(p_all[pool_i][y_pool == 0],
                                                   target_fpr=0.01)
                f1_bq = MACRO_F1(y_eval, p_eval >= thr_bq)
                f1_oracle = MACRO_F1(y_eval, p_eval >= best_threshold(y_eval, p_eval))
                auc_eval = (roc_auc_score(y_eval, p_eval)
                            if len(np.unique(y_eval)) > 1 else float("nan"))

                for k in K_BUDGETS:
                    if k == 0:
                        rows.append({
                            "source": src, "target": tgt, "seed": seed, "k": 0, "draw": 0,
                            "f1_rethreshold": f1_src, "f1_finetune": f1_src,
                            "f1_source_threshold": f1_src, "f1_benign_quantile": f1_bq,
                            "f1_oracle": f1_oracle, "external_auc": auc_eval,
                            "n_eval": int(len(y_eval)), "n_pool": int(len(y_pool)),
                        })
                        continue

                    for d in range(args.draws):
                        rng = np.random.default_rng(seed * 1000 + d)
                        sel = draw_labels(y_pool, k, rng)
                        if len(sel) == 0 or len(np.unique(y_pool[sel])) < 2:
                            continue
                        g = pool_i[sel]                 # indices into the full target
                        yk = y_all[g]

                        # (a) re-tune the threshold on the k labels, evaluate on eval set
                        thr_k = best_threshold(yk, p_all[g])
                        f1_re = MACRO_F1(y_eval, p_eval >= thr_k)

                        # (b) retrain on source-train plus the k labels, evaluate on eval
                        X_aug = pd.concat([Xtr_s, Xt_s.iloc[g]], ignore_index=True)
                        y_aug = np.concatenate([ys_c, yk])
                        m2 = make_models(seed)[args.model]
                        m2.fit(X_aug, y_aug,
                               sample_weight=compute_sample_weight("balanced", y_aug))
                        p_ft_lab = m2.predict_proba(Xt_s.iloc[g])[:, 1]
                        thr_ft = best_threshold(yk, p_ft_lab)
                        p_ft_eval = m2.predict_proba(Xt_eval)[:, 1]
                        f1_ft = MACRO_F1(y_eval, p_ft_eval >= thr_ft)

                        rows.append({
                            "source": src, "target": tgt, "seed": seed, "k": k, "draw": d,
                            "f1_rethreshold": f1_re, "f1_finetune": f1_ft,
                            "f1_source_threshold": f1_src, "f1_benign_quantile": f1_bq,
                            "f1_oracle": f1_oracle, "external_auc": auc_eval,
                            "n_eval": int(len(y_eval)), "n_pool": int(len(y_pool)),
                            "n_labels_used": int(len(sel)),
                        })

                print(f"{src:20s} -> {tgt:20s} s{seed} | eval n={len(y_eval):,} "
                      f"AUC {auc_eval:.3f} | src-thr {f1_src:.4f} benign-q {f1_bq:.4f} "
                      f"oracle {f1_oracle:.4f}", flush=True)

    payload = {"config": {**vars(args), "adapt_fraction": ADAPT_FRACTION,
                          "label_composition": "balanced, k/2 per class"},
               "rows": rows}
    (RESULTS / args.out).write_text(json.dumps(payload, indent=1, default=float),
                                    encoding="utf-8")

    agg = defaultdict(lambda: defaultdict(list))
    for r in rows:
        agg[r["k"]]["re"].append(r["f1_rethreshold"])
        agg[r["k"]]["ft"].append(r["f1_finetune"])
    print(f"\n{'k':>6s} {'re-threshold median [5,95]':>34s} {'fine-tune median [5,95]':>34s}")
    for k in sorted(agg):
        a, b = np.array(agg[k]["re"]), np.array(agg[k]["ft"])
        print(f"{k:6d}   {np.median(a):.4f} [{np.percentile(a,5):.4f}, {np.percentile(a,95):.4f}]"
              f"        {np.median(b):.4f} [{np.percentile(b,5):.4f}, {np.percentile(b,95):.4f}]")
    print(f"\nwrote {RESULTS / args.out} ({len(rows)} rows) "
          f"in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
