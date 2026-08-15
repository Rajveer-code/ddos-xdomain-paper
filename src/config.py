"""
Single source of truth for paths, seeds and the dataset registry.

Nothing else in this codebase may hardcode a filesystem path or a magic constant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ----------------------------------------------------------------------------- PATHS

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
RESULTS = PROJECT / "results"
FIGURES = PROJECT / "figures"
MODELS = PROJECT / "models"
PAPER = PROJECT / "paper"
CONFIGS = PROJECT / "configs"

for _d in (DATA, RESULTS, FIGURES, MODELS, CONFIGS):
    _d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------- CONSTANTS

SEED = 42
SEEDS = (42, 43, 44, 45, 46)  # multi-seed runs: seed variance is reported separately
TEST_SIZE = 0.20
CV_FOLDS = 5
N_BOOT = 2000  # bootstrap resamples for 95% CIs

# Memory guard for the sweep. NF-CSE-CIC-IDS2018-v2 alone is ~18.9M flows; the full-data
# confirmation run overrides this with SAMPLE_N_PER_CLASS = None.
SAMPLE_N_PER_CLASS = 200_000

# Publication figure defaults: serif, 300 dpi, Okabe-Ito (colourblind-safe).
FIG_DPI = 300
OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442"]

# --------------------------------------------------------------------- LEAKY COLUMNS

# Identity / socket / bookkeeping columns. Keeping any of these lets a model memorise the
# testbed's addressing plan instead of learning attack behaviour (Arp et al., 2022).
LEAKY_COLS = {
    "unnamed: 0", "flow id", "fwd id",
    "source ip", "src ip", "destination ip", "dst ip", "ipv4_src_addr", "ipv4_dst_addr",
    "source port", "src port", "destination port", "dst port",
    "l4_src_port", "l4_dst_port",
    "timestamp", "simillarhttp", "similarhttp", "inbound",
    "attack", "dataset",
}

# ------------------------------------------------------------------ DATASET REGISTRY


@dataclass(frozen=True)
class Dataset:
    """One source dataset: where it comes from and how to read it."""

    key: str
    kaggle_ref: str
    family: str          # "netflow_v2" (43 common features) or "cicflowmeter"
    label_col: str
    note: str
    globs: tuple[str, ...] = field(default=("**/*.parquet",))

    @property
    def path(self) -> Path:
        return DATA / self.key


#: The NetFlow v2 quartet (Sarhan et al., 2021) shares 43 identical features, which is what
#: makes cross-dataset transfer claims legitimate rather than an artefact of column
#: intersection. This is the primary study.
NETFLOW_V2 = [
    Dataset("nf_cse_cic_ids2018", "dhoogla/nfcsecicids2018v2", "netflow_v2", "Attack",
            "CSE-CIC-IDS2018 in NetFlow v2 form; enterprise testbed, DDoS/DoS families"),
    Dataset("nf_bot_iot", "dhoogla/nfbotiotv2", "netflow_v2", "Attack",
            "BoT-IoT in NetFlow v2 form; IoT testbed, heavily attack-dominated"),
    Dataset("nf_ton_iot", "dhoogla/nftoniotv2", "netflow_v2", "Attack",
            "ToN-IoT in NetFlow v2 form; IoT/telemetry testbed"),
    Dataset("nf_unsw_nb15", "dhoogla/nfunswnb15v2", "netflow_v2", "Attack",
            "UNSW-NB15 in NetFlow v2 form; DoS present, DDoS absent"),
]

#: The CICFlowMeter pairing the literature usually uses. Kept as a secondary study so the
#: paper can show what happens when harmonisation is done the conventional, ad-hoc way.
CICFLOWMETER = [
    Dataset("cic_ddos2019", "dhoogla/cicddos2019", "cicflowmeter", "Label",
            "CIC-DDoS2019; reflection/amplification and volumetric DDoS"),
    Dataset("cic_ids2017", "dhoogla/cicids2017", "cicflowmeter", "Label",
            "CICIDS2017, original labels"),
    Dataset("cic_ids2017_fixed", "dhoogla/distrinetcicids2017", "cicflowmeter", "Label",
            "DistriNet-corrected CICIDS2017 (Engelen et al., WTMC 2021); isolates label noise"),
]

DATASETS = {d.key: d for d in (*NETFLOW_V2, *CICFLOWMETER)}

# ------------------------------------------------------------------ ATTACK TAXONOMY

#: Attack-family taxonomy. Dataset-level transfer numbers hide the mechanism; the paper
#: reports transfer per family. Matching is done on lowercased label substrings, longest
#: match first, and every unmatched label is reported rather than silently bucketed.
FAMILY_PATTERNS: dict[str, tuple[str, ...]] = {
    "volumetric": ("syn", "udp", "udplag", "udp-lag", "tftp", "loic", "hoic",
                   "ddos", "dos hulk", "hulk", "goldeneye"),
    "reflection_amplification": ("dns", "ldap", "mssql", "netbios", "ntp", "snmp",
                                 "ssdp", "portmap", "chargen", "memcached"),
    "low_rate_application": ("slowloris", "slowhttptest", "slowhttp", "rudy",
                             "slow", "http flood"),
}

BENIGN_LABELS = {"benign", "normal", "background", "0"}


def summary() -> str:
    lines = [f"project : {PROJECT}", f"seeds   : {SEEDS}", ""]
    for fam in ("netflow_v2", "cicflowmeter"):
        lines.append(f"[{fam}]")
        for d in DATASETS.values():
            if d.family == fam:
                lines.append(f"  {d.key:22s} {d.kaggle_ref:32s} {d.note}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
