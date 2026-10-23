# A Shift Alarm Is Not a Safety Certificate: Recall Certification for Cross-Testbed Intrusion Detectors

**Rajveer Singh Pall**

*Preprint, October 2026. Code and all result files: this repository. Every number in the paper is
produced by a script and checked against its source file by `check_numbers_p1.py`.*

---

## Abstract

A machine-learning intrusion detector can score almost perfectly on the network it was trained on
and then quietly stop catching attacks when it is moved to a different network. Because the new
network has no attack labels, operators are told to watch the model instead — with label-free
monitors such as Average Thresholded Confidence (ATC) and confidence-drift signals. Ahmed et al.
(2026) recently showed that these monitors can report perfect accuracy for a detector that catches
nothing, and explained why. We take the next step and ask a security question: can an attacker, who
is only allowed to make traffic-plausible changes, *deliberately* steer attacks into the blind spot
those monitors leave open?

Working across the four NetFlow v2 datasets (twelve source→target transfers, four model families,
five seeds, 240 configurations), we find that the problem is mostly already there before any
attacker acts: on average the transferred detector calls 68% of real attack flows benign *with high
confidence*. A constrained, query-only attacker widens this where the detector still has room to
fail — in 74 of the 145 configurations where it drives the high-confidence miss rate above one half,
both confidence monitors stay silent — and adds nothing where the detector is already saturated. The
effect depends strongly on the model: a logistic-regression detector is the most exposed and the
most often unseen, while a random forest largely resists the attack. The obvious fix — watch the
responder-side features the attacker cannot set — fails, because those features do not survive the
move between networks either. We also tested an approximate version of Ahmed et al.'s conformal
drift alarm on our matrix; in this adversarial cross-testbed setting it did not separate the
dangerous cases from the safe ones (it alarmed on 0.92 of safe and 0.84 of unsafe configurations).
The only thing that reliably told the dangerous cases apart was a small labelled audit — and we
measure, honestly, what that audit costs.

We claim no new theorem and no new monitor: the monitoring blindness and its formal statement are
Ahmed et al.'s, and the audit is textbook finite-sample statistics. What is ours is the adversarial,
cross-testbed measurement, the model dependence, the failed defence, and a careful account of what
evidence can and cannot certify that a transferred detector still works. Scope: feature-space
attacks (no wire-level claim), one feature family, the datasets tested.

---

## 1. Introduction

Suppose you train a flow-based denial-of-service detector on one organisation's network. It reaches
about 0.98 macro-F1 in testing. You deploy it on a different organisation's network. A companion
study in this repository (referred to as P11) measured what happens next across four public NetFlow
v2 datasets: the detector's area under the ROC curve on the new network falls below 0.5 — worse than
a coin flip — for roughly half of the dataset pairs, and the failure is usually in the *ranking*,
not a stale threshold.

You cannot simply re-measure accuracy on the new network, because you have no attack labels there.
The standard advice is to watch the model with *label-free* monitors: methods that estimate accuracy
or detect distribution shift using only unlabelled traffic. ATC (Garg et al., 2022) is the most
common; confidence-drift and distribution-distance measures are others. Ahmed et al. (2026), in a
paper titled *The dashboard says "perfect,"* audited this toolbox under a benign one-year drift
between two intrusion-detection datasets and found it wanting: ATC assigned a predicted accuracy of
1.000 to a detector whose recall on every attack family was zero, and they proved two propositions
explaining the failure.

Their shift was benign — the world changed on its own. Ours is adversarial. We ask whether an
attacker who can only make changes a real attack could make — within the rate, size, and protocol
limits of an actual denial-of-service flow — can push malicious traffic into exactly the region
where the detector is confidently wrong and the monitors stay quiet. The short answer is yes, but
the more useful answer is more careful, and most of this paper is about being careful. In
particular:

1. **The detector is usually already broken before the attacker shows up.** Across our 240
   configurations, the transferred detector labels an average of 68% of real attack flows benign at
   high confidence, with no attack at all. This latent exposure, not the attacker, is the main
   event.
