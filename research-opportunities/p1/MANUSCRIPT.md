# Hiding in the Shift: Label-Free Monitors Do Not See a Cross-Testbed DoS Detector That Is Already High-Confidence Wrong

**Rajveer Singh Pall** (sole author)

> Working manuscript, 2026-10-22. Full frozen specification (5 seeds, 200k/class source cap, 50k
> target benign, 2,000 target attack flows/family, 200-query score-only budget), NetFlow v2
> quartet. Every headline number is keyed to `results/p1/summary_p1.json` /
> `matrix_latent.json` and verified by `check_numbers_p1.py`. Scope is deliberately bounded:
> one feature family (NetFlow v2), feature-space attacks, no wire-realization claim. Language is
> sized to that evidence — "suggests", not "proves".

## Abstract

Flow-based DoS detectors score ~99% in-domain and collapse across independently captured networks;
operators are told to catch this with label-free monitors (Average Thresholded Confidence,
confidence drift, distribution distances) that need no target labels. Across the full NetFlow v2
quartet — 12 ordered source→target pairs, four detector families, five seeds, 240 configurations —
we measure what those monitors actually see. The dominant finding is not an attack: **before any
adversary acts, the cross-testbed detector already classifies a mean of 67.9% of real target DoS
flows (range 0–100%) as benign at high confidence**, the exact operating point the monitors
protect, and the model-based monitors stay silent on a large, systematic subset — **36 of 240
configurations, spanning nine distinct source→target→model combinations, pair high latent exposure
(>0.5) with both confidence monitors silent.** The blindness is model-dependent and aligns with
exposure: LogisticRegression is both the most exposed (mean latent 0.800) and the most frequently
silent (33%), while RandomForest is the least exposed (0.524) and never silent. A constrained,
score-only, traffic-plausible adversary adds capability only where the detector still has headroom
— its own contribution (searched minus projected high-confidence-miss rate) ranges from +0.607 to
+0.001 across cells and is ≈0 where the detector is already saturated; its power is not evasion
(nearly free) but confidence, moving flows across the auto-accept threshold. The obvious
responder-side defence — watch the features the adversary cannot freely set — fails a
pre-registered bar everywhere (ΔHCMR ≤ 0.072 against a 0.10 bar), because those features do not
transfer across independent testbeds either. The practical danger is therefore not a clever
adversary but a detector that is a thin margin from waving everything through and a label-free
safety net calibrated on the wrong network. Scope: feature-space, one feature family, the tested
pairs; "suggests", not "proves".

## 1. Introduction

Machine-learning network intrusion detectors report near-perfect in-domain scores and then
collapse when they are moved to an independently captured network. The prior study this work
builds on (P11, same repository) measured this for flow-based DoS/DDoS detection across the
NetFlow v2 quartet: in-domain macro-F1 ≈ 0.98, external ROC-AUC that falls below chance on
roughly half of the ordered dataset pairs, and a failure that is representational — the model
ranks attacks *below* benign traffic — rather than a merely stale threshold, for most pairs.

Because an operator cannot label traffic on the new network, the field's recommended safeguard is
**label-free monitoring**: estimate the deployed model's accuracy, or detect that the input
distribution has shifted, using only unlabeled target traffic. Average Thresholded Confidence
(ATC; Garg et al., ICLR 2022), confidence-drift signals, and distribution distances (A-distance,
MMD, per-feature Wasserstein) are the standard instruments. Bikdeli et al. (*The Dashboard Says
"Perfect"*, Frontiers in AI 2026) recently showed that this whole toolbox fails under a **benign**
one-year temporal drift between CIC-IDS2017 and CSE-CIC-IDS2018: no label-free selector or
test-time-adaptation variant beats the unadapted source model in both transfer directions.

This paper asks the adversarial and cross-testbed version of that question, and answers it
honestly — the answer is not the one the title of an attack paper would promise. We find that:

1. **The detector is already defeated at the monitored operating point.** Before any adversary
   acts, across the NetFlow v2 quartet the cross-testbed detector classifies a large and
   model-dependent fraction of *real* target DoS flows as benign **at high confidence** — the exact
   regime a confidence monitor is meant to protect. This latent exposure, not any attack, is the
   dominant phenomenon.
2. **The label-free monitors are model-dependently blind, and blindest where the detector is
   worst.** The model-based monitors (ATC, confidence drift) track the *natural* distribution
   shift, not the presence of high-confidence misses. For some detectors they fire (and would fire
   on benign drift anyway); for others — notably a low-capacity LogisticRegression on a
   strong-ranking transfer — they stay silent while essentially every target attack is a
   high-confidence miss.
