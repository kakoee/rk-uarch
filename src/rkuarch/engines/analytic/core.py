"""Stateless physical resolved-operator rooflines. No preparation or oracle imports."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.hashing import content_hash, verify_identity
from uarch_contract.prepared import PreparedBundle, PreparedOp, validate_prepared_op
from uarch_contract.report_context import DependencySelector
from uarch_contract.table import (
    Counts,
    Diagnostics,
    OpResult,
    ReportScope,
    ReportScopePrecisionRoles,
)

from rkuarch.engines.protocol import (
    EngineIdentity,
    EngineJob,
    EngineResult,
    EngineResultAttributionPs,
    EngineResultBusyTimePs,
    validate_engine_result,
)

_IMPLEMENTATION_HASH = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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


def engine_identity() -> EngineIdentity:
    return EngineIdentity(
        name="analytic",
        version="resolved-ops/1",
        implementation_hash=_IMPLEMENTATION_HASH,
        model=ModelIdentity(
            name="physical-resolved", version="1", implementation_hash=_IMPLEMENTATION_HASH
        ),
    )


def _counts(op: PreparedOp, repeat: int, *, causal: bool) -> dict[str, int]:
    validate_prepared_op(op)
    dims, name = op.spec.dimensions, str(op.spec.operator)
    matrix = vector = 0
    if name in _PROJECTIONS:
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


def run_analytic(job: EngineJob) -> EngineResult:
    """Execute already resolved work. Bundle/spec joins are checked by the caller.

    This boundary validates its self-contained job and never constructs, re-shards or
    changes an operator. Unit tests may supply isolated operators without a full model.
    """
    job = EngineJob.model_validate(job)
    verify_identity(job, "job_hash")
    verify_identity(job.point, "payload_hash")
    if job.point_hash != job.point.payload_hash:
        raise ValueError("EngineJobMismatch: point_hash")
    if job.engine != engine_identity():
        raise ValueError("EngineIdentityMismatch: analytic implementation")
    detail = job.fidelity_detail
    if (
        detail.compute != 0
        or detail.noc != 0
        or detail.dram != 0
        or detail.shared_sram not in (None, "unrepresented")
        or detail.sync != "exact"
    ):
        raise ValueError("UnsupportedFidelity: analytic stateless roofline")
    hardware = job.hardware
    per_op = []
    for group in job.point.graph.groups:
        for op in group.ops:
            counts = Counts(
                **_counts(op, group.repeat, causal=job.point.graph.attention_mask == "causal")
            )
            assert counts.vector_ops is not None and counts.memory_write_bytes is not None
            compute_s = math.fsum(
                (
                    counts.matrix_ops / hardware.matrix_peak_ops_per_s,
                    counts.vector_ops / hardware.vector_peak_ops_per_s,
                )
            )
            memory_bytes = counts.memory_read_bytes + counts.memory_write_bytes
            memory_s = memory_bytes / hardware.dram_bw_bytes_per_s
            compute_ps, memory_ps = compute_s * 1e12, memory_s * 1e12
            duration_ps = max(compute_ps, memory_ps)
            intensity = counts.matrix_ops / memory_bytes if memory_bytes else None
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
                    counts=counts,
                    compute_time_ps=compute_ps,
                    memory_time_ps=memory_ps,
                    duration_ps=duration_ps,
                    bound="compute" if compute_ps >= memory_ps else "memory",
                    operational_intensity_ops_per_byte=intensity,
                    achieved_ops_per_s=(
                        counts.matrix_ops / max(compute_s, memory_s) if duration_ps else None
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
        for v in o.spec.operands.values()
    ):
        unrepresented.append("precision_conversion")
    result = EngineResult(
        protocol="uarch-engine/1",
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
    return validate_engine_result(result, job)


def metric_contributors(
    job: EngineJob, bundle: object
) -> dict[str, tuple[DependencySelector, ...]]:
    """Capture source selectors from the operands/formulas consumed by this computation.

    These are required computation inputs, not evidence or display permissions. B attaches
    model evidence and preserves independent source-recipe scopes after verifying these.
    """
    b = PreparedBundle.model_validate(bundle)
    matches = [i for i, p in enumerate(b.points) if p == job.point]
    if len(matches) != 1 or b.bundle_hash != job.bundle_hash:
        raise ValueError("EngineJobMismatch: contributor point/bundle")
    index = matches[0]
    base = f"/points/{index}/graph"
    common = [
        DependencySelector(
            kind="prepared_content",
            artifact_hash=b.bundle_hash,
            json_pointer=base + "/attention_mask",
        ),
        DependencySelector(
            kind="model_assumption", artifact_hash=job.assumptions_hash, json_pointer="/algorithms"
        ),
    ]
    for gi, group in enumerate(job.point.graph.groups):
        prefix = base + f"/groups/{gi}"
        common.append(
            DependencySelector(
                kind="prepared_content",
                artifact_hash=b.bundle_hash,
                json_pointer=prefix + "/repeat",
            )
        )
        for oi, _op in enumerate(group.ops):
            for field in ("spec", "operand_access", "embedding_local_tokens", "work_repeat"):
                common.append(
                    DependencySelector(
                        kind="prepared_content",
                        artifact_hash=b.bundle_hash,
                        json_pointer=prefix + f"/ops/{oi}/{field}",
                    )
                )
    timing = list(common)
    for path in (
        "/clock_domains/core/freq_hz",
        "/cores/grid/rows",
        "/cores/grid/cols",
        f"/cores/core_type/matrix_engine/macs_per_cycle/{job.precision.compute}",
        "/cores/core_type/vector_engine/ops_per_cycle",
        "/memory/dram/bw_bytes_per_s",
    ):
        timing.append(
            DependencySelector(
                kind="hardware_leaf", artifact_hash=b.intent.hardware_spec_hash, json_pointer=path
            )
        )
    timing.append(
        DependencySelector(
            kind="prepared_content",
            artifact_hash=b.bundle_hash,
            json_pointer=f"/points/{index}/frequency_ratio",
        )
    )
    result = {"/counts/" + name: tuple(common) for name in Counts.model_fields}
    result["/duration_ps"] = result["/u_c0_duration_ps"] = tuple(timing)
    ordinal = 0
    for gi, group in enumerate(job.point.graph.groups):
        for oi, _op in enumerate(group.ops):
            prefix = base + f"/groups/{gi}"
            local = tuple(
                s
                for s in common
                if (
                    s.kind == "model_assumption"
                    or s.json_pointer == base + "/attention_mask"
                    or s.json_pointer == prefix + "/repeat"
                    or s.json_pointer.startswith(prefix + f"/ops/{oi}/")
                )
            )
            local_timing = local + tuple(s for s in timing if s not in common)
            for name in Counts.model_fields:
                result[f"/per_op/{ordinal}/counts/{name}"] = local
            result[f"/per_op/{ordinal}/instances"] = local
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
                result[f"/per_op/{ordinal}/{field}"] = local_timing
            ordinal += 1
    return result
