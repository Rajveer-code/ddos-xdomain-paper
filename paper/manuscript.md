# Confidently Wrong: Ranking Inversion in Cross-Network Denial-of-Service Detection

**Rajveer Singh Pall**

---

## Abstract

Flow-based DDoS detectors report accuracies above 99% and lose most of that skill when
applied to a different network. The loss is well documented; its character is not, and
the difference decides which remedies can work. Training four model families on each of
four independently constructed testbeds under a published common feature set, and
evaluating every ordered pair, we find that cross-network transfer does not decay toward
chance. It passes through it. Pooling four model families, twelve ordered pairs and five seeds, 108 of 240 external evaluations score below 0.5 and mean external ROC-AUC is 0.5054; and one pair reaches 0.0697, meaning attack flows are systematically assigned lower scores than benign flows; negating that detector's score would yield an ROC-AUC of approximately 0.9303. A model at chance carries no usable ordering; a model at 0.0697 carries a strong one with the sign reversed. Three consequences follow. Feature engineering along the obvious semantic axis does not
help: we pre-specified the hypothesis that capacity-bound features carry testbed
identity, and removing all twenty of them changes external macro-F1 by +0.0132 [-0.0084,
+0.0320], an interval spanning zero, so the hypothesis is not supported at the power this
study affords. A one-feature set does reach external macro-F1 0.6512 against 0.3748 for all 39, a paired difference of +0.2763 [+0.2230, +0.3366], but a control over random subsets at controlled size shows that dimensionality accounts for the smaller part of this and the identity of that feature — a DNS indicator that is itself a dataset shortcut — for the larger. Feature count tracks in-domain separability (Spearman +0.626) and external macro-F1 (-0.290) while leaving external ranking untouched (+0.004 [-0.081, +0.088]), making it a threshold effect rather than a representational one. Distribution-divergence monitoring did not work in this benchmark: proxy A-distance, RBF-MMD and summed Wasserstein distance all predicted the observed loss worse than assuming the average drop, while the model's own confidence
(ATC) reaches Spearman −0.726 and cuts leave-one-pair-out error by 24%. Recalibration works for one pair in twelve: in the primary LightGBM analysis it is the only pair whose ranking survived, and there a threshold read from target benign traffic recovers 97.0% of the available headroom using no attack labels, but pooled over held-out evaluation sets that recalibration is net harmful. Ten labelled target flows, used to retrain, reach median macro-F1 0.7253 [0.5604, 0.9540] and exceed what the best achievable threshold reaches with unlimited target labels (0.6158).
Finally, the failure mode depends strongly on the dataset pair: the same-lineage CIC pairing failed mainly at the threshold and looked recoverable, while the independently built transfers failed at the ranking. Cross-network evaluation therefore has to distinguish ranking failure from threshold failure, because the two admit different remedies.

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
This paper tests a representative version of each and finds the reading incomplete in a way that matters.

Running every ordered pair among four independently captured testbeds, on the NetFlow v2
common feature set, with exact de-duplication and source-only preprocessing, we find that
transfer does not decay toward chance. It passes through chance. Mean external ROC-AUC is
0.5054; 108 of 240 run-level external evaluations fall *below* 0.5, as do 5 of the 12
ordered pairs once seeds are averaged; one pair reaches **0.0697**.

That last number is what an aggregate near chance conceals. An AUC of 0.0697 is not weak evidence; it is strong evidence with the wrong sign. Attack flows are systematically assigned lower scores than benign flows, and negating the detector's output would yield an ROC-AUC of approximately 0.9303. Note that this is a statement about ranking, not about accuracy: ROC-AUC is threshold-free, and the accuracy of a negated detector would still depend on the operating point and the target prevalence. A model at chance carries no usable ordering. A model at 0.0697 carries a strong ordering with the sign reversed.

A plausible mechanism is easy to state. If high throughput marks attack traffic in one testbed and marks the busiest legitimate hosts in another, a decision surface fitted to the first is close to optimal-but-negated on the second. Two of our own results constrain what that mechanism can be. Logistic regression inverts on the same pairs as the tree ensembles (§4.2), so it cannot require high-order feature interactions, which a linear model cannot represent. And feature count is uncorrelated with external ranking quality (§4.4), so it is not a matter of model capacity either. What remains is the simplest reading: individual feature-label associations reverse sign between these networks. We do not isolate which associations, and §6 says so.

Three consequences follow, each of which narrows a standard remedy:

**Feature engineering along the obvious axis does not help.** We pre-specified the
expectation that capacity-bound features (throughput, duration, volume) carry testbed
identity and cause the collapse, and committed it to the project repository before the experiment ran. Removing all twenty of them moves external macro-F1 by +0.0132 [-0.0084,
+0.0320], an interval spanning zero, and capacity features alone transfer as well as the
full set. The hypothesis is not supported. A one-feature set does out-transfer the full set by +0.2763 [+0.2230, +0.3366], but a control over randomly chosen subsets at controlled size shows dimensionality to be the smaller part of that advantage. Random subsets gain +0.105 on the way from 39 features down to one, while the chosen feature beats a random single feature by +0.147. The two are measured against different baselines and are not an additive split of +0.2763 (§4.4); what they jointly establish is that most of the advantage is the feature, which turns out to be a second dataset shortcut.

**Distribution-divergence monitoring did not work here.** Proxy A-distance, RBF-MMD and
summed Wasserstein distance, the quantities motivating much of the domain-adaptation
literature, all have correlations whose confidence intervals span zero, and all three
predict the observed loss *worse* than assuming the average drop. What does carry signal
is the model's own confidence: Average Thresholded Confidence reaches Spearman −0.726 and
cuts leave-one-pair-out error by 24%.

**Recalibration works for one pair in twelve.** Decomposing each failure in the primary LightGBM analysis into ranking loss and threshold loss shows eleven of twelve fail representationally. For the single
ranking-preserving pair, a threshold read from target benign traffic, which requires no
attack labels, recovers 97.0% of the available headroom. On three others it is actively
harmful.
Ten labelled target flows, drawn from an adaptation pool disjoint from the evaluation set, lift median external macro-F1 from 0.3919 to 0.7253 and beat the best threshold obtainable with unlimited labels.

A fourth result conditions all of the above. In the feature space a model actually sees,
these datasets are up to 99.7% exact duplicates: NF-BoT-IoT's 30,420,086 rows reduce to
101,369. Studies that split them without de-duplicating are testing, in part, on rows they
trained on.

### 1.1 Contributions

