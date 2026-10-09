"""Isolated nominal-rk-compatibility/1 algebra, never a production engine.

The caller validates component bindings and A-F12 vocabulary scope before this boundary.
No expected artifacts, fixture IDs, physical operators or reference-selection logic enter it.
The source fingerprint is captured at module load; evaluation has no file/network access.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field
from uarch_contract.assumptions import ModelIdentity
from uarch_contract.common import FrozenModel, Hash, JsonNonNegativeFloat, NonEmpty
from uarch_contract.exports import ExecutionModelInput, ExplicitPrecision
from uarch_contract.hashing import content_hash, verify_identity
from uarch_contract.model_shape import ModelSpec
from uarch_contract.prepared import Query
from uarch_contract.sourced import SourcedValue

_IMPLEMENTATION_HASH = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_WIDTHS = dict(fp32=4, tf32=4, bf16=2, fp16=2, fp8=1, int8=1, fp4=0.5, int4=0.5)


class NominalInput(FrozenModel):
    bandwidth: SourcedValue
    component_binding_hash: Hash
    execution_model: ExecutionModelInput
    format: Literal["uarch-nominal-input/1"]
    input_hash: Hash
    model: ModelSpec
    model_identity: ModelIdentity
    precision: ExplicitPrecision
    query: Query
    selected_peak: SourcedValue
    tp: Annotated[int, Field(strict=True, ge=1)]


class NominalCounts(FrozenModel):
    matrix_ops: JsonNonNegativeFloat
    memory_read_bytes: JsonNonNegativeFloat
    memory_write_bytes: JsonNonNegativeFloat | None
    vector_ops: None


class NominalOutput(FrozenModel):
    counts: NominalCounts
    duration_s: JsonNonNegativeFloat
    format: Literal["uarch-nominal-output/1"]
    input_hash: Hash
    model_identity: ModelIdentity
    omissions: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]
    output_hash: Hash


def candidate_identity() -> ModelIdentity:
    return ModelIdentity(
        name="nominal-rk-compatibility", version="1", implementation_hash=_IMPLEMENTATION_HASH
    )


def evaluate_nominal(value: NominalInput) -> NominalOutput:
    """Recompute declared nominal work; the only input is this accepted carrier.

    Shape/vocabulary and external component binding checks belong to the caller: the
    accepted NominalInput intentionally has no ModelShape or expected-value payload.
    """
    value = NominalInput.model_validate(value)
    verify_identity(value, "input_hash")
    verify_identity(value.execution_model, "execution_model_hash")
    if value.model_identity != candidate_identity():
        raise ValueError("ModelIdentityMismatch: candidate implementation")
    model, query = value.model, value.query
    if model.kv_heads % value.tp or model.n_heads % value.tp:
        raise ValueError("ProjectionScope: A-F12 replicated KV or indivisible heads")
    unit = "TOPS" if value.precision.compute.value.startswith("int") else "TFLOPS"
    if value.selected_peak.unit != unit or value.bandwidth.unit != "TB/s":
        raise ValueError("ParamsMismatch: selected peak/bandwidth unit")
    if value.selected_peak.value <= 0 or value.bandwidth.value <= 0:
        raise ValueError("ParamsMismatch: rates must be positive")
    weights = model.active_params * _WIDTHS[value.precision.compute]
    kv = 2 * model.n_layers * model.kv_heads * model.head_dim * _WIDTHS[value.precision.kv_cache]
    if query.phase == "decode":
        if query.total_context_tokens % query.batch:
            raise ValueError("ProjectionScope: nonuniform decode context")
        matrix = 2 * model.active_params * query.batch
        matrix += 4 * model.n_layers * model.d_model * query.total_context_tokens
        reads = weights + kv * query.total_context_tokens
        writes = None
    else:
        tokens = query.n_prompts * query.prompt_tokens
        matrix = 2 * model.active_params * tokens
        matrix += 2 * model.n_layers * model.d_model * tokens * query.prompt_tokens
        reads, writes = weights, kv * tokens
    compute_efficiency = value.execution_model.compute.value
    memory_efficiency = (
        value.execution_model.memory.value if value.execution_model.memory is not None else 1.0
    )
    duration = max(
        matrix / (value.selected_peak.value * 1e12 * compute_efficiency),
        (reads + (writes or 0)) / (value.bandwidth.value * 1e12 * memory_efficiency),
    )
    result = NominalOutput(
        format="uarch-nominal-output/1",
        input_hash=value.input_hash,
        output_hash="sha256:" + "0" * 64,
        model_identity=candidate_identity(),
        counts=NominalCounts(
            matrix_ops=matrix / value.tp,
            memory_read_bytes=reads / value.tp,
            memory_write_bytes=None if writes is None else writes / value.tp,
            vector_ops=None,
        ),
        duration_s=duration / value.tp,
        omissions=(
            "Nominal model excludes vector work, collectives, spill and DVFS.",
            "Decode writes are not modelled; this is not physical duration validation.",
        ),
    )
    return result.model_copy(update={"output_hash": content_hash(result, exclude=("output_hash",))})


def schemas() -> dict[str, str]:
    """Test-only mirrors of the accepted nominal carrier shapes."""
    result = {}
    for model in (NominalInput, NominalOutput, NominalCounts):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        result[model.__name__ + ".schema.json"] = (
            json.dumps(schema, indent=2, sort_keys=True) + "\n"
        )
    return result
