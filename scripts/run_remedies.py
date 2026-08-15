"""
B3 + B4 — given that transfer fails, what actually fixes it?

F1 established that 11 of 12 pairs fail representationally rather than operationally, so
the honest expectation here is that recalibration helps little. This script measures how
little, and how many labels are needed instead.

Remedies evaluated, in increasing order of what they demand from an operator:

    source_threshold      0 target labels   the deployed baseline
    benign_quantile       0 target labels   threshold from target benign-traffic quantiles
    coral                 0 target labels   align target covariance to source, then apply
    k_labels              k target labels   re-tune the threshold on k labelled flows
    k_labels_finetune     k target labels   retrain on source plus k labelled target flows
    oracle_threshold      all target labels the unreachable ceiling for threshold-only fixes

Calibration (ECE, Brier) is reported in both domains, because a detector deploys a
threshold and not a ranking.

Writes results/calibration.json and results/label_budget.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sklearn.metrics import f1_score
from sklearn.utils.class_weight import compute_sample_weight

from src.config import NETFLOW_V2, RESULTS
from src.metrics import (
    benign_quantile_threshold,
    best_threshold,
    binary_metrics,
    expected_calibration_error,
)
from src.pipeline import apply_to, fit_source, get_domain, make_models, stratified_cap

K_BUDGETS = [0, 10, 50, 100, 500, 1000]
MACRO_F1 = lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0)


def coral_transform(Xs: np.ndarray, Xt: np.ndarray) -> np.ndarray:
    """
    CORAL (Sun et al., 2016): whiten the target covariance, recolour it with the source's.

    Needs no labels from either domain. Included as the standard zero-label domain
    adaptation baseline; the point is not novelty but whether it recovers anything here.
    """
    eps = 1e-6
    ms, mt = Xs.mean(0), Xt.mean(0)
    Cs = np.cov(Xs - ms, rowvar=False) + eps * np.eye(Xs.shape[1])
    Ct = np.cov(Xt - mt, rowvar=False) + eps * np.eye(Xt.shape[1])

    def _pow(C, p):
        w, V = np.linalg.eigh(C)
        return V @ np.diag(np.maximum(w, eps) ** p) @ V.T

    return ((Xt - mt) @ _pow(Ct, -0.5) @ _pow(Cs, 0.5)) + ms


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=50_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--model", default="LightGBM")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    calib_rows: list[dict] = []
    budget_rows: list[dict] = []
    t0 = time.perf_counter()

    for seed in args.seeds:
        for src in sources:
            fit = fit_source(src, args.model, seed=seed, n_per_class=args.n_per_class)
            pred_in = fit.proba_test >= fit.threshold
            in_metrics = binary_metrics(fit.y_test, pred_in, fit.proba_test)

            for tgt in sources:
                if tgt == src:
                    continue
                r = apply_to(fit, tgt, n_per_class=args.n_per_class)
                y_ex, p_ex = r["y"], r["proba"]

                # ---------------------------------------------------------- B3 calibration
                f1_source_thr = MACRO_F1(y_ex, p_ex >= fit.threshold)
                thr_oracle = best_threshold(y_ex, p_ex)
                f1_oracle = MACRO_F1(y_ex, p_ex >= thr_oracle)

                # Zero-label remedy: the operator has traffic they believe is benign.
                benign_scores = p_ex[y_ex == 0]
                thr_bq = benign_quantile_threshold(benign_scores, target_fpr=0.01)
                f1_bq = MACRO_F1(y_ex, p_ex >= thr_bq)

                calib_rows.append({
                    "source": src, "target": tgt, "seed": seed, "model": args.model,
                    "ece_in": in_metrics["ece"], "brier_in": in_metrics["brier"],
                    "ece_external": r["external"]["ece"],
                    "brier_external": r["external"]["brier"],
                    "auc_external": r["external"]["roc_auc"],
                    "f1_source_threshold": f1_source_thr,
                    "f1_benign_quantile": f1_bq,
                    "f1_oracle_threshold": f1_oracle,
                    "recovered_by_benign_quantile": f1_bq - f1_source_thr,
                    "recoverable_by_threshold_at_all": f1_oracle - f1_source_thr,
                    "threshold_source": fit.threshold,
                    "threshold_benign_quantile": thr_bq,
                    "threshold_oracle": thr_oracle,
                })

                # ------------------------------------------------------------- CORAL (0 labels)
                dom_t = get_domain(tgt)
                Xt, yt_all, _ = stratified_cap(dom_t.X, dom_t.y, dom_t.fam,
                                               args.n_per_class, seed)
                Xt = Xt[fit.features]
                Xt_s = pd.DataFrame(fit.scaler.transform(Xt),
                                    columns=fit.features).clip(0, 1).fillna(fit._median)
                dom_s = get_domain(src)
                Xs_c, ys_c, _ = stratified_cap(dom_s.X, dom_s.y, dom_s.fam,
                                               args.n_per_class, seed)
                Xs_s = pd.DataFrame(fit.scaler.transform(Xs_c[fit.features]),
                                    columns=fit.features).clip(0, 1).fillna(fit._median)
                Xt_coral = coral_transform(Xs_s.to_numpy(np.float64),
                                           Xt_s.to_numpy(np.float64))
                p_coral = fit.model.predict_proba(
                    pd.DataFrame(Xt_coral, columns=fit.features))[:, 1]
                f1_coral = MACRO_F1(yt_all, p_coral >= fit.threshold)

                # ------------------------------------------------------- B4 label budget
                rng = np.random.default_rng(seed)
                for k in K_BUDGETS:
                    if k == 0:
                        budget_rows.append({
                            "source": src, "target": tgt, "seed": seed, "k": 0,
                            "f1_rethreshold": f1_source_thr,
                            "f1_finetune": f1_source_thr,
                            "f1_benign_quantile": f1_bq,
                            "f1_coral": f1_coral,
                        })
                        continue

                    # Stratified draw of k labelled target flows.
                    idx = np.concatenate([
                        rng.choice(np.flatnonzero(yt_all == c),
                                   min(max(k // 2, 1), int((yt_all == c).sum())),
                                   replace=False)
                        for c in (0, 1)
                    ])
                    yk = yt_all[idx]
                    # apply_to caps with the same seed and cap, so p_ex is row-aligned
                    # with yt_all and idx indexes both.
                    pk = p_ex[idx]

                    thr_k = best_threshold(yk, pk) if len(np.unique(yk)) > 1 else fit.threshold
                    f1_k = MACRO_F1(yt_all, p_ex >= thr_k)

                    # Retrain on source-train plus the k labelled target flows.
                    Xtr_s = pd.DataFrame(
                        fit.scaler.transform(Xs_c[fit.features]),
                        columns=fit.features).clip(0, 1).fillna(fit._median)
                    X_aug = pd.concat([Xtr_s, Xt_s.iloc[idx]], ignore_index=True)
                    y_aug = np.concatenate([ys_c, yk])
                    m2 = make_models(seed)[args.model]
                    m2.fit(X_aug, y_aug,
                           sample_weight=compute_sample_weight("balanced", y_aug))
                    p_ft = m2.predict_proba(Xt_s)[:, 1]
                    f1_ft = MACRO_F1(yt_all, p_ft >= best_threshold(yk,
                                     m2.predict_proba(Xt_s.iloc[idx])[:, 1]))

                    budget_rows.append({
                        "source": src, "target": tgt, "seed": seed, "k": k,
                        "f1_rethreshold": f1_k, "f1_finetune": f1_ft,
                        "f1_benign_quantile": f1_bq, "f1_coral": f1_coral,
                    })

                print(f"{src:20s} -> {tgt:20s} s{seed} | src-thr {f1_source_thr:.4f} "
                      f"benign-q {f1_bq:.4f} CORAL {f1_coral:.4f} "
                      f"oracle {f1_oracle:.4f} | ECE {r['external']['ece']:.4f}",
                      flush=True)

    for name, rows in [("calibration", calib_rows), ("label_budget", budget_rows)]:
        (RESULTS / f"{name}.json").write_text(
            json.dumps({"config": vars(args), "rows": rows}, indent=1, default=float),
            encoding="utf-8")
        print(f"wrote {RESULTS / f'{name}.json'} ({len(rows)} rows)")
    print(f"done in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
