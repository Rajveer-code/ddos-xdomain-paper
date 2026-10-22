# P-1 Master Plan — *Hiding in the Shift*

**An executable plan for one autonomous assistant (Sonnet-class) to carry out with no human in the loop.**

Author of record: Rajveer Singh Pall. Prepared 2026-10-22. Builds on P11 (*Confidently Wrong*),
this repository. Everything here is defensive security research: the author red-teams **his own**
detector to measure a blind spot in its monitoring, then builds a monitor that closes it. This is
the standard adversarial-ML evaluation paradigm (Carlini et al. 2019; Apruzzese et al. 2022; PANTS,
USENIX Security 2025). No third-party or production system is targeted. All data is public and
offline; all traffic manipulation is synthetic and confined to local datasets the author already
has.

---

## 0. How to use this document

You are an autonomous coding assistant. Read this whole file first. Then execute Section 6 phase by
phase. Each phase ends in a **gate** with numeric pass/fail criteria you evaluate yourself; if a
gate fails, follow its branch (narrow, or fall back) rather than forcing the idea. Do not skip the
pre-registration step in Phase 0 — it is committed to git before any result exists, and the paper's
credibility depends on it.

Three rules hold throughout, and they override any instinct to make the result look good:

1. **Report negatives.** If the attack does not work under realistic constraints, or the defense
   does not help, that is the finding. It is publishable and it is honest. The whole portfolio's
   identity is "the reported number does not mean what people think"; a forced positive here would
   betray exactly that.
2. **Never widen a claim past its evidence.** Everything operates in a **constrained feature
   space** (Section 3). You are not claiming wire-realizable packet attacks unless Phase 1's
   optional realism check actually produces them. Say "feature-space, domain-constrained" wherever
   that is what was done.
3. **Pre-state before you look.** Metrics, thresholds, and the definition of a successful attack
   are fixed in Phase 0 and committed, before the main experiment runs.

Deliverables, in priority order: (a) a committed pre-registration; (b) a reproducible pilot with
one honest headline number; (c) a short paper draft; (d) three SOP-ready sentences (Section 8). If
time runs out, (a)+(b)+(d) alone are a success — they are what the SOP needs.

---

## 1. The question, in one line

After a flow-based DoS detector is moved to an independently captured network (P11's exact
cross-network setting), can an adversary operating under stated, traffic-plausible feature
constraints produce malicious flows that the detector misclassifies as benign **and scores with
high confidence**, so that label-free monitors (ATC, confidence, drift tests) do not flag the
degradation — and does monitoring the features the adversary cannot freely set restore the warning?

The emphasis is the whole contribution. Plain evasion of a NIDS is a crowded, largely solved topic.
Plain "ATC can be fooled" is shown for a degenerate detector by Bikdeli et al.'s *Dashboard Says
Perfect*. The gap is the **joint** object: high-confidence misses + the quiet monitor + the
independent-testbed shift + a defense that is tested rather than assumed.

---

## 2. Where this sits in the literature (verified 2026-10-22)

Read the full text of every row before writing the paper's related-work section. Each was confirmed
to exist this session via search; full texts were **not** all read here, so re-read them. Do not
claim novelty for the combination without filling this table from the actual papers.

