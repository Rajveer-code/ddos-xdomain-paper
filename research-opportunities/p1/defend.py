"""
Phase 4: the monitor-side defence.

It watches ONLY the low-controllability features found in Phase 1 (the ones the attacker
cannot freely set; results/p1/feature_controllability.json). The conservative attacker froze
those features at the original attack flow's values, so a successful high-confidence miss still
carries the target attack's responder-side signature on exactly these columns. A novelty score
fitted on SOURCE-benign traffic over these columns should therefore flag the adversarial flows.

The defence is an IsolationForest on the scaled low-controllability columns, fitted on one half
of source-validation benign, with its alarm threshold calibrated on the other half to the same
1% benign false-alarm budget as the other monitors. A flagged flow is escalated and no longer
counts as a successful miss.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sklearn.ensemble import IsolationForest  # noqa: E402
import constraints as C  # noqa: E402


class Defense:
    def __init__(self, low_features: list[str], budget: float = 0.01, seed: int = 42):
        self.cols = [C.IDX[f] for f in low_features]
        self.features = low_features
        self.budget = budget
        self.seed = seed
        self.clf = None
        self.thr = None
        self._med = None

    def _prep(self, X: np.ndarray) -> np.ndarray:
        sub = np.atleast_2d(X)[:, self.cols].astype(np.float64)
        if self._med is None:
            self._med = np.nanmedian(sub, axis=0)
        bad = ~np.isfinite(sub)
        if bad.any():
            sub[bad] = np.take(self._med, np.where(bad)[1])
        return sub

    def fit(self, src_benign_X: np.ndarray) -> "Defense":
        """Fit on one half of source benign, calibrate the threshold on the other half."""
        rng = np.random.default_rng(self.seed)
        n = len(src_benign_X)
        idx = rng.permutation(n)
        half = n // 2
        Xfit = self._prep(src_benign_X[idx[:half]])
        self.clf = IsolationForest(n_estimators=200, random_state=self.seed, contamination="auto")
        self.clf.fit(Xfit)
        cal = self.clf.score_samples(self._prep(src_benign_X[idx[half:]]))
        # lower score = more anomalous; flag the lowest `budget` fraction of benign
        self.thr = float(np.quantile(cal, self.budget))
        return self

    def flag(self, X: np.ndarray) -> np.ndarray:
        """True where the flow is escalated (anomalous on the low-controllability features)."""
        s = self.clf.score_samples(self._prep(X))
        return s < self.thr


def _self_check() -> None:
    rng = np.random.default_rng(0)
    low = ["DST_TO_SRC_SECOND_BYTES", "RETRANSMITTED_OUT_PKTS"]
    # source benign: low-ctrl features near 0
    srcben = np.zeros((2000, C.N_FEAT))
    for f in low:
        srcben[:, C.IDX[f]] = rng.normal(0, 1, 2000)
    d = Defense(low, budget=0.01, seed=0).fit(srcben)
    # benign-like target: should mostly pass
    benign = np.zeros((1000, C.N_FEAT))
    for f in low:
        benign[:, C.IDX[f]] = rng.normal(0, 1, 1000)
    fpr = d.flag(benign).mean()
    # attack-like target: low-ctrl features shifted far -> should be flagged
    atk = np.zeros((1000, C.N_FEAT))
    for f in low:
        atk[:, C.IDX[f]] = rng.normal(12, 1, 1000)
    tpr = d.flag(atk).mean()
    assert fpr < 0.1, f"defence false-alarm too high on benign: {fpr:.2f}"
    assert tpr > 0.8, f"defence missed shifted attack flows: {tpr:.2f}"
    print(f"defend self-check passed  (benign flag {fpr:.3f}, shifted-attack flag {tpr:.3f})")


if __name__ == "__main__":
    _self_check()
