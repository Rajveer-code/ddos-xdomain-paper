# 1. Introduction

Published flow-based DDoS detectors report accuracies above 99%. Deployed ones do not
behave that way, and the gap between those two facts has been documented repeatedly:
models trained on one intrusion-detection dataset and tested on another lose most of
their apparent skill (D'hooge et al., 2020; Cantone et al., 2024). That finding is by now
established. What it *means* is not.

The default reading is a quantitative one — the model is somewhat overfitted to its
training network, and performance degrades. Under that reading the remedies are the
familiar ones: engineer features that describe the attack rather than the capture,
monitor the distance between training and deployment distributions, and recalibrate the
decision threshold on arrival. This paper tests all three, and finds the reading wrong in
a way that matters.

Running every ordered pair among four independently captured testbeds, on a published
common feature set, with de-duplication and source-only preprocessing, we find that
cross-network transfer does not degrade toward chance. It passes through chance. Mean
external ROC-AUC is 0.5054; **108 of 240** external runs score *below* 0.5, and one pair
reaches **0.0697** — a detector that ranks attack flows below benign flows almost
perfectly, and whose output would be 93% accurate if negated. A model at chance has lost
its signal. A model at 0.07 has kept it and reversed it.

That reframing changes what the remedies must do, and we find each of them narrower than
advertised:

**Feature engineering does not help, and the obvious hypothesis is false.** We
pre-registered the expectation that capacity-bound features — throughput, duration,
volume — carry testbed identity and cause the collapse. Removing all twenty of them
recovers 0.013 macro-F1. Capacity features alone transfer as well as the full set. We
report the hypothesis as refuted. What the data shows instead is a size effect: a
*single* protocol bit reaches external macro-F1 0.6512 where all 39 features reach
0.3748. The 38 additional features buy 0.311 in-domain and cost 0.276 externally.

**Distribution-divergence monitoring does not work.** Proxy A-distance, RBF-MMD and
summed Wasserstein distance — the quantities that motivate much of the domain-adaptation
literature — all have correlations whose confidence intervals span zero, and all three
predict the observed gap *worse* than simply assuming the average drop. What does carry
signal is the model's own confidence: Average Thresholded Confidence reaches ρ = −0.726
and cuts leave-one-pair-out error by 24%.

**Recalibration works, for one pair in twelve.** Decomposing each failure into ranking
loss and threshold loss shows eleven of twelve pairs fail representationally. For the
single ranking-preserving pair, a threshold taken from target benign-traffic quantiles —
requiring no attack labels — recovers macro-F1 from 0.4736 to 0.9685 against an oracle of
0.9702. For the rest it does nothing.

A fourth finding conditions all of the above. In the feature space a model actually sees,
these datasets are **up to 99.7% exact duplicates** (NF-BoT-IoT: 30,420,086 rows reduce to
101,369). Studies that split them without de-duplicating are testing, in part, on rows
they trained on.

### Contributions

1. Evidence that cross-network failure in flow-based DDoS detection is **sign inversion**
   rather than degradation, over 240 external evaluations with paired-bootstrap intervals
   on the gap itself.
2. A refuted pre-registered hypothesis about capacity features, and the size effect the
   data supports instead: one protocol bit out-generalises the standard 39-feature set.
3. A negative result on distribution-divergence measures as deployment-risk predictors,
   with a confidence-based alternative that beats a mean baseline.
4. A decomposition separating recoverable threshold failures from representational ones,
   and a zero-label recalibration that closes the recoverable case to within 0.002.
5. Duplicate and label-contradiction accounting that bounds every in-domain figure this
   literature reports.

All code, seeds and result files are released; every number in this paper is regenerated
from `results/*.json` by the scripts that produced them.

---

# 9. Threats to validity

**All four datasets are testbed captures.** None is production traffic. This limits
external validity in the usual way, but it also sharpens the finding rather than
weakening it: if detectors cannot transfer between four carefully constructed research
testbeds, the case for transfer to a live network is not stronger.

**De-duplication is a choice, and a consequential one.** Removing exact duplicates in the
post-socket-drop feature space reduces NF-BoT-IoT by 99.7%. A reader who considers those
rows legitimately independent observations would obtain higher in-domain scores and a
different gap. We report the counts so that either position can be evaluated, and we
consider the alternative untenable: rows a model cannot distinguish cannot be
independent test evidence for that model.

**The stratified cap alters base rates.** Capping at 50,000 rows per class bounds cost but
changes class balance, which moves precision-sensitive metrics. Base rates are reported
throughout and operating-point metrics accompany F1 for this reason.

**Non-DoS attacks are excluded from the primary analysis.** Retaining them would change
the base rate again; the policy is an explicit parameter and the counts moved are
recorded, but the primary numbers describe a DoS/DDoS-versus-benign task.

**Twelve ordered pairs is a small sample for §7.** The leave-one-pair-out evaluation is
the right protocol for the question, but a 24% error reduction estimated from twelve
pairs supports triage, not a service-level guarantee.

**NF-UNSW-NB15 is a weak source.** After de-duplication it retains 3,075 DoS flows at a
1.3% base rate. Its behaviour as a source — the most strongly inverted row in the matrix —
may partly reflect that scarcity rather than domain distance alone.

**Low-rate attacks are underpowered in the NetFlow quartet.** After de-duplication,
NF-CSE-CIC-IDS2018 retains only 203 low-rate application-layer flows, so the per-family
transfer analysis for that family rests on the CICFlowMeter secondary study.

**Label error is a confound we bound but do not eliminate.** CICIDS2017's documented
labelling defects are addressed by rerunning against the DistriNet-corrected release; the
NetFlow quartet has no comparably corrected counterpart, so residual label noise there is
unmeasured.

**The inversion has an interpretation we have not proven.** We argue that a
gradient-boosted ensemble over 39 correlated flow statistics encodes testbed-specific
conjunctions whose sign is arbitrary across networks. The size effect in §6.3 is
consistent with this and the capacity ablation rules out one competing explanation, but we
have not isolated the responsible conjunctions directly.
