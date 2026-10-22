"""
Keyed-number check for the P-1 draft (mirrors scripts/check_numbers.py).

Derives the headline literals from results/p1/summary_p1.json and asserts each appears verbatim
in research-opportunities/p1/PAPER_DRAFT.md. If the data changes, this fails until the paper is
updated — no number is hand-typed and left to drift. Exit non-zero on any miss.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results" / "p1"
PAPER = (Path(__file__).resolve().parent / "PAPER_DRAFT.md").read_text(encoding="utf-8")


def f3(x):
    return f"{x:.3f}"


def main() -> int:
    S = json.loads((R / "summary_p1.json").read_text())
    per = S["per_pair_model"]
    checks: list[tuple[str, str]] = []

    def add(label, literal):
        checks.append((label, str(literal)))

    # config
    add("budget", S["config"]["budget"])
    add("attack_cap", "2,000")
    add("review budget", "1%")

    for key, short in [("nf_unsw_nb15__LightGBM", "UNSW/LGBM"),
                       ("nf_unsw_nb15__LogisticRegression", "UNSW/LogReg"),
                       ("nf_bot_iot__LightGBM", "BoT/LGBM"),
                       ("nf_bot_iot__LogisticRegression", "BoT/LogReg")]:
        p = per[key]
        add(f"{short} HCMR", f3(p["hcmr"]))
        add(f"{short} natural_hcmr", f3(p["natural_hcmr"]))
        add(f"{short} lift", f"{p['adversarial_lift']:+.3f}")

    # defense drops and bar
    add("UNSW defense drop", f3(per["nf_unsw_nb15__LightGBM"]["defense_hcmr_drop"]))
    add("BoT defense drop", f3(per["nf_bot_iot__LightGBM"]["defense_hcmr_drop"]))
    add("gate4 bar", "0.10")
    # the quiet-monitor config AUC
    add("BoT/LogReg AUC", f3(per["nf_bot_iot__LogisticRegression"]["baseline_external_auc"]))

    missing = [(lab, lit) for lab, lit in checks if lit not in PAPER]
    for lab, lit in checks:
        mark = "MISS" if (lab, lit) in missing else "ok"
        print(f"  [{mark:4s}] {lab:22s} {lit}")
    if missing:
        print(f"\nFAIL: {len(missing)} number(s) in summary_p1.json not found in PAPER_DRAFT.md:")
        for lab, lit in missing:
            print(f"   - {lab}: {lit}")
        return 1
    print(f"\nPASS: all {len(checks)} keyed numbers present and consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