1. Evidence that cross-network failure can manifest as systematic **ranking inversion** rather than monotonic degradation, across 240 model-pair-seed evaluations, with permutation and label-reversal controls establishing that the below-chance results are not a pipeline artefact.
2. A pre-specified hypothesis about capacity features that the data does not support,
   reported with its interval and the effect size this design could detect, alongside the
   size effect the data does support.
3. A negative result on distribution-divergence measures as deployment-risk predictors,
   with a confidence-based alternative that beats a mean baseline.
4. A failure taxonomy separating threshold failure from ranking failure, and ranking failure from sign inversion, together with evidence that which mode appears depends strongly on the source-target pairing.
5. Duplicate and label-contradiction accounting that bounds every in-domain figure this
   literature reports.

---

## 2. Related work

### 2.1 The cross-dataset gap

That flow-based intrusion detectors transfer badly is not in dispute. D'Hooge et al. [2020]
established reference scores on CIC-IDS2017 and CSE-CIC-IDS2018 across twelve supervised
algorithms and concluded that the classifiers could not operate reliably on traffic from a
network unseen at training time. Cantone et al. [2024] extended the design to four datasets
and four classifiers, reported cross-dataset accuracy largely commensurate with random
chance, and traced part of it to anomalies in the data itself.

Our study shares their protocol and departs on the question. Prior work establishes *that*
the gap exists and how large it is. We ask what kind of failure it is. That distinction is
not rhetorical: an aggregate accuracy near chance is compatible with a detector that has
lost its signal and with one that has reversed it, and only the second is visible once
ROC-AUC is reported per ordered pair. The remedies implied by the two readings differ
completely, which is why sections 4.4 to 4.6 test three of them rather than proposing a
fourth.

### 2.2 Feature standardisation and dataset quality

Sarhan et al. [2021] identified the absence of a common feature set as a structural
obstacle to cross-dataset claims, and released NetFlow v2 conversions of four datasets
sharing 43 fields. We adopt that feature set precisely so our transfer results cannot be
attributed to ad-hoc harmonisation, and verify the shared space by assertion rather than
assumption. The four source datasets themselves are CSE-CIC-IDS2018 [Sharafaldin et al.
2018], BoT-IoT [Koroniotis et al. 2019], ToN-IoT [Alsaedi et al. 2020] and UNSW-NB15
[Moustafa and Slay 2015]; the secondary study uses CIC-DDoS2019 [Sharafaldin et al. 2019]
and CICIDS2017 [Sharafaldin et al. 2018].

Dataset quality has its own literature. Engelen et al. [2021] documented labelling and
traffic-generation defects in CICIDS2017 and released a corrected version; Lanvin et al.
[2022] extended the analysis and quantified the effect of the corrections on measured
performance. Both studies examine in-domain consequences. We use the corrected release
differently, as an instrument: applying one identical source model to the original and
corrected targets isolates label error from domain shift, and the result runs opposite to
the intuitive direction (§4.11).

Our duplicate accounting (§3.3) is adjacent to this work but, to our knowledge, has not
been reported at this scale for the NetFlow v2 datasets. That three of four are more than
80% duplicate in the model's own feature space bounds every in-domain number computed on
them.

### 2.3 Methodology and evaluation norms

Arp et al. [2022] catalogue ten recurring pitfalls in machine learning for security, of
which sampling bias, data snooping, spurious correlations and the base-rate fallacy bear
directly on cross-dataset evaluation. We map the protocol against all ten in Table 2 rather
than asserting compliance in prose. Axelsson [2000] established that intrusion detection is
dominated by the base rate; the datasets here span base rates from 1.3% to 77.4%, so
balanced-test-set F1 is not comparable across them and operating-point metrics are reported
alongside.

### 2.4 Predicting performance without labels

Estimating target accuracy from unlabelled data is an active area outside security. Garg et
al. [2022] introduced Average Thresholded Confidence, which learns a confidence threshold
on source data and predicts accuracy as the fraction of unlabelled target points above it.
The competing family of approaches measures distance between source and target feature
distributions directly, which is also the theoretical motivation for domain-adversarial
training. Section 4.5 evaluates both families on the same twelve ordered pairs and finds
their ordering reversed relative to the assumption embedded in most of that work: the
distribution-distance measures lose to a mean baseline, and the confidence-based estimator
does not.

### 2.5 Domain adaptation for intrusion detection

Adapting a detector to a new network is a well-populated area, including covariance
alignment [Sun et al. 2016] and domain-invariant representation learning for NIDS
specifically. We make no methodological contribution here and do not claim one. CORAL
appears in §4.8 as the standard zero-label baseline, and the contribution is the
measurement: what the available zero-label methods actually recover in this setting, which
is close to nothing, against what a handful of labelled target flows recovers, which is
most of the gap.

## 3. Data and experimental protocol

The design in one paragraph. Four intrusion-detection datasets, each captured on a
different testbed, are reduced to a single shared 39-feature space. For each dataset in
turn, four model families are trained on 80% of it and evaluated twice: on its own held-out
20%, which we call **in-domain**, and on each of the other three datasets, which we call **external**. In the primary transfer experiment nothing about the target is used in fitting: not its labels, not its
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

Three of the four NetFlow datasets are more than 80% duplicate. We additionally count *contradictory groups*, identical feature vectors carrying opposite labels, at 1,940 in NF-CSE-CIC-IDS2018 and 858 in NF-UNSW-NB15. Those counts are taken over the full attack taxonomy. Under the DoS-only policy the primary analysis actually uses, both fall to zero: every contradictory group in these two datasets pairs a benign flow with a *non-DoS* attack, and those rows are removed before modelling. The ceiling is therefore real for a general intrusion detector on these captures and absent for the DoS detector studied here, which is verified rather than assumed in §4.6.

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
Target features are clipped to the range the scaler observed; the clipping is ablated in §4.6, not assumed. Imbalance is handled with balanced sample weights, never resampling, in all model fitting reported here; the label-budget experiment of §4.8 deliberately draws a balanced labelled adaptation set, which is a controlled supervision-budget intervention rather than a training-time resampling choice, since SMOTE
applied before a split leaks synthetic neighbours across it. Models are LightGBM
(primary), XGBoost, RandomForest and LogisticRegression at fixed hyperparameters, with no
tuning against any target. Five seeds are used for the transfer matrix and three for the ablations and remedy experiments, which are correspondingly more expensive; the asymmetry is a cost decision and every reported interval states the number of pairs it rests on.

