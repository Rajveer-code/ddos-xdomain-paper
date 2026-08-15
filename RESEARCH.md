# RESEARCH.md — Cross-Dataset DDoS Generalization → Publication Strategy

**Date:** 2026-08-15
**Artifact reviewed:** `C:\Users\Asus\Downloads\CrossDataset_DDoS_Colab (2).ipynb` (41 cells)
**Author:** Rajveer Singh Pall (sole author)
**Clock:** acceptances needed before Nov–Dec 2026 (Fall-2027 US MS applications)

---

## 0. Verified state of the artifact

Read the whole notebook. Facts:

| Item | Status |
|---|---|
| `SMOKE_TEST` | **`True`** — every number in the notebook comes from fabricated Gaussian data (200 rows/class, 10 columns) |
| Real results | **Zero.** No Kaggle run has been executed. |
| Pipeline quality | Good. Leakage-safe ordering, dedup-before-split, scaler fit on train only, balanced sample weights, bootstrap CIs (N=2000), 5-fold CV, SHAP, feature-shift, 2 ablations, MANIFEST + zip |
| Outputs | 13 figures + 13 tables + 4 models, all numbered and manifested |
| Honesty discipline | Cell 0 explicitly retracts three fabricated figures from a prior notebook. Keep this. It is the reason this project is salvageable. |

**Implication:** every number currently in the notebook — the 97.8% macro-F1, the 0.0005 gap, the SHAP rankings, the prior-art table row for "THIS WORK" — is plumbing output, not a result. Nothing can be written until `SMOKE_TEST = False` runs.

---

## 1. The blunt problem with the current design

The design is: *train on CIC-DDoS2019, test in-domain, test on CICIDS2017, report the generalization gap.*

That is a **strict subset of already-published work**:

| Prior work | What it did | Why it dominates the current design |
|---|---|---|
| Cantone, Marrone et al. 2024, *On the Cross-Dataset Generalization of ML for NIDS* — arXiv:2402.10974 / IEEE Access | 4 classifiers × 4 datasets (CIC-IDS2017, CSE-CIC-IDS2018, LycoS-IDS2017, LycoS-Unicas-IDS2018), full cross-dataset matrix, near-chance transfer, visualization-based diagnosis of data anomalies, **plus released a new corrected dataset** | More datasets, more pairs, plus a dataset contribution |
| D'hooge et al. 2020, JISA | Cross-evaluation 2017↔2018, near-perfect in-domain → collapse cross-domain | Established the finding 6 years ago |
| *Cross-Dataset Temporal and Semantic Generalization of IDS for the Future Internet*, MDPI Future Internet 18(4):194, 2026 | 4 datasets 2017–2024, 5 models, in-dataset / forward-temporal / enterprise→IoT / dataset-agnostic protocols, ΔF1 ≈ 0.20–0.27 | Same finding, more protocols, published this year |
| *A cross-dataset harmonized IDS framework with statistically validated multi-model learning*, PLOS One 2026 | Feature harmonization + multi-model benchmarking + statistical validation | Owns "harmonization + statistics" framing |
| *Cross-network transferability of AI-based NIDS in heterogeneous IoT*, Computer Networks 2026 | Cross-network transfer, domain-aware calibration discussion | Owns cross-network transfer framing |
| Sarhan et al. 2021, *Towards a Standard Feature Set for NIDS Datasets* (NetFlow-v2, 43 features) | Built NF-*-v2 datasets **specifically so cross-dataset comparison is legitimate** | Makes ad-hoc column intersection look amateur |

**The one-line reviewer rejection you will get as-is:**
> "This replicates a well-established result with fewer datasets, a single attack class, and an ad-hoc feature intersection. No new insight."

**Measuring the gap is table stakes in 2026. It cannot be the contribution.** Everything in §4 exists to give you a contribution.

---

## 2. "Free" — the honest answer

You asked for a conference that costs nothing. State of the world:

| Cost component | Reality |
|---|---|
| **Submission** | Free at every reputable venue (IEEE, ACM, USENIX, Springer, Elsevier). No exceptions worth caring about. |
| **Presenting at a conference** | **Never free.** Every IEEE/ACM/USENIX conference requires ≥1 author to register, or the paper is pulled from proceedings. International student rates are typically several hundred USD. `[VERIFY: exact 2027 rates per venue]` |
| **Publishing in a journal** | **Genuinely free** if you take the subscription (non-open-access) route. Verified: Elsevier *Computers & Security* charges **no APC** under the subscription model; open access is optional at USD 3190. Same structure for *Computer Networks*, *JISA*, IEEE Transactions (TNSM/TIFS/TDSC). |
| **arXiv preprint** | Free, immediate, timestamps priority. Do this regardless. |

