"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator
from uarch_contract.assumptions import ModelIdentity
from uarch_contract.common import FrozenModel, JsonFloat
from uarch_contract.fidelity import FidelityDetail
from uarch_contract.precision import Precision
from uarch_contract.prepared import PreparedPoint, Producer, RankScope
from uarch_contract.table import Counts, Diagnostics, OpResult


class EngineIdentity(FrozenModel):
    implementation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    model: ModelIdentity
    name: Literal["analytic"]
    version: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def physical_model_only(self) -> EngineIdentity:
        if self.model.name != "physical-resolved":
            raise ValueError("EngineIdentity: nominal compatibility is not a production engine")
        return self


class ResolvedHardware(FrozenModel):
    array_cols: Annotated[int, Field(strict=True, ge=1)]
    array_rows: Annotated[int, Field(strict=True, ge=1)]
    core_freq_hz: Annotated[int, Field(strict=True, ge=1)]
    dram_bw_bytes_per_s: Annotated[JsonFloat, Field(gt=0)]
    dram_capacity_bytes: Annotated[int, Field(strict=True, ge=1)]
    dram_freq_hz: Annotated[int, Field(strict=True, ge=1)]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    matrix_peak_ops_per_s: Annotated[JsonFloat, Field(gt=0)]
    noc_freq_hz: Annotated[int, Field(strict=True, ge=1)]
    vector_peak_ops_per_s: Annotated[JsonFloat, Field(gt=0)]


class EngineJob(FrozenModel):
    accounting: Literal["resolved-ops/1"]
    assumptions_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    bundle_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    engine: EngineIdentity
    fidelity_detail: FidelityDetail
    hardware: ResolvedHardware
    initial_state: Literal["steady", "cold"]
    job_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    mode: Literal["aggregate", "per_op"]
    point: PreparedPoint
    point_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    precision: Precision
    producer: Producer
    protocol: Literal["uarch-engine/1"]
    rank: RankScope
    request_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    seed: Annotated[int, Field(strict=True, ge=0)]
    state_model: Literal["stateless_roofline"]


class EngineResultAttributionPs(FrozenModel):
    compute: Annotated[JsonFloat, Field(ge=0)]
    memory: Annotated[JsonFloat, Field(ge=0)]
    noc: Annotated[JsonFloat, Field(ge=0)]
    overhead: Annotated[JsonFloat, Field(ge=0)]
    sync: Annotated[JsonFloat, Field(ge=0)]


class EngineResultBusyTimePs(FrozenModel):
    compute: Annotated[JsonFloat, Field(ge=0)] | None
    memory: Annotated[JsonFloat, Field(ge=0)] | None
    noc: Annotated[JsonFloat, Field(ge=0)] | None


class EngineResult(FrozenModel):
    attribution_ps: EngineResultAttributionPs
    busy_time_ps: EngineResultBusyTimePs
    counts: Counts
    diagnostics: Diagnostics
    duration_ps: Annotated[JsonFloat, Field(ge=0)]
    engine: EngineIdentity
    fidelity_detail: FidelityDetail
    job_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    per_op: Annotated[tuple[OpResult, ...], Field(min_length=1)]
    protocol: Literal["uarch-engine/1"]
    result_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    simulator_metrics: None
    trace: None
    u_c0_duration_ps: Annotated[JsonFloat, Field(ge=0)]
    unrepresented: Annotated[tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=0)]


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    EngineIdentity,
    ResolvedHardware,
    EngineJob,
    EngineResult,
)

for _model in (
    EngineIdentity,
    ResolvedHardware,
    EngineJob,
    EngineResultAttributionPs,
    EngineResultBusyTimePs,
    EngineResult,
):
    _model.model_rebuild()


