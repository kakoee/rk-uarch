"""Coordinator arithmetic/replay probe; run from the reviewed A checkout."""

import builtins
import json
import runpy
from copy import deepcopy
from itertools import product
from unittest.mock import patch

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, spec_hash
from uarch_contract.rotary_v2 import RequestIntentV3, RotaryCoefficients

from rkuarch.table.capture_v2 import capture, replay
from rkuarch.workload.capacity_v2 import capacity_summary
from rkuarch.workload.prepared_v2 import physical_assumptions
from rkuarch.workload.producer_v2 import prepare

cases = runpy.run_path("contract/tests/rotary_v2_cases.py")
original_import = builtins.__import__


def refuse_producer(name, *args, **kwargs):
    if name.endswith("producer_v2"):
        raise AssertionError("producer imported during replay")
    return original_import(name, *args, **kwargs)


outcomes = []
for i, (dtype, rotary_dim, tp) in enumerate(product(("fp32", "bf16", "fp16"), (2, 4), (1, 2))):
    fixture = cases["examples"]()["bundle"]
    intent, hardware, coefficients = (
        deepcopy(fixture[k]) for k in ("intent", "hardware_spec", "coefficients")
    )
    # Explicit tiny model: 136 embedding/head/final-norm parameters + 2*400 decoder parameters.
    intent["model"].update(d_model=8, total_params=936, active_params=936)
    intent["tp"] = tp
    intent["analytic_mode"] = "aggregate" if i % 2 else "per_op"
    intent["uarch_fidelity"]["layer_reuse"] = bool(i % 2)
    intent["precision"] = dict(compute=dtype, kv_cache=dtype)
    intent["grid"]["decode"] = dict(batch=[2], context_per_seq=[17])
    intent["grid"]["prefill"] = dict(n=[2], L=[3])
    intent["assumptions_hash"] = physical_assumptions().assumptions_hash
    coefficients.update(
        rotary_dim=rotary_dim,
        cos_bits=[["3f800000"] * (rotary_dim // 2) for _ in range(17)],
        sin_bits=[["00000000"] * (rotary_dim // 2) for _ in range(17)],
    )
    cases["seal"](coefficients, "coefficients_hash")
    intent["position_encoding"].update(
        rotary_dim=rotary_dim,
        coefficients_hash=coefficients["coefficients_hash"],
        pairing="split_halves" if i % 2 else "adjacent",
    )
    if dtype != "bf16":
        hardware["formats"][dtype] = deepcopy(hardware["formats"]["bf16"])
        hardware["formats"][dtype]["bytes"] = 4.0 if dtype == "fp32" else 2.0
        rates = hardware["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]
        rates[dtype] = deepcopy(rates["bf16"])
    hw = HardwareSpec.model_validate(hardware)
    intent["hardware_spec_hash"] = spec_hash(hw)
    bundle = prepare(
        RequestIntentV3.model_validate(intent),
        hw,
        coefficients=RotaryCoefficients.model_validate(coefficients),
        embedding_hits=((2,), (6,)) if tp == 1 else ((1, 1), (3, 3)),
        fused_attention=bool(i % 2),
    )
    captured = capture(bundle, assumptions=physical_assumptions())
    width = 4 if dtype == "fp32" else 2
    heads = 2 // tp + 1  # Local Q plus local K; K is replicated for tp=2.
    for point, result, tokens in zip(bundle.points, captured.results, (2, 6), strict=True):
        ops = [op for op in result.per_op if op.scope.op_class == "rotary_embedding"]
        got = tuple(
            sum(getattr(op.counts, field) for op in ops)
            for field in ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes")
        )
        expected = (
            0,
            2 * tokens * heads * rotary_dim * (3 if dtype == "fp32" else 5),
            2 * (width * tokens * heads * 4 + 8 * tokens * rotary_dim),
            2 * width * tokens * heads * 4,
        )
        assert got == expected, (dtype, rotary_dim, tp, got, expected)
        assert result.duration_ps >= result.u_c0_duration_ps
        assert capacity_summary(bundle, point).coefficient_bytes == 8 * 17 * (rotary_dim // 2)
    with (
        patch(
            "rkuarch.workload.producer_v2.prepare",
            side_effect=AssertionError("producer called during replay"),
        ),
        patch("builtins.__import__", side_effect=refuse_producer),
    ):
        restored = replay(
            bundle.model_dump(mode="json"),
            captured.request.model_dump(mode="json"),
            [j.model_dump(mode="json") for j in captured.jobs],
            [r.model_dump(mode="json") for r in captured.results],
            assumptions=captured.assumptions,
        )
    assert [canonical_json(r) for r in restored.results] == [
        canonical_json(r) for r in captured.results
    ]
    outcomes.append(dict(dtype=dtype, rotary_dim=rotary_dim, tp=tp, points=2, status="passed"))
print(json.dumps(outcomes, indent=2))