2. **The confidence monitors miss it, and the reason is known.** They are functions of the model's
   score distribution, and that distribution barely moves when recall collapses at a low attack base
   rate. Ahmed et al. stated this formally; we restate it only to make the adversarial version clear.
3. **A constrained attacker widens the gap where there is room, and nowhere else.** Whether it can
   depends on the model.
4. **The obvious defence does not transfer, and neither does any label-free signal we tested.** What
   does separate the dangerous cases is a labelled audit, whose cost we measure honestly — it is
   cheap to *flag* a broken detector and expensive to *clear* a working one.

Our contribution is the measurement and its honesty, not a theorem or a tool.

## 2. Background and related work

**The closest work.** Ahmed et al. (2026, *The dashboard says "perfect"*; Frontiers in Artificial
Intelligence, DOI 10.3389/frai.2026.1928858) audit label-free monitoring and test-time adaptation
under a benign temporal shift (CIC-IDS2017 ↔ CSE-CIC-IDS2018). They show ATC reporting accuracy
1.000 for a zero-recall detector, formalise the inversion in two propositions, and report that a
conformal abstention rate is the one label-free statistic that behaves reliably as a drift alarm in
their setting. We build directly on this. The blindness result and its proof are theirs; our
additions are an *adversary*, the move between *independently built* testbeds rather than one dataset
across time, a stated constraint model, the model dependence, and a defence and audit-cost analysis.

**Realizable attacks on traffic classifiers.** PANTS (Jin and Apostolaki, USENIX Security 2025)
generates packet-level adversarial traffic with an SMT solver and hardens classifiers with
adversarial training. PLAA (You et al., 2026) produces packet-level realizable evasions and reports
a 92.78% evasion rate. Both are classifier-only, with no confidence monitor and no cross-testbed
framing, and both own the wire-level realism we deliberately do not claim. PAVE (2026) shows that
standard feature-space attacks are 0–3% valid on the wire; this is why we keep our scope explicitly
in feature space.

**Constraint models.** Apruzzese et al. (DTRAP 2022) give a realistic attacker-capability model, and
Merzouk et al. (Annals of Telecommunications 2022) give four validity criteria for a network feature
vector — value ranges, binary values, category membership, and semantic relations. We adopt these
directly as our feasible set.

**Risk monitoring with a few labels.** Our audit uses, rather than invents, finite-sample risk
monitoring. Podkopaev and Ramdas (2022) track a deployed model's risk from a labelled stream;
Prediction-Powered Risk Monitoring (Zhang et al., ICML 2026) corrects unlabelled predictions with a
small labelled set under an anytime-valid bound; RiskGate-IDS (2026) calibrates a NetFlow detector
to a new network with a small labelled budget. We cite these as the machinery a defender would
actually use and show, in Section 5.6, why the cheaper label-free options do not close the gap here.

**What is and is not new.** Not new: the monitoring blindness (Ahmed et al.), the audit machinery
(the risk-monitoring line above), conformal abstention (Ahmed et al.). New here: the adversarial,
cross-testbed, constraint-modelled measurement; the model dependence; the failed responder-side
defence; and the honest accounting of certification cost.

## 3. Setup

We reuse the P11 codebase for loading, model fitting, and metrics, so the pipeline is identical to
the cross-network study it builds on. Data loading streams the 17–30 million-row parquet files in
column-wise batches so the machine never has to hold a whole dataset in memory; the model logic is
unchanged. Leakage discipline is inherited: scalers and thresholds are fit on source-train data
only, monitor thresholds on source-validation only, and target labels are used solely to score.

**Datasets and detectors.** The four NetFlow v2 datasets (UNSW-NB15, BoT-IoT, ToN-IoT,
CSE-CIC-IDS2018) share 39 features. Detectors are LightGBM, XGBoost, RandomForest, and
LogisticRegression, each trained on a source dataset (200,000 flows per class) and applied to a
target, with a MinMax scaler, balanced sample weights, and a threshold chosen on the source test
split. We use five seeds (42–46).

**Three questions that are usually conflated.** It helps to keep three things apart:

- *Ranking* — can the detector put attacks above benign traffic? (ROC-AUC)
- *Operating-point safety* — does it actually catch attacks at the threshold it will deploy with?
  (recall, or equivalently the high-confidence miss rate)
- *Monitoring* — do the label-free signals tell you when the operating point has gone unsafe?

The paper's spine is that these come apart. A detector can rank attacks reasonably (AUC 0.919) and
still catch almost none of them at its deployed threshold (recall near zero), and the confidence
monitors track neither — they track how much the score distribution moved.

## 4. Threat model and constraints

The attacker wants a denial-of-service flow on the target network to be scored benign by the
source-trained detector, at a confidence high enough that a confidence monitor will not escalate it.

**What the attacker knows and can do.** The realistic setting is grey-box and query-only: the
attacker knows the public NetFlow v2 feature schema and can ask the deployed model for a score, up to
200 times per flow, with no gradients. As a worst-case comparison we also run a stronger search
(larger budget plus a coordinate sweep); because tree ensembles have no gradient, this stands in for
a white-box attacker and is labelled as an upper bound, never as a gradient attack.

**What the attacker may change.** We split the 39 features by mechanism into three classes, fixed
before any experiment. *Directly controllable* (16): the source-side byte and packet counts, rates,
durations, client TCP flags, and packet-size features the attacker sets by choosing how to send.
*Indirectly influenced* (13): responder-side bytes, packets, server flags, retransmissions, and
windows, which change only as a response. *Uncontrollable* (10): protocol identity, TTLs, and
DNS/ICMP fields, frozen at the original flow. During the search, only the directly controllable
features move; the rest stay as they were — the conservative attacker who cannot dictate how the
victim responds.

**What counts as a valid flow.** Following Merzouk et al., a candidate is feasible only if each
changed feature stays within the per-family 1st–99th percentile range of real attacks, integer
counts stay integers, flag fields stay valid, and the obvious physical relations hold (bytes ≥ 20 ×
packets, mean packet length between the min and max, size bins summing to the total, retransmissions
no larger than totals). A projection operator repairs any candidate into this set, and a
functionality check keeps the rate and volume features inside the attack family's range so an evaded
flow is still a working attack.

**What counts as success.** A flow is a *high-confidence miss* if, after the source detector's scaler
and threshold are applied on the target, it is predicted benign, its confidence is at least the
auto-accept threshold τ (set on source-validation benign traffic at a 1% review budget), and it is
feasible and functional. The high-confidence-miss rate (HCMR) is the fraction of target attack flows
the search can turn into such a miss within the query budget.

**Measuring honestly.** Feasibility is a constraint on the *attacker*, not a validity test for real
traffic. So we measure the latent (no-attack) miss rate on the real flows *without* the feasibility
box, and we measure the attacker's own contribution against the projected real flow — never against
a filtered natural baseline. An earlier draft of this work conflated the two and overstated the
attacker's effect; a self-audit caught it, and the comparison is now apples-to-apples.

## 5. Results

Every number is keyed to a file in `results/p1/` and checked by `check_numbers_p1.py`. The 240
configurations are twelve dataset pairs × four models × five seeds, so they are *not* 240
independent environments; configurations that share a pair or a model are correlated, and we read
aggregate counts as descriptions of this design, not as a sample of independent deployments, and
report per-model and per-pair breakdowns.

### 5.1 The detector is usually already blind to attacks after transfer

Before any attacker, we measure how often the transferred detector already calls a real attack flow
benign at high confidence. Across the full matrix, the mean latent high-confidence-miss rate is
**0.679**, ranging from 0 to 1. This is not limited to the pairs where ranking inverts: on the
strong-ranking BoT-IoT→CSE-CIC pair (AUC around 0.9) the latent rate still reaches **0.999** for
LogisticRegression, driven by a stale threshold and overconfidence rather than a ranking collapse.
The exposure depends on the model — mean latent rate 0.800 for LogisticRegression, 0.707 for
LightGBM, 0.685 for XGBoost, and **0.524** for RandomForest. Figure 1 shows the decomposition on the
two pairs we study in detail.