def validate_engine_result(value: object, job: object) -> EngineResult:
    """Verify captured result identity, duplicated job bindings and arithmetic conservation.

    Does not execute the physical model or certify that captured timings match hardware.
    A2 owns original-work count computation and hardware derivation/replay.
    """
    import math

    from uarch_contract.hashing import verify_identity

    r, j = EngineResult.model_validate(value), EngineJob.model_validate(job)
    verify_identity(j, "job_hash")
    verify_identity(r, "result_hash")
    if r.job_hash != j.job_hash or r.engine != j.engine or r.fidelity_detail != j.fidelity_detail:
        raise ValueError("EngineResultMismatch: job/engine/fidelity")
    for name in type(r.counts).model_fields:
        values = [getattr(op.counts, name) for op in r.per_op]
        if any(x is None for x in values) or getattr(r.counts, name) != math.fsum(values):
            raise ValueError("EngineResultMismatch: counts/" + name)
    for op in r.per_op:
        duration = max(op.compute_time_ps, op.memory_time_ps)
        bound = "compute" if op.compute_time_ps >= op.memory_time_ps else "memory"
        if op.duration_ps != duration or op.bound != bound:
            raise ValueError("EngineResultMismatch: per_op duration/bound")
    aggregate = max(
        math.fsum(op.compute_time_ps for op in r.per_op),
        math.fsum(op.memory_time_ps for op in r.per_op),
    )
    expected = aggregate if j.mode == "aggregate" else math.fsum(op.duration_ps for op in r.per_op)
    if not math.isclose(r.duration_ps, expected, rel_tol=1e-9, abs_tol=1e-3):
        raise ValueError("EngineResultMismatch: duration_ps")
    if not math.isclose(
        math.fsum(r.attribution_ps.model_dump().values()), r.duration_ps, rel_tol=1e-9, abs_tol=1e-3
    ):
        raise ValueError("EngineResultMismatch: attribution_ps")
    if any(
        x is not None
        for x in (*r.busy_time_ps.model_dump().values(), *r.diagnostics.model_dump().values())
    ):
        raise ValueError("EngineResultMismatch: unmodelled busy time/diagnostics")
    return r


def schemas() -> dict[str, str]:
    """The four standalone engine schemas, from this module's sole authority."""
    import json

    result = {}
    for model in SCHEMA_ROOTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[model.__name__ + ".json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def generate(*, check: bool = False) -> list[str]:
    """Write protocol schema mirrors, or return stale names without writing."""
    from pathlib import Path

    directory = Path(__file__).with_name("schema")
    expected = schemas()
    actual = {p.name: p.read_text() for p in directory.glob("*.json")}
    stale = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
    if not check:
        directory.mkdir(exist_ok=True)
        for name, text in expected.items():
            (directory / name).write_text(text)
    return stale


def validate_engine_job(value: object, bundle: object, request: object) -> EngineJob:
    """Verify an imported job's request/bundle/point identity and duplicated fields.

    Numeric hardware projection against original sourced leaves is an A2 derivation
    obligation; this check binds the projection to the correct original hardware hash.
    """
    from uarch_contract.hashing import content_hash, verify_identity
    from uarch_contract.prepared import validate_prepared_bundle
    from uarch_contract.request import CharacterizationRequest

    j = EngineJob.model_validate(value)
    b = validate_prepared_bundle(bundle)
    r = CharacterizationRequest.model_validate(request)
    verify_identity(j, "job_hash")
    if (
        r.prepared_input_hash != b.bundle_hash
        or content_hash(r, exclude=("prepared_input_hash",)) != b.intent_hash
    ):
        raise ValueError("EngineJobMismatch: reconstructed request")
    if (
        j.bundle_hash != b.bundle_hash
        or j.request_hash != content_hash(r)
        or j.point_hash != j.point.payload_hash
        or j.point not in b.points
        or j.rank != b.rank
        or j.producer != b.producer
    ):
        raise ValueError("EngineJobMismatch: bundle/request/point/rank/producer")
    if (
        j.initial_state != j.point.initial_state
        or j.initial_state != r.initial_state
        or j.precision != r.precision
        or j.fidelity_detail != r.uarch_fidelity
        or j.mode != r.analytic_mode
        or j.accounting != r.accounting
        or j.seed != r.seed
        or j.assumptions_hash != r.assumptions_hash
        or j.hardware.hardware_spec_hash != r.hardware_spec_hash
    ):
        raise ValueError("EngineJobMismatch: duplicated execution input")
    return j
