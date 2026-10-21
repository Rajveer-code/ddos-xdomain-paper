# Pilot plan (written before any pilot analysis was run)

Written 2026-10-21 19:00 UTC, before the analysis scripts below existed. Committed on its own so
the history shows the hypotheses and failure conditions predate the results. Exploratory
descriptive counts of one AgentDojo cross-tab (GPT-4o, base vs. four defenses) had been
looked at when screening candidates; that look is recorded here and the Pilot B hypothesis is
therefore *not* blind to it. Pilot A is blind: no union or estimator had been computed.

Data (public, pinned):

- AgentDojo run logs, `github.com/ethz-spylab/agentdojo` at `089ed468cf3ed0322acc66b0211f26d9d90dbf60`, `runs/`
- JailbreakBench artifacts, `github.com/JailbreakBench/artifacts` at `909e68c01d94222b8ad2e397a017e2e12e2adb73`

Neither is redistributed here; `fetch_data.sh` clones them at these commits.

---

## Pilot A — Can the incidence pattern of a few attacks predict the vulnerabilities they missed?

**Candidate:** F1, residual-vulnerability estimation for AI red-teaming.

**Assumption under test.** The pattern of *which* cases each attack breaks (incidence data:
case × attack) carries usable information about cases that no tested attack broke but some
further attack from the same family would. If it does not, species-richness estimators add
nothing over reporting the observed union, and the candidate collapses into the union-coverage
reporting already proposed by Maple et al. (arXiv 2605.09070).

**Design.** For a target with K attacks, draw every (or up to 200 random) subset of k < K
attacks. From the k-attack incidence matrix, predict the union attack success rate (fraction
of cases broken by at least one attack) over all K attacks. Compare predictors:

1. best single attack in the subset (the conventional headline number);
2. observed union over the k attacks (Maple et al.'s union coverage);
3. Chao2 (bias-corrected, incidence-based) richness, extrapolated to K occasions with the
   Chao et al. (2014) incidence extrapolation formula;
4. first-order jackknife extrapolated the same way (as a second, differently-biased estimator).

**Targets.** AgentDojo GPT-4o-2024-05-13, the 10 injection attacks that target integrity
(`direct`, `ignore_previous`, `important_instructions` and its five name variants,
`injecagent`, `tool_knowledge`) over 629 cases; JailbreakBench, each of the four target
models with its 4–5 attacks over 100 behaviours.

**Primary metric.** Mean absolute error (percentage points) of the predicted K-attack union,
averaged over subsets, at each k. Secondary: how often the predictor under-predicts.

**Expected if the hypothesis holds.** Estimators 3–4 have lower error than predictor 2 at
small k on most targets, and predictor 1 is far below the union.

**Falsified if.** Estimators 3–4 do not beat predictor 2 on mean absolute error at k = 2 and
k = 3 on at least two of the three target families (AgentDojo; JBB open models; JBB API models),
or they over-predict on average (Chao-type estimators are supposed to be lower-bound-like;
systematic over-prediction would mean the incidence pattern is misleading here).

**Known limits, stated now.** (i) The "truth" is the union over the K attacks we happen to
have, not the full attack surface; this tests within-family extrapolation only. (ii) Attacks
are not exchangeable draws: five AgentDojo attacks differ only in names. Correlated occasions
bias richness estimators downward; the pilot reports this rather than correcting for it.
(iii) JailbreakBench labels come from an LLM judge; AgentDojo labels from deterministic
environment checks. (iv) K is small (4–10), so this is a feasibility check, not a validation.

**Synthetic check (run alongside).** Simulate cases with heterogeneous per-attack success
probabilities, with and without correlation between attacks, and confirm the estimator code
recovers known unions where its assumptions hold and under-predicts where attacks are
positively correlated.

---

## Pilot B — Does a prompt-injection defense stop the attack, or stop the agent?

**Candidate:** F2, separating resistance from incapacitation in defense evaluation.

**Assumption under test.** Defenses differ materially in how much of their reduction in attack
success comes from the agent stopping (neither the user task nor the injection completes)
versus resisting (user task completed, injection not executed), so a single ASR misranks them.

**Design.** Pair each case (suite, user task, injection task, attack) between the undefended
and defended configuration of the same model. Classify each run as clean (utility, no breach),
stopped (no utility, no breach), hijacked (breach, no utility) or both (breach and utility).
Among cases breached without the defense, report the share that the defense moves to clean
versus stopped. Rank defenses by ASR and by a resistance rate (breach→clean among baseline
breaches).

**Noise floor.** No replicate runs exist. Proxy: between two attack variants that differ only
in names (`important_instructions` vs `important_instructions_no_names`, same model, no defense),
the rate at which non-breached cases flip between clean and stopped. A defense's
incapacitation share is only informative if its breach→stopped rate exceeds this flip rate.

**Targets.** GPT-4o-2024-05-13 with `repeat_user_prompt`, `spotlighting_with_delimiting`,
`tool_filter`, `transformers_pi_detector`; Llama-3.3-70B and Meta-SecAlign-70B, each with and
without `repeat_user_prompt`, three attacks each.

**Falsified if.** The breach→stopped share is within the noise floor for every defense, or the
ranking by resistance rate equals the ranking by ASR for every model with ≥3 defenses.

**Known limits.** One run per configuration; one model family carries the 4-defense
comparison; utility is AgentDojo's own checker; the descriptive cross-tab for GPT-4o was seen
during screening (above).