### 5.2 The confidence monitors do not see it, for a known reason

Under natural transfer the distribution-distance monitors (A-distance, Wasserstein, KS) fire on
almost everything, and the model-based monitors (ATC, confidence-drift) fire about three-quarters of
the time. Their alarms track how much the distribution moved, not whether recall collapsed.

The reason is not a calibration slip. A monitor that reads the model's score distribution alone
cannot, even in principle, see a recall collapse that leaves that distribution unchanged — because
accuracy at a low attack base rate is dominated by benign traffic, and recall is a property of the
attack subpopulation that no function of the scores can recover. Ahmed et al. (2026) proved this for
the benign-shift case (their Propositions 1–2), and we claim no novelty for it. To make the
adversarial version concrete: on the BoT-IoT→CSE-CIC / LogisticRegression cell, the adversarial
deployment has an **ATC-estimated accuracy of 0.999 while the detector's attack recall is 0.000**
(the measured accuracy of 0.908 looks fine only because benign traffic dominates it). The monitor
reports "perfect" over a detector that catches nothing.

Where the natural shift already lights the model-based monitors — both LightGBM cells, for instance —
they would fire anyway. The dangerous case is the one where they stay dark. Figure 2 is the monitor
heatmap on the two detailed pairs; the single silent cell is BoT-IoT→CSE-CIC / LogisticRegression.

### 5.3 A constrained attacker widens the gap, but only where there is room

For the two representative pairs (UNSW-NB15 and BoT-IoT into CSE-CIC-IDS2018) × four models, we run
the query-only search and separate three quantities: the latent rate (real flows, no attacker), the
projected floor (project the real flow into the feasible box, no search), and the searched rate (the
full attack). Table 1 reports all of them with bootstrap confidence intervals.

