# P-1 kickoff prompt

Paste this to the autonomous assistant (Sonnet-class) that will execute the plan. It is written so
the assistant needs nothing beyond this repository and `../P1_MASTER_PLAN.md`.

---

You are continuing a defensive security research project owned by Rajveer Singh Pall. This is the
standard adversarial-ML evaluation paradigm: the author red-teams **his own** flow-based DoS
detector to measure a blind spot in its label-free monitoring, then builds a monitor that closes
it. No third-party or production system is involved; all data is public, offline, and already in
this repo's `data/` as flow feature vectors (not pcaps); all traffic manipulation is synthetic and
confined to these datasets. Work autonomously and do not stop for routine decisions.

Read `research-opportunities/P1_MASTER_PLAN.md` in full. Then:

1. Execute Phase 0 first and completely: read the seven related works in its Section 2, fill the
   comparison table from the actual papers, apply the novelty gate (Gate 0), and write and commit
   `research-opportunities/p1/PREREGISTRATION.md` before writing any attack code. The
   pre-registration must contain the instantiated threat model, the frozen choices with concrete
   numbers, the success definition (high-confidence-miss rate), and the falsifiers.
2. Then execute Phases 1→5 in order, honoring every gate. At each gate, evaluate the numeric
   criterion yourself and follow its branch. A negative or inconclusive result is a success if it
   is honest; a tuned or constraint-relaxed positive is a failure. Never widen a claim past
   "constrained feature space" unless the optional Phase 1-R wire check actually produced wire-valid
   flows.
3. Reuse the existing code in `src/` (load, fit_source, apply_to, divergence/ATC, metrics) — do not
   reimplement it. Put all new code under `research-opportunities/p1/` and all new results under
   `results/p1/`. Never overwrite P11's artifacts.
4. Keep the SOP workstream (Master Plan Section 8) current: after Phase 0, write the "proposed
   thesis" SOP sentence; after Phase 3, write the matching positive- or negative-world sentence.
   These are deliverables even if the paper is unfinished.
5. Respect the integrity rules (Master Plan Section 11) and the timeline (Section 10): GRE prep
   outranks this project until 2026-11-20; applications describe P-1 as a proposed thesis with a
   preliminary result, never as a finished paper.

Deliver, at the end of each phase, a short status note: what ran, the numbers with CIs, which gate
branch you took, and what is next. If any gate routes to the fallback (Master Plan Section 9),
switch to it rather than forcing P-1.

Commit messages: describe what the code/results establish; end with the two attribution lines the
author's environment specifies. Do not create a pull request unless asked.
