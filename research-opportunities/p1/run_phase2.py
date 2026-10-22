"""
Phase 2 entry point: the monitor battery at a fixed operating point, with NO attack.

Establishes the "quiet monitor" baseline the attack must preserve: under honest cross-network
transfer, which monitors fire? For each (pair, model, seed) it trains the source detector on a
capped sample, scores the natural target sample, and runs the calibrated battery on it.

Memory-safe: streams data via p1common.read_capped, frees per-config arrays, never caches a
full domain. Saves results/p1/monitor_baseline.json.
"""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import RESULTS  # noqa: E402
import monitors as M  # noqa: E402
from p1common import build_fit, read_capped, external_metrics, FEATURES  # noqa: E402

PAIRS = [("nf_unsw_nb15", "nf_cse_cic_ids2018"),
         ("nf_bot_iot", "nf_cse_cic_ids2018")]
MODELS = ["LightGBM", "LogisticRegression"]
SEEDS = [42, 43, 44, 45, 46]            # full frozen spec
TGT_BENIGN = 50_000
TGT_ATTACK = 50_000
OUT = RESULTS / "p1"


def main() -> None:
    results = []
    t0 = time.time()
    for source, target in PAIRS:
        for seed in SEEDS:
            Xtdf, yt, _fam = read_capped(target, TGT_BENIGN, TGT_ATTACK, seed, family=None)
            Xt = Xtdf.to_numpy(dtype=np.float64)
            for model in MODELS:
                F = build_fit(source, model, seed)
                ext, proba = external_metrics(F.fit, Xt, yt)
                cal = M.calibrate(F.srcval_proba, F.srcval_X, F.source_acc)
                mon = M.score(cal, proba, Xt)
                rec = {
                    "source": source, "target": target, "model": model, "seed": seed,
                    "external_auc": float(ext["roc_auc"]),
                    "external_macro_f1": float(ext["macro_f1"]),
                    "source_acc": F.source_acc, "threshold": float(F.fit.threshold),
                    "n_target": int(len(yt)), "target_base_rate": float((yt == 1).mean()),
                    "monitors": mon,
                    "n_alarm": int(sum(v["alarm"] for v in mon.values())),
                }
                results.append(rec)
                alarms = [m for m, v in mon.items() if v["alarm"]]
                print(f"[{source[:7]}->{target[:10]} {model[:5]} s{seed}] "
                      f"AUC={rec['external_auc']:.3f} alarms={rec['n_alarm']}/5 {alarms} "
                      f"({time.time()-t0:.0f}s)", flush=True)
                del F, cal, proba, mon
                gc.collect()
            del Xtdf, Xt, yt
            gc.collect()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "monitor_baseline.json").write_text(json.dumps(results, indent=2))
    per_mon = {m: float(np.mean([r["monitors"][m]["alarm"] for r in results]))
               for m in M.MONITORS}
    print("\nbaseline alarm rate per monitor (fraction of configs):")
    for m, r in per_mon.items():
        print(f"  {m:18s} {r:.2f}")
    print(f"\nwrote monitor_baseline.json  ({len(results)} configs, {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
