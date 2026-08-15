# 3. Data and protocol

*(Draft. Every quantity is produced by `scripts/` and stored in `results/`.)*

## 3.1 Why a standard feature set

Cross-dataset claims in this area usually rest on intersecting the column names of two
CICFlowMeter exports and training on whatever survives. The resulting feature space is
undocumented, varies between studies, and is itself a confound: a transfer result
obtained this way cannot be separated from the harmonisation that produced it.

We use the NetFlow v2 feature set of Sarhan et al. (2021), which was built for exactly
this purpose. Its four datasets — NF-CSE-CIC-IDS2018, NF-BoT-IoT, NF-ToN-IoT and
NF-UNSW-NB15 — ship an identical 43-column schema. We verify this rather than assume it:
`netflow_common_features()` asserts that the numeric feature sets of all four datasets
are equal, not merely overlapping, and fails loudly otherwise.

From the 43 columns we drop `Label` and `Attack` (targets) and `L4_SRC_PORT` and
`L4_DST_PORT` (socket identifiers), leaving **39 features**. Ports are dropped because in
these testbeds a destination port frequently identifies the attack script rather than the
service, which is the spurious-correlation failure Arp et al. (2022) describe.

The conventional CICFlowMeter pairing (CIC-DDoS2019 ↔ CICIDS2017) is retained as a
secondary study, so the primary conclusions can be checked in the feature space the
literature actually uses.

## 3.2 Labels

The positive class is any DoS or DDoS flow; the negative class is benign. Attacks that
are neither — Exploits, Fuzzers, PortScan, brute-force, and so on — are **not silently
discarded**. The policy is an explicit parameter and every run records how many rows it
moved, because discarding them changes the base rate and the base rate drives precision.

Labels are additionally mapped to attack families (volumetric, reflection/amplification,
low-rate application) so transfer can be reported per family. Family assignment resolves
the longest matching pattern across all families rather than taking the first family that
matches: `DoS slowloris` contains both `dos` and `slowloris`, and a first-match rule files
a low-rate attack as volumetric. Ties break on a declared precedence, which is what puts
CIC-DDoS2019's `DrDoS_*` labels in reflection/amplification rather than volumetric. The
complete label → class → family map for all seven datasets is in
`results/label_mapping.json`.

## 3.3 De-duplication, and why it changes the picture

Exact duplicates are removed **in the feature space the model actually sees** — that is,
after socket columns are dropped. Two flows differing only in source port are one example
to a model that never observes the port, and allowing such a pair to straddle a
train/test split is leakage.

The scale of this is not a detail:

| dataset | raw rows | after de-duplication | duplicate rate |
|---|---:|---:|---:|
| NF-BoT-IoT | 30,420,086 | 101,369 | 99.7% |
| NF-UNSW-NB15 | 1,986,745 | 236,999 | 88.1% |
| NF-ToN-IoT | 13,135,881 | 2,477,944 | 81.1% |
| NF-CSE-CIC-IDS2018 | 17,129,715 | 8,981,062 | 47.6% |
| CIC-DDoS2019 | 431,371 | 418,884 | 2.9% |
| CICIDS2017 | 2,313,810 | 2,231,536 | 3.6% |

We additionally count *contradictory groups*: identical feature vectors carrying opposite
labels (1,940 in NF-CSE-CIC-IDS2018, 858 in NF-UNSW-NB15). These place a hard ceiling on
any achievable in-domain score and are reported alongside it.

## 3.4 Non-finite and impossible values

The per-second rate features carry finite but physically impossible magnitudes:
`SRC_TO_DST_SECOND_BYTES` reaches 8.9 × 10³⁰⁴ in NF-ToN-IoT, produced by dividing byte
counts by near-zero flow durations — the extraction artefact Engelen et al. (2021)
document. Such cells describe the extractor, not the traffic. They are set to missing and
counted (213 in NF-CSE-CIC-IDS2018, 216 in NF-ToN-IoT) rather than allowed to become
silent infinities under a numeric cast.