| Work | Setting | What it establishes | What it leaves open (your wedge) |
|---|---|---|---|
| **Bikdeli/"The Dashboard Says Perfect"**, Frontiers in AI 2026 (`frai.2026.1928858`) | Label-free monitoring + TTA under temporal shift, CIC-IDS2017↔2018 | ATC reports accuracy 1.000 for a detector with 0 recall on every attack family; label-free selectors pick the wrong model 10–12/12; conformal coverage falls below nominal | It is an **audit of benign temporal shift**, not an **adversary** who deliberately steers flows into the high-confidence-benign region under constraints, and not the independent-testbed quartet. This is the closest paper; cite it as motivation and state the delta precisely. |
| **Kingston 2026** (Gnanaratna et al.), uncertainty-aware IDS under proxy-adversarial exposure | Confidence-based deferral + few-shot meta-learner + cross-dataset (CIC-IDS2017/2018), proxy adversary in feature space | A deferral system can be hardened against a proxy adversary under shift | Their adversary is a training-time proxy for robustification; it is not a measurement of **how many high-confidence misses an adaptive evader can buy at a fixed benign review budget**, and the monitor is the thing being improved, not the thing being probed. |
| **PANTS**, USENIX Security 2025 (Jin & Apostolaki) | White-box realizable traffic adversarial samples via PGD/ZOO + SMT, then adversarial training | Realizable packet-sequence attacks against traffic classifiers; +52.7% robustness via adversarial training; code + Zenodo artifact | Classifier-only, not a classifier+confidence-monitor system; not framed around high-confidence misses or the quiet-monitor failure; general traffic classification, not the cross-testbed DoS transfer setting. Borrow its **constraint/SMT discipline**; do not duplicate its goal. |
| **PAVE** (protocol-validity-aware robustness eval, IoT NIDS, 2026) | Checks whether feature-space attacks map to valid CAN/MQTT/IP artifacts | Standard FGSM/PGD/Square examples are 0–3% valid on the wire; feature-space vulnerability is overstated | This is the **main threat to your realism claim**. It means a naive feature-space attack is not credible. Your Phase 1 constraint model and Phase 1-R realism gate exist to answer PAVE directly. |
| **Apruzzese et al.**, *Modeling Realistic Adversarial Attacks against NIDS*, DTRAP 2022 (`2106.09380`); **Merzouk et al.** 2022 (four validity criteria) | Realistic attacker capability model; value-range/binary/category/semantic constraints for valid network feature vectors | Most literature threat models are unrealistic; gives the capability model and the four feature-validity criteria you must adopt | Not about confidence monitors or cross-testbed transfer. Use their **capability model and validity criteria** as your constraint spec; cite as the basis of Section 3. |
| **"Evasion Attacks Remain Impractical…"** SoK (`2306.05494`) | Surveys NIDS evasion practicality, esp. dynamic/retrained detectors | Many published evasion results do not survive functionality + practicality checks; dynamic detectors resist | Your honesty anchor. Pre-empt it: report functional validity and treat impracticality as a possible finding. |
| **Garg et al.**, ATC, ICLR 2022 | Average Thresholded Confidence for label-free accuracy estimation | The monitor you probe; already implemented in `src/divergence.py` | Not adversarial. You are stress-testing it, not proposing it. |

**The defensible one-sentence novelty claim** (keep "to our knowledge", cite the six rows above in
the same paragraph): *To our knowledge, this is the first measurement of adversarial high-confidence
false negatives against the joint detector-plus-label-free-monitor system under cross-testbed
distribution shift and stated traffic-plausibility constraints, together with a monitor-side defense
evaluated for both security gain and false-alarm cost.*

If Phase 0 literature reading finds a paper that already does this joint object in this setting,
**narrow or switch to the fallback (Section 9), do not force it.**

---

## 3. Threat model — fix this before any code

State all of this in the paper's threat-model section and in the pre-registration. Vague threat
models are the single most common reason NIDS adversarial papers are rejected.

**Goal of the adversary.** Get a DoS/DDoS flow scored benign by the deployed detector, with model
confidence at or above the detector's automatic-acceptance threshold (so a confidence/ATC monitor
does not escalate it), on a target network the detector was not trained on.

**Knowledge.** Grey-box, stated as the realistic default and ablated:
- *Primary setting:* the adversary knows the feature schema (public — NetFlow v2 is a published
  standard) and can query the deployed model's score for a candidate flow a bounded number of times
  (score-only, no gradients). This is the realistic "the model is a deployed service" case and
  matches Apruzzese's capability model.
- *Ablation (upper bound):* white-box (gradients available). Report it as a worst case, labelled as
  such. A result that needs white-box is weaker; say so.

**Capability — what the adversary may change, and by how much.** This is the heart of the realism
defense against PAVE. Partition the 39 shared NetFlow v2 features (taxonomy already in
`src/features.py`) into three control classes, and **derive the partition from the attack mechanism,
not from convenience**:
- **Directly controllable** (the attacker sets these by choosing how to send): source→dst packet
  sizes/counts within the DoS tool's working range, inter-arrival/duration within rate limits,
  source-side TCP flags consistent with the protocol. Candidates: `IN_BYTES`, `IN_PKTS`,
  `NUM_PKTS_*` (source-side), `SRC_TO_DST_*`, `DURATION_IN`, `CLIENT_TCP_FLAGS`, parts of
  `FLOW_DURATION_MILLISECONDS`.
