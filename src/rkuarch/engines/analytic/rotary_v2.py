"""Stateless physical resolved-operator rooflines. No preparation or oracle imports."""

from __future__ import annotations

import math
from typing import Any

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import DependencySelector
from uarch_contract.rotary_v2 import CharacterizationRequestV3, PreparedOpV2
from uarch_contract.table import (
    Counts,
    Diagnostics,
    OpResult,
    ReportScope,
    ReportScopePrecisionRoles,
)

from rkuarch.engines.protocol import EngineResultAttributionPs, EngineResultBusyTimePs
from rkuarch.engines.protocol_v2 import (
    EngineIdentityV2,
    EngineJobV2,
    EngineResultV2,
    ModelIdentityV2,
    validate_engine_job,
)
from rkuarch.workload.prepared_v2 import validate_execution_bundle, validate_op

from .identity_v2 import implementation_hash

_WIDTHS = dict(fp32=4, tf32=4, bf16=2, fp16=2, fp8=1, int8=1, fp4=0.5, int4=0.5)
_PROJECTIONS = {
    "q_projection",
    "k_projection",
    "v_projection",
    "output_projection",
    "ffn_up",
    "ffn_gate",
    "ffn_down",
    "lm_head",
}


def engine_identity() -> EngineIdentityV2:
    identity = implementation_hash()
    return EngineIdentityV2(
        name="analytic",
        version="resolved-ops/2",
        implementation_hash=identity,
        model=ModelIdentityV2(name="physical-resolved", version="2", implementation_hash=identity),
    )


def counts(op: PreparedOpV2, repeat: int, *, causal: bool) -> dict[str, int]:
    validate_op(op)
    dims, name = op.spec.dimensions, str(op.spec.operator)
    matrix = vector = 0
    if name == "rotary_embedding":
        elements = dims["B"] * dims["S"] * dims["H"] * dims["R"]
        vector = 3 * elements
        if op.spec.operands["X"].dtype != "fp32":
            vector += 2 * elements
    elif name in _PROJECTIONS:
        matrix = 2 * dims["M"] * dims["K"] * dims["N"]
    elif name in ("normalization", "activation", "residual_addition"):
        factor = (
            6
            if name == "normalization"
            else 1
            if name == "residual_addition"
            else 6
            if "G" in op.spec.operands
            else 5
        )
        vector = factor * dims["M"] * dims["D"]
    elif name in ("attention_fused", "qk_score", "softmax", "av_application"):
        if causal and dims["S"] != dims["T"]:
            # Decode has S=1, reads all valid context; causal triangular applies to prefill only.
            pairs = dims["B"] * dims["Hq"] * dims["S"] * dims["T"]
        elif causal:
            pairs = dims["B"] * dims["Hq"] * dims["S"] * (dims["S"] + 1) // 2
        else:
            pairs = dims["B"] * dims["Hq"] * dims["S"] * dims["T"]
        if name != "softmax":
            matrix = (4 if name == "attention_fused" else 2) * pairs * dims["D"]
        if name in ("attention_fused", "softmax"):
            vector = 5 * pairs
    reads = writes = 0
    for key, operand in op.spec.operands.items():
        if name == "embedding" and key == "W":
            assert op.embedding_local_tokens is not None
            extent = op.embedding_local_tokens * dims["D"]
        else:
            extent = math.prod(dims[d] for d in operand.dimensions)
        # Exact integer extent; half-byte packing rounds EACH transfer before multiplicity.
        width = _WIDTHS[operand.dtype]
        size = (extent + 1) // 2 if width == 0.5 else extent * int(width)
        if op.operand_access[key] in ("read", "read_write"):
            reads += size
        if op.operand_access[key] in ("write", "read_write"):
            writes += size
    instances = repeat * op.work_repeat
    return dict(
        matrix_ops=matrix * instances,
        vector_ops=vector * instances,
        memory_read_bytes=reads * instances,
        memory_write_bytes=writes * instances,
    )


