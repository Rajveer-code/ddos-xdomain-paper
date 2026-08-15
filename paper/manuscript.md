# Confidently Wrong: Cross-Network DDoS Detectors Invert Rather Than Degrade

**Rajveer Singh Pall**

---

## Abstract

Flow-based DDoS detectors report accuracies above 99% and lose most of that skill when
applied to a different network. The loss is well documented; its character is not, and
the difference decides which remedies can work. Training four model families on each of
four independently constructed testbeds under a published common feature set, and
evaluating every ordered pair, we find that cross-network transfer does not decay toward
chance. It passes through it. Mean external ROC-AUC is 0.5054, 108 of 240 external
evaluations score below 0.5, and one pair reaches 0.0697. That detector ranks attack
flows below benign flows almost perfectly, and its predictions would be 93% accurate if
negated. A model at chance has lost its signal; a model at 0.07 has kept it and reversed
it. Three consequences follow. Feature engineering along the obvious semantic axis does not
help: we pre-specified the hypothesis that capacity-bound features carry testbed
identity, and removing all twenty of them changes external macro-F1 by +0.0132 [-0.0084,
+0.0320], an interval spanning zero, so the hypothesis is not supported at the power this
study affords. What the data does support is a size effect: a single protocol bit reaches
external macro-F1 0.6512 against 0.3748 for all 39 features, a paired difference of
+0.2763 [+0.2230, +0.3366]. Distribution-divergence monitoring
does not work: proxy A-distance, RBF-MMD and summed Wasserstein distance all predict the
observed loss worse than assuming the average drop, while the model's own confidence
(ATC) reaches Spearman −0.726 and cuts leave-one-pair-out error by 24%. Recalibration
works for one pair in twelve, the only one whose ranking survived, where a threshold
read from target benign traffic recovers 97.0% of the available headroom using no attack
labels, while ten labelled target flows lift mean external macro-F1 from 0.3776 to 0.7099.
Finally, the pairing chosen governs the conclusion: datasets sharing an institution fail
at the threshold and look recoverable, independently built ones fail at the ranking and
do not. All code, seeds and result files are released; every number reported here is
regenerated from them.

**Keywords:** network intrusion detection, DDoS, cross-dataset generalisation,
distribution shift, calibration, evaluation methodology

---

## 1. Introduction

