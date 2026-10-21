"""Pilot A: does a few attacks' incidence pattern predict the cases the rest of the family breaks?

Usage: python pilot_a.py --data ./data --out results/pilot_a.json
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from richness import predict_union

AGENTDOJO_ATTACKS = [
    "direct", "ignore_previous", "important_instructions",
    "important_instructions_no_model_name", "important_instructions_no_names",
    "important_instructions_no_user_name", "important_instructions_wrong_model_name",
    "important_instructions_wrong_user_name", "injecagent", "tool_knowledge",
]
PREDICTORS = ["best_single", "observed_union", "chao2_extrap", "jack1_extrap", "betabinom"]


def agentdojo_matrix(runs_dir, config="gpt-4o-2024-05-13"):
    rows = []
    for attack in AGENTDOJO_ATTACKS:
        for f in (runs_dir / config).glob(f"*/user_task_*/{attack}/injection_task_*.json"):
            d = json.loads(f.read_text())
            rows.append((d["suite_name"], d["user_task_id"], d["injection_task_id"], attack, bool(d["security"])))
    df = pd.DataFrame(rows, columns=["suite", "user_task", "injection_task", "attack", "breach"])
    Y = df.pivot_table(index=["suite", "user_task", "injection_task"], columns="attack", values="breach", aggfunc="first")
    Y = Y.dropna()[AGENTDOJO_ATTACKS].astype(int)
    return Y


def jbb_matrices(art_dir):
    def truthy(x):
        return x is True or str(x).strip().lower() == "true"

    per_model = {}
    for f in sorted(art_dir.glob("attack-artifacts/*/*/*.json")):
        method = f.parts[-3]
        if method == "test-artifact":
            continue
        d = json.loads(f.read_text())
        model = d["parameters"]["model"]
        col = {int(j["index"]): int(truthy(j.get("jailbroken"))) for j in d["jailbreaks"]}
        per_model.setdefault(model, {})[method] = col
    return {m: pd.DataFrame(cols).sort_index().fillna(0).astype(int) for m, cols in per_model.items()}


def evaluate(Y, max_subsets=300, seed=0):
    """For each k < K: predictors' error (percentage points of cases) against the K-attack union."""
    Y = np.asarray(Y, dtype=int)
    n, K = Y.shape
    truth = (Y.sum(axis=1) > 0).sum()
    rng = np.random.default_rng(seed)
    out = []
    for k in range(2, K):
        subsets = list(itertools.combinations(range(K), k))
        if len(subsets) > max_subsets:
            subsets = [subsets[i] for i in rng.choice(len(subsets), max_subsets, replace=False)]
        errs = {p: [] for p in PREDICTORS}
        for s in subsets:
            pred = predict_union(Y[:, list(s)], K)
            for p in PREDICTORS:
                errs[p].append(100 * (pred[p] - truth) / n)
        out.append({
            "k": k, "n_subsets": len(subsets),
            **{f"{p}_mae": float(np.mean(np.abs(e))) for p, e in errs.items()},
            **{f"{p}_bias": float(np.mean(e)) for p, e in errs.items()},
            **{f"{p}_under": float(np.mean(np.array(e) < 0)) for p, e in errs.items()},
        })
    return {"n_cases": n, "K": K, "union_pct": 100 * truth / n, "best_single_pct": 100 * Y.sum(0).max() / n,
            "mean_single_pct": 100 * Y.mean(0).mean(), "by_k": out}


def synthetic(n=1000, K=10, vulnerable=0.6, rho=0.0, seed=0):
    """Heterogeneous cases; rho = probability each attack after the first copies attack 0's outcome
    (a crude near-duplicate attack family)."""
    rng = np.random.default_rng(seed)
    vuln = rng.random(n) < vulnerable
    p_case = rng.beta(0.6, 1.4, n) * vuln
    strength = rng.uniform(0.5, 1.5, K)
    P = np.clip(p_case[:, None] * strength[None, :], 0, 1)
    Y = (rng.random((n, K)) < P).astype(int)
    if rho > 0:
        copy = rng.random((n, K)) < rho
        copy[:, 0] = False
        Y = np.where(copy, Y[:, [0]], Y)
    return Y


def summarise(res, label):
    lines = [f"\n### {label}: n={res['n_cases']}, K={res['K']}, union over K = {res['union_pct']:.1f}%, "
             f"best single = {res['best_single_pct']:.1f}%, mean single = {res['mean_single_pct']:.1f}%",
             "| k | " + " | ".join(f"{p} MAE (bias)" for p in PREDICTORS) + " |",
             "|---|" + "---|" * len(PREDICTORS)]
    for r in res["by_k"]:
        lines.append(f"| {r['k']} | " + " | ".join(f"{r[p+'_mae']:.2f} ({r[p+'_bias']:+.1f}; {100*r[p+'_under']:.0f}% under)" for p in PREDICTORS) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="./data")
    ap.add_argument("--out", default="results/pilot_a.json")
    args = ap.parse_args()
    data = Path(args.data)
    results, report = {}, []

    Y = agentdojo_matrix(data / "agentdojo" / "runs")
    results["agentdojo_gpt4o"] = evaluate(Y.values)
    report.append(summarise(results["agentdojo_gpt4o"], "AgentDojo GPT-4o-2024-05-13, 10 integrity attacks"))
    # The five name-variants of important_instructions are near-duplicates; repeat with one of them.
    distinct = ["direct", "ignore_previous", "important_instructions", "injecagent", "tool_knowledge"]
    results["agentdojo_gpt4o_distinct5"] = evaluate(Y[distinct].values)
    report.append(summarise(results["agentdojo_gpt4o_distinct5"], "AgentDojo GPT-4o, 5 distinct attack families"))

    for model, M in jbb_matrices(data / "jbb_artifacts").items():
        results[f"jbb_{model}"] = evaluate(M.values)
        report.append(summarise(results[f"jbb_{model}"], f"JailbreakBench {model}, attacks {list(M.columns)}"))

    for rho in (0.0, 0.5):
        accum = []
        for s in range(20):
            accum.append(evaluate(synthetic(rho=rho, seed=s), max_subsets=60, seed=s))
        by_k = []
        for i, r in enumerate(accum[0]["by_k"]):
            by_k.append({kk: (float(np.mean([a["by_k"][i][kk] for a in accum])) if kk != "k" else r["k"]) for kk in r})
        res = {**{kk: float(np.mean([a[kk] for a in accum])) for kk in ("n_cases", "K", "union_pct", "best_single_pct", "mean_single_pct")}, "by_k": by_k}
        res["n_cases"], res["K"] = int(res["n_cases"]), int(res["K"])
        results[f"synthetic_rho{rho}"] = res
        report.append(summarise(res, f"Synthetic, 20 replicates, near-duplicate rate rho={rho}"))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=1))
    md = Path(args.out).with_suffix(".md")
    md.write_text("# Pilot A results\n\nMAE and mean signed error in percentage points of cases, "
                  "predicting the union over all K attacks from k of them.\n" + "\n".join(report) + "\n")
    print(md.read_text())


if __name__ == "__main__":
    main()
