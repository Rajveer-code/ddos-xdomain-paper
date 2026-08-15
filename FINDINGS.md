# FINDINGS

Every number here traces to a file in `results/`. Nothing is quoted from another paper.
Where a pre-specified hypothesis was not supported, it is recorded as not supported, with
its interval and the smallest effect the design could have detected.

Protocol: shared 39-feature NetFlow v2 space, exact de-duplication in the model's own
feature space, source-only scaling and imputation, balanced sample weights, stratified
cap of 50,000 rows per class, LightGBM primary with XGBoost / RandomForest /
LogisticRegression alongside, 5 seeds for the matrix and 3 for the ablations.

---

## F1 — Cross-network transfer does not degrade. It inverts.

`results/transfer_matrix.json`, `results/matrix_summary.json`

| | LightGBM, 12 ordered pairs, 5 seeds |
|---|---|
| in-domain macro-F1 | 0.9817 (min 0.9546, max 1.0000) |
| external macro-F1 | 0.3788 (min 0.1935, max 0.5957) |
| external ROC-AUC | 0.5054 (min 0.0421, max 0.9683) |
| external MCC | −0.0459 |
| mean paired gap (macro-F1) | 0.6029, significant at p<0.05 in **60/60** pair-seeds |

Across all four models and all seeds: **108 of 240** external runs score ROC-AUC below
0.5, and **149 of 240** have negative MCC.

`NF-UNSW-NB15 → NF-CSE-CIC-IDS2018` reaches **AUC 0.0697**. A detector that ranks
attacks below benign traffic that consistently is not failing at random; inverting its
output would score 0.93. The learned decision surface is not merely non-transferable,
it is anti-correlated in the target domain.

**Failure mode is overwhelmingly representational, not operational.** Decomposing each
gap into ranking loss (ΔAUC) and threshold loss (external macro-F1 at the target-optimal
threshold minus at the source threshold), **11 of 12 pairs are ranking-dominated**. The
sole exception is `NF-BoT-IoT → NF-CSE-CIC-IDS2018`, which holds AUC 0.9656 while losing
0.4217 to a stale operating point — the one case recalibration alone would rescue.

---

## F2 — The pre-specified capacity hypothesis is not supported (and the grouping hid a real sub-effect).

`results/feature_ablation.json`

Hypothesis: capacity-bound features (rate, duration, volume) encode testbed properties,
inflate in-domain accuracy and destroy transfer. Removing them should recover external
performance. It does not.

| feature set | k | ext macro-F1 | Δ vs all |
|---|---:|---:|---:|
| `semantic_only` | 18 | 0.3896 | +0.0148 |
| `no_capacity` | 19 | 0.3881 | +0.0132 |
| **`all`** | **39** | **0.3748** | — |
| `drop_rate_throughput` | 35 | 0.3739 | −0.0010 |
| `capacity_only` | 20 | 0.3738 | −0.0011 |

Stripping every capacity feature buys +0.0132 macro-F1, 95% CI [−0.0084, +0.0320],
p = 0.209 by paired bootstrap over the 12 source-seed pairs. The interval spans zero, so
this is a failure to detect an effect rather than a demonstration that none exists; the
design has 80% power for a true difference of 0.0301.

**The coarse grouping hid a real sub-effect.** Dropping the 13 size/volume features alone
gives **+0.0615 [+0.0278, +0.0991], p < 0.001**, and dropping the three duration features
gives +0.0114 [+0.0009, +0.0277], p = 0.021. Byte and packet counts do carry testbed
identity as the hypothesis anticipated. What failed was the aggregation: bundling them with
throughput features that contribute nothing (−0.0010 [−0.0033, +0.0013]) dilutes the effect
below significance. Reported as an aggregation failure rather than re-cutting the classes
until something reached significance. See `results/ablation_intervals.json`.

**Provenance.** The hypothesis was committed in `ed7fb10` at 13:32:00 and the result in
`6d82cd1` at 15:49:37 on 2026-08-15. That is pre-specification in public history, not
pre-registration, and the manuscript says so.

## F3 — It is a feature-set *size* effect. One protocol bit beats the standard set.

| feature set | k | in-domain | ext macro-F1 | ext AUC |
|---|---:|---:|---:|---:|
| `only_identifier` | **1** | 0.6711 | **0.6512** | **0.7327** |
| `only_duration_timing` | 3 | 0.7474 | 0.5407 | 0.5983 |
| `only_rate_throughput` | 4 | 0.9593 | 0.4688 | 0.6248 |
| `only_flags_behaviour` | 7 | 0.8380 | 0.4288 | 0.3759 |
| `all` | 39 | 0.9821 | 0.3748 | 0.4931 |

The best external performers are the smallest sets. The 38 features beyond the single
best one buy **+0.311 in-domain** and cost **−0.276 external**. The standard NetFlow v2
feature set is actively harmful for cross-network deployment.

### Correction: `DNS_QUERY_ID` is not a null control

It entered the taxonomy as a null control on the assumption that a 16-bit DNS
transaction ID is noise. Measurement refuted that and the code comment asserting it has
been corrected.

