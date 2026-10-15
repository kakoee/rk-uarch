"""B's finite release/ownership witnesses, not an executor or native result producer.

Times are literal picoseconds. Each job row is id, owner, release, dependencies,
ready, grant, end, ps_duration, cycles. None is a public EngineResult.
"""

FREQ_HZ = 1_200_000_000
# Critical rows are kind, cause, start, end. release_offset is NOT resource occupancy.
CASES = {
    "S01-late-release-positive": {
        "jobs": [("c", 0, 835, (), 835, 835, 2500, 0, 1)],
        "critical": [("release_offset", "c", 0, 835), ("service", "c", 835, 2500)],
        "busy": {0: 1665},
        "duration": 2500,
    },
    "S02-dependency-before-release": {
        "jobs": [
            ("a", 1, 0, (), 0, 0, 500, 500, None),
            ("c", 0, 835, ("a",), 835, 835, 2500, 0, 1),
        ],
        "critical": [("release_offset", "c", 0, 835), ("service", "c", 835, 2500)],
        "busy": {0: 1665, 1: 500},
        "duration": 2500,
    },
    "S03-dependency-after-release": {
        "jobs": [
            ("a", 1, 0, (), 0, 0, 1000, 1000, None),
            ("c", 0, 835, ("a",), 1000, 1000, 2500, 0, 1),
        ],
        "critical": [("service", "a", 0, 1000), ("service", "c", 1000, 2500)],
        "busy": {0: 1500, 1: 1000},
        "duration": 2500,
    },
    "S04-busy-owner-positive": {
        "jobs": [("a", 0, 0, (), 0, 0, 3000, 3000, None), ("c", 0, 835, (), 835, 3000, 4167, 0, 1)],
        "critical": [("service", "a", 0, 3000), ("service", "c", 3000, 4167)],
        "busy": {0: 4167},
        "duration": 4167,
    },
    "S05-busy-owner-zero": {
        "jobs": [("a", 0, 0, (), 0, 0, 3000, 3000, None), ("z", 0, 835, (), 835, 3000, 3000, 0, 0)],
        "critical": [("service", "a", 0, 3000)],
        "busy": {0: 3000},
        "duration": 3000,
    },
    "S06-off-edge-owned-zero": {
        "jobs": [("z", 0, 835, (), 835, 835, 835, 0, 0)],
        "critical": [("release_offset", "z", 0, 835)],
        "busy": {0: 0},
        "duration": 835,
    },
    "S07-same-time-release-dependency": {
        "jobs": [
            ("a", 0, 0, (), 0, 0, 1000, 1000, None),
            ("b", 0, 1000, ("a",), 1000, 1000, 1000, 0, 0),
            ("c", 1, 0, ("b",), 1000, 1000, 1000, 0, None),
        ],
        "critical": [("service", "a", 0, 1000)],
        "busy": {0: 1000, 1: 0},
        "duration": 1000,
    },
    "S08-zero-bridge": {
        "jobs": [
            ("a", 0, 0, (), 0, 0, 3000, 3000, None),
            ("c", 1, 0, ("z",), 3000, 3000, 5000, 2000, None),
            ("p", 1, 0, (), 0, 0, 1000, 1000, None),
            ("z", 0, 0, ("p",), 1000, 3000, 3000, 0, None),
        ],
        "critical": [
            ("service", "a", 0, 3000),
            ("service", "z", 3000, 3000),
            ("service", "c", 3000, 5000),
        ],
        "busy": {0: 3000, 1: 3000},
        "duration": 5000,
    },
    "S09-same-ready-fifo-zero": {
        "jobs": [
            ("a", 0, 0, (), 0, 0, 1000, 1000, None),
            ("b", 0, 1000, (), 1000, 1000, 1000, 0, 0),
            ("c", 0, 0, ("a",), 1000, 1000, 1001, 1, None),
        ],
        "critical": [("service", "a", 0, 1000), ("service", "c", 1000, 1001)],
        "busy": {0: 1001},
        "duration": 1001,
    },
    "S10-all-zero-at-zero": {
        "jobs": [
            ("a", 0, 0, (), 0, 0, 0, 0, None),
            ("b", 0, 0, ("a",), 0, 0, 0, 0, 0),
            ("c", 1, 0, ("b",), 0, 0, 0, 0, None),
        ],
        "critical": [],
        "busy": {0: 0, 1: 0},
        "duration": 0,
    },
    "S11-release-dependency-tie": {
        "jobs": [
            ("a", 1, 0, (), 0, 0, 1000, 1000, None),
            ("c", 0, 1000, ("a",), 1000, 1000, 2500, 0, 1),
        ],
        "critical": [("service", "a", 0, 1000), ("service", "c", 1000, 2500)],
        "busy": {0: 1500, 1: 1000},
        "duration": 2500,
    },
    "S12-idle-owner-history": {
        "jobs": [
            ("a", 0, 0, (), 0, 0, 500, 500, None),
            ("b", 1, 0, (), 0, 0, 2000, 2000, None),
            ("c", 0, 835, ("b",), 2000, 2000, 3334, 0, 1),
        ],
        "critical": [("service", "b", 0, 2000), ("service", "c", 2000, 3334)],
        "busy": {0: 1834, 1: 2000},
        "duration": 3334,
    },
    "S13-on-edge-zero": {
        "jobs": [("z", 0, 834, (), 834, 834, 834, 0, 0)],
        "critical": [("release_offset", "z", 0, 834)],
        "busy": {0: 0},
        "duration": 834,
    },
    "S14-on-edge-positive": {
        "jobs": [("c", 0, 834, (), 834, 834, 1667, 0, 1)],
        "critical": [("release_offset", "c", 0, 834), ("service", "c", 834, 1667)],
        "busy": {0: 833},
        "duration": 1667,
    },
    "S15-ps-without-clock": {
        "jobs": [("a", 0, 0, (), 0, 0, 835, 835, None)],
        "critical": [("service", "a", 0, 835)],
        "busy": {0: 835},
        "duration": 835,
    },
}


