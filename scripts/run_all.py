"""
Regenerate every result, figure and check in dependency order.

Arguments are the settings each experiment actually ran with, as recorded in the
"config" block of its results file; several scripts have different defaults, so running
them bare does not reproduce the paper. Full run: roughly 6-12 h on one CPU machine,
dominated by data loading and the no-dedup preprocessing arm.

    python scripts/run_all.py --dry-run         # print the plan
    python scripts/run_all.py                   # run everything
    python scripts/run_all.py --from summarize  # resume at the first step whose name contains this
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS: list[tuple[str, list[str]]] = [
    ("characterize", ["characterize_data.py"]),
    ("provenance", ["record_provenance.py"]),
    ("transfer_matrix", ["run_transfer_matrix.py", "--n-per-class", "50000", "--boot", "1000"]),
    ("summarize_matrix", ["summarize_matrix.py"]),
    ("robustness", ["analyze_robustness.py"]),
    ("operating_point", ["aggregate_operating_point.py"]),
    ("feature_ablation", ["run_feature_ablation.py"]),
    ("ablation_intervals", ["ablation_intervals.py"]),
    ("feature_count", ["run_feature_count.py"]),
    ("dns_query_id", ["analyze_dns_query_id.py"]),
    ("inversion_controls", ["run_inversion_controls.py", "--n-per-class", "15000", "--seeds", "42",
                            "--models", "LightGBM"]),
    ("unsw_robustness", ["run_unsw_robustness.py"]),
    ("preprocessing", ["run_preprocessing_sensitivity.py"]),
    ("divergence", ["run_divergence.py"]),
    ("gap_forecast", ["analyze_gap_forecast.py"]),
    ("remedies", ["run_remedies.py"]),
    ("label_budget", ["run_label_budget.py", "--n-per-class", "25000", "--seeds", "42", "43",
                      "--draws", "10"]),
    ("target_only_control", ["run_target_only_control.py"]),
    ("cic_study", ["run_cic_study.py"]),
    ("summarize_all", ["summarize_all.py"]),
    ("summarize_secondary", ["summarize_secondary.py"]),
    ("figures", ["make_figures.py"]),
    ("check_numbers", ["check_numbers.py"]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--from", dest="start", default=None)
    args = ap.parse_args()

    steps = STEPS
    if args.start:
        idx = next((i for i, (name, _) in enumerate(STEPS) if args.start in name), None)
        if idx is None:
            print(f"no step matches {args.start!r}")
            return 2
        steps = STEPS[idx:]

    for name, cmd in steps:
        line = [sys.executable, str(ROOT / "scripts" / cmd[0]), *cmd[1:]]
        print(f"[{name}] {' '.join(cmd)}", flush=True)
        if args.dry_run:
            continue
        t0 = time.perf_counter()
        rc = subprocess.run(line, cwd=ROOT).returncode
        print(f"[{name}] exit {rc} in {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
        if rc != 0:
            print(f"stopped at {name}; resume with --from {name}")
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