Published flow-based DDoS detectors report accuracies above 99%. Deployed ones do not
behave that way. The gap between those two facts has been measured repeatedly: models
trained on one intrusion-detection dataset and tested on another lose most of their
apparent skill [D'hooge 2020; Cantone 2024]. That finding is established. What it *means*
is not, and the ambiguity is expensive, because the two available readings prescribe
opposite engineering.

The default reading is quantitative. The model is somewhat overfitted to its training
network and performance degrades, so the remedies are the familiar three: engineer
features that describe the attack rather than the capture, monitor the distance between
training and deployment distributions, and recalibrate the decision threshold on arrival.
This paper tests all three and finds the reading wrong in a way that matters.

Running every ordered pair among four independently captured testbeds, on the NetFlow v2
common feature set, with exact de-duplication and source-only preprocessing, we find that
transfer does not decay toward chance. It passes through chance. Mean external ROC-AUC is
0.5054; 108 of 240 external evaluations fall *below* 0.5; one pair reaches **0.0697**.

That last number is the paper. An AUC of 0.07 is not weak evidence. It is strong
evidence with the wrong sign. The detector ranks attack flows below benign flows with
high consistency, and negating its output would score 0.93. A model at chance has lost
its signal. A model at 0.07 has kept it and applied it backwards.

The mechanism is not mysterious once stated. If high throughput marks attack traffic in
one testbed and marks the busiest legitimate hosts in another, a decision surface fitted
to the first is close to optimal-but-negated on the second. Inversion is what you should
expect when a model has learned a real property of the wrong network.

Three consequences follow, each of which narrows a standard remedy:

**Feature engineering along the obvious axis does not help.** We pre-specified the
expectation that capacity-bound features (throughput, duration, volume) carry testbed
identity and cause the collapse, and committed it to the public repository before the
experiment ran. Removing all twenty of them moves external macro-F1 by +0.0132 [-0.0084,
+0.0320], an interval spanning zero, and capacity features alone transfer as well as the
full set. The hypothesis is not supported. What the data does support is a size effect: a
*single* protocol bit reaches external macro-F1 0.6512 where all 39 features reach
0.3748, a paired difference of +0.2763 [+0.2230, +0.3366].

**Distribution-divergence monitoring does not work.** Proxy A-distance, RBF-MMD and
summed Wasserstein distance, the quantities motivating much of the domain-adaptation
literature, all have correlations whose confidence intervals span zero, and all three
predict the observed loss *worse* than assuming the average drop. What does carry signal
is the model's own confidence: Average Thresholded Confidence reaches Spearman −0.726 and
cuts leave-one-pair-out error by 24%.

**Recalibration works for one pair in twelve.** Decomposing each failure into ranking loss
and threshold loss shows eleven of twelve fail representationally. For the single
ranking-preserving pair, a threshold read from target benign traffic, which requires no
attack labels, recovers 97.0% of the available headroom. On three others it is actively
harmful.
Ten labelled target flows do more than every zero-label method combined, lifting mean
external macro-F1 from 0.3776 to 0.7099.

A fourth result conditions all of the above. In the feature space a model actually sees,
these datasets are up to 99.7% exact duplicates: NF-BoT-IoT's 30,420,086 rows reduce to
101,369. Studies that split them without de-duplicating are testing, in part, on rows they
trained on.

### 1.1 Contributions

1. Evidence that cross-network failure in flow-based DDoS detection is **sign inversion**
   rather than degradation, across 240 external evaluations with paired-bootstrap
   intervals on the gap itself.
2. A pre-specified hypothesis about capacity features that the data does not support,
   reported with its interval and the effect size this design could detect, alongside the
   size effect the data does support.
3. A negative result on distribution-divergence measures as deployment-risk predictors,
   with a confidence-based alternative that beats a mean baseline.
4. A decomposition separating recoverable threshold failures from representational ones,
   and the demonstration that the dataset pairing chosen governs which is observed.
5. Duplicate and label-contradiction accounting that bounds every in-domain figure this
   literature reports.

---

## 2. Related work

**Cross-dataset evaluation.** D'hooge et al. [2020] cross-evaluated CIC-IDS2017 and
CSE-CIC-IDS2018 and found near-perfect in-domain scores collapsing across datasets.
Cantone et al. [2024] extended this to four datasets and four classifiers, reporting
cross-dataset accuracy "largely commensurate with random chance" and diagnosing data
anomalies behind it. Our work departs on the question asked: prior studies establish
*that* the gap exists and how large it is, whereas we characterise its *sign*, decompose
it into ranking and threshold components, and test whether it is predictable and
recoverable. The inversion we report is visible in an aggregate below 0.5 but not
interpretable from aggregate accuracy alone.

**Feature standardisation.** Sarhan et al. [2021] observed that the absence of a common
feature set makes cross-dataset comparison unreliable, and released NetFlow v2 versions of
four datasets sharing 43 fields. We adopt that feature set precisely so that our transfer
results cannot be attributed to ad-hoc harmonisation, and verify the shared space by
assertion rather than assumption.

**Dataset quality.** Engelen et al. [2021] documented labelling and extraction defects in
CICIDS2017 and released a corrected version; Lanvin et al. [2022] extended that analysis.
We use the corrected release to isolate label error from domain shift, and find the
correction moves external performance *downward*, which to our knowledge has not been
reported.

**Methodology.** Arp et al. [2022] catalogue ten recurring pitfalls in machine learning
for security. We map our protocol against all ten (Table 2). Axelsson [2000] established
that intrusion detection is dominated by the base rate; our datasets span base rates from
1.3% to 77.4%, so we report operating-point metrics alongside F1.

**Predicting performance without labels.** Garg et al. [2022] introduced Average
Thresholded Confidence for estimating target accuracy from source-calibrated scores. We
evaluate it against distribution-divergence measures in the intrusion-detection setting
and find the ordering between them reversed relative to the assumption embedded in most
domain-adaptation work.

**Domain adaptation for NIDS.** CORAL [Sun et al. 2016] and domain-invariant NIDS
approaches are established; we include CORAL as the zero-label baseline. Our contribution
is not a new adaptation method but a measurement of what the existing ones recover here,
which is close to nothing.

---

## 3. Data and experimental protocol

The design in one paragraph. Four intrusion-detection datasets, each captured on a
different testbed, are reduced to a single shared 39-feature space. For each dataset in
turn, four model families are trained on 80% of it and evaluated twice: on its own held-out
20%, which we call **in-domain**, and on each of the other three datasets entire, which we
call **external**. Nothing about the target is used in fitting: not its labels, not its
feature statistics, not its threshold. The quantity of interest is the difference between
those two evaluations, and every design decision below exists to ensure that difference
measures domain change rather than an artefact of preparation.

### 3.1 A published feature space, verified

Cross-dataset claims in this area usually rest on intersecting the column names of two
CICFlowMeter exports. The resulting space is undocumented, varies between studies, and is
itself a confound: a transfer result obtained this way cannot be separated from the
harmonisation that produced it.

We use the NetFlow v2 feature set of Sarhan et al. [2021], built for this purpose. Its
four datasets ship an identical 43-column schema. We verify rather than assume this: the
loader asserts that the numeric feature sets of all four are equal, not merely
overlapping, and fails otherwise. From the 43 columns we drop the two label columns and
`L4_SRC_PORT` and `L4_DST_PORT`, leaving **39 features**. Ports are dropped because in
these testbeds a destination port frequently identifies the attack script rather than the
service. That is the spurious-correlation failure Arp et al. describe.

The conventional CICFlowMeter pairing (CIC-DDoS2019 ↔ CICIDS2017) is retained as a
secondary study, so the primary conclusions can be checked in the feature space the
literature actually uses.

### 3.2 Labels

The positive class is any DoS or DDoS flow; the negative class is benign. Attacks that are
neither, such as exploits, fuzzers, port scans and brute-force, are not silently
discarded: the
policy is an explicit parameter and every run records how many rows it moved, because
discarding them changes the base rate and the base rate drives precision.

Labels also map to attack families (volumetric, reflection/amplification, low-rate
application-layer) so transfer can be reported per family. Family assignment resolves the
longest matching pattern across all families rather than the first family that matches:
`DoS slowloris` contains both `dos` and `slowloris`, and a first-match rule files a
low-rate attack as a flood. Ties break on a declared precedence, which places
CIC-DDoS2019's `DrDoS_*` labels in reflection/amplification. The complete label → class →
family map for all seven datasets is released.

### 3.3 De-duplication, and why it changes the picture

Exact duplicates are removed **in the feature space the model actually sees**, after
socket columns are dropped. Two flows differing only in source port are one example to a
model that never observes the port, and letting such a pair straddle a train/test split is
leakage.

**Table 1. Datasets after preparation.**

| dataset | raw rows | after de-duplication | duplicate rate | DDoS/DoS flows | base rate |
|---|---:|---:|---:|---:|---:|
| NF-CSE-CIC-IDS2018 | 17,129,715 | 8,981,062 | 47.6% | 453,237 | 0.0505 |
| NF-BoT-IoT | 30,420,086 | 101,369 | **99.7%** | 53,005 | 0.5229 |
| NF-ToN-IoT | 13,135,881 | 2,477,944 | 81.1% | 529,884 | 0.2138 |
| NF-UNSW-NB15 | 1,986,745 | 236,999 | 88.1% | 3,075 | 0.0130 |
| CIC-DDoS2019 | 431,371 | 418,884 | 2.9% | 324,197 | 0.7740 |
| CICIDS2017 | 2,313,810 | 2,231,536 | 3.6% | 321,706 | 0.1442 |
| CICIDS2017 (corrected) | 1,787,358 | 1,747,255 | 2.2% | 266,899 | 0.1528 |

Three of the four NetFlow datasets are more than 80% duplicate. We additionally count
*contradictory groups*, identical feature vectors carrying opposite labels, at 1,940 in
NF-CSE-CIC-IDS2018 and 858 in NF-UNSW-NB15. These place a hard ceiling on any achievable
in-domain score.

### 3.4 Non-finite and impossible values

The per-second rate features carry finite but physically impossible magnitudes:
`SRC_TO_DST_SECOND_BYTES` reaches 8.9 × 10³⁰⁴ in NF-ToN-IoT and `DST_TO_SRC_SECOND_BYTES`
reaches 2.3 × 10²⁵², produced by dividing byte counts by near-zero flow durations. This is
the extraction artefact Engelen et al. document. Such cells describe the extractor, not
the
traffic. They are set to missing and counted (213 in NF-CSE-CIC-IDS2018, 216 in
NF-ToN-IoT) rather than allowed to become silent infinities under a numeric cast.

### 3.5 Training

The order of operations is the substance of the protocol:

> de-duplicate → split → fit scaler on **source-train only** → transform everything else

Splits are stratified 80/20 and seeded. Scaler and median imputer are fitted on
source-train alone and applied unchanged to the source test split and to every target.
Target features are clipped to the range the scaler observed; the clipping is ablated, not
assumed. Imbalance is handled with balanced sample weights, never resampling, since SMOTE
applied before a split leaks synthetic neighbours across it. Models are LightGBM
(primary), XGBoost, RandomForest and LogisticRegression at fixed hyperparameters, with no
tuning against any target. Five seeds are used for the transfer matrix and three for the
ablations, and a stratified cap of 50,000 rows per class bounds cost.

The leakage guarantee is asserted rather than documented. The pipeline self-check verifies
that a scaler fitted on train maps train exactly into [0, 1] **and** lets some unseen test
rows fall outside it; a scaler that had seen the test set fails this check.

### 3.6 Choosing the operating threshold

The decision threshold is tuned on the source test split, never on target data, and taken
as the midpoint of the widest tied-optimal plateau, over candidates placed between
consecutive score levels.

This is not a detail. In-domain AUC here routinely reaches 1.0000, so a wide interval of
thresholds is exactly optimal. Selecting by `argmax` returns whichever endpoint the grid
visited first, and that endpoint sits flush against the score distribution, maximally
fragile under any shift. In our own runs the naive choice inflated apparent threshold loss
on one pair from +0.0128 to +0.1948, an artefact of the tie-break with no relation to
domain shift.

### 3.7 Metrics

To quantify the gap itself rather than its endpoints, we resample both test sets jointly
and report a **paired bootstrap** interval and p-value on the difference (2,000
resamples). Reporting one interval for the in-domain score and another for the external
score says nothing about the interval of their difference.

To separate a representation that stopped working from an operating point that went stale,
we decompose each gap into **ranking loss** (Δ ROC-AUC) and **threshold loss** (external
macro-F1 at the target-optimal threshold minus at the source threshold). The two have
different remedies, and aggregating them hides which failure occurred.

To ask whether a detector's probabilities remain usable, we report **ECE** (15 equal-width
bins) and **Brier score** in both domains, because a detector deploys a threshold rather
than a ranking.

