# Manuscript Audit & Strategy — *Confidently Wrong*

> **Status 2026-08-15, post-fix.** BLOCKER-1 (bibliography), BLOCKER-2 (figures),
> BLOCKER-3 (pre-registration wording) and MAJOR-4 (missing interval), MAJOR-5 (length),
> MINOR-6 and MINOR-7 are all resolved. MAJOR-4 changed the paper's claim rather than
> merely defending it: the capacity hypothesis is now reported as unsupported at this
> power (+0.0132 [-0.0084, +0.0320], p=0.209) rather than refuted, and computing the
> intervals surfaced a genuine sub-effect the coarse grouping had hidden
> (drop_size_volume +0.0615 [+0.0278, +0.0991], p<0.001). Remaining open item:
> Reviewer C's benign-pool contamination sensitivity, deliberately deferred.

Audit date: 2026-08-15. Venue economics verified this session (see §VI).
**Scope note:** this is a partial run of the manuscript-elevator pipeline. Executed: pre-scan,
novelty/statistics audit, gatekeeping, simulated peer review, venue strategy, action plan.
**Not executed:** live competitive benchmarking against full texts of recent accepted COSE papers,
and the journal-voice profile. Both need many full-text reads; the verdicts below are therefore
calibrated against the prior-art survey done earlier this session, not against a fresh comparator set.

---

## PART I — STRATEGIC VERDICT

**Bottom line.** The science is genuinely publishable and, in two places, genuinely interesting: the
reframing of cross-network failure as *sign inversion* rather than degradation is well-evidenced
(108/240 runs below chance AUC, one pair at 0.0697), and the negative result on
distribution-divergence predictors contradicts an assumption embedded in a large body of
domain-adaptation work. A refuted pre-specified hypothesis reported as refuted is a strong integrity
signal that reviewers reward. **The manuscript is not, however, submittable today.** It has no
bibliography, no embedded figures, and at roughly 4,700 words it is about half the length of a
typical *Computers & Security* article. One statistical claim, the central refutation, is not
currently defended with an interval. Fix those four things and this is a credible Q1 submission.

**Portfolio placement.** Invest here. This is a stronger paper than the original CIC-2019→2017
notebook could ever have been, and its findings are not replaceable by a follow-up.

**Publication strategy.** arXiv preprint immediately after the fixes, then submit to *Computers &
Security*. Do not chase a conference for speed: "under review at Computers & Security" plus a
citable preprint is listable on Fall-2027 applications and costs nothing.

**Timeline headline: Moderate, and it fits.** COSE first decisions typically run 2–4 months.
Submitting mid-September 2026 puts a first decision around November–January. Even a Major Revision
verdict leaves "under review" listable in the Nov–Dec 2026 window, and the preprint is listable from
the day it posts.

**Professor Perspective.** A faculty member skimming this CV sees an applicant who ran a 240-cell
transfer study single-handed, pre-specified a hypothesis, watched it fail, and published the failure
with the effect size attached. That reads as maturity, not weakness. The visible risk is the reverse:
a reviewer who thinks the author over-claims from four testbeds and twelve ordered pairs.

**Research Identity.** Empirical-audit / evaluation-methodology researcher. Coherent with the
existing fairness-audit and benchmark work; this is the same instinct applied to network security.

### Admissions ROI

| dimension | /10 | reason |
|---|---:|---|
| Research quality | 8 | Real findings, honest negative results, verified reproducibility |
| Publication prestige | 7 | COSE is Q1 and well-regarded, but not a top-4 security venue |
| Timeline feasibility | 8 | Preprint immediately; "under review" listable by Nov–Dec 2026 |
| Admissions impact | 6 | For course-based MS, research helps but letters and grades outrank it |
| Time investment | 7 | Most of the cost is already sunk; ~20 hours to submittable |
| **Overall ROI** | **7** | Worth finishing. Not worth a third follow-on paper of the same kind |

### Reviewer Scorecard