A stratified cap of 50,000 rows per class bounds cost, and it is applied to **both** the source and the target: external metrics are computed on a seeded stratified sample of the de-duplicated target, not on the target in full. Because the cap equalises the two classes it also changes the evaluated prevalence, which moves every prevalence-sensitive metric. This is why ROC-AUC, which is invariant to prevalence under a fixed score ordering, carries the paper's central claim, and macro-F1 and MCC are read alongside it rather than in place of it.

The order of operations that carries the leakage guarantee is: de-duplicate, then split, then fit. Exact duplicates are removed from a dataset before any partition is drawn, so no feature vector can appear on both sides of a split. The imputer and the scaler are fitted on the source training partition alone and applied unchanged to the source evaluation partition and to every target; the decision threshold is chosen on the source evaluation partition (§3.6). No target label, target feature statistic or target-derived threshold enters the primary transfer experiment. A pipeline self-check verifies the scaler property on every run: a scaler fitted on train maps train exactly into [0, 1] **and** lets some unseen rows fall outside it, which a scaler that had seen those rows cannot do.

### 3.6 Choosing the operating threshold

The decision threshold is chosen on the source evaluation split, never on target data, and taken as the midpoint of the widest tied-optimal plateau, over candidates placed between
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

Two features of these numbers matter for what follows. First, they are obtained *after*
de-duplication, so they are not inflated by the train/test contamination described in §3.3;
the uncorrected figures would be higher still. Second, ROC-AUC reaches 1.0000 on
NF-CSE-CIC-IDS2018 to four decimal places, meaning the classes are perfectly separable in
the source domain. Perfect in-domain separability is what makes the threshold plateau of
§3.6 wide, and it is the first hint that the model is fitting something more specific than
attack behaviour.

### 4.2 Out-of-domain, the failure has a sign

Applying the identical fitted model to another testbed across all 12 ordered pairs and 5
seeds, LightGBM averages 0.3788 external macro-F1 (0.1935–0.5957). The mean paired gap is
0.6029 and the paired bootstrap rejects a zero gap in **60 of 60** pair-seeds at p < 0.05
(Figure 1).

![Figure 1](../figures/fig1_generalization_gap.png)

**Figure 1.** In-domain versus external macro-F1 for all 12 ordered pairs, LightGBM, mean over 5 seeds.


The informative statistic is external ROC-AUC. It averages 0.5054, which is chance. A mean at
chance could describe a detector that has merely lost its signal. That is not what
happened:

- **108 of 240** (model, pair, seed) runs score below 0.5;
- **149 of 240** have negative MCC;
- NF-UNSW-NB15 → NF-CSE-CIC-IDS2018 reaches **0.0697**, averaged over its five seeds.

Figure 2 shows the matrix. The entire NF-UNSW-NB15 source row is inverted against every
target. This is the paper's central claim: cross-network failure can involve systematic ranking inversion rather than simple attenuation of the learned relationship. It is not the only mode observed. Of the 240 external evaluations, 108 fall below chance, so inversion is common rather than universal, and the taxonomy in §4.3 separates it from the milder modes.

![Figure 2](../figures/fig2_auc_matrix.png)

**Figure 2.** External ROC-AUC per ordered pair. Values below 0.5 indicate the ranking inverts in the target domain.


**The inversion is not a property of one learner.** The same 12 ordered pairs and 5 seeds
were run for four model families, which lets the question be asked directly rather than
assumed away.

**Table 3. Model-family robustness.** External performance over all 12 ordered pairs and 5
seeds. The last column is the single worst run, not a pair mean.

| model | n | mean external AUC | 95% CI | below 0.5 | mean macro-F1 | mean MCC | lowest run |
|---|---:|---:|---|---:|---:|---:|---:|
| Logistic regression | 60 | 0.5091 | [0.4448, 0.5735] | 41.7% | 0.4789 | +0.0590 | 0.0668 |
| Random forest | 60 | 0.5499 | [0.4925, 0.6085] | 40.0% | 0.3665 | −0.0596 | 0.1360 |
| XGBoost | 60 | 0.5184 | [0.4537, 0.5840] | 51.7% | 0.3988 | −0.0063 | 0.0339 |
| **LightGBM (primary)** | 60 | 0.5054 | [0.4391, 0.5718] | 46.7% | 0.3788 | −0.0459 | 0.0421 |

No family escapes. Mean external AUC lies between 0.5054 and 0.5499 for all four and the
share of runs below chance between 40.0% and 51.7%; three of the four have negative mean
MCC. Random forest transfers nominally best and still puts two runs in five below chance.
Logistic regression carries the most weight here, because it is the one family that cannot
represent interactions among features at all, and it inverts as readily as the ensembles
do, with a worst run of 0.0668.

Averaging seeds within each pair shows that the failure is concentrated rather than
diffuse.

**Table 4. External ROC-AUC by ordered pair and model family.** Mean over 5 seeds. Bold
marks a ranking below chance.

| source→target | LR | RF | XGB | LGBM | families below 0.5 |
|---|---:|---:|---:|---:|---:|
| BoT-IoT→IDS2018 | 0.9825 | 0.9742 | 0.9811 | 0.9656 | 0 of 4 |
| BoT-IoT→ToN-IoT | 0.6390 | **0.4642** | **0.4569** | 0.5833 | 2 of 4 |
| BoT-IoT→UNSW-NB15 | **0.3888** | 0.7361 | 0.8191 | 0.8256 | 1 of 4 |
| IDS2018→BoT-IoT | 0.6717 | 0.6499 | **0.4800** | 0.5006 | 1 of 4 |
| IDS2018→ToN-IoT | 0.6884 | **0.4967** | 0.5805 | 0.5497 | 1 of 4 |
| IDS2018→UNSW-NB15 | 0.6321 | 0.7791 | 0.7703 | 0.7750 | 0 of 4 |
| ToN-IoT→BoT-IoT | 0.6406 | 0.6064 | 0.7255 | 0.6279 | 0 of 4 |
| ToN-IoT→IDS2018 | 0.6296 | 0.6848 | **0.4904** | **0.4127** | 2 of 4 |
| ToN-IoT→UNSW-NB15 | **0.0726** | 0.5326 | **0.3908** | **0.3241** | 3 of 4 |
| UNSW-NB15→BoT-IoT | **0.2334** | **0.2964** | **0.1910** | **0.2045** | 4 of 4 |
| UNSW-NB15→IDS2018 | **0.3162** | **0.1729** | **0.0901** | **0.0697** | 4 of 4 |
| UNSW-NB15→ToN-IoT | **0.2139** | **0.2056** | **0.2449** | **0.2256** | 4 of 4 |

