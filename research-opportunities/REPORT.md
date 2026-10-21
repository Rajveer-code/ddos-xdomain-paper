# Research-opportunity report

**For:** Rajveer Singh Pall · **Prepared:** 21 Oct 2026 · **Scope:** choose the next paper on merit, not continuity

Everything in this directory is new and separate from the *Confidently Wrong* manuscript; nothing
in the paper, its results or its history was changed. Hypotheses tested here were committed before
the analyses ran (`pilots/PILOT_PLAN.md`, commit `1bcb637`).

---

## 0. Bottom line

**Recommendation.** Pursue **F1, residual-vulnerability estimation for AI red-teaming**: estimate,
with stated assumptions and valid uncertainty, how much of an LLM agent's attack surface a finite
red-team *missed*, and separate defenses that make vulnerabilities **rarer** from defenses that make
them **fewer**. It asks the same epistemic question as the quiet-monitor project (what does the
absence of findings license?) in a form that is sharper, measurable on public data, less crowded,
and squarely in AI security.

**Pilot evidence is mixed, and the claim was narrowed because of it.** As pre-specified, the broad
version failed: on JailbreakBench, where the "attacks" are a menu of different algorithms of very
unequal strength, species-richness estimators did not beat simply reporting the observed union.
Where attacks were near-exchangeable draws from one family, they cut prediction error by about
2–4× (AgentDojo's six template variants: 1.7–4.4× at k = 2–5; synthetic exchangeable data:
2.5–6.6× at k = 3–6). The AgentDojo-variant result is post hoc. The paper
therefore stands or falls on a **prospective** test with exchangeable draws (Section 10.12), and
it is defined relative to a *declared* attack distribution, never "the" attack surface.

**Backup.** **F2, "Secure or stopped?"**: decompose a prompt-injection defense's reduction in attack
success into resistance (the agent finishes the user's task and ignores the injection) and
incapacitation (the agent stops). Its pilot supports the effect (AgentDojo's PI detector: 65% of
the breaches it removes end with the agent stopped, 95% CI [0.54, 0.75]; the sandwich defense: 10%)
and the defense ranking changes under it. Lower ceiling: SecFid (ICML 2026 spotlight) and WASP
already separate related outcomes.

**Quiet monitor.** I could not read the manuscript: it is in none of the eight repositories I
cloned, GitHub code search across your account finds no match, and Google Drive returned *Forbidden*. Judged on the field it would enter, it is
**not competitive as the next paper** unless it contains a specific guarantee none of the roughly
twenty AI-oversight monitor papers in the NeurIPS 2026 main track has (Section 5, F4). I recommend pausing it and carrying its
question into F1. Section 5 gives a three-question test you can apply to the manuscript in ten minutes.

**The genre warning that matters most.** "The reported metric does not justify the conclusion" is
now a crowded genre in almost every sub-area of LLM evaluation and security: judges, verifiers,
leaderboards, monitors, jailbreak ASR, agent ASR. Of 7,174 NeurIPS 2026 main-track titles, 101
contain the word "audit". A sixth critique paper adds little to your record. What is
missing from it is a **method with a guarantee that other people can use**. F1 is chosen because
it supplies one.

**Limits of this investigation.** arXiv, OpenReview, ACL Anthology, PMLR, USENIX, ACM, IEEE,
Springer and Hugging Face were blocked from this environment (network policy; only GitHub and PyPI
were reachable). Novelty assessments therefore rest on search-engine abstracts and summaries, the
papers' public GitHub repositories, and the full NeurIPS 2026 accepted-title list (mirrored on
GitHub). **I did not read the full text of any 2026 paper cited below.** Every novelty statement is
scoped accordingly, and Section 10.8 lists what must be read before writing.

---

## 1. Method of investigation

1. Read the research record in the repositories reachable from this session (Section 2).
2. Searched nine directions (A–I) with independent routes: web search with multiple phrasings per
   idea, deliberate disproof searches ("has someone already done X?"), the NeurIPS 2026 accepted list
   (7,174 titles, keyword-scanned), and the GitHub repositories of benchmarks and papers.
3. Generated 17 research questions, screened to five finalists, scored them on the stated
   framework, wrote mini-proposals for the top three, and ran pre-specified pilots for the top two.

Sources actually opened: GitHub repositories (AgentDojo runs, JailbreakBench artifacts, Scale's
MRT code, the NeurIPS 2026 list, all of your repositories). Everything else is from search
summaries.

---

## 2. Research inventory

Statuses come from your research site's data file (`rajveer-research/src/data/research.ts`, which
says it follows `TRUTH.md`, 2026-10-19 block). `TRUTH.md` itself is on your local drive and was not
reachable. "Verified" below means confirmed from a public source in this session.

| | Question | Principal contribution | Status (verification) | Data / code | Strongest result | Known weaknesses | Do not present as new |
|---|---|---|---|---|---|---|---|
| **P9** | Do diabetes risk models survive a new population? | External validation NHANES→BRFSS (1.28M) with subgroup audit | Published, CIPHER-2026 (arXiv 2607.16253 verified; it records the acceptance. The IEEE Xplore DOI on your site was **not** found by search; the arXiv record says DOI pending) | NHANES, BRFSS; Federated-Diabetes repo | AUC 0.794→0.717; age 60+ 0.607 | 8 non-lab predictors; label definitions differ across surveys | That external validation degrades performance |
| **P06b** | Can subgroup AUC improve while the screening decision worsens? | Exact pooled-AUC decomposition; capacity-based audit | Submitted, ML4H 2026 Findings (repo README; not externally verifiable) | Same; 10 seeds | AUC gap 0.0075→0.0005 while sensitivity gap 0.009→0.034 | Small AUC effects; earlier pipeline defects (documented) | That within-group AUC and cross-group terms can diverge (xAUC literature) |
| **P14** | Which leaderboard orderings survive a human reader? | Partial identification of pairwise gaps with a human audit; breakdown values | Submitted, DMLR (repo tag `dmlr-submission` verified; submission itself not verifiable) | Open LLM Leaderboard MATH-Hard; 400-item audit; code public | 174/351 certified at ε=0.01; 0 without pooling; 15.9% reversals on verifier change | Pooling assumption untested; one labeller; one benchmark | Verifier-induced ranking reversals; judge/verifier unreliability (dozens of 2025–26 papers) |
| **P2** | How large and where is the Black–White mortgage approval gap? | DFL, within-lender FE, RDD, DiD, Manski bounds on 42M HMDA records | Under review, J. Housing Economics (SSRN 6334459; not verifiable) | HMDA; code public | 14.95 pp; 74.6% within lender | No credit scores | — |
| **P5** | How do LLMs handle Indian financial regulation? | 406-item benchmark, 12 models | Preprint, arXiv 2604.19298 (verified) | HF dataset, code | 70.4–89.7%; numeric reasoning most discriminative | Human IAA κ lower than model check | — |
| **P11** | Does cross-network DoS detection fail at the threshold or the ranking? | 4 testbeds × 4 families × 5 seeds; ranking/threshold decomposition; label budget | In preparation; arXiv not yet posted (search found nothing; `ARXIV_SUBMISSION.md` ready) | NetFlow-v2 quartet; this repo | 108/240 below AUC 0.5; 11/12 pairs ranking-dominated | 12 pairs; 50k cap | Cross-dataset NIDS collapse (Cantone et al. 2024 and others); ATC-type gap forecasting |
| knowledgeshift | Can a scorer tell a wrong answer from an unreadable one? | Scorer census; identification of orderings | README names an ICLR 2027 write-up; status unknown; appears folded into P14 | private repo | 341/378 orderings not identified | Overlaps P14 | Same as P14 |
| trustshift | Does shift mechanism predict which trust axis fails? | Four-domain audit, "inconclusive" as an outcome | In preparation (README) | public | Lending ranks improve under covariate shift while operating point is flat | Mechanism-vs-magnitude claim not established (its own README) | — |
| Quiet monitor | Unknown (manuscript not reachable) | — | Not on the 2026-10-19 keep list | — | — | — | — |

