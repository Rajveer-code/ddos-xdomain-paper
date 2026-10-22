"""
Feasible-set checker and projection operator for the P-1 constrained attack.

This is the realism defence against PAVE (feature-space attacks that are invalid on the
wire). A candidate adversarial flow is *feasible* only if it obeys the four Merzouk et al.
(2022) criteria made concrete per feature, with the control-class partition frozen in
``research-opportunities/p1/PREREGISTRATION.md`` §3.

Design decisions (kept deliberately small):

* Flows are 1-D ``float64`` arrays aligned to ``FEATURES`` (``netflow_common_features()``,
  sorted). ``IDX`` maps a feature name to its column.
* The adversary perturbs **directly-controllable** features only. **Indirectly-influenced**
  and **uncontrollable** features are held at the original flow's values during the search
  (the conservative, honest attacker: it cannot freely set the responder's behaviour). This
  is exactly what lets a monitor on the low-controllability features catch the attack —
  Phase 4 tests whether it does.
* ``project`` is a well-defined, idempotent repair: restore immutable features, clip the box,
  round integers, repair the algebraic dependencies, in that order. ``feasible`` verifies the
  result; anything ``project`` could not make feasible (box too tight for a dependency) is
  rejected by the search.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.data import netflow_common_features  # noqa: E402

FEATURES: list[str] = netflow_common_features()
IDX: dict[str, int] = {f: i for i, f in enumerate(FEATURES)}
N_FEAT = len(FEATURES)

# ---- control-class partition (frozen in PREREGISTRATION §3; mechanism-derived) ----

DIRECT = [
    "IN_BYTES", "IN_PKTS", "SRC_TO_DST_SECOND_BYTES", "SRC_TO_DST_AVG_THROUGHPUT",
    "DURATION_IN", "FLOW_DURATION_MILLISECONDS", "CLIENT_TCP_FLAGS",
    "MIN_IP_PKT_LEN", "MAX_IP_PKT_LEN", "LONGEST_FLOW_PKT", "SHORTEST_FLOW_PKT",
    "NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES", "NUM_PKTS_256_TO_512_BYTES",
    "NUM_PKTS_512_TO_1024_BYTES", "NUM_PKTS_1024_TO_1514_BYTES",
]
INDIRECT = [
    "OUT_BYTES", "OUT_PKTS", "DST_TO_SRC_SECOND_BYTES", "DST_TO_SRC_AVG_THROUGHPUT",
    "DURATION_OUT", "SERVER_TCP_FLAGS", "TCP_FLAGS", "TCP_WIN_MAX_IN", "TCP_WIN_MAX_OUT",
    "RETRANSMITTED_IN_BYTES", "RETRANSMITTED_IN_PKTS",
    "RETRANSMITTED_OUT_BYTES", "RETRANSMITTED_OUT_PKTS",
]
UNCONTROLLABLE = [
    "PROTOCOL", "L7_PROTO", "MIN_TTL", "MAX_TTL", "ICMP_TYPE", "ICMP_IPV4_TYPE",
    "DNS_QUERY_TYPE", "DNS_TTL_ANSWER", "DNS_QUERY_ID", "FTP_COMMAND_RET_CODE",
]

# The only continuous features; everything else is integer-valued on the wire.
FLOAT_FEATURES = {
    "SRC_TO_DST_SECOND_BYTES", "DST_TO_SRC_SECOND_BYTES",
    "SRC_TO_DST_AVG_THROUGHPUT", "DST_TO_SRC_AVG_THROUGHPUT",
}
# Features the rate/volume functionality test must keep attack-like (Section 3, "Functionality").
RATE_VOLUME = [
    "IN_BYTES", "IN_PKTS", "SRC_TO_DST_SECOND_BYTES", "SRC_TO_DST_AVG_THROUGHPUT",
]

_IMMUTABLE = INDIRECT + UNCONTROLLABLE
_DIRECT_IDX = np.array([IDX[f] for f in DIRECT], dtype=int)
_IMMUT_IDX = np.array([IDX[f] for f in _IMMUTABLE], dtype=int)
_INT_IDX = np.array([IDX[f] for f in FEATURES if f not in FLOAT_FEATURES], dtype=int)
# project rounds only the features it may have changed; immutable features keep their
# original (already integer on the wire) values untouched.
_DIRECT_INT_IDX = np.array([IDX[f] for f in DIRECT if f not in FLOAT_FEATURES], dtype=int)

_MIN_IP_PKT = 20.0  # smallest possible IP packet, bytes


def _check_partition() -> None:
    allp = DIRECT + INDIRECT + UNCONTROLLABLE
    assert len(allp) == N_FEAT == 39, f"partition covers {len(allp)}, features {N_FEAT}"
    assert set(allp) == set(FEATURES), "partition does not match the shared feature space"
    assert len(set(allp)) == len(allp), "a feature is in two control classes"


_check_partition()


@dataclass(frozen=True)
class Bounds:
    """Per-family feasible-set description, derived from real source attack flows."""

    family: str
    lo: np.ndarray            # per-feature p1 (len N_FEAT)
    hi: np.ndarray            # per-feature p99
    rate_lo: np.ndarray       # p1 on RATE_VOLUME features only (functionality floor)
    rate_hi: np.ndarray

    def to_json(self) -> dict:
        return {
            "family": self.family,
            "features": FEATURES,
            "p1": self.lo.tolist(),
            "p99": self.hi.tolist(),
            "rate_volume_features": RATE_VOLUME,
            "rate_p1": self.rate_lo.tolist(),
            "rate_p99": self.rate_hi.tolist(),
        }

    @staticmethod
    def from_json(d: dict) -> "Bounds":
        return Bounds(
            family=d["family"],
            lo=np.asarray(d["p1"], float), hi=np.asarray(d["p99"], float),
            rate_lo=np.asarray(d["rate_p1"], float), rate_hi=np.asarray(d["rate_p99"], float),
        )


def derive_bounds(X_attack: np.ndarray, family: str) -> Bounds:
    """Per-feature [p1, p99] box from real attack flows of one family. X_attack: (n, N_FEAT)."""
    lo = np.nanpercentile(X_attack, 1, axis=0)
    hi = np.nanpercentile(X_attack, 99, axis=0)
    hi = np.maximum(hi, lo)  # guard degenerate columns
    rv = np.array([IDX[f] for f in RATE_VOLUME], dtype=int)
    return Bounds(family=family, lo=lo, hi=hi, rate_lo=lo[rv].copy(), rate_hi=hi[rv].copy())


def project(cand: np.ndarray, original: np.ndarray, b: Bounds) -> np.ndarray:
    """
    Snap a candidate into the feasible set. Vectorised over rows: cand/original (n, N_FEAT).

    Order: restore immutable -> clip box (direct only) -> round integers -> repair the
    algebraic dependencies by adjusting the directly-controllable side within the box.
    """
    cand = np.atleast_2d(cand).astype(np.float64).copy()
    orig = np.atleast_2d(original).astype(np.float64)
    lo, hi = b.lo, b.hi

    # 1. immutable features frozen at the original flow
    cand[:, _IMMUT_IDX] = orig[:, _IMMUT_IDX]

    # 2. box-clip the directly-controllable features, then round integers
    cand[:, _DIRECT_IDX] = np.clip(cand[:, _DIRECT_IDX], lo[_DIRECT_IDX], hi[_DIRECT_IDX])
    cand[:, _DIRECT_INT_IDX] = np.rint(cand[:, _DIRECT_INT_IDX])

    def col(name):
        return cand[:, IDX[name]]

    def put_clamp(name, vals):
        """Set a directly-controllable feature, clamped to its box so repairs never leave it."""
        i = IDX[name]
        cand[:, i] = np.clip(vals, lo[i], hi[i])

    # 3. dependency repairs. Each clamps to the box, so the output is always in-box; a repair
    #    the box forbids is left unmet and feasible() rejects that row (box/dependency conflict
    #    is a genuine infeasibility the search must avoid, not something to force).
    put_clamp("MAX_IP_PKT_LEN", np.maximum(col("MAX_IP_PKT_LEN"), col("MIN_IP_PKT_LEN")))
    put_clamp("LONGEST_FLOW_PKT", np.maximum(col("LONGEST_FLOW_PKT"), col("SHORTEST_FLOW_PKT")))
    # raise IN_PKTS to cover frozen retransmitted packets before the byte floor uses it
    put_clamp("IN_PKTS", np.maximum(col("IN_PKTS"), col("RETRANSMITTED_IN_PKTS")))
    put_clamp("IN_BYTES", np.maximum.reduce([
        col("IN_BYTES"), _MIN_IP_PKT * col("IN_PKTS"), col("RETRANSMITTED_IN_BYTES")]))

    # mean packet length IN_BYTES/IN_PKTS must sit within [MIN_IP_PKT_LEN, MAX_IP_PKT_LEN]
    mean_len = col("IN_BYTES") / np.maximum(col("IN_PKTS"), 1.0)
    put_clamp("MIN_IP_PKT_LEN", np.minimum(col("MIN_IP_PKT_LEN"), np.floor(mean_len)))
    put_clamp("MAX_IP_PKT_LEN", np.maximum(col("MAX_IP_PKT_LEN"), np.ceil(mean_len)))

    # size-bin counts sum to at most total packets (IN + OUT, OUT frozen)
    bins = ["NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES",
            "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES",
            "NUM_PKTS_1024_TO_1514_BYTES"]
    bidx = [IDX[x] for x in bins]
    total_pkts = col("IN_PKTS") + col("OUT_PKTS")
    binsum = cand[:, bidx].sum(axis=1)
    over = binsum > total_pkts
    if over.any():
        sc = np.where(binsum[over] > 0, total_pkts[over] / binsum[over], 1.0)[:, None]
        cand[np.ix_(over, bidx)] = np.floor(cand[np.ix_(over, bidx)] * sc)

    cand[:, _DIRECT_INT_IDX] = np.rint(cand[:, _DIRECT_INT_IDX])
    return cand


def feasible(cand: np.ndarray, original: np.ndarray, b: Bounds,
             tol: float = 1e-6) -> np.ndarray:
    """Boolean mask (len n): does each row obey box + immutability + integer + dependency?"""
    cand = np.atleast_2d(cand).astype(np.float64)
    orig = np.atleast_2d(original).astype(np.float64)
    ok = np.ones(len(cand), dtype=bool)

    # immutability
    ok &= np.all(np.isclose(cand[:, _IMMUT_IDX], orig[:, _IMMUT_IDX], atol=tol, equal_nan=True),
                 axis=1)
    # box on direct features
    d = cand[:, _DIRECT_IDX]
    ok &= np.all((d >= b.lo[_DIRECT_IDX] - tol) & (d <= b.hi[_DIRECT_IDX] + tol), axis=1)
    # integrality
    ci = cand[:, _INT_IDX]
    ok &= np.all(np.abs(ci - np.rint(ci)) <= tol, axis=1)

    def col(name):
        return cand[:, IDX[name]]

    ok &= col("MAX_IP_PKT_LEN") >= col("MIN_IP_PKT_LEN") - tol
    ok &= col("LONGEST_FLOW_PKT") >= col("SHORTEST_FLOW_PKT") - tol
    ok &= col("IN_BYTES") >= _MIN_IP_PKT * col("IN_PKTS") - tol
    ok &= col("IN_PKTS") >= col("RETRANSMITTED_IN_PKTS") - tol
    ok &= col("IN_BYTES") >= col("RETRANSMITTED_IN_BYTES") - tol
    mean_len = col("IN_BYTES") / np.maximum(col("IN_PKTS"), 1.0)
    ok &= (mean_len >= col("MIN_IP_PKT_LEN") - 1.0) & (mean_len <= col("MAX_IP_PKT_LEN") + 1.0)
    bins = ["NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES",
            "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES",
            "NUM_PKTS_1024_TO_1514_BYTES"]
    binsum = cand[:, [IDX[x] for x in bins]].sum(axis=1)
    ok &= binsum <= col("IN_PKTS") + col("OUT_PKTS") + tol
    return ok


def functional(cand: np.ndarray, b: Bounds, tol: float = 1e-6) -> np.ndarray:
    """Still a working DoS: rate/volume features stay inside the family's [p1,p99] box."""
    cand = np.atleast_2d(cand).astype(np.float64)
    rv = np.array([IDX[f] for f in RATE_VOLUME], dtype=int)
    v = cand[:, rv]
    return np.all((v >= b.rate_lo - tol) & (v <= b.rate_hi + tol), axis=1)