3. **A constrained adversary widens the hole only where there is headroom.** An adversary limited
   to traffic-plausible, score-only feature changes raises the high-confidence-miss rate toward a
   feasibility ceiling where the detector still has headroom, and contributes essentially nothing
   where the detector is already saturated. Its power is not evasion (nearly free) but confidence:
   moving flows from the monitor's review region across the auto-accept threshold.
4. **The obvious responder-side defence does not transfer.** Watching the features the adversary
   cannot freely set does not close the gap at an acceptable false-alarm cost, because those
   features do not transfer across independent testbeds either.

The contribution is a measurement, under a pre-registered threat model and an apples-to-apples
baseline, of the **joint** object that the literature has only touched in pieces: adversarial and
latent high-confidence false negatives against the detector-plus-label-free-monitor system, under
cross-testbed shift, with a stated traffic-plausibility constraint model and a monitor-side defence
evaluated for both security gain and false-alarm cost.

## 2. Related work

We position against seven works (verified 2026-10-22; full URLs in the references). The novelty
gate was committed before any attack code (`PREREGISTRATION.md`).

- **Bikdeli et al., "The Dashboard Says 'Perfect'" (Frontiers in AI 2026)** — the closest work.
  It audits label-free monitors + test-time adaptation under a *benign* one-year temporal drift
  (CIC-IDS2017↔2018) and finds none beats the unadapted source in both directions. We add the
  *adversary* and the *independent-testbed* quartet, and we separate latent exposure from
  adversarial lift. Our delta: Bikdeli shows the monitors miss benign drift; we show they miss a
  detector that is already high-confidence wrong, and that an adversary can widen it under
  constraints.
- **Gnanaratna et al. (Kingston), SecureComm 2026** — hardens an uncertainty-aware deferral IDS
  against a *training-time* proxy adversary. There the monitor is the artefact being improved; here
  it is the artefact being probed, and we measure how many high-confidence misses survive it.
- **PANTS (Jin & Apostolaki, USENIX Security 2025)** — white-box realizable packet-level
  adversarial samples + adversarial training for traffic classifiers. Classifier-only; no
  confidence-monitor system and no cross-testbed-transfer framing. We borrow its constraint
  discipline, not its goal.