**Reusable assets for the recommendation.** Your partial-identification machinery (P14, P2), your
habit of pre-specifying and reporting null results (P11 F2, P06b corrections), and the
ranking-versus-threshold lens (P11) all transfer. The AgentDojo/JailbreakBench loaders and estimator
code written for the pilots are the starting codebase.

**Status discrepancies to fix before applications** (they are small, but admissions readers check):

- The IndiaFinBench Hugging Face Space header says "EMNLP 2026"; your site and the `TRUTH.md`
  convention say arXiv preprint. If it was not accepted at EMNLP, change the Space header.
- Your site describes IndiaFinBench's human study as 180 items (κ 0.645); the arXiv abstract
  describes 60 items (κ 0.611). Probably a version difference; make them agree or name the version.
- The P9 IEEE Xplore DOI could not be confirmed from here. Check that the DOI resolves before
  listing it as the primary link.

---

## 3. What the field looks like (nine directions)

| Dir. | Area | State in Oct 2026 | Representative evidence (search-verified titles/abstracts) | Open space, if any |
|---|---|---|---|---|
| A | Evaluation validity, shift, label-free performance | Mature methods; active harmful-shift monitoring | Dis² (NeurIPS'23), ODD (2506.14978), Podkopaev & Ramdas (ICLR'22), Amoukou et al. (NeurIPS'24), prediction-powered risk monitoring (2602.02229) | Little for a student without a new theorem |
| B | LLM judges, verifiers, reward models | **Saturated** | Coin Flip for Safety (ICML'26), Nine Judges Two Votes (2605.29800), Partial Identification from LLM Prompts (2606.15031), BACON, JudgeSense, Forced Orders, Rank Intervals, SOTA or Luck (all NeurIPS'26) | P14's own next step (test the pooling assumption); not a new paper |
| C | Agent security, monitors, runtime enforcement | Monitors **saturated**; agent-security evaluation **filling fast** | About twenty AI-oversight monitor papers at NeurIPS'26 incl. Tight PAC-Bayes guarantees for safety monitoring and an untrusted-monitoring safety case; SLEIGHT-Bench; A False Average (2608.00583); Recall Is Not Protection (2609.05797); ASR Is Not a Number (2609.25173); SecFid (2606.30783); Defense Trilemma (2604.06436); AgentLAB (ICML'26) | Coverage/residual risk of red-teaming (F1); resist vs. stop (F2); verifier information access (F5) |
| D | Adversarial ML / security evaluation | Static-vs-adaptive gap well documented; little predictive theory | The Attacker Moves Second (USENIX Sec'26); RETA, PISmith, AutoDojo; Risk Under Pressure (2606.11409); DAPRO (2605.06605); MIA reliability (2605.25819); Causal Evaluation of MIA (NeurIPS'26) | Inference about what an evaluation did *not* find (F1) |
| E | Multilingual / population-dependent evaluation | Judge bias across languages done; Indic guards emerging | Fu & Liu (EMNLP-F'25); MM-Eval; IndicGuard (2606.22841); PolyGuard; Safety Alignment Illusion (2608.18131) | Multilingual over-defense of PI detectors: PIDS-Bench (2609.15017) names it as open (F3) |
| F | Benchmarks, retrieval, coverage | Active | Coverage, Not Averages (2604.20763); Single-configuration ASR is not enough (2605.09070, union coverage) | Union coverage *observed*, not *estimated* |
| G | SE / security of AI-enabled systems | Vulnerability-detection validity well covered; secure-code oracles partly open | PrimeVul; CWEval; BaxBench; RealSec-bench; static-analyser oracle weaknesses reported | Oracle-disagreement certification of secure-code leaderboards (a P14 transplant) |
| H | Theory of inversion / transfer | Old results cover it | Spurious-correlation reversal (IRM's coloured MNIST) | Weak |
| I | Software-testing statistics (independent route) | Mature in fuzzing, absent in AI red-teaming | STADS (Böhme, TOSEM'18), residual risk in greybox fuzzing (FSE'21), capture–recapture for inspections (Briand et al. 2000) | **The bridge F1 uses** |

Two observations shaped the decision. First, the critique genre is crowded everywhere in B and C;
second, the statistics of *inference from absence* (species richness, cure-fraction survival models,
residual risk in fuzzing) is mature elsewhere and, as far as these searches reach, unused in AI
red-teaming.

---

## 4. Longlist: 17 research questions, screened

Each row: problem → why it matters → what existing work fails to establish → research question →
hypothesised contribution → what would support it → what would refute it → screening verdict.

| # | Research question | Gap and hypothesised contribution | Supports / refutes | Verdict |
|---|---|---|---|---|
| L1 | Given a label-free drift monitor that stays quiet, what performance loss is still consistent with the evidence? (quiet monitor, shift reading) | Bound worst-case degradation over the shift set the monitor cannot detect | Support: bound tighter than Dis²/ODD and covers truth on real shifts. Refute: bound vacuous on P11's 12 pairs | Merged into F4 |
| L2 | Given a sabotage monitor that never fires, how much undetected attack is consistent with red-team data? (quiet monitor, control reading) | Undetected-attack bound with threshold and attack-shift uncertainty | Support: valid bound on SHADE-Arena/BCB held-out attacks. Refute: equals bootstrap CI already reported (Retrying vs Resampling, 2605.26047) | Merged into F4 |
| L3 | Does P14's pooling assumption hold model by model in the concordant cells? | P14's stated next step | Labels drawn by model in concordant cells | Out: extension of P14, not a new paper |
| L4 | Which jailbreak-ASR orderings survive the judge? | P14 method on jailbreak benchmarks | — | Out: Coin Flip, Concerns in Benchmarking Jailbreaks (2610.26595), PandaGuard; and a renamed P14 |
| L5 | Do secure-code-generation leaderboard orderings survive the choice of security oracle? | Certify orderings under CodeQL/exploit/LLM-judge disagreement | Support: many reversals; few certified. Refute: oracles agree | Out of top five: P14 transplant; generation cost |
| L6 | **What fraction of cases is vulnerable to a declared attack family, beyond what k attacks found?** | No estimator of the *unobserved* union exists for red-teaming (union coverage is only reported as observed); species-richness and cure-fraction methods supply one; separates rarer from fewer | Support: estimators from k draws predict the 10k-draw union better than the observed union, with valid lower bounds. Refute: no gain on exchangeable draws | **Finalist F1** |
| L7 | **Does a PI defense stop the attack or stop the agent?** | Paired four-state decomposition, noise-aware; availability accounting | Support: incapacitation shares differ and reorder defenses. Refute: within noise | **Finalist F2** |
| L8 | **Do fail-closed PI detectors deny service disproportionately to Indic and code-mixed users?** | Over-defense measured in English only; fairness × security × Indic | Support: benign FPR gaps by language at deployment thresholds. Refute: parity | **Finalist F3** |
| L9 | **What must an independent action verifier see to catch injected tool calls without being injected itself?** | Information access studied for sabotage monitors, not for PI action verifiers | Support: an information-access setting dominates at fixed FPR under adaptive attack. Refute: full context dominates | **Finalist F5** |
| L10 | Can benign-only target traffic reveal whether a security detector's ranking has inverted? | Partial identification of target AUC from target benign + source attacks | Support: informative bounds on P11 pairs. Refute: bounds vacuous unless attack invariance, which P11 contradicts | Out: overlaps P11 §4.10; likely negative |
| L11 | Are published agent-security defense differences statistically distinguishable? | Crossed random effects; power | — | Out: ASR Is Not a Number (2609.25173) did it |
| L12 | When does distribution shift push AUC below 0.5? | Characterisation of inversion | — | Out: known from spurious-correlation reversal |
| L13 | Which RAG system orderings survive LLM relevance judges? | P14 on retrieval | — | Out: crowded; renamed P14 |
| L14 | Does answer extraction fail more in non-Latin scripts in multilingual math benchmarks? | knowledgeshift extension | — | Out: low significance; overlaps knowledgeshift |
| L15 | Do vulnerability-detection benchmarks' labels support their accuracy claims? | Label validity | — | Out: PrimeVul, Risse & Böhme, Croft et al. |
| L16 | Are low-FPR MIA evaluations statistically reliable? | CIs at low FPR | — | Out: 2605.25819; Causal Evaluation of MIA (NeurIPS'26) |
| L17 | When can a negative capability evaluation conclude absence? | Hypothesis tests for absence | — | Out: Bukkapatnam & Karuturi (ICML'26) |

Screening rules applied: out if a 2025–26 paper already answers the question, if it is a renamed
P14, if a credible test needs data or compute out of reach, or if the likely result is a reporting
recommendation with no method.

---

## 5. Five finalists

### F1. Residual-vulnerability estimation (rarer or fewer?)

**Working title.** *Rarer or Fewer? Estimating the Residual Attack Surface of LLM Agents from Finite Red-Teaming*

**Research questions.** (RQ1) For a declared attack distribution 𝒜 (a parameterised template
family with sampling randomness, or an optimiser with random seeds), what fraction of cases is
vulnerable to 𝒜 at all, and what does a k-draw evaluation license about it? (RQ2) Can the expected
union after m > k draws be predicted from k draws with valid uncertainty? (RQ3) Do published
defenses make vulnerabilities rarer (lower per-draw success, same support) or fewer (smaller
support), and does the single-draw ASR rank them correctly?

**Estimand.** Per case c, v_c = P_{a∼𝒜}(breach). Single-draw ASR = E[v_c]. Expected union after m
draws U(m) = E[1 − (1 − v_c)^m]. Vulnerable fraction θ = P(v_c > 0) = lim U(m). A defense can lower
E[v_c] a lot while leaving θ almost unchanged ("rarer"), or lower θ ("fewer"). The canonical ASR
cannot tell these apart.

**Contributions (to be established, not yet established).** (1) The estimand and the rarer/fewer
distinction, formally. (2) Identification: θ is not identified from finite k without a condition on
the mass of v near zero (the analogue of survival analysis' "sufficient follow-up" for cure
fractions); a lower bound is (Chao-type estimators are lower bounds under heterogeneity); U(m) for
m up to a constant multiple of k is estimable with explicit error (Chao et al. 2014; Orlitsky, Suresh
and Wu 2016 for the abundance analogue). (3) Design rule backed by the pilot: estimates are only
valid when draws are exchangeable; a menu of distinct attack algorithms breaks them. (4) A
red-teaming stopping rule from the discovery probability (Good–Turing, as STADS did for fuzzing).
(5) Re-evaluation of prompt-injection and jailbreak defenses on the rarer/fewer axis.

**Method.** Incidence-based richness (Chao2, jackknife, Chao et al. extrapolation) for shared-draw
designs; mixture-of-binomials / beta-binomial and nonparametric-MLE bounds for per-case replicated
designs; a sufficient-follow-up test before reporting θ̂; cluster bootstrap over cases for CIs.

**Baselines.** Best single configuration (convention); observed union coverage (Maple et al.,
2605.09070); best-of-N power-law extrapolation (Hughes et al. 2412.03556); distributional
estimator of per-problem success (Schaeffer et al. 2502.17578); extreme-value forecasting (Jones et
al. 2502.16797); conformal survival bounds on iterations-to-jailbreak (DAPRO, 2605.06605).
Criterion: error predicting held-out U(m) at m = 2k…10k, CI coverage, and lower-bound validity.

**Evaluation.** Synthetic (known v-distributions, including point mass at zero and heavy mass
near zero, where identification must fail); prospective exchangeable-draw data (best-of-N
augmentations and template grids on 2–3 open models; AgentDojo with resampling); application to
defenses.

**Data.** AgentDojo run logs and JailbreakBench artifacts (public, on GitHub); new draws generated
by you (Section 10.9).

**Closest work and the exact distinction**

| Paper | Its question | Setting / assumptions | Method / guarantee | Data, metrics | Finding | Stated limits | Code | What F1 adds |
|---|---|---|---|---|---|---|---|---|
| Maple, Kumar, Tapwal 2026 (2605.09070) | Is single-configuration ASR enough? | Parameterised jailbreaks; tested variants only | Variant sensitivity (VSM), observed union coverage (UC) | HarmBench-100; PAIR, bijection | PAIR best 69% vs UC 88%; bijection 81% vs UC 100% over 36 variants | Variant selection ad hoc (secondary summary) | not checked | Estimates the *unobserved* union and θ with uncertainty; stopping rule; rarer/fewer |
| DAPRO, "How Many Iterations to Jailbreak?" (2605.06605; NeurIPS'26) | Lower bounds on time-to-jailbreak under a budget | Multi-turn, censored events | Conformal survival, dynamic allocation; finite-sample coverage | jailbreak and task events | tighter bounds than static allocation | — | not checked | Targets the vulnerable *fraction* (a cure fraction), not per-prompt time; extrapolation across draws; defenses compared on support |
| Risk Under Pressure (2606.11409) | ASR as a function of attacker compute | 10 models, 3 attack types | Risk–compute curves (FLOPs) | 2 jailbreak benchmarks | Alignment non-monotone in compute space | — | not checked | Compute curves are observed, not extrapolated beyond budget; no support estimand |
| Hughes et al. 2024, Best-of-N (2412.03556) | How ASR scales with attempts | Random augmentations | Power-law fit to −log ASR | many models | Power-law scaling | Fit is empirical | public | Lower bound and identification conditions; per-case support |
| Schaeffer et al. 2025 (2502.17578) | Why aggregate power laws arise | Per-problem success distribution | Distributional estimator | math, jailbreaks | Power law from mass near zero | — | public | Same mechanism read as an identification problem for θ; cure-fraction view |
| Jones et al. 2025 (2502.16797) | Forecast deployment-scale rare behaviour | Elicitation probabilities | Extreme-value (Gumbel) forecasting | misuse behaviours | Forecasts over 3 orders of magnitude | — | — | Different target (worst-query probability); F1 targets case coverage of an attack family |
| Nasr et al. 2025, The Attacker Moves Second (2510.09023; USENIX Sec'26) | Do defenses survive adaptive attacks? | 12 defenses | Adaptive optimisation, human red-teaming | AgentDojo, others | >90% ASR on most defenses reporting ≈0% | — | — | Statistical account of what a static evaluation leaves undiscovered within a family; does not replace adaptive attacks |
| Böhme, STADS (TOSEM'18); residual risk in greybox fuzzing (FSE'21) | When to stop fuzzing; residual risk | Inputs as species; adaptive bias | Good–Turing discovery probability; bias corrections | fuzzing campaigns | Blackbox estimators underestimate under adaptivity | adaptive bias | — | Transfers the framework to LLM red-teaming, where draws are stochastic, judges err, and attacks are templated |
| ASR Is Not a Number (2609.25173) | Is agent ASR comparable across papers? | 259-paper meta-analysis | power analysis, checklist | — | 58–65% report no variance | — | — | Provides an estimator, not a checklist |

Novelty statement, scoped: in four independent searches (different phrasings, the NeurIPS 2026
accepted list, citation-adjacent searches on fuzzing residual risk and union coverage), I found no
application of species-richness, capture–recapture or cure-fraction estimation to LLM red-teaming or
agent-security evaluation. Full texts of Maple et al., DAPRO and Risk Under Pressure were not read;
an extrapolation component inside any of them would reduce F1's novelty to its rarer/fewer analysis
and identification results. Read those three first.

### F2. Secure or stopped?

**Working title.** *Secure or Stopped? Separating Resistance from Incapacitation in Prompt-Injection Defense Evaluation*

**Research questions.** How much of each defense's ASR reduction comes from the agent stopping,
and does ranking by resistance reverse rankings by ASR? How much of the apparent decomposition is
run-to-run noise?

**Contribution.** Four-state paired outcome model (clean, stopped, hijacked, both); decomposition
of ΔASR into resistance and incapacitation; noise-aware estimation using replicate runs; an
availability-adjusted attacker-success metric (an attacker who wants the agent to fail also wins
when it stops).

**Closest work.** SecFid (2606.30783, ICML'26 spotlight) separates resisting, executing and
processing-as-data and proves no universal defense when benign and adversarial inputs overlap; WASP
(NeurIPS'25 D&B) names "security by incompetence"; AgentDojo's authors note low-utility models look
secure; ASR Is Not a Number (2609.25173); the Defense Trilemma (2604.06436); From Shield to Target
(2606.14517) on guardrail DoS. **Distinction:** a paired, per-case causal decomposition with a noise
floor, applied across published defenses; the others report marginal metrics or theory.

### F3. Who gets locked out?

**Working title.** *Fail-Closed, Locked Out: Language-Dependent Denial of Service from Prompt-Injection Defenses*

**Question.** At deployment thresholds set on English data, do PI detectors flag benign Hindi,
Tamil, Bengali and code-mixed tool content at higher rates, and what share of agent tasks does that
abort for those users?

**Closest work.** PIDS-Bench (2609.15017) is English-only and names multilingual as a priority
extension; model cards report Hindi FPR ≈0.61 on translated sets (self-reported); IndicGuard
(2606.22841) and PolyGuard address harmful-content guards, not injection detectors; Passing the Test
You Trained On (2610.03448) shows detector rankings transfer poorly. A 2026 *Scientific Reports*
paper on PI detection in Indian multilingual LLMs exists and was not read. **Distinction:**
availability harm, measured as task-level denial of service by language, rather than detector
accuracy.

### F4. The quiet-monitor project (as best it can be judged)

Without the manuscript, two readings were assessed. **Shift reading:** bound the degradation a
silent label-free drift monitor permits. Closest: Dis² (Rosenfeld & Garg, NeurIPS'23), ODD
(2506.14978), harmful-shift detection (Podkopaev & Ramdas; Amoukou et al.), prediction-powered risk
monitoring (2602.02229). **Control reading:** bound the undetected attacks a silent sabotage monitor
permits. Closest: Tight PAC-Bayes Generalisation Guarantees for LLM Safety Monitoring and *When can
we trust untrusted monitoring?* (both NeurIPS'26 main track), SHADE-Arena, Arike et al. (ICLR/ICML'26),
Kale et al. MRT (ICLR'26 oral), Terekhov et al. (ICLR'26), A False Average, Recall Is Not Protection,
SLEIGHT-Bench, and a NeurIPS'26 abstract titled *The Operating Point Moves More Than the Ranking*
(probe monitor; recall and FPR move at a frozen threshold while AUROC does not; effective n ≈ 10;
author not identified, so if it is yours, note that it is already your most direct overlap).

**Ten-minute test for the manuscript.** Keep it as the next paper only if all three are yes:

1. Does it state a quantitative bound or guarantee that holds under a *stated* adversary or shift,
   with the assumption carried as a parameter rather than fixed?
2. Is that bound checked against ground truth on public data (SHADE-Arena, BigCodeBench-Sabotage,
   SLEIGHT-Bench, or your own P11 pairs)?
3. Is its central claim absent from the two NeurIPS'26 monitoring-guarantee papers above and from
   A False Average and Recall Is Not Protection?

### F5. What should an action verifier see?

**Working title.** *What Should an Action Verifier See? Information Access and Correlated Failure in Independent Checks of Agent Tool Calls*

**Question.** For a verifier that approves consequential tool calls, which inputs (user goal and
proposed call; plus trusted context; plus untrusted tool output) maximise catch rate at fixed benign
FPR under injections that also target the verifier, and how correlated are verifier and agent
failures in each setting?

**Closest work.** Arike et al. (less-is-more for sabotage monitors); Terekhov et al. (injections
subvert monitors); LlamaFirewall AlignmentCheck (2505.03574) and its evasion in 2510.17276; CaMeL
(Debenedetti et al. 2025, not re-verified this session); correlated-verifier cascades (2607.13918).
**Distinction:** the information-access question for PI action verifiers, measured offline on
public AgentDojo trajectories (which already contain the calls and outputs a verifier would see).

---

## 6. Scores

Scale 1–10 per dimension; weights as specified. Scores after the pilots, with the pre-pilot score in
brackets where it changed. These are decision aids.

| Dimension (weight) | F1 residual vulnerability | F2 secure or stopped | F3 locked out | F4 quiet monitor | F5 verifier access |
|---|---:|---:|---:|---:|---:|
| Originality, defensibility of gap (25%) | 7 [7.5] | 5 | 6.5 | 4.5 | 6 |
| Technical depth (20%) | 8 [7.5] | 6 | 5 | 6 | 6.5 |
| Significance (15%) | 7.5 | 6.5 | 6.5 | 6.5 | 7 |
| Feasibility of rigorous validation (15%) | 6.5 [8] | 8 [8.5] | 6 | 7 | 5 |
| Relevance to intended fields (10%) | 9 | 9 | 8 | 9 | 9 |
| Builds on record without duplication (5%) | 7 | 7 | 8 | 7 | 5 |
| Data, tools, compute (5%) | 6.5 [8] | 8 [9] | 6 | 6 | 6 |
| Venue fit and completion (5%) | 7 | 6 | 6 | 5 | 7 |
| **Weighted** | **7.38** [7.70] | **6.58** [6.70] | **6.30** | **6.15** | **6.40** |

Evidence behind the less obvious ratings:

- F1 originality fell from 7.5 to 7 after DAPRO and Risk Under Pressure surfaced; depth rose because
  the identification problem (cure fraction, sufficient follow-up) is real theory rather than a
  reporting choice; feasibility fell because the broad version failed its pilot and the claim now
  needs new exchangeable-draw data.
- F2's feasibility is high (data in hand, effect visible) but its originality is capped by SecFid and WASP.
- F4 is scored on the field it would enter, not on the manuscript, which I could not read.
- F5 needs verifier calls on thousands of trajectory steps (API spend or a local GPU) and could not be piloted here.

Sensitivity: F1 stays first unless roughly 23 points of weight move from originality to feasibility
(feasibility ≈ 38%), at which point F2 overtakes it.

---

## 7. Mini-proposals for the top three

### 7.1 F1 — Rarer or fewer?

- **Research question.** What does a k-draw red-team license about the fraction of cases vulnerable to a declared attack distribution, and do defenses make vulnerabilities rarer or fewer?
- **Gap.** Union coverage is reported as observed (Maple et al.); scaling laws and forecasts describe ASR or worst-query probability, not the vulnerable support; fuzzing's residual-risk statistics have not been carried to LLM red-teaming (as far as searched).
- **Contribution.** Estimand; identification (lower bound identified, upper bound not without a tail condition); extrapolation with error control; exchangeability design rule; stopping rule; defense re-evaluation.
- **Method.** Prove the lower-bound and non-identification statements for the mixture-of-binomials model; implement Chao2/jackknife/extrapolation, NPMLE bounds and a sufficient-follow-up test; cluster bootstrap.
- **Baselines.** Best single; observed union; BoN power law; Schaeffer distributional estimator; DAPRO; Jones EVT. Beat them on held-out U(m) error and lower-bound validity, not on ASR.
- **Experiments.** Synthetic families where the answer is known, including ones built to break each estimator. Prospective data: per case, 50–100 exchangeable draws from (a) best-of-N augmentations, (b) a template-parameter grid, on 2–3 open models; AgentDojo with 20+ resampled template draws per case. Defenses: sandwich, spotlighting, tool filter, PI detector, SecAlign.
- **Metrics.** MAE and coverage for U(m) at m = 2k…10k; lower-bound violation rate; θ̂ with CI; rarity ratio E[v]/θ.
- **Ablations and robustness.** k; number of cases; correlated draws (near-duplicates); occasion heterogeneity (strong and weak attacks mixed, the JailbreakBench failure); judge error (simulated flips plus a human audit of 200 judged outputs); model family; benchmark.
- **Reproducibility.** Seeds and full draw logs; incidence matrices released; one script per table; pinned data commits; cost recorded per run.
- **Limitations.** Says nothing about attacks outside 𝒜 (adaptive attackers leave the family); judge error propagates; θ itself is only bounded below.
- **What makes it different.** It turns "how many did we miss?" into an estimand with an identification analysis and a tested estimator, and it gives defenses a second axis.
- **Failure conditions.** See 10.12.

### 7.2 F2 — Secure or stopped?

- **Research question.** What share of each defense's ASR reduction is incapacitation, net of run-to-run noise?
- **Gap.** Marginal metrics (BU, UA, ASR) and SecFid's outcome classes do not give a per-case paired decomposition with a noise floor.
- **Contribution.** Paired decomposition; replicate-run noise model; availability-adjusted attacker success; reanalysis of published defenses.
- **Method.** Run each configuration three times on AgentDojo (and one second benchmark); estimate per-case state probabilities; decompose ΔASR into resistance and incapacitation with cluster-bootstrap CIs.
- **Baselines.** ASR, UA, BU; SecFid outcome classes; WASP partial/complete success.
- **Experiments.** 8–10 defenses × 2–3 models; replicate runs; DoS-goal attacks for availability.
- **Metrics.** Resistance and incapacitation shares; rank correlation between ASR ranking and resistance ranking.
- **Ablations.** Attack template; suite; model; replicate count.
- **Reproducibility.** AgentDojo logs plus new runs; same tooling as the pilot.
- **Limitations.** Utility checker validity; incapacitation is legitimate fail-closed behaviour in some deployments (the paper must say when).
- **What makes it different.** Per-case accounting with a noise floor, across defenses.
- **Failure conditions.** If replicate-run noise absorbs everything except the defense that aborts by design, publish as a section of F1, not a paper.

### 7.3 F5 — What should an action verifier see?

- **Research question.** Which information-access setting gives the best catch rate at fixed benign FPR under verifier-targeted injection, and how correlated are verifier and agent failures?
- **Gap.** Information access is studied for sabotage monitors, not for PI action verifiers; correlated failure is studied in theory, not measured under injection.
- **Contribution.** Controlled information-access experiment; correlation measurement; a design rule.
- **Method.** Replay AgentDojo trajectories offline; at each consequential call, query verifiers under three access settings; add adaptive injections aimed at the verifier.
- **Baselines.** AlignmentCheck-style auditor; MELON-style re-execution; plan-checking (CaMeL-like).
- **Metrics.** TPR at 1% benign FPR; ΔTPR under verifier-targeted injection; φ correlation between agent and verifier failure.
- **Reproducibility.** Public trajectories; prompts and verdicts released.
- **Limitations.** Offline replay ignores the agent's reaction to a block.
- **Failure condition.** If full-context verifiers dominate in every setting including verifier-targeted injection, the design question has a trivial answer.

---

## 8. Pilots

Both pilots used only public logs, ran on CPU in minutes, and followed `pilots/PILOT_PLAN.md`
(committed before the code). Full tables: `pilots/results/`.

### 8.1 Pilot A (F1): do a few attacks predict what the rest of the family breaks?

**Set-up.** Cases × attacks incidence matrices. Targets: AgentDojo GPT-4o, 10 integrity attacks
over 629 cases (pre-specified primary); JailbreakBench, 4–5 attacks × 100 behaviours for each of
four models. From every k-subset, predict the K-attack union. Leakage: none possible (no fitting
on the held-out attacks); the "truth" is the union of the attacks that exist, so this tests
within-family extrapolation only.

**Results** (mean absolute error, percentage points of cases; observed union / Chao2 / jackknife):

| Target | union over K | best single | k = 2 | k = 3 |
|---|---:|---:|---|---|
| AgentDojo, 10 attacks (primary) | 59.6% | 47.7% | 19.0 / 20.8 / **11.6** | 12.4 / 9.5 / **6.3** |
| AgentDojo, 5 distinct families | 53.1% | 47.7% | 20.8 / 28.2 / 20.1 | **11.4** / 13.0 / 12.6 |
| JBB Llama-2-7B | 96% | 94% | 30.6 / 30.4 / 30.7 | 11.7 / 11.7 / 12.5 |
| JBB Vicuna-13B | 96% | 95% | 2.4 / **2.1** / 2.7 | 1.0 / **0.8** / 0.9 |
| JBB GPT-3.5 | 95% | 93% | 14.8 / **4.0** / 8.4 | 3.8 / 3.7 / 4.4 |
| JBB GPT-4 | 86% | 78% | 33.3 / **27.4** / 33.2 | **14.5** / 20.2 / 19.3 |
| Synthetic, exchangeable (20 reps) | 43.6% | 24.1% | 18.0 / 8.1 / 9.5 | 12.8 / 5.1 / **3.2** |

**Verdict against the pre-specified criterion: not supported.** The criterion required both
estimators to beat the observed union at k = 2 and 3 in at least two of three families. Strictly
read, every family fails (Chao2 loses on AgentDojo at k = 2; the jackknife loses on Llama-2; both
lose on GPT-4 at k = 3). Read leniently (the better estimator wins), only AgentDojo clearly passes;
Llama-2's margins are 0.2 and 0.04 points.

What the failures have in common: JailbreakBench's "attacks" are different algorithms of very
unequal strength (DSN breaks 94 behaviours on Llama-2 while JBC breaks none). Richness estimators
assume occasions are exchangeable; a menu of unequal algorithms violates that, and a subset that
omits the strongest algorithm carries no information about it. The estimators did remove most of the
downward bias everywhere (AgentDojo k = 3: observed union −12.4, Chao2 −0.2, jackknife 0.0), but
the variance at small k cost more than the bias saved on JailbreakBench.

**Exploratory, post hoc (not pre-specified).** On the six near-exchangeable name-variants of
AgentDojo's `important_instructions` template (union 57.4%, canonical single template 47.7%), error
fell from 9.6 to 3.3 points at k = 2 and from 5.5 to 1.2 at k = 3 (jackknife). This supports the
narrowed claim and is the reason it survives, but it was chosen after seeing the main result and
cannot confirm it. A descriptive by-product worth keeping: renaming people in one shipped template
exposes 9.7 points more breached cases than the canonical template's headline ASR.

**Decision.** Narrow, do not abandon. The claim becomes: *relative to a declared attack
distribution sampled exchangeably*, k draws license a lower bound and a short-range extrapolation.
This must be tested prospectively on new data (10.12).

### 8.2 Pilot B (F2): does the defense stop the attack or stop the agent?

**Set-up.** Same cases with and without each defense; four states per run; among cases breached
without the defense, the share moved to clean (resist) or stopped (incapacitate). Noise floor: two
attack variants differing only in names, no defense.

| Model | Defense | ASR 0→1 | Resist | Incapacitate | Collateral clean→stopped |
|---|---|---|---|---|---:|
| GPT-4o | sandwich (`repeat_user_prompt`) | 0.477→0.278 | 0.37 [0.30, 0.45] | 0.10 [0.06, 0.15] | 0.10 |
| GPT-4o | spotlighting | 0.477→0.417 | 0.13 [0.09, 0.17] | 0.07 [0.04, 0.10] | 0.11 |
| GPT-4o | tool filter | 0.477→0.068 | 0.48 [0.39, 0.59] | 0.42 [0.31, 0.52] | 0.22 |
| GPT-4o | PI detector | 0.477→0.079 | 0.19 [0.11, 0.28] | **0.65 [0.54, 0.75]** | **0.74** |
| Llama-3.3-70B | sandwich | 0.103→0.058 | 0.30 [0.20, 0.41] | 0.29 [0.20, 0.38] | 0.21 |
| Llama-3.3-70B | → Meta-SecAlign-70B | 0.129→0.017 | 0.66 [0.51, 0.82] | 0.22 [0.13, 0.32] | 0.09 |

Noise floor: among 293 cases breached under neither name-variant, 16.0% flip between clean and
stopped; 18.6% of clean cases become stopped. (Upper bound on pure noise, since the attack text
differs.) 95% intervals are cluster bootstraps over user tasks.

**Verdict: supported, with a caveat about blindness.** Incapacitation exceeds the noise floor for
the PI detector and the tool filter, and the ranking changes: by ASR the PI detector is second-best,
by resistance it is third, behind the sandwich defense, with non-overlapping intervals (0.19 vs.
0.37). The GPT-4o cross-tab had been seen during screening, so this pilot was not blind. The large
noise floor is itself a finding: single-run benchmarks cannot resolve incapacitation effects smaller
than about 0.2, which covers at least three of the six comparisons shown (sandwich and spotlighting
on GPT-4o, and the SecAlign swap), with the Llama-3.3 sandwich borderline. Meta-SecAlign with the
sandwich defense is omitted from the table: with 48 baseline breaches its intervals span [0, 1].

---

## 9. Admissions relevance

What F1, completed, would show a committee and a prospective advisor:

- **Problem formulation.** A new estimand for a question the field asks informally ("did we test enough?").
- **Mathematical depth.** Identification arguments and estimator theory drawn from ecology and
  survival analysis, adapted to stochastic, judged, templated attacks.
- **Experimental discipline.** A pre-specified pilot that falsified the broad claim, reported as
  such, and a narrowed claim tested prospectively. This is the strongest single signal of research
  maturity you can give, and your record already shows the habit (P11's unsupported hypothesis,
  P06b's corrections).
- **Literature command.** Positioned against fuzzing statistics, scaling-law work and the 2026
  agent-security evaluation papers.
- **Ownership.** Sole-author method and code, released.
- **Fit.** AI security groups that build and break agent defenses (the AgentDojo and
  adaptive-attack lines) and software-security groups that study testing statistics (the STADS line)
  meet in this paper. Name specific faculty only after reading their recent work.

Coherence: P9 → P06b → P14 → P11 measured where evaluations mislead; F1 is the first paper that
says how much an evaluation can *certify*. That is a natural next step, not a forced one.

**What can honestly be claimed before December 2026.** A preprint with the estimand, the
identification results, the retrospective pilots (including the failed pre-specified test), and a
prospective test on at least one open model. Not a defended conference paper. Describe it as
"preprint" or "in preparation", never "under review", until it is.

---

## 10. Recommendation

### 10.1 Working title
*Rarer or Fewer? Estimating the Residual Attack Surface of LLM Agents from Finite Red-Teaming*

### 10.2 Central question
After k exchangeable draws from a declared attack distribution, what fraction of cases is vulnerable
to that distribution at all, and how many more draws would find how many more?

### 10.3 Most defensible novelty claim
"To our knowledge, the first application of incidence-based richness and cure-fraction estimation
to LLM red-teaming: an identification analysis of the vulnerable fraction under a declared attack
distribution, an extrapolation estimator validated on held-out draws, and a re-evaluation of
prompt-injection defenses that separates rarer from fewer vulnerabilities." Keep "to our knowledge"
and cite Maple et al., DAPRO, Risk Under Pressure, BoN, Schaeffer et al., Jones et al. and STADS in
the same paragraph.

### 10.4 Closest prior work and the exact distinction
Maple et al. (2605.09070) report the observed union across tested variants; F1 estimates the
unobserved part with uncertainty. DAPRO (2605.06605) bounds iterations-to-jailbreak per prompt; F1
estimates the population's vulnerable fraction and its extrapolation curve. STADS and FSE'21 do this
for fuzzers; F1 handles stochastic responses, judge error and templated families.

### 10.5 Technical contribution
Estimand and rarer/fewer decomposition; identification results; estimator with validated
extrapolation and a stopping rule; exchangeability design rule; empirical re-evaluation of defenses.

### 10.6 Feasibility result
Pre-specified pilot: broad claim not supported (Section 8.1). Post hoc: 1.7–4.4× error reduction on
exchangeable template variants (k = 2–5). Synthetic: 2.5–6.6× at k = 3–6. Narrowed claim untested
prospectively.

### 10.7 Validation strategy
(1) Synthetic families with known θ, including adversarial ones. (2) Prospective, pre-registered:
new exchangeable draws, predict held-out U(m). (3) Lower-bound validity on per-case replicated data.
(4) Judge-error audit on 200 outputs. (5) Defense re-evaluation with cluster-bootstrap CIs. (6) A
negative control: an attack family known to be strong only on a subset, to show the method reports
heterogeneity instead of hiding it.

### 10.8 Weaknesses and risks
- Undiscovered overlap: read Maple et al., DAPRO and Risk Under Pressure in full before writing.
- Exchangeable draws may still be too correlated in real templates for useful extrapolation.
- Judge error inflates or deflates incidence; needs the audit.
- Reviewers may say "this does not cover adaptive attackers". It does not, and the paper must say so
  in the abstract.
- Statistical novelty may be judged modest by ML-theory reviewers; the identification results are
  what lift it.

### 10.9 Resources
- Public: AgentDojo logs, JailbreakBench artifacts, HarmBench behaviours.
- New draws: 2–3 open 7–8B models locally (your laptop GPU, if it has ≥8 GB VRAM, with 4-bit
  quantisation) or a cheap API model. Rough scale: 100 behaviours × 100 draws × 3 models = 30k
  generations plus 30k judge calls; AgentDojo resampling is costlier (multi-step episodes), so start
  with one suite. Estimate cost from a 50-episode dry run before committing; do not extrapolate
  this report's numbers.
- No restricted data, no external commitments.

### 10.10 Manuscript structure
1. Introduction: absence of findings as evidence. 2. Setting and estimand (rarer vs. fewer).
3. Identification. 4. Estimators, extrapolation, stopping rule. 5. Synthetic validation.
6. Retrospective evidence, including the failed pre-specified test. 7. Prospective validation.
8. Re-evaluating defenses. 9. Limits: adaptive attackers, judges, correlated templates. 10. Related work.

### 10.11 Venues and the bar for each
- **USENIX Security / IEEE S&P / CCS 2027** (verify cycles): needs the prospective validation on two
  or more targets plus a defense re-evaluation that changes a conclusion someone has published.
- **SaTML 2027** (verify deadline): natural home; needs the method and one convincing application.
- **ICML 2027 / NeurIPS 2027 Evaluations & Datasets track:** needs the identification results stated
  as theorems with proofs, plus the experiments.
- **TMLR:** rolling, rigour-focused; a realistic first target if the theory is modest.
- **ICLR 2027 or SaTML workshops:** fine for an early version; label it a workshop paper on the CV.

No acceptance is predictable. Competitiveness at the top security venues depends on whether the
defense re-evaluation overturns a published claim.

### 10.12 Execution plan (correctness before speed)
1. **Week 1.** Read the three closest papers in full. If any already estimates the unobserved
   union, stop and re-scope to the rarer/fewer analysis only.
2. **Week 1–2.** Write the identification results and proofs; build the synthetic suite, including
   cases designed to break each estimator.
3. **Week 2.** Pre-register the prospective test in the repository before generating data:
   *failure* = on fresh exchangeable-draw data, estimators from k ≤ 5 draws do not beat the observed
   union on MAE for the 10k-draw union on at least two of three targets, **or** the lower bound is
   violated for more than 10% of bootstrap replicates. On failure, drop the estimator claim and keep a
   descriptive rarer/fewer measurement with large-m sampling.
4. **Weeks 3–4.** Generate draws (dry run first for cost); judge audit.
5. **Weeks 4–5.** Defense re-evaluation (fold in F2's decomposition as one section).
6. **Weeks 6–7.** Write; adversarial self-review; release code and incidence matrices; arXiv.

Separately and independently of F1: P11's arXiv bundle is ready (`paper/ARXIV_SUBMISSION.md`).
Posting it is a decision for you; it is not part of this recommendation.

### 10.13 Backup
F2, *Secure or Stopped?*, if F1's prospective test fails or the closest-paper reading reveals an
existing estimator. It needs replicate runs (three per configuration) to get below the 16–19% noise
floor the pilot found. F5 is the better long-term direction if you gain access to a GPU budget,
because its question is architectural rather than evaluative.

---

## 11. The direct answer

If I had your background and could choose freely, I would pursue **F1**. Three pieces of evidence
decide it. First, the literature: across nine directions the critique genre you have worked in is
saturated, and F1 is the only finalist whose core is a method with an identification analysis,
while its closest neighbours (observed union coverage, time-to-jailbreak bounds, compute curves)
measure something adjacent rather than the vulnerable fraction itself. Second, the pilot: it did not
flatter the idea. The broad version failed its pre-specified test, and the failure located the exact
condition (exchangeable draws) under which the method works, which the post hoc and synthetic results
then matched. A direction that survives a falsification attempt by becoming more precise is a better
bet than one that has not been tested. Third, fit: it is AI security, it uses the statistical
strengths your record already shows, and it answers the question the quiet-monitor project was
circling (what does silence license?) in a form you can validate on public data this term.

The quiet-monitor project, as far as it can be judged without the manuscript, is not the strongest
next paper. Pause it unless it passes the three-question test in Section 5.

---

## Sources

Search-verified titles and abstracts (full texts not read in this session):

- AgentDojo, Debenedetti et al., arXiv 2406.13352; run logs at github.com/ethz-spylab/agentdojo (read, commit 089ed46)
- JailbreakBench artifacts, github.com/JailbreakBench/artifacts (read, commit 909e68c)
- Maple, Kumar, Tapwal, *Single-Configuration Attack Success Rate Is Not Enough*, arXiv 2605.09070
- *How Many Iterations to Jailbreak? Dynamic Budget Allocation for Multi-Turn LLM Evaluation* (DAPRO), arXiv 2605.06605, NeurIPS 2026
- Ehghaghi et al., *Risk Under Pressure*, arXiv 2606.11409
- Hughes et al., *Best-of-N Jailbreaking*, arXiv 2412.03556
- Schaeffer et al., *How Do Large Language Monkeys Get Their Power (Laws)?*, arXiv 2502.17578
- Jones et al., *Forecasting Rare Language Model Behaviors*, arXiv 2502.16797
- Nasr et al., *The Attacker Moves Second*, arXiv 2510.09023, USENIX Security 2026
- Böhme, *STADS: Software Testing as Species Discovery*, arXiv 1803.02130 (TOSEM 2018); Böhme, Liyanage, Wüstholz, *Estimating Residual Risk in Greybox Fuzzing*, ESEC/FSE 2021
- Briand et al., capture–recapture models for software inspections (IEEE TSE 2000), via search summary
- Pathade et al., *Attack Success Rate Is Not a Number*, arXiv 2609.25173
- Hermon et al., *Security–Fidelity Tradeoffs* (SecFid), arXiv 2606.30783, ICML 2026
- Evtimov et al., *WASP*, arXiv 2504.18575, NeurIPS 2025 D&B
- Bhatt et al., *The Defense Trilemma*, arXiv 2604.06436
- Abdelnabi & Bagdasarian, *AI Agents May Always Fall for Prompt Injections*, arXiv 2605.17634
- *From Shield to Target: Denial-of-Service Attacks on LLM-Based Agent Guardrails*, arXiv 2606.14517
- PIDS-Bench, arXiv 2609.15017; *Passing the Test You Trained On*, arXiv 2610.03448; IndicGuard, arXiv 2606.22841
- Arike et al., arXiv 2601.21112; Kale et al., arXiv 2508.19461 (code read: github.com/scaleapi/mrt); Terekhov et al., arXiv 2510.09462; SHADE-Arena, arXiv 2506.15740; SLEIGHT-Bench, arXiv 2605.16626
- Shiromani & Richter, *A False Average*, arXiv 2608.00583; *Recall Is Not Protection*, arXiv 2609.05797
- Schwinn et al., *A Coin Flip for Safety*, arXiv 2603.06594, ICML 2026; *Concerns in Benchmarking Jailbreaks*, arXiv 2610.26595
- Rosenfeld & Garg, Dis², NeurIPS 2023; ODD, arXiv 2506.14978; Amoukou et al., NeurIPS 2024; arXiv 2602.02229
- Bukkapatnam & Karuturi, *When Can We Conclude a Dangerous Capability is Absent?*, ICML 2026
- *Coverage, Not Averages*, arXiv 2604.20763; *Auditable Agents*, arXiv 2604.05485; AgentLAB, arXiv 2602.16901
- LlamaFirewall, arXiv 2505.03574; *Breaking and Fixing Defenses Against Control-Flow Hijacking*, arXiv 2510.17276
- NeurIPS 2026 accepted list, mirrored at github.com/YuanDaoze/NIPS26- (read)
- Method references (standard, not re-verified): Chao (1987) *Biometrics*; Chao et al. (2014) *Ecological Monographs*; Burnham & Overton (1978) *Biometrika*; Orlitsky, Suresh & Wu (2016) *PNAS*; Maller & Zhou (1996) *Survival Analysis with Long-Term Survivors*
