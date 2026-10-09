"""Literal physical operator/count/timing expectations; no nominal fixtures."""

import copy
import importlib
import json
import math
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash, verify_identity

from rkuarch.engines.protocol import EngineJob, validate_engine_result

FIXTURES = Path(__file__).resolve().parents[2] / "contract/tests/fixtures/u2"


def core():
    return importlib.import_module("rkuarch.engines.analytic.core")


def job():
    value = json.loads((FIXTURES / "engine-job.json").read_text())
    value["engine"] = core().engine_identity().model_dump(mode="json")
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    return EngineJob.model_validate(value)


def test_literal_decoder_counts_and_timing():
    value = job()
    result = core().run_analytic(value)
    assert result.counts.model_dump() == dict(
        matrix_ops=1184.0, vector_ops=572.0, memory_read_bytes=1296.0, memory_write_bytes=288.0
    )
    assert result.duration_ps == pytest.approx(1_892_000.0)
    assert result.u_c0_duration_ps == pytest.approx(1_584_000.0)
    assert result.attribution_ps.compute == pytest.approx(828_000.0)
    assert result.attribution_ps.memory == pytest.approx(1_064_000.0)
    assert math.fsum(result.attribution_ps.model_dump().values()) == result.duration_ps
    validate_engine_result(result, value)
    verify_identity(result, "result_hash")
    assert result.busy_time_ps.compute is None and result.trace is None
    assert all(v is None for v in result.diagnostics.model_dump().values())


def test_aggregate_uses_same_work_and_keeps_isolated_op_predictions():
    value = job().model_dump(mode="json")
    value["mode"] = "aggregate"
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    result = core().run_analytic(EngineJob.model_validate(value))
    assert result.duration_ps == pytest.approx(1_584_000.0)
    assert result.attribution_ps.memory == result.duration_ps
    assert result.attribution_ps.compute == 0
    assert result.per_op == core().run_analytic(job()).per_op


def small_job(matrix_rate=48e12, memory_rate=52e12):
    # X[2,3] + W[3,4] reads = 36 bytes; Y[2,4] writes =16. 48 matrix ops.
    value = job().model_dump(mode="json")
    op = copy.deepcopy(value["point"]["graph"]["groups"][1]["ops"][1])
    assert op["spec"]["operator"] == "q_projection"
    op["spec"]["dimensions"] = dict(M=2, K=3, N=4)
    op.update(depends_on=[], work_repeat=1, weight_copies=1, padding=[], replication=[])
    value["point"]["graph"]["groups"] = [
        dict(id="literal", kind="decoder", repeat=1, depends_on=[], ops=[op])
    ]
    value["point"]["payload_hash"] = content_hash(value["point"], exclude=("payload_hash",))
    value["point_hash"] = value["point"]["payload_hash"]
    value["hardware"]["matrix_peak_ops_per_s"] = matrix_rate
    value["hardware"]["dram_bw_bytes_per_s"] = memory_rate
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    return EngineJob.model_validate(value)


def test_one_ps_fractional_ps_and_compute_tie():
    result = core().run_analytic(small_job())
    assert result.counts.model_dump() == dict(
        matrix_ops=48.0, vector_ops=0.0, memory_read_bytes=36.0, memory_write_bytes=16.0
    )
    assert result.duration_ps == 1.0
    assert result.per_op[0].bound == "compute"
    tiny = core().run_analytic(small_job(96e12, 104e12))
    assert tiny.duration_ps == 0.5


def test_half_byte_rounds_each_operand_before_repeats():
    value = small_job().model_dump(mode="json")
    op = value["point"]["graph"]["groups"][0]["ops"][0]
    op["spec"]["dimensions"] = dict(M=1, K=3, N=1)
    for operand in op["spec"]["operands"].values():
        operand["dtype"] = "int4"
    value["point"]["graph"]["groups"][0]["repeat"] = 2
    value["point"]["payload_hash"] = content_hash(value["point"], exclude=("payload_hash",))
    value["point_hash"] = value["point"]["payload_hash"]
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    result = core().run_analytic(EngineJob.model_validate(value))
    assert result.counts.memory_read_bytes == 8  # 2*(ceil(1.5)+ceil(1.5))
    assert result.counts.memory_write_bytes == 2  # 2*ceil(.5)
    assert result.counts.matrix_ops == 12


def test_wrong_engine_identity_and_detailed_fidelity_refuse():
    value = job().model_dump(mode="json")
    value["engine"]["version"] = "other"
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    with pytest.raises(ValueError, match="EngineIdentityMismatch"):
        core().run_analytic(EngineJob.model_validate(value))
    value = job().model_dump(mode="json")
    value["fidelity_detail"]["compute"] = 1
    value["job_hash"] = content_hash(value, exclude=("job_hash",))
    with pytest.raises(ValueError, match="UnsupportedFidelity"):
        core().run_analytic(EngineJob.model_validate(value))


def test_contributors_are_captured_for_counts_and_duration():
    value = job()
    result = core().run_analytic(value)
    contributors = core().metric_contributors(
        value, json.loads((FIXTURES / "independent-bundle.json").read_text())
    )
    assert "/duration_ps" in contributors
    counts = contributors["/counts/matrix_ops"]
    assert not any(s.kind == "hardware_leaf" for s in counts)
    assert any(
        s.kind == "prepared_content" and s.artifact_hash == value.bundle_hash for s in counts
    )
    duration = contributors["/duration_ps"]
    assert any(s.json_pointer == "/memory/dram/bw_bytes_per_s" for s in duration)
    assert any(s.json_pointer == "/cores/core_type/vector_engine/ops_per_cycle" for s in duration)
    assert all(s.artifact_hash != result.result_hash for s in duration)