To keep the base rate visible, we report **FPR at 95% TPR** and expected alerts per hour,
since balanced-test-set F1 flatters every detector in this literature.

**Table 2. Arp et al. [2022] pitfalls and how this protocol addresses each.**

| Pitfall | Addressed by |
|---|---|
| Sampling bias | Four independently collected testbeds; every ordered pair in both directions; per-dataset base rates reported, not normalised away |
| Label inaccuracy | Full label→class map released; contradictory groups counted; label error isolated against the corrected CICIDS2017 |
| Data snooping | Scaler, imputer and threshold fitted on source-train only, asserted by the pipeline self-check |
| Spurious correlations | Socket columns dropped; feature classes ablated; `DNS_QUERY_ID` examined directly rather than trusted as noise |
| Biased parameter selection | Fixed hyperparameters across all domains; no tuning against any target |
| Inappropriate baseline | Four model families including logistic regression; a one-feature set as minimal reference |
| Inappropriate performance measures | macro-F1, MCC, AUC, PR-AUC, ECE, Brier, FPR@95%TPR reported together |
| Base rate fallacy | Base rates span 1.3%–77.4% and are stated; alert volumes given at realistic rates |
| Lab-only evaluation | Acknowledged in §6; all four datasets are testbed captures, which is part of the finding |
| Inappropriate threat model | Scope stated as DoS/DDoS detection under network change, not adversarial evasion |