## 3.5 Training protocol

The order of operations is the substance of the protocol:

> de-duplicate → split → fit scaler on **source-train only** → transform everything else

- Splits are stratified, 80/20, seeded.
- Scaler and median imputer are fitted on source-train alone and applied unchanged to the
  source test split and to every target domain.
- Target features are clipped to the range the scaler observed; the clipping is ablated,
  not assumed.
- Imbalance is handled with balanced sample weights. No resampling is used: SMOTE applied
  before a split leaks synthetic neighbours across it.
- Models: LightGBM (primary), XGBoost, RandomForest, LogisticRegression, fixed
  hyperparameters, no tuning against any target domain.
- Five seeds for the transfer matrix, three for the ablations. Seed spread is reported
  separately from sampling error.
- A stratified cap of 50,000 rows per class bounds cost. The cap changes the base rate
  and is therefore reported, and operating-point metrics are given alongside F1.

The leakage guarantee is asserted, not documented: the pipeline self-check verifies that
a scaler fitted on train maps train exactly into [0, 1] **and** lets some unseen test rows
fall outside it. A scaler that had seen the test set would fail this check.

## 3.6 Choosing the operating threshold

The decision threshold is tuned on the source test split — never on target data — and is
taken as the **midpoint of the widest tied-optimal plateau**, over candidates placed at
midpoints between consecutive score levels.

This is not a detail either. In-domain AUC here routinely reaches 1.0000, so a wide
interval of thresholds is exactly optimal. Selecting by `argmax` returns whichever
endpoint the candidate grid visited first; that endpoint sits flush against the score
distribution and is maximally fragile under any shift. In our own runs the naive choice
inflated apparent threshold loss on one pair from +0.013 to +0.195 — an artefact of the
tie-break with no relation to domain shift.

## 3.7 Metrics

Point estimates are accompanied by:

- **Paired bootstrap CIs on the gap itself** (2,000 resamples). The gap is the estimand;
  reporting one interval for the in-domain score and another for the external score says
  nothing about the interval of their difference.
- **Calibration**: ECE (15 equal-width bins) and Brier score, in both domains, because a
  detector deploys a threshold and not a ranking.
- **A ranking/threshold decomposition**: ranking loss (Δ AUC) versus threshold loss
  (external macro-F1 at the target-optimal threshold minus at the source threshold).
  These have different remedies and aggregating them hides which failure occurred.
- **Operating-point metrics**: FPR at 95% TPR, and expected alerts per hour at realistic
  base rates, since balanced-test-set F1 flatters every detector in this literature
  (the base-rate fallacy, Axelsson 2000).

## Table 2 — Arp et al. (2022) pitfalls and how this protocol addresses each

| Pitfall | How it is addressed here |
|---|---|
| Sampling bias | Four independently collected testbeds; every ordered pair run in both directions; per-dataset base rates reported rather than normalised away |
| Label inaccuracy | Full label→class map published; contradictory groups counted; label error isolated by rerunning against the DistriNet-corrected CICIDS2017 |
| Data snooping | Scaler, imputer and threshold fitted on source-train only, asserted by the pipeline self-check; no target data touches any fitting step |
| Spurious correlations | Socket columns dropped; feature classes ablated; `DNS_QUERY_ID` examined directly rather than trusted as noise |
| Biased parameter selection | Fixed hyperparameters across all domains; no tuning against any target |
| Inappropriate baseline | Four model families including logistic regression; a one-feature set as the minimal reference |
| Inappropriate performance measures | macro-F1, MCC, AUC, PR-AUC, ECE, Brier, FPR@95%TPR, alerts/hour — reported together |
| Base rate fallacy | Base rates span 1.3%–77.4% and are stated; alert volumes given at realistic rates |
| Lab-only evaluation | Acknowledged as a limitation; all four datasets are testbed captures, which is itself part of the finding |
| Inappropriate threat model | Scope stated as DoS/DDoS detection under network change, not adversarial evasion |
