# Feasibility pilots

Two small pilots for the two strongest candidates in `../REPORT.md`. Hypotheses and failure
conditions were committed before any analysis ran (`PILOT_PLAN.md`, commit `1bcb637`).

```bash
./fetch_data.sh ./data                  # AgentDojo run logs + JailbreakBench artifacts, pinned commits
pip install numpy pandas scipy
python pilot_a.py --data ./data          # residual-vulnerability estimators (pre-specified)
python pilot_a_exploratory.py ./data     # post hoc: exchangeable template variants only
python pilot_b.py --data ./data          # resist vs. stop decomposition of PI defenses
```

CPU only, under five minutes in total. No API calls, no model downloads.

| file | what it holds |
|---|---|
| `richness.py` | Chao2, first-order jackknife, Chao et al. (2014) incidence extrapolation, beta-binomial union |
| `results/pilot_a.{json,md}` | predicted vs. actual K-attack union, by k, every target |
| `results/pilot_a_exploratory.{json,md}` | the same on six near-exchangeable template variants (not pre-specified) |
| `results/pilot_b.{json,md}` | paired state transitions, resist/incapacitate shares, cluster-bootstrap CIs, noise floor |

Deviations from the plan, all disclosed in the report: a beta-binomial predictor was added that
the plan did not list (exploratory; its first run overflowed for k = 2 and its optimiser was
bounded); Pilot B's bootstrap drops resamples with no baseline breach (affects only
Meta-SecAlign, whose 48 baseline breaches make its interval uninformative); one truncated
AgentDojo log without a `utility` field is skipped and listed in `results/pilot_b.json`.