def raw_edge(start_ps, cycles):
    """Small independent rational-edge search over the finite witnesses (not scheduling)."""
    assert 0 <= start_ps <= 5000 and 0 <= cycles <= 4
    edges = [(k * 2500 + 2) // 3 for k in range(16)]
    first = next(i for i, edge in enumerate(edges) if edge >= start_ps)
    return edges[first + cycles]


# Independent expected dispatch order, not a trace recovered from an executor.
GRANT_ORDER = {
    "S01-late-release-positive": ("c",),
    "S02-dependency-before-release": ("a", "c"),
    "S03-dependency-after-release": ("a", "c"),
    "S04-busy-owner-positive": ("a", "c"),
    "S05-busy-owner-zero": ("a", "z"),
    "S06-off-edge-owned-zero": ("z",),
    "S07-same-time-release-dependency": ("a", "b", "c"),
    "S08-zero-bridge": ("a", "p", "z", "c"),
    "S09-same-ready-fifo-zero": ("a", "b", "c"),
    "S10-all-zero-at-zero": ("a", "b", "c"),
    "S11-release-dependency-tie": ("a", "c"),
    "S12-idle-owner-history": ("a", "b", "c"),
    "S13-on-edge-zero": ("z",),
    "S14-on-edge-positive": ("c",),
    "S15-ps-without-clock": ("a",),
    "S16-equal-owner-dependency-causes": ("a", "b", "c"),
    "S17-oldest-ready-before-id": ("a", "z", "b"),
}
CASES["S16-equal-owner-dependency-causes"] = {
    "jobs": [
        ("a", 0, 0, (), 0, 0, 1000, 1000, None),
        ("b", 1, 0, (), 0, 0, 1000, 1000, None),
        ("c", 0, 0, ("b",), 1000, 1000, 1001, 1, None),
    ],
    "critical": [("service", "a", 0, 1000), ("service", "c", 1000, 1001)],
    "busy": {0: 1001, 1: 1000},
    "duration": 1001,
}
CASES["S17-oldest-ready-before-id"] = {
    "jobs": [
        ("a", 0, 0, (), 0, 0, 100, 100, None),
        ("b", 0, 3, (), 3, 100, 100, 0, 0),
        ("z", 0, 1, (), 1, 100, 100, 0, 0),
    ],
    "critical": [("service", "a", 0, 100)],
    "busy": {0: 100},
    "duration": 100,
}
# Exact chosen predecessor for every job; ties prefer tight jobs over release,
# then smallest public job ID. Acceptance of this tie choice remains pending.
CHOSEN = {
    "S01-late-release-positive": {"c": None},
    "S02-dependency-before-release": {"a": None, "c": None},
    "S03-dependency-after-release": {"a": None, "c": "a"},
    "S04-busy-owner-positive": {"a": None, "c": "a"},
    "S05-busy-owner-zero": {"a": None, "z": "a"},
    "S06-off-edge-owned-zero": {"z": None},
    "S07-same-time-release-dependency": {"a": None, "b": "a", "c": "b"},
    "S08-zero-bridge": {"a": None, "p": None, "z": "a", "c": "z"},
    "S09-same-ready-fifo-zero": {"a": None, "b": "a", "c": "a"},
    "S10-all-zero-at-zero": {"a": None, "b": "a", "c": "b"},
    "S11-release-dependency-tie": {"a": None, "c": "a"},
    "S12-idle-owner-history": {"a": None, "b": None, "c": "b"},
    "S13-on-edge-zero": {"z": None},
    "S14-on-edge-positive": {"c": None},
    "S15-ps-without-clock": {"a": None},
    "S16-equal-owner-dependency-causes": {"a": None, "b": None, "c": "a"},
    "S17-oldest-ready-before-id": {"a": None, "z": "a", "b": "z"},
}
