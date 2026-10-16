"""Independent placement literals; all authority fixtures here are synthetic unit anchors."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import Compute, Dma, MappedBundle, NativeEngineIdentity
from uarch_contract.prepared import PreparedOp, Producer

from rkuarch.mapping.component import map_component
from rkuarch.workload.component import (
    component_point,
    prepare_component_bundle,
    prepare_component_job,
)
from rkuarch.workload.mapped import (
    export_component_bundle,
    export_component_job,
    load_component_bundle,
    load_component_job,
    loads_component_bundle,
    loads_component_job,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "contract/fixtures/mapped"


@pytest.fixture
def baseline() -> MappedBundle:
    return MappedBundle.model_validate_json((FIXTURES / "component.json").read_bytes())


def op(
    b: MappedBundle,
    m: int = 3,
    k: int = 5,
    n: int = 7,
    name: str = "g0",
    dependencies: tuple[str, ...] = (),
) -> PreparedOp:
    raw = b.scope.model_dump(mode="json")["ops"][0]
    raw.update(id=name, depends_on=list(dependencies))
    raw["spec"]["dimensions"] = {"M": m, "K": k, "N": n}
    return PreparedOp.model_validate(raw)


def bundle(b: MappedBundle, ops: tuple[PreparedOp, ...], state: str = "cold") -> MappedBundle:
    graph = map_component(ops, b.hardware_spec, initial_state=state)
    point = component_point(ops, graph, initial_state=state)
    return prepare_component_bundle(
        ops,
        b.hardware_spec,
        point,
        producer=Producer(
            name="synthetic-unit-mapper",
            version="1",
            implementation_hash=content_hash("synthetic unit source identity; not authority"),
        ),
        assumptions=b.assumptions,
        rank=b.rank,
        admission=b.admission,
    )


def registry() -> dict[str, Any]:
    return json.loads((FIXTURES / "registry.json").read_bytes())


def anchors() -> dict[str, Any]:
    return dict(
        invocation="production",
        registry=registry(),
        profile=None,
        trusted_registry_hash=registry()["registry_hash"],
        trusted_profile_hash=None,
    )


def seal(raw: dict[str, Any]) -> None:
    for p in raw["points"]:
        p["task_graph"]["graph_hash"] = content_hash(p["task_graph"], exclude=("graph_hash",))
        p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))


def test_small_literal_and_no_timing(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    g = b.points[0].task_graph
    sr = [
        (x.operand, x.offset_bytes, x.size_bytes, x.slot_index, x.bank)
        for x in g.buffers
        if x.space == "sram"
    ]
    assert sr == [
        ("X", 0, 30, 0, 0),
        ("W", 256, 70, 0, 0),
        ("Y", 512, 42, 0, 0),
        (None, 768, 768, 1, 0),
    ]
    assert [(x.offset_bytes, x.size_bytes) for x in g.buffers if x.space == "hbm"] == [
        (0, 30),
        (256, 70),
        (512, 42),
    ]
    assert [(x.offset_bytes, x.size_bytes) for x in g.buffers if x.space == "accumulator"] == [
        (0, 84)
    ]
    compute = next(x for x in g.jobs if isinstance(x, Compute))
    assert compute.tile_extents.model_dump() == {"M": 3, "K": 5, "N": 7}
    assert compute.physical_extents.model_dump() == {"M": 3, "K": 256, "N": 256}
    assert len(g.coverage) == 1
    dma = [x for x in g.jobs if isinstance(x, Dma)]
    assert [
        (x.direction, [(f.channel_id, f.payload_bytes, f.transaction_bytes) for f in x.fragments])
        for x in dma
    ] == [("read", [(0, 30, 256)]), ("read", [(1, 70, 256)]), ("write", [(2, 42, 256)])]
    edges = {(x.before, x.after) for x in g.dependencies}
    assert edges == {(dma[0].id, compute.id), (dma[1].id, compute.id), (compute.id, dma[2].id)}
    assert "duration_ps" not in canonical_json(b)
    assert b == loads_component_bundle(canonical_json(b), **anchors())


@pytest.mark.parametrize(
    "m,rows", [(1, [1]), (255, [255]), (256, [256]), (257, [256, 1]), (1024, [256] * 4)]
)
def test_rows_and_exact_traffic(baseline: MappedBundle, m: int, rows: list[int]) -> None:
    b = bundle(baseline, (op(baseline, m, 256, 256),))
    g = b.points[0].task_graph
    comp = [x for x in g.jobs if isinstance(x, Compute)]
    assert [x.tile_extents.M for x in comp] == rows
    assert [x.core_id for x in comp] == list(range(len(rows)))
    assert [x.tile_origin.M for x in comp] == [256 * i for i in range(len(rows))]
    dma = [x for x in g.jobs if isinstance(x, Dma)]
    assert sum(x.source.size_bytes for x in dma if x.direction == "read") == (
        512 * m + len(rows) * 131072
    )
    assert sum(x.source.size_bytes for x in dma if x.direction == "write") == 512 * m
    assert (
        sum(2 * x.tile_extents.M * x.tile_extents.K * x.tile_extents.N for x in comp) == 131072 * m
    )


def test_split_payload_and_routes(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline, 257, 5, 7),))
    g = b.points[0].task_graph
    dma = [x for x in g.jobs if isinstance(x, Dma)]
    assert [f.payload_bytes for f in dma[0].fragments] == [256] * 10
    assert [f.channel_id for f in dma[0].fragments] == [0, 1, 2, 3, 4, 5, 6, 7, 0, 1]
    # Tail row is a separate core's exact ten-byte X, seventy-byte W, fourteen-byte Y.
    assert [x.source.size_bytes for x in dma[3:]] == [10, 70, 14]
    assert all(
        r.core_ids[0] == r.source_core_id and r.core_ids[-1] == r.destination_core_id
        for r in g.routes
    )
    assert any(r.core_ids == (0,) for r in g.routes)
    assert any(r.core_ids == (0, 1, 3) for r in g.routes)


def test_determinism_order_and_dependencies(baseline: MappedBundle) -> None:
    a, z = op(baseline, name="a", dependencies=("z",)), op(baseline, name="z")
    g = map_component((a, z), baseline.hardware_spec)
    assert canonical_json(g) == canonical_json(map_component((z, a), baseline.hardware_spec))
    b = bundle(baseline, (a, z))
    assert b == loads_component_bundle(canonical_json(b), **anchors())
    assert len([x for x in g.jobs if x.kind == "barrier"]) == 1


def test_sixteen_max_shape_ops(baseline: MappedBundle) -> None:
    b = bundle(baseline, tuple(op(baseline, 1024, 256, 256, f"g{i:02}") for i in range(16)))
    assert len(b.points[0].task_graph.coverage) == 64
    assert len([x for x in b.points[0].task_graph.buffers if x.space == "accumulator"]) == 4


@pytest.mark.parametrize("m,k,n", [(1025, 5, 7), (3, 257, 7), (3, 5, 257)])
def test_shape_refusal(baseline: MappedBundle, m: int, k: int, n: int) -> None:
    with pytest.raises(ValueError, match="UnsupportedShape"):
        map_component((op(baseline, m, k, n),), baseline.hardware_spec)


@pytest.mark.parametrize("count", [0, 17])
def test_scope_count_refusal(baseline: MappedBundle, count: int) -> None:
    with pytest.raises(ValueError, match="UnsupportedScope"):
        map_component(
            tuple(op(baseline, name=f"g{i}") for i in range(count)), baseline.hardware_spec
        )


@pytest.mark.parametrize("state", ["steady", "fixture_cold"])
def test_state_refusal(baseline: MappedBundle, state: str) -> None:
    with pytest.raises(ValueError, match="UnsupportedInitialState"):
        map_component((op(baseline),), baseline.hardware_spec, initial_state=state)


def test_cycle_and_duplicate_refusal(baseline: MappedBundle) -> None:
    with pytest.raises(ValueError, match="InvalidDependency"):
        map_component(
            (
                op(baseline, name="a", dependencies=("b",)),
                op(baseline, name="b", dependencies=("a",)),
            ),
            baseline.hardware_spec,
        )
    with pytest.raises(ValueError, match="InvalidCoverage"):
        map_component((op(baseline), op(baseline)), baseline.hardware_spec)


def test_resident_explicit_and_no_dma(baseline: MappedBundle) -> None:
    g = map_component((op(baseline),), baseline.hardware_spec, initial_state="fixture_resident")
    assert len(g.jobs) == 1 and g.jobs[0].kind == "compute"
    assert not g.routes and not any(x.space == "hbm" for x in g.buffers)
    assert [x.operand for x in g.buffers if x.initial_residency == "preloaded"] == ["X", "W"]
    # Merely relabelling production admission is not permission for resident use.
    b = bundle(baseline, (op(baseline),), "fixture_resident")
    with pytest.raises(ValueError, match="UnsupportedInitialState"):
        loads_component_bundle(canonical_json(b), **anchors())


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("bank", "InvalidBank"),
        ("alignment", "InvalidResource"),
        ("alias", "LiveBufferAlias"),
        ("capacity", "SramCapacityExceeded"),
        ("coverage", "InvalidCoverage"),
        ("cycle", "InvalidDependency"),
        ("channel", "InvalidTransfer"),
        ("rank", "UnsupportedRankScope"),
        ("precision", "UnsupportedPrecision"),
        ("hardware", "UnsupportedHardware"),
    ],
)
def test_rehashed_semantic_guards(baseline: MappedBundle, mutation: str, reason: str) -> None:
    good = bundle(baseline, (op(baseline),))
    assert loads_component_bundle(canonical_json(good), **anchors()) == good
    raw = good.model_dump(mode="json")
    g = raw["points"][0]["task_graph"]
    sr = [x for x in g["buffers"] if x["space"] == "sram"]
    if mutation == "bank":
        sr[0]["bank"] = 1
    if mutation == "alignment":
        sr[0]["offset_bytes"] = 1
    if mutation == "alias":
        sr[1]["offset_bytes"] = 0
    if mutation == "capacity":
        sr[-1]["size_bytes"] = 16777217
    if mutation == "coverage":
        g["coverage"] = []
    if mutation == "cycle":
        edge = g["dependencies"][0]
        g["dependencies"].append(dict(before=edge["after"], after=edge["before"]))
        g["dependencies"].sort(key=lambda x: (x["before"], x["after"]))
    if mutation == "channel":
        next(x for x in g["jobs"] if x["kind"] == "dma")["fragments"][0]["channel_id"] = 7
    if mutation == "rank":
        raw["rank"].update(tp=2, equivalent_ranks=[0, 1])
    if mutation == "precision":
        raw["scope"]["ops"][0]["spec"]["operands"]["X"]["dtype"] = "fp16"
    if mutation == "hardware":
        from uarch_contract.hardware import HardwareSpec
        from uarch_contract.hashing import spec_hash

        raw["hardware_spec"]["id"] = "not-npu-l4"
        raw["hardware_spec_hash"] = spec_hash(HardwareSpec.model_validate(raw["hardware_spec"]))
    seal(raw)
    with pytest.raises(ValueError, match=reason):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_stale_and_changed_valid_placement(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    raw = b.model_dump(mode="json")
    sr = next(x for x in raw["points"][0]["task_graph"]["buffers"] if x["space"] == "sram")
    sr.update(offset_bytes=524288, bank=1)
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        loads_component_bundle(canonical_json(raw), **anchors())
    seal(raw)
    changed = loads_component_bundle(canonical_json(raw), **anchors())
    assert changed.bundle_hash != b.bundle_hash
    assert changed.mapping_policy == b.mapping_policy


def test_saved_bundle_and_job(baseline: MappedBundle, tmp_path: Path) -> None:
    b = bundle(baseline, (op(baseline),))
    engine = NativeEngineIdentity.model_validate(
        json.loads((FIXTURES / "component-job.json").read_bytes())["engine"]
    )
    job_args = dict(
        invocation="production",
        trusted_registry_hash=registry()["registry_hash"],
        trusted_profile_hash=None,
        expected_engine=engine,
    )
    j = prepare_component_job(
        b, point_hash=b.points[0].payload_hash, registry=registry(), profile=None, **job_args
    )
    p, q = tmp_path / "bundle.json", tmp_path / "job.json"
    export_component_bundle(b, p, **anchors())
    export_component_job(j, q, **job_args)
    assert load_component_bundle(p, **anchors()) == b
    assert load_component_job(q, **job_args) == j
    assert loads_component_job(q.read_bytes(), **job_args) == j
    with pytest.raises(FileExistsError):
        export_component_bundle(b, p, **anchors())
    with pytest.raises(FileExistsError):
        export_component_job(j, q, **job_args)
    bad = copy.deepcopy(j.model_dump(mode="json"))
    bad["bundle_hash"] = content_hash("foreign")
    bad["job_hash"] = content_hash(bad, exclude=("job_hash",))
    with pytest.raises(ValueError, match="ContentHashMismatch"):
        loads_component_job(canonical_json(bad), **job_args)


def test_incomplete_input_transfer_refused(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    raw = b.model_dump(mode="json")
    dma = next(j for j in raw["points"][0]["task_graph"]["jobs"] if j["kind"] == "dma")
    dma["source"]["size_bytes"] = dma["destination"]["size_bytes"] = 2
    dma["fragments"][0]["payload_bytes"] = 2
    seal(raw)
    with pytest.raises(ValueError, match="InvalidTransfer.*complete operand"):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_missing_output_write_refused(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    raw = b.model_dump(mode="json")
    g = raw["points"][0]["task_graph"]
    write = next(j for j in g["jobs"] if j["kind"] == "dma" and j["direction"] == "write")
    g["jobs"].remove(write)
    g["buffers"] = [x for x in g["buffers"] if x["id"] != write["destination"]["buffer_id"]]
    next(x for x in g["buffers"] if x["id"] == write["source"]["buffer_id"])[
        "final_consumer_ids"
    ] = []
    g["dependencies"] = [e for e in g["dependencies"] if e["after"] != write["id"]]
    seal(raw)
    with pytest.raises(ValueError, match="InvalidTransfer.*complete output"):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_barrier_owner_join_refused(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline, name="a"), op(baseline, name="b", dependencies=("a",))))
    raw = b.model_dump(mode="json")
    next(j for j in raw["points"][0]["task_graph"]["jobs"] if j["kind"] == "barrier")[
        "owner_id"
    ] = 0
    seal(raw)
    with pytest.raises(ValueError, match="InvalidResource.*barrier owner"):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_distinct_accumulator_capacity_is_explicit(baseline: MappedBundle) -> None:
    # Both fit alone; installed lifetime rules cannot reuse different footprints.
    for n in (255, 256):
        assert bundle(baseline, (op(baseline, 256, 256, n),))
    with pytest.raises(ValueError, match="CapacityExceeded.*accumulator.*available 262144"):
        map_component(
            (op(baseline, 256, 256, 255, "a"), op(baseline, 256, 256, 256, "b", ("a",))),
            baseline.hardware_spec,
        )


def test_resident_profile_and_foreign_rehash(baseline: MappedBundle, tmp_path: Path) -> None:
    from uarch_contract.mapped import Admission

    ops = (op(baseline),)
    point = component_point(
        ops,
        map_component(ops, baseline.hardware_spec, initial_state="fixture_resident"),
        initial_state="fixture_resident",
    )
    profile = json.loads((FIXTURES / "resident-profile.json").read_bytes())
    entry = profile["entries"][0]
    entry.update(
        graph_hash=point.task_graph.graph_hash,
        point_hash=point.payload_hash,
        case_id="SYNTHETIC-UNIT-ONLY",
        allowed_job_kinds=["compute"],
    )
    profile["owner"] = "synthetic unit anchor; no human approval"
    profile["profile_hash"] = content_hash(profile, exclude=("profile_hash",))
    admission = Admission(
        checkpoint="B",
        invocation="test",
        profile_hash=profile["profile_hash"],
        case_id=entry["case_id"],
        eligibility="verification_only",
    )
    b = prepare_component_bundle(
        ops,
        baseline.hardware_spec,
        point,
        producer=baseline.producer,
        assumptions=baseline.assumptions,
        rank=baseline.rank,
        admission=admission,
    )
    auth = dict(
        anchors(), invocation="test", profile=profile, trusted_profile_hash=profile["profile_hash"]
    )
    export_component_bundle(b, tmp_path / "resident.json", **auth)
    assert load_component_bundle(tmp_path / "resident.json", **auth) == b
    foreign = copy.deepcopy(profile)
    foreign["owner"] = "caller rehash is not independent authority"
    foreign["profile_hash"] = content_hash(foreign, exclude=("profile_hash",))
    raw = b.model_dump(mode="json")
    raw["admission"]["profile_hash"] = foreign["profile_hash"]
    seal(raw)
    # Consistency control succeeds under a separately supplied SYNTHETIC changed anchor.
    assert loads_component_bundle(
        canonical_json(raw),
        **dict(auth, profile=foreign, trusted_profile_hash=foreign["profile_hash"]),
    )
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        loads_component_bundle(canonical_json(raw), **dict(auth, profile=foreign))


@pytest.mark.parametrize("text", ['{"x":1,"x":2}', '{"x":NaN}', "{} {}", "[]", "null"])
def test_component_strict_json(text: str) -> None:
    with pytest.raises(ValueError):
        loads_component_bundle(text, **anchors())


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("operator", "UnsupportedOperator"),
        ("precision", "UnsupportedPrecision"),
        ("layout", "UnsupportedCapability"),
        ("padding", "UnsupportedShape"),
        ("missing_dependency", "InvalidDependency"),
        ("operand_access", "InvalidCoverage"),
    ],
)
def test_mapper_scope_refusals(baseline: MappedBundle, mutation: str, reason: str) -> None:
    raw = op(baseline).model_dump(mode="json")
    if mutation == "operator":
        raw["spec"]["operator"] = "k_projection"
    if mutation == "precision":
        raw["spec"]["operands"]["Y"]["dtype"] = "fp8"
    if mutation == "layout":
        raw["spec"]["operands"]["X"].update(layout="paged", block_size_tokens=16)
    if mutation == "padding":
        raw["padding"] = [dict(dimension="M", logical=2, physical=3)]
    if mutation == "missing_dependency":
        raw["depends_on"] = ["absent"]
    if mutation == "operand_access":
        del raw["operand_access"]["X"]
    bad = PreparedOp.model_validate(raw)
    with pytest.raises(ValueError, match=reason):
        map_component((bad,), baseline.hardware_spec)


def test_mutable_model_export_refuses_before_creation(
    baseline: MappedBundle, tmp_path: Path
) -> None:
    b = bundle(baseline, (op(baseline),))
    next(j for j in b.points[0].task_graph.jobs if isinstance(j, Compute)).operand_buffers["X"] = (
        "lost"
    )
    destination = tmp_path / "absent.json"
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        export_component_bundle(b, destination, **anchors())
    assert not destination.exists()


def test_duplicate_and_missing_tiles(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    raw = b.model_dump(mode="json")
    g = raw["points"][0]["task_graph"]
    c = next(j for j in g["jobs"] if j["kind"] == "compute")
    # A matching duplicate coverage entry is still overlapping semantic work.
    second = dict(c, id=c["id"] + ".duplicate")
    g["jobs"].append(second)
    g["jobs"].sort(key=lambda x: x["id"])
    g["coverage"].append(dict(g["coverage"][0], job_id=second["id"]))
    g["coverage"].sort(key=lambda x: x["job_id"])
    for buf in g["buffers"]:
        if c["id"] in buf["final_consumer_ids"]:
            buf["final_consumer_ids"].append(second["id"])
    seal(raw)
    with pytest.raises(ValueError, match="InvalidCoverage"):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_producer_disabled_relocation_three_processes(
    baseline: MappedBundle, tmp_path: Path
) -> None:
    import subprocess
    import sys

    b = bundle(baseline, (op(baseline),))
    engine = NativeEngineIdentity.model_validate(
        json.loads((FIXTURES / "component-job.json").read_bytes())["engine"]
    )
    job_auth = dict(
        invocation="production",
        trusted_registry_hash=registry()["registry_hash"],
        trusted_profile_hash=None,
        expected_engine=engine,
    )
    j = prepare_component_job(
        b, point_hash=b.points[0].payload_hash, registry=registry(), profile=None, **job_auth
    )
    relocated = tmp_path / "elsewhere"
    relocated.mkdir()
    export_component_bundle(b, tmp_path / "bundle.json", **anchors())
    export_component_job(j, tmp_path / "job.json", **job_auth)
    (tmp_path / "bundle.json").rename(relocated / "bundle.json")
    (tmp_path / "job.json").rename(relocated / "job.json")
    # Separate test harness anchor file; never synthesized by the replay loader.
    (relocated / "unit-anchors.json").write_text(
        canonical_json(dict(anchors(), expected_engine=engine.model_dump(mode="json")))
    )
    script = r"""
