# FINAL DECISION after both checks (2026-10-23): **NARROW (GO at narrowed scope)**

Both pre-declared checks executed; results folded in honestly. No material correctness problem
remains. Recommendation: proceed with the manuscript at its narrowed scope; do not expand.

**What is genuinely novel (ours):** the *adversarial, cross-testbed, constraint-modelled*
measurement — a constrained attacker deliberately exploiting the known blind spot across the
independent-testbed NetFlow v2 quartet; the model-dependence spectrum (RandomForest resists, LogReg
worst); the honest latent-vs-adversarial decomposition; the negative responder-side defence; and the
honest certification-cost accounting, including the empirical finding that in this setting **no
tested label-free signal — confidence (ATC/drift), distance (A-dist/Wasserstein), or an approximate
conformal-abstention drift alarm — specifically flags the dangerous confident-miss cells** (conformal
caught only 25% of them, and alarmed more on safe than unsafe configs).

**What overlaps with prior work (not ours):** the label-free-monitoring blindness and its
formalisation (Bikdeli et al. 2026, "Dashboard Says Perfect"); the labelled-audit / risk-monitoring
machinery (PPRM 2026; RiskGate-IDS 2026; Podkopaev–Ramdas 2022); conformal abstention as a drift
alarm (Bikdeli). We claim none of these as contributions.

**Claims the evidence supports:** the 240-config adversarial + latent measurement with CIs; the
model-dependence; the Gate-4 defence negative; and the certification-cost accounting — an
attack-reference audit of ~10 labelled attacks *escalates* the unsafe majority, passive sampling is
expensive/infeasible at low base rates (π=0.01: a 100-label budget never reaches 10 attacks), and 10
attacks certify *safe* only at 9/10 caught. The 0.03% is an empirical benchmark frequency, not a
guarantee.

**Untested / limitations:** a faithful (non-approximate) conformal-abstention reproduction;
wire-realizability (feature-space only; cf. PLAA/PAVE); DoS families beyond volumetric; independence
across the correlated 12×4×5 design.

### Safe wording for the SOP (use verbatim or close)

> Building on prior evidence that label-free confidence monitors can misjudge a drifted intrusion
> detector, I asked whether an adversary constrained to traffic-plausible changes could *deliberately*
> exploit that blind spot after a detector moves to an independently built network. Across the
> NetFlow v2 quartet I found that it can — in roughly half of successful evasions the confidence
> monitors stay silent — that the effect is sharply model-dependent, that the obvious responder-side
> defence does not transfer, and that none of the label-free signals I tested specifically flags the
> dangerous cases, so certifying that the detector still catches attacks requires a small labelled
> audit whose cost I quantify. This is the security instance of the question running through my work
> — when does a reported evaluation metric license the decision made from it? — alongside
> cross-network clinical AUC (P9), subgroup-versus-pooled screening (P06b), leaderboard verifiers
> (P14), and cross-network detection failure (P11).

Do **not** write, in the SOP: that you proved a new theorem; that you built a novel monitor or gate;
that a 10-flow audit certifies safety; or that label-free monitoring is universally blind. Those are
either prior work or unsupported.

---

# PRE-DECLARED PROTOCOL for the final two checks (2026-10-23, before running)

Declared before execution so thresholds are not chosen after seeing results. Existing data/code
only; no new models/theorems/defences.

