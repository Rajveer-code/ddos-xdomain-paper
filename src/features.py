"""
Semantic feature taxonomy — the instrument for the paper's central experiment.

The hypothesis under test is that flow features split into two groups that behave very
differently under domain shift:

* **capacity features** describe how much traffic moved and how fast. Their values are
  set by the *testbed's* link speed, host count and generator configuration as much as by
  the attack. A model that leans on them is partly fitting the measurement apparatus.
* **semantic features** describe what the endpoints actually did — protocol, flags,
  TTLs, retransmissions. These should survive a change of network.

Every one of the 39 shared NetFlow v2 features is assigned exactly one class, asserted at
import.

`DNS_QUERY_ID` is held out in its own class. It was originally included as a null
control on the assumption that a 16-bit DNS transaction ID is random noise, so any
accuracy from it would be memorisation by definition. Measurement refuted that:

    dataset              P(attack | id == 0)   P(attack | id != 0)
    NF-CSE-CIC-IDS2018          0.741                 0.000
    NF-BoT-IoT                  0.785                 0.000
    NF-UNSW-NB15                0.051                 0.001
    NF-ToN-IoT                  0.528                 0.427

The field is zero for every non-DNS flow, so it is not an identifier at all -- it is a
one-bit "this flow is DNS" indicator, and in three of four datasets DNS traffic is
essentially never labelled as attack. It is kept separate precisely because it is the
crudest possible protocol signal, which makes it the natural yardstick: any feature set
that cannot beat one protocol bit out-of-domain is not carrying transferable knowledge.
"""

from __future__ import annotations

# --------------------------------------------------------------- NetFlow v2 taxonomy

NETFLOW_TAXONOMY: dict[str, tuple[str, ...]] = {
    "rate_throughput": (
        "SRC_TO_DST_SECOND_BYTES",
        "DST_TO_SRC_SECOND_BYTES",
        "SRC_TO_DST_AVG_THROUGHPUT",
        "DST_TO_SRC_AVG_THROUGHPUT",
    ),
    "duration_timing": (
        "FLOW_DURATION_MILLISECONDS",
        "DURATION_IN",
        "DURATION_OUT",
    ),
    "size_volume": (
        "IN_BYTES", "OUT_BYTES", "IN_PKTS", "OUT_PKTS",
        "LONGEST_FLOW_PKT", "SHORTEST_FLOW_PKT",
        "MIN_IP_PKT_LEN", "MAX_IP_PKT_LEN",
        "NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES",
        "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES",
        "NUM_PKTS_1024_TO_1514_BYTES",
    ),
    "header_protocol": (
        "PROTOCOL", "L7_PROTO", "MIN_TTL", "MAX_TTL",
        "TCP_WIN_MAX_IN", "TCP_WIN_MAX_OUT",
        "ICMP_TYPE", "ICMP_IPV4_TYPE",
        "DNS_QUERY_TYPE", "DNS_TTL_ANSWER", "FTP_COMMAND_RET_CODE",
    ),
    "flags_behaviour": (
        "TCP_FLAGS", "CLIENT_TCP_FLAGS", "SERVER_TCP_FLAGS",
        "RETRANSMITTED_IN_BYTES", "RETRANSMITTED_IN_PKTS",
        "RETRANSMITTED_OUT_BYTES", "RETRANSMITTED_OUT_PKTS",
    ),
    "identifier": (
        "DNS_QUERY_ID",
    ),
}

#: The two super-groups the central hypothesis contrasts.
CAPACITY_CLASSES = ("rate_throughput", "duration_timing", "size_volume")
SEMANTIC_CLASSES = ("header_protocol", "flags_behaviour")
CONTROL_CLASSES = ("identifier",)


def class_of(feature: str) -> str:
    """Semantic class for one feature name."""
    for cls, feats in NETFLOW_TAXONOMY.items():
        if feature in feats:
            return cls
    raise KeyError(f"{feature!r} has no assigned semantic class")


def features_in(classes: tuple[str, ...] | list[str]) -> list[str]:
    """All features belonging to the given classes."""
    return [f for c in classes for f in NETFLOW_TAXONOMY[c]]


def all_features() -> list[str]:
    return [f for feats in NETFLOW_TAXONOMY.values() for f in feats]


def capacity_features() -> list[str]:
    return features_in(CAPACITY_CLASSES)


def semantic_features() -> list[str]:
    return features_in(SEMANTIC_CLASSES)


