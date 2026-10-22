"""
Generality backbone: the latent high-confidence-miss exposure and the (cheap) model-based
monitor response across the FULL NetFlow v2 quartet — every ordered source->target pair x
4 models x 5 seeds. No per-flow search here (that stays on the two representative pairs); this
measures the dominant finding at scale:

  * external AUC (benign + all-DoS target);
  * latent high-confidence-miss rate on real target volumetric flows (no attacker constraint);
  * natural predicted-benign rate;
  * ATC-drop and confidence-drop alarms, each thresholded on a source-validation two-half null
    at the 1% budget (cheap: confidence quantiles only, no discriminator training).

A pair whose target carries no volumetric DoS flows is skipped (recorded). Saves
results/p1/matrix_latent.json.
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

from src.config import RESULTS, NETFLOW_V2  # noqa: E402
from src.divergence import confidence_scores  # noqa: E402
from p1common import build_fit, read_capped, score_flows  # noqa: E402

DATASETS = [d.key for d in NETFLOW_V2]          # 4 NetFlow v2 datasets
MODELS = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
SEEDS = [42, 43, 44, 45, 46]
FAMILY = "volumetric"
TGT_BENIGN = 30_000
TGT_ALL = 30_000
VOL_CAP = 2000
OUT = RESULTS / "p1"


def tau_from(srcval_proba, srcval_y, budget=0.01):
    conf = np.maximum(srcval_proba, 1 - srcval_proba)
    ben = conf[np.asarray(srcval_y) == 0]
    return float(np.quantile(ben if len(ben) else conf, budget))


def model_monitor_null(srcval_proba, source_acc, b_cheap=100, budget=0.01, seed=42):
    """Two-half source-val null thresholds for the two cheap model-based monitors."""
    rng = np.random.default_rng(seed)
    p = np.asarray(srcval_proba)
    n = len(p)
    atc, conf = [], []
    for _ in range(b_cheap):
        idx = rng.permutation(n)
        a, bb = idx[: n // 2], idx[n // 2:]
        cs = confidence_scores(p[a], p[bb], source_acc)
        atc.append(source_acc - cs["atc_estimated_accuracy"])
        conf.append(cs["mean_confidence_drop"])
    q = 1 - budget
    return float(np.quantile(atc, q)), float(np.quantile(conf, q))


def main():
    rows, skipped = [], []
    t0 = time.time()
    for target in DATASETS:
        for seed in SEEDS:
            Xall_df, yall, _ = read_capped(target, TGT_BENIGN, TGT_ALL, seed, family=None)
            Xall = Xall_df.to_numpy(np.float64)
            Xv_df, _, _ = read_capped(target, 0, VOL_CAP, seed, family=FAMILY)
            Xvol = Xv_df.to_numpy(np.float64)
            has_vol = len(Xvol) > 0
            for source in DATASETS:
                if source == target:
                    continue
                for model in MODELS:
                    F = build_fit(source, model, seed)
                    thr = F.fit.threshold
                    tau = tau_from(F.srcval_proba, F.srcval_y)
                    # external AUC on benign + all-DoS
                    from src.metrics import binary_metrics
                    pa = score_flows(F.fit, Xall)
                    ext = binary_metrics(yall, pa >= thr, pa)
                    # model-monitor alarms on the external deployment
                    atc_thr, conf_thr = model_monitor_null(F.srcval_proba, F.source_acc, seed=seed)
                    cs = confidence_scores(F.srcval_proba, pa, F.source_acc)
                    atc_alarm = (F.source_acc - cs["atc_estimated_accuracy"]) > atc_thr
                    conf_alarm = cs["mean_confidence_drop"] > conf_thr
                    rec = {"source": source, "target": target, "model": model, "seed": seed,
                           "external_auc": float(ext["roc_auc"]),
                           "atc_alarm": bool(atc_alarm), "conf_drop_alarm": bool(conf_alarm),
                           "has_volumetric": has_vol}
                    if has_vol:
                        pv = score_flows(F.fit, Xvol)
                        confv = np.maximum(pv, 1 - pv)
                        rec["natural_pred_benign_rate"] = float((pv < thr).mean())
                        rec["latent_hcm_rate"] = float(((pv < thr) & (confv >= tau)).mean())
                    rows.append(rec)
                    del F
                    gc.collect()
            del Xall_df, Xall, Xv_df, Xvol
            gc.collect()
            print(f"  target={target} seed={seed} done ({time.time()-t0:.0f}s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "matrix_latent.json").write_text(json.dumps(rows, indent=2))
    # summary
    vol = [r for r in rows if r.get("has_volumetric")]
    print(f"\n{len(rows)} configs, {len(set((r['source'],r['target']) for r in rows))} ordered pairs")
    if vol:
        lat = np.mean([r["latent_hcm_rate"] for r in vol])
        print(f"mean latent HCMR (vol targets): {lat:.3f}  "
              f"range [{min(r['latent_hcm_rate'] for r in vol):.3f}, "
              f"{max(r['latent_hcm_rate'] for r in vol):.3f}]")
    print(f"ATC alarm rate: {np.mean([r['atc_alarm'] for r in rows]):.2f}  "
          f"conf-drop alarm rate: {np.mean([r['conf_drop_alarm'] for r in rows]):.2f}")
    print(f"wrote matrix_latent.json ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