Nine of twelve pairs fall below chance in at least one family; three do so in all four,
and those three are exactly the transfers out of NF-UNSW-NB15, which §4.5 takes up
separately. This is the more useful statement of the result. Inversion is not scattered
noise that a different learner would average away: it attaches to particular source-target
combinations and survives a change of hypothesis class, including a change to a model that
can only add up single-feature contributions.

**What counts as one observation.** The counts above treat each (model, pair, seed) run as
a unit, and those units are not independent — five seeds share a source dataset and four
families share a split. Taking the ordered pair as the inferential unit instead, 5 of 12
pairs have a mean external AUC below chance, and the pair-level mean is 0.5054 [0.3589,
0.6529] over 12 pairs. That interval is wide, and it contains both substantial inversion
and substantial above-chance transfer. We therefore do not claim that the population mean
across conceivable network pairs is at or below chance; twelve pairs cannot support that.
The claim this paper does defend is the one the interval leaves untouched: particular
transfers invert systematically, repeatably across seeds, and in every model family tried.
Throughout, run-level counts are reported as "of 240" and pair-level counts as "of 12", and
the two are not interchangeable.

---

### 4.3 Representation or operating point?

A collapsed macro-F1 admits two explanations with opposite remedies. The model may no
longer separate the classes (a **ranking** failure, requiring retraining), or it may
separate them well while the in-domain threshold has become meaningless (a **threshold**
failure, requiring only recalibration).

Eleven of twelve pairs are ranking-dominated (Figure 3). The lone exception,
NF-BoT-IoT → NF-CSE-CIC-IDS2018, retains ROC-AUC 0.9656, a ranking that transferred nearly
intact, while losing 0.4217 macro-F1 to a stale operating point.

![Figure 3](../figures/fig3_failure_decomposition.png)

**Figure 3.** Ranking loss versus threshold loss per ordered pair. Points below the diagonal fail representationally; only one pair lies above it.


The optimistic reading available in the literature, that cross-domain collapse is largely
a calibration artefact, is therefore true here for exactly one pair in twelve. §4.8
measures what that is worth.

The decomposition also gives an operator a decision rule, though not a free one. Ranking
loss requires target labels to compute, so it cannot be measured before deployment. What
§4.7 shows is that a label-free proxy for the same quantity exists and is moderately
informative, which is why the two sections are ordered as they are: the decomposition
establishes that the distinction matters, and the prediction section asks whether it can be
made without labels.

### 4.4 Which features cause it? A pre-specified hypothesis the data does not support

Flow features divide into those describing *how much traffic moved and how fast*
(throughput, duration, byte and packet volumes) and those describing *what the endpoints
did* (protocol, TCP flags, TTLs, retransmissions). The first group's values are set partly
by the capturing testbed's link capacity and generator configuration. The hypothesis this
study was designed around is that these **capacity features** inflate in-domain accuracy
while carrying testbed identity, so removing them should recover external performance. It was committed to the project repository before the experiment ran; the commit recording it precedes the commit carrying the result by two hours and seventeen minutes. The repository was private at that time and made public on release, so this is time-stamped pre-specification in version history rather than public pre-registration, and we claim only the former.

We assigned all 39 features to one of five semantic classes (20 capacity, 18 semantic, 1
held out) and trained under 17 feature sets. Each set is evaluated on the same
(source, seed) combinations as the full-feature baseline, so differences are paired and
the bootstrap resamples pairs.

**Table 5. Capacity ablation, paired differences against the full 39-feature set.**

| feature set | k | external macro-F1 | Δ vs `all` | 95% CI | p |
|---|---:|---:|---:|---|---:|
| `semantic_only` | 18 | 0.3896 | +0.0148 | [−0.0077, +0.0341] | 0.174 |
| `no_capacity` | 19 | 0.3881 | +0.0132 | [−0.0084, +0.0320] | 0.209 |
| **`all`** | **39** | **0.3748** | 0 | n/a | n/a |
| `drop_rate_throughput` | 35 | 0.3739 | −0.0010 | [−0.0033, +0.0013] | 0.406 |
| `capacity_only` | 20 | 0.3738 | −0.0011 | [−0.0293, +0.0314] | 0.915 |

Removing every capacity feature moves external macro-F1 by +0.0132, and the interval spans
zero. The hypothesis is not supported. We state that carefully: this is a failure to detect an effect, not a demonstration that none exists. The interval does not exclude effects up to roughly three points of macro-F1 in either direction, and with 12 source-seed pairs the study is not positioned to resolve differences of that size.

**The coarse grouping does, however, hide one real sub-effect.** Dropping the 13
size and volume features alone yields +0.0615 [+0.0278, +0.0991], p < 0.001, and dropping
the three duration features yields +0.0114 [+0.0009, +0.0277], p = 0.021. Byte and packet
counts do carry testbed identity in the way the hypothesis anticipated. What fails is the
aggregation: bundling them with the throughput features, which contribute nothing
(−0.0010 [−0.0033, +0.0013]), dilutes the effect to non-significance. A semantic partition
chosen a priori was the wrong instrument, and we report that rather than re-cutting the
classes until something reached significance.

**Smaller sets do transfer better, but not mainly because they are smaller.** Ordering
the same 17 sets by external performance puts the smallest on top (Figure 4).

![Figure 4](../figures/fig4_feature_set_size.png)

**Figure 4.** Feature-set size against in-domain and external macro-F1. The single-feature set attains the best external score of any subset tested.


**Table 6. External performance by feature-set size.**

| feature set | k | in-domain | external macro-F1 | Δ vs `all` | 95% CI | external AUC |
|---|---:|---:|---:|---:|---|---:|
| `only_identifier` | **1** | 0.6711 | **0.6512** | **+0.2763** | [+0.2230, +0.3366] | **0.7327** |
| `only_duration_timing` | 3 | 0.7474 | 0.5407 | +0.1659 | [+0.0944, +0.2340] | 0.5983 |
| `only_rate_throughput` | 4 | 0.9593 | 0.4688 | +0.0939 | [+0.0493, +0.1405] | 0.6248 |
| `only_flags_behaviour` | 7 | 0.8380 | 0.4288 | +0.0539 | [+0.0371, +0.0705] | 0.3759 |
| `all` | 39 | 0.9821 | 0.3748 | 0 | n/a | 0.4931 |

Every one of these differences is significant at p < 0.001. One feature out-generalises the entire standard set by 0.2763 macro-F1 [+0.2230, +0.3366].

That ordering cannot, on its own, tell dimensionality apart from feature identity: a one-bit DNS indicator and a four-feature throughput block differ in both. We therefore ran a control that varies size alone, sampling random subsets at controlled k over a 1 to 39 grid with splits, seeds, model and targets held fixed (584 runs).