- **Indirectly influenced** (the attacker's choices change these, but not freely — they are a
  response of the network/victim): `DST_TO_SRC_*`, `OUT_BYTES`, `OUT_PKTS`, `SERVER_TCP_FLAGS`,
  `RETRANSMITTED_OUT_*`, `TCP_WIN_MAX_OUT`, round-trip-dependent timing.
- **Uncontrollable under this threat model**: protocol identity where the attack needs a specific
  protocol (`PROTOCOL`, `L7_PROTO` for a given attack family), `MIN_TTL`/`MAX_TTL` set by path,
  `DNS_*` fields when not a DNS attack.

**Do not assert the responder-side features are uncontrollable. Prove the weaker, true statement:**
under this threat model the attacker sets them only *indirectly*, and Phase 1 measures how much an
attacker's direct changes move them (via feature-dependency analysis on real flows). The defense in
Phase 4 then rests on "harder for the attacker to steer", quantified, not on "impossible".

**Constraints (the feasible set the search optimizes within).** Adopt Merzouk's four criteria,
made concrete per feature:
1. **Box**: each changed feature stays within the empirical [p1, p99] range of **real DoS flows of
   that family** in the source data (not arbitrary ε).
2. **Immutability**: uncontrollable features are frozen at the original flow's values.
3. **Integer/binary**: packet counts integer, flag fields valid flag combinations, not continuous.
4. **Dependency**: enforce the relations that must hold among features of one flow — e.g.
   `IN_BYTES ≥ IN_PKTS × MIN_IP_PKT_LEN`, `LONGEST_FLOW_PKT ≥ SHORTEST_FLOW_PKT`, bytes/sec
   consistent with bytes and duration, packet-size-bin counts sum to `IN_PKTS`. Encode these as
   explicit checks; a candidate violating any is infeasible.

**Functionality.** The flow must still represent a working DoS: enough volume/rate to be an attack.
Operationalize as: the changed flow stays inside the convex hull (or [p1,p99] box) of real attack
flows of its family on **at least the rate/volume features**, and does not collapse to a benign
profile on those. State this explicitly; it is what separates "evaded" from "no longer an attack".

**Success of one attack (pre-stated).** A candidate flow counts as a **high-confidence miss** iff,
after the detector's source-fitted scaler + threshold are applied on the target domain: (i) detector
predicts benign; (ii) model confidence `max(p, 1−p) ≥ τ_accept`, where `τ_accept` is set on
**source validation data** at the operating point defined in Phase 2 (not tuned on target); (iii)
the flow satisfies all constraints above. The headline metric is the **high-confidence-miss rate
(HCMR)**: fraction of target attack flows for which the search finds such a candidate within the
query budget.

---

## 4. The codebase you are plugging into

Repo root is this directory's parent (`/home/user/ddos-xdomain-paper` in the dev environment; on
the author's machine `D:\Projects\ddos_xdomain_paper`). Everything you need already exists; **reuse
it, do not reimplement.**

| You need | It is here | Signature / note |
|---|---|---|
| Config, seeds, dataset registry | `src/config.py` | `SEEDS=(42..46)`, `SAMPLE_N_PER_CLASS`, `NETFLOW_V2`, `OKABE` colours, `FIG_DPI=300` |
| Load + harmonise + label one dataset | `src/data.py::load(key, other_policy, dedup)` | returns `(X, y, fam, LoadReport)`; dedup + leakage handling already correct |
| Shared 39-feature space, asserted identical | `src/data.py::netflow_common_features()` | use this feature list, do not hand-pick |
| Feature taxonomy (rate/size/timing/header/flags/id) | `src/features.py` | `NETFLOW_TAXONOMY`, `CAPACITY_CLASSES`, `SEMANTIC_CLASSES`; **base your control-class partition here** |
| Train one model on a source, tune threshold on source test | `src/pipeline.py::fit_source(...)` → `SourceFit` | gives `.model`, `.scaler`, `.threshold`, `.features`, `._median`; scaler fitted on source-train only (leakage-safe). `label_mode` controls exist. |
| Apply a source model to a target domain | `src/pipeline.py::apply_to(fit, target, ...)` | returns dict with `external` metrics, `proba`, `y`, `fam`, `rows_outside_train_range` |
| ATC + confidence signals | `src/divergence.py::confidence_scores(proba_source, proba_target, acc_source)` | returns `atc_estimated_accuracy`, `atc_threshold`, `mean_confidence_drop` — the monitors you probe |
| Divergence monitors (A-distance, MMD, Wasserstein) | `src/divergence.py` | additional monitors for the battery |
| Metrics, bootstrap CIs, paired gap, FPR@TPR, alerts/hour | `src/metrics.py` | `bootstrap_ci`, `paired_gap_ci`, `fpr_at_tpr`, `benign_quantile_threshold`, `best_threshold` |
| Figures style, number-checking pattern | `scripts/make_figures.py`, `scripts/check_numbers.py`, `paper/claims.json` | mirror the keyed-number discipline: every headline number pinned to a results file |
| Existing transfer results to anchor against | `results/transfer_matrix.json` | the 12 ordered pairs; reuse, do not recompute from scratch |