def ablation_sets() -> dict[str, list[str]]:
    """
    The feature sets the B1 experiment trains on.

    ``all``                     every shared feature (the usual practice)
    ``drop_<class>``            leave-one-class-out
    ``only_<class>``            one-class-only
    ``capacity_only``           the apparatus-bound features alone
    ``semantic_only``           the behaviour-bound features alone
    ``no_capacity``             the central intervention
    ``no_identifier``           sanity: dropping a pure ID should cost nothing
    """
    every = all_features()
    sets: dict[str, list[str]] = {"all": every}
    for cls in NETFLOW_TAXONOMY:
        sets[f"drop_{cls}"] = [f for f in every if class_of(f) != cls]
        sets[f"only_{cls}"] = list(NETFLOW_TAXONOMY[cls])
    sets["capacity_only"] = capacity_features()
    sets["semantic_only"] = semantic_features()
    sets["no_capacity"] = [f for f in every if class_of(f) not in CAPACITY_CLASSES]
    sets["no_identifier"] = [f for f in every if class_of(f) not in CONTROL_CLASSES]
    return sets


def validate(shared_features: list[str]) -> None:
    """Assert the taxonomy exactly covers the observed shared feature space."""
    taxo = set(all_features())
    obs = set(shared_features)
    if taxo != obs:
        raise AssertionError(
            "Taxonomy does not match the observed NetFlow v2 feature space.\n"
            f"  in taxonomy, not in data: {sorted(taxo - obs)}\n"
            f"  in data, not in taxonomy: {sorted(obs - taxo)}"
        )
    counts: dict[str, int] = {}
    for f in shared_features:
        counts[class_of(f)] = counts.get(class_of(f), 0) + 1
    if sum(counts.values()) != len(shared_features):
        raise AssertionError("A feature was assigned to more than one class")


# ----------------------------------------------------------- CICFlowMeter taxonomy

#: Substring rules for the secondary CICFlowMeter study, where column names vary between
#: releases. Longest match wins, same as the attack taxonomy.
CIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "rate_throughput": ("bytes/s", "packets/s", "byts/s", "pkts/s", "rate"),
    "duration_timing": ("duration", "iat", "active", "idle"),
    "size_volume": ("length", "len", "size", "total fwd", "total backward",
                    "total packets", "bytes", "packets", "bulk", "segment"),
    "header_protocol": ("protocol", "header", "window", "init_win", "ttl"),
    "flags_behaviour": ("flag", "count", "ratio", "urg", "psh", "ack",
                        "syn", "fin", "rst", "cwe", "ece"),
}


def cic_class_of(feature: str) -> str:
    """Semantic class for a CICFlowMeter column; 'unclassified' if no rule matches."""
    low = feature.strip().lower()
    best: tuple[int, str] | None = None
    for cls, pats in CIC_PATTERNS.items():
        for p in pats:
            if p in low and (best is None or len(p) > best[0]):
                best = (len(p), cls)
    return best[1] if best else "unclassified"


def _self_check() -> None:
    every = all_features()
    assert len(every) == len(set(every)), "duplicate feature in taxonomy"
    assert len(every) == 39, f"expected 39 shared features, taxonomy has {len(every)}"
    assert len(capacity_features()) == 20, "capacity group changed unexpectedly"
    assert len(semantic_features()) == 18, "semantic group changed unexpectedly"
    assert class_of("SRC_TO_DST_AVG_THROUGHPUT") == "rate_throughput"
    assert class_of("TCP_FLAGS") == "flags_behaviour"
    assert class_of("DNS_QUERY_ID") == "identifier"
    assert "SRC_TO_DST_AVG_THROUGHPUT" not in ablation_sets()["no_capacity"]
    assert "TCP_FLAGS" in ablation_sets()["no_capacity"]
    assert cic_class_of("Flow Bytes/s") == "rate_throughput"
    assert cic_class_of(" Flow Duration") == "duration_timing"
    assert cic_class_of("SYN Flag Count") == "flags_behaviour"


_self_check()


if __name__ == "__main__":
    print(f"{len(all_features())} shared NetFlow v2 features\n")
    for cls, feats in NETFLOW_TAXONOMY.items():
        group = ("capacity" if cls in CAPACITY_CLASSES
                 else "semantic" if cls in SEMANTIC_CLASSES else "control")
        print(f"  {cls:18s} ({group:8s}) n={len(feats):2d}  {', '.join(feats)}")
    print(f"\ncapacity={len(capacity_features())}  semantic={len(semantic_features())}")
    print(f"\nablation sets: {list(ablation_sets())}")
