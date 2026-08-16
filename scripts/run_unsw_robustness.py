"""
E1 — is the strongest inversion a property of the network, or of a small source?

Every one of the three transfers that fall below chance in all four model families has
NF-UNSW-NB15 as its source, and NF-UNSW-NB15 retains only 3,075 attack flows after
de-duplication at a 1.30% base rate. A reviewer is entitled to ask whether the paper's
most extreme result is a weak-source artefact rather than evidence about cross-network
transfer.

The confound is that source identity and source size vary together, so this holds size
fixed and varies identity. Every source is capped to the same number of attack flows that
NF-UNSW-NB15 actually has, and each configuration is repeated over independent subsamples.
If the other sources also invert once starved to 3,075 attacks, the finding is about
sample size. If NF-UNSW-NB15 still inverts far harder than sources of identical size, it
is about the network.

The reverse direction is run too: NF-UNSW-NB15 at its full size against itself capped, to
see whether its inversion softens when it is not starved.

Checkpointed. Writes results/unsw_robustness.json.
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
from src.runlock import single_instance
from src.pipeline import apply_to, fit_source

#: Attack flows surviving de-duplication in NF-UNSW-NB15; the size every source is held to.
UNSW_ATTACKS = 3_075
MODELS = ["LightGBM", "LogisticRegression"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44])
    ap.add_argument("--models", nargs="*", default=MODELS)
    ap.add_argument("--full-cap", type=int, default=25_000)
    ap.add_argument("--out", default="unsw_robustness.json")
    args = ap.parse_args()

    sources = [d.key for d in NETFLOW_V2]
    out_path = RESULTS / args.out
    t0 = time.perf_counter()

    rows: list[dict] = []
    done: set[tuple] = set()
    if out_path.exists():
        try:
            rows = json.loads(out_path.read_text(encoding="utf-8"))["rows"]
            done = {(r["regime"], r["model"], r["seed"], r["source"], r["target"])
                    for r in rows}
            print(f"resuming: {len(done)} units complete")
        except (json.JSONDecodeError, KeyError):
            rows, done = [], set()

    def flush():
        out_path.write_text(json.dumps(
            {"config": {**vars(args), "matched_attack_flows": UNSW_ATTACKS}, "rows": rows},
            indent=1, default=float), encoding="utf-8")

    # "matched" starves every source to UNSW's surviving attack count; "full" is the
    # ordinary cap and exists as the within-run reference.
    regimes = {"matched": UNSW_ATTACKS, "full": args.full_cap}

    for regime, cap in regimes.items():
        for model in args.models:
            for seed in args.seeds:
                for src in sources:
                    for tgt in sources:
                        if tgt == src:
                            continue
                        key = (regime, model, seed, src, tgt)
                        if key in done:
                            continue
                        fit = fit_source(src, model, seed=seed, n_per_class=cap)
                        r = apply_to(fit, tgt, n_per_class=args.full_cap)
                        rows.append({
                            "regime": regime, "model": model, "seed": seed,
                            "source": src, "target": tgt,
                            "source_cap_per_class": cap,
                            "n_source_train": fit.n_train,
                            "indomain_auc": fit.indomain["roc_auc"],
                            "external_auc": r["external"]["roc_auc"],
                            "external_macro_f1": r["external"]["macro_f1"],
                            "below_chance": bool(r["external"]["roc_auc"] < 0.5),
                        })
                        done.add(key)
                        flush()
                    print(f"  {regime:8s} {model:20s} s{seed} {src:20s} done", flush=True)

    flush()

    # ---- verdict ---------------------------------------------------------------------
    def sel(regime, src=None, exclude_src=None):
        return [r for r in rows if r["regime"] == regime
                and (src is None or r["source"] == src)
                and (exclude_src is None or r["source"] != exclude_src)]

    print("\n" + "=" * 74)
    print("Does the inversion survive when every source is starved to UNSW's size?")
    print(f"{'regime':10s} {'source group':22s} {'n':>4s} {'mean AUC':>9s} {'below chance':>13s}")
    summary = {}
    for regime in regimes:
        for label, kw in [("NF-UNSW-NB15", {"src": "nf_unsw_nb15"}),
                          ("other three sources", {"exclude_src": "nf_unsw_nb15"})]:
            rs = sel(regime, **kw)
            if not rs:
                continue
            auc = np.array([r["external_auc"] for r in rs], dtype=float)
            below = float(np.mean(auc < 0.5))
            summary[f"{regime}|{label}"] = {
                "n": len(rs), "mean_auc": float(auc.mean()),
                "median_auc": float(np.median(auc)), "frac_below_chance": below}
            print(f"{regime:10s} {label:22s} {len(rs):4d} {auc.mean():9.4f} {below:13.1%}")

    m_u = summary.get("matched|NF-UNSW-NB15", {}).get("mean_auc", float("nan"))
    m_o = summary.get("matched|other three sources", {}).get("mean_auc", float("nan"))
    print(f"\nAt matched source size, NF-UNSW-NB15 mean external AUC {m_u:.4f} against "
          f"{m_o:.4f} for the other three.")
    print("If those are close, the inversion is a small-source effect. If UNSW remains far "
          "lower, it is a property of that network.")

    out = json.loads(out_path.read_text(encoding="utf-8"))
    out["summary"] = summary
    out_path.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {out_path} ({len(rows)} rows) in {(time.perf_counter()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    with single_instance("unsw_robustness"):
        raise SystemExit(main())
