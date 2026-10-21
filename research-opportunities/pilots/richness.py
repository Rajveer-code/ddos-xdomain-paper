"""Incidence-based estimators of how many cases a family of attacks can break.

A case is a "species", an attack is a "sampling occasion", and a case is "detected" by an
attack that breaks it. From a cases x attacks 0/1 matrix built with T attacks, each predictor
returns the number of cases it expects T + t attacks from the same family to break.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln


def frequency_counts(Y):
    """Y: (n_cases, T) 0/1. Returns S_obs, Q1, Q2, T, per-case detection counts."""
    Y = np.asarray(Y, dtype=int)
    counts = Y.sum(axis=1)
    return int((counts > 0).sum()), int((counts == 1).sum()), int((counts == 2).sum()), Y.shape[1], counts


def chao2_undetected(Q1, Q2, T):
    """Bias-corrected Chao2 estimate of vulnerable cases no tested attack broke (Chao 1987/2005)."""
    if T < 2 or Q1 == 0:
        return 0.0
    k = (T - 1) / T
    return k * Q1 * (Q1 - 1) / (2 * (Q2 + 1)) if Q2 == 0 else k * Q1 * Q1 / (2 * Q2)


def jackknife1_undetected(Q1, T):
    """First-order incidence jackknife (Burnham and Overton 1978)."""
    return Q1 * (T - 1) / T if T > 1 else 0.0


def extrapolate(S_obs, Q1, T, Q0, t):
    """Chao et al. (2014, Ecol. Monogr.) incidence extrapolation from T to T + t occasions."""
    if t <= 0 or Q0 <= 0 or Q1 == 0:
        return float(S_obs)
    return S_obs + Q0 * (1 - (1 - Q1 / (T * Q0 + Q1)) ** t)


def betabinom_union(counts, T, K):
    """Fit p_i ~ Beta(a, b), counts_i ~ Binomial(T, p_i) by ML; return expected cases broken
    by at least one of K attacks: n * (1 - E[(1 - p)^K])."""
    counts = np.asarray(counts)

    # log-parameters bounded to [-8, 8]: with T <= 3 the likelihood is often flat in one
    # direction and an unbounded optimiser walks a or b off to overflow.
    def nll(theta):
        a, b = np.exp(np.clip(theta, -8, 8))
        return -np.sum(betaln(counts + a, T - counts + b) - betaln(a, b))

    res = minimize(nll, x0=[0.0, 0.0], method="L-BFGS-B", bounds=[(-8, 8), (-8, 8)])
    a, b = np.exp(res.x)
    p_none = np.exp(betaln(a, b + K) - betaln(a, b))
    return len(counts) * (1 - p_none)


def predict_union(Y_sub, K):
    """All predictors of the K-attack union, from a T-attack submatrix. Returns case counts."""
    n = Y_sub.shape[0]
    S_obs, Q1, Q2, T, counts = frequency_counts(Y_sub)
    t = K - T
    best_single = int(np.asarray(Y_sub).sum(axis=0).max())
    q0_c = chao2_undetected(Q1, Q2, T)
    q0_j = jackknife1_undetected(Q1, T)
    out = {
        "best_single": best_single,
        "observed_union": S_obs,
        "chao2_extrap": min(n, extrapolate(S_obs, Q1, T, q0_c, t)),
        "jack1_extrap": min(n, extrapolate(S_obs, Q1, T, q0_j, t)),
        "chao2_asymptote": min(n, S_obs + q0_c),
        "betabinom": min(n, betabinom_union(counts, T, K)),
    }
    return out
