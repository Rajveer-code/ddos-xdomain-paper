"""
Fetch every Kaggle mirror into data/<key>/.

Idempotent: a dataset that already has parquet files on disk is skipped unless --force.
Credentials come from ~/.kaggle/kaggle.json and are never copied into the repo.

    python scripts/download_data.py
    python scripts/download_data.py --only nf_bot_iot nf_unsw_nb15
    python scripts/download_data.py --force
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import netfix  # noqa: F401  # must precede any network call
from src.config import DATA, DATASETS, Dataset


def _parquet_files(root: Path) -> list[Path]:
    return sorted(root.glob("**/*.parquet"))


def download(ds: Dataset, force: bool = False) -> dict:
    """Download one dataset. Returns a record of what landed on disk."""
    target = ds.path
    existing = _parquet_files(target) if target.exists() else []

    if existing and not force:
        size = sum(f.stat().st_size for f in existing)
        print(f"  [skip] {ds.key}: {len(existing)} parquet, {size / 1e6:,.1f} MB already present")
        return {"key": ds.key, "status": "cached", "files": len(existing), "bytes": size}

    if force and target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    print(f"  [get ] {ds.key} <- {ds.kaggle_ref}", flush=True)
    t0 = time.perf_counter()

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(ds.kaggle_ref, path=str(target), unzip=True, quiet=False)

    files = _parquet_files(target)
    size = sum(f.stat().st_size for f in files)
    dt = time.perf_counter() - t0

    if not files:
        raise RuntimeError(f"{ds.key}: download produced no .parquet under {target}")

    print(f"  [ok  ] {ds.key}: {len(files)} parquet, {size / 1e6:,.1f} MB in {dt:,.1f}s")
    return {"key": ds.key, "status": "downloaded", "files": len(files),
            "bytes": size, "seconds": round(dt, 1)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", default=None, help="dataset keys to fetch")
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    args = ap.parse_args()

    keys = args.only or list(DATASETS)
    unknown = [k for k in keys if k not in DATASETS]
    if unknown:
        ap.error(f"unknown dataset keys: {unknown}. Known: {list(DATASETS)}")

    print(f"Downloading {len(keys)} dataset(s) into {DATA}\n")
    records = [download(DATASETS[k], force=args.force) for k in keys]

    total = sum(r["bytes"] for r in records)
    print(f"\nDone. {len(records)} dataset(s), {total / 1e9:,.2f} GB on disk under {DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