**Table 7. Random subsets at controlled size.** Median over subsets, sources and seeds; 5th and 95th percentiles in brackets.

| k | in-domain | external macro-F1 | external AUC |
|---:|---:|---|---:|
| 1 | 0.7158 | 0.5046 [0.2835, 0.6973] | 0.5889 |
| 3 | 0.9250 | 0.4214 [0.2950, 0.5881] | 0.5336 |
| 10 | 0.9774 | 0.4021 [0.2928, 0.5195] | 0.5766 |
| 20 | 0.9842 | 0.3993 [0.2786, 0.5111] | 0.5898 |
| 39 | 0.9843 | 0.3997 [0.3017, 0.4406] | 0.5843 |

Size matters, and less than the semantic ablation implied. Across random subsets external macro-F1 falls from 0.5046 at k=1 to 0.3997 at k=39, Spearman -0.290 [-0.369, -0.210]. That accounts for **+0.105** of the one-feature advantage. The remaining **+0.147** is identity: `DNS_QUERY_ID` alone reaches 0.6512 where a random single feature reaches 0.5046. Both components are measured inside the control, against its own median 39-feature baseline of 0.3997, whereas Table 6's +0.2763 is a mean paired difference against the full-feature runs at 0.3748. One baseline is a median over random subsets and the other a mean over the full-feature set, so the two components do not sum to +0.2763 and are not a partition of it. What survives either normalisation is that dimensionality is the smaller share: most of the one-feature advantage is the feature, not the count.

**The size component is a threshold effect, not a representational one.** Feature count correlates strongly with in-domain macro-F1 (Spearman +0.626 [+0.566, +0.679]) and negatively with external macro-F1 (-0.290), but is uncorrelated with external ROC-AUC (+0.004 [-0.081, +0.088]). Adding features sharpens separation at home and leaves the target ordering unchanged; what degrades is the usefulness of the operating point chosen against that sharper separation. This connects directly to §4.3 and to §3.6: perfect in-domain separability widens the tied-optimal threshold plateau and pushes the chosen threshold into a position that does not survive a change of network.

An earlier draft of this paper explained the ordering by supposing that a gradient-boosted ensemble given 39 correlated flow statistics finds high-order conjunctions encoding its own testbed, which a one-feature model cannot express. Two of our own results rule that out. Logistic regression inverts on the same pairs as the tree ensembles (§4.2) and cannot represent such conjunctions at all, and feature count is uncorrelated with external ranking quality, which is what a capacity explanation would predict it to govern. We record the discarded explanation because the experiments that killed it are in this paper, and a reader who reaches the same intuition deserves to know it was tested.

**A correction, stated where the claim depends on it.** `DNS_QUERY_ID` was placed in its
own class as a null control, on the assumption that a 16-bit DNS transaction ID is random
and any accuracy from it would be memorisation by construction. That assumption is wrong.

**Table 8. `DNS_QUERY_ID` is a protocol indicator, not an identifier.**

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
0.48–0.49. The correct statement is therefore that a **one-bit DNS indicator out-generalises the 39-feature standard set**, and we read that as a finding about the benchmark rather than as a detector worth deploying. A field that separates the classes this well across three of four independently built testbeds, while carrying no information about attack behaviour, is a dataset-construction shortcut: DNS traffic was generated as background in these testbeds and was therefore almost never labelled as attack. Its in-domain score of 0.6711 is unusable in any case. What it establishes is that feature count and semantic quality are different things, and that the standard feature set contains at least one shortcut that transfers better than the behaviour the model is supposed to be learning.

### 4.5 Is the strongest inversion a weak-source artefact?

The three pairs that invert in every model family (§4.2) share a source, and that source
retains only 3,075 attack flows after de-duplication at a 1.30% base rate. Source identity
and source size are therefore confounded in the study's most extreme result, and the
obvious alternative explanation is that a detector trained on very few positives simply
fails unpredictably.

We separate the two by holding size fixed and varying identity: every source is starved to
the same 3,075 attack flows that NF-UNSW-NB15 actually has, and the transfer matrix is
rerun over two model families and three seeds.

**Table 9. Source-size control.** External ROC-AUC, 144 transfers.

| regime | source | n | mean external AUC | below chance |
|---|---|---:|---:|---:|
| matched (3,075 attacks) | NF-UNSW-NB15 | 18 | 0.3889 | 72.2% |
| matched (3,075 attacks) | other three sources | 54 | 0.6155 | 25.9% |
| full cap | NF-UNSW-NB15 | 18 | 0.2513 | 88.9% |
| full cap | other three sources | 54 | 0.6147 | 20.4% |

Starving the other three sources does not make them invert. Their mean external AUC moves
from 0.6147 at the full cap to 0.6155 when reduced to NF-UNSW-NB15's attack count, a
difference of 0.0008. The inversion is therefore not explained by the number of positive training flows alone.

NF-UNSW-NB15 inverts under both regimes and remains 0.227 below the other sources at
identical size. The explanation is a property of that network rather than of its sample.

One secondary effect is worth stating because it is not what we expected. NF-UNSW-NB15's
external AUC is *higher* under the matched regime (0.3889) than under the full cap
(0.2513). The two regimes differ for this source in class balance rather than attack
count: capping at 3,075 balances it, whereas the ordinary cap leaves roughly eight benign
flows per attack. A more balanced source therefore inverts less severely, which is
consistent with the threshold reading in §4.4 but is a single observation and we do not
build on it.

### 4.6 Do the preprocessing choices manufacture the result?

Three decisions in §3.3 and §3.4 could in principle produce the effect this paper reports
rather than expose it. Each is ablated over four sources and two seeds, holding everything
else fixed.

**Table 10. Preprocessing sensitivity.** Mean over four sources and two seeds. The primary
configuration is marked.

| configuration | in-domain macro-F1 | external macro-F1 | external ROC-AUC |
|---|---:|---:|---:|
| de-duplicated (primary) | 0.9857 | 0.3952 | 0.5229 |
| duplicates retained | 0.9968 | 0.4345 | 0.5476 |
| contradictory groups excluded | 0.9857 | 0.3952 | 0.5229 |
| clipped, LightGBM (primary) | 0.9857 | 0.3951 | 0.5245 |
| unclipped, LightGBM | 0.9857 | 0.3951 | 0.5245 |
| clipped, logistic regression (primary) | 0.9195 | 0.4834 | 0.5295 |
| unclipped, logistic regression | 0.9195 | 0.5057 | 0.5460 |

