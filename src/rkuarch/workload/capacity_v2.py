"""Known allocation checks, never a claim about total activation peak or accuracy."""

from __future__ import annotations

import math
from typing import NamedTuple

from uarch_contract.rotary_v2 import PreparedBundleV2, PreparedPointV2

from rkuarch.hw.derive import FORMAT_BYTES


class CapacitySummary(NamedTuple):
    weight_bytes: int
    kv_bytes: int
    coefficient_bytes: int
    total_peak_bytes: None
    warnings: tuple[str, ...]


def capacity_summary(bundle: PreparedBundleV2, point: PreparedPointV2) -> CapacitySummary:
    """Sum unique weights (all experts, replicated router, tied sharing) and paged KV.

    This consumes validated captured extents. Known weights must fit. KV plus weights
    overflowing is a warning; no activation lifetime model exists in this version.
    """
    if point not in bundle.points:
        raise ValueError("PointMismatch: capacity")
    weights = 0
    for group in point.graph.groups:
        for op in group.ops:
            if "W" not in op.spec.operands:
                continue
            if str(op.spec.operator) == "lm_head" and bundle.intent.model_shape.tie_embeddings:
                continue
            operand = op.spec.operands["W"]
            size = math.prod(op.spec.dimensions[a] for a in operand.dimensions)
            weights += (
                math.ceil(size * FORMAT_BYTES[operand.dtype]) * op.weight_copies * group.repeat
            )
    m = bundle.intent.model
    weights += (
        math.ceil(m.d_model * m.n_experts * FORMAT_BYTES[bundle.intent.precision.compute])
        * m.n_layers
    )
    q = point.query
    batch = q.batch if q.phase == "decode" else q.n_prompts
    context = q.total_context_tokens // q.batch if q.phase == "decode" else q.prompt_tokens
    block = bundle.intent.kv_layout.block_size_tokens
    # KV allocation includes physical head width/extents captured by each decoder group.
    kv_bytes = 0
    for group in point.graph.groups:
        if group.kind != "decoder":
            continue
        append = next(o for o in group.ops if str(o.spec.operator) == "kv_write")
        dims = append.spec.dimensions
        for key in ("K_cache", "V_cache"):
            kv_bytes += (
                math.ceil(
                    batch
                    * dims["Hkv"]
                    * dims["D"]
                    * ((context + block - 1) // block)
                    * block
                    * FORMAT_BYTES[append.spec.operands[key].dtype]
                )
                * group.repeat
            )
    capacity = bundle.hardware_spec.memory.dram.capacity_bytes.value
    if weights > capacity:
        raise ValueError(f"WeightCapacityExceeded: {weights} > {capacity}")
    warnings = ["Total activation peak is unmodelled; HBM/SRAM peak remains unknown."]
    if weights + kv_bytes > capacity:
        warnings.append(
            f"KV capacity exceeded: known weights {weights} + paged KV {kv_bytes} > {capacity}."
        )
    coefficient_bytes = (
        8 * bundle.coefficients.position_count * (bundle.coefficients.rotary_dim // 2)
    )
    if weights + kv_bytes + coefficient_bytes > capacity:
        warnings.append("Known weight/KV/coefficient allocation exceeds DRAM capacity.")
    return CapacitySummary(weights, kv_bytes, coefficient_bytes, None, tuple(warnings))