- **PAVE (protocol-validity-aware robustness evaluation, IoT NIDS, 2026)** — shows standard
  feature-space attacks are 0–3% valid on the wire. This is the principal threat to any
  feature-space claim; our constraint model (Merzouk's four criteria, §3) and our explicit refusal
  to claim wire-realizability are the direct answer.
- **Apruzzese et al. (DTRAP 2022)** and **Merzouk et al. (Annals of Telecommunications 2022)** —
  the realistic attacker-capability model and the four feature-validity criteria (value ranges,
  binary values, multiple-category membership, semantic relations) we adopt verbatim as our
  constraint specification.
- **elShehaby & Matrawy, SoK on evasion practicality (arXiv 2306.05494, v4 2025)** — argues many
  published NIDS evasions do not survive functionality/practicality checks, and dynamic detectors
  resist. Our honesty anchor: we report functional validity, and our headline is consistent with
  it — the practical danger is the detector's latent exposure, not a powerful evasion.
- **Garg et al., ATC (ICLR 2022)** — the monitor we probe. Its own theory notes that accuracy
  estimation under shift is as hard as finding the optimal predictor, hence rests on assumptions
  about the shift; our adversary and our cross-testbed setting break exactly those assumptions.

To our knowledge, no prior work measures adversarial high-confidence false negatives against the
joint detector-plus-label-free-monitor system under cross-testbed distribution shift and stated
traffic-plausibility constraints, together with a monitor-side defence evaluated for both security
gain and false-alarm cost.

## 3. Threat model and constraints

We instantiate Apruzzese's capability model and Merzouk's validity criteria; the full
specification is frozen in `PREREGISTRATION.md` §3.

**Goal.** Make a target-network DoS/DDoS flow be scored benign by the source-trained detector with
model confidence at or above an auto-acceptance threshold τ_accept, so a confidence/ATC monitor
does not escalate it.

**Knowledge.** Grey-box, **score-only** (the realistic default): the adversary knows the public
NetFlow v2 feature schema and can query the deployed model's score up to 200 times per flow, with
no gradients. A **strong** upper-bound search (larger budget + coordinate descent) stands in for a
white-box ablation; tree ensembles are non-differentiable, so we do not claim a gradient attack.

**Capability — three control classes** over the 39 shared NetFlow v2 features, derived from the
attack mechanism (not convenience) and frozen before any run:
- *Directly controllable* (16): source-side byte/packet counts, rates, durations, client TCP
  flags, packet-size features and bins.
- *Indirectly influenced* (13): responder-side bytes/packets, server flags, retransmissions, TCP
  windows — the attacker changes these only as a response, measured in §4.
- *Uncontrollable* (10): protocol identity, TTLs, DNS/ICMP/FTP fields — frozen at the original
  flow.

**Constraints (Merzouk's four criteria, made concrete).** (1) Box: each changed feature within the
empirical [p1, p99] range of real source attack flows of its family. (2) Immutability:
indirect and uncontrollable features frozen at the original flow. (3) Integer/flag: packet and
size-bin counts integral, flag bytes valid. (4) Dependency: mean packet length within [MIN,MAX],
bytes ≥ 20·packets, size-bin sum ≤ total packets, retransmissions ≤ totals. A projection operator
repairs any candidate into this set; a *functionality* test keeps the rate/volume features inside
the attack family's box so an evaded flow is still a working DoS.

**Success (high-confidence miss, HCM).** A flow is an HCM iff, after the source-fitted scaler and
threshold are applied on the target, it is predicted benign, its confidence max(p, 1−p) ≥ τ_accept
(set on source-validation benign at a 1% review budget), and it is feasible and functional. HCMR
is the fraction of target attack flows turned into an HCM within budget.

**Honest baseline.** Feasibility is an *attacker* constraint, not a validity test for real
wire-captured traffic. The latent HCM rate is therefore measured on the real target flows
**without** the source feasibility box; the adversarial lift is measured against the *projected*
real flow (same feasibility regime as the attack), never against the filtered natural rate. (An
earlier draft conflated the two; a correctness audit caught it and the comparison was fixed.)

## 4. Methods

All data loading, model fitting, and metrics reuse the P11 codebase (`src/`); P-1 code lives in
`research-opportunities/p1/` and never overwrites P11 artifacts. Leakage discipline is inherited:
scaler and median imputation are fit on source-train only, monitor and defence thresholds on
source-validation only, and target labels are used only to score. Data is loaded with a
memory-bounded streaming reader (pyarrow `iter_batches`, columns-only, two-pass per-class
Bernoulli downsample) so the 17–30M-row parquets never materialize; the ML logic is unchanged.

**Detectors.** Four families from the P11 pipeline — LightGBM, XGBoost, RandomForest,
LogisticRegression — each trained on a source domain (200k/class cap) and applied to the target
with a MinMax scaler, balanced sample weights, and a plateau-robust threshold.

**Controllability (Phase 1).** For each indirectly-influenced feature we fit a 5-fold
cross-validated predictor from the directly-controllable features on real flows and report R². A
low R² means the attacker cannot freely set that feature — the only features the Phase-4 defence
is permitted to watch, chosen on evidence rather than assumption.

**Attack (Phase 3).** A constrained search over the directly-controllable features minimises the
detector's P(attack) subject to feasibility; because a low P(attack) simultaneously flips the
label and raises the benign confidence, one objective serves both halves of the HCM definition.
The search is batched (one model query scores all flows' current candidate), so the 200-query
budget is per flow. Indirect and uncontrollable features are frozen at the original flow — the
conservative attacker that cannot set the responder's behaviour, which is what gives a
responder-side monitor something to detect.

**Monitor battery (Phase 2).** Five label-free monitors from `src/divergence.py` — ATC estimated
accuracy, mean-confidence drop, KS on the score distribution, proxy A-distance, per-feature max
Wasserstein — each thresholded on a source-validation two-half null at the 1% false-alarm budget.
The identical battery is evaluated with no attack (baseline), during the attack, and across the
full transfer matrix.

**Defence (Phase 4).** An IsolationForest novelty score on the low-controllability features,
fitted on one half of source-validation benign and thresholded on the other half at the 1% budget.
A flagged flow is escalated and no longer counts as a successful miss. We report the drop in HCMR
and the added benign-review cost, and gate the defence on a pre-registered bar (ΔHCMR ≥ 0.10 at
added cost ≤ 0.02).

**Statistics.** HCMR and its components carry paired-bootstrap 95% CIs over flows (N ≥ 2000);
seed variance is reported separately across five seeds.

## 5. Results

Numbers are keyed to `results/p1/summary_p1.json` (`matrix`, `per_pair_model`) and
`matrix_latent.json`; `check_numbers_p1.py` verifies them against this text.

### 5.1 Latent high-confidence exposure is pervasive across the quartet

Across the full NetFlow v2 transfer matrix — 12 ordered pairs × 4 models × 5 seeds, 240
configurations, every target carrying volumetric DoS flows — the **mean latent high-confidence-miss
rate is 0.679**, ranging from 0.0 to 1.0. Before any adversary, a cross-testbed DoS detector on
average already assigns benign-at-high-confidence to two thirds of real target attack flows. This
is not confined to the pairs where ranking inverts: on the strong-ranking BoT-IoT→CSE-CIC pair
(external AUC 0.89–0.93) the latent rate still reaches 0.999 for LogisticRegression, driven by
threshold-loss and overconfidence rather than ranking collapse. The exposure is strongly
model-dependent (per-model mean latent: LogisticRegression 0.800, LightGBM 0.707, XGBoost 0.685,
RandomForest 0.524). Figure 1 shows the decomposition on the two representative pairs.

### 5.2 The label-free monitors are model-dependently blind — and blindest where exposure is worst

The model-based monitors fire at a mean rate of 0.80 (ATC) and 0.80 (confidence drop) across the
matrix — but their alarm tracks the *natural* distribution shift, not the presence of
high-confidence misses. The dangerous regime is a monitor that stays silent while the detector is
wide open: **36 of 240 configurations have latent HCMR > 0.5 with both model-based monitors
silent, spanning nine distinct source→target→model combinations** (e.g. BoT-IoT→CSE-CIC/LogReg,
ToN-IoT→BoT-IoT/{LightGBM,LogReg,XGBoost}, ToN-IoT→CSE-CIC/LogReg, UNSW→ToN-IoT/LogReg). The
blindness aligns with exposure by model: LogisticRegression is silent at a rate of 0.33 (33% of
its configurations, and is the most exposed), whereas RandomForest is **never** silent (and is the
least exposed).
Figure 2 is the alarm heatmap on the representative pairs. For an operator this is the worst
possible pairing — the monitor is quietest exactly where the detector has already failed.

### 5.3 The adversary buys confidence, not evasion, and only where there is headroom

On the two representative pairs (UNSW-NB15, BoT-IoT → CSE-CIC-IDS2018) × 4 models we run the full
score-only search and decompose the high-confidence-miss rate into latent (real flows, no attacker
box), projected (project into the box, no search) and searched (full attack). The search's own
contribution (searched − projected) is **+0.607 (BoT/LightGBM), +0.551 (BoT/XGBoost), +0.251
(UNSW/LogReg), +0.232 (UNSW/LightGBM), +0.242 (UNSW/XGBoost), +0.226 (UNSW/RandomForest), +0.195
(BoT/RandomForest), and +0.001 (BoT/LogReg)**: the adversary widens the hole where the detector has
headroom and adds essentially nothing where it is already saturated (BoT/LogReg, latent 0.999).
One model resists outright: on BoT-IoT→CSE-CIC, **RandomForest holds the searched HCMR to 0.219**
(latent 0.144) — its coarse, less-overconfident probabilities keep most feasible flows below the
auto-accept threshold. The per-flow P(attack) drop is small throughout (mean 0.003–0.048) and the
strong upper-bound search adds ≤ 0.01 over the score-only search; the flows sit a thin margin from
the confidence threshold, so where the search helps, a feasible nudge suffices. Consistent with
this, the query budget matters only where the detector has headroom: on BoT-IoT→CSE-CIC, HCMR for
LightGBM rises from 0.685 at 50 queries to 0.889 at 200, and for XGBoost from 0.697 to 0.851, while
it is flat for LogisticRegression (≈0.902, already saturated) and stays low for RandomForest
(0.136→0.219) regardless of budget (Figure 3). Where the detector is saturated or the model
resists, more queries do nothing; where there is headroom, they help, but the per-flow P(attack)
drop remains small because the flows begin near the threshold. Figure 4 shows the mechanism — the
search shifts the benign-confidence distribution across τ_accept.

### 5.4 The obvious responder-side defence does not transfer

A novelty monitor on the low-controllability features (the only ones the attacker cannot freely
set; Phase 1 found just 1–3 per source) **fails the pre-registered bar everywhere**: it cuts HCMR
by 0.072 (UNSW pairs) and 0.012 (BoT-IoT pairs) against a 0.10 bar, catching ≤ 8% of misses at
≤ 1.0% added benign-review cost. The reason is P11's reason: across independently built testbeds
the low-controllability features do not transfer either, so a source-fitted novelty detector on
them cannot separate an adversarial target flow from benign target traffic. We report this negative
as a result, not a footnote.

### Figures

![Figure 1](fig1_hcmr_decomposition.png)
**Figure 1.** Latent / projected / searched high-confidence-miss rate for the two representative
pairs × four models. Latent exposure (blue) dominates; the search (orange) adds only where the
detector has headroom, and RandomForest on BoT-IoT resists outright.

![Figure 2](fig2_monitor_alarm_heatmap.png)
**Figure 2.** ATC / confidence-drop alarm rate (1 = fires). The monitors are silent (green) only on
BoT-IoT→CSE-CIC / LogisticRegression — the cell where the detector is already fully exposed.

![Figure 3](fig3_hcmr_vs_budget.png)
**Figure 3.** HCMR vs score-only query budget. More queries help only where the detector has
headroom (BoT-IoT/LightGBM, XGBoost); flat where saturated (BoT-IoT/LogReg) or where the model
resists (BoT-IoT/RandomForest).

![Figure 4](fig4_confidence_margin.png)
**Figure 4.** Mechanism (BoT-IoT→CSE-CIC / XGBoost, τ_accept = 0.968). Natural flows (blue) sit
just below the auto-accept threshold; the search shifts them (orange) across it — the adversary
buys confidence, not evasion.

## 6. Discussion

The uncomfortable alignment in §5.2 is the paper's core message for practice. Label-free
confidence monitors do not fail randomly across detectors; they fail *systematically* on the
detectors that are already most exposed. A low-capacity, well-calibrated-looking model
(LogisticRegression) that transfers "well" by AUC can still assign benign-at-high-confidence to
almost every target attack, and precisely because its confidence distribution shifts little between
source and target, ATC and confidence-drift report normal. A monitor that measures how much the
model's own confidence moved cannot, in principle, see a failure that does not move it. This is the
adversarial, cross-testbed sharpening of Bikdeli et al.: not only does the toolbox miss benign
drift, it misses a detector that is confidently wrong, and an adversary can deliberately keep flows
inside the region it trusts.

RandomForest's resistance is informative rather than a fix. Its probabilities are coarse (fractions
of trees), so fewer feasible flows clear a high τ_accept, and its latent exposure is lowest. But it
is never the operator's only model, its in-domain scores are indistinguishable from the others, and
nothing at deployment tells an operator which model they have drawn. The lesson is not "use
RandomForest" but "a label-free confidence monitor is not a safety net you can rely on across
networks, and the obvious responder-side patch does not survive the move." This is consistent with
the evasion-practicality SoK: the practical danger here is not a powerful evasion but a detector a
thin margin from waving everything through. Ten labelled target flows (P11, F7) remain worth more
than any zero-label monitor in this setting.

## 7. Limitations

One feature family (NetFlow v2) and the dataset pairs tested; both of the attacked sources carry a
single DoS family (volumetric), so the per-family box is one family's. The main study is
feature-space; no wire-realizability is claimed — the optional single-family wire check (Phase
1-R) was not run, so the realism argument rests on the constraint model and the controllability
analysis, not on re-extracted flows. The strong search is an upper bound, not a gradient attack.
External AUCs are at a fixed sampling cap and are not identical to P11's full-pipeline numbers; we
report them as internal context, not as P11's results. The findings are a measurement for the
tested system, not a general claim about all NIDS or all monitors.

## 8. Ethics and responsible disclosure

This is defensive security research under the standard adversarial-ML evaluation paradigm (Carlini
et al. 2019; Apruzzese et al. 2022; PANTS 2025). The author red-teams **his own** detector, trained
on public, offline, already-held datasets, to measure a blind spot in its label-free monitoring
and then test a monitor-side defence. No third-party or production system is probed; all traffic
manipulation is synthetic and confined to local feature-space datasets. No pcaps are produced and
no wire-realizable exploit is released. The attack code is kept in a private repository until the
paper is public.

## 9. Reproducibility

Every figure and table regenerates from a `results/p1/*.json` file; every headline number is pinned
to a key in `summary_p1.json` and checked by `check_numbers_p1.py`. Seeds are fixed (42–46);
configurations are at the top of each entry point. The pre-registration (threat model, frozen
choices, success definition, falsifiers) was committed before any attack code, with dated
amendments for the pilot-vs-full scale, the strong-search ablation, and the memory-bounded loader.

## References

<!-- Bikdeli (frai.2026.1928858); Gnanaratna et al. SecureComm 2026 (LNICST 705); Jin & Apostolaki
USENIX Sec 2025 (arXiv 2409.04691); PAVE (ScienceDirect S2667295226000450); Apruzzese et al. DTRAP
2022 (arXiv 2106.09380); Merzouk et al. Annals of Telecom 2022 (10.1007/s12243-022-00910-1);
elShehaby & Matrawy SoK (arXiv 2306.05494); Garg et al. ICLR 2022 (arXiv 2201.04234). Full entries
in PREREGISTRATION.md §2. -->
