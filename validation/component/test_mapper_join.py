"""Real published A mapper/loader joins, with independent B expectations. No native calls."""

import copy

import pytest
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import MappedBundle
from uarch_contract.prepared import PreparedOp, Producer

from rkuarch.mapping.component import map_component
from rkuarch.workload.component import component_point, prepare_component_bundle
from rkuarch.workload.mapped import export_component_bundle, load_component_bundle
from validation.component.arithmetic import resident
from validation.component.corpus import base, read


def make(m, k, n, state="cold"):
    baseline = MappedBundle.model_validate(base("component"))
    raw = baseline.scope.model_dump(mode="json")["ops"][0]
    raw["spec"]["dimensions"] = dict(M=m, K=k, N=n)
    op = PreparedOp.model_validate(raw)
    g = map_component([op], baseline.hardware_spec, initial_state=state)
    p = component_point([op], g, initial_state=state)
    return prepare_component_bundle(
        [op],
        baseline.hardware_spec,
        p,
        producer=Producer(
            name="B-real-A-mapper-join",
            version="1",
            implementation_hash=content_hash("unit provenance, not authority"),
        ),
        assumptions=baseline.assumptions,
        rank=baseline.rank,
        admission=baseline.admission,
    )


@pytest.mark.parametrize(
    "m,k,n,rows,read_bytes,write_bytes",
    [
        (3, 5, 7, [3], 100, 42),
        (257, 256, 256, [256, 1], 393728, 131584),
        (1024, 256, 256, [256] * 4, 1048576, 524288),
    ],
)
def test_real_mapping_exact_work_and_transfer(m, k, n, rows, read_bytes, write_bytes):
    b = make(m, k, n)
    g = b.points[0].task_graph
    computes = [x for x in g.jobs if x.kind == "compute"]
    assert [x.tile_extents.M for x in computes] == rows
    assert [x.core_id for x in computes] == list(range(len(rows)))
    assert sum(resident(x.tile_extents.M, k, n)[0] for x in computes) == 2 * m * k * n
    assert (
        sum(
            f.payload_bytes
            for x in g.jobs
            if x.kind == "dma" and x.direction == "read"
            for f in x.fragments
        )
        == read_bytes
    )
    assert (
        sum(
            f.payload_bytes
            for x in g.jobs
            if x.kind == "dma" and x.direction == "write"
            for f in x.fragments
        )
        == write_bytes
    )
    for x in g.jobs:
        if x.kind != "dma":
            continue
        hbm = next(
            z
            for z in g.buffers
            if z.id == (x.source.buffer_id if x.direction == "read" else x.destination.buffer_id)
        )
        for f in x.fragments:
            offset = f.source_offset_bytes if x.direction == "read" else f.destination_offset_bytes
            assert f.channel_id == (hbm.offset_bytes + offset) // 256 % 8
            assert f.transaction_bytes == 256
    assert "duration_ps" not in canonical_json(b)


def test_producer_disabled_relocation_and_alternative_mapping(tmp_path, monkeypatch):
    b = make(3, 5, 7)
    registry = read("contract/fixtures/mapped/registry.json")
    anchors = dict(
        invocation="production",
        registry=registry,
        profile=None,
        trusted_registry_hash=registry["registry_hash"],
        trusted_profile_hash=None,
    )
    saved = tmp_path / "saved.json"
    export_component_bundle(b, saved, **anchors)
    relocated = tmp_path / "relocated.json"
    saved.rename(relocated)

    def disabled(*args, **kwargs):
        raise AssertionError("producer ran during replay")

    import rkuarch.mapping.component as mapping
    import rkuarch.workload.component as component
    import rkuarch.workload.prepare as prepare

    monkeypatch.setattr(mapping, "map_component", disabled)
    monkeypatch.setattr(component, "component_point", disabled)
    monkeypatch.setattr(component, "prepare_component_bundle", disabled)
    monkeypatch.setattr(prepare, "prepare", disabled)
    assert load_component_bundle(relocated, **anchors) == b
    # Different valid SRAM placement changes identity while preserving useful work.
    raw = copy.deepcopy(b.model_dump(mode="json"))
    p = raw["points"][0]
    for buf in p["task_graph"]["buffers"]:
        if buf["space"] == "sram":
            buf["offset_bytes"] += 2048
    p["task_graph"]["graph_hash"] = content_hash(p["task_graph"], exclude=("graph_hash",))
    p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    alternate = MappedBundle.model_validate(raw)
    export_component_bundle(alternate, tmp_path / "alternate.json", **anchors)
    assert load_component_bundle(tmp_path / "alternate.json", **anchors) == alternate
    assert alternate.bundle_hash != b.bundle_hash


@pytest.mark.parametrize(
    "name,shape,tiles,expectation",
    [
        ("A-C01-resident", (16, 256, 256), [16], (2097152, 702000)),
        ("A-C02-resident", (3, 5, 7), [3], (210, 547000)),
        ("A-C03-resident", (257, 256, 256), [256, 1], (33685504, 1182000)),
        ("A-C02-cold", (3, 5, 7), [3], (210, 656000)),
    ],
)
def test_published_A_fixture_join(name, shape, tiles, expectation):
    from validation.component.corpus import ROOT

    directory = ROOT / "docs/reviews/U4-A-component-mapper-v1/fixtures"
    import json

    raw = json.loads((directory / (name + ".json")).read_bytes())
    profile_path = directory / (name + ".profile.json")
    profile = json.loads(profile_path.read_bytes()) if profile_path.exists() else None
    registry = read("contract/fixtures/mapped/registry.json")
    loaded = load_component_bundle(
        directory / (name + ".json"),
        invocation="test" if profile else "production",
        registry=registry,
        profile=profile,
        trusted_registry_hash=registry["registry_hash"],
        trusted_profile_hash=profile["profile_hash"] if profile else None,
    )
    assert loaded.bundle_hash == raw["bundle_hash"]
    comp = [x for x in loaded.points[0].task_graph.jobs if x.kind == "compute"]
    assert [x.tile_extents.M for x in comp] == tiles
    assert sum(resident(m, shape[1], shape[2])[0] for m in tiles) == expectation[0]
    if profile:
        assert max(resident(m, shape[1], shape[2])[-1] for m in tiles) == expectation[1]
    else:
        dma = [x for x in loaded.points[0].task_graph.jobs if x.kind == "dma"]
        assert [f.channel_id for x in dma for f in x.fragments] == [0, 1, 2]
        assert 53000 + resident(3, 5, 7)[-1] + 56000 == expectation[1]
