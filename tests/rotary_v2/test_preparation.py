"""Synthetic explicit coefficients and literal counts across producer variants."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, spec_hash
from uarch_contract.rotary_v2 import RequestIntentV3, RotaryCoefficients

from rkuarch.engines.analytic.dispatch import execute
from rkuarch.engines.analytic.rotary_v2 import engine_identity
from rkuarch.table.capture_v2 import capture, replay
from rkuarch.workload.capacity_v2 import capacity_summary
from rkuarch.workload.prepared_v2 import physical_assumptions, validate_execution_bundle
from rkuarch.workload.producer_v2 import prepare

from .test_boundary import CASES, active_bundle


def inputs(dtype="bf16", r=4, tp=1, kv_heads=1, reuse=True, context=17):
    b = CASES["examples"]()["bundle"]
    intent, hw, coeff = b["intent"], b["hardware_spec"], b["coefficients"]
    # Independently derived global parameter totals, never production implied_params.
    d, heads, parameters = (8, 2, 936) if tp == 1 else (16, 4, 2384 if kv_heads == 1 else 2640)
    intent["model"].update(
        name="synthetic-explicit-rope",
        d_model=d,
        n_heads=heads,
        kv_heads=kv_heads,
        total_params=parameters,
        active_params=parameters,
    )
    intent["tp"] = tp
    intent["precision"] = dict(compute=dtype, kv_cache=dtype)
    intent["uarch_fidelity"]["layer_reuse"] = reuse
    intent["grid"]["decode"] = dict(batch=[1], context_per_seq=[context])
    intent["grid"]["prefill"] = dict(n=[2], L=[3])
    intent["assumptions_hash"] = physical_assumptions().assumptions_hash
    coeff.update(
        position_count=context,
        rotary_dim=r,
        cos_bits=[["3f800000"] * (r // 2) for _ in range(context)],
        sin_bits=[["00000000"] * (r // 2) for _ in range(context)],
    )
    CASES["seal"](coeff, "coefficients_hash")
    intent["position_encoding"].update(rotary_dim=r, coefficients_hash=coeff["coefficients_hash"])
    if dtype != "bf16":
        hw["formats"][dtype] = deepcopy(hw["formats"]["bf16"])
        hw["formats"][dtype]["bytes"] = 4.0 if dtype == "fp32" else 2.0
        hw["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"][dtype] = deepcopy(
            hw["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]["bf16"]
        )
    hardware = HardwareSpec.model_validate(hw)
    intent["hardware_spec_hash"] = spec_hash(hardware)
    return (
        RequestIntentV3.model_validate(intent),
        hardware,
        RotaryCoefficients.model_validate(coeff),
    )


@pytest.mark.parametrize("dtype", ["bf16", "fp16", "fp32"])
@pytest.mark.parametrize("r", [2, 4])
@pytest.mark.parametrize("fused", [True, False])
def test_prepare_supported_counts_positions_tail(dtype, r, fused):
    intent, hw, coeff = inputs(dtype, r)
    b = prepare(intent, hw, coefficients=coeff, fused_attention=fused, attention_mask="causal")
    validate_execution_bundle(b)
    c = capture(b, assumptions=physical_assumptions())
    expected = {
        ("bf16", 2): (60, 80, 48),
        ("fp16", 2): (60, 80, 48),
        ("fp32", 2): (36, 128, 96),
        ("bf16", 4): (120, 112, 48),
        ("fp16", 4): (120, 112, 48),
        ("fp32", 4): (72, 160, 96),
    }[dtype, r]
    for point, result, factor in zip(b.points, c.results, (1, 6), strict=True):
        ropes = [o for o in result.per_op if o.scope.op_class == "rotary_embedding"]
        assert len(ropes) == 2
        assert sum(o.counts.matrix_ops for o in ropes) == 0
        got = tuple(
            sum(getattr(o.counts, field) for o in ropes)
            for field in ("vector_ops", "memory_read_bytes", "memory_write_bytes")
        )
        assert got == tuple(x * factor for x in expected)
        bindings = [o.rotary for g in point.graph.groups for o in g.ops if o.rotary]
        assert all(
            x.position_ids == (((16,),) if factor == 1 else ((0, 1, 2), (0, 1, 2)))
            for x in bindings
        )
        allocation = capacity_summary(b, point)
        assert allocation.coefficient_bytes == (136 if r == 2 else 272)
        assert allocation.total_peak_bytes is None
    assert c.bundle.intent.model.total_params == c.bundle.intent.model.active_params == 936


@pytest.mark.parametrize("rank", [0, 1])
@pytest.mark.parametrize("kv_heads", [1, 2])
def test_rank_replication_and_layer_repeat(rank, kv_heads):
    intent, hw, coeff = inputs(tp=2, kv_heads=kv_heads)
    b = prepare(intent, hw, coefficients=coeff, rank_index=rank, embedding_hits=((1, 0), (3, 3)))
    c = capture(b, assumptions=physical_assumptions())
    ropes = [o for o in c.results[0].per_op if o.scope.op_class == "rotary_embedding"]
    assert [o.counts.vector_ops for o in ropes] == [80, 40]
    assert b.rank.equivalent_ranks == (rank,)
    assert b.rank.kind == "balanced_tp_selected_rank"
    bad = b.model_dump(mode="json")
    k = next(o for o in bad["points"][0]["graph"]["groups"][1]["ops"] if o["id"] == "rope_k")
    k["replication"] = (
        [] if kv_heads == 1 else [dict(dimension="H", global_extent=1, rank_extent=1, replicas=2)]
    )
    CASES["rehash"](bad)
    with pytest.raises(ValueError, match="replication|replicated"):
        validate_execution_bundle(bad)
    intent2, _, _ = inputs(tp=2, kv_heads=kv_heads, reuse=False)
    b2 = prepare(intent2, hw, coefficients=coeff, rank_index=rank, embedding_hits=((1, 0), (3, 3)))
    c2 = capture(b2, assumptions=physical_assumptions())
    assert [r.counts for r in c.results] == [r.counts for r in c2.results]
    assert c.results[0].duration_ps == c2.results[0].duration_ps


@pytest.mark.parametrize("edge", ["qk", "softmax", "av"])
def test_unfused_bypass_refused(edge):
    intent, hw, coeff = inputs()
    b = prepare(intent, hw, coefficients=coeff, fused_attention=False)
    validate_execution_bundle(b)
    bad = b.model_dump(mode="json")
    ops = {o["id"]: o for o in bad["points"][0]["graph"]["groups"][1]["ops"]}
    if edge == "qk":
        ops["qk_score"]["depends_on"][0] = "q_projection"
    elif edge == "softmax":
        ops["softmax"]["depends_on"] = ["rope_q"]
    else:
        ops["av_application"]["depends_on"] = ["softmax"]
    CASES["rehash"](bad)
    with pytest.raises(ValueError):
        validate_execution_bundle(bad)


def test_context_and_finite_table_replacement_are_distinct_inputs():
    intent, hw, coeff = inputs(context=17)
    b = prepare(intent, hw, coefficients=coeff)
    intent2, hw2, coeff2 = inputs(context=33)
    b2 = prepare(intent2, hw2, coefficients=coeff2)
    c = capture(b, assumptions=physical_assumptions())
    c2 = capture(b2, assumptions=physical_assumptions())

    def ropes(result):
        return [o.counts for o in result.per_op if o.scope.op_class == "rotary_embedding"]

    assert ropes(c.results[0]) == ropes(c2.results[0])
    assert c.results[0].counts.memory_read_bytes != c2.results[0].counts.memory_read_bytes
    changed = b.model_dump(mode="json")
    changed["coefficients"]["cos_bits"][0][0] = "80000000"  # signed zero, finite, explicit input
    CASES["seal"](changed["coefficients"], "coefficients_hash")
    CASES["rehash"](changed)
    with pytest.raises(ValueError):
        validate_execution_bundle(changed)
    h = changed["coefficients"]["coefficients_hash"]
    changed["intent"]["position_encoding"]["coefficients_hash"] = h
    for point in changed["points"]:
        point["graph"]["kv_key_encoding"]["coefficients_hash"] = h
        for group in point["graph"]["groups"]:
            for op in group["ops"]:
                if op["rotary"]:
                    op["rotary"]["coefficients_hash"] = h
    CASES["rehash"](changed)
    different = capture(changed, assumptions=physical_assumptions())
    assert different.bundle.bundle_hash != b.bundle_hash
    assert different.results[0].counts == c.results[0].counts


def test_dispatch_and_dependency_bytes(monkeypatch):
    c = capture(active_bundle(), assumptions=physical_assumptions())
    assert execute(c.jobs[0], bundle=c.bundle, assumptions=c.assumptions) == c.results[0]
    for value in ({}, {"protocol": "uarch-engine/3"}, c.jobs[0]):
        with pytest.raises(ValueError):
            execute(value)
    original = engine_identity()
    read = Path.read_bytes

    def changed(path):
        payload = read(path)
        if path.name == "rotary_v2.py" and path.parent.name == "analytic":
            return payload + b"\n# changed implementation, same version\n"
        return payload

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="ImplementationChanged"):
        engine_identity()
    with pytest.raises(ValueError):
        replay(c.bundle, c.request, c.jobs, c.results, assumptions=c.assumptions)
    monkeypatch.undo()
    assert engine_identity() == original
    restored = replay(c.bundle, c.request, c.jobs, c.results, assumptions=c.assumptions)
    assert [canonical_json(r) for r in restored.results] == [canonical_json(r) for r in c.results]
