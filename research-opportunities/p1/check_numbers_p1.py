"""
Keyed-number check for the P-1 manuscript (mirrors scripts/check_numbers.py).

Derives the headline literals from results/p1/summary_p1.json (per_pair_model + matrix) and
asserts each appears verbatim in MANUSCRIPT.md. If the data changes, this fails until the
manuscript is updated — no number is hand-typed and left to drift. Exit non-zero on any miss.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "results" / "p1"
PAPER = (HERE / "MANUSCRIPT.md").read_text(encoding="utf-8")


def f3(x):
    return f"{x:.3f}"


def main() -> int:
    S = json.loads((R / "summary_p1.json").read_text())
    per = S["per_pair_model"]
    mx = S.get("matrix", {})
    checks: list[tuple[str, str]] = []

    def add(label, literal):
        checks.append((label, str(literal)))

    # matrix (generality backbone)
    if mx:
        add("matrix configs", mx["n_configs"])
        add("matrix pairs", mx["n_ordered_pairs"])
        add("matrix mean latent", f3(mx["mean_latent_hcmr"]))
        add("matrix dangerous cells", mx["n_dangerous_cells"])
        add("matrix dangerous combos", mx["n_dangerous_combos"])
        add("LogReg matrix latent", f3(mx["per_model"]["LogisticRegression"]["mean_latent_hcmr"]))
        add("RF matrix latent", f3(mx["per_model"]["RandomForest"]["mean_latent_hcmr"]))
        add("LogReg silent rate", f"{mx['per_model']['LogisticRegression']['both_monitors_silent_rate']:.2f}")

    # per-cell searched HCMR, search lift, and the resisting RandomForest cell
    cells = [("nf_bot_iot__LightGBM", "BoT/LGBM"),
             ("nf_bot_iot__LogisticRegression", "BoT/LogReg"),
             ("nf_bot_iot__XGBoost", "BoT/XGB"),
             ("nf_bot_iot__RandomForest", "BoT/RF"),
             ("nf_unsw_nb15__LogisticRegression", "UNSW/LogReg")]
    for key, short in cells:
        if key in per:
            add(f"{short} search_lift", f"{per[key]['search_lift']:+.3f}")
    # the resisting RF searched HCMR and the saturated LogReg latent
    add("BoT/RF searched HCMR", f3(per["nf_bot_iot__RandomForest"]["hcmr"]))
    add("BoT/LogReg latent", f3(per["nf_bot_iot__LogisticRegression"]["latent_hcm_rate"]))
    # CIs, per-flow score drops, and strong-search deltas (the audit-fixed numbers)
    for key, short in [("nf_bot_iot__RandomForest", "BoT/RF"),
                       ("nf_unsw_nb15__LightGBM", "UNSW/LGBM")]:
        lo, hi = per[key]["hcmr_ci"]
        add(f"{short} CI lo", f3(lo))
        add(f"{short} CI hi", f3(hi))
    add("BoT/LGBM Pdrop", f3(per["nf_bot_iot__LightGBM"]["mean_score_drop"]))
    add("BoT/XGB Pdrop", f3(per["nf_bot_iot__XGBoost"]["mean_score_drop"]))
    add("BoT/XGB strong delta", f"{per['nf_bot_iot__XGBoost']['strong_minus_score']:+.3f}")
    add("BoT/RF strong delta", f"{per['nf_bot_iot__RandomForest']['strong_minus_score']:+.3f}")
    # defense drops and bar
    add("UNSW defense drop", f3(per["nf_unsw_nb15__LightGBM"]["defense_hcmr_drop"]))
    add("BoT defense drop", f3(per["nf_bot_iot__LightGBM"]["defense_hcmr_drop"]))
    add("gate4 bar", "0.10")

    missing = [(lab, lit) for lab, lit in checks if lit not in PAPER]
    for lab, lit in checks:
        print(f"  [{'MISS' if (lab, lit) in missing else 'ok':4s}] {lab:26s} {lit}")
    if missing:
        print(f"\nFAIL: {len(missing)} number(s) not found in MANUSCRIPT.md:")
        for lab, lit in missing:
            print(f"   - {lab}: {lit}")
        return 1
    print(f"\nPASS: all {len(checks)} keyed numbers present and consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
