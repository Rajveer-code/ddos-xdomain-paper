# arXiv submission sheet (prepared 2026-10-19; the author submits)

**Upload:** `paper/arxiv_source.tar.gz` (main.tex + figures/, 1.1 MB). Built by
`python scripts/build_pdf_elsarticle.py --arxiv`, then `tar -czf` of `paper/arxiv/{main.tex,figures}`.
Tested: extracted into an empty folder, pdfLaTeX twice, exit 0, 41 pages, no undefined references.
The arXiv build omits the journal name and the elsarticle "Preprint submitted to" footer,
because the paper has not been submitted anywhere yet.

## Form fields

**Title**
Confidently Wrong: Ranking Inversion in Cross-Network Denial-of-Service Detection

**Authors**
Rajveer Singh Pall

**Abstract** (1,464 characters, plain ASCII; arXiv limit 1,920)

Flow-based DoS detectors score near-perfectly on the network they were trained on and lose most of that skill on a different one. The loss is well documented; its character is not. Where the score ordering survives the move, the repair is a new threshold; where it has broken, no threshold is enough and the scoring function itself has to change. We train four model families on four independently captured testbeds under a published common feature set and evaluate every ordered pair over five seeds. Transfer does not decay toward chance; it passes through chance. Of 240 run-level evaluations, 108 score below ROC-AUC 0.5, three of the twelve ordered pairs do so in all four model families, and the worst reaches 0.0697 -- negating the score would give 0.9303. Attack flows are being scored below benign ones. Most pairs fail at the ranking rather than at the threshold, nine to eleven of twelve for the primary model depending on how the two losses are compared, which makes recalibration the wrong instrument for most of them: a threshold can only cut an ordering it cannot repair. Ten deliberately balanced labelled target flows lift median macro-F1 from 0.3919 to 0.7253 when added to the source data, but a classifier trained on those ten flows alone does at least as well (0.7852): here the labels, not the source model, do the repair. Cross-network evaluation has to separate ranking failure from threshold failure, because the two admit different fixes.

**Comments**
41 pages, 7 figures, 16 tables. Code, results and a full-pipeline rerun record: https://github.com/Rajveer-code/ddos-xdomain-paper

**Primary category:** cs.LG (Machine Learning). You are already endorsed here (arXiv 2607.16253).

**Cross-list:** cs.CR (Cryptography and Security). Whether a cs.CR cross-list needs its own
endorsement is not stated on arXiv's help pages; if the form asks for an endorsement, drop the
cross-list rather than wait, and keep cs.LG alone. Optional second cross-list: cs.NI.

**ACM class (optional):** I.2.6; C.2.0

**Licence:** arXiv.org perpetual, non-exclusive licence. It is the least restrictive choice for
a later copyright transfer to Elsevier under the subscription route. The licence cannot be
changed once chosen.

**Journal-ref / DOI / Report number:** leave empty.

## Compatibility already checked

- Elsevier (Computer Networks): sharing a preprint "will not count as prior publication"
  (Guide for Authors, read 2026-10-17 in the readiness audit). Submit to Computer Networks the
  same week and cite the arXiv ID in the cover letter.
- Repository is public and the manuscript's code-availability statement is true (verified
  logged-out, 2026-10-19).

## After arXiv announces the paper

1. Add the arXiv ID to the README, Google Scholar, ORCID and your CV ("preprint", not
   "under review", until Computer Networks confirms receipt).
2. Submit `paper/elsarticle/` (main.tex, figures, highlights.txt) to Computer Networks.
3. Update `TRUTH.md` and the master plan status for P11.
