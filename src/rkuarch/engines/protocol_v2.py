"""Additive protocol/2 carriers and complete closure admission, never v1 fallback."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.common import FrozenModel, Hash, JsonFloat
from uarch_contract.fidelity import FidelityDetail
from uarch_contract.hashing import content_hash, verify_identity
from uarch_contract.precision import Precision
from uarch_contract.prepared import Producer, RankScope
from uarch_contract.rotary_v2 import CharacterizationRequestV3, PreparedPointV2, RotaryCoefficients
from uarch_contract.table import Counts, Diagnostics, OpResult

from rkuarch.engines.protocol import (
    EngineResultAttributionPs,
    EngineResultBusyTimePs,
    ResolvedHardware,
)


class ModelIdentityV2(FrozenModel):
    implementation_hash: Hash
    name: Literal["physical-resolved"]
    version: Literal["2"]


class EngineIdentityV2(FrozenModel):
    implementation_hash: Hash
    model: ModelIdentityV2
    name: Literal["analytic"]
    version: Literal["resolved-ops/2"]


class EngineJobV2(FrozenModel):
    coefficients: RotaryCoefficients
    accounting: Literal["resolved-ops/2"]
    assumptions_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    bundle_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    engine: EngineIdentityV2
    fidelity_detail: FidelityDetail
    hardware: ResolvedHardware
    initial_state: Literal["steady", "cold"]
    job_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    mode: Literal["aggregate", "per_op"]
    point: PreparedPointV2
    point_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    precision: Precision
    producer: Producer
    protocol: Literal["uarch-engine/2"]
    rank: RankScope
    request_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    seed: Annotated[int, Field(strict=True, ge=0)]
    state_model: Literal["stateless_roofline"]


class EngineResultV2(FrozenModel):
    attribution_ps: EngineResultAttributionPs
    busy_time_ps: EngineResultBusyTimePs
    counts: Counts
    diagnostics: Diagnostics
    duration_ps: Annotated[JsonFloat, Field(ge=0)]
    engine: EngineIdentityV2
    fidelity_detail: FidelityDetail
    job_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    per_op: Annotated[tuple[OpResult, ...], Field(min_length=1)]
    protocol: Literal["uarch-engine/2"]
    result_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    simulator_metrics: None
    trace: None
    u_c0_duration_ps: Annotated[JsonFloat, Field(ge=0)]
    unrepresented: Annotated[tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=0)]


SCHEMA_ROOTS = (ModelIdentityV2, EngineIdentityV2, EngineJobV2, EngineResultV2)


def validate_engine_job(
    value: object, bundle: object, request: object, *, assumptions: AssumptionSet
) -> EngineJobV2:
    from rkuarch.engines.analytic.rotary_v2 import engine_identity
    from rkuarch.hw.derive import resolve_hardware
    from rkuarch.workload.prepared_v2 import raw, validate_assumptions, validate_execution_bundle

    j = EngineJobV2.model_validate(raw(value))
    b = validate_execution_bundle(bundle)
    r = CharacterizationRequestV3.model_validate(raw(request))
    validate_assumptions(b, assumptions)
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
        or j.coefficients != b.coefficients
    ):
        raise ValueError("EngineJobMismatch: bundle/request/point/rank/producer/coefficients")
    if (
        j.initial_state != j.point.initial_state
        or j.initial_state != r.initial_state
        or j.precision != r.precision
        or j.fidelity_detail != r.uarch_fidelity
        or j.mode != r.analytic_mode
        or j.accounting != r.accounting
        or j.seed != r.seed
        or j.assumptions_hash != r.assumptions_hash
    ):
        raise ValueError("EngineJobMismatch: duplicated execution input")
    if j.hardware != resolve_hardware(
        b.hardware_spec, r.precision, frequency_ratio=j.point.frequency_ratio
    ):
        raise ValueError("EngineJobMismatch: resolved sourced hardware")
    if j.engine != engine_identity():
        raise ValueError("EngineIdentityMismatch: actual execution closure")
    return j


def validate_engine_result(
    value: object, job: object, bundle: object, request: object, *, assumptions: AssumptionSet
) -> EngineResultV2:
    from rkuarch.engines.analytic.rotary_v2 import _evaluate
    from rkuarch.workload.prepared_v2 import raw

    j = validate_engine_job(job, bundle, request, assumptions=assumptions)
    r = EngineResultV2.model_validate(raw(value))
    verify_identity(r, "result_hash")
    # Exact replay checks every per-op scope/count/time and all null diagnostics, not
    # merely self-consistent sums. Literal test expectations are independently authored.
    if r != _evaluate(j):
        raise ValueError("EngineResultMismatch: exact admitted-work replay")
    return r


def schemas() -> dict[str, str]:
    import json

    result = {}
    for model in SCHEMA_ROOTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[model.__name__ + ".json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def generate(*, check: bool = False) -> list[str]:
    from pathlib import Path

    directory = Path(__file__).with_name("schema") / "v2"
    expected = schemas()
    actual = {p.name: p.read_text() for p in directory.glob("*.json")}
    stale = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
    if not check:
        if actual.keys() - expected.keys():
            raise ValueError("Unexpected v2 schema roots")
        directory.mkdir(parents=True, exist_ok=True)
        for name, text in expected.items():
            (directory / name).write_text(text)
    return stale


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = generate(check=args.check)
    if args.check and stale:
        raise SystemExit("Stale v2 schemas: " + ", ".join(stale))