**De-duplication changes what the study would have concluded.** Retaining duplicates lifts
in-domain macro-F1 by 0.0111 and external macro-F1 by 0.0392, which makes the argument in
§3.3 concrete: a study that splits these captures without removing exact duplicates reports
in-domain numbers it has not earned.

The more consequential effect is on the external side, and it does not run in one direction.
Retaining duplicates raises NF-UNSW-NB15's external ROC-AUC from 0.1872 to 0.4486, because
its 1,915,838 raw rows collapse to 203,641 distinct ones and the surviving copies are not
distributed evenly across the decision surface. Severe inversion would have been reported as
ordinary near-chance failure. On NF-BoT-IoT the same choice moves external ROC-AUC the other
way, from 0.7858 down to 0.6126. Duplicate contamination does not simply inflate results; it
adds source-dependent noise to the very quantity this paper estimates, and on the strongest
inversion in the study it would have hidden the finding.

**Contradictory groups do not bind here.** Excluding them changes nothing at all: the two
rows of Table 10 are identical because, under the DoS-only policy, there are no such groups
to exclude. Zero of 8,889,592 distinct feature vectors in NF-CSE-CIC-IDS2018 and zero of
203,641 in NF-UNSW-NB15 carry both labels. The 1,940 and 858 groups counted in §3.3 all pair
a benign flow with a non-DoS attack and disappear with those rows. The arbitrary-survivor
concern that motivates the check is therefore inapplicable to this analysis, which is worth
stating precisely because the check was run expecting the opposite.

**Clipping cannot matter for the tree ensembles, and slightly hurts the linear model.** For
LightGBM the ablation is exactly zero on every metric, and this is a property of the model
rather than a measurement: every split threshold is learned inside the source training
range, so clamping an out-of-range value to that range cannot move a row across any split.
We report it because a null that follows from the model class is evidence about the design,
not about the data, and reporting it as though it were the latter would be misleading.

Logistic regression is where the choice can bind, and there it is mildly harmful: not
clipping improves external macro-F1 by 0.0223 and external ROC-AUC by 0.0165. Clipping
touches between 4,014 and 51,468 target rows per source-seed, so the intervention is not
negligible in scope. The direction matters for the paper's honesty rather than its
conclusion. For the tree-based primary model clipping is immaterial; for logistic regression the chosen policy modestly reduces external performance. Neither manufactures the collapse. Unclipped logistic regression still transfers at 0.5460
overall, and on NF-UNSW-NB15 it still inverts, at 0.4087.

None of the three decisions creates the effect. One of them, de-duplication, would have
materially changed the conclusion had it been skipped, in the direction of understating what
we found.

### 4.7 Can an operator predict the loss without labels?

An operator deploying a detector on their own network has traffic but no attack labels. We
ask whether any label-free quantity predicts the loss, evaluated leave-one-pair-out, with
all seeds of a held-out pair excluded together, against the baseline of predicting the
mean
gap (LOPO MAE 0.0827). A predictor that cannot beat "assume the average drop" is not
useful whatever its in-sample correlation.

**Table 11. Label-free predictors of the observed gap.**

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
intervals spanning zero and all three are worse than the mean baseline out-of-sample. This deserves stating plainly, because proxy A-distance in particular is the theoretical motivation behind a large body of domain-adaptation work. In this benchmark, these three marginal feature-distribution measures carry almost no information about how much a detector will lose. The result is not paradoxical: these measures describe the shift in $P(X)$, whereas the loss is driven by the shift in $P(Y \mid X)$, and the two need not move together. A benchmark on which they did would be a benchmark on which covariate shift dominated concept shift, and these four testbeds are evidently not that.

![Figure 5](../figures/fig5_gap_forecast.png)

**Figure 5.** Observed generalization gap against three label-free predictors, with Spearman correlation and bootstrap CI.


Measures of the model's own behaviour work, moderately. ATC reaches ρ = −0.726 against the
gap and +0.756 [+0.585, +0.861] against external macro-F1, reducing leave-one-pair-out
error by 24%. Twelve ordered pairs is a small sample, and a 24% error reduction supports
triage, a decision about which deployments need labelled validation first, rather than a
guarantee.

### 4.8 What actually fixes it

**Calibration collapses by two orders of magnitude.** Mean ECE is 0.0043 in-domain and
0.4372 externally. These detectors do not become hesitant on an unfamiliar network; they
stay confident and become wrong, which is the worse failure for an operator setting an
alert threshold.

**Zero-label recalibration fixes the diagnosable minority, and harms others.** A threshold
read from the target's benign-traffic quantiles requires no attack labels. Its recovery,
as a fraction of the headroom between the deployed threshold and the all-labels oracle,
tracks external AUC almost exactly (Figure 6).

![Figure 6](../figures/fig6_remedies.png)

**Figure 6.** External macro-F1 under the deployed threshold, zero-label benign-quantile recalibration, and the all-labels oracle, ordered by external AUC.


**Table 12. Zero-label recalibration by pair.**

| pair | ext AUC | source thr | benign-quantile | oracle | headroom recovered |
|---|---:|---:|---:|---:|---:|
| BoT-IoT→IDS2018 | 0.967 | 0.5399 | **0.9558** | 0.9688 | **97.0%** |
| IDS2018→UNSW | 0.792 | 0.4918 | 0.5268 | 0.6280 | 25.7% |
| BoT-IoT→UNSW | 0.829 | 0.4820 | 0.5138 | 0.6386 | 20.3% |
| IDS2018→ToN-IoT | 0.535 | 0.3690 | 0.3474 | 0.5890 | −9.8% |
| BoT-IoT→ToN-IoT | 0.583 | 0.3773 | 0.3465 | 0.6421 | −11.7% |
| ToN-IoT→BoT-IoT | 0.642 | 0.3469 | 0.2480 | 0.7220 | **−26.4%** |

It closes 97.0% of the one ranking-preserving pair and is actively harmful on three.

Pooled, it does not pay for itself. Scored on the held-out evaluation sets of §4.8.3,
benign-quantile recalibration reaches median macro-F1 0.3482 against 0.3919 for the
deployed source threshold, so averaged over all twelve pairs the procedure loses ground.
The per-pair table is the useful reading and the pooled number is the warning attached to
it: recalibration is worth doing when the ranking survived, and worth avoiding otherwise,
which means an operator needs the diagnosis of §4.3 before choosing it rather than after.
CORAL, a standard zero-label covariance alignment, recovers 0.0029 macro-F1 averaged
over all pairs, which is indistinguishable from doing nothing. This bounds CORAL
specifically; stronger representation-learning approaches to domain-invariant intrusion
detection exist and are not evaluated here.