---

## 4. Results

### 4.1 In-domain, the problem looks solved

On its own held-out split every source reaches what this literature routinely reports.
LightGBM averages 0.9817 macro-F1 across the four sources (0.9546–1.0000) at ROC-AUC
0.9977–1.0000. The other three model families agree within a few points, and seed-to-seed
standard deviations reach at most 0.0023. Nothing here suggests an unsolved problem.

### 4.2 Out-of-domain, the failure has a sign

Applying the identical fitted model to another testbed across all 12 ordered pairs and 5
seeds, LightGBM averages 0.3788 external macro-F1 (0.1935–0.5957). The mean paired gap is
0.6029 and the paired bootstrap rejects a zero gap in **60 of 60** pair-seeds at p < 0.05
(Figure 1).

The informative statistic is external ROC-AUC. It averages 0.5054, which is chance. A mean at
chance could describe a detector that has merely lost its signal. That is not what
happened:

- **108 of 240** external runs score below 0.5;
- **149 of 240** have negative MCC;
- NF-UNSW-NB15 → NF-CSE-CIC-IDS2018 reaches **0.0697**.

Figure 2 shows the matrix. The entire NF-UNSW-NB15 source row is inverted against every
target. This is the paper's central claim: cross-network failure in flow-based DDoS
detection is the reversal of a learned relationship, not its loss.

### 4.3 Representation or operating point?

A collapsed macro-F1 admits two explanations with opposite remedies. The model may no
longer separate the classes (a **ranking** failure, requiring retraining), or it may
separate them well while the in-domain threshold has become meaningless (a **threshold**
failure, requiring only recalibration).

Eleven of twelve pairs are ranking-dominated (Figure 3). The lone exception,
NF-BoT-IoT → NF-CSE-CIC-IDS2018, retains ROC-AUC 0.9656, a ranking that transferred nearly
intact, while losing 0.4217 macro-F1 to a stale operating point.

