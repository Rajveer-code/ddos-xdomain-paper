"""
Aggregate three secondary experiments into the summary files the manuscript cites.

Produces:
    results/label_budget_summary.json   Table 14 and the abstract's k=0 / k=10 medians,
                                        from results/label_budget_v2.json
    results/feature_count_summary.json  Table 8 and the size/identity decomposition,
                                        from results/feature_count_random.json
    results/family_transfer.json        Table 15, from LightGBM rows of
                                        results/transfer_matrix.json

These summaries were first produced by ad-hoc aggregation that was never committed; this
script is the committed producer, so every cell regenerates from the raw rows.

    python scripts/summarize_secondary.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import RESULTS

BUDGET_METHODS = ["rethreshold", "finetune", "benign_quantile", "oracle", "source_threshold"]
COUNT_METRICS = ["external_macro_f1", "external_auc", "indomain_macro_f1"]
N_BOOT = 2000
SEED = 42


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def dump(name: str, payload: dict) -> None:
    (RESULTS / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote results/{name}")


def spread(vals) -> dict:
    a = np.asarray(vals, dtype=float)
    return {"median": float(np.median(a)), "p5": float(np.percentile(a, 5)),
            "p95": float(np.percentile(a, 95)), "mean": float(a.mean()), "n": int(a.size)}


def bootstrap_spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    n = len(x)
    rs = [spearmanr(x[i], y[i]).statistic for i in (rng.integers(0, n, n) for _ in range(N_BOOT))]
    rs = np.array([r for r in rs if np.isfinite(r)])
    return float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))


def label_budget() -> dict:
    src = load("label_budget_v2.json")
    rows, cfg = src["rows"], src["config"]
    by_k = defaultdict(list)
    for r in rows:
        by_k[r["k"]].append(r)
    per_k = {str(k): {m: spread([r[f"f1_{m}"] for r in rs]) for m in BUDGET_METHODS}
             for k, rs in sorted(by_k.items())}
    per_pair = defaultdict(list)
    for r in by_k[10]:
        per_pair[f'{r["source"]}|{r["target"]}'].append(r["f1_finetune"])
    k10 = {p: {key: v for key, v in spread(vals).items() if key in ("median", "p5", "p95")}
           for p, vals in per_pair.items()}
    return {
        "per_k": per_k,
        "k10_finetune_per_pair": k10,
        "design": {
            "adaptation_pool_fraction": cfg["adapt_fraction"],
            "draws_per_pair_seed_k": cfg["draws"],
            "seeds": cfg["seeds"],
            "n_per_class": cfg["n_per_class"],
            "n_rows": len(rows),
            "note": "disjoint adaptation pool and evaluation set; labels drawn only from pool; "
                    "scored only on evaluation set",
        },
    }


def feature_count() -> dict:
    src = load("feature_count_random.json")
    rows = src["rows"]
    by_k = defaultdict(list)
    for r in rows:
        by_k[r["k"]].append(r)
    per_k = {str(k): {m: spread([r[m] for r in rs]) for m in COUNT_METRICS}
             for k, rs in sorted(by_k.items())}
    ks = np.array([r["k"] for r in rows], dtype=float)
    correlations = {}
    for m in COUNT_METRICS:
        y = np.array([r[m] for r in rows], dtype=float)
        lo, hi = bootstrap_spearman(ks, y)
        correlations[m] = {"spearman": float(spearmanr(ks, y).statistic), "ci_lo": lo, "ci_hi": hi}

    dns = load("paper_aggregates.json")["feature_ablation"]["only_identifier"]
    k_min, k_max = str(min(by_k)), str(max(by_k))
    med = lambda k: per_k[k]["external_macro_f1"]["median"]
    decomposition = {
        "semantic_ablation_total_delta": dns["delta_external_vs_all"],
        "size_component_random_k1_minus_k39": med(k_min) - med(k_max),
        "identity_component_dns_minus_random_k1": dns["external_macro_f1"] - med(k_min),
        "note": "total advantage of the one-feature semantic set over all 39, split into the part "
                "explained by dimensionality alone (random subsets) and the part attributable to "
                "that particular feature",
    }
    seeds = sorted({r["seed"] for r in rows})
    subsets = max(r["subset"] for r in rows) + 1
    return {"per_k": per_k, "correlations": correlations, "decomposition": decomposition,
            "design": {"n_runs": len(rows), "subsets_per_k": subsets, "seeds": seeds,
                       "spearman_ci": f"percentile bootstrap over runs, B={N_BOOT}, seed {SEED}"}}


def family_transfer() -> dict:
    rows = [r for r in load("transfer_matrix.json")["rows"] if r["model"] == "LightGBM"]
    out = {}
    for fam in ("volumetric", "low_rate_application"):
        rec = {"in_domain": [], "external": []}
        n = {"in_domain": 0, "external": 0}
        for r in rows:
            f = r["family"].get(fam)
            if f and f.get("n", 0) > 0 and f.get("recall") is not None:
                rec[r["kind"]].append(f["recall"])
                n[r["kind"]] += f["n"]
        ind, ext = float(np.mean(rec["in_domain"])), float(np.mean(rec["external"]))
        out[fam] = {"in_domain_recall": ind, "external_recall": ext, "drop": ind - ext,
                    "n_in": n["in_domain"], "n_ext": n["external"],
                    "runs_in": len(rec["in_domain"]), "runs_ext": len(rec["external"])}
    fpr = {"in_domain": [], "external": []}
    for r in rows:
        b = r["family"].get("benign")
        if b and b.get("n", 0) > 0:
            fpr[r["kind"]].append(b["fpr"])
    ind, ext = float(np.mean(fpr["in_domain"])), float(np.mean(fpr["external"]))
    out["benign_fpr"] = {"in_domain": ind, "external": ext, "increase": ext - ind}
    out["aggregation"] = ("unweighted mean of per-run values over LightGBM runs that contain the "
                          "family; n_in / n_ext are flows summed over those runs")
    return out


def decomposition_rule() -> dict:
    """
    Count ranking-dominated pairs under two rules. The manuscript's original rule compares
    ranking loss in AUC units with threshold loss in macro-F1 units, which is a convention.
    The same-unit rule splits the macro-F1 gap itself: (in-domain F1 - external F1 at the
    target-optimal threshold) against (that oracle F1 - external F1 at the deployed threshold).
    """
    rows = [r for r in load("transfer_matrix.json")["rows"] if r["kind"] == "external"]
    out = {}
    for model in sorted({r["model"] for r in rows}):
        by_pair = defaultdict(list)
        for r in rows:
            if r["model"] == model:
                by_pair[(r["source"], r["target"])].append(r["decomposition"])
        mixed = same = 0
        for ds in by_pair.values():
            m = lambda f: float(np.mean([d[f] for d in ds]))
            thr = m("threshold_loss")
            mixed += m("ranking_loss") > thr
            same += (m("f1_in") - m("f1_external_oracle_threshold")) > thr
        out[model] = {"n_pairs": len(by_pair), "ranking_dominated_auc_vs_f1": int(mixed),
                      "ranking_dominated_f1_units": int(same)}
    return {"per_model": out, "aggregation": "seed means per ordered pair"}


def target_only_per_pair(k: int = 10) -> dict:
    """
    Per ordered pair at budget k: source+k retraining against learners trained on the same
    k target flows alone (results/label_budget_target_only.json), matched draw for draw,
    with each pair's external AUC. Tests whether the source helps where its ranking survived.
    """
    to = {(r["target"], r["seed"], r["k"], r["draw"]): r
          for r in load("label_budget_target_only.json")["rows"]}
    budget = load("label_budget_v2.json")["rows"]
    aucs, vals = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for b in budget:
        pair = f'{b["source"]}|{b["target"]}'
        if b["k"] == 0:
            aucs[pair].append(b["external_auc"])
        elif b["k"] == k:
            t = to[(b["target"], b["seed"], b["k"], b["draw"])]
            vals[pair]["source_plus_k"].append(b["f1_finetune"])
            vals[pair]["logreg"].append(t["f1_logreg"])
            vals[pair]["nn1"].append(t["f1_nn1"])
    per_pair = {}
    for pair, v in vals.items():
        med = {m: float(np.median(x)) for m, x in v.items()}
        best_target_only = max(med["logreg"], med["nn1"])
        per_pair[pair] = {"external_auc": float(np.mean(aucs[pair])), **med,
                          "source_benefit_vs_best_target_only": med["source_plus_k"] - best_target_only}
    a = np.array([p["external_auc"] for p in per_pair.values()])
    d = np.array([p["source_benefit_vs_best_target_only"] for p in per_pair.values()])
    lo, hi = bootstrap_spearman(a, d)
    return {"k": k, "per_pair": per_pair,
            "n_pairs_source_helps": int((d > 0).sum()),
            "spearman_auc_vs_source_benefit": {"rho": float(spearmanr(a, d).statistic),
                                               "ci_lo": lo, "ci_hi": hi},
            "note": "medians over 20 draws per pair (2 seeds x 10); benefit = source+k minus "
                    "the better of the two target-only learners"}


def main() -> int:
    dump("target_only_per_pair.json", target_only_per_pair())
    dump("decomposition_rule.json", decomposition_rule())
    dump("label_budget_summary.json", label_budget())
    dump("feature_count_summary.json", feature_count())
    dump("family_transfer.json", family_transfer())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