So: **there is no free conference.** Anyone telling you otherwise is describing a predatory venue that charges an APC instead, which is worse for admissions than no paper at all.

Two viable zero-rupee paths:
1. **No-APC journal** (Computers & Security / IEEE TNSM) + arXiv preprint. Cost: ₹0. Cost in time: 3–6 months to first decision.
2. **A conference in India** where registration is domestic-rate and travel is a train ticket, with travel grants available.

---

## 3. Recommended venue portfolio

Ranked for: renown × acceptance probability × cost × fits the Nov–Dec 2026 clock.

### Tier 1 — the two moves to actually make

**1a. COMSNETS 2027 — 19th Int'l Conf. on Communication Systems & Networks**
- Bengaluru, India, **5–9 Jan 2027**. Paper deadline **31 Aug 2026** (16 days from today). 8 pages incl. figures/tables, EDAS. `[VERIFY on comsnets.org — the CFP page is JS-rendered and did not fetch cleanly]`
- IEEE proceedings, IEEE Xplore indexed, genuinely well-regarded in networking, runs since 2009.
- **Why it is the best conference fit for you specifically:** domestic registration, negligible travel cost from India, an explicit Travel Grants programme, notification lands ~Oct–Nov 2026 → **before your application deadline**.
- Also has a workshop track (incl. a security/privacy workshop) with later deadlines and higher acceptance if the main track misses.
- Risk: 16 days. Only viable with a scoped contribution (see §5 Option 1).

**1b. Elsevier *Computers & Security* (COSE)**
- Q1, CORE-listed, **zero cost** under the subscription model, and it is *the* journal for NIDS evaluation-methodology work.
- Won't produce an acceptance before Nov 2026, but "under review at Computers & Security" plus a public arXiv preprint is a legitimate and verifiable CV line.
- Alternative of equal standing and equal cost: **IEEE TNSM** (Transactions on Network and Service Management).

### Tier 2 — topically perfect, later cycles

