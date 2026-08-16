"""
E2/E3 — how much do three preprocessing decisions move the results?

Each of these choices is defended in the methods section on principle. A reviewer is
entitled to the magnitude rather than the principle, and two of them bear directly on
claims the paper makes.

    de-duplication      The paper asserts that studies splitting these datasets without
                        removing exact duplicates test partly on rows they trained on.
                        That argument is currently theoretical. Running the pipeline with
                        de-duplication disabled measures it.
    target clipping     Target features are clipped to the range the source scaler saw.
                        Since the paper is about distribution shift, a preprocessing step
                        that truncates shifted values could plausibly create or mask the
                        effect being reported.
    contradictions      De-duplication keeps the first row of each duplicate group, so for
                        groups carrying both labels an arbitrary label survives. Excluding
                        contradictory groups entirely bounds what that choice is worth.

Writes results/preprocessing_sensitivity.json.
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

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.class_weight import compute_sample_weight

from src.config import NETFLOW_V2, RESULTS
from src.runlock import single_instance
from src.data import load
from src.metrics import best_threshold, binary_metrics
from src.pipeline import apply_to, fit_source, make_models, stratified_cap

CAP = 25_000
MODEL = "LightGBM"


def contradiction_free(X: pd.DataFrame, y: np.ndarray):
    """Drop every feature vector that appears with more than one label."""
    h = pd.util.hash_pandas_object(X, index=False).to_numpy()
    df = pd.DataFrame({"h": h, "y": y})
    bad = set(df.groupby("h")["y"].nunique().pipe(lambda s: s[s > 1]).index)
    keep = ~np.isin(h, list(bad)) if bad else np.ones(len(X), bool)
    return keep, len(bad)


def fit_raw(X, y, seed, cap):
    """Minimal source fit used by the variants that bypass the standard loader."""
    X, y, _ = stratified_cap(X, y, np.zeros(len(y), dtype=object), cap, seed)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed,
                                          stratify=y)
    sc = MinMaxScaler().fit(Xtr)
    cols = list(X.columns)
    Xtr_s = pd.DataFrame(sc.transform(Xtr), columns=cols)
    Xte_s = pd.DataFrame(sc.transform(Xte), columns=cols)
    med = Xtr_s.median()
    Xtr_s, Xte_s = Xtr_s.fillna(med), Xte_s.fillna(med)
    m = make_models(seed)[MODEL]
    m.fit(Xtr_s, ytr, sample_weight=compute_sample_weight("balanced", ytr))
    proba = m.predict_proba(Xte_s)[:, 1]
    thr = best_threshold(yte, proba)
    return m, sc, med, cols, thr, binary_metrics(yte, proba >= thr, proba)


def apply_raw(m, sc, med, cols, thr, X, y, cap, seed, clip=True):
    X, y, _ = stratified_cap(X, y, np.zeros(len(y), dtype=object), cap, seed)
    Xs = pd.DataFrame(sc.transform(X[cols]), columns=cols)
    if clip:
        Xs = Xs.clip(0.0, 1.0)
    Xs = Xs.fillna(med)
    proba = m.predict_proba(Xs)[:, 1]
    return binary_metrics(y, proba >= thr, proba)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43])
    args = ap.parse_args()
    sources = [d.key for d in NETFLOW_V2]
    rows: list[dict] = []
    t0 = time.perf_counter()

    # ---- 1. de-duplication and contradiction handling --------------------------------
    for seed in args.seeds:
        for src in sources:
            for variant in ("dedup", "no_dedup", "no_contradictions"):
                if variant == "no_contradictions":
                    X, y, _f, _r = load(src, other_policy="drop", dedup=True)
                    keep, n_bad = contradiction_free(X, y.to_numpy())
                    X, yv = X[keep].reset_index(drop=True), y.to_numpy()[keep]
                else:
                    X, y, _f, _r = load(src, other_policy="drop",
                                        dedup=(variant == "dedup"))
                    yv, n_bad = y.to_numpy(), 0
                if len(np.unique(yv)) < 2:
                    continue
                m, sc, med, cols, thr, ind = fit_raw(X, yv, seed, CAP)
                ext = []
                for tgt in sources:
                    if tgt == src:
                        continue
                    Xt, yt, _f2, _r2 = load(tgt, other_policy="drop", dedup=True)
                    e = apply_raw(m, sc, med, cols, thr, Xt, yt.to_numpy(), CAP, seed)
                    ext.append(e)
                rows.append({
                    "axis": "dedup", "variant": variant, "seed": seed, "source": src,
                    "n_rows": int(len(X)), "n_contradictory_groups_removed": n_bad,
                    "indomain_macro_f1": ind["macro_f1"], "indomain_auc": ind["roc_auc"],
                    "external_macro_f1": float(np.mean([e["macro_f1"] for e in ext])),
                    "external_auc": float(np.nanmean([e["roc_auc"] for e in ext])),
                })
                print(f"  dedup/{variant:18s} {src:20s} s{seed} | "
                      f"in {ind['macro_f1']:.4f} ext {rows[-1]['external_macro_f1']:.4f}",
                      flush=True)

    # ---- 2. target clipping ------------------------------------------------------------
    for seed in args.seeds:
        for src in sources:
            fit = fit_source(src, MODEL, seed=seed, n_per_class=CAP)
            for clip in (True, False):
                ext = [apply_to(fit, t, n_per_class=CAP, clip=clip)["external"]
                       for t in sources if t != src]
                rows.append({
                    "axis": "clipping", "variant": "clipped" if clip else "unclipped",
                    "seed": seed, "source": src,
                    "indomain_macro_f1": fit.indomain["macro_f1"],
                    "indomain_auc": fit.indomain["roc_auc"],
                    "external_macro_f1": float(np.mean([e["macro_f1"] for e in ext])),
                    "external_auc": float(np.nanmean([e["roc_auc"] for e in ext])),
                })
            print(f"  clipping {src:20s} s{seed} done", flush=True)

    # ---- summary -----------------------------------------------------------------------
    summary = {}
    print("\n" + "=" * 74)
    print(f"{'axis':12s} {'variant':20s} {'n':>3s} {'in-domain F1':>13s} "
          f"{'external F1':>12s} {'external AUC':>13s}")
    for axis in ("dedup", "clipping"):
        for variant in sorted({r["variant"] for r in rows if r["axis"] == axis}):
            rs = [r for r in rows if r["axis"] == axis and r["variant"] == variant]
            e = {k: float(np.mean([r[k] for r in rs]))
                 for k in ("indomain_macro_f1", "indomain_auc",
                           "external_macro_f1", "external_auc")}
            e["n"] = len(rs)
            summary[f"{axis}|{variant}"] = e
            print(f"{axis:12s} {variant:20s} {len(rs):3d} {e['indomain_macro_f1']:13.4f} "
                  f"{e['external_macro_f1']:12.4f} {e['external_auc']:13.4f}")

    d = summary.get("dedup|dedup", {})
    nd = summary.get("dedup|no_dedup", {})
    if d and nd:
        print(f"\nSkipping de-duplication inflates in-domain macro-F1 by "
              f"{nd['indomain_macro_f1'] - d['indomain_macro_f1']:+.4f} and external by "
              f"{nd['external_macro_f1'] - d['external_macro_f1']:+.4f}.")

    (RESULTS / "preprocessing_sensitivity.json").write_text(
        json.dumps({"config": vars(args), "rows": rows, "summary": summary},
                   indent=1, default=float), encoding="utf-8")
    print(f"\nwrote preprocessing_sensitivity.json ({len(rows)} rows) "
          f"in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    with single_instance("preprocessing_sensitivity"):
        raise SystemExit(main())
