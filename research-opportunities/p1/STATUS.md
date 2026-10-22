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

## Manuscript upgrade (2026-10-22 PM, autonomous) — mostly DONE
Goal: best-possible submission-quality manuscript. The canonical paper is now **MANUSCRIPT.md**
(PAPER_DRAFT.md is superseded). State:
1. DONE (f93f978): 4 models (LightGBM, LogReg, XGBoost, RandomForest) on the 2 pairs. 8 cells.
2. DONE (fb6b9ad): full NetFlow v2 transfer matrix (matrix_latent.json) — 240 configs, 12 pairs.
   Mean latent HCMR 0.679; 36/240 dangerous cells across 9 combos. summary_p1.json has a `matrix`
   block. MANUSCRIPT.md written (all sections).
3. DONE (c2dbaa8): budget_curve.json (budget matters only with headroom); 4 figures.
4. DONE (this commit): fig5 transfer-matrix heatmap; Table 1 (8 cells); real references.
   check_numbers_p1.py verifies MANUSCRIPT.md.
5. Remote: private, pushed through c2dbaa8 (push again after this commit).
Remaining polish ideas (optional): τ_accept=5% sensitivity; controllability-R² table; convert
MANUSCRIPT.md to the repo's elsarticle/IEEE PDF pipeline; a second DoS family if a multi-family
source is added. All findings robust across 5 seeds and 4 models.
If resuming: re-read summary_p1.json + MANUSCRIPT.md + this file; the manuscript is complete and
verified — further work is polish, not core results.

### Later same day — review + hardening + generality (autonomous)
- Fresh senior-reviewer audit of MANUSCRIPT.md; all findings fixed in commit d9c04f2 (stale config
  block, "small Pdrop throughout" overclaim → two-regime, strong-search "≤0.01" → up to +0.049,
  CIs now in Table 1, evidence base + P11-AUC in §7, Gate-3 reconciliation, Fig5 caption). τ-accept
  1%-vs-5% sensitivity added (dangerous cell unchanged). check_numbers 26/26.
- RUNNING: `matrix_attack.py` → results/p1/matrix_attack.jsonl (+ .json) — the score-only attack
  across ALL 12 ordered pairs × 4 models × 5 seeds, resumable (skips done configs). Removes the
  "adversarial result is one cell" limitation. When done: aggregate dangerous-cell count into the
  summary (`matrix` block or new `matrix_attack` block), add a §5.2/§5.3 sentence + fig, re-check,
  commit, push.
- README.md added (commit c0fc571). Repo private; pushed through c0fc571.
- PDF: pandoc absent, pdflatex (MiKTeX) present — PDF build left as an easy follow-up (adapt
  scripts/build_pdf_elsarticle.py, or hand-write a short LaTeX wrapper).
If resuming and matrix_attack.jsonl exists: re-run matrix_attack.py (it resumes), then aggregate.

## Resume / extend
- Optional Phase 1-R wire-realism check (one family, nfstream) to lift "feature-space" to
  "wire-valid" for that family.
- Add a second DoS family if a source with reflection/low-rate families is used.
- Compile the draft to the repo's figure/PDF pipeline for submission.
