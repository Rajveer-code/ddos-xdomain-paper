# Hiding in the Shift: Adversarial High-Confidence False Negatives against Label-Free NIDS Monitoring under Cross-Testbed Transfer

**Rajveer Singh Pall** (sole author). Draft — full frozen-spec run, 2026-10-22.

> **Scale note (read first).** Every number below is from the **full frozen specification**
> (`research-opportunities/p1/PREREGISTRATION.md`): 5 seeds (42–46), a 200k-per-class source cap,
> 50k target benign flows, 2,000 target attack flows per family, a 200-query score-only budget,
> two source→target pairs, two models. Claims are still sized to one dataset family (NetFlow v2)
> and the two tested pairs — "suggests", not "demonstrates"; the feature-space scope and the
> optional wire-realism check (Phase 1-R, not run) are the remaining limits. Every headline number
> is keyed to `results/p1/summary_p1.json` and checked by `check_numbers_p1.py` (23/23).

## Abstract

Flow-based DoS detectors that score ~99% in-domain collapse on independently captured
networks (P11, this repository). Operators are told to watch for this with *label-free*
monitors — Average Thresholded Confidence (ATC), confidence drift, distribution distances —
that need no target labels. We ask whether these monitors see a detector that has already
failed, and whether an adversary constrained to traffic-plausible changes can make matters worse
in the region the monitors trust.

Four findings, on NetFlow v2 (UNSW-NB15, BoT-IoT → CSE-CIC-IDS2018), reported honestly with a
baseline that is apples-to-apples with the attack. (1) **Latent exposure is already large and
model-dependent:** before any attack, the cross-testbed detector classifies **31.9–99.9%** of
real target DoS flows as benign *at high confidence* (latent high-confidence-miss rate
0.984/0.953/0.319/0.999 for unsw/LightGBM, unsw/LogReg, bot/LightGBM, bot/LogReg). The detector
is, by default, wide open at exactly the operating point the monitors protect. (2) **A
constrained, score-only adversary adds capability only where there is headroom.** Isolated from
the feasibility-projection step (baseline = the projected real flow with no search), the search's
own contribution is **+0.001 to +0.607** (bot/LightGBM +0.607, unsw/LogReg +0.251, unsw/LightGBM
+0.232, bot/LogReg +0.001); the searched high-confidence-miss rate converges to ~0.90, which is
the feasibility ceiling, not a measure of search power. For the already-saturated bot/LogReg cell
the search earns essentially nothing. (3) **The monitors are model-dependently blind, and
blindest where the detector is already worst.** For LightGBM the confidence monitors fire (they
fire on benign shift too); for LogisticRegression on the strong-transfer pair they stay
**completely silent** (alarm 0.0, attack or no attack) while 99.9% of real target DoS flows are
high-confidence misses — the quiet-monitor failure, on the cell where the adversary is irrelevant
because the detector is already defenceless. (4) **The obvious responder-side defence does not
transfer:** watching the low-controllability features cuts HCMR by ≤ 0.072 against a
pre-registered 0.10 bar, because across independent testbeds those features do not transfer
either, so a source-fitted monitor on them is blind. We report this negative as a result.

The headline is therefore not "a powerful adversary defeats the monitor" but the sharper and more
uncomfortable "the monitored detector is already defeated, the adversary merely widens the hole
where it can, and the recommended fix does not survive the move between networks."

## 1. Introduction

P11 established that cross-network flow DoS detection does not merely degrade — it inverts, and
the failure is representational, not a stale threshold, for most pairs. The field's answer to
"you cannot label the new network" is label-free monitoring: estimate accuracy or detect shift
from unlabeled target traffic. Bikdeli et al. (*The Dashboard Says "Perfect"*, Frontiers in AI
2026) showed these monitors fail under a *benign* one-year temporal drift. We take the
adversarial step they did not: an attacker who *steers* flows into the region the monitors
trust, under stated traffic-plausibility constraints, across independently built testbeds — and
a defence that is tested, not assumed.

## 2. Related work and the gap

