"""Explicit v2 raw capture/replay. No public table/report or evidence attachment."""

from __future__ import annotations

from typing import NamedTuple

from pydantic import TypeAdapter
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.rotary_v2 import CharacterizationRequestV3, PreparedBundleV2

from rkuarch.engines.protocol_v2 import EngineJobV2, EngineResultV2, validate_engine_result
from rkuarch.workload.prepared_v2 import (
    execute_prepared_point,
    raw,
    validate_assumptions,
    validate_execution_bundle,
)


class CapturedWorkV2(NamedTuple):
    bundle: PreparedBundleV2
    assumptions: AssumptionSet
    request: CharacterizationRequestV3
    jobs: tuple[EngineJobV2, ...]
    results: tuple[EngineResultV2, ...]


def capture(bundle: object, *, assumptions: AssumptionSet, workers: int = 1) -> CapturedWorkV2:
    if type(workers) is not int or workers != 1:
        raise ValueError("UnsupportedConcurrency: analytic v2 supports workers=1")
    b = validate_execution_bundle(bundle)
    validate_assumptions(b, assumptions)
    pairs = tuple(
        execute_prepared_point(b, p.payload_hash, assumptions=assumptions) for p in b.points
    )
    request = CharacterizationRequestV3(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    return CapturedWorkV2(
        b, assumptions, request, tuple(j for j, _ in pairs), tuple(r for _, r in pairs)
    )


def replay(
    bundle: object, request: object, jobs: object, results: object, *, assumptions: AssumptionSet
) -> CapturedWorkV2:
    """Authenticate existing captures against actual code; never call preparation."""
    b = validate_execution_bundle(bundle)
    validate_assumptions(b, assumptions)
    r = CharacterizationRequestV3.model_validate(raw(request))
    js = TypeAdapter(tuple[EngineJobV2, ...]).validate_python(jobs)
    rs = TypeAdapter(tuple[EngineResultV2, ...]).validate_python(results)
    if len(js) != len(b.points) or len(rs) != len(js):
        raise ValueError("MissingCoverage: capture points/jobs/results")
    for point, job, result in zip(b.points, js, rs, strict=True):
        if job.point != point:
            raise ValueError("MissingCoverage: exact ordered capture point")
        validate_engine_result(result, job, b, r, assumptions=assumptions)
    return CapturedWorkV2(b, assumptions, r, js, rs)