The optimistic reading available in the literature, that cross-domain collapse is largely
a calibration artefact, is therefore true here for exactly one pair in twelve. §4.6
measures what that is worth.

### 4.4 Which features cause it? A pre-specified hypothesis the data does not support

Flow features divide into those describing *how much traffic moved and how fast*
(throughput, duration, byte and packet volumes) and those describing *what the endpoints
did* (protocol, TCP flags, TTLs, retransmissions). The first group's values are set partly
by the capturing testbed's link capacity and generator configuration. The hypothesis this
study was designed around is that these **capacity features** inflate in-domain accuracy
while carrying testbed identity, so removing them should recover external performance. It
was committed to the project's public repository before the experiment ran; the commit
that records it precedes the commit carrying the result by two hours and seventeen
minutes.

We assigned all 39 features to one of five semantic classes (20 capacity, 18 semantic, 1
held out) and trained under 17 feature sets. Each set is evaluated on the same
(source, seed) combinations as the full-feature baseline, so differences are paired and
the bootstrap resamples pairs.

**Table 3. Capacity ablation, paired differences against the full 39-feature set.**

| feature set | k | external macro-F1 | Δ vs `all` | 95% CI | p |
|---|---:|---:|---:|---|---:|
| `semantic_only` | 18 | 0.3896 | +0.0148 | [−0.0077, +0.0341] | 0.174 |
| `no_capacity` | 19 | 0.3881 | +0.0132 | [−0.0084, +0.0320] | 0.209 |
| **`all`** | **39** | **0.3748** | 0 | n/a | n/a |
| `drop_rate_throughput` | 35 | 0.3739 | −0.0010 | [−0.0033, +0.0013] | 0.406 |
| `capacity_only` | 20 | 0.3738 | −0.0011 | [−0.0293, +0.0314] | 0.915 |

Removing every capacity feature moves external macro-F1 by +0.0132, and the interval spans
zero. The hypothesis is not supported. We state that carefully: this is a failure to detect
an effect, not a demonstration that none exists. With 12 source-seed pairs the design has
80% power for a true difference of 0.0301, so effects smaller than roughly three points of
macro-F1 remain possible and unmeasured here.

**The coarse grouping does, however, hide one real sub-effect.** Dropping the 13
size and volume features alone yields +0.0615 [+0.0278, +0.0991], p < 0.001, and dropping
the three duration features yields +0.0114 [+0.0009, +0.0277], p = 0.021. Byte and packet
counts do carry testbed identity in the way the hypothesis anticipated. What fails is the
aggregation: bundling them with the throughput features, which contribute nothing
(−0.0010 [−0.0033, +0.0013]), dilutes the effect to non-significance. A semantic partition
chosen a priori was the wrong instrument, and we report that rather than re-cutting the
classes until something reached significance.

**What the data does support is a size effect.** Ordering the same 17 sets by external
performance puts the smallest on top (Figure 4).

**Table 4. External performance by feature-set size.**

| feature set | k | in-domain | external macro-F1 | Δ vs `all` | 95% CI | external AUC |
|---|---:|---:|---:|---:|---|---:|
| `only_identifier` | **1** | 0.6711 | **0.6512** | **+0.2763** | [+0.2230, +0.3366] | **0.7327** |
| `only_duration_timing` | 3 | 0.7474 | 0.5407 | +0.1659 | [+0.0944, +0.2340] | 0.5983 |
| `only_rate_throughput` | 4 | 0.9593 | 0.4688 | +0.0939 | [+0.0493, +0.1405] | 0.6248 |
| `only_flags_behaviour` | 7 | 0.8380 | 0.4288 | +0.0539 | [+0.0371, +0.0705] | 0.3759 |
| `all` | 39 | 0.9821 | 0.3748 | 0 | n/a | 0.4931 |

Every one of these differences is significant at p < 0.001. One feature out-generalises the
entire standard set by 0.2763 macro-F1 [+0.2230, +0.3366] and 0.2396 AUC, and the 38
features added on top of it purchase 0.3110 in-domain at a cost of 0.2764 externally.

We read this as follows. A gradient-boosted ensemble given 39 correlated flow statistics
finds high-order conjunctions that separate its own testbed's attack traffic essentially
perfectly, and those conjunctions encode the testbed. Restricted to one or three features
the model cannot express them, fits a coarser and more transferable rule, and pays for it
only at home. On this reading the semantic class of a feature matters less than how many
features the model is given to combine, which is consistent with size and volume mattering
individually while the 20-feature capacity bundle does not.

