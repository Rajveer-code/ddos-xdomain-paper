# 4–7. Results

*(Draft. Every figure reference resolves to `figures/`; every number to `results/`.)*

---

## 4. The gap, and its sign

### 4.1 In-domain, the problem looks solved

On its own held-out split every source reaches what this literature routinely reports.
LightGBM averages **0.9817** macro-F1 across the four sources (min 0.9546, max 1.0000),
with ROC-AUC between 0.9977 and 1.0000. The three other model families agree to within a
few points, and seed-to-seed standard deviations are at most 0.0023. Nothing in these
numbers suggests an unsolved problem.

### 4.2 Out-of-domain, it is not solved — and not merely degraded

Applying the identical fitted model to another testbed, across all 12 ordered pairs and
5 seeds, LightGBM averages **0.3788** external macro-F1 (min 0.1935, max 0.5957). The
mean paired gap is **0.6029**, and the paired bootstrap rejects a zero gap in **60 of 60**
pair-seeds at p < 0.05 (Figure 1).

The more informative statistic is the external ROC-AUC. It averages **0.5054** — chance.
A mean at chance could describe a detector that has merely lost its signal. That is not
what happened:

- **108 of 240** external runs (all models, all seeds) score **below 0.5**;
- **149 of 240** have **negative MCC**;
- `NF-UNSW-NB15 → NF-CSE-CIC-IDS2018` reaches ROC-AUC **0.0697**.

An AUC of 0.07 is not weak evidence. It is strong evidence with the wrong sign: the
detector ranks attack flows *below* benign flows with high consistency, and inverting its
output would yield 0.93. Figure 2 shows the full matrix; the entire NF-UNSW-NB15 source
row is inverted against every target.

This is the paper's first claim. **Cross-network failure in flow-based DDoS detection is
not the loss of a learned relationship but the reversal of one.** A detector that has
learned nothing sits at 0.5 and raises alarms at random. A detector at 0.07 has learned
something real about its training network and applies it, confidently, backwards.

The mechanism is not mysterious once stated: if high throughput marks attack traffic in
one testbed and marks the busiest legitimate hosts in another, a decision surface fitted
to the first is close to optimal-but-negated on the second.

## 5. Which failure is it — representation, or operating point?

A collapsed macro-F1 admits two very different explanations, with very different fixes.
The model may no longer separate the classes at all (a **ranking** failure, requiring
retraining), or it may separate them perfectly well while the threshold chosen in-domain
has become meaningless (a **threshold** failure, requiring only recalibration).

We separate them per pair (Figure 3): ranking loss as the drop in ROC-AUC, threshold loss
as external macro-F1 at the target-optimal threshold minus at the source threshold.

**Eleven of twelve pairs are ranking-dominated.** The lone exception is
`NF-BoT-IoT → NF-CSE-CIC-IDS2018`, which retains ROC-AUC **0.9656** — a ranking that
transferred nearly intact — while losing **0.4217** macro-F1 to a stale operating point.

The optimistic reading available in the literature, that cross-domain collapse is largely
a calibration artefact and recalibration will recover it, is therefore true here for
exactly one pair in twelve. Section 8 measures what that is worth.

## 6. Which features cause it? A pre-registered hypothesis, refuted

### 6.1 The hypothesis

Flow features divide naturally into those describing *how much traffic moved and how fast*
— throughput, duration, byte and packet volumes — and those describing *what the endpoints
did* — protocol, TCP flags, TTLs, retransmissions. The first group's values are set partly
by the capturing testbed's link capacity, host count and generator configuration. The
natural hypothesis, and the one this study was designed around, is that these
**capacity features** inflate in-domain accuracy while carrying testbed identity rather
than attack semantics, and that removing them should recover external performance.

We assigned all 39 features to one of five semantic classes (20 capacity, 18 semantic,
1 held out) and trained under 17 feature sets: the full set, each class dropped, each
class alone, and the capacity/semantic partitions.

### 6.2 The hypothesis is false

| feature set | k | in-domain | external | Δ external vs `all` |
|---|---:|---:|---:|---:|
| `semantic_only` | 18 | 0.9690 | 0.3896 | +0.0148 |
| `no_capacity` | 19 | 0.9683 | 0.3881 | +0.0132 |
| **`all`** | **39** | **0.9821** | **0.3748** | — |
| `drop_rate_throughput` | 35 | 0.9818 | 0.3739 | −0.0010 |
| `capacity_only` | 20 | 0.9735 | 0.3738 | −0.0011 |

Removing every capacity feature buys **0.013** macro-F1 externally. Removing only the
throughput features changes nothing. Capacity features *alone* transfer as well as the
complete set. Whatever drives the inversion, it is not localised in this semantic
partition, and we report the hypothesis as refuted.

### 6.3 What the data shows instead: a size effect

Ordering the same 17 sets by external performance puts the **smallest** sets on top
(Figure 4):