**Data reality.** The repo consumes the `dhoogla` Kaggle parquet mirrors — these are **flow feature
vectors, not pcaps**. The whole main study therefore lives in constrained feature space. That is a
deliberate, defensible scope given the author's hardware (one laptop, RTX 4060) and the fact that
the published NetFlow v2 datasets are themselves distributed as flows. Raw pcaps (UNSW-NB15 ~100 GB,
BoT-IoT ~69 GB) are too large to process on this machine and are **out of scope** except for the
optional, single-family realism check in Phase 1-R.

**Environment.** Python venv, CPU is enough for the tree models; the RTX 4060 only matters for the
fallback project, not this one. Reuse `requirements.txt`. Add nothing heavier than `scipy`,
`cvxpy` (optional, for the dependency-constrained projection), and `nfstream` (only if Phase 1-R
runs).

---

## 5. Pre-registered choices (fill in Phase 0, then freeze)

These are the knobs. Phase 0 sets each to a concrete value, commits the file, and nothing after
Phase 0 may change them without a dated amendment in the same file.

- **Source→target pair(s).** Primary: `nf_unsw_nb15 → nf_cse_cic_ids2018` (P11's worst inversion,
  LightGBM external AUC 0.070 — the most dramatic quiet failure) **and** one pair where transfer is
  strong so the attack has to work against a genuinely good detector: `nf_bot_iot →
  nf_cse_cic_ids2018` (LightGBM AUC 0.966). Two pairs, chosen for contrast, stated up front.
- **Model(s).** LightGBM (P11 primary) for the main result; LogisticRegression as the
  low-capacity contrast (its inversion does not need high-order interactions — see FINDINGS F1).
- **τ_accept operating point.** Confidence threshold fixed at the source-validation point giving a
  stated benign review budget (e.g. 1% benign flows escalated). Set the exact number in Phase 0.
- **Query budget.** Score-only budget per flow (e.g. 200 queries). State it; report HCMR as a
  function of it.
- **Monitors in the battery.** ATC; mean-confidence-drop; KS test on score distribution;
  proxy A-distance; per-feature max Wasserstein. All already in `src/divergence.py`. Treated as
  **candidate signals to evaluate**, thresholds set on source-validation data — not as established
  operational alarms.
- **Primary metric.** HCMR (Section 3). Secondary: benign review burden (alerts/hour at the
  operating point), plain evasion rate (ignoring confidence), attack functional-validity rate,
  and the monitors' alarm rates (did any fire?).
- **Falsifiers** (Section 7).

---

## 6. Execution phases

### Phase 0 — Pre-registration and literature gate  (≈ 1–2 days)

1. Read the full text of all seven Section 2 works. Fill the comparison table from the papers, not
   from this file's summaries.
2. **Gate 0 (novelty):** if any paper already measures adversarial high-confidence misses against
   the joint detector+monitor system under cross-testbed shift with a stated constraint model, stop
   and go to Section 9 fallback. Otherwise write the one-sentence delta against the closest
   (Bikdeli) explicitly.
3. Write `research-opportunities/p1/PREREGISTRATION.md`: the threat model (Section 3 instantiated),
   the frozen choices (Section 5 with numbers), the success definition, the metrics, and the
   falsifiers. Commit it **before** writing any attack code. This commit is the credibility anchor;
   its timestamp must precede the results commits.

### Phase 1 — Constraint model + feature-dependency analysis  (≈ 2–3 days)

