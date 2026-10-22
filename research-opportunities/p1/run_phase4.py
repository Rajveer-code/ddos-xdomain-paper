"""
Phase 4 entry point: evaluate the low-controllability defence, honestly.

For each (pair, model, seed) it re-runs the score-only search (same seed -> same attack as
Phase 3), then applies the Phase-4 defence fitted on source-benign low-controllability
features. Reports, per config:
  * HCMR before and after the defence (security gain);
  * the share of successful misses the defence catches;
  * the added benign-review cost = fraction of TARGET benign flows the defence flags.

Gate 4: the defence is a contribution only if it cuts HCMR by >= 0.10 (absolute) at an added
target-benign false-alarm cost <= 0.02. Otherwise it is reported as a negative result. Both
numbers are frozen in PREREGISTRATION §5.
"""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import RESULTS  # noqa: E402
import constraints as C  # noqa: E402
import evade as E  # noqa: E402
from defend import Defense  # noqa: E402
from p1common import build_fit, read_capped, score_flows  # noqa: E402
from run_phase3 import tau_accept_from, boot_rate_ci  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"),
         ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression"]
SEEDS = [42, 43, 44, 45, 46]
FAMILY = "volumetric"
BUDGET = 200
ATTACK_CAP = 2000
TGT_BENIGN = 50_000
HCMR_DROP_BAR = 0.10
FPR_CEILING = 0.02
OUT = RESULTS / "p1"


def main() -> None:
    ctrl = json.loads((OUT / "feature_controllability.json").read_text())
    bounds_all = json.loads((OUT / "constraints.json").read_text())
    results = []
    t0 = time.time()
    for source, target in PAIRS:
        b = C.Bounds.from_json(bounds_all[source][FAMILY])
        low = ctrl[source]["low_controllability_features"]
        for seed in SEEDS:
            Xb_df, yb, _ = read_capped(target, TGT_BENIGN, 0, seed, family=None)
            Xben = Xb_df.to_numpy(dtype=np.float64)[yb == 0]
            Xa_df, _ya, _ = read_capped(target, 0, ATTACK_CAP, seed, family=FAMILY)
            Xatk = Xa_df.to_numpy(dtype=np.float64)
            for model in MODELS:
                F = build_fit(source, model, seed)
                fit, thr = F.fit, F.fit.threshold
                tau = tau_accept_from(F.srcval_proba, F.srcval_y)
                src_benign = F.srcval_X[F.srcval_y == 0]
                dfn = Defense(low, budget=0.01, seed=seed).fit(src_benign)

                rng = np.random.default_rng(1000 + seed)   # same seed as Phase 3
                best, bp = E.search(fit, Xatk, b, BUDGET, rng, mode="score")
                sf = E.success_flags(best, bp, Xatk, b, thr, tau)
                hcm = sf["high_conf_miss"]

                flagged = dfn.flag(best)
                defended_hcm = hcm & (~flagged)
                hcmr0, lo0, hi0 = boot_rate_ci(hcm, seed=seed)
                hcmr1, lo1, hi1 = boot_rate_ci(defended_hcm, seed=seed)
                caught_of_misses = float(flagged[hcm].mean()) if hcm.any() else 0.0
                fpr_cost = float(dfn.flag(Xben).mean())

                rec = {
                    "source": source, "target": target, "model": model, "seed": seed,
                    "low_controllability_features": low,
                    "hcmr_before": hcmr0, "hcmr_before_ci": [lo0, hi0],
                    "hcmr_after": hcmr1, "hcmr_after_ci": [lo1, hi1],
                    "hcmr_drop": hcmr0 - hcmr1,
                    "defence_catch_rate_of_misses": caught_of_misses,
                    "added_benign_review_cost": fpr_cost,
                    "gate4_security": bool((hcmr0 - hcmr1) >= HCMR_DROP_BAR),
                    "gate4_cost_ok": bool(fpr_cost <= FPR_CEILING),
                }
                rec["gate4_pass"] = bool(rec["gate4_security"] and rec["gate4_cost_ok"])
                results.append(rec)
                print(f"[{source[:7]}->{target[:7]} {model[:5]} s{seed}] "
                      f"HCMR {hcmr0:.3f}->{hcmr1:.3f} (drop {hcmr0-hcmr1:.3f}) "
                      f"catch {caught_of_misses:.2f} benign-cost {fpr_cost:.3f} "
                      f"gate4={'PASS' if rec['gate4_pass'] else 'no'} ({time.time()-t0:.0f}s)",
                      flush=True)
                del F, best, bp, dfn
                gc.collect()
            del Xben, Xatk, Xb_df, Xa_df
            gc.collect()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "defense_results.json").write_text(json.dumps(results, indent=2))

    # Gate 4 summary, split by model (the quiet-monitor story was model-dependent).
    print("\n=== Gate 4 ===")
    by = {}
    for r in results:
        by.setdefault((r["source"], r["model"]), []).append(r)
    summ = {}
    for (src, mdl), rs in by.items():
        drop = float(np.mean([x["hcmr_drop"] for x in rs]))
        cost = float(np.mean([x["added_benign_review_cost"] for x in rs]))
        npass = sum(x["gate4_pass"] for x in rs)
        summ[f"{src}|{mdl}"] = {"mean_hcmr_drop": drop, "mean_benign_cost": cost,
                                "n_gate4_pass": npass, "n": len(rs)}
        print(f"  {src[:11]:11s} {mdl:18s} drop={drop:.3f} cost={cost:.3f} "
              f"gate4 {npass}/{len(rs)}")
    (OUT / "gate4_verdict.json").write_text(json.dumps(
        {"hcmr_drop_bar": HCMR_DROP_BAR, "fpr_ceiling": FPR_CEILING, "by_source_model": summ},
        indent=2))
    print(f"\nwrote defense_results.json  ({len(results)} configs, {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
