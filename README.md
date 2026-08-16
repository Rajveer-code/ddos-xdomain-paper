# Confidently Wrong

**Ranking inversion in cross-network denial-of-service detection.**

Cross-dataset transfer of flow-based DoS detectors does not decay toward chance. It passes
through chance. Across every ordered pair of four independently captured testbeds, mean
external ROC-AUC is 0.5054 and 108 of 240 external evaluations fall *below* 0.5; the worst
pair reaches 0.0697, which is a strong ranking with the sign reversed.

Status: **complete.** Manuscript, figures and results are in the repository. Every number
in the paper is produced by a seeded run and written to `results/*.json` first;
`scripts/check_numbers.py` verifies that all 1,025 numeric literals in the manuscript trace
back to a result file, and it is expected to pass at 100%.

- Manuscript: [`paper/manuscript.pdf`](paper/manuscript.pdf) (22 pages) and
  [`paper/manuscript.md`](paper/manuscript.md), the source of truth.
- Target venue: Computers & Security (Elsevier), with an arXiv preprint.

---

## What this study asks, and what it found

The project began with a hypothesis about *which* features cause the collapse. That
hypothesis was pre-specified in version control before the experiment ran, and the data did
not support it. Both the original question and the answer are reported.

1. **Which features cause it?** Pre-specified hypothesis: features encoding *testbed
   capacity* (throughput, packet rate, inter-arrival timing) drive in-domain accuracy and
   destroy transfer. **Not supported.** Removing all twenty capacity features moves external
   macro-F1 by +0.0132 [-0.0084, +0.0320], an interval spanning zero.
2. **Can you see it coming without labels?** **Largely no.** Proxy A-distance, MMD and
   Wasserstein-1 carry almost no information about the loss; their intervals span zero and
   all three are worse out-of-sample than predicting the mean.
3. **What does the failure actually look like?** Inversion, not degradation, and it appears
   in all four model families tested. Logistic regression inverts on the same pairs as the
   tree ensembles, which rules out any mechanism requiring high-order feature interactions.

Null and negative results are reported as such. The single strongest remedy found is a
small number of target labels, not feature engineering, distance monitoring, or threshold
recalibration; zero-label recalibration is net harmful when pooled.

## Protocol

- **Feature space:** the NetFlow v2 standard feature set (Sarhan et al., 2021) — 43
  identical features across four datasets, so cross-dataset claims do not rest on an
  ad-hoc column intersection. The usual CICFlowMeter pairing is kept as a secondary study.
- **Datasets:** `NF-CSE-CIC-IDS2018-v2`, `NF-BoT-IoT-v2`, `NF-ToN-IoT-v2`,
  `NF-UNSW-NB15-v2`, plus `CIC-DDoS2019` / `CICIDS2017` and the DistriNet-corrected
  CICIDS2017 (Engelen et al., 2021) for label-noise isolation.
- **Transfer:** every ordered source→target pair, both directions.
- **Statistics:** paired bootstrap CIs on the *gap* itself, over multiple seeds.

## Layout

```
src/          harness: config, data loading, harmonisation, feature taxonomy, experiments
configs/      run configurations
results/      every metric, as JSON — the single source of truth for the paper
figures/      regenerated from results/, never hand-edited
paper/        manuscript
scripts/      entry points
```

## Reproducing

```bash
pip install -r requirements.txt
```

Kaggle credentials are read from `~/.kaggle/kaggle.json` and are never copied into the
repository. Then:

```bash
python scripts/download_data.py
```

One experiment is one entry point; each writes its own file under `results/`.

| script | produces |
|---|---|
| `run_transfer_matrix.py` | the transfer matrix, every ordered pair x model x seed |
| `run_feature_ablation.py` | capacity/semantic ablation with paired bootstrap CIs |
| `run_feature_count.py` | random subsets at controlled size, separating size from identity |
| `run_inversion_controls.py` | permutation and label-reversal controls |
| `run_unsw_robustness.py` | source-size control for the strongest inversion |
| `run_preprocessing_sensitivity.py` | de-duplication, contradiction and clipping ablations |
| `run_divergence.py` | proxy A-distance, MMD, Wasserstein-1, ATC |
| `run_remedies.py` | CORAL, threshold transfer, benign-quantile recalibration |
| `run_label_budget.py` | leakage-free label budget with disjoint adaptation and evaluation |
| `run_cic_study.py` | the CICFlowMeter secondary study and corrected-label comparison |
| `analyze_robustness.py` | model-family robustness and unit-of-inference analysis |
| `make_figures.py` | all figures, regenerated from `results/` |
| `build_pdf.py` | `paper/manuscript.pdf` from the markdown source |
| `check_numbers.py` | verifies every numeric literal in the manuscript traces to a result |

Long runs are checkpointed and hold a PID lock in `results/.locks/`, so an interrupted run
resumes rather than restarting and two runs cannot race on the same output.

## Data credits

- Sharafaldin et al., CICIDS2017 (ICISSP 2018) and CIC-DDoS2019 (ICCST 2019)
- Engelen et al., *Troubleshooting an Intrusion Detection Dataset* (WTMC 2021) — corrected labels
- Lanvin et al., *Errors in the CICIDS2017 dataset* (CRiSIS 2022)
- Sarhan et al., *Towards a Standard Feature Set for NIDS Datasets* (2021) — NetFlow v2
- Cleaned parquet mirrors: [`dhoogla`](https://www.kaggle.com/dhoogla) on Kaggle
- Arp et al., *Dos and Don'ts of Machine Learning in Computer Security* (USENIX Security 2022) — methodology

## Author

Rajveer Singh Pall
