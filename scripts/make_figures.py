"""
Regenerate every manuscript figure from results/*.json.

No figure reads a dataset and none contains a hand-entered number. Delete figures/ and
rerun to reproduce the whole set.

    python scripts/make_figures.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import FIGURES, OKABE, RESULTS

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

SHORT = {"nf_cse_cic_ids2018": "IDS2018", "nf_bot_iot": "BoT-IoT",
         "nf_ton_iot": "ToN-IoT", "nf_unsw_nb15": "UNSW",
         "cic_ddos2019": "DDoS2019", "cic_ids2017": "IDS2017",
         "cic_ids2017_fixed": "IDS2017-fix"}
ORDER = ["nf_cse_cic_ids2018", "nf_bot_iot", "nf_ton_iot", "nf_unsw_nb15"]

_n = 0
MANIFEST: list[dict] = []


def save(fig, name: str, caption: str) -> None:
    global _n
    _n += 1
    fname = f"fig{_n}_{name}.png"
    fig.savefig(FIGURES / fname)
    plt.close(fig)
    MANIFEST.append({"n": _n, "file": fname, "caption": caption})
    print(f"  fig{_n}: {fname}")


def load(name: str):
    p = RESULTS / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def mean(vals):
    a = np.asarray([v for v in vals if np.isfinite(v)], dtype=float)
    return float(a.mean()) if len(a) else float("nan")


# ------------------------------------------------------------------ fig: the gap
def fig_gap(matrix):
    rows = [r for r in matrix["rows"] if r["model"] == "LightGBM"]
    ind = defaultdict(list)
    ext = defaultdict(list)
    for r in rows:
        if r["kind"] == "in_domain":
            ind[r["source"]].append(r["metrics"]["macro_f1"])
        else:
            ext[(r["source"], r["target"])].append(r["metrics"]["macro_f1"])

    pairs = sorted(ext, key=lambda k: mean(ext[k]))
    labels = [f"{SHORT[s]}→{SHORT[t]}" for s, t in pairs]
    e = [mean(ext[p]) for p in pairs]
    i = [mean(ind[s]) for s, _ in pairs]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = np.arange(len(pairs))
    for k, (a, b) in enumerate(zip(i, e)):
        ax.plot([b, a], [y[k], y[k]], color="0.75", lw=2, zorder=1)
    ax.scatter(i, y, s=34, color=OKABE[0], label="in-domain (source held-out)", zorder=3)
    ax.scatter(e, y, s=34, color=OKABE[3], label="external (target)", zorder=3)
    ax.set_yticks(y, labels, fontsize=8)
    ax.set_xlabel("macro-F1")
    ax.set_xlim(0, 1)
    ax.axvline(0.5, color="0.6", ls=":", lw=1)
    ax.set_title("Near-perfect in-domain, near chance out-of-domain")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    save(fig, "generalization_gap",
         "In-domain versus external macro-F1 for all 12 ordered pairs, LightGBM, "
         "mean over 5 seeds.")


# --------------------------------------------------------- fig: AUC matrix (inversion)
def fig_auc_matrix(matrix):
    rows = [r for r in matrix["rows"] if r["model"] == "LightGBM"]
    M = np.full((len(ORDER), len(ORDER)), np.nan)
    for r in rows:
        si, ti = ORDER.index(r["source"]), ORDER.index(r["target"])
        vals = [x["metrics"]["roc_auc"] for x in rows
                if x["source"] == r["source"] and x["target"] == r["target"]]
        M[si, ti] = mean(vals)

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(M, cmap="RdBu_r", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(ORDER)), [SHORT[k] for k in ORDER], rotation=30, ha="right")
    ax.set_yticks(range(len(ORDER)), [SHORT[k] for k in ORDER])
    ax.set_xlabel("target"); ax.set_ylabel("source")
    for a in range(len(ORDER)):
        for b in range(len(ORDER)):
            if np.isfinite(M[a, b]):
                ax.text(b, a, f"{M[a, b]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(M[a, b] - 0.5) > 0.28 else "black")
    ax.set_title("External ROC-AUC: blue cells rank attacks below benign")
    fig.colorbar(im, ax=ax, fraction=0.046, label="ROC-AUC")
    save(fig, "auc_matrix",
         "External ROC-AUC per ordered pair. Values below 0.5 indicate the ranking "
         "inverts in the target domain.")


# ------------------------------------------------ fig: ranking vs threshold failure
def fig_decomposition(matrix):
    agg = defaultdict(lambda: {"r": [], "t": [], "auc": []})
    for r in matrix["rows"]:
        if r["kind"] != "external" or r["model"] != "LightGBM":
            continue
        k = (r["source"], r["target"])
        agg[k]["r"].append(r["decomposition"]["ranking_loss"])
        agg[k]["t"].append(r["decomposition"]["threshold_loss"])
        agg[k]["auc"].append(r["metrics"]["roc_auc"])

    fig, ax = plt.subplots(figsize=(5.8, 5.0))
    for (s, t), v in agg.items():
        x, y = mean(v["r"]), mean(v["t"])
        ax.scatter(x, y, s=46, color=OKABE[0] if x > y else OKABE[2], zorder=3)
        ax.annotate(f"{SHORT[s]}→{SHORT[t]}", (x, y), fontsize=7,
                    xytext=(4, 4), textcoords="offset points")
    lim = 1.0
    ax.plot([0, lim], [0, lim], "k--", lw=1, zorder=1)
    ax.text(0.72, 0.60, "threshold-limited\n(recalibration helps)", fontsize=7.5,
            color=OKABE[2], ha="center")
    ax.text(0.62, 0.06, "ranking-limited\n(recalibration cannot help)", fontsize=7.5,
            color=OKABE[0], ha="center")
    ax.set_xlabel("ranking loss  (in-domain AUC − external AUC)")
    ax.set_ylabel("threshold loss  (oracle − stale threshold, macro-F1)")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_title("How each pair fails")
    ax.grid(alpha=0.3)
    save(fig, "failure_decomposition",
         "Ranking loss versus threshold loss per ordered pair. Points below the "
         "diagonal fail representationally; only one pair lies above it.")


# ------------------------------------------------------------- fig: B1 size effect
def fig_feature_sets(abl):
    agg = defaultdict(lambda: {"k": 0, "i": [], "e": []})
    for r in abl["rows"]:
        a = agg[r["feature_set"]]
        a["k"] = r["n_features"]
        a["i"].append(r["indomain"]["macro_f1"])
        a["e"].append(r["external_mean_macro_f1"])

    names = list(agg)
    ks = np.array([agg[n]["k"] for n in names], dtype=float)
    ii = np.array([mean(agg[n]["i"]) for n in names])
    ee = np.array([mean(agg[n]["e"]) for n in names])

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))
    ax = axes[0]
    ax.scatter(ii, ee, s=44, c=ks, cmap="viridis", zorder=3)
    for n, a, b in zip(names, ii, ee):
        if n in {"all", "only_identifier", "only_duration_timing",
                 "only_rate_throughput", "no_capacity", "semantic_only"}:
            ax.annotate(f"{n} (k={agg[n]['k']})", (a, b), fontsize=7,
                        xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("in-domain macro-F1"); ax.set_ylabel("external macro-F1")
    ax.set_title("In-domain gain is bought with external loss")
    ax.grid(alpha=0.3)

    ax = axes[1]
    o = np.argsort(ks)
    ax.plot(ks[o], ee[o], "o-", color=OKABE[3], label="external", zorder=3)
    ax.plot(ks[o], ii[o], "s-", color=OKABE[0], label="in-domain", zorder=3)
    ax.set_xscale("log")
    ax.set_xlabel("number of features (log)"); ax.set_ylabel("macro-F1")
    ax.set_title("Smaller feature sets transfer better")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    save(fig, "feature_set_size",
         "Feature-set size against in-domain and external macro-F1. The single-feature "
         "set attains the best external score of any subset tested.")


# --------------------------------------------------------- fig: B2 gap forecasting
def fig_forecast(div, fc):
    rows = div["rows"]
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.6))
    for ax, key, nice in [
        (axes[0], "atc_estimated_accuracy", "ATC estimated accuracy"),
        (axes[1], "proxy_a_distance", "proxy A-distance"),
        (axes[2], "mmd_rbf", "RBF-MMD"),
    ]:
        x = np.array([r[key] for r in rows], dtype=float)
        y = np.array([r["gap_macro_f1"] for r in rows], dtype=float)
        ax.scatter(x, y, s=26, color=OKABE[0], alpha=0.8, zorder=3)
        stat = fc.get("gap_macro_f1", {}).get(key)
        if stat:
            ax.set_title(f"{nice}\nrho = {stat['spearman']:+.3f} "
                         f"[{stat['ci_lo']:+.2f}, {stat['ci_hi']:+.2f}]", fontsize=9)
        ax.set_xlabel(nice); ax.grid(alpha=0.3)
    axes[0].set_ylabel("observed gap (macro-F1)")
    fig.suptitle("Only the model's own confidence predicts the loss; "
                 "distribution distance does not", fontweight="bold", fontsize=10)
    save(fig, "gap_forecast",
         "Observed generalization gap against three label-free predictors, with "
         "Spearman correlation and bootstrap CI.")


# ------------------------------------------------------------- fig: B3/B4 remedies
def fig_remedies(cal, budget):
    agg = defaultdict(lambda: defaultdict(list))
    for r in cal["rows"]:
        k = (r["source"], r["target"])
        agg[k]["src"].append(r["f1_source_threshold"])
        agg[k]["bq"].append(r["f1_benign_quantile"])
        agg[k]["or"].append(r["f1_oracle_threshold"])
        agg[k]["auc"].append(r["auc_external"])

    pairs = sorted(agg, key=lambda k: -mean(agg[k]["auc"]))
    y = np.arange(len(pairs))
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.barh(y - 0.26, [mean(agg[p]["src"]) for p in pairs], 0.26,
            label="source threshold (0 labels)", color=OKABE[3])
    ax.barh(y, [mean(agg[p]["bq"]) for p in pairs], 0.26,
            label="benign-quantile recalibration (0 labels)", color=OKABE[2])
    ax.barh(y + 0.26, [mean(agg[p]["or"]) for p in pairs], 0.26,
            label="oracle threshold (all labels)", color=OKABE[0])
    ax.set_yticks(y, [f"{SHORT[s]}→{SHORT[t]}  (AUC {mean(agg[(s,t)]['auc']):.2f})"
                      for s, t in pairs], fontsize=7.5)
    ax.set_xlabel("external macro-F1")
    ax.set_title("Recalibration rescues only the pair whose ranking survived")
    ax.legend(fontsize=7.5, loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    save(fig, "remedies",
         "External macro-F1 under the deployed threshold, zero-label benign-quantile "
         "recalibration, and the all-labels oracle, ordered by external AUC.")

    if budget:
        by_k = defaultdict(lambda: defaultdict(list))
        for r in budget["rows"]:
            by_k[r["k"]]["re"].append(r["f1_rethreshold"])
            by_k[r["k"]]["ft"].append(r["f1_finetune"])
        ks = sorted(by_k)
        fig, ax = plt.subplots(figsize=(6.0, 4.0))
        ax.plot(ks, [mean(by_k[k]["re"]) for k in ks], "o-", color=OKABE[1],
                label="re-tune threshold on k labels")
        ax.plot(ks, [mean(by_k[k]["ft"]) for k in ks], "s-", color=OKABE[4],
                label="retrain on source + k labels")
        ax.set_xlabel("labelled target flows (k)"); ax.set_ylabel("external macro-F1")
        ax.set_title("How many target labels buy the gap back")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        save(fig, "label_budget",
             "External macro-F1 against the number of labelled target flows, averaged "
             "over all ordered pairs and seeds.")


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    matrix, abl = load("transfer_matrix"), load("feature_ablation")
    div, fc = load("divergence"), load("gap_forecast")
    cal, budget = load("calibration"), load("label_budget")

    print("Regenerating figures from results/:")
    if matrix:
        fig_gap(matrix); fig_auc_matrix(matrix); fig_decomposition(matrix)
    if abl:
        fig_feature_sets(abl)
    if div and fc:
        fig_forecast(div, fc)
    if cal:
        fig_remedies(cal, budget)

    (FIGURES / "MANIFEST.json").write_text(
        json.dumps(MANIFEST, indent=2), encoding="utf-8")
    print(f"\n{len(MANIFEST)} figures written to {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
