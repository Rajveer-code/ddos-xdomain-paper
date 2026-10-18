# CLAUDE.md — ddos_xdomain_paper

Project-level rules. Extends the global `~/.claude/CLAUDE.md`; the global file wins on conflict.

## What this is

A sole-author research study on cross-dataset generalisation of flow-based DDoS detectors.
Target (decided 2026-10-18): **Computer Networks (Elsevier), subscription route (no fee)**,
plus an arXiv preprint (primary cs.LG). Fallbacks: TMLR, then IEEE TNSM (needs <=16 pp).
Readiness audit and fix plan: `PLAN_audit_fixes.md` (gitignored).

**Not Computers & Security** (Elsevier) — ruled out 2026-08-22. COSE instituted a moratorium
on AI/ML-as-significant-component submissions in early 2024; this paper trains four ML model
families, so it falls inside the exclusion, not near its edge. See `RESEARCH.md` §3 1b.

TNSM mechanics that constrain the manuscript: two-column IEEE Transactions format, 16-page
hard ceiling (10 free + up to 6 paid pages at $220/page, waivable for unfunded academic
authors), 75–200 word abstract, mandatory related-work section. The manuscript is currently
25 pages single-column — compression is a submission requirement, not a style preference.

Strategy, venue analysis and the full contribution plan live in [`RESEARCH.md`](RESEARCH.md).
Task state lives in `PLAN_phase*.md` (gitignored — working state, not deliverable).

## PATHS

```
PROJECT = D:\Projects\ddos_xdomain_paper
DATA    = D:\Projects\ddos_xdomain_paper\data        # gitignored, Kaggle downloads
RESULTS = D:\Projects\ddos_xdomain_paper\results     # JSON, committed
FIGURES = D:\Projects\ddos_xdomain_paper\figures     # PNG 300dpi, gitignored
PAPER   = D:\Projects\ddos_xdomain_paper\paper
```

Never hardcode paths outside `src/config.py`.

## Commands

```bash
pip install -r requirements.txt
python scripts/download_data.py        # fetch Kaggle mirrors into data/
python scripts/run_all.py --dry-run    # full pipeline in order, with the settings that ran
python scripts/check_numbers.py        # keyed claims (paper/claims.json) + loose literal scan
python scripts/build_pdf.py            # single-column proof from paper/manuscript.md
```

## Environment notes

- Windows 11, Python 3.13.12 (miniconda), RTX 4060 8 GB, i7-13650HX.
- **TLS:** Avast Web Shield MITMs HTTPS with a non-RFC5280-strict local root, which breaks
  every Python HTTPS call. `src/netfix.py` fixes this by trusting certifi + the local AV root
  and clearing `VERIFY_X509_STRICT` only. Chain, signature, expiry and hostname verification
  stay ON. **Import `netfix` before any network call.** Never disable verification instead.
- Kaggle credentials come from `~/.kaggle/kaggle.json`. Never copy them into the repo.

## Project rules

1. **No number without a run.** Every figure and table regenerates from `results/*.json`.
   No metric is written into the manuscript by hand. Unknowns are
   `[PLACEHOLDER: what is needed + how to get it]`, never a plausible guess.
2. **Seeds fixed, configs at the top.** One experiment = one entry point, logging what ran
   with which config to where.
3. **Leakage discipline.** De-duplicate before splitting, split before scaling, fit scalers
   on source-train only. No SMOTE. Document every filter that changes a class ratio.
4. **The gap is the estimand.** Report it with a paired-bootstrap CI over multiple seeds —
   not two separately-bootstrapped point estimates.
5. **Commits:** conventional (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `exp:`),
   small and single-purpose, one per task. **No AI attribution of any kind** — sole author is
   Rajveer Singh Pall. Push runs the `ship-github` checklist.
6. **Honesty over polish.** If a result is null, weak, or contradicts the hypothesis, that
   goes in the paper. The prior notebook's fabricated figures are why this project exists.
