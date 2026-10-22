# P-1 — *Hiding in the Shift*

Label-free monitors do not see a cross-testbed DoS detector that is already high-confidence wrong.

A defensive-security study (self-red-team of a flow-based DoS detector) built on top of P11 in this
repository. **The manuscript is [`MANUSCRIPT.md`](MANUSCRIPT.md).** All numbers are pinned to
`results/p1/summary_p1.json` and verified by `check_numbers_p1.py`.

## Headline (full run: 5 seeds, 4 models, NetFlow v2 quartet)

- Across the 12 ordered source→target pairs × 4 models (240 configs), a cross-testbed DoS detector
  already classifies a **mean 67.9% (range 0–100%)** of real target DoS flows as benign **at high
  confidence** — before any attack. The label-free confidence monitors (ATC, confidence drift) are
  model-dependently blind to it: **36/240 configs** pair high latent exposure with both monitors
  silent, and the blindness aligns with exposure (LogisticRegression most exposed and most silent;
  RandomForest least exposed, never silent).
- A constrained, score-only, traffic-plausible adversary *widens* the hole only where the detector
  has headroom (search's own contribution up to +0.607) and adds nothing where it is already
  saturated. Its power is confidence, not evasion.
- The obvious responder-side defence (watch the low-controllability features) fails a pre-registered
  bar everywhere, because those features do not transfer across independent testbeds either.

## Layout

| file | what |
|---|---|
| `PREREGISTRATION.md` | threat model, frozen choices, success definition, falsifiers, dated amendments — committed before any attack code |
| `MANUSCRIPT.md` | the paper (abstract, intro, related work, threat model, methods, results, discussion, limitations, ethics, reproducibility) |
| `constraints.py` | feasible-set checker + projection operator (Merzouk's four criteria) |
| `p1common.py` | memory-bounded loader + leakage-safe fit (reuses `src/`) |
| `monitors.py` | label-free monitor battery, source-validation null calibration |
| `evade.py` | the constrained score-only / strong search |
| `defend.py` | low-controllability novelty defence |
| `run_phase{1,2,3,4}.py` | per-phase entry points |
| `matrix_latent.py`, `matrix_attack.py` | full 12-pair transfer matrix (latent; adversarial) |
| `budget_curve.py`, `tau_sensitivity.py` | query-budget and operating-point robustness |
| `compute_lift.py`, `aggregate_p1.py` | honest latent/projected/searched decomposition; keyed summary |
| `make_figures_p1.py` | `fig1`–`fig5` (300 dpi, colourblind-safe) |
| `check_numbers_p1.py` | verifies every headline number in the manuscript against the results |
| `STATUS.md` | on-disk ledger / resume point |

## Reproduce

```bash
# from the repository root, with the NetFlow v2 data downloaded into data/
python research-opportunities/p1/run_phase1.py      # constraints + controllability (Gate 1)
python research-opportunities/p1/run_phase2.py      # monitor baseline
python research-opportunities/p1/run_phase3.py      # attack + monitors (Gate 3)
python research-opportunities/p1/run_phase4.py      # defence (Gate 4)
python research-opportunities/p1/matrix_latent.py   # full transfer matrix (latent)
python research-opportunities/p1/compute_lift.py && python research-opportunities/p1/aggregate_p1.py
python research-opportunities/p1/make_figures_p1.py
python research-opportunities/p1/check_numbers_p1.py   # must pass
```

Seeds are fixed (42–46); every module has a runnable self-check (`python <module>.py`). Memory is
bounded by a streaming loader, so the 17–30M-row parquets never materialize.

## Scope / honesty

One feature family (NetFlow v2); feature-space only (no wire-realizability claim); both attacked
sources are volumetric-only. The 240-config generality result is latent exposure + monitor response;
the adversarial/defence study is the two-source → one-target set (and the full adversarial matrix in
`matrix_attack.py`). Negatives (failed defence, model-dependent limits) are reported as results.
