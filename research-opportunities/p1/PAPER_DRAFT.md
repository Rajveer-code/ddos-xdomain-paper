# Hiding in the Shift: Adversarial High-Confidence False Negatives against Label-Free NIDS Monitoring under Cross-Testbed Transfer

**Rajveer Singh Pall** (sole author). Preliminary draft — pilot results, 2026-10-22.

> **Scale note (read first).** Every number below is from a **pilot**: 3 seeds (42–44), a
> 50k-per-class source cap, 2,000 target attack flows per family, a 200-query score-only
> budget, two source→target pairs, two models. The frozen full specification
> (`research-opportunities/p1/PREREGISTRATION.md`) is 5 seeds and the larger caps; it is the
> December–February extension. Claims are sized to one dataset family (NetFlow v2) and the
> tested pairs — "suggests", not "demonstrates". Every headline number is keyed to
> `results/p1/summary_p1.json` and checked by `check_numbers_p1.py`.

## Abstract

Flow-based DoS detectors that score ~99% in-domain collapse on independently captured
networks (P11, this repository). Operators are told to watch for this with *label-free*
monitors — Average Thresholded Confidence (ATC), confidence drift, distribution distances —
that need no target labels. We ask whether an adversary, constrained to traffic-plausible
changes it can actually make, can drive malicious flows into the **high-confidence benign**
region where those monitors stay silent, after cross-testbed transfer, and whether watching
the features the adversary cannot freely set restores the warning.

Three findings, on NetFlow v2 (UNSW-NB15, BoT-IoT → CSE-CIC-IDS2018). (1) Natural
cross-testbed misses are **low-confidence**: the detector already calls 96–100% of target DoS
flows benign, but at confidence below the 1%-review operating point, so a confidence monitor's
review region would catch them (natural high-confidence-miss rate 0.3–2.3%). (2) A constrained,
score-only adversary **converts** these into high-confidence misses: HCMR rises to 90.1–90.4%
(adversarial lift +0.88 to +0.90) with only a small push on P(attack) (mean 0.003–0.048),
because the flows sit a thin margin from the confidence threshold. (3) Whether the label-free
monitors catch this is **model-dependent and tracks natural shift, not the attack**: for
LightGBM the confidence monitors fire (they fire on benign shift too), but for
LogisticRegression on the strong-transfer pair they stay **completely silent** while HCMR is
90.1% — the quiet-monitor failure, realised. The obvious responder-side defence (watch the
low-controllability features) does **not** close the gap (ΔHCMR ≤ 0.075 against a pre-registered
0.10 bar), because across independent testbeds those features do not transfer either, so a
source-fitted monitor on them is blind. We report this negative as a result, not a footnote.

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

## 5. The attack buys high confidence, not evasion (Phase 3)

Evasion is nearly free before the attack: natural `pred_benign` on target volumetric flows is
0.957–1.000 (`summary_p1.json` → `per_pair_model.*.natural_pred_benign_rate`). But those misses
are **low-confidence** — natural HCMR is 0.020/0.023 (UNSW, LightGBM/LogReg) and 0.003/0.006
(BoT-IoT) — so a confidence monitor's review region would escalate them.

The constrained score-only search converts them: **HCMR = 0.904 / 0.904 (UNSW) and 0.901 / 0.901
(BoT-IoT)**, adversarial lift **+0.884 / +0.881 / +0.897 / +0.895**, with feasible rate ≈ 0.90,
functional rate ≥ 0.99, and mean confidence of the successful misses ≈ 1.0. The push on P(attack)
is small (mean drop 0.003–0.048): the flows sit a thin margin below the confidence threshold, and
a feasible nudge carries them over. The strong (upper-bound) search adds essentially nothing
(≤ +0.01), confirming the margin, not search power, is what matters.

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
a strong-ranking detector (external AUC 0.757), a label-free confidence monitor reporting normal,
and 90% of target DoS flows waved through at high confidence. The distribution monitors fire on
everything, so they do not distinguish the attack from benign drift — they are not a specific
alarm.

## 7. The obvious defence does not transfer (Phase 4)

A one-class novelty detector (IsolationForest) on the low-controllability features, fitted on
source benign and thresholded at the 1% budget, is the obvious responder-side defence: the
adversary froze those features at the original attack values, so a successful miss still carries
the attack's responder signature. It **fails** the pre-registered bar everywhere: ΔHCMR = 0.075
(UNSW) and 0.006 (BoT-IoT) against a 0.10 bar, catching ≤ 8% of misses at ≤ 0.3% benign cost
(`summary_p1.json` → `defense_*`, `gate4`). The reason is P11's reason: across independently
built testbeds the low-controllability features themselves do not transfer, so a source-fitted
monitor on them cannot tell an adversarial target flow from benign target traffic. We report the
negative as the result.

## 8. Limitations

Pilot scale (3 seeds, capped samples); one dataset family (NetFlow v2); two pairs, two models;
feature-space only — no wire-realizability is claimed (the optional Phase 1-R check was not run).
Both sources carry a single DoS family (volumetric), so the per-family box is one family's. The
monitor thresholds are calibrated by two-half source-validation resampling; the defence is
fitted and calibrated on disjoint halves of source-validation benign. External AUCs here differ
from P11's (smaller cap, volumetric-only target), and are reported as pilot context, not as P11's
numbers. The finding is a measurement for the tested system, not a general claim about all NIDS.

## 9. What this establishes (honest summary)

Under traffic-plausible, score-only constraints, cross-testbed DoS detectors do not just fail —
their label-free safety nets fail *with* them, and the obvious responder-side patch does not
transfer. The adversary's power is not in evading the classifier (that is nearly free) but in
buying **confidence**, moving flows from the monitor's review region into its trust region. This
extends P11 from "the detector is wrong" to "the detector is confidently wrong *and unwatched*",
and answers the evasion-practicality SoK: in the monitored setting, high-confidence evasion is
not impractical — it is a thin margin away by default.