**Check 1 — conformal abstention (faithful-as-possible reproduction of Bikdeli's drift signal).**
Split-conformal nonconformity = 1 − confidence = 1 − max(p, 1−p). Calibrate the conformal threshold
τ at the 1% quantile of source-validation **benign** nonconformity (≈99% conforming benign). Target
abstention rate = fraction of the target deployment below τ. Alarm threshold null-calibrated on
source-validation two-half resampling at the same 1% false-alarm budget as the other monitors (no
target labels, no adversarial metrics used to tune). Run over the full 12×4×5 matrix.
*Success criteria (pre-declared):* conformal abstention is a **useful danger signal** iff its alarm
rate on unsafe configs (true recall < 0.5) is high (≥ 0.8) AND it is more specific than ATC/
confidence-drift (does not simply fire on every transfer). It is **non-specific** if it alarms at a
similar rate on safe and unsafe configs. A drift alarm is never treated as a recall certificate.
Report whichever holds, by model and direction; label faithful-vs-approximate honestly.

**Check 2 — passive-sampling audit.** π ∈ {0.1, 0.01, 0.001}; labelling budgets N ∈ {100, 1000}.
Simulate random target draws (attack w.p. π, caught w.p. config recall). Report: (a) the
negative-binomial distribution of random labels to observe k = 10 attacks; (b) P(< 10 attacks within
budget N); (c) the Clopper-Pearson recall interval and gate verdict given the attacks observed; (d)
whether 10 labelled attacks can *certify safe* (recall ≥ 0.5) at 95% — stated from the CP math, not
assumed. Expected cost (k/π) kept separate from any guarantee. Active (attack-reference) result kept
separate from passive.

---

# VALIDATION ADDENDUM (2026-10-23) — stricter decision after a second review

A second review demanded scientific validation (sampling design, statistical meaning, novelty vs
the closest work) before relying on the gate. Outcome: **NARROW further.** Three corrections, all
now in the manuscript:

1. **The recall-invisibility "theorem" is not novel.** Bikdeli et al. (2026, "Dashboard Says
   Perfect") already report ATC assigning accuracy 1.000 to a zero-recall detector and **formalise
   the inversion in two propositions**. §4.5 now credits them explicitly and claims no novelty for
   the proposition; it is restated only to make the adversarial exploit explicit.
2. **The audit's sampling was attack-enriched.** The pilot draws k labelled *attack* flows — an
   attack-reference (active) audit that assumes the auditor can produce known attacks. Realistic for
   a defender with source attacks, but it certifies recall only against that reference, and passive
   labelling costs ≈ k/π (100–10 000 labels for k = 10 at π = 0.1–0.001). §5.5 now states this; the
   "10 flows" headline is "10 attack labels", not 10 random flows.
3. **0.03% is an empirical benchmark frequency, not a guarantee.** §5.5 now distinguishes it from
   the per-config α-level false-accept control of the Clopper-Pearson test, and notes the correlated
   (pair, model, seed) structure. Bikdeli's conformal-abstention drift alarm (which works) is
   acknowledged as complementary — a drift alarm is not a recall certificate — and flagged untested.

**Surviving, defensible contribution (what is actually ours):** the *adversarial, cross-testbed,
constraint-modelled* measurement — a constrained attacker deliberately exploiting the (known)
blind spot across the independent-testbed quartet; the model-dependence spectrum (RandomForest
resists); the honest latent-vs-adversarial decomposition; the negative defence; and the honest
cost-of-certification accounting. NOT ours: the blindness proposition (Bikdeli), the audit mechanism
(PPRM / RiskGate-IDS / Podkopaev–Ramdas), or any claim that a drift alarm cannot exist. The paper is
honest and SOP-relevant at this scope; it is not a theorem paper and must not be sold as one.

---

# P-1 reframe — strict decision (2026-10-22)

Response to the strategic review proposing a decision-risk / deployment-gate reframe. Per the
review's own instruction, this is the go/narrow/abandon decision **before** any full new build. A
compute-free pilot was run to test viability.

## Recommendation: **GO, NARROWED.**

Keep the cross-testbed intrusion-detection results and the recall-invisibility theorem as the
spine. Add the budgeted-audit deployment gate **only as the forced corollary of the theorem**, not
as a novel monitoring method, and cite the prior art that already owns the mechanism. Do **not**
attempt wire-realism; keep the feature-space scope and narrow the claims. Fix the title overclaim.

## Revised question and title

> When a flow intrusion detector moves to an unfamiliar network, which evidence can and cannot
> certify that its operating-point risk (attack recall at the deployed threshold) is acceptable —
> given that confidence monitors stay reassuring, distribution monitors cry wolf, and a constrained
> adversary can exploit the gap?

Working title: **"A Shift Alarm Is Not a Safety Certificate: Recall Certification for Cross-Testbed
Intrusion Detectors."** Provisional; precise, and it retires the old title's overclaim (not *all*
label-free monitors are blind — only the score-only ones).

## What the review got right, and what I changed

1. **Title overclaim.** Correct. The paper's own §4.5/§5.2 already split score-only monitors (blind)
   from feature monitors (non-specific). Title fixed; the three-task separation (ranking quality /
   operating-point risk / monitoring reliability) is made explicit.
2. **Decision-gate reframe.** Adopted, but narrowed (novelty below).
3. **Wire-realism study.** Declined — needs pcaps/extractors this machine cannot process, and PLAA
   (arXiv 2606.28439) already owns packet-level realizable attacks. The paper stays explicitly
   feature-space; claims narrowed. (The review's "FlowUAP / PacketEditRL" did not resolve to real
   papers; PLAA and PAVE are the real references.)

## Closest-work comparison (verified 2026-10-22)

| Work | What it establishes | Assumption | What it leaves for us |
|---|---|---|---|
| **Podkopaev & Ramdas 2022** (arXiv 2110.06177) | Sequential tracking of a deployed model's risk; detect harmful shift | Streaming labels / loss | Not recall-at-threshold for NIDS; not adversarial; not "why confidence monitors fail" |
| **PPRM** (Zhang et al., arXiv 2602.02229, ICML 2026) | Prediction-powered risk monitor: synthetic labels + few true labels + anytime-valid bound | A labelled trickle; general ML | General-purpose; not the NIDS operating-point / quiet-confidence-monitor failure, not adversarial |
| **RiskGate-IDS** (ScienceDirect S187454822600048X) | Budget-aware two-stage NetFlow IDS: source gate + small labelled target calibration + budgeted verify | Target labels for calibration | Builds a *detector*; does not isolate the recall-invisibility of score-only monitors, nor certify-vs-escalate decision risk |
| **PLAA** (arXiv 2606.28439) | Packet-level realizable adversarial traffic, 92.78% evasion | Packet control | Owns wire-realism; no confidence-monitor / certification framing |
| **PAVE** (S2667295226000450) | Feature-space attacks 0–3% wire-valid | Protocol validity | The realism caveat we adopt |

**Novelty verdict (honest).** The audit *mechanism* (budgeted labels + a finite-sample recall
bound) is **not novel** — PPRM, Podkopaev–Ramdas and RiskGate-IDS own it. Forcing it into the paper
as a new "gate" would fail a reviewer. The defensible contribution is **the theorem plus its
measured consequence**: (i) a proof that no score-only monitor can certify recall (§4.5), which none
of the above states; and (ii) a measurement, on the 240-config matrix, of how badly the deployed
confidence monitors mislead (false assurance on 15% of configs) and how few labels a standard
finite-sample audit needs to recover the truth (**10 flows: 15% → 0.03% false assurance**). The gate
is presented as the *necessary* response to the theorem, using off-the-shelf machinery that we cite,
not as a new monitor competing with PPRM/RiskGate-IDS.

## Pilot result (compute-free, `results/p1/riskgate_pilot.json`)

Across 240 configs, 227 are unsafe (true attack recall < 0.5 at the deployed threshold). The
score-only confidence monitors **accept 15% of configs as safe when they are not** (false
assurance 0.150). A Clopper-Pearson recall audit on **k = 10** labelled target attack flows cuts
false assurance to **0.0003**, with coverage 0.81 and 86% of unsafe configs correctly escalated; at
k = 50, coverage 0.90 and 95% escalated. This confirms the review's hypothesis that a small,
operating-point-aware audit is far more defensible than the confidence monitors — and it quantifies
the budget. It also connects to P11 (F7: ten labelled target flows beat every zero-label method).

## Minimum experiments to make the narrowed claim (mostly done)

- [x] Recall-invisibility proposition + empirical ATC 0.999 / recall 0.000 (§4.5).
- [x] The three-task separation across the transfer matrix (ranking AUC vs latent recall vs monitor).
- [x] Score-only false-assurance rate vs audit-gate false-assurance/coverage at budgets {10..250}.
- [ ] Report uncertainty acknowledging correlated (model, seed, pair) structure — add a note that
      240 configs are not 240 independent environments (12 pairs × 4 models × 5 seeds).
- [ ] One paragraph positioning vs PPRM / RiskGate-IDS / Podkopaev–Ramdas in related work.

## Risks / fallback

- **Risk:** the gate reads as "just apply a known audit." **Mitigation:** frame strictly as the
  theorem's corollary + a measurement; never claim a new estimator. If a reviewer still rejects the
  gate as derivative, drop it to a short "what certification costs" subsection — the theorem + the
  240-config measurement stand alone.
- **Risk:** correlated-observation inflation of the 240 count. **Mitigation:** report per-pair and
  per-model breakdowns (already have) and state the dependence explicitly.
- **Fallback:** if the gate adds nothing over citing PPRM, the paper is still the theorem +
  generality measurement + honest negative defence — publishable and SOP-relevant on its own.

## SOP effect

This completes the arc: P9/P06b/P14/P11 each found a metric that does not license its decision; P-1
proves *why* one such metric (label-free confidence) cannot, and measures what evidence does. The
research identity sharpens to: *when does an evaluation license a deployment decision, and what is
the minimal evidence that restores it?*