**Table 1.** Two pairs × four models, mean over 5 seeds. *lat* = latent high-confidence-miss rate;
*proj* = projected floor; *HCMR* = searched, with its mean per-seed 95% bootstrap interval; *lift* =
HCMR − proj (the search's own contribution); *Pdrop* = mean per-flow drop in P(attack); *mon* =
ATC/confidence-drift alarm during the attack (1 = fires); *defΔ* = defence HCMR reduction (bar 0.10).
Seed SD of HCMR is ≤ 0.011 except BoT-IoT/XGBoost (0.083) and BoT-IoT/RandomForest (0.074).

| source | model | AUC | lat | proj | HCMR [95% CI] | lift | Pdrop | mon | defΔ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UNSW | LightGBM | 0.236 | 0.984 | 0.679 | 0.910 [0.896, 0.924] | +0.232 | 0.010 | 1.0 | 0.072 |
| UNSW | LogisticRegression | 0.316 | 0.953 | 0.658 | 0.909 [0.895, 0.923] | +0.251 | 0.027 | 1.0 | 0.072 |
| UNSW | XGBoost | 0.158 | 0.974 | 0.670 | 0.912 [0.898, 0.926] | +0.242 | 0.028 | 1.0 | 0.072 |
| UNSW | RandomForest | 0.230 | 0.983 | 0.678 | 0.903 [0.889, 0.917] | +0.226 | 0.062 | 1.0 | 0.071 |
| BoT-IoT | LightGBM | 0.930 | 0.319 | 0.282 | 0.889 [0.874, 0.904] | +0.607 | 0.482 | 1.0 | 0.012 |
| BoT-IoT | LogisticRegression | 0.919 | 0.999 | 0.901 | 0.902 [0.887, 0.916] | +0.001 | 0.036 | **0.0** | 0.012 |
| BoT-IoT | XGBoost | 0.886 | 0.330 | 0.301 | 0.851 [0.835, 0.868] | +0.551 | 0.501 | 1.0 | 0.012 |
| BoT-IoT | RandomForest | 0.904 | 0.144 | 0.024 | 0.219 [0.200, 0.239] | +0.195 | 0.183 | 1.0 | 0.006 |

The search's own contribution is `lift` = HCMR − proj: **+0.607, +0.551, +0.251, +0.242, +0.232,
+0.226, +0.195, +0.001** across the cells. It buys high-confidence misses where the detector still
has room (both LightGBM cells, +0.607 and +0.232; XGBoost, +0.551) and essentially nothing where the
detector is already saturated (BoT-IoT/LogReg, +0.001, latent 0.999). One model resists: on
BoT-IoT→CSE-CIC, **RandomForest holds the searched rate to 0.219** (latent 0.144), because its coarse
probabilities keep most feasible flows below the high-confidence threshold.

The effort splits into two regimes (the `Pdrop` column). On the saturated cells the per-flow drop in
P(attack) is tiny (≤ 0.062) — the flows already sit a hair below the threshold, and latent exposure,
not search, does the work. On the two BoT-IoT headroom cells the drop is large (0.482 and 0.501) and
the search does real work; there the attacker, not latent exposure, dominates. The stronger
worst-case search adds little on the saturated cells (≤ 0.012) but up to +0.047 (XGBoost) and +0.049
(RandomForest) on the headroom cells, so the gap between a query-only and a white-box attacker
matters there. Query budget behaves the same way (Figure 3): more queries help on BoT-IoT/LightGBM
(0.685 at 50 queries, 0.889 at 200) and XGBoost (0.697 → 0.851), do nothing for the saturated
LogisticRegression (flat at 0.902), and never lift RandomForest far (0.136 → 0.219). Figure 4 shows
the mechanism on a headroom cell: the search slides the benign-confidence distribution across the
auto-accept line.

**Across the whole matrix.** Running the same query-only search over all twelve pairs, the mean
searched rate is **0.578**. In **74 of 240 configurations — 16 distinct source→target→model
combinations — the attacker pushes the high-confidence-miss rate above 0.5 while both confidence
monitors stay silent.** Of the **145** configurations where the attacker clears 0.5, **51%** have
both monitors silent: about half the time the attacker succeeds, the confidence monitors report
normal. The model ordering holds under attack — LogisticRegression is silent in 58% of its
configurations (mean searched rate 0.700), XGBoost 33% (0.604), LightGBM 32% (0.587), and
RandomForest 0% (never silent, and the search only reaches **0.419** on it). Figure 5 is the
latent-exposure heatmap across the quartet; Figure 6 shows the per-model silence, latent and under
attack.

### 5.4 The obvious defence does not transfer

The attacker froze the responder-side features, so a successful miss still carries the real attack's
responder signature. The natural defence is to watch the features the attacker cannot set. We first
measured which those are: predicting each responder feature from the controllable ones, most are
highly predictable (mean R² 0.84 on UNSW, 0.78 on BoT-IoT) — only `DST_TO_SRC_SECOND_BYTES` (R² 0.26
/ 0.25) and, on BoT-IoT, two retransmission features fall below 0.5. So the defence has thin material
to work with: one usable feature on UNSW, three on BoT-IoT.

A novelty detector (IsolationForest) on those features, fit on source benign traffic and thresholded
at the 1% budget, **fails its pre-registered bar everywhere**: it cuts the high-confidence-miss rate
by 0.072 (UNSW pairs) and 0.012 (BoT-IoT pairs) against a 0.10 bar, catching under 8% of misses. The
reason is the same reason the detector failed in the first place: across independently built
testbeds the low-controllability features do not transfer either, so a detector fit on source
traffic cannot tell an adversarial target flow from benign target traffic. We report this as a
result, not a footnote.

### 5.5 What it costs to check with labels

Since no score-only monitor can certify recall, the only sufficient evidence is a labelled one. We
do not propose a new estimator — the machinery (Clopper-Pearson intervals, prediction-powered risk
monitoring) is standard. We measure what it buys, and we are careful about what the labels have to be.

**The sampling assumption, stated plainly.** The audit draws *k labelled attack examples* and forms a
one-sided 95% Clopper-Pearson lower bound on recall. This is an *attack-reference* audit: it assumes
the defender can produce known attacks — replaying the source-network attacks the detector was
trained on, a red-team exercise, or honeypot captures. That is realistic for a defender who already
holds source attacks, and it certifies recall *against that reference attack set, not against unknown
or future attacks*. It does not assume free labels for target-native attacks.

**If instead you sample passively.** Drawing random target flows and labelling them, the number
needed to see k attacks is about k/π at attack prevalence π — and crucially, within a fixed budget
you might not get enough attacks at all. Simulating this (`results/p1/audit_passive.json`): at π =
0.1, a 100-label budget fails to reach 10 attacks about 45% of the time; at π = 0.01, a 100-label
budget essentially never reaches 10 attacks and a 1,000-label budget still fails about 46% of the
time; at π = 0.001, even 1,000 labels almost never suffice. Passive auditing is cheap only when
attacks are common, which they are not.

**What ten attacks can and cannot say.** With an operator who treats recall below 0.5 as unsafe, ten
labelled attacks are enough to *flag* a broken detector easily — if few are caught, the one-sided 95%
lower bound on recall sits well under 0.5 and the detector is escalated. But ten attacks can only
*clear* a detector (certify recall ≥ 0.5 at 95%) if **9 of the 10 are caught** (the Clopper-Pearson
lower bound is 0.606 at 9/10 and 0.493 at 8/10). Because 227 of our 240 configurations are deeply
unsafe (mean recall 0.086, and 80% catch under 10% of attacks), the audit's job here is
overwhelmingly correct escalation, not cheap safe-certification.

**The measurement.** Treating a configuration as unsafe when true recall is below 0.5 (227 of 240
qualify), a gate that trusts the confidence monitors — accept when neither fires — accepts an unsafe
detector in **15.0%** of configurations. The attack-reference audit (accept if the recall lower bound
clears 0.5, escalate if the upper bound falls below it, otherwise return *insufficient evidence*)
accepts an unsafe detector in **0.03%** of simulated audits at k = 10, with coverage 0.81 and 86% of
unsafe configurations escalated; at k = 50, coverage 0.90 and 95% escalated. That 0.03% is an
*empirical frequency* on this benchmark, not a guarantee — per configuration, the one-sided test
controls the chance of wrongly clearing an unsafe detector at the nominal level by construction, and
the empirical rate sits far below it only because most detectors are so broken that a few attacks
expose them. A sequential version that checks at a schedule of sizes (10, 20, …, 320) with the error
budget split across checks reaches the same coverage at a **mean of 39** labelled attacks (median
**10**), because the easy cases stop early. This matches P11's finding that a handful of labelled
target flows beats every label-free method; the audit's third verdict, *insufficient evidence*, is
the honest output the confidence monitors never give.

### 5.6 Other label-free monitors do not rescue it either

Three cheaper responses do not certify recall, for reasons Section 5.2 predicts (Table 2).

**Table 2.** Can each response certify recall at the deployed operating point?

| response | labels | certifies recall? | why / what we found |
|---|---|---|---|
| Confidence monitors (ATC, drift) | 0 | no | score-only, so blind to a recall collapse; accepts 15.0% of unsafe configs |
| Prediction-powered risk monitoring | a few | no | estimates a base-rate-weighted *overall* risk, which is itself recall-blind (error ≈ 0.09 while recall is 0 on the dangerous cell); pointed at recall it reduces to the labelled audit |
| Threshold recalibration (benign-quantile) | 0 | no | label-free, so no recall guarantee; it only trades the operating point, and where ranking inverts it does not restore recall (P11) |
| Conformal abstention (Ahmed et al. 2026) | 0 | not here | see below — an approximate reproduction did not separate dangerous from safe in our setting |
| **Labelled recall audit** | ~10 attack labels (or ≈k/π random) | yes | bounds recall directly with a finite-sample interval; needs an attack-reference sample |

On conformal abstention we were careful. Ahmed et al. report it as a reliable *drift* alarm under
their benign temporal shift. We implemented an approximate version — a split-conformal abstention
rate on the nonconformity score 1 − max(p, 1−p), calibrated on source-validation benign traffic —
and ran it over the whole matrix. In our adversarial cross-testbed setting it **did not reliably
distinguish the dangerous configurations**: it alarmed on **0.92** of safe configurations and
**0.84** of unsafe ones (about 84% sensitivity but only 8% specificity), and it was silent on three
quarters of the 36 dangerous cells where the confidence monitors were also silent. The explanation is
the same recall-invisibility: those misses are *confident*, so their nonconformity is low and a
conformal abstention does not fire. We stress that this is an approximate reproduction, not Ahmed et
al.'s exact pipeline, and that their setting differs from ours — so our result bounds, rather than
refutes, their finding. A drift alarm tells you the input changed; it does not tell you recall is
acceptable.

## 6. Discussion

The uncomfortable pattern is the one in Section 5.2: the confidence monitors are not unreliable at
random. They are quietest exactly where the detector is already most broken. A low-capacity model
that transfers "well" by AUC can still miss almost every attack at its threshold, and precisely
because its confidence barely shifts, ATC and confidence-drift report normal. This is the adversarial
reading of Ahmed et al.: not only do these monitors miss a benign drift, an attacker can keep flows
inside the region they trust.

RandomForest's resistance is informative but not a fix. Its coarse probabilities keep feasible flows
below a high auto-accept threshold, and its latent exposure is lowest. But it is never the only model
an operator runs, its in-domain scores are indistinguishable from the others, and nothing at
deployment says which model you drew. The lesson is not "use RandomForest." It is that a label-free
confidence monitor is not a safety net you can lean on across networks, and the obvious
responder-side patch does not survive the move. In this setting, a short labelled audit is worth more
than any number of unlabelled signals.

This project is one instance of a question that runs through my work: *when does a reported number
actually justify the decision made from it?* A model can look accurate in one sense and mislead the
decision it is used for — external clinical accuracy that does not hold on a new population; a pooled
fairness metric that disagrees with who gets screened; a leaderboard ranking that flips when the
answer-checker changes; a cross-network detector that fails on the traffic it is meant to catch. Here
the number is a label-free accuracy estimate, and the decision is "is it safe to keep trusting this
detector?" The honest answer is that the estimate cannot settle it, and I measure what evidence can.

## 7. Limitations

The attacks are in feature space; we make no wire-level claim, and we did not run a packet-level
check (PANTS and PLAA own that ground). Both attacked sources carry a single denial-of-service family
(volumetric), so the per-family box is one family's. The 240 configurations are correlated (twelve
pairs × four models × five seeds), so aggregate counts describe the design, not independent
deployments, and we give per-model and per-pair breakdowns. The worst-case search is an upper bound,
not a gradient attack, and it matters on the headroom cells. External AUCs here differ from P11's —
for example UNSW→CSE-CIC/LightGBM is 0.236 here against P11's 0.0697 — because of a smaller sampling
cap and a volumetric-only target, so the inversion is milder in our sample and these AUCs are
internal context, not comparable to P11's full-pipeline numbers.