| dataset | P(attack \| id = 0) | P(attack \| id ≠ 0) |
|---|---:|---:|
| NF-CSE-CIC-IDS2018 | 0.741 | 0.000 |
| NF-BoT-IoT | 0.785 | 0.000 |
| NF-UNSW-NB15 | 0.051 | 0.001 |
| NF-ToN-IoT | 0.528 | 0.427 |

The field is zero for every non-DNS flow, making it a one-bit "this flow is DNS"
indicator; DNS traffic is essentially never attack-labelled in three of four datasets.
The ID *value* carries nothing: AUC on the raw value equals AUC on the zero/nonzero bit
to four decimals in every dataset, and conditioning on nonzero leaves AUC at 0.48–0.49.

The claim is therefore "one crude protocol bit out-generalises the standard 39-feature
set", which is both true and sharper than the original framing.

---

## F4 — Distribution divergence does not predict the gap. Model confidence partially does.

`results/divergence.json`, `results/gap_forecast.json`
36 pair-seed observations, 12 ordered pairs, leave-one-pair-out (all seeds of a held-out
pair excluded together). Baseline = predict the mean gap, LOPO MAE 0.0827.

| predictor | Spearman vs gap | 95% CI | LOPO MAE | vs baseline |
|---|---:|---|---:|---:|
| **ATC estimated accuracy** | **−0.726** | [−0.836, −0.532] | **0.0629** | **−24%** |
| mean confidence drop | +0.503 | [+0.168, +0.738] | 0.0671 | −19% |
| max per-feature Wasserstein | +0.433 | [+0.103, +0.720] | 0.0678 | −18% |
| summed Wasserstein | +0.149 | [−0.197, +0.491] | 0.0930 | +12% (worse) |
| proxy A-distance | −0.119 | [−0.442, +0.242] | 0.0849 | +3% (worse) |
| RBF-MMD | +0.031 | [−0.306, +0.385] | 0.0910 | +10% (worse) |

The three standard domain-adaptation divergence measures all have confidence intervals
spanning zero and all three are **worse than the mean baseline** out-of-sample. How far
apart two feature distributions sit says almost nothing about how much a detector will
lose. What the model says about its own predictions does: ATC (Garg et al., 2022)
reaches ρ = −0.726 and cuts LOPO error by 24%.

Stated with its limits: twelve ordered pairs is a small sample and a 24% error reduction
is useful, not decisive.

---

## F5 — Dataset quality bounds every in-domain number in this literature.

`results/dataset_summary.json`

Exact duplicates **in the feature space the model actually sees**:

| dataset | raw rows | after dedup | dup rate | contradictory groups |
|---|---:|---:|---:|---:|
| NF-BoT-IoT | 30,420,086 | 101,369 | **99.7%** | — |
| NF-UNSW-NB15 | 1,986,745 | 236,999 | **88.1%** | 858 |
| NF-ToN-IoT | 13,135,881 | 2,477,944 | **81.1%** | — |
| NF-CSE-CIC-IDS2018 | 17,129,715 | 8,981,062 | 47.6% | 1,940 |
| CIC-DDoS2019 | 431,371 | 418,884 | 2.9% | — |
| CICIDS2017 | 2,313,810 | 2,231,536 | 3.6% | — |

Studies that split these without de-duplicating are testing partly on rows they trained
on. Contradictory groups — identical feature vectors carrying opposite labels — put a
hard ceiling on any achievable in-domain score.

Attack base rates span 1.3% (NF-UNSW-NB15) to 77.4% (CIC-DDoS2019), so raw F1 is not
comparable across these datasets and must be read at matched operating points.

### Rate-feature overflow

The per-second rate features carry finite but physically impossible magnitudes:
`SRC_TO_DST_SECOND_BYTES` reaches **8.9 × 10³⁰⁴** in NF-ToN-IoT and
`DST_TO_SRC_SECOND_BYTES` reaches 2.3 × 10²⁵², produced by dividing byte counts by
near-zero flow durations (Engelen et al., 2021). 213 such cells in NF-CSE-CIC-IDS2018
and 216 in NF-ToN-IoT. They exceed float32 entirely and describe the extractor rather
than the traffic.

---

## F6 — Calibration collapses by two orders of magnitude, and zero-label fixes mostly fail.

`results/calibration.json` · 12 pairs × 3 seeds

Mean **ECE 0.0043 in-domain → 0.4372 external**. These detectors are not merely wrong on
a new network; they are confidently wrong, which is the worse failure for an operator
choosing an alert threshold.

Benign-quantile recalibration — a threshold taken from target benign-traffic quantiles,
needing no attack labels — recovers this fraction of the headroom between the deployed
threshold and the all-labels oracle:

| pair | external AUC | source thr | benign-quantile | oracle | headroom recovered |
|---|---:|---:|---:|---:|---:|
| BoT-IoT→IDS2018 | 0.967 | 0.5399 | **0.9558** | 0.9688 | **97.0%** |
| UNSW→IDS2018 | 0.079 | 0.3263 | 0.3325 | 0.3432 | 36.9% |
| IDS2018→UNSW | 0.792 | 0.4918 | 0.5268 | 0.6280 | 25.7% |
| BoT-IoT→UNSW | 0.829 | 0.4820 | 0.5138 | 0.6386 | 20.3% |
| IDS2018→ToN-IoT | 0.535 | 0.3690 | 0.3474 | 0.5890 | −9.8% |
| BoT-IoT→ToN-IoT | 0.583 | 0.3773 | 0.3465 | 0.6421 | −11.7% |
| ToN-IoT→BoT-IoT | 0.642 | 0.3469 | 0.2480 | 0.7220 | **−26.4%** |

It nearly closes the one ranking-preserving pair and is **actively harmful on three**.
It is a fix for a diagnosable minority, not a general remedy.

**CORAL recovers 0.0029 macro-F1** averaged over all pairs (0.3805 vs 0.3776). Nothing.

## F7 — Ten labelled target flows beat every zero-label method combined.

`results/label_budget.json` · mean over 12 pairs × 3 seeds

| k labelled target flows | re-tune threshold | retrain on source + k |
|---:|---:|---:|
| 0 | 0.3776 | 0.3776 |
| 10 | 0.4909 | **0.7099** |
| 50 | 0.5500 | 0.8727 |
| 100 | 0.5636 | 0.9082 |
| 500 | 0.5662 | 0.9419 |
| 1000 | 0.5623 | 0.9512 |

Zero-label reference points: benign-quantile 0.4162, CORAL 0.3805.

Ten labelled flows lift external macro-F1 by **+0.332**; one hundred reach 0.9082 against
an in-domain ceiling of ~0.98. Re-thresholding on the same labels plateaus near 0.566,
because no threshold repairs an inverted ranking.

**The operational recommendation is concrete:** unsupervised domain adaptation is not
worth the effort in this setting; labelling a few dozen flows from the target network is.

## F8 — The finding replicates in the conventional feature space, but the *failure mode* depends on which datasets you pick.

`results/cic_pair.json` · CIC-DDoS2019 ↔ CICIDS2017, 76 shared CICFlowMeter features,
4 models × 5 seeds, both directions

The gap replicates: in-domain 0.9675–0.9995, external 0.3368–0.4986, mean LightGBM paired
gap **0.5848**, significant in **10/10** pair-seeds. So neither the size of the gap nor the
inversion is an artefact of choosing the NetFlow v2 feature set.

The decomposition, however, comes out differently:

| pair | model | ext AUC | ranking loss | threshold loss |
|---|---|---:|---:|---:|
| ids2017→ddos2019 | RandomForest | **0.9348** | +0.0651 | **+0.5643** |
| ids2017→ddos2019 | XGBoost | 0.8693 | +0.1306 | +0.5232 |
| ids2017→ddos2019 | LightGBM | 0.7594 | +0.2406 | +0.4180 |
| ddos2019→ids2017 | XGBoost | 0.7875 | +0.2125 | +0.2506 |

Where the NetFlow quartet is ranking-dominated in 11 of 12 pairs, the CIC pairing is
**threshold-dominated in most configurations**, and RandomForest retains ROC-AUC 0.9348
across it.

This is a substantive point about the literature rather than a detail. CIC-DDoS2019 and
CICIDS2017 come from the same institution, testbed lineage and extractor. Ranking largely
survives that move and the failure is an operating-point failure — which is recoverable,
and which is exactly the optimistic conclusion some prior work draws. Moving between
*independently built* testbeds destroys the ranking instead, and no threshold can repair
it.

**The choice of dataset pair determines which failure mode you observe, and therefore
which remedy appears to work.** Studies that evaluate transfer only within one
institution's dataset family will systematically overstate how recoverable the problem is.

## F9 — Correcting label errors makes transfer look *worse*, not better.

`results/label_noise.json` · identical CIC-DDoS2019 source model applied to the original
CICIDS2017 and to the DistriNet-corrected release (Engelen et al., 2021)

| model | original labels | corrected labels | Δ macro-F1 | Δ AUC |
|---|---:|---:|---:|---:|
| LightGBM | 0.4827 | 0.3375 | **−0.1453** | −0.0566 |
| XGBoost | 0.4986 | 0.3391 | −0.1595 | −0.0246 |
| RandomForest | 0.4824 | 0.3381 | −0.1443 | −0.0798 |
| LogisticRegression | 0.4543 | 0.3287 | −0.1256 | −0.2252 |

Mean **|Δ| = 0.1437**, consistent in sign and magnitude across all four model families.

Label error was not masking good transfer — it was manufacturing the appearance of it.
Roughly a quarter of the external macro-F1 reported against the original CICIDS2017
labels does not survive correction. Any cross-dataset result using uncorrected CICIDS2017
as a target is optimistic by about this margin.

---

## Still open

- Full-data confirmation run for the headline pair (currently 50k/class cap)
- Per-attack-family transfer table (data collected in `transfer_matrix.json`, not yet
  summarised into its own table)
- Manuscript assembly and a final number-consistency pass
