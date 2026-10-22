"""Literal R expectations: independent arithmetic, never mapper-derived oracles."""

from copy import deepcopy

import pytest
from uarch_contract.hashing import content_hash


def test_matrix_tail_work_and_partial_traffic():
    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import matrix_source, nominal_hardware

    b = map_reference(matrix_source(3, 130, 7), nominal_hardware())
    tasks = b.points[0].task_graph.jobs
    dots = [t for t in tasks if t.kind == "compute"]
    assert [(t.tile_extents.M, t.tile_extents.K, t.tile_extents.N) for t in dots] == [
        (3, 128, 7),
        (3, 2, 7),
    ]
    assert sum(2 * t.tile_extents.M * t.tile_extents.K * t.tile_extents.N for t in dots) == 5460
    assert len({t.accumulator_buffer_id for t in dots}) == 1
    assert (
        sum(
            t.source.size_bytes
            for t in tasks
            if t.kind == "local_transfer" and t.purpose == "partial"
        )
        == 336
    )


def test_int8_output_is_int32():
    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import matrix_source, nominal_hardware

    b = map_reference(matrix_source(3, 5, 7, precision="int8"), nominal_hardware())
    assert [
        x.size_bytes
        for x in b.points[0].task_graph.buffers
        if x.operand == "Y" and x.space == "hbm"
    ] == [84]
    assert all(
        x.accumulator_dtype == "int32" for x in b.points[0].task_graph.jobs if x.kind == "compute"
    )


def test_explicit_stub_admitted_missing_refused():
    from uarch_contract.reference import TpuV5eReference

    from rkuarch.workload.reference import nominal_hardware

    h = nominal_hardware()
    assert h.kernel_startup_ps.provenance == "stub"
    raw = h.model_dump(mode="json")
    del raw["vector_tile_ps"]
    with pytest.raises(ValueError):
        TpuV5eReference.model_validate(raw)


def test_alias_and_missing_coverage_refused():
    from uarch_contract.reference import ReferenceBundle

    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import matrix_source, nominal_hardware

    raw = map_reference(matrix_source(3, 130, 7), nominal_hardware()).model_dump(mode="json")
    bad = deepcopy(raw)
    g = bad["points"][0]["task_graph"]
    g["coverage"] = g["coverage"][:-1]
    g["graph_hash"] = content_hash(g, exclude=("graph_hash",))
    bad["points"][0]["payload_hash"] = content_hash(bad["points"][0], exclude=("payload_hash",))
    bad["bundle_hash"] = content_hash(bad, exclude=("bundle_hash",))
    with pytest.raises(ValueError):
        ReferenceBundle.model_validate(bad)


def test_analytic_retains_useful_work_baseline():
    from fractions import Fraction

    from rkuarch.engines.analytic.reference import resolve_reference
    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import matrix_source, nominal_hardware

    b = map_reference(matrix_source(3, 5, 7), nominal_hardware())
    result = resolve_reference(b)
    # 210 useful matrix operations, 21 final casts; exactly 142 HBM operand bytes.
    assert result["ops"]["dot"]["compute_ps"] == Fraction(210 * 10**12, 197 * 10**12) + Fraction(
        21 * 1000, 1024
    )
    assert result["ops"]["dot"]["operand_hbm_bytes"] == 142
    raw = b.hardware_spec.model_dump(mode="json")
    raw["kernel_startup_ps"]["value"] *= 10
    from uarch_contract.reference import TpuV5eReference

    other = map_reference(matrix_source(3, 5, 7), TpuV5eReference.model_validate(raw))
    assert resolve_reference(other) == result


def test_reference_canonical_bytes_and_hashes():
    from uarch_contract.hashing import canonical_json as original
    from uarch_contract.reference_json import canonical_json as large
    from uarch_contract.reference_json import content_hash as large_hash

    from rkuarch.mapping.reference import map_reference
    from rkuarch.workload.reference import matrix_source, nominal_hardware, prepare_job

    job = prepare_job(map_reference(matrix_source(3, 130, 7), nominal_hardware()))
    for value in (
        job,
        job.model_dump(mode="json"),
        dict(z=-0.0, a=[1, 1.0, 1e-7, 1e20, "λ", None]),
    ):
        assert large(value) == original(value)
        assert large_hash(value) == content_hash(value)
