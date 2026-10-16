"""Finite independent first-use proposal. No engine execution or human authority."""

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, spec_hash
from uarch_contract.mapped import MappedBundle, NativeTestProfile, NativeTestRegistry

MAX = 2**64 - 1
REVISION = "B-K2-construction-first-use/1"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seal(value, field):
    value[field] = content_hash(value, exclude=(field,))
    return value


def prepare(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    assert output.is_relative_to(Path("/tmp")) and not output.exists()
    old = root / "docs/reviews/U4-B-K2-first-use-v1/fixtures"
    old_identity = json.loads((old / "identity.json").read_bytes())
    for name, digest in old_identity["files"].items():
        assert hashlib.sha256((old / name).read_bytes()).hexdigest() == digest
    literals = load_module(
        root / "docs/reviews/U4-B-K2-semantic-reconciliation-v1/literals.py", "independent_literals"
    )
    projections = ast.parse(
        (root / "docs/reviews/U4-B-A-addendum-reconciliation-v1/projections.py").read_text()
    )
    events = next(
        ast.literal_eval(n.value)
        for n in projections.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "EVENTS" for t in n.targets)
    )
    kinds = dict(
        R="TASK_READY", L="TASK_RELEASE", D="DEPENDENCY_READY", G="OWNER_GRANT", C="COMPUTE_DONE"
    )
    profile = json.loads((old / "profile.json").read_bytes())
    registry = json.loads((old / "registry.json").read_bytes())
    expected = json.loads((old / "expectations.json").read_bytes())
    original_ids = sorted(expected)
    assert len(original_ids) == 113 and sum(x.startswith("K07-") for x in original_ids) == 100
    bundles = {
        case: json.loads((old / f"bundles/{case}.json").read_bytes()) for case in original_ids
    }
    # Explicit prospective correction only; historical bytes/answers remain untouched.
    original_k06 = copy.deepcopy(expected["K06-02"])
    assert original_k06["duration_ps"] == 1667
    expected["K06-02"]["duration_ps"] = 835
    for interval in expected["K06-02"]["intervals"]:
        if interval[0] == "b-clock":
            assert interval[-1] == 1667
            interval[-1] = 835
    expected["K06-02"]["raw_clock_edge_ps"] = 1667
    producer = {
        "name": "B-independent-K2-first-use-proposal",
        "version": "1",
        "implementation_hash": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }

    def add(case, freq, jobs, deps, clocks, answer, owners=None):
        bundle = copy.deepcopy(bundles["K01"])
        bundle["producer"] = producer
        bundle["scope"]["owner_ids"] = sorted(owners or {owner for _, owner, _ in jobs})
        hardware = bundle["hardware_spec"]
        if freq != 10**9:
            hardware["id"] = f"u4-b-k2-readiness-clock-{freq}"
            hardware["clock_domains"]["core"]["freq_hz"].update(
                value=float(freq),
                rationale="Finite K2 fixture clock stipulation, not a hardware claim.",
            )
        bundle["hardware_spec_hash"] = spec_hash(hardware)
        point = bundle["points"][0]
        point.update(point_id=case, identity={"kind": "fixture", "fixture_id": case})
        graph = point["task_graph"]
        graph.update(
            jobs=[
                dict(kind="fixed_delay", id=job, owner_id=owner, duration_ps=duration)
                for job, owner, duration in sorted(jobs)
            ],
            dependencies=[dict(before=a, after=b) for a, b in sorted(deps)],
            buffers=[],
            routes=[],
            coverage=[],
        )
        seal(graph, "graph_hash")
        seal(point, "payload_hash")
        entry = copy.deepcopy(profile["entries"][0])
        entry.update(
            case_id=case,
            hardware_spec=hardware,
            hardware_spec_hash=bundle["hardware_spec_hash"],
            freq_hz=dict(core=freq, noc=10**9, dram=10**9),
            graph_hash=graph["graph_hash"],
            point_hash=point["payload_hash"],
            clock_setup_hash=content_hash(clocks),
            case_selection_revision=REVISION,
            expected_outcome="success",
        )
        profile["entries"].append(entry)
        bundles[case] = bundle
        expected[case] = dict(clock_setup=clocks, **answer)
        if bundle["hardware_spec_hash"] != bundles["K01"]["hardware_spec_hash"] and not any(
            x["hardware_spec_hash"] == bundle["hardware_spec_hash"]
            for x in registry["test_only_specs"]
        ):
            registry["test_only_specs"].append(
                dict(
                    hardware_spec_hash=bundle["hardware_spec_hash"],
                    rationale="Independent finite first-use clock fixture; no hardware fidelity.",
                )
            )

    for case, witness in sorted(literals.CASES.items()):
        jobs = [(j[0], j[1], j[7]) for j in witness["jobs"]]
        deps = [(dependency, j[0]) for j in witness["jobs"] for dependency in j[3]]
        clocks = [
            dict(job_id=j[0], domain="core", start_ps=j[2], n_cycles=j[8])
            for j in witness["jobs"]
            if j[8] is not None
        ]
        answer = dict(
            outcome="success",
            duration_ps=witness["duration"],
            intervals=[(j[0], j[1], j[4], j[5], j[6]) for j in witness["jobs"]],
            busy_by_owner=witness["busy"],
            critical_positive=[c for c in witness["critical"] if c[2] < c[3]],
            chosen_predecessors=literals.CHOSEN[case],
            grant_order=literals.GRANT_ORDER[case],
            event_projection=[
                (t, phase, job, kinds[kind]) for t, phase, job, kind in events[case[:3]]
            ],
        )
        add(case, literals.FREQ_HZ, jobs, deps, clocks, answer)
    add(
        "ZMAX-raw-overflow-owned-zero",
        10**9,
        [("z", 0, 0)],
        [],
        [dict(job_id="z", domain="core", start_ps=MAX, n_cycles=0)],
        dict(
            outcome="success",
            duration_ps=MAX,
            intervals=[("z", 0, MAX, MAX, MAX)],
            raw_clock_outcome="TimeOverflow",
            raw_clock_edge_ps=None,
            busy_by_owner={0: 0},
            critical_positive=[("release_offset", "z", 0, MAX)],
            chosen_predecessors={"z": None},
        ),
    )
    add(
        "ZMAX-positive-overflow",
        10**12,
        [("z", 0, 0)],
        [],
        [dict(job_id="z", domain="core", start_ps=MAX, n_cycles=1)],
        dict(
            outcome="TimeOverflow",
            duration_ps=None,
            intervals=[],
            raw_clock_outcome="success",
            raw_clock_edge_ps=MAX,
        ),
    )
    add(
        "O01-sparse-u64-owners",
        10**9,
        [("a", 7, 1), ("b", MAX, 1)],
        [],
        [],
        dict(
            outcome="success",
            duration_ps=1,
            intervals=[("a", 7, 0, 0, 1), ("b", MAX, 0, 0, 1)],
            busy_by_owner={7: 1, MAX: 1},
            critical_positive=[("service", "a", 0, 1)],
            chosen_predecessors={"a": None, "b": None},
            grant_order=["a", "b"],
        ),
    )
    # Literal old-case causal joins under the now-installed tie law. No scheduling.
    old_causes = {
        "K01": {"a": None, "b": None, "c": "b"},
        "K02": {"a": None, "b": "a", "c": "b"},
        "K03-owner": {"a": None, "b": None, "c": "a"},
        "K04": {"a": None, "p": None, "z": "a", "c": "z"},
        "K05": {"a": None, "b": None, "c": "a"},
        "K05-chain": {"a": None, "b": "a", "c": "a", "d": "b"},
    }
    positive_paths = {
        "K01": ["b", "c"],
        "K02": ["a", "b", "c"],
        "K03-owner": ["a"],
        "K04": ["a", "c"],
        "K05": ["c"],
        "K05-chain": ["a", "d"],
    }
    for case, causes in old_causes.items():
        answer = expected[case]
        answer["chosen_predecessors"] = causes
        rows = {row[0]: row for row in answer["intervals"]}
        answer["critical_positive"] = [
            ("service", name, rows[name][3], rows[name][4]) for name in positive_paths[case]
        ]
        answer["historical_causal_path"] = answer.pop("causal_job_path", None)
    for case in original_ids:
        answer = expected[case]
        if answer["outcome"] != "success" or not answer["clock_setup"]:
            continue
        setup = answer["clock_setup"][0]
        start = setup["start_ps"]
        freq = next(e["freq_hz"]["core"] for e in profile["entries"] if e["case_id"] == case)
        k = 0 if start == 0 else ((start - 1) * freq) // 10**12 + 1
        answer["raw_clock_edge_ps"] = (k * 10**12 + freq - 1) // freq
        answer["raw_clock_outcome"] = "success"
        answer["chosen_predecessors"] = {"b-clock": "a-wait" if start else None}
        if start:
            answer["chosen_predecessors"]["a-wait"] = None
        answer["critical_positive"] = [
            ("service", row[0], row[3], row[4]) for row in answer["intervals"] if row[3] < row[4]
        ]
        answer["historical_causal_path"] = answer.pop("causal_job_path", None)
    for case, answer in expected.items():
        if answer["outcome"] != "success":
            continue
        owners = bundles[case]["scope"]["owner_ids"]
        answer["busy_by_owner"] = {
            owner: sum(row[4] - row[3] for row in answer["intervals"] if row[1] == owner)
            for owner in owners
        }
        answer["queue_rows"] = sorted(
            (f"owner:{row[1]}:{population}", row[0], population, begin, end, row[1], None)
            for row in answer["intervals"]
            for population, begin, end in [("waiting", row[2], row[3]), ("service", row[3], row[4])]
        )
    for entry in profile["entries"]:
        entry["case_selection_revision"] = REVISION
    profile["entries"].sort(key=lambda e: e["case_id"])
    profile["owner"] = "Lane B independent first-use proposal; human acceptance pending"
    seal(profile, "profile_hash")
    registry["test_only_specs"].sort(key=lambda e: e["hardware_spec_hash"])
    seal(registry, "registry_hash")
    NativeTestProfile.model_validate(profile)
    NativeTestRegistry.model_validate(registry)
    output.mkdir()
    artifacts = {"profile.json": profile, "registry.json": registry, "expectations.json": expected}
    cases = {}
    for case, bundle in sorted(bundles.items()):
        bundle["admission"].update(profile_hash=profile["profile_hash"], case_id=case)
        seal(bundle, "bundle_hash")
        MappedBundle.model_validate(bundle)
        artifacts[f"bundles/{case}.json"] = bundle
        point = bundle["points"][0]
        cases[case] = dict(
            bundle_hash=bundle["bundle_hash"],
            point_hash=point["payload_hash"],
            graph_hash=point["task_graph"]["graph_hash"],
            hardware_spec_hash=bundle["hardware_spec_hash"],
            clock_setup_hash=content_hash(expected[case]["clock_setup"]),
            seed=0,
            admission_expected="success",
            execution_expected=expected[case]["outcome"],
            public_execution="pending_final_human_binding",
        )
    files = {}
    for name, value in artifacts.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        raw = (canonical_json(value) + "\n").encode()
        path.write_bytes(raw)
        files[name] = hashlib.sha256(raw).hexdigest()
    manifest = dict(
        format="B-K2-first-use-candidate/1",
        authority="proposal_only",
        profile_hash=profile["profile_hash"],
        registry_hash=registry["registry_hash"],
        original_ids=original_ids,
        original_K06_02=original_k06,
        added_ids=sorted(set(cases) - set(original_ids)),
        cases=cases,
        files=files,
        private_wheel_inventory={
            "path": "docs/reviews/U4-B-K2-first-use-v1/fixtures/wheel-schedules.json",
            "sha256": old_identity["files"]["wheel-schedules.json"],
            "count": 100,
            "public_mapping": (
                "private-only Wheel/Arena insertion/reuse/exhaustion exception; "
                "no public event-injection IR"
            ),
        },
        expected_engine=None,
        build_receipts=None,
        human_host_record=None,
    )
    (output / "candidate.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
