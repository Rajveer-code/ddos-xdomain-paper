"""
Model-family robustness and the unit of inference.

Two review points that need no new experiments, because the transfer matrix already holds
four model families across twelve ordered pairs and five seeds.

**Is the inversion a LightGBM artefact?** If only the primary model inverts, the finding is
about gradient boosting rather than about cross-network transfer, and the paper has to say
so. Per-family external AUC, below-chance rate, macro-F1 and MCC answer it directly.

**What is the unit of inference?** The paper reports "108 of 240" and "60 of 60", which
read as counts of independent experiments. They are not: the same ordered pair recurs
across seeds and models, so the runs are nested, not independent. The descriptive unit is
model x pair x seed; the inferential unit is the ordered pair. This recomputes the headline
at pair level so both can be stated without conflation.

Writes results/model_family_robustness.json and results/inference_units.json.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS

SHORT = {"nf_cse_cic_ids2018": "IDS2018", "nf_bot_iot": "BoT-IoT",
         "nf_ton_iot": "ToN-IoT", "nf_unsw_nb15": "UNSW"}


def mean(v):
    a = np.asarray([x for x in v if np.isfinite(x)], dtype=float)
    return float(a.mean()) if len(a) else float("nan")


def boot_ci(v, n_boot=10_000, seed=42):
    a = np.asarray([x for x in v if np.isfinite(x)], dtype=float)
    if len(a) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    b = np.array([a[rng.integers(0, len(a), len(a))].mean() for _ in range(n_boot)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main() -> int:
    d = json.loads((RESULTS / "transfer_matrix.json").read_text(encoding="utf-8"))
    ext = [r for r in d["rows"] if r["kind"] == "external"]

    # ------------------------------------------------ per model family
    by_model = defaultdict(list)
    for r in ext:
        by_model[r["model"]].append(r)

    print("MODEL-FAMILY ROBUSTNESS  (external transfers, 12 pairs x 5 seeds each)")
    print(f"{'model':22s} {'n':>4s} {'mean AUC':>9s} {'AUC<0.5':>8s} {'mean F1':>8s} "
          f"{'mean MCC':>9s} {'MCC<0':>7s}")
    fam = {}
    for m, rs in sorted(by_model.items()):
        auc = [x["metrics"]["roc_auc"] for x in rs]
        f1 = [x["metrics"]["macro_f1"] for x in rs]
        mcc = [x["metrics"]["mcc"] for x in rs]
        below = float(np.mean([a < 0.5 for a in auc if np.isfinite(a)]))
        negm = float(np.mean([c < 0 for c in mcc if np.isfinite(c)]))
        lo, hi = boot_ci(auc)
        fam[m] = {"n": len(rs), "mean_auc": mean(auc), "auc_ci_lo": lo, "auc_ci_hi": hi,
                  "frac_below_chance": below, "mean_macro_f1": mean(f1),
                  "mean_mcc": mean(mcc), "frac_negative_mcc": negm,
                  "min_auc": float(np.nanmin(auc)), "max_auc": float(np.nanmax(auc))}
        print(f"{m:22s} {len(rs):4d} {mean(auc):9.4f} {below:8.1%} {mean(f1):8.4f} "
              f"{mean(mcc):+9.4f} {negm:7.1%}")

    # Is inversion present in every family? Count pairs below chance per family.
    print("\nPer-pair mean external AUC by model family (below-chance cells marked *)")
    pairs = sorted({(r["source"], r["target"]) for r in ext})
    models = sorted(by_model)
    header = "pair".ljust(22) + "".join(m[:9].rjust(11) for m in models)
    print(header)
    pair_tbl = {}
    for s_, t_ in pairs:
        cells = []
        row = {}
        for m in models:
            v = mean([x["metrics"]["roc_auc"] for x in ext
                      if x["source"] == s_ and x["target"] == t_ and x["model"] == m])
            row[m] = v
            cells.append(f"{v:.3f}{'*' if v < 0.5 else ' '}".rjust(11))
        pair_tbl[f"{s_}|{t_}"] = row
        print(f"{SHORT[s_]+'->'+SHORT[t_]:22s}" + "".join(cells))

    n_all_below = sum(1 for r in pair_tbl.values() if all(v < 0.5 for v in r.values()))
    n_any_below = sum(1 for r in pair_tbl.values() if any(v < 0.5 for v in r.values()))
    print(f"\npairs below chance in ALL four families: {n_all_below}/{len(pair_tbl)}")
    print(f"pairs below chance in AT LEAST ONE family: {n_any_below}/{len(pair_tbl)}")

    (RESULTS / "model_family_robustness.json").write_text(json.dumps(
        {"per_model": fam, "per_pair_auc": pair_tbl,
         "n_pairs_below_chance_all_families": n_all_below,
         "n_pairs_below_chance_any_family": n_any_below,
         "n_pairs": len(pair_tbl)}, indent=2, default=float), encoding="utf-8")

    # ------------------------------------------------ unit of inference
    prim = [r for r in ext if r["model"] == "LightGBM"]
    run_below = sum(1 for r in ext if r["metrics"]["roc_auc"] < 0.5)
    prim_below = sum(1 for r in prim if r["metrics"]["roc_auc"] < 0.5)

    # pair-level: average over seeds first, then count
    pair_auc = {}
    for (s_, t_) in pairs:
        pair_auc[f"{s_}|{t_}"] = mean([r["metrics"]["roc_auc"] for r in prim
                                       if r["source"] == s_ and r["target"] == t_])
    pair_below = sum(1 for v in pair_auc.values() if v < 0.5)
    pv = list(pair_auc.values())
    lo, hi = boot_ci(pv)

    units = {
        "descriptive_unit": "model x ordered pair x seed",
        "inferential_unit": "ordered pair (seeds averaged within pair)",
        "n_runs_all_models": len(ext),
        "n_runs_below_chance_all_models": run_below,
        "n_runs_primary": len(prim),
        "n_runs_below_chance_primary": prim_below,
        "n_pairs": len(pair_auc),
        "n_pairs_below_chance_primary": pair_below,
        "pair_level_mean_auc_primary": mean(pv),
        "pair_level_auc_ci_lo": lo,
        "pair_level_auc_ci_hi": hi,
    }
    (RESULTS / "inference_units.json").write_text(
        json.dumps(units, indent=2, default=float), encoding="utf-8")

    print("\nUNIT OF INFERENCE")
    print(f"  descriptive (model x pair x seed): {run_below}/{len(ext)} runs below chance")
    print(f"  primary model only              : {prim_below}/{len(prim)} runs below chance")
    print(f"  inferential (ordered pair)      : {pair_below}/{len(pair_auc)} pairs below chance")
    print(f"  pair-level mean external AUC    : {mean(pv):.4f} [{lo:.4f}, {hi:.4f}]")
    print(f"\nwrote model_family_robustness.json and inference_units.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