import importlib.abc, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path[:0] = [str(root/'src'), str(root/'contract')]
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.startswith(('rkuarch.mapping', 'rkuarch.workload.component',
                                'rkuarch.workload.prepare', 'rkuarch.workload.producer',
                                'rkuarch.workload.rotary', 'rkuarch.engines', 'subprocess')):
            raise AssertionError('producer/executor imported: '+fullname)
sys.meta_path.insert(0, Guard())
from uarch_contract.hashing import canonical_json
from uarch_contract.mapped import NativeEngineIdentity
from rkuarch.workload.mapped import load_component_bundle, load_component_job
import rkuarch.workload.mapped as module
assert pathlib.Path(module.__file__).resolve() == root/'src/rkuarch/workload/mapped.py'
a = json.loads(pathlib.Path('unit-anchors.json').read_bytes())
engine = NativeEngineIdentity.model_validate(a.pop('expected_engine'))
b = load_component_bundle(pathlib.Path('bundle.json'), **a)
j = load_component_job(pathlib.Path('job.json'), invocation=a['invocation'],
    trusted_registry_hash=a['trusted_registry_hash'], trusted_profile_hash=None,
    expected_engine=engine)
assert canonical_json(b).encode() == pathlib.Path('bundle.json').read_bytes()
assert canonical_json(j).encode() == pathlib.Path('job.json').read_bytes()
print(b.bundle_hash, j.job_hash)
"""
    outputs = [
        subprocess.check_output(
            [sys.executable, "-I", "-B", "-c", script, str(ROOT)], cwd=relocated
        )
        for _ in range(3)
    ]
    assert outputs == [outputs[0]] * 3


def test_import_unaligned_stripe_crossing(baseline: MappedBundle) -> None:
    raw = bundle(baseline, (op(baseline, 1, 1, 1),)).model_dump(mode="json")
    g = raw["points"][0]["task_graph"]
    dma = next(j for j in g["jobs"] if j["kind"] == "dma")
    src = next(b for b in g["buffers"] if b["id"] == dma["source"]["buffer_id"])
    src.update(offset_bytes=8192, size_bytes=257)
    dma["source"]["offset_bytes"] = 255
    first = dict(dma["fragments"][0], source_offset_bytes=255, payload_bytes=1, channel_id=0)
    second = dict(
        first,
        request_id=first["request_id"] + "-tail",
        source_offset_bytes=256,
        destination_offset_bytes=1,
        channel_id=1,
    )
    dma["fragments"] = [first, second]
    seal(raw)
    imported = loads_component_bundle(canonical_json(raw), **anchors())
    found = next(j for j in imported.points[0].task_graph.jobs if isinstance(j, Dma))
    assert [(f.channel_id, f.payload_bytes, f.transaction_bytes) for f in found.fragments] == [
        (0, 1, 256),
        (1, 1, 256),
    ]
    dma["fragments"] = [dict(first, payload_bytes=2)]
    seal(raw)
    with pytest.raises(ValueError, match="InvalidTransfer"):
        loads_component_bundle(canonical_json(raw), **anchors())


@pytest.mark.parametrize(
    "change,reason",
    [
        ("second_slot", "CapacityExceeded"),
        ("accumulator", "CapacityExceeded"),
        ("dma_engine", "InvalidResource"),
        ("route", "InvalidRoute"),
    ],
)
def test_resource_join_controls(baseline: MappedBundle, change: str, reason: str) -> None:
    raw = bundle(baseline, (op(baseline),)).model_dump(mode="json")
    assert loads_component_bundle(canonical_json(raw), **anchors())
    g = raw["points"][0]["task_graph"]
    if change == "second_slot":
        g["buffers"] = [b for b in g["buffers"] if b["slot_index"] != 1]
    if change == "accumulator":
        next(b for b in g["buffers"] if b["space"] == "accumulator")["offset_bytes"] = 262144
    if change == "dma_engine":
        next(j for j in g["jobs"] if j["kind"] == "dma")["dma_engine_id"] = 4
    if change == "route":
        g["routes"][0]["core_ids"] = [0, 1, 0]
    seal(raw)
    with pytest.raises(ValueError, match=reason):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_exact_sram_end_and_beyond(baseline: MappedBundle) -> None:
    raw = bundle(baseline, (op(baseline),)).model_dump(mode="json")
    sr = next(b for b in raw["points"][0]["task_graph"]["buffers"] if b["slot_index"] == 1)
    sr.update(offset_bytes=16776448, bank=31)
    seal(raw)
    assert loads_component_bundle(canonical_json(raw), **anchors())
    sr["size_bytes"] += 1
    seal(raw)
    with pytest.raises(ValueError, match="SramCapacityExceeded"):
        loads_component_bundle(canonical_json(raw), **anchors())


def test_independent_registry_and_engine_anchors(baseline: MappedBundle) -> None:
    b = bundle(baseline, (op(baseline),))
    with pytest.raises(ValueError, match="RegistryTrustMismatch"):
        loads_component_bundle(
            canonical_json(b),
            **dict(anchors(), trusted_registry_hash=content_hash("untrusted registry")),
        )
    engine = NativeEngineIdentity.model_validate(
        json.loads((FIXTURES / "component-job.json").read_bytes())["engine"]
    )
    auth = dict(
        invocation="production",
        trusted_registry_hash=registry()["registry_hash"],
        trusted_profile_hash=None,
        expected_engine=engine,
    )
    j = prepare_component_job(
        b, point_hash=b.points[0].payload_hash, registry=registry(), profile=None, **auth
    )
    foreign = engine.model_copy(update={"implementation_hash": content_hash("foreign code")})
    with pytest.raises(ValueError, match="EngineIdentityMismatch"):
        loads_component_job(canonical_json(j), **dict(auth, expected_engine=foreign))
    raw = j.model_dump(mode="json")
    raw["owners"][0]["resource"] = "foreign"
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    with pytest.raises(ValueError, match="InvalidResource"):
        loads_component_job(canonical_json(raw), **auth)


def test_import_missing_operand_access_is_refusal(baseline: MappedBundle) -> None:
    raw = bundle(baseline, (op(baseline),)).model_dump(mode="json")
    del raw["scope"]["ops"][0]["operand_access"]["X"]
    seal(raw)
    with pytest.raises(ValueError, match="InvalidCoverage.*operand access"):
        loads_component_bundle(canonical_json(raw), **anchors())
