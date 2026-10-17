"""Prospective tests; run only in private candidate export. Synthetic anchors only."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import MappedBundle, validate_resources

from rkuarch.mapping.component import map_component
from rkuarch.workload.component import component_point, prepare_component_bundle
from validation.component.corpus import two_tiles

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file() and (parent / "contract/fixtures/mapped").is_dir()
)


def baseline():
    return MappedBundle.model_validate_json(
        (ROOT / "contract/fixtures/mapped/component.json").read_bytes()
    )


def seal(raw):
    for p in raw["points"]:
        g = p["task_graph"]
        for key in ("buffers", "jobs", "routes"):
            g[key].sort(key=lambda x: x["id"])
        g["dependencies"].sort(key=lambda x: (x["before"], x["after"]))
        g["graph_hash"] = content_hash(g, exclude=("graph_hash",))
        p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    return raw


def accept(raw):
    b = MappedBundle.model_validate(seal(deepcopy(raw)))
    validate_resources(b, b.points[0])
    return b


def transient():
    raw = two_tiles(True)
    raw["mapping_policy"]["version"] = "2"
    g = raw["points"][0]["task_graph"]
    for buf in g["buffers"]:
        if buf["space"] == "accumulator":
            job = "c" if buf["id"] == "acc" else "z"
            buf.update(offset_bytes=0, producer_id=job, final_consumer_ids=[job])
    g["dependencies"] = [dict(before="c", after="z")]
    return seal(raw)


def test_c04_new_and_old():
    with pytest.raises(ValueError, match="CapacityExceeded"):
        accept(two_tiles(True))
    good = transient()
    assert accept(good)
    old = deepcopy(good)
    old["mapping_policy"]["version"] = "1"
    with pytest.raises(ValueError, match="UnsupportedMapping"):
        accept(old)
    assert accept(good)


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("independent", "LiveBufferAlias"),
        ("false_producer", "InvalidDependency"),
        ("last_use", "InvalidDependency"),
        ("owner", "InvalidResource"),
        ("size", "CapacityExceeded"),
        ("capacity", "CapacityExceeded"),
    ],
)
def test_lifetime_attacks(fault, reason):
    good = transient()
    assert accept(good)
    bad = deepcopy(good)
    g = bad["points"][0]["task_graph"]
    a = next(x for x in g["buffers"] if x["id"] == "acc")
    if fault == "independent":
        g["dependencies"] = []
    if fault == "false_producer":
        a["producer_id"] = "z"
    if fault == "last_use":
        a["final_consumer_ids"] = []
    if fault == "owner":
        a["core_id"] = 1
    if fault == "size":
        a["size_bytes"] -= 4
    if fault == "capacity":
        a["size_bytes"] += 4
    with pytest.raises(ValueError, match=reason):
        accept(bad)
    assert accept(good)


def test_mapper_versions_and_maximum_pair():
    b = baseline()
    raw = b.scope.ops[0].model_dump(mode="json")
    from uarch_contract.prepared import PreparedOp

    ops = []
    for name, n in (("a", 255), ("z", 256)):
        d = deepcopy(raw)
        d.update(id=name, depends_on=[])
        d["spec"]["dimensions"] = {"M": 256, "K": 256, "N": n}
        ops.append(PreparedOp.model_validate(d))
    with pytest.raises(ValueError, match="CapacityExceeded"):
        map_component(ops, b.hardware_spec)
    g = map_component(ops, b.hardware_spec, mapping_version="2")
    assert [(x.offset_bytes, x.size_bytes) for x in g.buffers if x.space == "accumulator"] == [
        (0, 261120),
        (0, 262144),
    ]
    p = component_point(ops, g)
    candidate = prepare_component_bundle(
        ops,
        b.hardware_spec,
        p,
        producer=b.producer,
        assumptions=b.assumptions,
        rank=b.rank,
        admission=b.admission,
        mapping_version="2",
    )
    assert accept(candidate.model_dump(mode="json"))
    assert canonical_json(map_component(b.scope.ops, b.hardware_spec)) == canonical_json(
        map_component(b.scope.ops, b.hardware_spec, mapping_version="1")
    )
    stale = candidate.model_dump(mode="json")
    stale["points"][0]["task_graph"]["dependencies"] = []
    with pytest.raises(ValueError, match="HashMismatch"):
        MappedBundle.model_validate(stale)
    with pytest.raises(ValueError, match="LiveBufferAlias"):
        accept(stale)
    assert accept(candidate.model_dump(mode="json"))


def test_explicit_activity_schema():
    from uarch_contract.mapped import ComponentActivity

    value = dict(
        activity_id="a",
        job_id="c",
        request_id=None,
        subphase="compute_overhead",
        kind="service",
        ready_ps=0,
        start_ps=0,
        end_ps=32000,
        owner_id=0,
        category="overhead",
        receiving_domain="core",
        occupies_resource=True,
        dispatch_ordinal=0,
        completion_ordinal=1,
        predecessors=[],
    )
    assert ComponentActivity.model_validate(value).request_id is None
    for update in (
        {"subphase": "compute:request-string"},
        {"end_ps": -1},
        {"request_id": 3},
        {"kind": "waiting"},
    ):
        with pytest.raises(ValueError):
            ComponentActivity.model_validate(dict(value, **update))


@pytest.mark.parametrize("fault", ["operand_access", "input", "output", "barrier"])
@pytest.mark.parametrize(
    "entry", ["assembly", "bundle_load", "bundle_export", "prepare_job", "job_load", "job_export"]
)
def test_completeness_all_component_entries(fault, entry, tmp_path):
    from uarch_contract.mapped import MappedPoint, NativeEngineIdentity
    from uarch_contract.prepared import PreparedOp

    from rkuarch.workload.component import prepare_component_job
    from rkuarch.workload.mapped import (
        export_component_bundle,
        export_component_job,
        loads_component_bundle,
        loads_component_job,
    )

    b = baseline()
    first = b.scope.ops[0].model_dump(mode="json")
    first.update(id="a", depends_on=[])
    second = deepcopy(first)
    second.update(id="z", depends_on=["a"])
    ops = [PreparedOp.model_validate(first), PreparedOp.model_validate(second)]
    point = component_point(ops, map_component(ops, b.hardware_spec))
    good = prepare_component_bundle(
        ops,
        b.hardware_spec,
        point,
        producer=b.producer,
        assumptions=b.assumptions,
        rank=b.rank,
        admission=b.admission,
    )
    registry = json.loads((ROOT / "contract/fixtures/mapped/registry.json").read_bytes())
    args = dict(
        invocation="production",
        registry=registry,
        profile=None,
        trusted_registry_hash=registry["registry_hash"],
        trusted_profile_hash=None,
    )
    template = json.loads((ROOT / "contract/fixtures/mapped/component-job.json").read_bytes())
    engine = NativeEngineIdentity.model_validate(template["engine"])
    goodjob = prepare_component_job(
        good, point_hash=point.payload_hash, expected_engine=engine, **args
    )
    raw = good.model_dump(mode="json")
    g = raw["points"][0]["task_graph"]
    reason = "InvalidTransfer"
    if fault == "operand_access":
        raw["scope"]["ops"][0]["operand_access"].pop("X")
        reason = "InvalidCoverage"
    elif fault == "input":
        dma = next(j for j in g["jobs"] if j["kind"] == "dma" and j["direction"] == "read")
        dma["source"]["size_bytes"] = dma["destination"]["size_bytes"] = 2
        dma["fragments"][0]["payload_bytes"] = 2
    elif fault == "output":
        dma = next(
            j
            for j in g["jobs"]
            if j["kind"] == "dma" and j["direction"] == "write" and j["op_id"] == "z"
        )
        g["jobs"].remove(dma)
        g["buffers"] = [x for x in g["buffers"] if x["id"] != dma["destination"]["buffer_id"]]
        next(x for x in g["buffers"] if x["id"] == dma["source"]["buffer_id"])[
            "final_consumer_ids"
        ] = []
        g["dependencies"] = [x for x in g["dependencies"] if x["after"] != dma["id"]]
    else:
        next(j for j in g["jobs"] if j["kind"] == "barrier")["owner_id"] = 0
        reason = "InvalidResource"
    seal(raw)
    jobraw = goodjob.model_dump(mode="json")
    jobraw.update(
        workload_closure=raw,
        bundle_hash=raw["bundle_hash"],
        mapped_point=raw["points"][0],
        point_hash=raw["points"][0]["payload_hash"],
    )
    jobraw["job_hash"] = content_hash(jobraw, exclude=("job_hash",))
    jobargs = {k: v for k, v in args.items() if k not in ("registry", "profile")}
    jobargs["expected_engine"] = engine
    with pytest.raises(ValueError, match=reason):
        if entry == "assembly":
            prepare_component_bundle(
                [PreparedOp.model_validate(x) for x in raw["scope"]["ops"]],
                b.hardware_spec,
                MappedPoint.model_validate(raw["points"][0]),
                producer=b.producer,
                assumptions=b.assumptions,
                rank=b.rank,
                admission=b.admission,
            )
        elif entry == "bundle_load":
            loads_component_bundle(canonical_json(raw), **args)
        elif entry == "bundle_export":
            export_component_bundle(raw, tmp_path / "refused.json", **args)
        elif entry == "prepare_job":
            prepare_component_job(
                MappedBundle.model_validate(raw),
                point_hash=raw["points"][0]["payload_hash"],
                expected_engine=engine,
                **args,
            )
        elif entry == "job_load":
            loads_component_job(canonical_json(jobraw), **jobargs)
        else:
            export_component_job(jobraw, tmp_path / "refused.json", **jobargs)
    assert not (tmp_path / "refused.json").exists()
    assert loads_component_bundle(canonical_json(good), **args) == good
    assert loads_component_job(canonical_json(goodjob), **jobargs) == goodjob


@pytest.mark.parametrize("producer_kind", ["dma", "barrier"])
def test_false_producer_is_not_merely_an_ancestor(producer_kind):
    from uarch_contract.prepared import PreparedOp

    b = baseline()
    first = b.scope.ops[0].model_dump(mode="json")
    first.update(id="a", depends_on=[])
    second = deepcopy(first)
    second.update(id="z", depends_on=["a"])
    second["spec"]["dimensions"]["M"] = 4
    ops = [PreparedOp.model_validate(first), PreparedOp.model_validate(second)]
    g = map_component(ops, b.hardware_spec, mapping_version="2")
    p = component_point(ops, g)
    good = prepare_component_bundle(
        ops,
        b.hardware_spec,
        p,
        producer=b.producer,
        assumptions=b.assumptions,
        rank=b.rank,
        admission=b.admission,
        mapping_version="2",
    ).model_dump(mode="json")
    bad = deepcopy(good)
    graph = bad["points"][0]["task_graph"]
    if producer_kind == "dma":
        acc = next(x for x in graph["buffers"] if x["space"] == "accumulator")
        producer = next(x for x in graph["jobs"] if x["kind"] == "dma")
    else:
        acc = [x for x in graph["buffers"] if x["space"] == "accumulator"][-1]
        producer = next(x for x in graph["jobs"] if x["kind"] == "barrier")
    acc["producer_id"] = producer["id"]
    with pytest.raises(ValueError, match="InvalidDependency.*producer"):
        accept(bad)
    assert accept(good)


def test_uniform_reverse_id_dependency_uses_topological_operand_placement():
    from uarch_contract.prepared import PreparedOp

    b = baseline()
    ops = []
    for name, dependencies in [("a", ["b"]), ("b", [])]:
        raw = b.scope.ops[0].model_dump(mode="json")
        raw.update(id=name, depends_on=dependencies)
        raw["spec"]["dimensions"] = dict(M=256, K=256, N=256)
        ops.append(PreparedOp.model_validate(raw))
    old = map_component(ops, b.hardware_spec, mapping_version="1")
    new = map_component(ops, b.hardware_spec, mapping_version="2")
    assert old == map_component(ops, b.hardware_spec)
    assert old.dependencies == new.dependencies
    assert all(x.producer_id is None for x in new.buffers if x.space == "accumulator")
    before = {x.id: x.offset_bytes for x in old.buffers}
    after = {x.id: x.offset_bytes for x in new.buffers}
    assert sum(before[key] != after[key] for key in before) == 14
    assert old.graph_hash != new.graph_hash
    assert min(x.offset_bytes for x in new.buffers if x.space == "hbm" and x.op_id == "b") < min(
        x.offset_bytes for x in new.buffers if x.space == "hbm" and x.op_id == "a"
    )