4. Implement `p1/constraints.py`: the feasible-set checker and a projection operator.
   - `feasible(flow, family, bounds) -> bool`: enforces box [p1,p99] per family, immutability of
     uncontrollable features, integer/flag validity, and the dependency relations in Section 3.
   - `project(candidate, original, family, bounds) -> flow`: snap an infeasible candidate back into
     the feasible set (clip to box, round integers, repair dependencies, restore immutable features).
   - Derive `bounds` from the real source attack flows via `data.load` (per family, per feature
     p1/p99 and the empirical dependency slacks). Save to `results/p1/constraints.json`.
5. **Feature-dependency measurement (answers "don't assume responder features are uncontrollable").**
   On real flows, fit a simple predictor of each indirectly-influenced feature from the directly
   controllable ones, and report R². A high R² means the attacker's direct changes largely
   determine that feature (so it is *not* a free defense); a low R² means it carries
   attacker-independent signal (so it *is* a candidate defense feature). Save
   `results/p1/feature_controllability.json`. This table decides which features Phase 4's defense
   may use, on evidence — not assumption.
6. **Gate 1 (realism of the feature-space study):** at least some indirectly-influenced features
   must have low controllability R² (there exist features the attacker cannot freely set). If every
   feature is either directly controllable or trivially derivable from controllable ones, the
   defense has nothing to stand on — narrow to "we show the monitor can be fully evaded and no
   responder-side defense exists in this feature set", which is still an honest (negative) result.

#### Phase 1-R (OPTIONAL) — single-family wire-realism check