The audit assumes an attack-reference sample: it certifies recall against attacks the auditor can
produce, not against unknown attacks, and passive labelling is expensive at low base rates — so the
gate is a statement about the *cost* of certification, not a claim that recall is cheap to certify
everywhere. Our conformal-abstention test is an approximate reproduction, and its negative result is
scoped to our adversarial cross-testbed setting; a faithful reproduction of Ahmed et al.'s pipeline
is untested. None of the findings establishes a universal failure of label-free monitoring — only
that the signals we tested do not separate the dangerous cases here.

## 8. Ethics and responsible use

This is defensive security research of the standard self-red-team kind. The author studies his own
detector, trained on public, offline datasets he already holds, to find a blind spot in its
monitoring and test a response. No third-party or production system is touched; all traffic
manipulation is synthetic and confined to local feature-space datasets. No packet captures are
produced and no wire-level exploit is released. The attack code stays in a private repository until
the paper is public.

## 9. Reproducibility

Every figure and table regenerates from a `results/p1/*.json` file; every headline number is keyed to
`summary_p1.json` and checked by `check_numbers_p1.py`. Seeds are fixed (42–46), configurations sit
at the top of each entry point, and each module has a runnable self-check. A pre-registration (threat
model, frozen choices, success definition, falsifiers) was committed before any attack code, with
dated amendments for scale, the worst-case search, and the memory-bounded loader.