def run_analytic(job: object, *, bundle: object, assumptions: AssumptionSet) -> EngineResultV2:
    """Require complete authenticated inputs; carrier parsing alone never executes."""
    b = validate_execution_bundle(bundle)
    request = CharacterizationRequestV3(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    admitted = validate_engine_job(job, b, request, assumptions=assumptions)
    return _evaluate(admitted)


def _evaluate(job: EngineJobV2) -> EngineResultV2:
    """Internal deterministic evaluation; only public callers perform full closure admission."""
    detail = job.fidelity_detail
    hardware = job.hardware
    per_op = []
    for group in job.point.graph.groups:
        for op in group.ops:
            work = Counts(
                **counts(op, group.repeat, causal=job.point.graph.attention_mask == "causal")
            )
            assert work.vector_ops is not None and work.memory_write_bytes is not None
            compute_s = math.fsum(
                (
                    work.matrix_ops / hardware.matrix_peak_ops_per_s,
                    work.vector_ops / hardware.vector_peak_ops_per_s,
                )
            )
            memory_bytes = work.memory_read_bytes + work.memory_write_bytes
            memory_s = memory_bytes / hardware.dram_bw_bytes_per_s
            compute_ps, memory_ps = compute_s * 1e12, memory_s * 1e12
            duration_ps = max(compute_ps, memory_ps)
            intensity = work.matrix_ops / memory_bytes if memory_bytes else None
            ridge = hardware.matrix_peak_ops_per_s / hardware.dram_bw_bytes_per_s
            regime: Any = (
                None
                if intensity is None
                else "low"
                if intensity < 0.5 * ridge
                else "high"
                if intensity > 2 * ridge
                else "middle"
            )
            fill: Any = None
            if str(op.spec.operator) in _PROJECTIONS:
                fill = (
                    "full"
                    if op.spec.dimensions["M"] >= hardware.array_rows
                    and op.spec.dimensions["N"] >= hardware.array_cols
                    else "underfilled"
                )
            scope = ReportScope(
                op_class=str(op.spec.operator),
                intensity_regime=regime,
                array_fill=fill,
                noc_load_regime=None,
                dram_load_regime=None,
                mapping_match=None,
                precision_roles=ReportScopePrecisionRoles(
                    compute=job.precision.compute,
                    kv_cache=job.precision.kv_cache,
                    operands={k: v.dtype for k, v in op.spec.operands.items()},
                ),
            )
            per_op.append(
                OpResult(
                    id=group.id + "/" + op.id,
                    group_id=group.id,
                    instances=group.repeat * op.work_repeat,
                    counts=work,
                    compute_time_ps=compute_ps,
                    memory_time_ps=memory_ps,
                    duration_ps=duration_ps,
                    bound="compute" if compute_ps >= memory_ps else "memory",
                    operational_intensity_ops_per_byte=intensity,
                    achieved_ops_per_s=(
                        work.matrix_ops / max(compute_s, memory_s) if duration_ps else None
                    ),
                    ridge_ops_per_byte=ridge,
                    scope=scope,
                    matrix_peak_ops_per_s=hardware.matrix_peak_ops_per_s,
                    vector_peak_ops_per_s=hardware.vector_peak_ops_per_s,
                    dram_bw_bytes_per_s=hardware.dram_bw_bytes_per_s,
                )
            )
    compute_total = math.fsum(o.compute_time_ps for o in per_op)
    memory_total = math.fsum(o.memory_time_ps for o in per_op)
    aggregate = max(compute_total, memory_total)
    attribution = dict(compute=0.0, memory=0.0, noc=0.0, overhead=0.0, sync=0.0)
    if job.mode == "aggregate":
        duration = aggregate
        attribution["compute" if compute_total >= memory_total else "memory"] = duration
    else:
        duration = math.fsum(o.duration_ps for o in per_op)
        for bound in ("compute", "memory"):
            attribution[bound] = math.fsum(o.duration_ps for o in per_op if o.bound == bound)
    totals = {
        name: math.fsum(getattr(o.counts, name) for o in per_op) for name in Counts.model_fields
    }
    unrepresented = [
        "cores.core_type.dma",
        "cores.core_type.job_overhead_cycles",
        "cores.core_type.matrix_engine.dataflows",
        "cores.core_type.matrix_engine.operand_buffer_bytes",
        "cores.core_type.sram",
        "energy",
        "memory.controllers",
        "memory.dram.organization",
        "memory.dram.timing",
        "memory.interleave",
        "nocs",
        "static_power_w",
        "sync",
        "tdp_w",
    ]
    if detail.shared_sram is not None:
        unrepresented.append("shared_sram")
    if any(
        v.dtype != job.precision.compute
        for g in job.point.graph.groups
        for o in g.ops
        if str(o.spec.operator) != "rotary_embedding"
        for v in o.spec.operands.values()
    ):
        unrepresented.append("precision_conversion")
    result = EngineResultV2(
        protocol="uarch-engine/2",
        result_hash="sha256:" + "0" * 64,
        job_hash=job.job_hash,
        engine=job.engine,
        fidelity_detail=detail,
        duration_ps=duration,
        u_c0_duration_ps=aggregate,
        counts=Counts(**totals),
        per_op=tuple(per_op),
        attribution_ps=EngineResultAttributionPs(**attribution),
        busy_time_ps=EngineResultBusyTimePs(compute=None, memory=None, noc=None),
        diagnostics=Diagnostics(),
        simulator_metrics=None,
        trace=None,
        unrepresented=tuple(sorted(unrepresented)),
    )
    result = result.model_copy(
        update={"result_hash": content_hash(result, exclude=("result_hash",))}
    )
    return result


def metric_contributors(
    job: object, bundle: object, *, assumptions: AssumptionSet
) -> dict[str, tuple[DependencySelector, ...]]:
    """Conservative dependencies, not independent evidence or display permissions.

    Select the complete point so query, edges, repeats, positions, rotary bindings and
    cache encoding stay authenticated together. Broader than a minimal per-op recipe;
    no v1 evidence attachment API consumes these selectors automatically.
    """
    b = validate_execution_bundle(bundle)
    request = CharacterizationRequestV3(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    j = validate_engine_job(job, b, request, assumptions=assumptions)
    index = b.points.index(j.point)
    common = tuple(
        DependencySelector(kind="prepared_content", artifact_hash=b.bundle_hash, json_pointer=path)
        for path in (f"/points/{index}", "/coefficients", "/intent/position_encoding", "/rank")
    ) + (
        DependencySelector(
            kind="model_assumption", artifact_hash=j.assumptions_hash, json_pointer="/algorithms"
        ),
    )
    timing = common + tuple(
        DependencySelector(
            kind="hardware_leaf", artifact_hash=b.intent.hardware_spec_hash, json_pointer=path
        )
        for path in (
            "/clock_domains/core/freq_hz",
            "/cores/grid/rows",
            "/cores/grid/cols",
            "/cores/core_type/matrix_engine/array/rows",
            "/cores/core_type/matrix_engine/array/cols",
            f"/cores/core_type/matrix_engine/macs_per_cycle/{j.precision.compute}",
            "/cores/core_type/vector_engine/ops_per_cycle",
            "/memory/dram/bw_bytes_per_s",
        )
    )
    result = {"/counts/" + field: common for field in Counts.model_fields}
    result["/duration_ps"] = result["/u_c0_duration_ps"] = timing
    ordinal = 0
    for group in j.point.graph.groups:
        for _op in group.ops:
            for field in Counts.model_fields:
                result[f"/per_op/{ordinal}/counts/{field}"] = common
            result[f"/per_op/{ordinal}/instances"] = common
            for field in (
                "duration_ps",
                "compute_time_ps",
                "memory_time_ps",
                "operational_intensity_ops_per_byte",
                "achieved_ops_per_s",
                "ridge_ops_per_byte",
                "matrix_peak_ops_per_s",
                "vector_peak_ops_per_s",
                "dram_bw_bytes_per_s",
            ):
                result[f"/per_op/{ordinal}/{field}"] = timing
            ordinal += 1
    return result
