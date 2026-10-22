"""
Phase 3 entry point: the adaptive high-confidence-miss search, both threat modes, with the
monitor battery measured DURING the attack.

For each (pair, model, seed):
  * build the source detector; set tau_accept on source-validation benign confidence (1% review
    budget); load the per-source family bounds from results/p1/constraints.json.
  * take the target's real volumetric DoS flows (cap per PREREGISTRATION §5).
  * run the score-only search (primary) and the strong upper-bound search (ablation).
  * record HCMR (with bootstrap CI over flows), plain evasion rate, mean confidence of the
    successful misses, feasibility/functionality rates, and the monitor battery's alarms on the
    NATURAL target deployment vs the ADVERSARIAL deployment (benign + attack), so we can see
    whether the monitors that fire on natural shift stay quiet on the adversarial one.

Saves results/p1/attack_results.json and prints the Gate 3 "which world" verdict.
Memory-safe: reuses the capped streaming loader; attack sets are small (<=2000 flows).
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
import monitors as M  # noqa: E402
import evade as E  # noqa: E402
from p1common import build_fit, read_capped, score_flows  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"),
         ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression"]
SEEDS = [42, 43, 44]
FAMILY = "volumetric"
BUDGET = 200
ATTACK_CAP = 2000
TGT_BENIGN = 20_000
OUT = RESULTS / "p1"
MODEL_MONITORS = ("atc_acc_drop", "mean_conf_drop")   # the quiet-monitor story lives here


def boot_rate_ci(flags: np.ndarray, n_boot=2000, seed=0) -> tuple[float, float, float]:
    f = np.asarray(flags, dtype=float)
    n = len(f)
    if n == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    means = np.array([f[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    return float(f.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def tau_accept_from(srcval_proba, srcval_y, budget=0.01) -> float:
    conf = np.maximum(srcval_proba, 1 - srcval_proba)
    benign = conf[np.asarray(srcval_y) == 0]
    if len(benign) == 0:
        return float(np.quantile(conf, budget))
    return float(np.quantile(benign, budget))   # 1% of benign fall below -> escalated


def deployment_alarms(cal, benign_proba, benign_X, atk_proba, atk_X):
    proba = np.concatenate([benign_proba, atk_proba])
    X = np.vstack([benign_X, atk_X])
    return M.score(cal, proba, X)


def main() -> None:
    bounds_all = json.loads((OUT / "constraints.json").read_text())
    results = []
    t0 = time.time()
    for source, target in PAIRS:
        b = C.Bounds.from_json(bounds_all[source][FAMILY])
        for seed in SEEDS:
            Xb_df, yb, _ = read_capped(target, TGT_BENIGN, 0, seed, family=None)
            Xben = Xb_df.to_numpy(dtype=np.float64)
            ben_benign = Xben[yb == 0]
            Xa_df, ya, _ = read_capped(target, 0, ATTACK_CAP, seed, family=FAMILY)
            Xatk = Xa_df.to_numpy(dtype=np.float64)
            for model in MODELS:
                F = build_fit(source, model, seed)
                fit, thr = F.fit, F.fit.threshold
                tau = tau_accept_from(F.srcval_proba, F.srcval_y)
                cal = M.calibrate(F.srcval_proba, F.srcval_X, F.source_acc)

                nat_p = score_flows(fit, Xatk)
                nat_pred_benign = float((nat_p < thr).mean())

                rec = {"source": source, "target": target, "model": model, "seed": seed,
                       "n_attack": int(len(Xatk)), "threshold": float(thr), "tau_accept": tau,
                       "natural_pred_benign_rate": nat_pred_benign,
                       "natural_monitors": deployment_alarms(
                           cal, score_flows(fit, ben_benign), ben_benign, nat_p, Xatk)}

                for mode in ("score", "strong"):
                    rng = np.random.default_rng(1000 + seed)
                    best, bp = E.search(fit, Xatk, b, BUDGET, rng, mode=mode)
                    sf = E.success_flags(best, bp, Xatk, b, thr, tau)
                    hcm = sf["high_conf_miss"]
                    rate, lo, hi = boot_rate_ci(hcm, seed=seed)
                    succ_conf = sf["confidence"][hcm]
                    rec[mode] = {
                        "hcmr": rate, "hcmr_ci": [lo, hi],
                        "plain_evasion_rate": float(sf["pred_benign"].mean()),
                        "high_conf_rate": float(sf["high_conf"].mean()),
                        "feasible_rate": float(sf["feasible"].mean()),
                        "functional_rate": float(sf["functional"].mean()),
                        "mean_conf_of_misses": float(succ_conf.mean()) if hcm.any() else 0.0,
                        "mean_score_drop": float((score_flows(fit, Xatk) - bp).mean()),
                        "adversarial_monitors": deployment_alarms(
                            cal, score_flows(fit, ben_benign), ben_benign, bp, best),
                    }
                results.append(rec)
                s = rec["score"]
                nat_a = [m for m in MODEL_MONITORS if rec["natural_monitors"][m]["alarm"]]
                adv_a = [m for m in MODEL_MONITORS if s["adversarial_monitors"][m]["alarm"]]
                print(f"[{source[:7]}->{target[:7]} {model[:5]} s{seed}] "
                      f"HCMR(score)={s['hcmr']:.3f} CI[{s['hcmr_ci'][0]:.3f},{s['hcmr_ci'][1]:.3f}] "
                      f"strong={rec['strong']['hcmr']:.3f} "
                      f"model-mon nat={nat_a} adv={adv_a} ({time.time()-t0:.0f}s)", flush=True)
                del F, cal, best, bp
                gc.collect()
            del Xben, ben_benign, Xatk, Xb_df, Xa_df
            gc.collect()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "attack_results.json").write_text(json.dumps(results, indent=2))

    # Gate 3: which world are we in?
    by_pair = {}
    for r in results:
        by_pair.setdefault((r["source"], r["target"]), []).append(r)
    print("\n=== Gate 3 (which world) ===")
    world = {}
    for (src, tgt), rs in by_pair.items():
        hcmr_los = [x["score"]["hcmr_ci"][0] for x in rs]
        nontrivial = any(lo > 0 for lo in hcmr_los)
        # model-based monitors quiet during successful attacks?
        adv_model_alarm = np.mean([
            any(x["score"]["adversarial_monitors"][m]["alarm"] for m in MODEL_MONITORS)
            for x in rs])
        quiet = adv_model_alarm < 0.5
        world[f"{src}->{tgt}"] = {
            "hcmr_mean": float(np.mean([x["score"]["hcmr"] for x in rs])),
            "hcmr_ci_lo_min": float(min(hcmr_los)), "hcmr_ci_lo_max": float(max(hcmr_los)),
            "nontrivial_hcmr": bool(nontrivial),
            "adv_model_monitor_alarm_rate": float(adv_model_alarm),
            "model_monitors_quiet": bool(quiet)}
        print(f"  {src}->{tgt}: HCMR mean={world[f'{src}->{tgt}']['hcmr_mean']:.3f} "
              f"nontrivial={nontrivial} model-mon quiet during attack={quiet} "
              f"(alarm rate {adv_model_alarm:.2f})")
    defense_world = any(w["nontrivial_hcmr"] and w["model_monitors_quiet"] for w in world.values())
    print(f"\nProceed to defense (nontrivial HCMR + quiet model monitors on >=1 pair): "
          f"{defense_world}")
    (OUT / "gate3_verdict.json").write_text(json.dumps(
        {"world": world, "proceed_to_defense": bool(defense_world)}, indent=2))
    print(f"\nwrote attack_results.json  ({len(results)} configs, {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
