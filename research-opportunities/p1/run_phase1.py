"""
Phase 1 entry point: derive the feasible-set bounds and measure feature controllability.

For each source domain:
  * bounds  -> results/p1/constraints.json  (per-family [p1,p99] box from real attack flows)
  * controllability R^2 of each indirectly-influenced feature from the directly-controllable
    ones, by 5-fold cross-validated prediction on real flows
    -> results/p1/feature_controllability.json

Gate 1 (realism of the feature-space study): at least one indirectly-influenced feature must
have LOW controllability R^2 (R^2 < R2_LOW). Those are the features the attacker cannot freely
set, and they are the only ones Phase 4's defence is allowed to watch. If every indirect
feature is trivially derivable from controllable ones, the defence has nothing to stand on and
we narrow to the evasion-only (negative) result per falsifier F-no-defense-features.

Reuses src/ for loading. No model training from scratch beyond the small controllability probes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402
from sklearn.model_selection import cross_val_predict  # noqa: E402
from sklearn.metrics import r2_score  # noqa: E402

from src.data import load  # noqa: E402
from src.config import RESULTS  # noqa: E402
import constraints as C  # noqa: E402

SOURCES = ["nf_unsw_nb15", "nf_bot_iot"]
FAMILY = "volumetric"            # the only DoS family both sources carry
R2_LOW = 0.50                    # below this: attacker cannot freely set the feature
N_PROBE = 15_000                 # rows sampled for the controllability probes
SEED = 42
OUT = RESULTS / "p1"
OUT.mkdir(parents=True, exist_ok=True)


def controllability(X: np.ndarray, rng: np.random.Generator) -> dict[str, float]:
    """5-fold CV R^2 of each indirect feature predicted from the directly-controllable ones."""
    if len(X) > N_PROBE:
        X = X[rng.choice(len(X), N_PROBE, replace=False)]
    Xd = X[:, C._DIRECT_IDX]
    Xd = np.nan_to_num(Xd, nan=0.0, posinf=0.0, neginf=0.0)
    out: dict[str, float] = {}
    for f in C.INDIRECT:
        y = np.nan_to_num(X[:, C.IDX[f]], nan=0.0, posinf=0.0, neginf=0.0)
        if np.allclose(y, y[0]):           # constant target: trivially "predictable", R^2 := 1
            out[f] = 1.0
            continue
        reg = HistGradientBoostingRegressor(max_iter=120, random_state=SEED)
        pred = cross_val_predict(reg, Xd, y, cv=5, n_jobs=-1)
        out[f] = float(r2_score(y, pred))
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    bounds_json: dict[str, dict] = {}
    ctrl_json: dict[str, dict] = {}

    for src in SOURCES:
        X, y, fam, rep = load(src, other_policy="drop", dedup=True)
        Xf = X[C.FEATURES].to_numpy(dtype=np.float64, na_value=np.nan)
        attack = (y.to_numpy() == 1) & (fam.to_numpy() == FAMILY)
        Xatk = Xf[attack]
        b = C.derive_bounds(Xatk, FAMILY)
        bounds_json[src] = {FAMILY: b.to_json(), "n_attack_flows": int(attack.sum())}

        ctrl = controllability(Xf, rng)
        low = sorted([f for f, r in ctrl.items() if r < R2_LOW], key=lambda f: ctrl[f])
        ctrl_json[src] = {
            "r2_low_threshold": R2_LOW,
            "controllability_r2": ctrl,
            "low_controllability_features": low,
            "n_low": len(low),
        }
        print(f"[{src}] n_attack={int(attack.sum())}  low-controllability indirect "
              f"features ({len(low)}/{len(C.INDIRECT)}): {low}")

    (OUT / "constraints.json").write_text(json.dumps(bounds_json, indent=2))
    (OUT / "feature_controllability.json").write_text(json.dumps(ctrl_json, indent=2))

    # Gate 1: defense needs at least one low-controllability feature on at least one source.
    gate_src = {s: ctrl_json[s]["n_low"] for s in SOURCES}
    gate_pass = any(n >= 1 for n in gate_src.values())
    verdict = "PASS" if gate_pass else "FAIL (narrow to evasion-only, F-no-defense-features)"
    print(f"\nGate 1 (low-controllability features exist): {verdict}")
    print(f"  per source n_low: {gate_src}")
    (OUT / "gate1_verdict.json").write_text(json.dumps(
        {"gate": "Gate 1", "pass": gate_pass, "n_low_per_source": gate_src,
         "r2_low_threshold": R2_LOW}, indent=2))


if __name__ == "__main__":
    main()
