# P-1 status ledger — *Hiding in the Shift*

State lives here, not in chat. Any model should resume from this file alone.

## Governing docs
- Spec: `research-opportunities/P1_MASTER_PLAN.md`
- Pre-registration (frozen choices): `research-opportunities/p1/PREREGISTRATION.md`
- SOP deliverables: `research-opportunities/p1/SOP_SENTENCE.md`

## Phase log

### Phase 0 — pre-registration + literature gate — COMPLETE (2026-10-22)
- All seven related works verified to exist (URLs in PREREGISTRATION §2). Row 2
  (Gnanaratna/Kingston, SecureComm 2026) exists but its internal details are **UNVERIFIED** —
  abstract not retrievable; re-read the full chapter before citing specifics.
- **Gate 0 (novelty): PASS.** No paper does the joint object. Closest is Bikdeli (benign-shift
  audit of label-free monitors); one-sentence delta recorded in PREREGISTRATION §2.
- Frozen choices set with concrete numbers: τ_accept = 1% benign-review budget; query budget 200
  (reported at {50,100,200}); 2,000 target attack flows/family cap; seeds 42–46; monitor battery +
  thresholds on source-validation; Phase 3 "which world" gate; Phase 4 bar = HCMR −10 pp absolute
  at ≤ +2 pp benign review.
- Baseline AUCs pinned to `results/matrix_summary.json`: UNSW→IDS2018 LightGBM 0.0697 (inverted);
  BoT-IoT→IDS2018 LightGBM 0.9656 (threshold-dominated).
- SOP proposed-thesis sentence written (SOP_SENTENCE §"After Phase 0").
- **Ruling (scope):** master-plan Section 10 and the kickoff's point 5 both make GRE outrank P-1
  until 2026-11-20 and limit current work to Phase 0 (reading/writing). Phases 1–5 need the Kaggle
  data downloaded and days of attack-search compute, dated 2026-11-21+. So Phase 0 was executed and
  committed now; Phases 1–5 are **deferred, not skipped**. Cost if wrong: a few weeks' delay, which
  the calendar already builds in.

## Resume here (Phase 1, on/after 2026-11-21)
1. `research-opportunities/p1/constraints.py` — `feasible()` + `project()`; derive per-family
   [p1,p99] box and dependency slacks from real source attack flows via `src/data.load`. Save
   `results/p1/constraints.json`.
2. Feature-controllability R² of each indirectly-influenced feature from the directly-controllable
   ones, on real flows. Save `results/p1/feature_controllability.json`. **Gate 1:** some indirect
   features must have low R² or the defense has nothing to stand on (→ narrow per F-no-defense-features).
3. Then Phases 2→5 per master plan, honoring every gate. Reuse `src/` (fit_source, apply_to,
   divergence/ATC, metrics) — do not reimplement.

## Data note
`data/` is gitignored (Kaggle mirrors). Confirm the NetFlow v2 quartet is downloaded
(`python scripts/download_data.py`) before Phase 1; Phase 0 needed no data.