## References

1. W. Ahmed, M. A. Rahaman, P. Roy, P. Alam. *The dashboard says "perfect:" a systematic audit of
   label-free model monitoring and test-time adaptation under temporal distribution shift in network
   intrusion detection.* Frontiers in Artificial Intelligence, 2026. DOI 10.3389/frai.2026.1928858.
2. S. Garg, S. Balakrishnan, Z. Lipton, B. Neyshabur, H. Sedghi. *Leveraging Unlabeled Data to
   Predict Out-of-Distribution Performance (ATC).* ICLR 2022. arXiv:2201.04234.
3. M. Jin, M. Apostolaki. *Robustifying ML-powered Network Classifiers with PANTS.* USENIX Security
   2025. arXiv:2409.04691.
4. J. You et al. *PLAA: Packet-level Adversarial Attacks in Network Traffic Detection.*
   arXiv:2606.28439, 2026.
5. *PAVE: A protocol-validity-aware framework for adversarial robustness evaluation of deep-learning
   intrusion detection in IoT networks.* ScienceDirect S2667295226000450, 2026.
6. G. Apruzzese et al. *Modeling Realistic Adversarial Attacks against NIDS.* ACM DTRAP 3(3):31, 2022.
   arXiv:2106.09380.
7. M. A. Merzouk, F. Cuppens, N. Boulahia-Cuppens, R. Yaich. *Investigating the practicality of
   adversarial evasion attacks on network intrusion detection.* Annals of Telecommunications 77,
   763–775, 2022. DOI 10.1007/s12243-022-00910-1.
