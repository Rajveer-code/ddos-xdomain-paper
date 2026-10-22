"""
Phase 3 core: the adaptive high-confidence-miss search.

The objective is NOT merely to flip the label. It is to push the detector's P(attack) as low
as possible subject to feasibility, because a low P(attack) simultaneously (a) flips the
prediction to benign and (b) raises the benign-confidence max(p,1-p) toward the
auto-acceptance threshold tau_accept. So minimising P(attack) over the feasible set serves
both halves of the high-confidence-miss definition.

Threat model (frozen, PREREGISTRATION §3):
  mode="score"   grey-box, score-only: constrained random search + hill-climbing over the
                 directly-controllable features, each candidate passed through
                 constraints.project, scored via the deployed model. The realistic attacker.
  mode="strong"  capability upper bound: a larger query budget plus a coordinate-descent
                 sweep. Tree ensembles are non-differentiable, so this stands in for the
                 pre-registered white-box ablation (amendment dated 2026-10-22 in
                 PREREGISTRATION §8); it is an upper bound on a score-only adversary, labelled
                 as such, never claimed as a gradient attack.

Only the directly-controllable features move; indirect and uncontrollable features are frozen
at the original flow (the conservative attacker that cannot set the responder's behaviour).
Batched: one model query scores all flows' current candidate at once, so `budget` is the
number of score queries per flow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import constraints as C  # noqa: E402
from p1common import score_flows  # noqa: E402

_DIRECT = C._DIRECT_IDX


def _perturb(best: np.ndarray, b: C.Bounds, step: float, rng: np.random.Generator,
             k: int = 4) -> np.ndarray:
    """Perturb k random directly-controllable features of each row; occasional box re-draw."""
    n = len(best)
    cand = best.copy()
    width = (b.hi[_DIRECT] - b.lo[_DIRECT])
    # k random direct dims per row
    sel = rng.integers(0, len(_DIRECT), size=(n, k))
    for j in range(k):
        cols = _DIRECT[sel[:, j]]
        noise = rng.normal(0.0, step, n) * width[sel[:, j]]
        cand[np.arange(n), cols] += noise
    # exploration: 10% of rows get one feature redrawn uniformly in its box
    expl = rng.random(n) < 0.10
    if expl.any():
        d = rng.integers(0, len(_DIRECT), expl.sum())
        cols = _DIRECT[d]
        cand[np.where(expl)[0], cols] = (
            b.lo[cols] + rng.random(expl.sum()) * (b.hi[cols] - b.lo[cols]))
    return cand


def search(fit, flows: np.ndarray, b: C.Bounds, budget: int, rng: np.random.Generator,
           mode: str = "score") -> tuple[np.ndarray, np.ndarray]:
    """Return (best_flow per input, best P(attack) per input). flows: (n, 39) raw."""
    flows = np.atleast_2d(flows).astype(np.float64)
    best = C.project(flows, flows, b)
    best_p = score_flows(fit, best)

    iters = budget if mode == "score" else budget * 3
    for t in range(iters):
        step = 0.5 * (1.0 - t / max(iters - 1, 1)) + 0.03   # anneal 0.53 -> 0.03
        cand = C.project(_perturb(best, b, step, rng), flows, b)
        p = score_flows(fit, cand)
        imp = (p < best_p) & C.feasible(cand, flows, b)   # only accept feasible improvements
        if imp.any():
            best[imp] = cand[imp]
            best_p[imp] = p[imp]

    if mode == "strong":
        # coordinate-descent sweep: for each direct feature, try a grid across its box
        grid = np.linspace(0.0, 1.0, 11)
        for ci in _DIRECT:
            for g in grid:
                cand = best.copy()
                cand[:, ci] = b.lo[ci] + g * (b.hi[ci] - b.lo[ci])
                cand = C.project(cand, flows, b)
                p = score_flows(fit, cand)
                imp = (p < best_p) & C.feasible(cand, flows, b)
                if imp.any():
                    best[imp] = cand[imp]
                    best_p[imp] = p[imp]
    return best, best_p


def success_flags(best: np.ndarray, best_p: np.ndarray, flows: np.ndarray,
                  b: C.Bounds, threshold: float, tau_accept: float) -> dict:
    """Per-flow success components of the high-confidence-miss definition (PREREGISTRATION §3)."""
    pred_benign = best_p < threshold
    confidence = np.maximum(best_p, 1.0 - best_p)
    high_conf = confidence >= tau_accept
    feas = C.feasible(best, flows, b)
    func = C.functional(best, b)
    hcm = pred_benign & high_conf & feas & func
    return {
        "pred_benign": pred_benign, "high_conf": high_conf,
        "feasible": feas, "functional": func,
        "high_conf_miss": hcm, "confidence": confidence,
    }


def _self_check() -> None:
    """A toy monotone detector: search must drive its score down under the box."""
    rng = np.random.default_rng(0)
    n = 200
    X = np.abs(rng.normal(100, 30, (n, C.N_FEAT))).astype(float)
    X[:, C.IDX["IN_PKTS"]] = rng.integers(5, 300, n)
    X[:, C.IDX["IN_BYTES"]] = X[:, C.IDX["IN_PKTS"]] * rng.integers(60, 400, n)
    X[:, C._INT_IDX] = np.rint(np.abs(X[:, C._INT_IDX]))
    b = C.derive_bounds(X, "volumetric")

    # detector: P(attack) rises with the (MinMax-scaled) IN_BYTES, a directly-controllable
    # feature, so a feasible attacker can lower it toward the box floor.
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    sc = MinMaxScaler().fit(pd.DataFrame(X, columns=C.FEATURES))
    jb = C.IDX["IN_BYTES"]

    class Toy:
        features = C.FEATURES
        scaler = sc
        _median = pd.Series(np.zeros(C.N_FEAT), index=C.FEATURES)

        class model:
            @staticmethod
            def predict_proba(Xs):
                v = np.asarray(Xs)[:, jb]      # scaled IN_BYTES in [0,1]
                p = 1.0 / (1.0 + np.exp(-(v - 0.5) * 8.0))
                return np.c_[1 - p, p]

    fit = Toy()
    flows = X[:50]
    init = C.project(flows, flows, b)
    feas0 = C.feasible(init, flows, b)
    p0 = score_flows(fit, init)
    best, bp = search(fit, flows, b, budget=60, rng=rng, mode="score")
    feas1 = C.feasible(best, flows, b)
    # search only accepts feasible improvements, so it never worsens feasibility
    assert feas1.mean() >= feas0.mean() - 1e-9, "search worsened feasibility"
    # and it drives the detector score down on the rows that started feasible
    m = feas0
    assert bp[m].mean() < p0[m].mean() - 0.05, \
        f"search did not reduce score: {p0[m].mean():.3f} -> {bp[m].mean():.3f}"
    print(f"evade self-check passed  (mean P on feasible: {p0[m].mean():.3f} -> {bp[m].mean():.3f}, "
          f"feasible start {feas0.mean():.2f} -> end {feas1.mean():.2f})")


if __name__ == "__main__":
    _self_check()