def _self_check() -> None:
    _check_partition()
    rng = np.random.default_rng(0)
    n = 1000
    # internally-consistent synthetic "attack" cloud: packet sizes bracket the mean length,
    # so a feasible region exists and repairs fit inside the box.
    X = np.abs(rng.normal(50, 20, (n, N_FEAT))) + 1.0
    pkts = rng.integers(2, 200, n).astype(float)
    mean_len = rng.uniform(60, 500, n)
    X[:, IDX["IN_PKTS"]] = pkts
    X[:, IDX["IN_BYTES"]] = pkts * mean_len
    X[:, IDX["MIN_IP_PKT_LEN"]] = mean_len * 0.5
    X[:, IDX["MAX_IP_PKT_LEN"]] = mean_len * 1.5
    X[:, IDX["SHORTEST_FLOW_PKT"]] = mean_len * 0.4
    X[:, IDX["LONGEST_FLOW_PKT"]] = mean_len * 1.6
    for bcol in ("NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES",
                 "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES",
                 "NUM_PKTS_1024_TO_1514_BYTES"):
        X[:, IDX[bcol]] = rng.integers(0, 20, n)
    X[:, IDX["OUT_PKTS"]] = rng.integers(0, 50, n)
    X[:, IDX["RETRANSMITTED_IN_PKTS"]] = 0
    X[:, IDX["RETRANSMITTED_IN_BYTES"]] = 0
    # wire-plausible: every non-rate feature is integer-valued, like real NetFlow
    X[:, _INT_IDX] = np.rint(np.abs(X[:, _INT_IDX]))
    b = derive_bounds(X, "volumetric")

    original = X[50:60].copy()
    cand = project(original + rng.normal(0, 30, original.shape), original, b)
    feas = feasible(cand, original, b)
    assert feas.mean() >= 0.5, f"project() left too many infeasible: {feas.mean():.2f}"

    # idempotent on its own output
    cand2 = project(cand, original, b)
    assert np.allclose(cand, cand2, atol=1e-6), "project must be idempotent"

    # immutable features untouched
    assert np.allclose(cand[:, _IMMUT_IDX], original[:, _IMMUT_IDX]), "immutable changed"

    # a wildly out-of-box candidate is caught by feasible() pre-projection
    bad = original.copy()
    bad[:, IDX["IN_PKTS"]] = b.hi[IDX["IN_PKTS"]] * 100
    assert not feasible(bad, original, b).all(), "feasible() missed a box violation"

    # integers are integral after projection
    assert np.allclose(cand[:, _INT_IDX], np.rint(cand[:, _INT_IDX])), "non-integer count"
    print(f"constraints self-check passed  (|direct|={len(DIRECT)} "
          f"|indirect|={len(INDIRECT)} |uncontrollable|={len(UNCONTROLLABLE)})")


if __name__ == "__main__":
    _self_check()
