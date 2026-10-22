# P-1 SOP workstream — sentences and framing

The SOP does not need the paper finished. It needs an honest, specific sentence phrased as a
question under investigation, plus P11's verifiable preprint link. These are deliverables
regardless of how Phases 3–4 turn out (master-plan Section 8).

## After Phase 0 — proposed-thesis sentence (use now)

> For my thesis I am investigating whether an adaptive adversary, constrained to
> traffic-plausible changes, can drive malicious flows into the high-confidence region where
> label-free monitors (such as Average Thresholded Confidence) stay silent after cross-network
> transfer, and whether monitoring the features the adversary cannot freely set restores the
> warning.

Rules for using it: phrase as a **question under investigation**, never as a completed result.
Pair it with P11 described as a *preprint with a preliminary result*, not a publication.

## After Phase 3 — FILLED from the pilot (2026-10-22). Honest, with caveats.

The pilot landed in a mixed world: the adversary is powerful, the monitors are *model-dependently*
blind, and the obvious defence fails. SOP sentence (use this):

> In preliminary work, I showed that cross-testbed DoS detectors already misclassify almost all
> target attacks as benign but at low confidence, where a label-free confidence monitor would flag
> them; a score-only adversary limited to traffic-plausible feature changes converts these into
> **high-confidence** misses in ~90% of transferred attack flows (from a ~0.3–2.3% natural rate),
> and for a well-transferring detector the confidence monitor stays silent throughout. The obvious
> responder-side defence does not close the gap, because the features it would watch do not
> transfer across networks either — which is itself the deeper problem my thesis targets.

Caveats to carry with it: **pilot** (3 seeds, one dataset family, feature-space, two pairs); the
quiet-monitor failure is clean for one of four (model, pair) cells (LogisticRegression on
BoT-IoT→CSE-CIC-IDS2018); for LightGBM the confidence monitors do fire. Do not round "~90%" up or
drop the "pilot/feature-space" qualifier. Numbers: `results/p1/summary_p1.json`.

Shorter variant (one line):

> For my thesis I am studying how a traffic-plausibly-constrained adversary turns the low-confidence
> false negatives of a cross-network DoS detector into high-confidence ones that label-free monitors
> wave through, and why the obvious responder-side defence fails to transfer.

## Faculty framing (verify before naming anyone in an SOP)

- **David Inouye (Purdue ECE)** — explaining/localizing distribution shift; the natural
  methodological complement, and in P11 the only distance-based signal that carried any warning was
  the largest single-feature shift (his territory). **Confirm he can advise a CS-department thesis
  before naming him as a committee hook.**
- **Ruqi Zhang (uncertainty)** — complement on the confidence signal.
- **Security advisor needed** — a cross-network-security thesis needs one (e.g. Bertino's group,
  concept drift in malware detection, NDSS 2025; or Li/Zhang AI-security advising). Name a specific
  person only if a current paper supports it.
- Name Saparov only if a specific current paper supports it.

## Non-project SOP fixes that outrank this project (do first; master-plan Section 8)

1. **Resolve P11 authorship** — CV says sole author, ~16 outreach drafts credit Dr. Yadav, the
   2026-10-07 decision added him, the manuscript still lists one author. Make all four agree before
   anything ships.
2. **Post P11 to arXiv** (~10 Nov) so the security paragraph is verifiable.
3. **If P06b is accepted at ML4H** (decision due ~2026-10-22) upgrade every profile the same day.
4. None of this costs GRE prep before 2026-11-20.