| feature set | k | in-domain | external macro-F1 | external AUC |
|---|---:|---:|---:|---:|
| `only_identifier` | **1** | 0.6711 | **0.6512** | **0.7327** |
| `only_duration_timing` | 3 | 0.7474 | 0.5407 | 0.5983 |
| `only_rate_throughput` | 4 | 0.9593 | 0.4688 | 0.6248 |
| `only_flags_behaviour` | 7 | 0.8380 | 0.4288 | 0.3759 |
| `all` | 39 | 0.9821 | 0.3748 | 0.4931 |

A single feature out-generalises the entire standard set by **+0.276** macro-F1 and
**+0.240** AUC. The 38 features added on top of it purchase **+0.311 in-domain** at a cost
of **−0.276 external**.

The interpretation we favour is that a gradient-boosted ensemble given 39 correlated flow
statistics will find high-order conjunctions that separate that testbed's attack traffic
essentially perfectly — and those conjunctions encode the testbed. Restricted to one or
three features, the model cannot express them, fits a coarser and more transferable rule,
and pays for it only at home.

### 6.4 A necessary correction: the held-out feature is not a null control

`DNS_QUERY_ID` was placed in its own class as a null control, on the assumption that a
16-bit DNS transaction ID is random and any accuracy from it would be memorisation by
construction. That assumption is wrong, and we state it plainly because the single most
quotable number in this section depends on it.

| dataset | P(attack \| id = 0) | P(attack \| id ≠ 0) |
|---|---:|---:|
| NF-CSE-CIC-IDS2018 | 0.741 | 0.000 |
| NF-BoT-IoT | 0.785 | 0.000 |
| NF-UNSW-NB15 | 0.051 | 0.001 |
| NF-ToN-IoT | 0.528 | 0.427 |

The field is zero for every non-DNS flow. It is therefore a one-bit *"this flow is DNS"*
indicator, and in three of four datasets DNS traffic is essentially never attack-labelled.
The ID value itself carries nothing: AUC computed on the raw value equals AUC on the
zero/nonzero bit to four decimal places in all four datasets, and conditioning on nonzero
leaves AUC at 0.48–0.49, i.e. chance.

The correct statement of the result is therefore: **one crude protocol bit out-generalises
the 39-feature standard set.** That is a sharper claim than the one we set out to test,
and it does not depend on any feature being noise.

## 7. Can an operator predict the loss without labels?

An operator deploying a detector on their own network has traffic but no attack labels.
We ask whether any label-free quantity predicts how much performance will be lost,
evaluated **leave-one-pair-out** — all seeds of a held-out pair excluded together — against
the baseline of predicting the mean gap (LOPO MAE 0.0827). A predictor that cannot beat
"assume the average drop" is not useful however strong its in-sample correlation.

| predictor | needs | Spearman vs gap | 95% CI | LOPO MAE | vs baseline |
|---|---|---:|---|---:|---:|
| ATC estimated accuracy | model outputs | **−0.726** | [−0.836, −0.532] | **0.0629** | **−24%** |
| mean confidence drop | model outputs | +0.503 | [+0.168, +0.738] | 0.0671 | −19% |
| max per-feature Wasserstein | features | +0.433 | [+0.103, +0.720] | 0.0678 | −18% |
| summed Wasserstein | features | +0.149 | [−0.197, +0.491] | 0.0930 | +12% |
| proxy A-distance | features | −0.119 | [−0.442, +0.242] | 0.0849 | +3% |
| RBF-MMD | features | +0.031 | [−0.306, +0.385] | 0.0910 | +10% |

The result splits cleanly by what the measure looks at (Figure 5).

**Measures of distance between feature distributions fail.** Proxy A-distance, RBF-MMD
and summed Wasserstein all have confidence intervals spanning zero, and all three are
*worse than the mean baseline* out-of-sample. This is worth stating directly because
these quantities — proxy A-distance in particular — are the theoretical motivation behind
a large body of domain-adaptation work. In this setting, how far apart two flow-feature
distributions sit carries almost no information about how much a detector will lose.

**Measures of the model's own behaviour work, moderately.** Average Thresholded Confidence
(Garg et al., 2022) reaches ρ = −0.726 against the gap and +0.756 against external
macro-F1, reducing leave-one-pair-out error by 24%.

We do not oversell this. Twelve ordered pairs is a small sample, and a 24% error reduction
supports triage — deciding which deployments need labelled validation first — not a
guarantee.

---

## 8. Remedies and their limits

### 8.1 Calibration collapses by two orders of magnitude

Mean expected calibration error is **0.0043 in-domain and 0.4372 externally**. The
detectors do not become hesitant on an unfamiliar network; they stay confident and become
wrong, which is the worse of the two failures for an operator setting an alert threshold.

### 8.2 Zero-label recalibration fixes the diagnosable minority, and harms others

