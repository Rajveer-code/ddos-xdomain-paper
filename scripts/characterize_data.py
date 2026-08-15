"""
Characterise every dataset and write the results the manuscript's Table 1 is built from.

Produces:
    results/dataset_summary.json   per-dataset rows, class balance, duplicates, families
    results/label_mapping.json     full raw-label -> class/family map, for the appendix
    results/feature_space.json     the shared NetFlow v2 feature space

No modelling happens here. This exists so that every descriptive number in the paper is
traceable to one seeded run instead of being quoted from a dataset's own paper.

    python scripts/characterize_data.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CICFLOWMETER, NETFLOW_V2, RESULTS
from src.data import load, netflow_common_features


def characterise(key: str) -> dict:
    """Load one dataset under the 'keep' policy so nothing is hidden, and describe it."""
    t0 = time.perf_counter()
    X, y, fam, rep = load(key, other_policy="keep", dedup=True)

    rec = rep.to_dict()
    rec["family_counts"] = {k: int(v) for k, v in fam.value_counts().items()}
    rec["benign_to_ddos_ratio"] = (
        round(rec["class_counts"]["benign"] / rec["class_counts"]["ddos"], 2)
        if rec["class_counts"]["ddos"] else None
    )
    rec["ddos_base_rate"] = (
        round(rec["class_counts"]["ddos"] / max(len(y), 1), 6)
    )
    rec["missing_cells"] = int(X.isna().to_numpy().sum())
    rec["seconds"] = round(time.perf_counter() - t0, 1)

    print(
        f"  {key:20s} raw={rec['rows_raw']:>10,} -> out={rec['rows_out']:>9,}  "
        f"dup={rec['duplicate_fraction']:.1%}  feats={rec['n_features']}  "
        f"ddos={rec['class_counts']['ddos']:>8,}  "
        f"base_rate={rec['ddos_base_rate']:.5f}  ({rec['seconds']}s)",
        flush=True,
    )
    return rec


def main() -> int:
    keys = [d.key for d in (*NETFLOW_V2, *CICFLOWMETER)]
    print(f"Characterising {len(keys)} datasets\n")

    summary, label_maps = {}, {}
    for k in keys:
        rec = characterise(k)
        label_maps[k] = {"class": rec.pop("label_map"), "family": rec.pop("family_map")}
        summary[k] = rec

    shared = netflow_common_features()
    feature_space = {
        "netflow_v2_shared_features": shared,
        "n_shared": len(shared),
        "note": (
            "All four NetFlow v2 datasets ship an identical column set (Sarhan et al., "
            "2021). The shared space is therefore a published standard, not an artefact "
            "of intersecting column names. L4_SRC_PORT and L4_DST_PORT are dropped as "
            "socket identifiers."
        ),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    for name, obj in [
        ("dataset_summary", summary),
        ("label_mapping", label_maps),
        ("feature_space", feature_space),
    ]:
        path = RESULTS / f"{name}.json"
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        print(f"\nwrote {path}")

    print(f"\nShared NetFlow v2 feature space: {len(shared)} features")
    unmatched = {
        k: [lab for lab, f in m["family"].items() if f == "other"]
        for k, m in label_maps.items()
    }
    print("\nLabels filed as 'other' (non-DoS attacks), per dataset:")
    for k, labs in unmatched.items():
        print(f"  {k:20s} {labs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