Seven works bound the contribution (full table and the novelty gate in PREREGISTRATION §2):
Bikdeli (benign-shift audit of label-free monitors — closest; we add the adversary);
Gnanaratna/Kingston (SecureComm 2026, hardens a deferral IDS against a *training-time* proxy —
the monitor is improved, not probed); PANTS (USENIX Sec 2025, realizable attacks + adversarial
training, classifier-only, no confidence monitor); PAVE (feature-space attacks are 0–3% valid
on the wire — the realism threat our constraint model answers); Apruzzese (DTRAP 2022) and
Merzouk (Annals of Telecom. 2022, the four validity criteria we adopt); the evasion-practicality
SoK (elShehaby & Matrawy — our honesty anchor); and ATC (Garg et al., ICLR 2022, the monitor we
probe). **Gate 0 (novelty) passes:** none measures adversarial high-confidence false negatives
against the detector+label-free-monitor system under cross-testbed shift with a constraint model
and a tested defence.

## 3. Threat model and constraints

Grey-box, **score-only** (realistic): the adversary knows the public NetFlow v2 schema and can
query the deployed model's score, no gradients, ≤200 queries per flow. The 39 shared features
are partitioned by mechanism into **directly controllable** (16; source-side sizes, counts,
timing, client flags), **indirectly influenced** (13; responder-side bytes/packets, server
flags, retransmissions, windows), and **uncontrollable** (10; protocol, TTL, DNS/ICMP fields),
frozen at the original flow. Feasibility follows Merzouk's four criteria made concrete: a
per-family [p1, p99] box from real source attack flows; immutability of frozen features; integer
counts and valid flag bytes; and dependency relations (mean packet length within [MIN,MAX],
bytes ≥ 20·packets, size-bin sum ≤ total packets, retransmissions ≤ totals). `project` repairs a
candidate into this set; `functional` keeps the rate/volume features attack-like so an evaded
flow is still a working DoS. Full specification: `constraints.py`, PREREGISTRATION §3.

A flow is a **high-confidence miss (HCM)** iff, after the source-fitted scaler and threshold are
applied on the target: it is predicted benign, its confidence max(p,1−p) ≥ τ_accept (set on
source-validation benign at a 1% review budget), and it is feasible and functional. HCMR is the
fraction of target attack flows the search can turn into an HCM within budget.

## 4. Feature controllability (Phase 1)

For each indirectly-influenced feature we fit a 5-fold cross-validated predictor from the
directly-controllable features on real flows (`run_phase1.py`). Most responder features are
**highly predictable** from the attacker's direct choices (R² ≥ 0.5): the attacker effectively
sets them. Only `DST_TO_SRC_SECOND_BYTES` (UNSW) and additionally `RETRANSMITTED_OUT_BYTES`,
`RETRANSMITTED_OUT_PKTS` (BoT-IoT) have low controllability. Gate 1 passes (a defence has
*something* to watch), but narrowly — a finding in itself: the responder-side features offer
thin defensive material.

## 5. Latent exposure, and what the search actually adds (Phase 3)

We measure three apples-to-apples quantities on the real target DoS flows (`compute_lift.py`,
keyed in `summary_p1.json`). A **naming caution that an audit of our own first draft forced**:
feasibility is an *attacker* constraint, not a validity test for real wire-captured traffic, so
the latent baseline must be computed on the real flows **without** the source-box filter;
measuring the "natural" rate through that filter understated it by ~50–140× and manufactured a
spurious lift. We correct that here.

1. **Latent high-confidence-miss rate** (real flows, no attacker constraint): the fraction already
   predicted benign at confidence ≥ τ_accept. It is **0.984 / 0.953 / 0.319 / 0.999** for
   unsw/LightGBM, unsw/LogReg, bot/LightGBM, bot/LogReg. A third to essentially all real target DoS
   flows are already high-confidence misses before any adversary acts.
2. **Projected floor** (project the real flow into the source feasible box, no search): 0.679 /
   0.658 / 0.282 / 0.901. This is what merely producing a feasible flow achieves.
3. **Searched HCMR** (full score-only search): 0.910 / 0.909 / 0.889 / 0.902 — it converges to the
   ~0.90 feasibility ceiling (`feasible_rate` ≈ `hcmr` in every cell), so this number reflects the
   constraint geometry, not search strength.

