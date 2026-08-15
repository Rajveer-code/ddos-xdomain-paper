# Capacity, Not Attack

**Why flow-based DDoS detectors fail across networks — and predicting the damage without labels.**

Status: **work in progress.** No results yet. This repository currently contains the
experimental harness only; every number will be produced by a seeded run and written to
`results/*.json` before it appears anywhere else.

---

## What this study asks

Flow-based DDoS detectors report near-perfect scores in-domain and collapse when applied
to a different network. That collapse is well documented. This work asks two questions
that are not:

1. **Which features cause it?** Hypothesis: features that encode *testbed capacity*
   (throughput, packet rate, inter-arrival timing) — not attack semantics — drive
   in-domain accuracy and destroy cross-dataset transfer.
2. **Can you see it coming without labels?** Given an unlabelled target network, how
   accurately can source↔target divergence predict the performance you will actually lose?

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

Kaggle credentials are read from `~/.kaggle/kaggle.json`. Then:

```bash
python scripts/download_data.py
```

Further entry points are added as experiments land.

## Data credits

- Sharafaldin et al., CICIDS2017 (ICISSP 2018) and CIC-DDoS2019 (ICCST 2019)
- Engelen et al., *Troubleshooting an Intrusion Detection Dataset* (WTMC 2021) — corrected labels
- Lanvin et al., *Errors in the CICIDS2017 dataset* (CRiSIS 2022)
- Sarhan et al., *Towards a Standard Feature Set for NIDS Datasets* (2021) — NetFlow v2
- Cleaned parquet mirrors: [`dhoogla`](https://www.kaggle.com/dhoogla) on Kaggle
- Arp et al., *Dos and Don'ts of Machine Learning in Computer Security* (USENIX Security 2022) — methodology

## Author

Rajveer Singh Pall
