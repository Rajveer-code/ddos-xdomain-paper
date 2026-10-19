# Confidently Wrong

**Ranking inversion in cross-network denial-of-service detection.**

Cross-dataset transfer of flow-based DoS detectors does not decay toward chance. It passes
through chance. Across every ordered pair of four independently captured testbeds, 108 of
240 external evaluations score *below* ROC-AUC 0.5, and the worst pair reaches 0.0697: a
strong ranking with the sign reversed.

**Status:** manuscript complete; preprint in preparation; not yet submitted to a journal.
Target venue: *Computer Networks* (Elsevier). The full pipeline was re-run from an empty
`results/` on 18–19 Oct 2026 and reproduced every result file and figure
([`RERUN_2026-10-19.md`](RERUN_2026-10-19.md)).

- Manuscript source of truth: [`paper/manuscript.md`](paper/manuscript.md)
- Single-column proof: [`paper/manuscript.pdf`](paper/manuscript.pdf) (28 pages)
- Journal build (elsarticle, pdfLaTeX): [`paper/elsarticle/`](paper/elsarticle/)

---

## What the study found

1. **Transfer inverts rather than degrades.** Three of twelve ordered pairs score below
   chance in all four model families, logistic regression included, so the inversion does
   not need high-order feature interactions.
2. **Most failures are in the ranking, not the threshold.** Nine to eleven of twelve pairs
   for the primary model, depending on whether the two losses are compared in the same unit.
   A new threshold cannot repair a reversed ordering.
3. **The pre-specified feature hypothesis was not supported.** Removing all twenty
   "capacity" features moves external macro-F1 by +0.0132 [−0.0084, +0.0320].
4. **Aggregate drift monitors miss it.** Proxy A-distance, MMD and summed Wasserstein
   distance lose to a mean baseline; the model's own confidence (ATC) and the largest
   single-feature shift carry some signal.
5. **A few target labels repair it, and the source model does not help.** Ten balanced
   labelled target flows lift median macro-F1 from 0.3919 to 0.7253 when added to the source
   data, but logistic regression trained on those ten flows alone reaches 0.7852.
6. **The benchmarks need care.** The NetFlow copies are up to 99.7% duplicate in the
   feature space a model sees, and swapping CICIDS2017 for its 2022 regenerated release
   moves the cross-dataset result by close to a third.

Null and negative results are reported as such.

## Protocol

- **Feature space:** the NetFlow v2 standard feature set (Sarhan et al.); 39 of its features
  after dropping labels and ports, identical across four datasets. The CICFlowMeter pairing
  CIC-DDoS2019 ↔ CICIDS2017 is a secondary study.
- **Datasets:** NF-CSE-CIC-IDS2018-v2, NF-BoT-IoT-v2, NF-ToN-IoT-v2, NF-UNSW-NB15-v2,
  CIC-DDoS2019, CICIDS2017 and the DistriNet 2022 regenerated CICIDS2017 (Liu et al.). All are
  public Kaggle mirrors by `dhoogla`; versions and row counts against the official releases
  are in `results/provenance.json`. No data is redistributed here.
- **Transfer:** every ordered source→target pair, four model families, five seeds.
- **Statistics:** paired bootstrap intervals on the gap itself; the inferential unit is the
  ordered pair.

## Reproducing

```bash
pip install -r requirements.txt
python scripts/download_data.py      # needs ~/.kaggle/kaggle.json (never copied into the repo)
python scripts/run_all.py --dry-run  # the full pipeline, in order, with the settings that ran
python scripts/run_all.py            # about 3 h on an i7-13650HX laptop CPU; no GPU needed
python scripts/check_numbers.py      # keyed check of the headline numbers
```

`run_all.py` passes each experiment the settings recorded in its own results file; several
scripts have different defaults, so running them bare does not reproduce the paper.
`check_numbers.py` pins every headline number to the exact results file and key it comes
from (`paper/claims.json`) and fails if one drifts; a looser scan of all numeric literals is
printed as a secondary report.

| script | produces |
|---|---|
| `characterize_data.py`, `record_provenance.py` | dataset table, label map, mirror provenance |
| `run_transfer_matrix.py` | every ordered pair × model × seed |
| `analyze_robustness.py`, `summarize_matrix.py`, `aggregate_operating_point.py` | model-family robustness, unit of inference, operating-point metrics |
| `run_feature_ablation.py`, `ablation_intervals.py` | capacity/semantic ablation with paired bootstrap intervals |
| `run_feature_count.py` | random subsets at controlled size, separating size from identity |
| `analyze_dns_query_id.py` | what `DNS_QUERY_ID` carries in each dataset |
| `run_inversion_controls.py` | permutation and label-reversal controls |
| `run_unsw_robustness.py` | source-size control for the strongest inversion |
| `run_preprocessing_sensitivity.py` | de-duplication and clipping ablations |
| `run_divergence.py`, `analyze_gap_forecast.py` | label-free predictors of the loss |
| `run_remedies.py` | CORAL, threshold transfer, benign-reference recalibration |
| `run_label_budget.py` | leakage-free label budget, disjoint adaptation and evaluation sets |
| `run_target_only_control.py` | the same label draws used to train on the target alone |
| `run_cic_study.py` | the CICFlowMeter secondary study and the regenerated-release comparison |
| `summarize_all.py`, `summarize_secondary.py` | aggregate files the manuscript cites |
| `make_figures.py` | all figures, from `results/` |
| `build_pdf.py`, `build_pdf_ieee.py`, `build_pdf_elsarticle.py` | proof, IEEE and Elsevier builds |

Long runs checkpoint and hold a PID lock in `results/.locks/`, so an interrupted run resumes
rather than restarting.

## Data credits

- Sarhan, Layeghy and Portmann, *Towards a Standard Feature Set for NIDS Datasets* (MONET 2022) — NetFlow v2
- Sharafaldin et al., CICIDS2017 (ICISSP 2018) and CIC-DDoS2019 (ICCST 2019)
- Koroniotis et al., BoT-IoT (FGCS 2019); Alsaedi et al., ToN-IoT (IEEE Access 2020); Moustafa and Slay, UNSW-NB15 (MilCIS 2015)
- Liu, Engelen, Lynar, Essam and Joosen, *Error Prevalence in NIDS datasets* (IEEE CNS 2022) — regenerated CICIDS2017
- Engelen et al. (WTMC 2021) and Lanvin et al. (CRiSIS 2022) — CICIDS2017 label errors
- Parquet mirrors: [`dhoogla`](https://www.kaggle.com/dhoogla) on Kaggle (CC BY-NC-SA 4.0)

## Author

Rajveer Singh Pall
