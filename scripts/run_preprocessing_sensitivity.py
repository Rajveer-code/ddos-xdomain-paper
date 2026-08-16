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
                        effect being reported. This axis must include a linear model:
                        for a tree ensemble every split threshold lies inside the source
                        range, so clamping cannot move a row across a split and clipping
                        is a no-op by construction rather than by measurement.
    contradictions      De-duplication keeps the first row of each duplicate group, so for
                        groups carrying both labels an arbitrary label survives. Excluding
                        contradictory groups entirely bounds what that choice is worth.
                        The exclusion must happen BEFORE de-duplication: the loader hashes
                        feature vectors alone, so after de-duplication every vector is
                        unique and no contradiction can be observed.

Writes results/preprocessing_sensitivity.json. `--axes` reruns a subset in place.
"""

from __future__ import annotations

import argparse
import gc
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
from src.pipeline import (_free_gb, apply_to, evict_domains, fit_source, get_domain,
                          make_models, stratified_cap)

CAP = 25_000
MODEL = "LightGBM"
#: Clipping can only bind for a model whose decision surface extends past the training
#: range. LightGBM is carried as the within-run reference; LogisticRegression is the test.
CLIP_MODELS = ["LightGBM", "LogisticRegression"]


def dedup_masks(X: pd.DataFrame, y: np.ndarray):
    """
    Build both row masks from one pass: plain de-duplication, and de-duplication with
    contradictory groups removed first.

    Order matters for the second one. `src.data.load` hashes feature vectors alone, so it
    collapses a contradictory group to whichever label happened to come first and leaves
    no trace to test afterwards. Running on pre-de-duplication rows is the only way to
    see them, and hashing once keeps a 28M-row frame from being traversed twice.
    """
    h = pd.util.hash_pandas_object(X, index=False).to_numpy()
    lab = pd.DataFrame({"h": h, "y": y}).drop_duplicates()
    n_groups = int(lab["h"].nunique())
    counts = lab["h"].value_counts()
    bad = counts[counts > 1].index.to_numpy()    # a hash seen with both labels
    del lab, counts

    first = ~pd.Series(h).duplicated(keep="first").to_numpy()
    keep_nc = first & ~np.isin(h, bad) if len(bad) else first.copy()
    del h
    gc.collect()
    return first, keep_nc, int(len(bad)), n_groups


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


def evaluate(X, yv, seed, sources, src) -> dict:
    """Fit on one source and average external metrics over the other three."""
    m, sc, med, cols, thr, ind = fit_raw(X, yv, seed, CAP)
    ext = []
    for tgt in sources:
        if tgt == src:
            continue
        dom = get_domain(tgt, "drop")
        ext.append(apply_raw(m, sc, med, cols, thr, dom.X, dom.y, CAP, seed))
    return {
        "indomain_macro_f1": ind["macro_f1"], "indomain_auc": ind["roc_auc"],
        "external_macro_f1": float(np.mean([e["macro_f1"] for e in ext])),
        "external_auc": float(np.nanmean([e["roc_auc"] for e in ext])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43])
    ap.add_argument("--axes", nargs="*", default=["dedup", "clipping"],
                    choices=["dedup", "clipping"],
                    help="rerun only these axes, merging into any existing result file")
    args = ap.parse_args()
    sources = [d.key for d in NETFLOW_V2]
    out_path = RESULTS / "preprocessing_sensitivity.json"
    t0 = time.perf_counter()

    # Keep rows from axes we are not rerunning so a partial rerun does not lose them.
    rows: list[dict] = []
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))["rows"]
            rows = [r for r in prev if r["axis"] not in args.axes]
            if rows:
                print(f"carrying {len(rows)} rows from axes not being rerun")
        except (json.JSONDecodeError, KeyError):
            rows = []

    # ---- 1. de-duplication and contradictory groups ------------------------------------
    # All three variants are derived from a single pre-de-duplication load, so they differ
    # only in which rows survive and share one evaluation protocol. Loading twice would
    # cost an extra pass over 28M rows and produce two baselines that disagree for
    # sampling reasons alone.
    if "dedup" in args.axes:
        for seed in args.seeds:
            for src in sources:
                # The pre-de-duplication frame reaches 28M rows. Drop the cached target
                # domains first and hold it in float32, or the two together exhaust RAM.
                evict_domains()
                X, y, _f, _r = load(src, other_policy="drop", dedup=False)
                X = X.astype(np.float32)
                yv = y.to_numpy()
                del y
                gc.collect()
                keep_plain, keep_nc, n_bad, n_groups = dedup_masks(X, yv)
                # `no_dedup` keeps every row, so it reuses the frame instead of taking a
                # boolean-indexed copy of it; that copy is another 4.4 GB on NF-BoT-IoT.
                variants = (("no_dedup", None),
                            ("dedup", keep_plain),
                            ("no_contradictions", keep_nc))
                for variant, keep in variants:
                    Xs = X if keep is None else X[keep].reset_index(drop=True)
                    ys = yv if keep is None else yv[keep]
                    if len(np.unique(ys)) < 2:
                        continue
                    rows.append({
                        "axis": "dedup", "variant": variant, "seed": seed,
                        "source": src, "n_rows": int(len(Xs)),
                        "n_contradictory_groups": n_bad, "n_groups": n_groups,
                        "contradictory_fraction": round(n_bad / max(n_groups, 1), 6),
                        **evaluate(Xs, ys, seed, sources, src)})
                    del Xs, ys
                    gc.collect()
                    print(f"  dedup/{variant:18s} {src:20s} s{seed} | "
                          f"n={rows[-1]['n_rows']:,} "
                          f"in {rows[-1]['indomain_macro_f1']:.4f} "
                          f"ext {rows[-1]['external_macro_f1']:.4f} "
                          f"| {_free_gb():.1f} GB free", flush=True)
                del X, yv, keep_plain, keep_nc, variants
                gc.collect()

    # ---- 3. target clipping ------------------------------------------------------------
    # Run per model: for a tree ensemble clipping cannot change a prediction, because
    # every split threshold was learned inside the source range. The linear model is
    # where the choice can actually bind.
    if "clipping" in args.axes:
        for seed in args.seeds:
            for src in sources:
                for model in CLIP_MODELS:
                    fit = fit_source(src, model, seed=seed, n_per_class=CAP)
                    for clip in (True, False):
                        res = [apply_to(fit, t, n_per_class=CAP, clip=clip)
                               for t in sources if t != src]
                        ext = [r["external"] for r in res]
                        rows.append({
                            "axis": "clipping",
                            "variant": "clipped" if clip else "unclipped",
                            "model": model, "seed": seed, "source": src,
                            "rows_outside_train_range": int(sum(
                                r["rows_outside_train_range"] for r in res)),
                            "indomain_macro_f1": fit.indomain["macro_f1"],
                            "indomain_auc": fit.indomain["roc_auc"],
                            "external_macro_f1": float(
                                np.mean([e["macro_f1"] for e in ext])),
                            "external_auc": float(
                                np.nanmean([e["roc_auc"] for e in ext])),
                        })
                    print(f"  clipping {model:20s} {src:20s} s{seed} done", flush=True)

    # ---- summary -----------------------------------------------------------------------
    summary = {}
    print("\n" + "=" * 74)
    print(f"{'axis':12s} {'variant':20s} {'n':>3s} {'in-domain F1':>13s} "
          f"{'external F1':>12s} {'external AUC':>13s}")
    # Clipping is keyed by model as well as variant; the other axes carry no model split.
    def key_of(r: dict) -> str:
        return (f"{r['axis']}|{r['variant']}" if r["axis"] != "clipping"
                else f"clipping|{r['model']}|{r['variant']}")

    for k in sorted({key_of(r) for r in rows}):
        rs = [r for r in rows if key_of(r) == k]
        e = {m: float(np.mean([r[m] for r in rs]))
             for m in ("indomain_macro_f1", "indomain_auc",
                       "external_macro_f1", "external_auc")}
        e["n"] = len(rs)
        summary[k] = e
        print(f"{k:40s} {len(rs):3d} {e['indomain_macro_f1']:13.4f} "
              f"{e['external_macro_f1']:12.4f} {e['external_auc']:13.4f}")

    # Stored, not just printed: the manuscript quotes these differences, and every number
    # it quotes has to trace back to a result file rather than to arithmetic done by hand.
    deltas: dict[str, dict] = {}

    def delta(a: str, b: str, label: str) -> None:
        x, z = summary.get(a), summary.get(b)
        if not x or not z:
            return
        deltas[label] = {m: round(z[m] - x[m], 6) for m in
                         ("indomain_macro_f1", "indomain_auc",
                          "external_macro_f1", "external_auc")}
        deltas[label].update({"baseline": a, "variant": b})
        print(f"\n{label}: in-domain macro-F1 "
              f"{deltas[label]['indomain_macro_f1']:+.4f}, external macro-F1 "
              f"{deltas[label]['external_macro_f1']:+.4f}, external AUC "
              f"{deltas[label]['external_auc']:+.4f}.")

    delta("dedup|dedup", "dedup|no_dedup", "Skipping de-duplication")
    delta("dedup|dedup", "dedup|no_contradictions", "Dropping contradictory groups")
    for model in CLIP_MODELS:
        delta(f"clipping|{model}|clipped", f"clipping|{model}|unclipped",
              f"Not clipping ({model})")

    contra = [r for r in rows if r["axis"] == "dedup" and "n_groups" in r]
    if contra:
        print("\ncontradictory feature-label groups per source:")
        for src in sorted({r["source"] for r in contra}):
            r = next(x for x in contra if x["source"] == src)
            print(f"  {src:20s} {r['n_contradictory_groups']:>9,d} / "
                  f"{r['n_groups']:>11,d} groups  ({r['contradictory_fraction']:.4%})")

    # Per-source seed-averaged view, so the manuscript can quote a single source without
    # recomputing the average outside the pipeline.
    per_source: dict[str, dict] = {}
    for r in rows:
        k = (f"{r['axis']}|{r.get('model', '')}|{r['variant']}|{r['source']}"
             .replace("||", "|"))
        per_source.setdefault(k, []).append(r)
    per_source = {
        k: {m: float(np.mean([x[m] for x in v]))
            for m in ("indomain_macro_f1", "indomain_auc",
                      "external_macro_f1", "external_auc")}
        | {"n_rows": int(np.mean([x["n_rows"] for x in v])) if "n_rows" in v[0] else None}
        for k, v in per_source.items()}

    out_path.write_text(
        json.dumps({"config": vars(args), "rows": rows, "summary": summary,
                    "deltas": deltas, "per_source": per_source},
                   indent=1, default=float), encoding="utf-8")
    print(f"\nwrote preprocessing_sensitivity.json ({len(rows)} rows) "
          f"in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    with single_instance("preprocessing_sensitivity"):
        raise SystemExit(main())
