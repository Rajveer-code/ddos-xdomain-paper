"""
Collect every P-1 headline number into one keyed file (results/p1/summary_p1.json), mirroring
the repo's paper/claims.json discipline: the paper quotes these keys and check_numbers_p1.py
verifies the manuscript against them. Nothing in the paper is typed by hand.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

R = Path("results/p1")


def load(name):
    return json.loads((R / name).read_text())


def main():
    base = load("monitor_baseline.json")
    atk = load("attack_results.json")
    dfn = load("defense_results.json")
    lift = load("lift.json")
    g1 = load("gate1_verdict.json")
    g3 = load("gate3_verdict.json")
    g4 = load("gate4_verdict.json")

    def mean(xs):
        return float(np.mean(xs))

    pairs = [("nf_unsw_nb15", "nf_cse_cic_ids2018"), ("nf_bot_iot", "nf_cse_cic_ids2018")]
    models = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
    S = {"config": {"seeds": [42, 43, 44, 45, 46], "budget": 200, "attack_cap": 2000,
                    "source_cap_per_class": 200000, "target_benign": 50000,
                    "models": ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"],
                    "tau_accept_benign_review_budget": 0.01, "scale": "full"}}

    # baseline monitor alarm rates
    S["baseline"] = {
        m: round(mean([r["monitors"][m]["alarm"] for r in base]), 3)
        for m in base[0]["monitors"]}

    per = {}
    for src, tgt in pairs:
        for mdl in models:
            A = [r for r in atk if r["source"] == src and r["model"] == mdl]
            D = [r for r in dfn if r["source"] == src and r["model"] == mdl]
            L = [r for r in lift if r["source"] == src and r["model"] == mdl]
            B = [r for r in base if r["source"] == src and r["model"] == mdl]
            key = f"{src}__{mdl}"
            hcmr_vals = [r["score"]["hcmr"] for r in A]
            per[key] = {
                "baseline_external_auc": round(mean([r["external_auc"] for r in B]), 3),
                "natural_pred_benign_rate": round(mean([r["natural_pred_benign_rate"] for r in A]), 3),
                "latent_hcm_rate": round(mean([r["latent_hcm_rate"] for r in L]), 3),
                "projected_hcmr": round(mean([r["projected_hcmr"] for r in L]), 3),
                "hcmr": round(mean(hcmr_vals), 3),
                "hcmr_ci": [round(mean([r["score"]["hcmr_ci"][0] for r in A]), 3),
                            round(mean([r["score"]["hcmr_ci"][1] for r in A]), 3)],
                "hcmr_seed_sd": round(float(np.std(hcmr_vals)), 3),
                "hcmr_strong": round(mean([r["strong"]["hcmr"] for r in A]), 3),
                "strong_minus_score": round(mean([r["strong"]["hcmr"] for r in A]) - mean(hcmr_vals), 3),
                "search_lift": round(mean([r["search_lift"] for r in L]), 3),
                "plain_evasion_rate": round(mean([r["score"]["plain_evasion_rate"] for r in A]), 3),
                "feasible_rate": round(mean([r["score"]["feasible_rate"] for r in A]), 3),
                "functional_rate": round(mean([r["score"]["functional_rate"] for r in A]), 3),
                "mean_conf_of_misses": round(mean([r["score"]["mean_conf_of_misses"] for r in A]), 3),
                "mean_score_drop": round(mean([r["score"]["mean_score_drop"] for r in A]), 4),
                "model_monitor_alarm_natural": round(mean([
                    any(r["natural_monitors"][m]["alarm"] for m in ("atc_acc_drop", "mean_conf_drop"))
                    for r in A]), 2),
                "model_monitor_alarm_adversarial": round(mean([
                    any(r["score"]["adversarial_monitors"][m]["alarm"]
                        for m in ("atc_acc_drop", "mean_conf_drop")) for r in A]), 2),
                "defense_hcmr_drop": round(mean([r["hcmr_drop"] for r in D]), 3),
                "defense_benign_cost": round(mean([r["added_benign_review_cost"] for r in D]), 3),
                "defense_catch_of_misses": round(mean([r["defence_catch_rate_of_misses"] for r in D]), 3),
            }
    S["per_pair_model"] = per
    S["gate1"] = {"pass": g1["pass"], "n_low_per_source": g1["n_low_per_source"]}
    S["gate3"] = g3
    S["gate4"] = {"hcmr_drop_bar": g4["hcmr_drop_bar"], "fpr_ceiling": g4["fpr_ceiling"],
                  "any_pass": any(v["n_gate4_pass"] > 0 for v in g4["by_source_model"].values())}
    S["low_controllability_features"] = {
        s: json.loads((R / "feature_controllability.json").read_text())[s]["low_controllability_features"]
        for s in ("nf_unsw_nb15", "nf_bot_iot")}

    # Full transfer matrix (generality backbone), if present.
    mpath = R / "matrix_latent.json"
    if mpath.exists():
        mx = json.loads(mpath.read_text())
        vol = [r for r in mx if r.get("has_volumetric")]
        lat = [r["latent_hcm_rate"] for r in vol]
        dangerous = [r for r in vol if r["latent_hcm_rate"] > 0.5
                     and not r["atc_alarm"] and not r["conf_drop_alarm"]]
        permodel = {}
        for mdl in ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]:
            rs = [r for r in vol if r["model"] == mdl]
            if rs:
                permodel[mdl] = {
                    "mean_latent_hcmr": round(float(np.mean([r["latent_hcm_rate"] for r in rs])), 3),
                    "both_monitors_silent_rate": round(float(np.mean(
                        [(not r["atc_alarm"] and not r["conf_drop_alarm"]) for r in rs])), 2)}
        S["matrix"] = {
            "n_configs": len(mx),
            "n_ordered_pairs": len({(r["source"], r["target"]) for r in mx}),
            "n_models": len({r["model"] for r in mx}),
            "mean_latent_hcmr": round(float(np.mean(lat)), 3),
            "latent_hcmr_min": round(float(min(lat)), 3),
            "latent_hcmr_max": round(float(max(lat)), 3),
            "atc_alarm_rate": round(float(np.mean([r["atc_alarm"] for r in mx])), 2),
            "conf_drop_alarm_rate": round(float(np.mean([r["conf_drop_alarm"] for r in mx])), 2),
            "n_dangerous_cells": len(dangerous),
            "n_vol_configs": len(vol),
            "n_dangerous_combos": len({(r["source"], r["target"], r["model"]) for r in dangerous}),
            "per_model": permodel,
        }

    # Full adversarial transfer matrix, if present.
    apath = R / "matrix_attack.json"
    if apath.exists():
        ax = json.loads(apath.read_text())
        sh = [r["searched_hcmr"] for r in ax]
        dangerous = [r for r in ax if r["searched_hcmr"] > 0.5
                     and not r["atc_alarm"] and not r["conf_drop_alarm"]]
        hi = [r for r in ax if r["searched_hcmr"] > 0.5]
        pm = {}
        for mdl in ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]:
            rs = [r for r in ax if r["model"] == mdl]
            if rs:
                pm[mdl] = {
                    "mean_searched_hcmr": round(float(np.mean([r["searched_hcmr"] for r in rs])), 3),
                    "both_monitors_silent_rate": round(float(np.mean(
                        [(not r["atc_alarm"] and not r["conf_drop_alarm"]) for r in rs])), 2)}
        S["matrix_attack"] = {
            "n_configs": len(ax),
            "n_ordered_pairs": len({(r["source"], r["target"]) for r in ax}),
            "mean_searched_hcmr": round(float(np.mean(sh)), 3),
            "n_dangerous_cells": len(dangerous),
            "n_dangerous_combos": len({(r["source"], r["target"], r["model"]) for r in dangerous}),
            "n_high_hcmr_configs": len(hi),
            "silent_rate_among_high_hcmr": round(float(np.mean(
                [(not r["atc_alarm"] and not r["conf_drop_alarm"]) for r in hi])), 2) if hi else 0.0,
            "per_model": pm,
        }

    (R / "summary_p1.json").write_text(json.dumps(S, indent=2))
    print("matrix:", json.dumps(S.get("matrix", {}), indent=2) if "matrix" in S else "none")
    print("matrix_attack:", json.dumps(S.get("matrix_attack", {}), indent=2) if "matrix_attack" in S else "none")


if __name__ == "__main__":
    main()
