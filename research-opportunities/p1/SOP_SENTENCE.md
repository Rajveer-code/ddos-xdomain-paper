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

## After Phase 3 — fill whichever world applies (do NOT write yet; Phase 3 is deferred)

- **Positive world:** "In preliminary work, an adversary limited to [stated capability] produced
  high-confidence misses in **X%** of transferred attack flows while ATC continued to report normal
  accuracy; monitoring the low-controllability features reduced this to **Y%** at a **Z%**
  review-burden cost."
- **Negative world:** "In preliminary work I found that under traffic-plausible constraints the
  monitored detector resisted high-confidence evasion, which sharpens rather than weakens the open
  question of what a realistic adversary can achieve."

X, Y, Z come only from `results/p1/attack_results.json` and `defense_results.json`. No number here
until those files exist.

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
