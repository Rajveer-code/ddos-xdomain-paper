# P-1 status ledger — *Hiding in the Shift*

State lives here, not in chat. Any model should resume from this file alone.

## Governing docs
- Spec: `research-opportunities/P1_MASTER_PLAN.md`
- Pre-registration (frozen choices + dated amendments): `research-opportunities/p1/PREREGISTRATION.md`
- Paper draft: `research-opportunities/p1/PAPER_DRAFT.md`
- Keyed numbers: `results/p1/summary_p1.json`; verifier `check_numbers_p1.py` (PASS, 19 keys).
- SOP deliverables: `research-opportunities/p1/SOP_SENTENCE.md`

## Code (all under research-opportunities/p1/, reuses src/)
`constraints.py` (feasible/project/bounds) · `p1common.py` (memory-bounded loader + leakage-safe
fit) · `monitors.py` (battery, source-val null calibration) · `evade.py` (score + strong search)
· `defend.py` (low-controllability novelty monitor) · runners `run_phase1/2/3/4.py`,
`compute_lift.py`, `aggregate_p1.py`. Each module has a runnable self-check.

## Phase log — ALL PHASES COMPLETE (full frozen spec: 5 seeds, 200k/50k caps), 2026-10-22

### Phase 0 — pre-registration + novelty gate — DONE (commit be3345e)
Seven works verified; Gate 0 (novelty) PASS; frozen choices committed before code.

### Phase 1 — constraints + controllability — DONE
Per-source [p1,p99] family box (`results/p1/constraints.json`). Controllability R² of each
indirect feature from the directly-controllable ones (`feature_controllability.json`).
**Gate 1 PASS but narrow:** only `DST_TO_SRC_SECOND_BYTES` (UNSW) and + `RETRANSMITTED_OUT_BYTES`,
`RETRANSMITTED_OUT_PKTS` (BoT-IoT) are low-controllability; most responder features are
predictable from the attacker's direct choices. Thin defensive material — recorded, not hidden.

### Phase 2 — monitor baseline (no attack) — DONE (`monitor_baseline.json`)
Under natural transfer the distribution monitors (KS, A-distance, Wasserstein) fire ~1.0; the
model-based monitors (ATC, conf-drop) ~0.75. Natural shift is loud. 12 configs.

### Phase 3 — adaptive high-confidence-miss search — DONE (`attack_results.json`, `lift.json`)
**CORRECTED after an own-code audit (see below). Full frozen spec, 5 seeds.** Honest decomposition
on real target flows:
- **Latent high-confidence-miss rate** (real flows, NO attacker box): 0.984/0.953/0.319/0.999
  (unsw-LGBM / unsw-LogReg / bot-LGBM / bot-LogReg). The detector is already high-confidence wrong
  on 32–100% of real target DoS flows — the dominant effect.
- Projected floor (project into box, no search): 0.679/0.658/0.282/0.901.
- Searched HCMR: 0.910/0.909/0.889/0.902 (≈ feasibility ceiling).
- **Search's own contribution** = searched − projected: **+0.232/+0.251/+0.607/+0.001**. The search
  buys misses where the detector has headroom (LightGBM cells) and nothing on the saturated
  bot/LogReg. Small P-drop (0.003–0.048); strong search adds ≤0.01.

**AUDIT CORRECTION (2026-10-22):** the first draft reported a "+0.88 lift" by computing the natural
baseline with the SOURCE-box feasibility filter applied to raw target flows (which never satisfy
it), conflating "clip into box" with "evasion". A read-only correctness audit caught it. Fixed:
`compute_lift.py` now reports latent (no filter) / projected / searched separately; lift =
searched − projected. The honest finding is latent-exposure-dominant, which is stronger and closer
to P11. No arithmetic/leakage bug was found; the flaw was the comparison definition only.
- **Ruling (Gate 3 world):** monitor alarm tracks natural shift, not the attack. For LightGBM the
  model-based monitors fire (ATC usable → F-monitor-already-works there). For **BoT-IoT→IDS2018 +
  LogisticRegression** they stay silent (0.0 natural & adversarial) while HCMR=0.901 — the genuine
  quiet-monitor failure. My global gate3 flag printed `proceed_to_defense=false` (threshold
  `<0.5`, BoT got exactly 0.5); the honest reading is a quiet world exists in the LogReg configs,
  so Phase 4 was run. Cost if wrong: a defence evaluated on a case where existing monitors already
  suffice — reported either way.

### Phase 4 — low-controllability defence — DONE (`defense_results.json`) — NEGATIVE
IsolationForest on low-controllability features, source-benign fit, 1% budget. **Fails Gate 4
everywhere:** ΔHCMR 0.072 (UNSW) / 0.012 (BoT-IoT) vs the 0.10 bar; catches ≤8% of misses.
Reason (ties to P11): the low-controllability features do not transfer across independent
testbeds, so a source-fitted monitor on them cannot separate adversarial target flows from
benign target traffic. Reported as the result, per Gate 4's negative branch.

### Phase 5 — write-up + verifier + SOP — DONE
`PAPER_DRAFT.md` (pilot-labelled, numbers pinned); `check_numbers_p1.py` PASS; SOP sentence
updated to the honest positive-with-caveat world.

## Deviations ruled & ledgered (also in PREREGISTRATION §8)
1. **Memory loader.** On this 16 GB machine (~1.5 GB free under load) `get_domain` OOMs on the
   17–30M-row parquets. `p1common.read_capped` streams with pyarrow `iter_batches` (columns-only,
   two-pass Bernoulli per class). ML logic unchanged (src primitives). Cost if wrong: a different
   capped sample than P11's; mitigated by fixed seeds + the two sources both being single-family.
2. **White-box ablation → strong upper bound.** Tree ensembles are non-differentiable; the
   pre-registered white-box mode is realised as a high-budget coordinate-descent upper bound,
   labelled as such, never claimed as gradients.
3. **Scale.** Full frozen spec ran 2026-10-22: 5 seeds (42–46), source cap 200k/class, target
   benign 50k, attack 2,000/family. (An earlier 3-seed pilot was superseded; git history keeps it.)
   Qualitative findings are unchanged from the pilot — robust across 5 seeds.

## Resume / extend
- Optional Phase 1-R wire-realism check (one family, nfstream) to lift "feature-space" to
  "wire-valid" for that family.
- Add a second DoS family if a source with reflection/low-rate families is used.
- Compile the draft to the repo's figure/PDF pipeline for submission.