**A correction, stated where the claim depends on it.** `DNS_QUERY_ID` was placed in its
own class as a null control, on the assumption that a 16-bit DNS transaction ID is random
and any accuracy from it would be memorisation by construction. That assumption is wrong.

**Table 5. `DNS_QUERY_ID` is a protocol indicator, not an identifier.**

| dataset | P(attack \| id = 0) | P(attack \| id ≠ 0) |
|---|---:|---:|
| NF-CSE-CIC-IDS2018 | 0.741 | 0.000 |
| NF-BoT-IoT | 0.785 | 0.000 |
| NF-UNSW-NB15 | 0.051 | 0.001 |
| NF-ToN-IoT | 0.528 | 0.427 |

The field is zero for every non-DNS flow, making it a one-bit "this flow is DNS"
indicator; in three of four datasets DNS traffic is essentially never attack-labelled. The
ID value itself carries nothing: AUC on the raw value equals AUC on the zero/nonzero bit
to four decimal places in all four datasets, and conditioning on nonzero leaves AUC at
0.48–0.49. The correct statement is therefore that **one crude protocol bit
out-generalises the 39-feature standard set**. That is a sharper claim than the one we set
out to test, and one that depends on no feature being noise.

### 4.5 Can an operator predict the loss without labels?

An operator deploying a detector on their own network has traffic but no attack labels. We
ask whether any label-free quantity predicts the loss, evaluated leave-one-pair-out, with
all seeds of a held-out pair excluded together, against the baseline of predicting the
mean
gap (LOPO MAE 0.0827). A predictor that cannot beat "assume the average drop" is not
useful whatever its in-sample correlation.

**Table 6. Label-free predictors of the observed gap.**

| predictor | inspects | Spearman | 95% CI | LOPO MAE | vs baseline |
|---|---|---:|---|---:|---:|
| ATC estimated accuracy | model outputs | **−0.726** | [−0.836, −0.532] | **0.0629** | **−24%** |
| mean confidence drop | model outputs | +0.503 | [+0.168, +0.738] | 0.0671 | −19% |
| max per-feature Wasserstein | features | +0.433 | [+0.103, +0.720] | 0.0678 | −18% |
| summed Wasserstein | features | +0.149 | [−0.197, +0.491] | 0.0930 | +12% |
| proxy A-distance | features | −0.119 | [−0.442, +0.242] | 0.0849 | +3% |
| RBF-MMD | features | +0.031 | [−0.306, +0.385] | 0.0910 | +10% |

The result splits by what the measure inspects (Figure 5). Measures of distance between
feature distributions fail: proxy A-distance, RBF-MMD and summed Wasserstein all have
intervals spanning zero and all three are worse than the mean baseline out-of-sample. This
deserves stating plainly, because proxy A-distance in particular is the theoretical
motivation behind a large body of domain-adaptation work. In this setting, how far apart
two flow-feature distributions sit carries almost no information about how much a detector
will lose.

Measures of the model's own behaviour work, moderately. ATC reaches ρ = −0.726 against the
gap and +0.756 [+0.585, +0.861] against external macro-F1, reducing leave-one-pair-out
error by 24%. Twelve ordered pairs is a small sample, and a 24% error reduction supports
triage, a decision about which deployments need labelled validation first, rather than a
guarantee.

### 4.6 What actually fixes it

**Calibration collapses by two orders of magnitude.** Mean ECE is 0.0043 in-domain and
0.4372 externally. These detectors do not become hesitant on an unfamiliar network; they
stay confident and become wrong, which is the worse failure for an operator setting an
alert threshold.

**Zero-label recalibration fixes the diagnosable minority, and harms others.** A threshold
read from the target's benign-traffic quantiles requires no attack labels. Its recovery,
as a fraction of the headroom between the deployed threshold and the all-labels oracle,
tracks external AUC almost exactly (Figure 6).

**Table 7. Zero-label recalibration by pair.**

| pair | ext AUC | source thr | benign-quantile | oracle | headroom recovered |
|---|---:|---:|---:|---:|---:|
| BoT-IoT→IDS2018 | 0.967 | 0.5399 | **0.9558** | 0.9688 | **97.0%** |
| IDS2018→UNSW | 0.792 | 0.4918 | 0.5268 | 0.6280 | 25.7% |
| BoT-IoT→UNSW | 0.829 | 0.4820 | 0.5138 | 0.6386 | 20.3% |
| IDS2018→ToN-IoT | 0.535 | 0.3690 | 0.3474 | 0.5890 | −9.8% |
| BoT-IoT→ToN-IoT | 0.583 | 0.3773 | 0.3465 | 0.6421 | −11.7% |
| ToN-IoT→BoT-IoT | 0.642 | 0.3469 | 0.2480 | 0.7220 | **−26.4%** |