8. A. Podkopaev, A. Ramdas. *Tracking the risk of a deployed model and detecting harmful distribution
   shifts.* arXiv:2110.06177, 2022.
9. G. Zhang, Y. Cai, G. Yu, O. Simeone. *Prediction-Powered Risk Monitoring of Deployed Models for
   Detecting Harmful Distribution Shifts.* ICML 2026. arXiv:2602.02229.
10. *RiskGate-IDS: Budget-aware two-stage NetFlow intrusion detection under domain shift.*
    ScienceDirect S187454822600048X, 2026.
11. R. S. Pall. *Confidently Wrong: Cross-Network Generalisation of Flow-Based DoS Detectors* (P11,
    this repository), 2026.

## Figures

![Figure 1](fig1_hcmr_decomposition.png)
**Figure 1.** Latent / projected / searched high-confidence-miss rate for the two detailed pairs ×
four models. Latent exposure dominates; the search adds only where the detector has room, and
RandomForest on BoT-IoT resists.

![Figure 2](fig2_monitor_alarm_heatmap.png)
**Figure 2.** ATC / confidence-drift alarm (1 = fires). Silent only on BoT-IoT→CSE-CIC /
LogisticRegression — the cell where the detector is already fully exposed.

![Figure 3](fig3_hcmr_vs_budget.png)
**Figure 3.** High-confidence-miss rate vs query budget. More queries help only where the detector
has room.

![Figure 4](fig4_confidence_margin.png)
**Figure 4.** Mechanism (BoT-IoT→CSE-CIC / XGBoost, τ = 0.968). Natural flows sit just below the
auto-accept line; the search moves them across it — the attacker buys confidence, not evasion.

![Figure 5](fig5_latent_matrix.png)
**Figure 5.** Latent high-confidence-miss rate across the full transfer matrix (mean over 4 models,
5 seeds). High on 8 of 12 pairs, moderate on three, near zero on CSE-CIC→BoT-IoT.

![Figure 6](fig6_silent_by_model.png)
**Figure 6.** Fraction of configurations where both confidence monitors are silent, per detector,
with no attack and under attack. Worst for LogisticRegression (0.33 → 0.58), absent for RandomForest.
