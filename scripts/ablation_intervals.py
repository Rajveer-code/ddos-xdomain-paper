"""
Confidence intervals on the feature-ablation deltas.

Section 4.4 declares the pre-specified capacity hypothesis refuted because removing every
capacity feature buys +0.0132 macro-F1. Stated alone that number cannot distinguish "no
effect" from "an effect this study was underpowered to detect", which is the single most
attackable sentence in the manuscript and, awkwardly, its own headline refutation.

The comparison is paired: each feature set is evaluated on the same (source, seed)
combinations as the full-feature baseline, so the delta is computed within pair and the
bootstrap resamples pairs rather than raw scores. A power check reports the smallest true
effect this design could reliably detect.

Writes results/ablation_intervals.json.
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

N_BOOT = 10_000
SEED = 42


def paired_bootstrap(deltas: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Percentile CI and two-sided p-value for the mean of paired differences."""
    rng = np.random.default_rng(seed)
    n = len(deltas)
    boot = np.array([deltas[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    p = float(2 * min((boot <= 0).mean(), (boot >= 0).mean()))
    return {
        "mean_delta": float(deltas.mean()),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "p_value": min(p, 1.0),
        "n_pairs": int(n),
        "sd": float(deltas.std(ddof=1)) if n > 1 else 0.0,
        "significant": bool(lo > 0 or hi < 0),
    }


def min_detectable_effect(sd: float, n: int) -> float:
    """
    Smallest true mean difference detectable at alpha=0.05 with 80% power, paired design.
    (1.96 + 0.84) * sd / sqrt(n).
    """
    return float(2.80 * sd / np.sqrt(n)) if n > 1 else float("nan")


def main() -> int:
    abl = json.loads((RESULTS / "feature_ablation.json").read_text(encoding="utf-8"))

    # Index external score by (feature_set, source, seed) so deltas are computed within pair.
    by = {}
    sets = set()
    for r in abl["rows"]:
        by[(r["feature_set"], r["source"], r["seed"])] = r["external_mean_macro_f1"]
        sets.add(r["feature_set"])

    keys = sorted({(s, sd) for (_f, s, sd) in by})
    base = np.array([by[("all", s, sd)] for s, sd in keys], dtype=float)

    out = {}
    print(f"Paired bootstrap on ablation deltas vs `all` "
          f"({len(keys)} source-seed pairs, B={N_BOOT:,})\n")
    print(f"{'feature set':24s} {'k':>3s} {'delta':>9s} {'95% CI':>20s} {'p':>7s} {'MDE':>7s}  verdict")

    for fs in sorted(sets):
        if fs == "all":
            continue
        try:
            vals = np.array([by[(fs, s, sd)] for s, sd in keys], dtype=float)
        except KeyError:
            continue
        d = vals - base
        st = paired_bootstrap(d)
        st["min_detectable_effect"] = min_detectable_effect(st["sd"], st["n_pairs"])
        st["k"] = next(r["n_features"] for r in abl["rows"] if r["feature_set"] == fs)
        out[fs] = st
        verdict = "DIFFERENT" if st["significant"] else "no effect detected"
        print(f"{fs:24s} {st['k']:3d} {st['mean_delta']:+9.4f} "
              f"[{st['ci_lo']:+.4f}, {st['ci_hi']:+.4f}] {st['p_value']:7.3f} "
              f"{st['min_detectable_effect']:7.4f}  {verdict}")

    (RESULTS / "ablation_intervals.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"\nwrote {RESULTS / 'ablation_intervals.json'}")

    cap = out.get("no_capacity")
    one = out.get("only_identifier")
    if cap:
        print(f"\ncapacity hypothesis: delta {cap['mean_delta']:+.4f} "
              f"[{cap['ci_lo']:+.4f}, {cap['ci_hi']:+.4f}], p={cap['p_value']:.3f}; "
              f"smallest effect detectable at 80% power = {cap['min_detectable_effect']:.4f}")
    if one:
        print(f"one-feature set    : delta {one['mean_delta']:+.4f} "
              f"[{one['ci_lo']:+.4f}, {one['ci_hi']:+.4f}], p={one['p_value']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