| Venue | Fit | Approx. cycle |
|---|---|---|
| **WTMC** (Int'l Workshop on Traffic Measurements for Cybersecurity, @ IEEE EuroS&P) | *Perfect.* Engelen et al.'s corrected-CICIDS2017 paper was published here. Small, measurement-first, receptive to "your benchmark is broken" papers | WTMC 2026 has passed; WTMC 2027 CFP ~Feb–Mar 2027 `[VERIFY]` |
| **USENIX CSET** (Cyber Security Experimentation and Test) | *Perfect.* Exists specifically for evaluation-methodology critique. Cheap workshop registration | ~Apr–May 2027 `[VERIFY]` |
| **IFIP/IEEE TMA** (Network Traffic Measurement and Analysis) | Strong. Selective, explicitly welcomes work "that challenges conventional wisdom" | TMA 2026 deadline was 27 May 2026; TMA 2027 ~Feb 2027 `[VERIFY]` |
| **MLCS @ ECML-PKDD** (Workshop on ML for CyberSecurity, 8th edition) | Good. High acceptance, Springer proceedings | ~Jun 2027 `[VERIFY]` |
| **RAID** (Int'l Symposium on Research in Attacks, Intrusions and Defenses) | The natural top-tier home. RAID 2026 deadline was 16 Apr 2026; RAID 2027 ~Apr 2027 | Hard. Aim here only with the full §4 Tier-B contribution |

### Tier 3 — fits the clock but weak topical fit

- **IEEE BigData 2026** — deadline **21 Aug 2026**, notification **24 Oct 2026**, Phoenix AZ, 14–17 Dec 2026. Timing is ideal; topical fit is poor (it is a big-data venue, not a security venue) and registration is expensive US-based. Only worth it if COMSNETS is missed.

### Explicitly NOT recommended

- **NeurIPS 2026 workshops.** I pulled the full accepted list (102 workshops, announced 10 Aug 2026). Every single one is LLM / foundation-model / agent / multimodal oriented. **There is no workshop where a tabular flow-based DDoS detector belongs.** Do not waste a submission.
- **ICLR 2027** (deadline 24 Sep 2026) — notification Jan 2027, after your clock, and the ML-methods bar for a tabular gradient-boosting study is not clearable.
- Anything charging an APC to publish.

---

## 4. What to add — tiered

### TIER A — mandatory. Without these it is desk-rejected regardless of venue.

**A1. Run it for real.** `SMOKE_TEST = False`, Kaggle credentials, full run. Nothing below matters until this exists. Save results to JSON so every figure regenerates from disk.

**A2. Replace ad-hoc column intersection with the NetFlow-v2 standard feature set.**
Sarhan et al. 2021 built `NF-UNSW-NB15-v2`, `NF-BoT-IoT-v2`, `NF-ToN-IoT-v2`, `NF-CSE-CIC-IDS2018-v2` — **43 identical NetFlow v9 features across all four**, precisely so cross-dataset claims are legitimate. All are on Kaggle under `dhoogla`, the same publisher your notebook already pulls from.
- Why it matters: your smoke run intersected to 10 features. On real data the intersection is arbitrary, undocumented, and the first thing a reviewer attacks. NetFlow-v2 removes that attack surface entirely.
- Bonus: 4 datasets → **12 ordered transfer pairs**, which is what makes B2 statistically possible.
- Keep the CICFlowMeter 2019→2017 pair as a *secondary* study, framed as "what happens when you do it the way the literature usually does."

**A3. Isolate the label-noise confound.** CICIDS2017 has documented label errors (Engelen et al., WTMC 2021; Lanvin et al., CRiSIS 2022 → LycoS-IDS2017). Run external validation against **both** original and corrected labels. Report how much of the "generalization gap" is actually label error. Your notebook already cites these papers — using them costs one extra run and pre-empts a guaranteed reviewer question.

**A4. Statistics on the gap itself.** Currently you bootstrap each split separately. The *gap* is the estimand — report it with a CI via **paired bootstrap over the two test sets**, plus a permutation test. Run ≥5 seeds and report seed variance separately from sampling variance.

**A5. Bidirectional and full-matrix transfer.** 2019→2017 **and** 2017→2019, plus the full N×N matrix on NetFlow-v2. Transfer asymmetry is itself a finding and costs one loop.

**A6. Attack-family decomposition.** Dataset-level numbers hide the mechanism. Report per-family recall under transfer:
- volumetric floods (SYN, UDP, LOIC)
- reflection/amplification (DNS, LDAP, MSSQL, NTP, SSDP, NetBIOS, SNMP)
- low-rate / application-layer (Slowloris, Slowhttptest, GoldenEye, Hulk)

Prediction worth testing: volumetric transfers, low-rate does not. If true, that single table is more informative than every aggregate number in the paper.

### TIER B — the actual contribution. Pick two and do them properly.

**B1. The rate-feature indictment.** *(cheapest, most quotable — do this one)*

Hypothesis: features encoding **testbed capacity** rather than attack semantics — `Flow Bytes/s`, `Flow Packets/s`, IAT statistics, duration — are what drive in-domain accuracy and destroy transfer.

Experiment:
1. Partition features into semantic classes: `{rate/throughput, timing/IAT, size/volume, header/protocol, flag/behavioural}`.
2. Leave-one-class-out training, and one-class-only training.
3. Plot in-domain vs external on the same axes → an explicit **transfer-cost curve**.
4. Add a **quantile/rank-transform** variant against the current MinMaxScaler. MinMax is the wrong transform for heavy-tailed rate features under domain shift, and this ablation is directly on-thesis.

Target claim: *"Removing the features that dominate in-domain importance costs A points in-domain and buys back B points externally."* If B > A, that is a direct indictment of standard practice in this literature — a quotable, defensible, mechanistic result. Cost: ~1 day of compute.

**B2. Label-free generalization-gap forecasting.** *(most novel — no NIDS-specific prior work found)*

For each ordered transfer pair, compute unsupervised source↔target divergence **using no target labels**:
- proxy A-distance (train a domain discriminator source-vs-target, `d_A = 2(1 − 2ε)`)
- summed per-feature Wasserstein-1
- MMD
- confidence-based proxies: mean max-probability on target, ATC / agreement score

Then regress the observed macro-F1 drop on each. Report Spearman ρ with CI, and **leave-one-pair-out predictive error** — i.e. can you predict a held-out pair's degradation?

Payoff: an operator can estimate how badly a detector will degrade on their network *before* deployment, with **zero labels**. Practical, novel, and cheap. Requires A2/A5 for enough pairs.

**B3. Ranking-loss vs threshold-loss decomposition.** *(strong, partly contested — position carefully)*

Decompose the gap into:
- **ranking loss:** ΔROC-AUC, ΔPR-AUC
- **threshold/calibration loss:** ΔF1 at the *in-domain* threshold vs ΔF1 at the *target-optimal* threshold

plus ECE, Brier, and reliability diagrams in both domains. Then show **unlabeled recalibration**: choose the threshold from target *benign* traffic quantiles only (an operator has benign traffic; they do not have labels) and report recovered F1.

If ΔAUC ≪ ΔF1 — which is the common pattern — the headline becomes: *"cross-dataset NIDS failure is a threshold failure, not a representation failure, and it is fixable without labels."* That reframes the literature.

⚠ **Contested space.** A 2026 preprint (*The Evaluation Protocol Is the Hidden Variable: A Drift-Aware Re-Examination of Flow-Based Intrusion Detection Benchmarks*) already uses the term "threshold-ranking divergence", and TechScience *JCS* 2026 published a cross-dataset Transformer-IDS with calibration + AUC optimization. You **must** cite both and differentiate: they address temporal drift / transformer architectures; you address cross-dataset shift with tree ensembles plus benign-quantile recalibration under an explicit label budget.

**B4. The label-budget curve.** *(practical closer)*

k labeled target flows, k ∈ {0, 10, 50, 100, 500, 1000} → re-threshold and fine-tune. *"How many labels buy back the gap?"*
Baselines: CORAL, DANN. Note these are **baselines, not your novelty** — domain-invariant NIDS is already published (DI-NIDS, 2022; *From Zero-Shot ML to Zero-Day Attack Detection*, 2021). Do not frame domain adaptation as new.

**Recommended spine:** B1 + B2 as the contribution, B3 as the reframing section, B4 as the "so what do I actually do" closer. That is a complete paper.

### TIER C — rigor that visibly moves reviewers

- **C1. Reproducibility artifact.** Pinned `requirements.txt`, one-command runner, fixed seeds, results JSON, every figure regenerated from JSON, Zenodo DOI, anonymized GitHub mirror for double-blind venues.
- **C2. Arp et al. pitfall table.** You already cite *Dos and Don'ts of Machine Learning in Computer Security* (USENIX Sec 2022). Turn it into an explicit table: each of their 10 pitfalls × how your protocol avoids it. Security reviewers reward this heavily and it costs one table.
- **C3. Threats to validity section.** Synthetic-testbed traffic, benign-traffic homogeneity, CICFlowMeter extraction bugs, label errors, and — importantly — the artificial base rate you create by filtering non-DDoS attacks out of CICIDS2017.
- **C4. SOC-meaningful operating points.** FPR@95%TPR and alerts/hour at a realistic base rate, not just balanced-test-set F1. Address the base-rate fallacy (Axelsson 2000) explicitly; it is the classic NIDS reviewer trap.
- **C5. Fix the prior-art table.** Cell 36 mixes MCC, accuracy, and the phrase "near-perfect" in one comparison table. That is reviewer bait. Standardize the metric or convert it to a narrative paragraph.
- **C6. Multiclass section must earn its place.** Keep it only if it supports the attack-family transfer story (A6); otherwise cut.

### Bugs and risks found in the current code

| Location | Issue | Action |
|---|---|---|
| `DDOS_MARKERS`, cell 4 | Substring matching on labels (`"dos"`, `"dns"`, `"syn"`) is fragile across datasets | Print and assert the full label→binary mapping table; include it in the appendix |
| Cell 8 | Filtering CICIDS2017 down to benign + DDoS **changes the base rate artificially** | Report it; ablate by keeping all 2017 attacks and reporting FPR on non-DDoS attacks separately |
| `SAMPLE_N_PER_CLASS = 20_000` | Caps discard data and shift class ratios, which moves PR-AUC and F1 | Report the discarded fraction; run full-data at least once |
| Cell 10 | MinMaxScaler + clip to [0,1] on heavy-tailed rate features | Keep the clipping ablation (currently null-effect on smoke data — will not be null on real data); add quantile transform as a variant (feeds B1) |
| Cell 30 | mean\|SHAP\| compared across domains with different base rates is not apples-to-apples | Note the caveat, or compare rank correlation instead of magnitude |

---

## 5. Two plans

### Option 1 — aggressive, hits the clock
Target **COMSNETS 2027**, deadline **31 Aug 2026**, 8 pages.
Scope: **A1 + A2 + A5 + A6 + B1**, with C2 and C4.
- Aug 16–19: real run, CIC pair + NetFlow-v2 quartet (A1, A2)
- Aug 20–22: bidirectional matrix + attack-family decomposition (A5, A6)
- Aug 23–25: rate-feature ablation and transfer-cost curve (B1)
- Aug 26–30: write 8 pages, figures, pitfall table
- Aug 31: submit. arXiv the same day.

Honest risk: 16 days, sole author, from zero real results. Achievable **only** because the pipeline already exists and is well built. If the real run reveals something unexpected (likely — the smoke numbers tell you nothing), the schedule breaks. Decide by ~Aug 22 whether to continue or fall back.

### Option 2 — stronger paper, later placement
Full **B1 + B2 + B3 + B4** → **Computers & Security** (₹0) or **IEEE TNSM**, submit ~Oct 2026. arXiv preprint immediately regardless.

### Recommended: both
Ship the scoped 8-page COMSNETS version now; extend it into the journal version with B2/B3/B4 afterwards. Conference-to-journal extension is standard practice — `[VERIFY COMSNETS/IEEE policy: normally requires ≥30% new material]`.

---

## 6. The "unrejectable" checklist

A reviewer cannot reject this if all of the following hold:

- [ ] Every number traces to a results JSON produced by a seeded, one-command run
- [ ] Feature harmonization uses a published standard (NetFlow-v2), not an ad-hoc intersection
- [ ] ≥3 datasets, ≥6 ordered transfer pairs, both directions
- [ ] Gap reported with a paired-bootstrap CI, over ≥5 seeds
- [ ] Label-noise confound isolated with corrected labels
- [ ] A mechanism is demonstrated, not just observed (B1)
- [ ] Something actionable is delivered that did not exist before (B2 or B3)
- [ ] Arp et al. pitfall table present
- [ ] Threats-to-validity section names the base-rate manipulation honestly
- [ ] Public, seeded, DOI'd artifact
- [ ] Zero unflagged placeholders

---

## 7. Sources

- Cantone et al., *On the Cross-Dataset Generalization of Machine Learning for Network Intrusion Detection* — https://arxiv.org/abs/2402.10974
- Sarhan et al., *Towards a Standard Feature Set for NIDS Datasets* — https://arxiv.org/pdf/2101.11315 · datasets: https://staff.itee.uq.edu.au/marius/NIDS_datasets/
- *Cross-Dataset Temporal and Semantic Generalization of IDS for the Future Internet*, MDPI Future Internet 18(4):194 — https://www.mdpi.com/1999-5903/18/4/194
- *A cross-dataset harmonized IDS framework*, PLOS One — https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0346982
- *Cross-network transferability of AI-based NIDS in heterogeneous IoT*, Computer Networks — https://www.sciencedirect.com/science/article/pii/S1389128626004469
- *Cross-Dataset Transformer-IDS with Calibration and AUC Optimization*, TechScience JCS — https://www.techscience.com/JCS/v7n1/64671/html
- *The Evaluation Protocol Is the Hidden Variable* — https://www.researchgate.net/publication/406911132
- *DI-NIDS: Domain Invariant Network Intrusion Detection System* — https://arxiv.org/pdf/2210.08252
- COMSNETS 2027 CFP — https://www.comsnets.org/call_for_papers.html
- NeurIPS 2026 workshop list — https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/
- IEEE BigData 2026 dates — https://bigdataieee.org/BigData2026/important-dates/
- WTMC — https://wtmc.info/index.html
- IFIP/IEEE TMA — https://tma.ifip.org/
- MLCS @ ECML-PKDD — https://mlcs.lasige.di.fc.ul.pt/
- RAID — https://raid2026.org/call.html
- Computers & Security APC policy — https://www.sciencedirect.com/journal/computers-and-security
