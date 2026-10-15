"""Finite literal fixture author; no timing engine, producer, or execution authority.

Inputs are installed carriers from the pinned private export. Output is proposal data.
"""

import copy
import hashlib
import json
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, spec_hash
from uarch_contract.mapped import MappedBundle, NativeTestProfile, NativeTestRegistry

REVISION = "B-K2-first-use/1"
MAX = 2**64 - 1


def seal(value, key):
    value[key] = content_hash(value, exclude=(key,))
    return value


def literal_cases():
    # Each interval is (job, owner, ready, start, end), independently worked by hand.
    rows = [
        (
            "K01",
            [("a", 0, 3000), ("b", 1, 5000), ("c", 0, 2000)],
            [("a", "c"), ("b", "c")],
            [("a", 0, 0, 0, 3000), ("b", 1, 0, 0, 5000), ("c", 0, 5000, 5000, 7000)],
            ["b", "c"],
        ),
        (
            "K02",
            [("a", 0, 3000), ("b", 0, 5000), ("c", 0, 2000)],
            [("a", "c"), ("b", "c")],
            [("a", 0, 0, 0, 3000), ("b", 0, 0, 3000, 8000), ("c", 0, 8000, 8000, 10000)],
            ["a", "b", "c"],
        ),
        (
            "K03-owner",
            [("a", 1, 1000), ("b", 0, 1000), ("c", 0, 0)],
            [("a", "c"), ("b", "c")],
            [("a", 1, 0, 0, 1000), ("b", 0, 0, 0, 1000), ("c", 0, 1000, 1000, 1000)],
            None,
        ),
        (
            "K04",
            [("a", 0, 3000), ("c", 1, 2000), ("p", 1, 1000), ("z", 0, 0)],
            [("p", "z"), ("z", "c")],
            [
                ("a", 0, 0, 0, 3000),
                ("c", 1, 3000, 3000, 5000),
                ("p", 1, 0, 0, 1000),
                ("z", 0, 1000, 3000, 3000),
            ],
            ["a", "z", "c"],
        ),
        (
            "K05",
            [("a", 0, 0), ("b", 1, 0), ("c", 0, 3000)],
            [("a", "c"), ("b", "c")],
            [("a", 0, 0, 0, 0), ("b", 1, 0, 0, 0), ("c", 0, 0, 0, 3000)],
            None,
        ),
        (
            "K05-chain",
            [("a", 0, 1000), ("b", 1, 0), ("c", 0, 0), ("d", 1, 2000)],
            [("a", "b"), ("b", "c"), ("c", "d")],
            [
                ("a", 0, 0, 0, 1000),
                ("b", 1, 1000, 1000, 1000),
                ("c", 0, 1000, 1000, 1000),
                ("d", 1, 1000, 1000, 3000),
            ],
            ["a", "b", "c", "d"],
        ),
    ]
    cases = []
    for name, jobs, deps, intervals, path in rows:
        cases.append(
            dict(
                case_id=name,
                freq_hz=10**9,
                jobs=jobs,
                dependencies=deps,
                clock_setup=[],
                expected=dict(
                    outcome="success",
                    intervals=intervals,
                    duration_ps=max(x[4] for x in intervals),
                    causal_job_path=path,
                ),
            )
        )
    clocks = [
        (f"K06-{i:02}", 1200000000, t, n, end)
        for i, (t, n, end) in enumerate(
            [(0, 3, 2500), (834, 0, 834), (835, 0, 1667), (835, 1, 2500), (0, 10**9, 833333333334)]
        )
    ]
    # Finite closed-form arithmetic, no event execution or production time helper.
    clocks += [
        (f"K07-{f}-{k:02}", f, (k * 10**12 + f - 1) // f, 0, (k * 10**12 + f - 1) // f)
        for f in (800000000, 900000000, 1000000000, 1200000000)
        for k in range(25)
    ]
    clocks.append(("K08-clock-overflow", 10**9, MAX, 1, None))
    for name, freq, start, cycles, end in clocks:
        jobs = [("b-clock", 0, 0)]
        deps, intervals = [], []
        if start:
            jobs.insert(0, ("a-wait", 1, start))
            deps.append(("a-wait", "b-clock"))
            intervals.append(("a-wait", 1, 0, 0, start))
        if end is not None:
            intervals.append(("b-clock", 0, start, start, end))
        cases.append(
            dict(
                case_id=name,
                freq_hz=freq,
                jobs=jobs,
                dependencies=deps,
                clock_setup=[
                    dict(job_id="b-clock", domain="core", start_ps=start, n_cycles=cycles)
                ],
                expected=dict(
                    outcome="success" if end is not None else "TimeOverflow",
                    duration_ps=end,
                    intervals=intervals,
                    causal_job_path=None,
                ),
            )
        )
    cases.append(
        dict(
            case_id="K08-add-overflow",
            freq_hz=10**9,
            jobs=[("a", 0, MAX), ("b", 0, 1)],
            dependencies=[("a", "b")],
            clock_setup=[],
            expected=dict(
                outcome="TimeOverflow", duration_ps=None, intervals=[], causal_job_path=None
            ),
        )
    )
    return sorted(cases, key=lambda c: c["case_id"])


def wheel_vectors():
    # Private Wheel API proposals; NOT mapped jobs or a new public protocol.
    rows = []
    for seed in range(100):
        width = 833
        times = [
            0,
            width * 4095,
            width * 4096,
            width * (4096**2 - 1),
            width * 4096**2,
            1000 + seed,
            1000 + seed,
            1000 + seed,
        ]
        order = [(i + seed) % len(times) for i in range(len(times))]
        events = [
            dict(
                t_ps=times[i],
                phase=(seed + i) % 4,
                target=(seed + 2 * i) % 3,
                seq=seq,
                payload=100 * seed + i,
            )
            for seq, i in enumerate(order)
        ]
        expected = sorted(events, key=lambda x: (x["t_ps"], x["phase"], x["target"], x["seq"]))
        rows.append(
            dict(
                case_id=f"K03-schedule-{seed:03}",
                seed=seed,
                max_freq_hz=1200000000,
                schedule=events,
                expected_pop=expected,
                reuse=dict(
                    t_ps=width * 4096**2 + 1, phase=0, target=0, seq=8, payload=10000 + seed
                ),
            )
        )
    return rows


def author(root, output):
    source = root / "contract/fixtures/mapped"
    template = json.loads((source / "kernel.json").read_text())
    author_hash = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    cases = literal_cases()
    bundles, entries, expected, specs = {}, [], {}, {}
    for c in cases:
        name = c["case_id"]
        b = copy.deepcopy(template)
        b["producer"] = dict(
            name="B-literal-K2-proposal", version="1", implementation_hash=author_hash
        )
        b["scope"] = dict(kind="kernel_fixture", owner_ids=[0, 1])
        spec = b["hardware_spec"]
        if c["freq_hz"] != 10**9:
            spec["id"] = f"u4-b-k2-clock-{c['freq_hz']}"
            spec["clock_domains"]["core"]["freq_hz"].update(
                value=float(c["freq_hz"]),
                rationale=(
                    "Verification-only proposed clock for exact edge checks; not a chip claim."
                ),
            )
        b["hardware_spec_hash"] = spec_hash(spec)
        if c["freq_hz"] != 10**9:
            specs[b["hardware_spec_hash"]] = "Finite K06/K07 core-clock stipulation; K2 test only."
        p = b["points"][0]
        p.update(point_id=name, identity=dict(kind="fixture", fixture_id=name))
        g = p["task_graph"]
        g.update(
            jobs=[
                dict(kind="fixed_delay", id=i, owner_id=o, duration_ps=d) for i, o, d in c["jobs"]
            ],
            dependencies=[dict(before=a, after=z) for a, z in c["dependencies"]],
            buffers=[],
            routes=[],
            coverage=[],
        )
        seal(g, "graph_hash")
        seal(p, "payload_hash")
        entries.append(
            dict(
                case_id=name,
                checkpoint="K2",
                scope="kernel_fixture",
                initial_state="fixture_cold",
                priming_iterations=0,
                hardware_spec_hash=b["hardware_spec_hash"],
                hardware_spec=spec,
                frequency_ratio=1.0,
                freq_hz=dict(core=c["freq_hz"], noc=10**9, dram=10**9),
                graph_hash=g["graph_hash"],
                point_hash=p["payload_hash"],
                allowed_job_kinds=["fixed_delay"],
                clock_setup_hash=content_hash(c["clock_setup"]),
                expected_outcome="success",
                seed=0,
                case_selection_revision=REVISION,
            )
        )
        bundles[name] = b
        expected[name] = dict(clock_setup=c["clock_setup"], **c["expected"])
    profile = seal(
        dict(
            format="uarch-native-test-profile/1",
            semantics_revision="U0011-stage2/1",
            owner="Lane B agent proposal; no human acceptance",
            entries=entries,
        ),
        "profile_hash",
    )
    registry = seal(
        dict(
            format="uarch-native-test-registry/1",
            semantics_revision="U0011-stage2/1",
            test_only_specs=[
                dict(hardware_spec_hash=h, rationale=r) for h, r in sorted(specs.items())
            ],
        ),
        "registry_hash",
    )
    NativeTestProfile.model_validate(profile)
    NativeTestRegistry.model_validate(registry)
    output.mkdir(parents=True, exist_ok=False)
    identities = dict(
        revision=REVISION,
        source_commit="4f3be8fab5fea1a030b72d5047677016f261eb5e",
        authority="proposal_only",
        registry_hash=registry["registry_hash"],
        profile_hash=profile["profile_hash"],
        expected_engine=None,
        cases={},
        files={},
    )
    artifacts = {
        "profile.json": profile,
        "registry.json": registry,
        "expectations.json": expected,
        "wheel-schedules.json": wheel_vectors(),
    }
    for name, b in bundles.items():
        b["admission"].update(profile_hash=profile["profile_hash"], case_id=name)
        seal(b, "bundle_hash")
        MappedBundle.model_validate(b)
        artifacts[f"bundles/{name}.json"] = b
        p = b["points"][0]
        identities["cases"][name] = dict(
            bundle_hash=b["bundle_hash"],
            point_hash=p["payload_hash"],
            graph_hash=p["task_graph"]["graph_hash"],
            hardware_spec_hash=b["hardware_spec_hash"],
            clock_setup_hash=content_hash(expected[name]["clock_setup"]),
            seed=0,
            expected_outcome=expected[name]["outcome"],
        )
    for name, data in artifacts.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        raw = (canonical_json(data) + "\n").encode()
        path.write_bytes(raw)
        identities["files"][name] = hashlib.sha256(raw).hexdigest()
    (output / "identity.json").write_text(json.dumps(identities, indent=2) + "\n")


if __name__ == "__main__":
    import sys

    author(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