The **search's own contribution** is searched − projected = **+0.232 / +0.251 / +0.607 / +0.001**.
So the adaptive search genuinely buys high-confidence misses where the detector still has
headroom (bot/LightGBM +0.607, unsw/LogReg +0.251, unsw/LightGBM +0.232), and buys **essentially
nothing** on bot/LogReg (+0.001), where the detector already assigns high-confidence-benign to the
entire feasible region (latent 0.999). The push on P(attack) is small throughout (mean drop
0.003–0.048) and the strong upper-bound search adds ≤ 0.01 over the score-only search: the flows
sit a thin margin from the confidence threshold, so where the search helps, a feasible nudge is
enough. We do **not** claim a large adversarial lift; the dominant effect is the latent exposure,
and the adversary's role is to widen it where it can.

## 6. The monitors are model-dependently blind (Phases 2–3)

Under natural transfer the **distribution** monitors (KS, proxy A-distance, max Wasserstein) fire
in ~100% of configs and the **model-based** monitors (ATC, confidence drop) in ~75%
(`summary_p1.json` → `baseline`). Their alarm tracks the *natural* shift, not the attack: the
adversarial deployment's alarms ≈ the natural deployment's.

So where natural shift already lights the model-based monitors — LightGBM, both pairs
(`model_monitor_alarm_adversarial` = 1.0) — they would fire anyway; ATC is a usable alarm there
(a contrast with Bikdeli's benign-shift finding). But on **BoT-IoT → CSE-CIC-IDS2018 with
LogisticRegression**, both model-based monitors stay **silent** (natural and adversarial alarm
0.0) while the adversary reaches **HCMR 0.901**. That is the quiet-monitor failure in the clear:
a strong-ranking detector (external AUC 0.919), a label-free confidence monitor reporting normal,
and ~90% of target DoS flows waved through at high confidence. The distribution monitors fire on
everything, so they do not distinguish the attack from benign drift — they are not a specific
alarm.

The uncomfortable alignment: the cell where the confidence monitors are silent (bot/LogReg) is
exactly the cell where the latent high-confidence-miss rate is already 0.999 and the adversarial
search adds essentially nothing (+0.001, §5). Where the adversary contributes most (the LightGBM
cells, search lift +0.232 and +0.607) the confidence monitors do fire. So the monitors are
blindest precisely where the detector is already fully compromised and the adversary is redundant
— the worst possible pairing for an operator who is relying on them.

## 7. The obvious defence does not transfer (Phase 4)

A one-class novelty detector (IsolationForest) on the low-controllability features, fitted on
source benign and thresholded at the 1% budget, is the obvious responder-side defence: the
adversary froze those features at the original attack values, so a successful miss still carries
the attack's responder signature. It **fails** the pre-registered bar everywhere: ΔHCMR = 0.072
(UNSW) and 0.012 (BoT-IoT) against a 0.10 bar, catching ≤ 8% of misses at ≤ 1.0% benign cost
(`summary_p1.json` → `defense_*`, `gate4`). The reason is P11's reason: across independently
built testbeds the low-controllability features themselves do not transfer, so a source-fitted
monitor on them cannot tell an adversarial target flow from benign target traffic. We report the
negative as the result.

## 8. Limitations

Full frozen spec (5 seeds, 200k/50k caps); one dataset family (NetFlow v2); two pairs, two models;
feature-space only — no wire-realizability is claimed (the optional Phase 1-R check was not run).
Both sources carry a single DoS family (volumetric), so the per-family box is one family's. The
monitor thresholds are calibrated by two-half source-validation resampling; the defence is
fitted and calibrated on disjoint halves of source-validation benign. External AUCs here differ
from P11's (smaller cap, volumetric-only target), and are reported as pilot context, not as P11's
numbers. The finding is a measurement for the tested system, not a general claim about all NIDS.

## 9. What this establishes (honest summary)

The dominant effect is not the adversary: cross-testbed DoS detectors are **already** high-confidence
wrong on 33–100% of real target DoS flows, at the operating point the label-free monitors are
supposed to protect, and the monitors are model-dependently blind to it. A constrained,
score-only adversary **widens** this hole where the detector still has headroom (search lift up to
+0.59) and is redundant where it does not (bot/LogReg, +0.00). The obvious responder-side patch —
watch the features the adversary cannot freely set — does not survive the move between networks,
because those features do not transfer either. This extends P11 from "the detector is wrong" to
"the detector is confidently wrong, unwatched, and not fixable by the obvious monitor", and
answers the evasion-practicality SoK on its own terms: in the monitored cross-testbed setting, the
practical danger is not a clever adversary but a detector that is a thin margin from waving
everything through and a safety net calibrated on the wrong network.
