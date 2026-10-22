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

The pilot (corrected after an own-code audit; see STATUS) landed on a latent-exposure-dominant
finding, which is stronger and more honest than a big-adversary claim. SOP sentence (use this):

> In preliminary work I found that cross-testbed DoS detectors are already *high-confidence* wrong
> on 32–100% of real target attack flows — exactly the operating point that label-free monitors
> (such as Average Thresholded Confidence) are meant to protect — and that those monitors are
> model-dependently blind to it. A traffic-plausibly-constrained, score-only adversary widens this
> hole where the detector still has headroom but adds nothing where it is already saturated, and
> the obvious responder-side defence does not close the gap because the features it would watch do
> not transfer across networks either.

Caveats to carry with it: 5-seed full run, but still **one NetFlow v2 family, feature-space, two
pairs**; the quiet-monitor failure is clearest for LogisticRegression on BoT-IoT→CSE-CIC-IDS2018,
which is also where the adversary is redundant (detector already fully open, latent 0.999); for
LightGBM the confidence monitors do fire. Lead with the *latent* failure, not the adversary.
Numbers: `results/p1/summary_p1.json`.

Shorter variant (one line):

> For my thesis I am studying why label-free monitors stay silent while cross-network DoS detectors
> already wave through most real attacks at high confidence, how far a traffic-plausibly-constrained
> adversary can widen that blind spot, and why the obvious responder-side defence fails to transfer.

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
