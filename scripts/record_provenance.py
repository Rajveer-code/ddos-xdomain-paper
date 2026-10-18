"""
Record where the datasets came from and how the copies used differ from the originals.

Produces:
    results/provenance.json   official release totals, mirror versions and licence, and
                              the row shortfall of each copy against its official release

The official totals and mirror versions are external facts, not computed here; each carries
the page it was read from and the date. Everything derived from them is computed from
results/dataset_summary.json so the manuscript's provenance numbers trace to one file.

    python scripts/record_provenance.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RESULTS

READ_ON = "2026-10-18"
UQ_PAGE = "https://staff.itee.uq.edu.au/marius/NIDS_datasets/"
KAGGLE_API = "https://www.kaggle.com/api/v1/datasets/view/dhoogla/"

# Official totals as published by the University of Queensland for the NetFlow v2 releases.
OFFICIAL_ROWS = {
    "nf_cse_cic_ids2018": 18_893_708,
    "nf_bot_iot": 37_763_497,
    "nf_ton_iot": 16_940_496,
    "nf_unsw_nb15": 2_390_275,
}

# Kaggle mirror slug and version actually downloaded (see src/config.py kaggle refs).
MIRRORS = {
    "nf_cse_cic_ids2018": ("nfcsecicids2018v2", 2),
    "nf_bot_iot": ("nfbotiotv2", 2),
    "nf_ton_iot": ("nftoniotv2", 2),
    "nf_unsw_nb15": ("nfunswnb15v2", 2),
    "cic_ddos2019": ("cicddos2019", 3),
    "cic_ids2017": ("cicids2017", 3),
    "cic_ids2017_fixed": ("distrinetcicids2017", 5),
}
LICENCE = "CC BY-NC-SA 4.0"


def main() -> int:
    summary = json.loads((RESULTS / "dataset_summary.json").read_text(encoding="utf-8"))
    datasets = {}
    for key, (slug, version) in MIRRORS.items():
        rows_copy = summary[key]["rows_raw"]
        entry = {
            "mirror": f"dhoogla/{slug}", "mirror_version": version, "licence": LICENCE,
            "source": KAGGLE_API + slug, "rows_in_copy": rows_copy,
        }
        if key in OFFICIAL_ROWS:
            official = OFFICIAL_ROWS[key]
            entry.update(official_rows=official, official_source=UQ_PAGE,
                         rows_missing_from_copy=official - rows_copy,
                         pct_fewer_than_official=round(100 * (1 - rows_copy / official), 1))
        datasets[key] = entry

    fewer = [d["pct_fewer_than_official"] for d in datasets.values()
             if "pct_fewer_than_official" in d]
    payload = {
        "read_on": READ_ON,
        "datasets": datasets,
        "netflow_pct_fewer_range": [min(fewer), max(fewer)],
        "cicids2017_regenerated_minus_original_rows":
            summary["cic_ids2017"]["rows_raw"] - summary["cic_ids2017_fixed"]["rows_raw"],
    }
    out = RESULTS / "provenance.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"NetFlow copies hold {fewer and min(fewer)}% to {max(fewer)}% fewer rows than official")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