A threshold read off the target's benign-traffic quantiles requires no attack labels. Its
recovery, as a fraction of the headroom between the deployed threshold and the all-labels
oracle, tracks external AUC almost exactly (Figure 6):

| pair | ext AUC | source thr | benign-quantile | oracle | headroom recovered |
|---|---:|---:|---:|---:|---:|
| BoT-IoT→IDS2018 | 0.967 | 0.5399 | **0.9558** | 0.9688 | **97.0%** |
| IDS2018→UNSW | 0.792 | 0.4918 | 0.5268 | 0.6280 | 25.7% |
| BoT-IoT→UNSW | 0.829 | 0.4820 | 0.5138 | 0.6386 | 20.3% |
| IDS2018→ToN-IoT | 0.535 | 0.3690 | 0.3474 | 0.5890 | −9.8% |
| BoT-IoT→ToN-IoT | 0.583 | 0.3773 | 0.3465 | 0.6421 | −11.7% |
| ToN-IoT→BoT-IoT | 0.642 | 0.3469 | 0.2480 | 0.7220 | **−26.4%** |

It closes 97% of the one ranking-preserving pair and is **actively harmful on three**.
CORAL, the standard zero-label covariance alignment, recovers **0.0029** macro-F1 averaged
over all pairs — indistinguishable from doing nothing.

### 8.3 Ten labelled flows beat every zero-label method

| k labelled target flows | re-tune threshold | retrain on source + k |
|---:|---:|---:|
| 0 | 0.3776 | 0.3776 |
| **10** | 0.4909 | **0.7099** |
| 50 | 0.5500 | 0.8727 |
| 100 | 0.5636 | 0.9082 |
| 1000 | 0.5623 | 0.9512 |

Ten labelled target flows lift mean external macro-F1 by **+0.332**; one hundred reach
0.9082 against an in-domain ceiling near 0.98 (Figure 7). Re-tuning the threshold on the
same labels plateaus at 0.566, because no threshold repairs an inverted ranking.

The operational conclusion is blunt: in this setting unsupervised domain adaptation is not
worth the effort, and labelling a few dozen flows from the target network is.

## 8.4 Which attacks stop being detected

Per-family recall under transfer (LightGBM, averaged over all pairs and seeds):

| attack family | in-domain recall | external recall | drop |
|---|---:|---:|---:|
| volumetric | 0.9834 | **0.0535** | 0.9299 |
| low-rate application-layer | 1.0000 | 0.2358 | 0.7642 |
| benign (false-positive rate) | 0.0118 | 0.0753 | +0.0634 |

Volumetric floods — the largest, most conspicuous attacks, and the class a detector is
least expected to miss — transfer **worst**, retaining 5.4% recall. This follows directly
from §4: a flood is defined by rates being high, and "high" is a property of the capturing
testbed. Low-rate application-layer attacks, defined by request patterns rather than
volume, survive four times better.

## 8.5 The conclusion replicates, but the failure mode is dataset-dependent

Repeating the study on the conventional CIC-DDoS2019 ↔ CICIDS2017 pairing over 76 shared
CICFlowMeter features reproduces the gap: in-domain 0.9675–0.9995, external 0.3368–0.4986,
mean paired gap **0.5848**, significant in 10/10 pair-seeds. Neither the gap nor its size
depends on the NetFlow v2 choice.

The decomposition does differ. Where the NetFlow quartet is ranking-dominated in 11 of 12
pairs, the CIC pairing is **threshold-dominated** in most configurations, and RandomForest
retains ROC-AUC **0.9348** across it.

CIC-DDoS2019 and CICIDS2017 share an institution, a testbed lineage and an extractor.
Ranking largely survives that move, leaving an operating-point failure that recalibration
can address. Moving between independently constructed testbeds destroys the ranking
instead. **The dataset pair chosen therefore determines which failure mode is observed,
and hence which remedy appears to work** — a study confined to one institution's dataset
family will systematically overstate how recoverable the problem is.

### 8.6 Correcting label errors makes transfer look worse

Applying one identical source model to the original CICIDS2017 and to the
DistriNet-corrected release (Engelen et al., 2021):

| model | original | corrected | Δ macro-F1 |
|---|---:|---:|---:|
| LightGBM | 0.4827 | 0.3375 | −0.1453 |
| XGBoost | 0.4986 | 0.3391 | −0.1595 |
| RandomForest | 0.4824 | 0.3381 | −0.1443 |
| LogisticRegression | 0.4543 | 0.3287 | −0.1256 |

Mean |Δ| = **0.1437**, consistent across all four model families. Label error was not
concealing good transfer; it was manufacturing the appearance of it. Roughly a quarter of
the external macro-F1 measured against the original labels does not survive correction,
so any cross-dataset result using uncorrected CICIDS2017 as a target is optimistic by
about this margin.
