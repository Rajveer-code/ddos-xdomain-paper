"""
B2 — can the collapse be predicted without target labels?

Computes label-free source->target divergence for every ordered pair, alongside the
model-based confidence signals, so they can be regressed against the observed gaps from
the transfer matrix.

Distribution measures are computed on features scaled by the *source* scaler, because
that is what an operator would have: a model, its preprocessing, and unlabelled traffic.

Writes results/divergence.json.

    python scripts/run_divergence.py
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

import pandas as pd

from src.config import NETFLOW_V2, RESULTS
from src.divergence import confidence_scores, feature_wasserstein, mmd_rbf, proxy_a_distance
from src.pipeline import apply_to, fit_source, get_domain, stratified_cap


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-per-class", type=int, default=50_000)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--model", default="LightGBM")
    ap.add_argument("--out", default="divergence.json")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    rows: list[dict] = []
    t0 = time.perf_counter()

    for seed in args.seeds:
        for src in sources:
            fit = fit_source(src, args.model, seed=seed, n_per_class=args.n_per_class)
            # Source-side reference distribution: the scaled training-domain features.
            dom_s = get_domain(src)
            Xs, _ys, _fs = stratified_cap(dom_s.X, dom_s.y, dom_s.fam,
                                          args.n_per_class, seed)
            Xs_s = pd.DataFrame(fit.scaler.transform(Xs[fit.features]),
                                columns=fit.features).clip(0.0, 1.0)

            for tgt in sources:
                if tgt == src:
                    continue
                dom_t = get_domain(tgt)
                Xt, _yt, _ft = stratified_cap(dom_t.X, dom_t.y, dom_t.fam,
                                              args.n_per_class, seed)
                Xt_s = pd.DataFrame(fit.scaler.transform(Xt[fit.features]),
                                    columns=fit.features).clip(0.0, 1.0)

                r = apply_to(fit, tgt, n_per_class=args.n_per_class)

                pad = proxy_a_distance(Xs_s, Xt_s, seed=seed)
                wass = feature_wasserstein(Xs_s, Xt_s, seed=seed)
                mmd = mmd_rbf(Xs_s, Xt_s, seed=seed)
                conf = confidence_scores(fit.proba_test, r["proba"],
                                         acc_source=fit.indomain["accuracy"])

                row = {
                    "source": src, "target": tgt, "seed": seed, "model": args.model,
                    **pad,
                    "wasserstein_sum": wass["wasserstein_sum"],
                    "wasserstein_mean": wass["wasserstein_mean"],
                    "wasserstein_max": wass["wasserstein_max"],
                    "per_feature_wasserstein": wass["per_feature"],
                    "mmd_rbf": mmd,
                    **conf,
                    # observed outcome, for the regression
                    "indomain_macro_f1": fit.indomain["macro_f1"],
                    "indomain_accuracy": fit.indomain["accuracy"],
                    "external_macro_f1": r["external"]["macro_f1"],
                    "external_accuracy": r["external"]["accuracy"],
                    "external_auc": r["external"]["roc_auc"],
                    "gap_macro_f1": fit.indomain["macro_f1"] - r["external"]["macro_f1"],
                    "gap_accuracy": fit.indomain["accuracy"] - r["external"]["accuracy"],
                }
                rows.append(row)
                print(
                    f"{src:20s} -> {tgt:20s} s{seed} | d_A {pad['proxy_a_distance']:.3f} "
                    f"W {wass['wasserstein_sum']:7.3f} MMD {mmd:.4f} "
                    f"ATC {conf['atc_estimated_accuracy']:.3f} | "
                    f"true acc {r['external']['accuracy']:.3f} "
                    f"gap-F1 {row['gap_macro_f1']:.3f}",
                    flush=True,
                )

    payload = {
        "config": {"model": args.model, "seeds": args.seeds, "sources": sources,
                   "n_per_class": args.n_per_class},
        "rows": rows,
    }
    out = RESULTS / args.out
    out.write_text(json.dumps(payload, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {out} ({len(rows)} rows) in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
