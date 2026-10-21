"""Pilot B: does a prompt-injection defense stop the attack, or stop the agent?

Usage: python pilot_b.py --data ./data --out results/pilot_b.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

KEY = ["suite", "user_task", "injection_task", "attack"]
STATES = ["clean", "stopped", "hijacked", "both"]
SKIPPED = []


def load(runs_dir, config, attacks):
    rows = []
    for attack in attacks:
        for f in (runs_dir / config).glob(f"*/user_task_*/{attack}/injection_task_*.json"):
            d = json.loads(f.read_text())
            if "utility" not in d or "security" not in d:  # one truncated log in the Llama-3.3 sandwich run
                SKIPPED.append(str(f.relative_to(runs_dir)))
                continue
            rows.append((d["suite_name"], d["user_task_id"], d["injection_task_id"], attack,
                         bool(d["utility"]), bool(d["security"])))
    df = pd.DataFrame(rows, columns=KEY + ["utility", "breach"])
    df["state"] = np.select(
        [df.utility & ~df.breach, ~df.utility & ~df.breach, ~df.utility & df.breach],
        ["clean", "stopped", "hijacked"], "both")
    return df.set_index(KEY)


def benign_utility(runs_dir, config):
    vals = [json.loads(f.read_text())["utility"] for f in (runs_dir / config).glob("*/user_task_*/none/none.json")]
    return float(np.mean(vals)) if vals else float("nan")


def paired(base, defended):
    j = base.join(defended, lsuffix="_0", rsuffix="_1", how="inner")
    return j


def rates(j):
    breached0 = j.breach_0
    nb = breached0.sum()
    return {
        "n": int(len(j)),
        "asr_0": float(j.breach_0.mean()), "asr_1": float(j.breach_1.mean()),
        "ua_0": float(j.utility_0.mean()), "ua_1": float(j.utility_1.mean()),
        "n_breached_0": int(nb),
        "resist": float((breached0 & (j.state_1 == "clean")).sum() / nb),
        "incapacitate": float((breached0 & (j.state_1 == "stopped")).sum() / nb),
        "still_breached": float((breached0 & j.breach_1).sum() / nb),
        "collateral_stop": float(((j.state_0 == "clean") & (j.state_1 == "stopped")).sum() / max(1, (j.state_0 == "clean").sum())),
    }


def cluster_boot(j, stat, n_boot=2000, seed=0):
    """Resample (suite, user_task) clusters with replacement."""
    rng = np.random.default_rng(seed)
    cl = j.reset_index()
    cl["cluster"] = cl.suite + "/" + cl.user_task
    groups = {c: g for c, g in cl.groupby("cluster")}
    names = np.array(list(groups))
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(names, len(names), replace=True)
        g = pd.concat([groups[c] for c in pick])
        if g.breach_0.sum() > 0:  # a resample with no baseline breach has no defined rate
            vals.append(stat(g))
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]


def noise_floor(runs_dir):
    """Clean<->stopped flips between two attack variants that differ only in names (no defense),
    among cases breached under neither: an upper bound on run-to-run utility noise."""
    a = load(runs_dir, "gpt-4o-2024-05-13", ["important_instructions"]).droplevel("attack")
    b = load(runs_dir, "gpt-4o-2024-05-13", ["important_instructions_no_names"]).droplevel("attack")
    j = a.join(b, lsuffix="_0", rsuffix="_1", how="inner")
    nb = j[~j.breach_0 & ~j.breach_1]
    flip = (nb.state_0 != nb.state_1).mean()
    clean_to_stop = ((nb.state_0 == "clean") & (nb.state_1 == "stopped")).sum() / max(1, (nb.state_0 == "clean").sum())
    return {"n": int(len(nb)), "flip_rate": float(flip), "clean_to_stopped": float(clean_to_stop)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="./data")
    ap.add_argument("--out", default="results/pilot_b.json")
    args = ap.parse_args()
    runs = Path(args.data) / "agentdojo" / "runs"

    comparisons = [
        ("gpt-4o-2024-05-13", d, ["important_instructions"])
        for d in ["repeat_user_prompt", "spotlighting_with_delimiting", "tool_filter", "transformers_pi_detector"]
    ] + [
        (m, "repeat_user_prompt", ["direct", "ignore_previous", "important_instructions"])
        for m in ["meta-llama_Llama-3.3-70B-Instruct", "Meta-SecAlign-70B"]
    ]
    out = {"noise_floor": noise_floor(runs), "comparisons": []}
    for model, defense, attacks in comparisons:
        base = load(runs, model, attacks)
        dfd = load(runs, f"{model}-{defense}", attacks)
        j = paired(base, dfd)
        r = rates(j)
        r.update(model=model, defense=defense, attacks=attacks,
                 bu_0=benign_utility(runs, model), bu_1=benign_utility(runs, f"{model}-{defense}"))
        r["incapacitate_ci"] = cluster_boot(j, lambda g: (g.breach_0 & (g.state_1 == "stopped")).sum() / g.breach_0.sum())
        r["resist_ci"] = cluster_boot(j, lambda g: (g.breach_0 & (g.state_1 == "clean")).sum() / g.breach_0.sum())
        r["transitions"] = pd.crosstab(j.state_0, j.state_1).reindex(index=STATES, columns=STATES, fill_value=0).to_dict()
        out["comparisons"].append(r)

    # SecAlign vs Llama-3.3 (the model swap is itself a defense): same cases, same attacks.
    base = load(runs, "meta-llama_Llama-3.3-70B-Instruct", ["direct", "ignore_previous", "important_instructions"])
    sec = load(runs, "Meta-SecAlign-70B", ["direct", "ignore_previous", "important_instructions"])
    j = paired(base, sec)
    r = rates(j)
    r.update(model="meta-llama_Llama-3.3-70B-Instruct", defense="Meta-SecAlign-70B (model swap)",
             attacks=["direct", "ignore_previous", "important_instructions"],
             bu_0=benign_utility(runs, "meta-llama_Llama-3.3-70B-Instruct"), bu_1=benign_utility(runs, "Meta-SecAlign-70B"))
    r["incapacitate_ci"] = cluster_boot(j, lambda g: (g.breach_0 & (g.state_1 == "stopped")).sum() / g.breach_0.sum())
    r["resist_ci"] = cluster_boot(j, lambda g: (g.breach_0 & (g.state_1 == "clean")).sum() / g.breach_0.sum())
    out["comparisons"].append(r)

    out["skipped_logs"] = sorted(set(SKIPPED))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1, default=str))

    nf = out["noise_floor"]
    lines = ["# Pilot B results", "",
             f"Noise floor (GPT-4o, no defense, `important_instructions` vs `_no_names`, {nf['n']} cases breached "
             f"under neither): clean/stopped flip rate {100*nf['flip_rate']:.1f}%, clean→stopped {100*nf['clean_to_stopped']:.1f}%.", "",
             "Among cases the undefended agent let the attacker breach: share the defense moves to *clean* "
             "(user task done, no breach) vs *stopped* (neither). 95% cluster-bootstrap intervals over user tasks.", "",
             "| model | defense | BU 0→1 | UA 0→1 | ASR 0→1 | breached₀ | resist | incapacitate | still breached | collateral clean→stopped |",
             "|---|---|---|---|---|---:|---|---|---:|---:|"]
    for r in out["comparisons"]:
        lines.append(
            f"| {r['model']} | {r['defense']} | {r['bu_0']:.3f}→{r['bu_1']:.3f} | {r['ua_0']:.3f}→{r['ua_1']:.3f} | "
            f"{r['asr_0']:.3f}→{r['asr_1']:.3f} | {r['n_breached_0']} | {r['resist']:.2f} [{r['resist_ci'][0]:.2f}, {r['resist_ci'][1]:.2f}] | "
            f"{r['incapacitate']:.2f} [{r['incapacitate_ci'][0]:.2f}, {r['incapacitate_ci'][1]:.2f}] | {r['still_breached']:.2f} | {r['collateral_stop']:.2f} |")
    md = Path(args.out).with_suffix(".md")
    md.write_text("\n".join(lines) + "\n")
    print(md.read_text())


if __name__ == "__main__":
    main()