It closes 97.0% of the one ranking-preserving pair and is actively harmful on three.
CORAL, the standard zero-label covariance alignment, recovers 0.0029 macro-F1 averaged
over all pairs, which is indistinguishable from doing nothing.

**Ten labelled flows beat every zero-label method.**

**Table 8. Label budget.**

| k labelled target flows | re-tune threshold | retrain on source + k |
|---:|---:|---:|
| 0 | 0.3776 | 0.3776 |
| **10** | 0.4909 | **0.7099** |
| 50 | 0.5500 | 0.8727 |
| 100 | 0.5636 | 0.9082 |
| 500 | 0.5662 | 0.9419 |
| 1000 | 0.5623 | 0.9512 |

Ten labelled target flows lift mean external macro-F1 by 0.3323; one hundred reach 0.9082
against an in-domain ceiling near 0.98 (Figure 7). Re-tuning the threshold on the same
labels plateaus at 0.5662, because no threshold repairs an inverted ranking. The
operational conclusion is blunt: unsupervised domain adaptation is not worth the effort
here, and labelling a few dozen flows from the target network is.

### 4.7 Which attacks stop being detected

**Table 9. Per-family recall under transfer.**

| attack family | in-domain | external | drop |
|---|---:|---:|---:|
| volumetric | 0.9834 | **0.0535** | 0.9299 |
| low-rate application-layer | 1.0000 | 0.2358 | 0.7642 |
| benign (false-positive rate) | 0.0118 | 0.0753 | +0.0634 |

Volumetric floods, the largest and most conspicuous attacks and the class a detector is
least expected to miss, transfer worst, retaining 5.35% recall. This follows directly from
§4.2: a flood is defined by rates being high, and "high" is a property of the capturing
testbed. Low-rate application-layer attacks, defined by request patterns rather than
volume, survive four times better.

### 4.8 The pairing chosen governs the conclusion

Repeating the study on the conventional CIC-DDoS2019 ↔ CICIDS2017 pairing over 76 shared
CICFlowMeter features reproduces the gap: in-domain 0.9675–0.9995, external 0.3368–0.4986,
mean paired gap 0.5848, significant in 10 of 10 pair-seeds. Neither the gap nor its size
depends on the NetFlow v2 choice.

The decomposition does differ. Where the NetFlow quartet is ranking-dominated in 11 of 12
pairs, the CIC pairing is **threshold**-dominated in most configurations, and RandomForest
retains ROC-AUC 0.9348 across it with ranking loss 0.0651 against threshold loss 0.5643.

CIC-DDoS2019 and CICIDS2017 share an institution, a testbed lineage and an extractor.
Ranking largely survives that move, leaving an operating-point failure that recalibration
can address. Moving between independently constructed testbeds destroys the ranking
instead. The dataset pair chosen therefore determines which failure mode is observed, and
hence which remedy appears to work. A study confined to one institution's dataset family
will systematically overstate how recoverable the problem is.

### 4.9 Correcting label errors makes transfer look worse

**Table 10. Original versus corrected CICIDS2017, identical source model.**

| model | original | corrected | Δ macro-F1 |
|---|---:|---:|---:|
| LightGBM | 0.4827 | 0.3375 | −0.1453 |
| XGBoost | 0.4986 | 0.3391 | −0.1595 |
| RandomForest | 0.4824 | 0.3381 | −0.1443 |
| LogisticRegression | 0.4543 | 0.3287 | −0.1256 |

Mean |Δ| is 0.1437, consistent across all four model families. Label error was not
concealing good transfer; it was manufacturing the appearance of it. Roughly a quarter of
the external macro-F1 measured against the original labels does not survive correction, so
any cross-dataset result using uncorrected CICIDS2017 as a target is optimistic by about
this margin.

---

## 5. Discussion

The practical reading of these results is narrow and, we think, useful.

A detector validated on one network carries no evidence about its behaviour on another,
and the failure it will exhibit is not conservatism. It will keep issuing confident
verdicts while its ranking is wrong or reversed, at an external ECE two orders of magnitude
above its in-domain value. Monitoring for drift by comparing feature distributions will not
raise the alarm, because that distance does not track the loss. Monitoring the model's own
confidence will, imperfectly.

The remedy hierarchy inverts the usual order of effort. Elaborate zero-label adaptation
recovers 0.0029 macro-F1; a benign-quantile threshold helps substantially in the one regime
where ranking survived and hurts in three others; ten labelled flows recover 0.3323. For an
operator, the cheapest useful action is also the most effective one: label a few dozen
flows from the network you actually run.

