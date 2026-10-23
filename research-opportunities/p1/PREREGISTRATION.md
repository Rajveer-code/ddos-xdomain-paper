# P-1 Pre-Registration — *Hiding in the Shift*

**Committed before any attack code exists.** This file fixes the threat model, the frozen
experimental choices with concrete numbers, the definition of a successful attack, the
metrics, and the falsifiers. Nothing after this commit may change a frozen choice without a
dated amendment appended to Section 8 of this file.

- **Author of record:** Rajveer Singh Pall (sole author).
- **Prepared / committed:** 2026-10-22.
- **Builds on:** P11 (*Confidently Wrong* / this repository's cross-network DoS study).
- **Master plan:** `research-opportunities/P1_MASTER_PLAN.md` (the governing spec).
- **Status at commit:** Phase 0 complete. Phases 1–5 deferred to 2026-11-21+ per master-plan
  Section 10 (GRE outranks this project until 2026-11-20).

**Ethics / authorized-use statement.** This is defensive security research under the standard
adversarial-ML evaluation paradigm (Carlini et al. 2019; Apruzzese et al. 2022; PANTS, USENIX
Security 2025). The author red-teams **his own** detector, trained on public offline datasets
he already holds, to measure a blind spot in its label-free monitoring and then build a
monitor that closes it. No third-party or production system is probed. All data is public and
offline (the `dhoogla` Kaggle NetFlow v2 mirrors — flow feature vectors, not pcaps). All
traffic manipulation is synthetic and confined to these local datasets. The whole main study
therefore lives in a **constrained feature space**; no wire-realizability is claimed unless the
optional Phase 1-R check actually produces wire-valid flows for the families it covers.

---

## 1. The question (frozen)

After a flow-based DoS detector is moved to an independently captured network (P11's exact
cross-network setting), can an adversary operating under stated, traffic-plausible feature
constraints produce malicious flows that the detector misclassifies as benign **and scores with
high confidence**, so that label-free monitors (ATC, mean-confidence drop, KS, A-distance,
per-feature Wasserstein) do not flag the degradation — and does monitoring the features the
adversary cannot freely set restore the warning?

The contribution is the **joint** object: high-confidence misses + the quiet monitor + the
independent-testbed shift + a monitor-side defense that is *tested* rather than assumed. Plain
NIDS evasion and plain "ATC can be fooled" are each already in the literature (Section 2); the
combination is not.

---

## 2. Where this sits in the literature (verified 2026-10-22)

All seven works were confirmed to exist via adversarial search on 2026-10-22. URLs are
resolvable. Where only an abstract/highlights were retrievable, the row says so and the claim
is marked UNVERIFIED — it must be re-read from the full text before the paper's related-work
section is written.

| # | Work (URL) | Setting | What it establishes | What it leaves open (the wedge) | Full text read? |
|---|---|---|---|---|---|
| 1 | **Ahmed et al., "The Dashboard Says 'Perfect'"**, Frontiers in AI 2026, DOI [10.3389/frai.2026.1928858](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1928858/full) | Label-free monitoring + TTA under a natural one-year temporal shift; CIC-IDS2017↔CSE-CIC-IDS2018, 7 classes, 77 shared features; 16 method variants, both directions | No evaluated variant beats the unadapted source model in both directions; structural failure modes formalized (Props 1–2). An **audit of benign temporal shift** of label-free monitors. | It is **not an adversary** who deliberately steers flows into the high-confidence-benign region under constraints, and not the independent-testbed NetFlow quartet. **Closest paper; cite as motivation; state the delta precisely.** | Abstract + intro only — re-read before writing |
| 2 | **Gnanaratna et al. (Kingston), "Adaptive and Uncertainty-Aware Intrusion Detection with Hybrid Meta-learning Under Proxy-Adversarial Exposure"**, SecureComm 2026, LNICST 705, pp. 74–88, [Springer](https://link.springer.com/book/10.1007/978-3-032-32767-3) | Uncertainty-aware IDS; confidence deferral + meta-learner; proxy adversary in feature space; cross-dataset | A deferral IDS can be *hardened* against a proxy adversary under shift (per title; details UNVERIFIED) | Their adversary is a training-time proxy for robustification; the monitor is the thing being **improved**, not **probed**. Not a measurement of HCMR at a fixed benign-review budget. | **UNVERIFIED** — abstract not retrievable; re-read full chapter before citing specifics |
| 3 | **Jin & Apostolaki, "Robustifying ML-powered Network Classifiers with PANTS"**, USENIX Security 2025, arXiv [2409.04691](https://arxiv.org/abs/2409.04691) | White-box realizable traffic adversarial samples via AML+SMT, then adversarial training | Realizable packet-sequence attacks against MNCs; ~70.33% of research classifiers vulnerable; 70%/2× better than Amoeba/BAP; code + artifact | Classifier-only, **no confidence-monitor system**; not framed around high-confidence misses or quiet-monitor failure; general traffic classification, not cross-testbed DoS transfer. **Borrow its constraint/SMT discipline; do not duplicate its goal.** | Abstract + blog; skim arXiv HTML before writing |
| 4 | **"PAVE: a protocol-validity-aware framework…"**, IoT NIDS, ScienceDirect [S2667295226000450](https://www.sciencedirect.com/science/article/pii/S2667295226000450) | Checks whether feature-space attacks map to valid CAN/MQTT/IP artifacts; 3 IoT datasets, 5 architectures, 6 defenses | Standard FGSM/PGD/Square examples are **0–3% valid** on the wire; feature-space vulnerability is overstated | **The main threat to the realism claim.** A naive feature-space attack is not credible. Phase 1's constraint model + Phase 1-R realism gate exist to answer PAVE directly. | Highlights + abstract only |
| 5a | **Apruzzese et al., "Modeling Realistic Adversarial Attacks against NIDS"**, DTRAP 2022, arXiv [2106.09380](https://arxiv.org/abs/2106.09380) | Realistic attacker-capability model | Most literature threat models are unrealistic (full knowledge / free interaction); gives the capability model to adopt | Not about confidence monitors or cross-testbed transfer. **Use its capability model as the basis of Section 3.** | Abstract; read PDF for capability taxonomy before writing |
| 5b | **Merzouk et al., "Investigating the practicality of adversarial evasion attacks on NIDS"**, Annals of Telecom. 2022, DOI [10.1007/s12243-022-00910-1](https://link.springer.com/article/10.1007/s12243-022-00910-1) | Four feature-validity criteria from inspecting generated examples | The four criteria: **value ranges; binary values; multiple-category membership; semantic relations** | Not about monitors/transfer. **Adopt the four criteria as the constraint spec (Section 3.4).** | Abstract confirms the four criteria |
| 6 | **elShehaby & Matrawy, SoK on evasion practicality**, arXiv [2306.05494](https://arxiv.org/abs/2306.05494) (v4, Oct 2025) | Surveys NIDS evasion practicality, esp. dynamic/retrained detectors | Many published evasion results do not survive functionality + practicality checks; dynamic detectors resist | **The honesty anchor.** Pre-empt it: report functional validity and treat impracticality as a possible finding. | Abstract/refs only; read before writing |
| 7 | **Garg et al., "Leveraging Unlabeled Data to Predict OOD Performance" (ATC)**, ICLR 2022, arXiv [2201.04234](https://arxiv.org/abs/2201.04234) | Average Thresholded Confidence for label-free accuracy estimation | The monitor P-1 probes; already implemented in `src/divergence.py::confidence_scores` | **Not adversarial.** We stress-test it, not propose it. Theory: accuracy estimation under shift is as hard as finding the optimal predictor — so it rests on shift assumptions an adversary can break. | Abstract + method confirmed |

### Gate 0 — novelty (PASS)

No work above measures **adversarial high-confidence false negatives against the joint
detector-plus-label-free-monitor system, under cross-testbed distribution shift, with a stated
traffic-plausibility constraint model, together with a monitor-side defense evaluated for both
security gain and false-alarm cost.** Row 1 (Ahmed et al.) is the closest and is a *benign*-shift
audit; rows 3–6 are classifier-only or realism-only; rows 2 and 7 concern the monitor as a thing
to improve or propose, not to adversarially probe.

**One-sentence delta vs. the closest paper (Ahmed et al.):** *Ahmed et al. audits whether label-free
monitors survive a benign one-year temporal drift and finds they do not; P-1 introduces an
adaptive adversary who, under stated traffic-plausibility constraints, deliberately steers
malicious flows into the high-confidence-benign region across independently built testbeds, and
asks whether the same monitors stay silent and whether watching the low-controllability features
restores the warning.*

**Defensible novelty claim (keep "to our knowledge"; cite rows 1–7 in the same paragraph):** *To
our knowledge, this is the first measurement of adversarial high-confidence false negatives
against the joint detector-plus-label-free-monitor system under cross-testbed distribution shift
and stated traffic-plausibility constraints, together with a monitor-side defense evaluated for
both security gain and false-alarm cost.*

If re-reading any full text in Phase 5 reveals the joint object already done, **narrow or switch
to the fallback (master-plan Section 9); do not force it.**

---

## 3. Threat model (frozen)

**Goal of the adversary.** Get a DoS/DDoS flow scored benign by the deployed detector, with model
confidence at or above the detector's automatic-acceptance threshold `τ_accept` (so a
confidence/ATC monitor does not escalate it), on a target network the detector was not trained on.

**Knowledge.**
- *Primary (realistic) setting:* **grey-box, score-only.** The adversary knows the public NetFlow
  v2 feature schema and can query the deployed model's score for a candidate flow up to a bounded
  number of times, with no gradients. Matches Apruzzese's capability model for a deployed service.
- *Ablation (upper bound):* **white-box** (gradients available), reported as a worst case and
  labelled as such. A result that needs white-box is weaker; the paper will say so (falsifier
  F-white-box-only).

**Capability — the three control classes (hypothesized from mechanism; measured in Phase 1).**
The partition below is derived from the attack mechanism, not convenience, over the 39 shared
NetFlow v2 features (`src/features.py::NETFLOW_TAXONOMY`). Phase 1 step 5 measures the
controllability R² of every indirectly-influenced feature from the directly-controllable ones and
**revises this partition on evidence**; the lists here are the pre-stated hypothesis.

- **Directly controllable** (attacker sets by choosing how to send): `IN_BYTES`, `IN_PKTS`,
  `SRC_TO_DST_SECOND_BYTES`, `SRC_TO_DST_AVG_THROUGHPUT`, `DURATION_IN`,
  `FLOW_DURATION_MILLISECONDS`, `CLIENT_TCP_FLAGS`, `MIN_IP_PKT_LEN`, `MAX_IP_PKT_LEN`,
  `LONGEST_FLOW_PKT`, `SHORTEST_FLOW_PKT`, and the source-side packet-size bins
  `NUM_PKTS_UP_TO_128_BYTES`, `NUM_PKTS_128_TO_256_BYTES`, `NUM_PKTS_256_TO_512_BYTES`,
  `NUM_PKTS_512_TO_1024_BYTES`, `NUM_PKTS_1024_TO_1514_BYTES`.
- **Indirectly influenced** (a response of the network/victim; the attacker's choices change these,
  but not freely): `OUT_BYTES`, `OUT_PKTS`, `DST_TO_SRC_SECOND_BYTES`, `DST_TO_SRC_AVG_THROUGHPUT`,
  `DURATION_OUT`, `SERVER_TCP_FLAGS`, `TCP_FLAGS` (union of both directions), `TCP_WIN_MAX_IN`,
  `TCP_WIN_MAX_OUT`, `RETRANSMITTED_IN_BYTES`, `RETRANSMITTED_IN_PKTS`, `RETRANSMITTED_OUT_BYTES`,
  `RETRANSMITTED_OUT_PKTS`.
- **Uncontrollable under this threat model** (frozen at the original flow's values): `PROTOCOL`,
  `L7_PROTO`, `MIN_TTL`, `MAX_TTL`, `ICMP_TYPE`, `ICMP_IPV4_TYPE`, `DNS_QUERY_TYPE`,
  `DNS_TTL_ANSWER`, `DNS_QUERY_ID`, `FTP_COMMAND_RET_CODE`.

We do **not** assert the responder-side features are uncontrollable. The weaker, true statement is
pre-registered: under this threat model the attacker sets them only *indirectly*, and Phase 1
measures how much a direct change moves them. The Phase 4 defense rests on "harder to steer",
quantified, not on "impossible".

**Constraints (the feasible set; Merzouk's four criteria made concrete).**
1. **Box.** Each changed feature stays within the empirical **[p1, p99]** range of real DoS flows
   of **that family** in the source data (not an arbitrary ε).
2. **Immutability.** Uncontrollable features frozen at the original flow's values.
3. **Integer / binary.** Packet counts and size-bin counts are integers; flag fields take valid
   flag combinations, not continuous values.
4. **Dependency** (enforced as explicit checks; empirical slacks derived in Phase 1):
   - `MIN_IP_PKT_LEN ≤ IN_BYTES / max(IN_PKTS, 1) ≤ MAX_IP_PKT_LEN`;
   - `IN_BYTES ≥ 20 × IN_PKTS` (minimum IP packet); `OUT_BYTES ≥ 20 × OUT_PKTS`;
   - `MAX_IP_PKT_LEN ≥ MIN_IP_PKT_LEN`; `LONGEST_FLOW_PKT ≥ SHORTEST_FLOW_PKT`;
   - `Σ(NUM_PKTS_* size bins) ≤ IN_PKTS + OUT_PKTS`;
   - `RETRANSMITTED_IN_BYTES ≤ IN_BYTES`, `RETRANSMITTED_IN_PKTS ≤ IN_PKTS` (and OUT analogues);
   - `SRC_TO_DST_SECOND_BYTES` consistent with `IN_BYTES` and the flow duration to within an
     empirical slack band (bytes/sec ≈ bytes / duration).
   A candidate violating any dependency is infeasible and is repaired by `project` (clip to box,
   round integers, repair dependencies, restore immutable features) before scoring.

**Functionality.** The flow must still be a working DoS: it stays inside the [p1, p99] box of real
attack flows of its family on **at least the rate/volume features** and does not collapse to a
benign profile on those. This is what separates "evaded" from "no longer an attack".

**Success of one attack (pre-stated HCMR definition).** A candidate flow is a **high-confidence
miss** iff, after the detector's source-fitted scaler + threshold are applied on the target domain:
(i) the detector predicts **benign** (`P(attack) < fit.threshold`); (ii) model confidence
`max(p, 1−p) ≥ τ_accept`, where `τ_accept` is set on **source-validation** data at the Section 5
operating point (never tuned on target); and (iii) the flow satisfies all constraints above. The
**high-confidence-miss rate (HCMR)** is the fraction of target attack flows for which the search
finds such a candidate within the query budget.

---

## 4. Baseline it operates against (pinned to P11 results)

Both source→target pairs, LightGBM, from `results/matrix_summary.json` key `external`:

| Pair | key | external ROC-AUC | failure mode |
|---|---|---:|---|
| `nf_unsw_nb15 → nf_cse_cic_ids2018` | `nf_unsw_nb15\|nf_cse_cic_ids2018\|LightGBM` | **0.0697** | ranking-dominated (ranking loss 0.928): the model ranks attacks *below* benign on the target |
| `nf_bot_iot → nf_cse_cic_ids2018` | `nf_bot_iot\|nf_cse_cic_ids2018\|LightGBM` | **0.9656** | threshold-dominated (threshold loss 0.4217): ranking survives, operating point is stale |

The first is the most dramatic quiet failure; the second is a genuinely good detector the attack
must beat. In-domain LightGBM ROC-AUC is 0.9977 (UNSW) and 0.9994 (BoT-IoT) — the "99% then fails"
gap P11 documents.

---

## 5. Frozen experimental choices (set in Phase 0; no change without a dated amendment)

- **Pairs.** `nf_unsw_nb15 → nf_cse_cic_ids2018` and `nf_bot_iot → nf_cse_cic_ids2018`. Two pairs,
  chosen for contrast (inverted vs. strong transfer).
- **Models.** **LightGBM** (primary); **LogisticRegression** (low-capacity contrast). Reuse
  `src/pipeline.py::make_models`; no re-tuning on target.
- **τ_accept operating point.** Confidence threshold fixed on **source-validation** data such that
  **≤ 1% of benign source-validation flows fall below it** (a 1% benign-review budget). Report HCMR
  at this point; report sensitivity at a 5% budget as a secondary.
- **Query budget (score-only).** **200 queries per flow** (primary). Report HCMR as a function of
  budget at **{50, 100, 200}**.
- **Target attack flows searched.** Capped per family at **2,000** real target attack flows (or all,
  if fewer), stratified by family; reuse the loader's family labels.
- **Seeds.** `SEEDS = (42, 43, 44, 45, 46)` (reuse `src/config.py`). Seed variance reported
  separately from sampling variance.
- **Monitor battery (thresholds all set on source-validation, at the 1% benign-FPR budget).** ATC
  estimated accuracy; mean-confidence drop; KS test on the score distribution; proxy A-distance;
  per-feature max Wasserstein. All already in `src/divergence.py`. Treated as **candidate signals
  to evaluate**, not established alarms.
- **Primary metric.** HCMR (Section 3), with paired-bootstrap 95% CIs (N ≥ 2000) over flows and
  reported across the 5 seeds.
- **Secondary metrics.** Benign review burden (alerts/hour at the operating point, via
  `src/metrics.py::alerts_per_hour`); plain evasion rate (label flip ignoring confidence); attack
  functional-validity rate; each monitor's alarm rate during successful attacks (did any fire?).
- **Phase 3 gate ("which world").** Continue to a *defense* claim only if, in the score-only
  setting on **at least one pair**, the HCMR bootstrap 95% CI lower bound is **> 0** **and** the
  monitors stay quiet during successful attacks (ATC alarm rate during successful misses ≤ its
  source-validation budget + bootstrap noise). If monitors already fire → report "existing monitors
  suffice" (falsifier F-monitor-already-works). If HCMR CI brackets 0 under constraints → report the
  negative (falsifier F-realism). Record which world **before** Phase 4.
- **Phase 4 defense bar (Gate 4).** The defense is reported as a contribution only if it **reduces
  HCMR by ≥ 10 percentage points (absolute)** at an **added benign-review cost ≤ 2 percentage points**
  above the no-defense monitor budget (i.e. total benign review ≤ 3%). If it clears neither bar,
  report it as a negative ("the obvious responder-side defense does not close the gap at acceptable
  cost") — do not quietly drop it. Both numbers are frozen here.

---

## 6. Metrics-to-results mapping (keyed-number discipline)

Every headline number in the paper will be pinned to a `results/p1/*.json` key and verified by a
`check_numbers`-style script, mirroring `paper/claims.json`. Planned result files:
`results/p1/constraints.json`, `feature_controllability.json`, `monitor_baseline.json`,
`attack_results.json`, `defense_results.json`.

---

## 7. Falsifiers (pre-stated — if these fire, narrow or report negative; none is a failure)

- **F-realism.** If under the score-only threat model with constraints enforced, HCMR on both
  pairs is within bootstrap noise of zero, the honest finding is "monitored cross-network DoS
  detection resists realistic high-confidence evasion" (reproduces + extends the SoK). Keep the
  paper; change the headline. **Do not relax constraints to manufacture an attack.**
- **F-monitor-already-works.** If the existing monitors (ATC etc.) already fire during successful
  evasions, there is no quiet-monitor failure to fix; report "ATC is a usable alarm against this
  adversary" (an interesting contrast with Ahmed et al.'s benign-shift finding).
- **F-no-defense-features.** If Phase 1 finds no low-controllability features (every indirect
  feature is trivially derivable from controllable ones, high R²), there is no responder-side
  defense; report the evasion result alone.
- **F-white-box-only.** If the attack works only white-box, state that the realistic adversary
  cannot do it; the contribution shrinks to a worst-case study. Still publishable, clearly scoped.
- **F-novelty.** Phase 0 or a Phase 5 re-read finds the joint object already done → master-plan
  Section 9 fallback.

The only real failure is a tuned, constraint-relaxed, cherry-picked positive, which would destroy
exactly the credibility the portfolio is built on.

---

## 8. Amendments (append-only; each dated)

**2026-10-22 — pilot execution of Phases 1–5.** The author directed execution ahead of the
Section-10 calendar. Phases 1–5 were first run at **pilot scale**: 3 seeds (42–44) and caps of
50k/class (source), 2,000 (target attack/family), 20k (target benign).

**2026-10-22 (later same day) — full frozen-spec run supersedes the pilot.** The author then
directed the full specification: **5 seeds (42–46), 200k/class source cap, 50k target benign, 2,000
target attack/family, 200-query budget**, and extended the detector set from two to **four models
(LightGBM, LogisticRegression, XGBoost, RandomForest)**. All committed `results/p1/*.json` and the
manuscript reflect this full run; the pilot numbers survive only in git history. `summary_p1.json`'s
`config` block records the full-run values. Findings are qualitatively unchanged from the pilot.

**2026-10-22 — white-box ablation realised as a strong upper bound.** The primary tree-ensemble
and LogisticRegression detectors trained here are scored as deployed services; LightGBM is
non-differentiable, so the pre-registered white-box (gradient) ablation is realised as a
high-budget coordinate-descent search (`evade.py` mode="strong"), an **upper bound** on a
score-only adversary. It is labelled as such and never presented as a gradient attack. (Full-run
result: it adds ≤0.012 HCMR over the score-only search on the saturated cells, but up to +0.047
(XGBoost) and +0.049 (RandomForest) on the strong-transfer BoT-IoT cells — so the distinction does
matter for the headroom cells, though it leaves the dangerous BoT-IoT/LogReg cell unchanged.)

**2026-10-22 — memory-bounded data loading.** On the author's 16 GB machine `src.pipeline.
get_domain` OOMs reading the 17–30M-row parquets, so P-1 loads via `p1common.read_capped`
(pyarrow `iter_batches`, columns-only, two-pass Bernoulli per class). The fit/scale/threshold/
metric logic is unchanged (src primitives). This is an engineering deviation, not a change to a
frozen scientific choice.

**2026-10-22 — Gate 3 interpretation.** The pre-registered Gate 3 asks for non-trivial HCMR **and**
model-based monitors quiet during successful attacks, on ≥1 pair. Pilot result: HCMR is non-trivial
on both pairs; the model-based monitors are quiet specifically for BoT-IoT→CSE-CIC-IDS2018 with
LogisticRegression (alarm 0.0) and loud for LightGBM. The quiet-monitor world therefore exists and
Phase 4 was run; for the loud configs the paper reports F-monitor-already-works. No frozen choice
changed.
