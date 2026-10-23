"""
Check 1 (pre-declared protocol in DECISION.md): conformal-abstention drift signal across the full
12x4x5 matrix, compared with the confidence monitors and with offline ground-truth safety.

Faithful-as-possible split-conformal abstention (we label it approximate, not a verbatim
reproduction of Bikdeli's pipeline): nonconformity s(x) = 1 - max(p, 1-p) = min(p, 1-p). The
conformal threshold q is the (1 - alpha_conf) quantile of s on source-validation BENIGN flows
(alpha_conf = 0.01, ~99% conforming). The target abstention rate is the fraction of the target
deployment with s > q. The ALARM threshold is null-calibrated on source-validation two-half
resampling at a 1% false-alarm budget (no target labels, no adversarial metric used to tune).

Per config we record: conformal_alarm, the ATC/conf-drop alarm (reused logic), and whether the
config is unsafe (true recall on volumetric attacks < 0.5). Saves results/p1/matrix_conformal.json.
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

DATASETS = [d.key for d in NETFLOW_V2]
MODELS = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
SEEDS = [42, 43, 44, 45, 46]
FAMILY = "volumetric"
ALPHA_CONF = 0.01
RECALL_FLOOR = 0.5
TGT_BENIGN = 30_000
TGT_ALL = 30_000
VOL_CAP = 2000
OUT = RESULTS / "p1"


def nonconf(p):
    return np.minimum(p, 1 - p)


def conformal_alarm(srcval_proba, srcval_y, tgt_proba, b_null=100, budget=0.01, seed=42):
    """Target abstention rate vs a source two-half null; alarm if it exceeds the (1-budget) qtile."""
    p = np.asarray(srcval_proba)
    y = np.asarray(srcval_y)
    s = nonconf(p)
    sben = s[y == 0]
    q = float(np.quantile(sben, 1 - ALPHA_CONF)) if len(sben) else float(np.quantile(s, 1 - ALPHA_CONF))
    tgt_abstain = float((nonconf(np.asarray(tgt_proba)) > q).mean())
    rng = np.random.default_rng(seed)
    n = len(p)
    null = []
    for _ in range(b_null):
        idx = rng.permutation(n)
        a, bb = idx[: n // 2], idx[n // 2:]
        sa_ben = nonconf(p[a])[y[a] == 0]
        qa = float(np.quantile(sa_ben, 1 - ALPHA_CONF)) if len(sa_ben) else q
        null.append(float((nonconf(p[bb]) > qa).mean()))
    thr = float(np.quantile(null, 1 - budget))
    return bool(tgt_abstain > thr), tgt_abstain, thr


def atc_conf_alarm(srcval_proba, source_acc, tgt_proba, seed=42, b=100, budget=0.01):
    rng = np.random.default_rng(seed)
    p = np.asarray(srcval_proba)
    n = len(p)
    atc, cd = [], []
    for _ in range(b):
        idx = rng.permutation(n)
        a, bb = idx[: n // 2], idx[n // 2:]
        cs = confidence_scores(p[a], p[bb], source_acc)
        atc.append(source_acc - cs["atc_estimated_accuracy"])
        cd.append(cs["mean_confidence_drop"])
    q = 1 - budget
    cs = confidence_scores(p, np.asarray(tgt_proba), source_acc)
    return (bool((source_acc - cs["atc_estimated_accuracy"]) > np.quantile(atc, q))
            or bool(cs["mean_confidence_drop"] > np.quantile(cd, q)))


def main():
    rows = []
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
                    pall = score_flows(F.fit, Xall)
                    c_alarm, abstain, _t = conformal_alarm(F.srcval_proba, F.srcval_y, pall, seed=seed)
                    m_alarm = atc_conf_alarm(F.srcval_proba, F.source_acc, pall, seed=seed)
                    rec = {"source": source, "target": target, "model": model, "seed": seed,
                           "conformal_alarm": c_alarm, "conformal_abstain_rate": round(abstain, 4),
                           "model_monitor_alarm": bool(m_alarm), "has_volumetric": has_vol}
                    if has_vol:
                        pv = score_flows(F.fit, Xvol)
                        rec["recall"] = float((pv >= thr).mean())
                        rec["unsafe"] = bool((pv >= thr).mean() < RECALL_FLOOR)
                    rows.append(rec)
                    del F
                    gc.collect()
            del Xall_df, Xall, Xv_df, Xvol
            gc.collect()
            print(f"  {target} seed {seed} ({time.time()-t0:.0f}s)", flush=True)

    (OUT / "matrix_conformal.json").write_text(json.dumps(rows, indent=2))
    vol = [r for r in rows if r.get("has_volumetric")]
    uns = [r for r in vol if r["unsafe"]]
    safe = [r for r in vol if not r["unsafe"]]

    def rate(rs, key):
        return float(np.mean([r[key] for r in rs])) if rs else 0.0
    print(f"\n{len(rows)} configs ({len(vol)} with volumetric, {len(uns)} unsafe)")
    print(f"conformal alarm: on UNSAFE {rate(uns,'conformal_alarm'):.2f}, on SAFE "
          f"{rate(safe,'conformal_alarm'):.2f}  (specificity gap = "
          f"{rate(uns,'conformal_alarm')-rate(safe,'conformal_alarm'):+.2f})")
    print(f"model-monitor alarm: on UNSAFE {rate(uns,'model_monitor_alarm'):.2f}, on SAFE "
          f"{rate(safe,'model_monitor_alarm'):.2f}")


if __name__ == "__main__":
    main()