**Ten labelled flows outperformed the zero-label baselines evaluated here.**

**Table 13. Label budget, leakage-free.** Median over 20 independent label draws per
(pair, budget), 12 ordered pairs, 2 seeds; 5th and 95th percentiles in brackets.

| k labelled target flows | re-tune threshold | retrain on source + k |
|---:|---|---|
| 0 | 0.3919 [0.2779, 0.5106] | 0.3919 [0.2779, 0.5106] |
| **10** | 0.5600 [0.2851, 0.9383] | **0.7253 [0.5604, 0.9540]** |
| 50 | 0.6090 [0.3336, 0.9592] | 0.8795 [0.7952, 0.9804] |
| 100 | 0.6104 [0.3482, 0.9604] | 0.9116 [0.8393, 0.9932] |
| 500 | 0.6135 [0.3503, 0.9600] | 0.9548 [0.8958, 0.9974] |
| 1000 | 0.6142 [0.3620, 0.9609] | 0.9574 [0.9228, 0.9986] |

Each target is split once per (pair, seed) into a disjoint adaptation pool and evaluation
set. Labels are drawn only from the pool and every score is computed only on the
evaluation set, including the zero-label baselines, so the comparison is like for like.
Draws are balanced, k/2 per class: at a 1.3% base rate a prevalence-proportional draw of
ten flows usually contains no attack at all, which would measure the base rate rather than
the value of supervision.

An earlier version of this experiment fine-tuned on k target rows and then scored a target
set that still contained them, and tuned the threshold on rows it went on to score. We
report the corrected design here. The direction of the error is worth stating: the
contaminated run gave 0.7099 at k=10 against 0.7253 for the clean one, so the leak was
depressing the estimate slightly rather than inflating it, and the conclusion is unchanged.

Ten labelled flows lift median external macro-F1 from 0.3919 to 0.7253, a hundred reach 0.9116, and a thousand reach 0.9574 against an in-domain ceiling near 0.98 (Figure 7). Re-tuning the threshold on the same labels plateaus at roughly 0.61, and the reason is structural rather than empirical: no threshold applied to a reversed ordering recovers it, whatever the label budget.

The sharpest comparison is against the oracle. The best threshold obtainable on the evaluation set with unlimited target labels reaches 0.6158. Retraining on **ten** labelled flows reaches 0.7253 and so exceeds it. Recalibration and supervision are not two points on one scale; beyond a certain point recalibration cannot buy what a few labels buy immediately.

Recovery is uneven across pairs, and unevenly in an informative direction. NF-UNSW-NB15 to NF-CSE-CIC-IDS2018, the most strongly inverted transfer in the study at ROC-AUC 0.070, reaches 0.9076 [0.8174, 0.9566] with ten labels. That is what inversion predicts: the ordering still carries the information, with the sign reversed, and a small labelled sample is enough to supply the sign. The
operational reading, at the scope the evidence supports, is that in this benchmark a small
labelled target sample was substantially more effective than the zero-label baselines
tested. We evaluated one covariance-alignment method and one threshold heuristic, not the
space of unsupervised domain adaptation, and the claim is limited accordingly.

![Figure 7](../figures/fig7_label_budget.png)

**Figure 7.** External macro-F1 against the number of labelled target flows, averaged over all ordered pairs and seeds.


### 4.9 Which attacks stop being detected

**Table 14. Per-family recall under transfer.**

| attack family | in-domain | external | drop |
|---|---:|---:|---:|
| volumetric | 0.9834 | **0.0535** | 0.9299 |
| low-rate application-layer | 1.0000 | 0.2358 | 0.7642 |
| benign (false-positive rate) | 0.0118 | 0.0753 | +0.0634 |

Volumetric floods, the largest and most conspicuous attacks and the class a detector is
least expected to miss, transfer worst, retaining 5.35% recall. This follows directly from
§4.2: a flood is defined by rates being high, and "high" is a property of the capturing
testbed. Low-rate application-layer attacks, defined by request patterns rather than
volume, had roughly four times the external recall, an estimate limited by how few low-rate flows survive de-duplication.

### 4.10 The pairing chosen governs the conclusion

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
instead. The failure mode therefore depends strongly on the dataset pair. We have one
same-lineage pairing against a cross-lineage quartet, so this is evidence consistent with a
lineage effect rather than a demonstration of one: CIC-DDoS2019 and CICIDS2017 may be
unusually similar for reasons other than shared provenance. Under either reading, a study
confined to one institution's dataset family risks overstating how recoverable the problem
is.

### 4.11 Correcting label errors makes transfer look worse

**Table 15. Original versus corrected CICIDS2017, identical source model.**

| model | original | corrected | Δ macro-F1 |
|---|---:|---:|---:|
| LightGBM | 0.4827 | 0.3375 | −0.1453 |
| XGBoost | 0.4986 | 0.3391 | −0.1595 |
| RandomForest | 0.4824 | 0.3381 | −0.1443 |
| LogisticRegression | 0.4543 | 0.3287 | −0.1256 |

Mean |Δ| is 0.1437, consistent across all four model families. For this source-target evaluation, correcting the target labels reduced measured macro-F1 by 0.1256 to 0.1595 across model families, so label error can materially inflate apparent transfer performance. Roughly a quarter of
the external macro-F1 measured against the original labels does not survive correction, so
any cross-dataset result using uncorrected CICIDS2017 as a target is optimistic by about
this margin.

---

## 5. Discussion

The practical reading of these results is narrow and, we think, useful.

Validation on one network provides no empirical guarantee of behaviour on another,
and the failure it will exhibit is not conservatism. It will keep issuing confident
verdicts while its ranking is wrong or reversed, at an external ECE two orders of magnitude
above its in-domain value. The three marginal feature-distribution measures evaluated here would not raise the alarm for these failures, because those distances did not track the loss. Monitoring the model's own
confidence will, imperfectly.

The remedy hierarchy inverts the usual order of effort. Zero-label feature alignment by
CORAL recovers 0.0029 macro-F1; a benign-quantile threshold helps substantially in the one
regime where ranking survived and hurts in three others; ten labelled flows recover 0.3323.
For an operator, the cheapest useful action is also the most effective one: label ten flows
from the network you actually run. The ordering holds for the zero-label methods we
evaluated and is not a claim about unsupervised domain adaptation in general.

The finding that a single protocol bit out-generalises a 39-feature standard set should not
be read as an endorsement of one-feature detectors, since its in-domain score of 0.6711 is
unusable. It is a statement about what the other 38 features are doing, which is encoding a
testbed at a 0.2764 external cost.

