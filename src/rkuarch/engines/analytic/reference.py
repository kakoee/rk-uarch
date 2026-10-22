"""Versioned R resolver for the retained U-C0 aggregate/per-op formula.

Useful mathematical work and operand HBM bytes only. Native overhead, padding,
local materialization, latency, credits and startup are intentionally absent.
"""

from fractions import Fraction
from math import prod
from typing import Any

from uarch_contract.reference import ReferenceBundle
from uarch_contract.reference_laws import DOTS, WIDTH, expected_primitives


def resolve_reference(bundle: Any) -> Any:
    b = ReferenceBundle.model_validate(bundle.model_dump(mode="json"))
    hardware = b.hardware_spec.model_dump(mode="json")
    h = {k: Fraction(str(v["value"])) for k, v in hardware.items() if isinstance(v, dict)}
    per_op: dict[str, dict[str, Any]] = {}
    total_compute = Fraction(0)
    total_memory = Fraction(0)
    for op in b.source.ops:
        raw = op.model_dump(mode="json")
        d = op.spec.dimensions
        name = op.spec.operator
        matrix = 0
        if name in DOTS:
            matrix = 2 * d["M"] * d["K"] * d["N"]
        elif name == "attention_fused":
            pairs = (
                d["B"]
                * d["Hq"]
                * (d["S"] * (d["S"] + 1) // 2 if d["S"] == d["T"] else d["S"] * d["T"])
            )
            matrix = 4 * pairs * d["D"]
        precision = "int8" if name in DOTS and op.spec.operands["X"].dtype == "int8" else "bf16"
        compute = matrix * 10**12 / h[precision + "_peak_ops_per_s"]
        for kind, count in expected_primitives(raw, b.source.model_dump(mode="json")).items():
            multiplier = (
                h["reduction_cost_ratio"]
                if kind.startswith("reduction_")
                else h.get(kind + "_cost_ratio", 1)
            )
            compute += count * h["vector_tile_ps"] * multiplier / 1024
        payload = 0
        for key, operand in op.spec.operands.items():
            size = prod(d[axis] for axis in operand.dimensions) * WIDTH[operand.dtype]
            if name == "kv_write" and key.endswith("_cache"):
                size = d["B"] * d["S"] * d["H"] * d["D"] * 2
            payload += size * (2 if op.operand_access[key] == "read_write" else 1)
        if name == "rotary_embedding":
            payload += d["S"] * d["R"] * 4
        if name in {"kv_write", "paged_gather", "attention_fused"}:
            pages = (d["T"] + d["P"] - 1) // d["P"]
            payload += pages * 4
            compute += pages * h["scalar_op_ps"]
        memory = payload * 10**12 / h["hbm_peak_bytes_per_s"]
        per_op[op.id] = dict(
            compute_ps=compute,
            memory_ps=memory,
            duration_ps=max(compute, memory),
            operand_hbm_bytes=payload,
        )
        total_compute += compute
        total_memory += memory
    return dict(
        profile="u-c0-tpu-v5e/1",
        aggregate_ps=max(total_compute, total_memory),
        per_op_ps=sum((x["duration_ps"] for x in per_op.values()), Fraction(0)),
        ops=per_op,
        unrepresented=(
            "matrix_fill",
            "padding",
            "vmem_staging",
            "hbm_latency_and_credits",
            "vector_setup",
            "dispatch",
            "kernel_startup",
        ),
    )