| axis | /10 | one-line reason |
|---|---:|---|
| Novelty | 7 | Inversion framing and the divergence negative result are new; the gap itself is not |
| Methodology | 8 | Leakage discipline asserted in code, de-duplication handled better than the field norm |
| Experimental design | 8 | Full ordered matrix, 4 model families, 5 seeds, both feature spaces |
| Statistics | 5 | Gap CIs are strong; the central refutation has no interval (see BLOCKER-3) |
| Writing | 8 | Clear argument spine, findings in topic sentences |
| Figures | 7 | Legible and regenerable, but not embedded in the manuscript |
| Tables | 8 | Ten tables carrying the enumerable content properly |
| Reproducibility | 9 | Seeds, pinned deps, all numbers regenerate, verification script |
| Ethical reporting | 8 | Refutation reported; corrections stated where the claim depends on them |
| **Overall readiness** | **6** | Strong science, incomplete artefact |

---

## PART III — GATEKEEPING (highest leverage; fix these first)

**[BLOCKER-1] No bibliography.** §References is a `[PLACEHOLDER]`. Nine sources are cited in text
by author-year with no entries. This is an automatic desk rejection. *Fix: ~2 hours.*

**[BLOCKER-2] Figures are not in the manuscript.** Seven figures are referenced; none is embedded and
none carries a caption in the document. They exist as PNGs with captions in `figures/MANIFEST.json`.
*Fix: ~1 hour.*

**[BLOCKER-3] "Pre-registered" is the wrong word, and it is an integrity risk.** The capacity
hypothesis was written into `RESEARCH.md` and committed *before* the ablation ran, which is
git-timestamped and genuinely creditable. But "pre-registered" has a specific meaning (a public,
time-stamped registration on OSF or similar) and this was not that. A reviewer who checks will treat
the overstatement as a credibility problem, and it would taint the paper's strongest integrity claim.
*Fix: replace with "pre-specified" throughout and add one sentence stating that the hypothesis was
committed to the public repository before the experiment was run, with the commit reference. Ten
minutes, and it converts a liability into verifiable evidence.*

**[MAJOR-4] The central refutation has no interval.** §4.4 concludes the capacity hypothesis is
refuted because removing all capacity features buys +0.0132 macro-F1. No confidence interval or test
accompanies that number, so the paper cannot presently distinguish "no effect" from "small effect we
were underpowered to see". This is the single claim most likely to be attacked, and it is the paper's
own headline refutation. *Fix: paired bootstrap over the ablation seeds, reporting the delta with a
95% CI, same machinery already used for the transfer gaps. ~2 hours of compute and a table column.*

**[MAJOR-5] Length.** At ~4,700 words the manuscript is roughly half a typical COSE article. The gap
is not padding-shaped: Related Work (355 words) is thin for a Q1 journal, §4.1–4.3 and §4.7/4.9 are
compressed, and there is no per-family analysis for the CIC study.

**[MINOR-6] Seed inconsistency.** The transfer matrix uses 5 seeds, the ablations 3. Defensible on
cost but must be stated in §3.5 rather than left for a reviewer to notice.