The finding that a single protocol bit out-generalises a 39-feature standard set should not
be read as an endorsement of one-feature detectors, since its in-domain score of 0.6711 is
unusable. It is a statement about what the other 38 features are doing, which is encoding a
testbed at a 0.2764 external cost.

Finally, §4.8 has a methodological consequence beyond this paper. Because the failure mode
depends on whether the source and target share a lineage, the community's habit of
evaluating transfer within a single institution's dataset family produces optimistic and
qualitatively different conclusions from evaluation across families. Cross-institution
evaluation should be the default.

---

## 6. Threats to validity

**All four datasets are testbed captures.** None is production traffic. This limits
external validity in the usual way, but it sharpens the finding rather than weakening it:
if detectors cannot transfer between four carefully constructed research testbeds, the case
for transfer to a live network is not stronger.

**De-duplication is a consequential choice.** Removing exact duplicates in the
post-socket-drop feature space reduces NF-BoT-IoT by 99.7%. A reader who considers those
rows independent observations would obtain higher in-domain scores and a different gap. We
report the counts so either position can be evaluated, and consider the alternative
untenable: rows a model cannot distinguish cannot be independent test evidence for it.

**The stratified cap alters base rates.** Capping at 50,000 rows per class bounds cost but
changes class balance, which moves precision-sensitive metrics. Base rates are reported
throughout and operating-point metrics accompany F1 for this reason.

**Non-DoS attacks are excluded from the primary analysis.** Retaining them would change the
base rate again; the policy is explicit and the counts moved are recorded, but the primary
numbers describe a DoS/DDoS-versus-benign task.

**Twelve ordered pairs is a small sample for §4.5.** Leave-one-pair-out is the right
protocol for the question, but a 24% error reduction estimated from twelve pairs supports
triage, not a service-level guarantee.

**NF-UNSW-NB15 is a weak source.** After de-duplication it retains 3,075 DoS flows at a
1.30% base rate. Its behaviour as a source, the most strongly inverted row in the matrix,
may partly reflect that scarcity rather than domain distance alone.

**Low-rate attacks are underpowered in the NetFlow quartet.** After de-duplication,
NF-CSE-CIC-IDS2018 retains only 203 low-rate application-layer flows, so §4.7 rests partly
on the CICFlowMeter secondary study.

**Label error is bounded, not eliminated.** CICIDS2017's defects are addressed against the
corrected release; the NetFlow quartet has no comparably corrected counterpart, so residual
label noise there is unmeasured.

**The mechanism proposed for the inversion is not directly isolated.** We argue that a
gradient-boosted ensemble over 39 correlated flow statistics encodes testbed-specific
conjunctions whose sign is arbitrary across networks. The size effect in §4.4 is consistent
with this and the capacity ablation rules out one competing explanation, but we have not
identified the responsible conjunctions.

---

## 7. Conclusion

A flow-based DDoS detector moved to an independently constructed network does not become
uncertain. It becomes confidently inverted: mean external ROC-AUC 0.5054, 108 of 240
external evaluations below chance, and one pair at 0.0697 whose predictions would be 93%
accurate if negated.

That distinction governs what can be done about it. Feature engineering along the obvious
semantic axis does not help: the pre-specified capacity hypothesis is not supported
(+0.0132 [−0.0084, +0.0320]), although size and volume features do matter individually
(+0.0615 [+0.0278, +0.0991]). Feature-set *size* is the effect that survives, to the point
that one protocol bit out-generalises the 39-feature standard by +0.2763 [+0.2230,
+0.3366]. Distribution-divergence monitoring does not predict the loss;
model confidence partially does. Recalibration recovers almost everything in the one regime
where ranking survived and nothing elsewhere, and ten labelled target flows outperform
every zero-label method available.

Underneath all of it, these benchmarks are up to 99.7% duplicate, and correcting known
label errors moves measured transfer *down* by 0.1437 macro-F1. The in-domain numbers this
field reports, and a measurable share of the cross-dataset numbers, are bounded by dataset
quality before any model is chosen.

---

## Data and code availability

All code, fixed seeds, configuration and result files are released. Every number in this
paper is regenerated from `results/*.json` by the scripts that produced them; a
verification script checks that each numeric literal in the manuscript traces to a stored
result.

## References

`[PLACEHOLDER: full bibliographic entries. Verified sources cited in text: Axelsson 2000;
Sun et al. 2016; D'hooge et al. 2020 (JISA); Engelen et al. 2021 (WTMC); Sarhan et al. 2021;
Arp et al. 2022 (USENIX Security); Garg et al. 2022; Lanvin et al. 2022 (CRiSIS); Cantone et
al. 2024 (arXiv:2402.10974 / IEEE Access). Format per Computers & Security style.]`
