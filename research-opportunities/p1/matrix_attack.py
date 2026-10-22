"""
Adversarial generality: run the constrained score-only search across the FULL NetFlow v2 matrix
(all 12 ordered pairs × 4 models × 5 seeds), not just the two representative pairs. For each
config this records the searched high-confidence-miss rate, the latent rate, and the cheap
model-based monitor alarms (ATC, confidence drop) during the attack — so we can count how many
cells across the whole quartet show the dangerous pairing (high adversarial HCMR + silent
monitor), removing the "one cell" limitation.

Resumable: appends one JSON line per config to results/p1/matrix_attack.jsonl and skips configs
already present, so a restart continues where it stopped. A final pass writes the aggregated
results/p1/matrix_attack.json. Cheap monitors only (no A-distance) to stay ~1 hour.
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
import constraints as C  # noqa: E402
import evade as E  # noqa: E402
from p1common import build_fit, read_capped  # noqa: E402

DATASETS = [d.key for d in NETFLOW_V2]
MODELS = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
SEEDS = [42, 43, 44, 45, 46]
FAMILY = "volumetric"
BUDGET = 200
ATTACK_CAP = 2000
BOUNDS_CAP = 5000
OUT = RESULTS / "p1"
JSONL = OUT / "matrix_attack.jsonl"

_BOUNDS: dict[str, C.Bounds] = {}


def source_bounds(source: str) -> C.Bounds | None:
    if source not in _BOUNDS:
        Xa, _, _ = read_capped(source, 0, BOUNDS_CAP, 42, family=FAMILY)
        if len(Xa) == 0:
            _BOUNDS[source] = None
        else:
            _BOUNDS[source] = C.derive_bounds(Xa.to_numpy(float), FAMILY)
    return _BOUNDS[source]


def tau_at(srcval_proba, srcval_y, budget=0.01):
    conf = np.maximum(srcval_proba, 1 - srcval_proba)
    ben = conf[np.asarray(srcval_y) == 0]
    return float(np.quantile(ben if len(ben) else conf, budget))


def model_monitor_null(srcval_proba, source_acc, b_cheap=100, budget=0.01, seed=42):
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


def done_set() -> set:
    if not JSONL.exists():
        return set()
    out = set()
    for line in JSONL.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out.add((r["source"], r["target"], r["model"], r["seed"]))
    return out


def main():
    done = done_set()
    print(f"resuming: {len(done)} configs already done")
    t0 = time.time()
    with JSONL.open("a") as fh:
        for target in DATASETS:
            for seed in SEEDS:
                todo = [(s, m) for s in DATASETS if s != target for m in MODELS
                        if (s, target, m, seed) not in done]
                if not todo:
                    continue
                Xa, _, _ = read_capped(target, 0, ATTACK_CAP, seed, family=FAMILY)
                if len(Xa) == 0:
                    continue
                Xatk = Xa.to_numpy(float)
                for source, model in todo:
                    b = source_bounds(source)
                    if b is None:
                        continue
                    F = build_fit(source, model, seed)
                    thr = F.fit.threshold
                    tau = tau_at(F.srcval_proba, F.srcval_y)
                    from p1common import score_flows
                    pnat = score_flows(F.fit, Xatk)
                    confnat = np.maximum(pnat, 1 - pnat)
                    latent = float(((pnat < thr) & (confnat >= tau)).mean())
                    best, bp = E.search(F.fit, Xatk, b, BUDGET,
                                        np.random.default_rng(1000 + seed), mode="score")
                    sf = E.success_flags(best, bp, Xatk, b, thr, tau)
                    atc_thr, conf_thr = model_monitor_null(F.srcval_proba, F.source_acc, seed=seed)
                    cs = confidence_scores(F.srcval_proba, bp, F.source_acc)
                    atc_alarm = (F.source_acc - cs["atc_estimated_accuracy"]) > atc_thr
                    conf_alarm = cs["mean_confidence_drop"] > conf_thr
                    rec = {"source": source, "target": target, "model": model, "seed": seed,
                           "latent_hcmr": latent, "searched_hcmr": float(sf["high_conf_miss"].mean()),
                           "feasible_rate": float(sf["feasible"].mean()),
                           "atc_alarm": bool(atc_alarm), "conf_drop_alarm": bool(conf_alarm)}
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    del F, best, bp
                    gc.collect()
                del Xa, Xatk
                gc.collect()
                print(f"  {target} seed {seed}: +{len(todo)} configs ({time.time()-t0:.0f}s)",
                      flush=True)

    # aggregate
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    (OUT / "matrix_attack.json").write_text(json.dumps(rows, indent=2))
    dangerous = [r for r in rows if r["searched_hcmr"] > 0.5
                 and not r["atc_alarm"] and not r["conf_drop_alarm"]]
    print(f"\n{len(rows)} configs. mean searched HCMR {np.mean([r['searched_hcmr'] for r in rows]):.3f}")
    print(f"dangerous (searched HCMR>0.5 AND both model-monitors silent): {len(dangerous)}/{len(rows)}, "
          f"{len({(r['source'],r['target'],r['model']) for r in dangerous})} combos")
    print(f"done ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