Finally, §4.10 has a methodological consequence beyond this paper. Because the failure mode
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

**Twelve ordered pairs is a small sample for §4.7.** Leave-one-pair-out is the right
protocol for the question, but a 24% error reduction estimated from twelve pairs supports
triage, not a service-level guarantee.

**NF-UNSW-NB15 is a small source.** After de-duplication it retains 3,075 DoS flows at a 1.30% base rate, and it produces the study's most extreme inversion. The obvious confound is tested rather than conceded in §4.5: starving every other source to the same attack count leaves their transfer essentially unchanged (0.6147 to 0.6155), while NF-UNSW-NB15 remains 0.227 below them at identical size. Sample size does not account for the effect. Its class balance has a secondary influence that we note but do not interpret.

**Low-rate attacks are underpowered in the NetFlow quartet.** After de-duplication,
NF-CSE-CIC-IDS2018 retains only 203 low-rate application-layer flows, so §4.9 rests partly
on the CICFlowMeter secondary study.

**Label error is bounded, not eliminated.** CICIDS2017's defects are addressed against the
corrected release; the NetFlow quartet has no comparably corrected counterpart, so residual
label noise there is unmeasured.

**The mechanism behind the inversion is not isolated.** Our experiments rule two
explanations out without establishing a third. It is not a gradient-boosting artefact:
logistic regression inverts on the same source-target pairs (§4.2) and cannot represent
feature interactions at all. It is not model capacity expressed as feature count: external
ranking quality is uncorrelated with the number of features (§4.4), which is the quantity a
capacity account predicts it should track. What remains, and what we did not measure, is
which individual feature-label associations reverse sign between networks. Invariance
across four hypothesis classes is consistent with reversal in the low-order associations
those classes have in common, but consistency is not identification, and we do not report
it as a finding.

---

## 7. Conclusion

A flow-based DDoS detector moved to an independently constructed network does not become
uncertain. It becomes confidently inverted: 108 of 240 run-level external evaluations score
below chance, 5 of 12 ordered pairs do so once seeds are averaged, three of those invert in
all four model families tried, and the worst pair reaches ROC-AUC 0.0697 — a ranking so
consistently reversed that negating the score would yield 0.9303.

That distinction governs what can be done about it. Feature engineering along the obvious
semantic axis does not help: the pre-specified capacity hypothesis is not supported
(+0.0132 [−0.0084, +0.0320]), although size and volume features do matter individually
(+0.0615 [+0.0278, +0.0991]). One protocol bit out-generalises the 39-feature standard by
+0.2763 [+0.2230, +0.3366], but a control at matched size splits that advantage into +0.105
for dimensionality and +0.147 for the identity of that feature, a DNS indicator that
separates the classes without describing attack behaviour. Feature count moves the
operating point and leaves external ranking alone. Distribution-divergence monitoring does
not predict the loss; model confidence partially does. Recalibration recovers almost
everything in the one regime where ranking survived and is net harmful pooled across the
others, and ten labelled target flows beat every zero-label method we evaluated, including
the best threshold that unlimited target labels can buy.

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

1. Arp, D., Quiring, E., Pendlebury, F., Warnecke, A., Pierazzi, F., Wressnegger, C.,
   Cavallaro, L., and Rieck, K. "Dos and Don'ts of Machine Learning in Computer Security."
   *31st USENIX Security Symposium*, 2022.

2. Axelsson, S. "The base-rate fallacy and the difficulty of intrusion detection."
   *ACM Transactions on Information and System Security* 3(3), 186–205, 2000.

3. Cantone, M., Marrocco, C., and Bria, A. "On the Cross-Dataset Generalization of
   Machine Learning for Network Intrusion Detection." arXiv:2402.10974, 2024.

4. D'Hooge, L., Wauters, T., Volckaert, B., and De Turck, F. "Inter-dataset
   generalization strength of supervised machine learning methods for intrusion detection."
   *Journal of Information Security and Applications* 54, 102564, 2020.

5. Engelen, G., Rimmer, V., and Joosen, W. "Troubleshooting an Intrusion Detection
   Dataset: the CICIDS2017 Case Study." *IEEE Security and Privacy Workshops (WTMC)*, 2021.

6. Garg, S., Balakrishnan, S., Lipton, Z. C., Neyshabur, B., and Sedghi, H. "Leveraging
   Unlabeled Data to Predict Out-of-Distribution Performance." *International Conference on
   Learning Representations (ICLR)*, 2022. arXiv:2201.04234.

7. Lanvin, M., Gimenez, P.-F., Han, Y., Majorczyk, F., Mé, L., and Totel, E. "Errors in
   the CICIDS2017 dataset and the resulting fair evaluation of machine learning."
   *International Conference on Risks and Security of Internet and Systems (CRiSIS)*, 2022.

8. Sarhan, M., Layeghy, S., Moustafa, N., and Portmann, M. "Towards a Standard Feature
   Set for Network Intrusion Detection System Datasets." arXiv:2101.11315, 2021.

9. Sun, B., Feng, J., and Saenko, K. "Return of Frustratingly Easy Domain Adaptation."
   *AAAI Conference on Artificial Intelligence*, 2016.

10. Sharafaldin, I., Lashkari, A. H., and Ghorbani, A. A. "Toward Generating a New
    Intrusion Detection Dataset and Intrusion Traffic Characterization." *International
    Conference on Information Systems Security and Privacy (ICISSP)*, 2018. (CICIDS2017)

11. Sharafaldin, I., Lashkari, A. H., Hakak, S., and Ghorbani, A. A. "Developing
    Realistic Distributed Denial of Service (DDoS) Attack Dataset and Taxonomy."
    *International Carnahan Conference on Security Technology (ICCST)*, 2019. (CIC-DDoS2019)

12. Moustafa, N., and Slay, J. "UNSW-NB15: a comprehensive data set for network
    intrusion detection systems." *Military Communications and Information Systems
    Conference (MilCIS)*, 2015.

13. Koroniotis, N., Moustafa, N., Sitnikova, E., and Turnbull, B. "Towards the
    development of realistic botnet dataset in the Internet of Things for network forensic
    analytics: Bot-IoT dataset." *Future Generation Computer Systems* 100, 779–796, 2019.

14. Alsaedi, A., Moustafa, N., Tari, Z., Mahmood, A., and Anwar, A. "TON_IoT telemetry
    dataset: A new generation dataset of IoT and IIoT for data-driven intrusion detection
    systems." *IEEE Access* 8, 165130–165150, 2020.
