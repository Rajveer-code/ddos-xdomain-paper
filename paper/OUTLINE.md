# Manuscript outline — argument spine

**Working title:** *Confidently Wrong: Cross-Network DDoS Detectors Invert Rather Than
Degrade, and What Actually Predicts It*

Target: Computers & Security (Elsevier, no APC under the subscription model).
Secondary: WTMC 2027, USENIX CSET 2027.

Every number cited below lives in `results/` and is reproduced in [FINDINGS.md](../FINDINGS.md).

---

## The one-sentence claim

A flow-based DDoS detector moved to a different network does not become uncertain — it
becomes **confidently inverted**, and the standard remedies (feature engineering,
distribution-divergence monitoring, recalibration) fail on all but a narrow, identifiable
subset of cases.

## The spine, in order

Each section exists to advance the argument. If a result does not move the reader from
one step to the next, it goes to the appendix.

1. **Detectors look solved in-domain.** 0.9817 mean macro-F1, AUC to 1.0000. So does
   every paper in this area.
2. **They are not.** Mean external macro-F1 0.3788, mean external AUC 0.5054 — chance.
   Gap 0.6029, significant in 60/60 pair-seeds.
3. **The failure is not noise, it is inversion.** 108/240 runs below chance AUC.
   `UNSW→IDS2018` at 0.0697. The learned relationship reverses sign across networks.
4. **So which features cause it?** The obvious hypothesis — that testbed-capacity
   features are to blame — is testable, was pre-registered, and is **false**. Removing
   all 20 capacity features buys 0.013 macro-F1.
5. **It is the number of features, not their kind.** One protocol bit reaches external
   0.6512; all 39 features reach 0.3748. The extra 38 buy +0.311 in-domain and cost
   −0.276 external.
6. **Can an operator see it coming?** Distribution divergence — the basis of most domain
   adaptation work — cannot: proxy A-distance, MMD and summed Wasserstein all have CIs
   spanning zero and lose to a mean baseline. The model's own confidence can: ATC at
   ρ = −0.726, cutting LOPO error 24%.
7. **What actually fixes it?** Only the ranking-preserving minority. Benign-quantile
   recalibration takes `BoT-IoT→IDS2018` from 0.4736 to 0.9685 against a 0.9702 oracle,
   with zero target labels — and does nothing for the other eleven pairs. `[PENDING:
   full-run numbers + label-budget curve]`
8. **And none of this is visible unless the data is cleaned first.** Duplicate rates to
   99.7% mean the in-domain figures this field reports are partly tests on training rows.

## Section plan

| § | Content | Figures/Tables | Status |
|---|---|---|---|
| 1 | Introduction — the claim, the three surprises | — | to draft |
| 2 | Related work — Cantone 2024, D'hooge 2020, Sarhan 2021, Engelen 2021, Arp 2022, Garg 2022 | — | to draft |
| 3 | Data and protocol | T1 datasets, T2 pitfalls | **stable, draftable now** |
| 4 | The gap and its sign | F1 gap, F2 AUC matrix | numbers final |
| 5 | Decomposition: ranking vs threshold | F3 | numbers final |
| 6 | Which features? (the refuted hypothesis) | F4 | numbers final |
| 7 | Predicting the loss without labels | F5 | numbers final |
| 8 | Remedies and their limits | F6, F7 | `[PENDING run]` |
| 9 | Threats to validity | — | to draft |
| 10 | Conclusion | — | to draft |

## Non-negotiables for this manuscript

- The refuted hypothesis (§6) is reported as refuted, in the main body, not buried.
- No metric appears that is not in `results/`.
- Base rates differ 1.3%–77.4% across datasets, so every cross-dataset comparison is
  made at a stated operating point, never on raw balanced F1 alone.
- `DNS_QUERY_ID` is described as a one-bit DNS indicator, never as a random identifier.
- Duplicate handling is stated before any in-domain number is quoted.