Only if Phases 0–4 finish with time to spare, and only to strengthen the realism claim against
PAVE. Do **not** let it block the main result.
- Take **one** DoS family and the smallest available real pcap subset (not the 100 GB full set —
  a few minutes of one attack). Apply a chosen feasible perturbation at the traffic level with a
  scriptable tool (e.g. `tcpreplay`/`scapy` for timing/padding within the DoS tool's envelope),
  re-extract flows with an open extractor (`nfstream`, free; or nProbe under ntop's free
  educational licence — email request documented, not assumed), and confirm the resulting flow
  lands where the feature-space search put it.
- This converts "feature-space, domain-constrained" into "at least one family verified wire-valid",
  a materially stronger claim. If it does not reproduce, report that honestly and keep the scope at
  feature space.

### Phase 2 — Monitor battery at a fixed operating point  (≈ 2 days)

7. Implement `p1/monitors.py` wrapping the existing `src/divergence.py` signals into a uniform
   `score(fit, target_proba, target_X) -> {monitor_name: alarm_bool, statistic}` where each
   monitor's threshold was set on **source-validation** data to the pre-stated benign-FPR budget.
8. Reproduce the baseline: run `fit_source` + `apply_to` for the two pairs × two models (reuse
   `results/transfer_matrix.json` where possible). Record, with no attack, each monitor's statistic
   and whether it fires. This establishes the "quiet monitor" baseline the attack must preserve.
   Save `results/p1/monitor_baseline.json`.

### Phase 3 — Adaptive high-confidence-miss search  (≈ 3–4 days)

9. Implement `p1/evade.py`:
   - `search(fit, flow, family, bounds, budget, mode)` returns the best feasible candidate and its
     detector score. `mode="score"` (primary): a constrained black-box search — random
     search + hill-climbing or a simple evolutionary search over the directly-controllable features
     only, each candidate passed through `constraints.project`, scored via `fit.model.predict_proba`
     on the `fit.scaler`-transformed vector. `mode="white"` (ablation): projected gradient on a
     differentiable surrogate, then `project`.
   - The objective is **not** "flip the label"; it is "flip the label **and** push confidence above
     τ_accept **and** stay feasible". Encode as: minimise detector P(attack) subject to feasibility,
     then among label-flipped feasible candidates maximise confidence.
10. Run the attack on every real target attack flow (capped per family for cost), both pairs, both
    models, both knowledge settings, five seeds. For each, record HCMR, plain evasion rate, mean
    confidence of successful misses, functional-validity rate, queries used, and — critically — the
    monitor battery's alarm rates **during the attack** (does ATC still say "fine"?). Save
    `results/p1/attack_results.json`. Figures via the repo's style.
11. **Gate 3 (is there a phenomenon):** report HCMR with bootstrap CIs. There is no minimum it
    "must" hit — a low HCMR under realistic constraints is the *Evasion-Impractical* SoK's finding
    reproduced for the monitored setting, which is itself a clean, publishable, honest result. What
    must be true to continue to a *defense* claim: HCMR is non-trivial in the score-only setting on
    at least one pair, **and** the monitors stay quiet during successful attacks (if they already
    fire, the defense story is "existing monitors suffice", also publishable). Write down which
    world you are in before Phase 4.

### Phase 4 — Monitor-side defense, evaluated honestly  (≈ 2–3 days)

12. Implement `p1/defend.py`: a monitor that watches the **low-controllability features** found in
    Phase 1 (step 5) — the ones the attacker cannot freely set — via a one-class/novelty score or a
    per-feature shift test on those columns only. Threshold on source-validation data at the same
    benign-FPR budget as the other monitors.
13. Re-run the Phase 3 attack against the detector+defense system. Report the **drop in HCMR** and
    the **false-alarm cost** (benign review burden) the defense adds. A defense that halves HCMR but
    triples benign alerts has a stated price; report both, plot the trade-off. Save
    `results/p1/defense_results.json`.
14. **Gate 4:** the defense is reported as a contribution only if it reduces HCMR by a
    pre-stated margin at a benign-FPR cost below a pre-stated ceiling (set both in Phase 0). If it
    does not clear the bar, report it as a negative result ("the obvious responder-side defense does
    not close the gap at acceptable cost") — do not quietly drop it.

### Phase 5 — Write-up and reproducibility  (≈ 3–4 days)

15. Short paper (8–10 pp): intro (the quiet-monitor failure, motivated by Bikdeli + P11);
    threat model (Section 3); the constraint model and controllability analysis (the realism
    answer to PAVE); the attack; the monitor battery and what stayed quiet; the defense and its
    price; limitations (feature-space scope, the one-family wire check if run, no claim beyond the
    tested pairs). Mirror P11's `claims.json` keyed-number discipline: every headline number pinned
    to a `results/p1/*.json` key, with a `check_numbers`-style verifier.
16. Release code and the constraint/results JSONs. Keep the attack code in the private repo until
    the paper is public; the datasets are already public mirrors, so no data is redistributed.

---

## 7. Falsifiers (pre-stated — if these fire, narrow or report negative)

- **F-realism:** if under the score-only (realistic) threat model, with constraints enforced, HCMR
  on both pairs is within bootstrap noise of zero, the honest finding is "monitored cross-network
  DoS detection resists realistic high-confidence evasion" (reproduces + extends the SoK). Keep the
  paper; change the headline. Do **not** relax constraints to manufacture an attack.
- **F-monitor-already-works:** if the existing monitors (ATC etc.) already fire during successful
  evasions, there is no quiet-monitor failure to fix; report "ATC is a usable alarm against this
  adversary", which contradicts Bikdeli's benign-shift finding in an interesting way.
- **F-no-defense-features:** if Phase 1 finds no low-controllability features (step 6 gate), there
  is no responder-side defense; report the evasion result alone.
- **F-white-box-only:** if the attack works only white-box, state that the realistic adversary
  cannot do it; the contribution shrinks to a worst-case study. Still publishable, clearly scoped.
- **F-novelty:** Phase 0 finds the joint object already done → Section 9 fallback.

None of these is failure. Each is a defensible paper. The only real failure is a tuned,
constraint-relaxed, cherry-picked positive — which would destroy exactly the credibility the
portfolio is built on.

---

## 8. SOP workstream (runs in parallel, independent of the result)

The SOP does not need the paper finished. It needs an honest, specific sentence and a verifiable
preprint link for P11. Produce these regardless of how Phases 3–4 turn out.

- **After Phase 0:** SOP sentence form — *"For my thesis I am investigating whether an adaptive
  adversary, constrained to traffic-plausible changes, can drive malicious flows into the
  high-confidence region where label-free monitors stay silent after cross-network transfer, and
  whether watching the features the adversary cannot freely set restores the warning."* Phrased as a
  question under investigation, never as a completed result.
- **After Phase 3 (whichever world):**
  - positive: *"In preliminary work, an adversary limited to [stated capability] produced
    high-confidence misses in X% of transferred attack flows while ATC continued to report normal
    accuracy; monitoring the low-controllability features reduced this to Y% at a Z% review-burden
    cost."*
  - negative: *"In preliminary work I found that under traffic-plausible constraints the monitored
    detector resisted high-confidence evasion, which sharpens rather than weakens the open question
    of what a realistic adversary can achieve."*
- **Faculty framing (verified this session):** David Inouye (Purdue ECE) works explicitly on
  explaining/localizing distribution shift — the natural methodological complement, and the only
  distance-based signal that carried any warning in P11 was the largest single-feature shift, which
  is his territory. Ruqi Zhang (uncertainty) is a complement on the confidence signal. Confirm
  Inouye can advise a CS-department thesis before naming him as a committee hook; name Saparov only
  if a specific current paper supports it. Add a security advisor (Bertino's group published on
  concept drift in malware detection, NDSS 2025; Li/Zhang co-advise AI-security students) — a
  cross-network-security thesis needs one.
- **Non-project SOP fixes that outrank the project** (do these first): resolve P11 authorship (CV
  says sole author, ~16 outreach drafts credit Dr. Yadav, the 2026-10-07 decision added him, the
  manuscript still lists one author — make all four agree before anything ships); post P11 to arXiv
  (~10 Nov) so the security paragraph is verifiable; if P06b is accepted at ML4H (decision due
  ~2026-10-22) upgrade every profile the same day; do not let any of this cost GRE prep before
  2026-11-20.

---

## 9. Fallback — *Rarer or Fewer?* (if Phase 0 or a gate kills P-1)

If P-1 fails its novelty gate or collapses to an uninteresting negative, switch to the
residual-vulnerability estimator from `REPORT.md` / `pilots/`: estimate how much of an attack
surface a finite red-team missed, under a declared exchangeable attack distribution, separating
defenses that make vulnerabilities *rarer* from those that make them *fewer*. It is the stronger
standalone method (no prior estimator found in this session's searches) but sits off the SOP's
security thesis and needs new exchangeable-draw data, so it is the fallback, not the lead. Its
pre-registered pilot plan already exists in `pilots/PILOT_PLAN.md`; its go/no-go is in `REPORT.md`
§10.12. Do not pursue both as separate papers — one finished contribution beats two half ones.

---

## 10. Timeline and hardware

Machine: i7-13650HX, RTX 4060 (laptop). The tree models are CPU-bound and already run the full P11
pipeline in ~3 h; the attack search is the new cost and is embarrassingly parallel over flows, so it
fits on CPU. GPU is not needed for P-1 (it is needed for the fallback). No paid API, no cloud, no
restricted data.

Calendar, against the fixed constraints (GRE retake 2026-11-20; first US deadlines 2026-12-01/04):
- **Now → 2026-11-20:** GRE is the priority. On P-1, do only Phase 0 (literature + pre-registration)
  in spare time — it is reading and writing, low-risk, and it is what the SOP sentence needs.
- **2026-11-21 → 2026-11-30:** Phases 1–3 (constraints, monitor battery, attack). Target one honest
  HCMR number with CIs by ~2026-11-27. This is the SOP-grade pilot.
- **2026-12-01 → mid-December:** applications go out describing P-1 as a *proposed thesis with a
  preliminary result*, never as a finished paper.
- **December → February:** Phase 4 (defense), Phase 1-R (optional wire check), Phase 5 (write-up),
  preprint if the result holds.

A preprint cannot be peer-reviewed before the deadlines, so its application value is the specific,
checkable SOP sentence plus a public repo — not a publication claim. Protect the GRE, the LORs, and
P11's arXiv posting ahead of it.

---

## 11. Integrity rules (non-negotiable)

- Pre-registration committed before results; results commits timestamped after it.
- Every headline number pinned to a results-file key and verified by a `check_numbers`-style script.
- Leakage discipline inherited from `src/pipeline.py`: scaler/threshold fitted on source-train only,
  monitor thresholds on source-validation only, target labels never touched except to score.
- Report seed variance separately from sampling variance (repo already does this).
- Negative and inconclusive results reported as such, in the abstract.
- No claim of wire-realizability unless Phase 1-R actually produced it, for the families it covered.
- No third-party or production system is probed; all traffic manipulation is synthetic, on public
  offline datasets the author already holds. State the authorized, defensive, self-red-team context
  in the paper's ethics/threat-model section.
- Preserve P11's repository and history; P-1 lives under `research-opportunities/p1/` and
  `results/p1/`, never overwriting P11 artifacts.
```