**[MINOR-7] `n/a` in Table 3.** The `all` row's delta cell reads `n/a` where `0` would be correct
(the baseline's delta against itself is zero by construction).

**Integrity scan:** no fabricated citations, no future-dated references, no claims exceeding evidence
that I could locate other than BLOCKER-3. Numbers are internally consistent by automated check
(787/787 trace to `results/`).

---

## PART V — SIMULATED PEER REVIEW

**Reviewer A (network measurement, positive, 7/10).** "The inversion result is the most interesting
thing I have read on this topic this year, and §4.8's observation that same-institution pairings
produce qualitatively different conclusions is a genuine service to the field. I want the label-noise
result expanded. **Tough question:** NF-UNSW-NB15 retains 3,075 attack flows and produces the most
extreme inversion. How much of Figure 2's bottom row is domain distance, and how much is a source
with almost no positives?"

**Reviewer B (machine learning, sceptical, 5/10).** "Twelve ordered pairs is a small sample on which
to declare that proxy A-distance does not work. The leave-one-pair-out protocol is correct, but the
conclusion is stated far more strongly than n=12 supports. Similarly, §4.4 declares a hypothesis
refuted on a difference of 0.0132 without an interval. **Tough question:** what is the 95% CI on that
0.0132, and is your study powered to detect an effect of 0.05?"

**Reviewer C (security practitioner, positive, 7/10).** "The label-budget curve is the most useful
figure here and should be promoted. The duplicate-rate table should be its own contribution.
**Tough question:** the benign-quantile threshold assumes an operator can identify benign traffic on
their own network. In practice that traffic contains undetected attacks. How sensitive is the 97.0%
recovery to contamination of the benign pool?"

**Associate Editor.** "Major Revision. The empirical contribution is solid and the honesty about the
refuted hypothesis is welcome. Address the statistical power concerns, add the missing bibliography,
expand Related Work, and moderate the claims in §4.5 to match n=12."

### Reviewer Confidence Score — Computers & Security (rough estimate)

| outcome | as-is | after BLOCKER 1–3 + MAJOR 4–5 |
|---|---:|---:|
| Desk reject | 60% | 5% |
| Reject after review | 15% | 15% |
| Major revision | 20% | 55% |
| Minor revision | 5% | 22% |
| Accept | 0% | 3% |

**The single change that shifts most mass to acceptance:** put a confidence interval on the
refutation (MAJOR-4). It converts the paper's most attackable sentence into its most defensible one.

---

## PART VI — WHERE TO SUBMIT (free-first; verified 2026-08-15)

| venue | type | cost to author | fit | odds | timeline | listable by Nov–Dec 2026 |
|---|---|---|---|---|---|---|
| **Computers & Security** (Elsevier) | Q1 journal | **Free** (subscription route; OA optional at USD 3190) | Excellent | Moderate | 2–4 mo to first decision | Yes, as "under review" |
| **IEEE TNSM** | Q1 journal | Free (non-OA) | Good | Moderate | 3–6 mo | Yes, as "under review" |
| arXiv cs.CR | preprint | Free | n/a | n/a | Days | **Yes, citable immediately** |
| WTMC @ EuroS&P 2027 | workshop | Free to submit; registration payable | Excellent | Strong | CFP ~Feb–Mar 2027 | No |
| USENIX CSET 2027 | workshop | Free to submit; registration payable | Excellent | Strong | ~Apr–May 2027 | No |
| RAID 2027 | top-tier conf | Free to submit; registration payable | Good | Long-shot | ~Apr 2027 | No |

**Recommendation:** arXiv now, COSE as first submission. WTMC 2027 is the natural home if COSE
rejects, and the paper would be competitive there.

**Cost warning restated:** no reputable conference is free to *present* at. Only the journal
subscription route and arXiv are genuinely zero-cost.

---

## PART VII — PLAN

### Prioritised actions

| # | action | effort | Δ publication probability | Δ admissions value |
|---|---|---|---:|---:|
| 1 | Bibliography (BLOCKER-1) | 2 h | +0.55 | — |
| 2 | Embed figures with captions (BLOCKER-2) | 1 h | +0.10 | — |
| 3 | "Pre-registered" → "pre-specified" + commit reference (BLOCKER-3) | 10 min | +0.05 | +high (integrity) |
| 4 | CI on the capacity refutation (MAJOR-4) | 2 h | +0.15 | — |
| 5 | Expand Related Work and §4.1–4.3 (MAJOR-5) | 6 h | +0.10 | — |
| 6 | Moderate §4.5 claims to n=12 | 30 min | +0.05 | — |
| 7 | Benign-pool contamination sensitivity (Reviewer C) | 3 h | +0.05 | — |

### Research investment decision

**Spend ~20 more hours here, then stop.** Items 1–6 make this a credible Q1 submission. Item 7 is
worth doing only if a reviewer asks. A third paper in this line would hit diminishing returns for
course-based MS admission, where letters and coursework outrank paper count.

### Dated plan

- **16–18 Aug** — items 1–4 (blockers plus the interval)
- **19–22 Aug** — item 5 (expansion), item 6 (claim moderation)
- **23 Aug** — full read-through, `check_numbers.py`, figure inspection
- **25 Aug** — arXiv preprint posted, listable from this date
- **early Sept** — submit to Computers & Security
- **Nov–Dec 2026** — CV lists preprint + "under review at Computers & Security"
