"""
Publication figures for P-1 (300 dpi, serif, Okabe-Ito colourblind-safe palette from
src.config). Reads results/p1/summary_p1.json and budget_curve.json; Fig 4 rebuilds one config
for the mechanism plot. Writes fig1_*.png .. fig4_*.png into research-opportunities/p1/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import OKABE, FIG_DPI, RESULTS  # noqa: E402

plt.rcParams.update({
    "font.family": "serif", "font.size": 10, "axes.grid": True,
    "grid.alpha": 0.3, "axes.axisbelow": True, "figure.dpi": FIG_DPI,
})
OUT = Path(__file__).resolve().parent
R = RESULTS / "p1"
CELLS = [("nf_unsw_nb15__LightGBM", "UNSW\nLightGBM"),
         ("nf_unsw_nb15__LogisticRegression", "UNSW\nLogReg"),
         ("nf_unsw_nb15__XGBoost", "UNSW\nXGBoost"),
         ("nf_unsw_nb15__RandomForest", "UNSW\nRandForest"),
         ("nf_bot_iot__LightGBM", "BoT-IoT\nLightGBM"),
         ("nf_bot_iot__LogisticRegression", "BoT-IoT\nLogReg"),
         ("nf_bot_iot__XGBoost", "BoT-IoT\nXGBoost"),
         ("nf_bot_iot__RandomForest", "BoT-IoT\nRandForest")]


def _cells(per):
    return [(lab, per[k]) for k, lab in CELLS if k in per]


def fig1_decomposition(S):
    per = S["per_pair_model"]
    cells = _cells(per)
    labels = [lab for lab, _ in cells]
    latent = [v["latent_hcm_rate"] for _, v in cells]
    proj = [v["projected_hcmr"] for _, v in cells]
    searched = [v["hcmr"] for _, v in cells]
    x = np.arange(len(labels)); w = 0.26
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(x - w, latent, w, label="latent (no attack)", color=OKABE[0])
    ax.bar(x, proj, w, label="projected (no search)", color=OKABE[1])
    ax.bar(x + w, searched, w, label="searched (full attack)", color=OKABE[3])
    ax.set_ylabel("high-confidence-miss rate"); ax.set_ylim(0, 1.05)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("Latent exposure dominates; the search adds only where there is headroom")
    ax.legend(loc="lower center", ncol=3, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig1_hcmr_decomposition.png"); plt.close(fig)


def fig2_monitor_heatmap(S):
    per = S["per_pair_model"]
    cells = _cells(per)
    labels = [lab.replace("\n", " ") for lab, _ in cells]
    mons = ["model_monitor_alarm_natural", "model_monitor_alarm_adversarial"]
    rown = ["model monitors\n(natural)", "model monitors\n(adversarial)"]
    M = np.array([[v[m] for _, v in cells] for m in mons])
    fig, ax = plt.subplots(figsize=(9, 2.6))
    im = ax.imshow(M, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
    ax.set_yticks(range(len(rown))); ax.set_yticklabels(rown, fontsize=8)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i,j]:.1f}", ha="center", va="center", fontsize=8)
    ax.set_title("ATC / confidence-drop alarm rate (1 = fires). Silent where the detector is worst.")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout(); fig.savefig(OUT / "fig2_monitor_alarm_heatmap.png"); plt.close(fig)


def fig3_budget():
    p = R / "budget_curve.json"
    if not p.exists():
        return
    rows = json.loads(p.read_text())
    budgets = sorted(set(r["budget"] for r in rows))
    fig, ax = plt.subplots(figsize=(6, 4))
    combos = sorted(set((r["source"], r["model"]) for r in rows))
    for i, (s, m) in enumerate(combos):
        ys = [np.mean([r["hcmr"] for r in rows if r["source"] == s and r["model"] == m
                       and r["budget"] == b]) for b in budgets]
        ax.plot(budgets, ys, marker="o", color=OKABE[i % len(OKABE)],
                label=f"{s.split('_')[1]}/{m[:5]}")
    ax.set_xlabel("score-only query budget per flow"); ax.set_ylabel("HCMR")
    ax.set_ylim(0, 1.0); ax.set_title("HCMR is flat in query budget: the margin, not search, is the lever")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout(); fig.savefig(OUT / "fig3_hcmr_vs_budget.png"); plt.close(fig)


def fig4_margin():
    """Mechanism: P(attack) of real vs adversarial flows against threshold and tau_accept."""
    import constraints as C
    import evade as E
    from p1common import build_fit, read_capped, score_flows
    from run_phase3 import tau_accept_from
    bounds = json.loads((R / "constraints.json").read_text())
    source, target, model, seed = "nf_bot_iot", "nf_cse_cic_ids2018", "XGBoost", 42
    b = C.Bounds.from_json(bounds[source]["volumetric"])
    Xa, _, _ = read_capped(target, 0, 2000, seed, family="volumetric")
    Xatk = Xa.to_numpy(float)
    F = build_fit(source, model, seed)
    thr, tau = F.fit.threshold, tau_accept_from(F.srcval_proba, F.srcval_y)
    nat = score_flows(F.fit, Xatk)
    best, bp = E.search(F.fit, Xatk, b, 200, np.random.default_rng(1042), mode="score")
    conf_nat, conf_adv = np.maximum(nat, 1 - nat), np.maximum(bp, 1 - bp)
    fig, ax = plt.subplots(figsize=(6.4, 4))
    bins = np.linspace(0.5, 1.0, 40)
    ax.hist(conf_nat, bins=bins, alpha=0.6, color=OKABE[0], label="natural flows")
    ax.hist(conf_adv, bins=bins, alpha=0.6, color=OKABE[3], label="adversarial flows")
    ax.axvline(tau, color="black", ls="--", lw=1.3, label=f"τ_accept = {tau:.3f}")
    ax.set_xlabel("benign confidence  max(p, 1−p)  (prediction already benign)")
    ax.set_ylabel("flows")
    ax.set_title(f"{source.split('_')[1]}→CSE-CIC / {model}: the search pushes flows over τ_accept")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig4_confidence_margin.png"); plt.close(fig)


def fig5_matrix():
    """Latent high-confidence-miss rate across the full NetFlow v2 transfer matrix."""
    p = R / "matrix_latent.json"
    if not p.exists():
        return
    rows = [r for r in json.loads(p.read_text()) if r.get("has_volumetric")]
    ds = ["nf_unsw_nb15", "nf_bot_iot", "nf_ton_iot", "nf_cse_cic_ids2018"]
    short = {"nf_unsw_nb15": "UNSW", "nf_bot_iot": "BoT-IoT", "nf_ton_iot": "ToN-IoT",
             "nf_cse_cic_ids2018": "CSE-CIC"}
    M = np.full((len(ds), len(ds)), np.nan)
    for i, s in enumerate(ds):
        for j, t in enumerate(ds):
            if s == t:
                continue
            vals = [r["latent_hcm_rate"] for r in rows if r["source"] == s and r["target"] == t]
            if vals:
                M[i, j] = np.mean(vals)
    fig, ax = plt.subplots(figsize=(6.2, 5))
    im = ax.imshow(M, cmap="OrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(ds))); ax.set_xticklabels([short[d] for d in ds], fontsize=9)
    ax.set_yticks(range(len(ds))); ax.set_yticklabels([short[d] for d in ds], fontsize=9)
    ax.set_xlabel("target network"); ax.set_ylabel("source network (trained on)")
    for i in range(len(ds)):
        for j in range(len(ds)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=9,
                        color="white" if M[i, j] > 0.6 else "black")
    ax.set_title("Latent high-confidence-miss rate (mean over 4 models, 5 seeds)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(OUT / "fig5_latent_matrix.png"); plt.close(fig)


def fig6_silent_by_model(S):
    """Both-monitors-silent rate per model across the full matrix: latent vs under attack."""
    mx, ma = S.get("matrix"), S.get("matrix_attack")
    if not (mx and ma):
        return
    models = ["LightGBM", "LogisticRegression", "XGBoost", "RandomForest"]
    short = ["LightGBM", "LogReg", "XGBoost", "RandForest"]
    lat = [mx["per_model"][m]["both_monitors_silent_rate"] for m in models]
    adv = [ma["per_model"][m]["both_monitors_silent_rate"] for m in models]
    x = np.arange(len(models)); w = 0.38
    fig, ax = plt.subplots(figsize=(6.4, 4))
    ax.bar(x - w / 2, lat, w, label="latent (no attack)", color=OKABE[0])
    ax.bar(x + w / 2, adv, w, label="under attack", color=OKABE[3])
    ax.set_xticks(x); ax.set_xticklabels(short)
    ax.set_ylabel("fraction of configs with both model-monitors silent")
    ax.set_ylim(0, max(max(lat), max(adv)) * 1.25 + 0.05)
    ax.set_title("Monitor blindness is model-dependent (240 configs)")
    for i, (a, b) in enumerate(zip(lat, adv)):
        ax.text(i - w / 2, a + 0.01, f"{a:.2f}", ha="center", fontsize=8)
        ax.text(i + w / 2, b + 0.01, f"{b:.2f}", ha="center", fontsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig6_silent_by_model.png"); plt.close(fig)


def main():
    S = json.loads((R / "summary_p1.json").read_text())
    fig1_decomposition(S)
    fig2_monitor_heatmap(S)
    fig3_budget()
    fig4_margin()
    fig5_matrix()
    fig6_silent_by_model(S)
    print("wrote fig1..fig6 PNGs")


if __name__ == "__main__":
    main()
