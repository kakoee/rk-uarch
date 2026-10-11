"""Independent standalone acceptance: literals fixed before producer implementation."""

import importlib
import json
from pathlib import Path
from typing import Literal

import pytest
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.prepared import PreparedBundle
from uarch_contract.request import RequestIntent

from rkuarch.engines.protocol import EngineResult
from rkuarch.workload.prepared import execute_prepared_point, physical_assumptions

FIX = Path(__file__).resolve().parents[2] / "contract/tests/fixtures/u2/independent-bundle.json"


def inputs(**updates: object) -> tuple[RequestIntent, HardwareSpec]:
    b = json.loads(FIX.read_text())
    i = b["intent"]
    i["assumptions_hash"] = physical_assumptions().assumptions_hash
    i.update(updates)
    return RequestIntent.model_validate(i), HardwareSpec.model_validate(b["hardware_spec"])


def prepare(
    i: RequestIntent,
    hw: HardwareSpec,
    *,
    rank_index: int = 0,
    embedding_hits: tuple[tuple[int, ...], ...] | None = None,
    synthetic_assignment: bool = False,
    attention_mask: Literal["full_square", "causal"] = "full_square",
    lm_head: Literal["all", "last"] = "all",
    fused_attention: bool = True,
) -> PreparedBundle:
    from rkuarch.workload.prepare import prepare as prepare_bundle

    return prepare_bundle(
        i,
        hw,
        rank_index=rank_index,
        embedding_hits=embedding_hits,
        synthetic_assignment=synthetic_assignment,
        attention_mask=attention_mask,
        lm_head=lm_head,
        fused_attention=fused_attention,
    )


def run(b: PreparedBundle, index: int = 0) -> EngineResult:
    return execute_prepared_point(
        b, b.points[index].payload_hash, assumptions=physical_assumptions()
    )[1]


def test_standalone_literal_decoder_and_capacity() -> None:
    i, hw = inputs()
    b = prepare(i, hw)
    r = run(b)
    assert r.counts.model_dump() == dict(
        matrix_ops=1184.0, vector_ops=572.0, memory_read_bytes=1296.0, memory_write_bytes=288.0
    )
    assert r.duration_ps == 1892000.0
    assert r.u_c0_duration_ps == 1584000.0
    cap = importlib.import_module("rkuarch.workload.characterize").capacity_summary(b, b.points[0])
    assert cap.weight_bytes == 744  # 372 bf16 parameters, untied
    assert cap.kv_bytes == 512  # 2 layers * K,V * 1 head * D2 * 32 page tokens * 2 bytes
    assert cap.total_peak_bytes is None
    assert "activation" in " ".join(cap.warnings).lower()


def test_selected_rank_and_explicit_assignment() -> None:
    i, hw = inputs(tp=2)
    with pytest.raises(ValueError, match="embedding|assignment"):
        prepare(i, hw)
    b = prepare(i, hw, synthetic_assignment=True, rank_index=1)
    assert b.rank.kind == "balanced_tp_selected_rank"
    assert b.rank.equivalent_ranks == (1,)
    assert all(p.embedding_hits == (1, 0) for p in b.points)
    assert run(b).per_op[0].counts.memory_read_bytes == 0
    explicit = prepare(i, hw, rank_index=1, embedding_hits=((1, 0), (1, 0)))
    assert explicit.points[0].hit_source == "provided_counts"
    assert b.points[0].hit_source == "synthetic_balanced_assignment"
    assert b.bundle_hash != explicit.bundle_hash
    with pytest.raises(ValueError, match="conservation"):
        prepare(i, hw, embedding_hits=((1, 1), (1, 1)))


def test_capacity_refusal_and_warning() -> None:
    i, hw = inputs()
    raw = hw.model_dump(mode="json")
    raw["memory"]["dram"]["capacity_bytes"]["value"] = 743
    small = HardwareSpec.model_validate(raw)
    with pytest.raises(ValueError, match="WeightCapacity"):
        prepare(i.model_copy(update={"hardware_spec_hash": spec_hash(small)}), small)
    raw["memory"]["dram"]["capacity_bytes"]["value"] = 1000
    small = HardwareSpec.model_validate(raw)
    b = prepare(i.model_copy(update={"hardware_spec_hash": spec_hash(small)}), small)
    c = importlib.import_module("rkuarch.workload.characterize").capacity_summary(b, b.points[0])
    assert any("KV" in w for w in c.warnings)


def test_moe_tied_residency_and_activity_once() -> None:
    i, hw = inputs()
    raw = i.model_dump(mode="json")
    # common148 (tied), router24, FFN192 per expert: total748, active556.
    raw["model"].update(total_params=748, active_params=556, n_experts=3, experts_per_token=2)
    raw["model_shape"].update(tie_embeddings=True, expert_d_ff=8)
    b = prepare(RequestIntent.model_validate(raw), hw)
    c = importlib.import_module("rkuarch.workload.characterize").capacity_summary(b, b.points[0])
    assert c.weight_bytes == 1496
    assert run(b).counts.matrix_ops == 1568
    assert run(b).counts.vector_ops == 668
    assert any("MoE" in s for s in b.points[0].graph.omissions)


def test_modes_layers_and_cold_identity() -> None:
    i, hw = inputs()
    a = prepare(i, hw)
    b = prepare(i.model_copy(update={"analytic_mode": "aggregate"}), hw)
    assert run(a).counts == run(b).counts
    assert run(b).duration_ps == 1584000
    cold = prepare(i.model_copy(update={"initial_state": "cold"}), hw)
    assert run(cold).duration_ps == run(a).duration_ps
    assert cold.bundle_hash != a.bundle_hash
    detail = i.uarch_fidelity.model_copy(update={"layer_reuse": False})
    expanded = prepare(i.model_copy(update={"uarch_fidelity": detail}), hw)
    assert [g.repeat for g in expanded.points[0].graph.groups] == [1, 1, 1, 1]
    assert run(expanded).counts == run(a).counts


def test_prefill_attention_and_head_literals() -> None:
    i, hw = inputs()
    raw = i.model_dump(mode="json")
    raw["grid"]["prefill"]["L"] = [3]
    i = RequestIntent.model_validate(raw)
    full = prepare(i, hw)
    causal = prepare(i, hw, attention_mask="causal")
    last = prepare(i, hw, lm_head="last")
    unfused = prepare(i, hw, fused_attention=False)
    # Across 2 layers: pairs 18 vs12 => 96 matrix and60 vector difference.
    assert run(full, 1).counts.matrix_ops - run(causal, 1).counts.matrix_ops == 96
    full_vector = run(full, 1).counts.vector_ops
    causal_vector = run(causal, 1).counts.vector_ops
    assert full_vector is not None and causal_vector is not None
    assert full_vector - causal_vector == 60
    assert run(full, 1).counts.memory_read_bytes == run(causal, 1).counts.memory_read_bytes
    assert run(full, 1).counts.matrix_ops - run(last, 1).counts.matrix_ops == 128
    assert run(full, 1).counts.matrix_ops == run(unfused, 1).counts.matrix_ops
    assert run(full, 1).counts.vector_ops == run(unfused, 1).counts.vector_ops
    # Two intermediates each written+read: 18*2 bytes*2 intermediates*2 layers.
    assert run(unfused, 1).counts.memory_read_bytes - run(full, 1).counts.memory_read_bytes == 144
    unfused_writes = run(unfused, 1).counts.memory_write_bytes
    full_writes = run(full, 1).counts.memory_write_bytes
    assert unfused_writes is not None and full_writes is not None
    assert unfused_writes - full_writes == 144


def test_authoritative_replay_never_reprepares(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    i, hw = inputs()
    b = prepare(i, hw, fused_attention=False, attention_mask="causal", lm_head="last")
    p = tmp_path / "prepared.json"
    p.write_text(b.model_dump_json())
    mod = importlib.import_module("rkuarch.workload.prepare")
    monkeypatch.setattr(mod, "prepare", lambda *a, **kw: pytest.fail("producer called"))
    from rkuarch.workload.prepared import load_prepared_input

    loaded = load_prepared_input(p)
    assert loaded == b
    assert run(loaded) == run(b)


def test_imported_unfused_missing_cache_dependency_refuses() -> None:
    i, hw = inputs()
    b = prepare(i, hw, fused_attention=False).model_dump(mode="json")
    p = b["points"][0]
    g = next(g for g in p["graph"]["groups"] if g["kind"] == "decoder")
    op = next(o for o in g["ops"] if o["spec"]["operator"] == "qk_score")
    op["depends_on"] = []
    p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    from rkuarch.workload.prepared import validate_execution_bundle

    with pytest.raises(ValueError, match="depend|correspondence"):
        validate_execution_bundle(b)


def reseal(raw: dict[str, object]) -> dict[str, object]:
    points = raw["points"]
    assert isinstance(points, list)
    for p in points:
        assert isinstance(p, dict)
        p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    raw["intent_hash"] = content_hash(raw["intent"])
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    return raw


@pytest.mark.parametrize(
    "mutation",
    ["replication", "paging", "dimensions", "padding", "equivalence", "group_dependency"],
)
def test_imported_physical_metadata_cannot_be_rehashed_away(mutation: str) -> None:
    from rkuarch.workload.prepared import validate_execution_bundle

    i, hw = inputs(tp=2)
    b = prepare(i, hw, synthetic_assignment=True).model_dump(mode="json")
    p = b["points"][0]
    g = p["graph"]["groups"][1]
    by = {o["spec"]["operator"]: o for o in g["ops"]}
    if mutation == "replication":
        by["k_projection"]["replication"] = []
    elif mutation == "paging":
        by["attention_fused"]["spec"]["operands"]["K"].update(
            layout="contiguous", block_size_tokens=None
        )
    elif mutation == "dimensions":
        by["ffn_up"]["spec"]["dimensions"]["unused"] = 3
    elif mutation == "padding":
        by["ffn_up"]["padding"] = [dict(dimension="N", logical=1, physical=4)]
    elif mutation == "equivalence":
        # All hits equal over every point: claiming fewer equivalent ranks is false.
        for point in b["points"]:
            point["query"].update(batch=2, total_context_tokens=34) if point["query"][
                "phase"
            ] == "decode" else None
        # Independent equal-hit control is constructed separately below.
        i2 = inputs()[0].model_dump(mode="json")
        i2["tp"] = 2
        i2["grid"]["decode"]["batch"] = [2]
        i2["grid"]["prefill"]["n"] = [2]
        b = prepare(RequestIntent.model_validate(i2), hw, synthetic_assignment=True).model_dump(
            mode="json"
        )
        b["rank"].update(kind="balanced_tp_selected_rank", equivalent_ranks=[0])
    else:
        g["depends_on"] = []
    with pytest.raises(
        ValueError, match="InvalidPreparedGraph|UnsupportedRankScope|KvLayoutMismatch"
    ):
        validate_execution_bundle(reseal(b))


def test_vocab_padding_and_kv_replication_execute_physical_extents() -> None:
    i, hw = inputs(tp=2)
    raw = i.model_dump(mode="json")
    raw["model_shape"]["vocab_size"] = 7
    raw["model"].update(total_params=364, active_params=364)
    b = prepare(RequestIntent.model_validate(raw), hw, synthetic_assignment=True, rank_index=1)
    embed = b.points[0].graph.groups[0].ops[0]
    assert embed.spec.dimensions["V"] == 4
    assert [(p.dimension, p.logical, p.physical) for p in embed.padding] == [("V", 3, 4)]
    assert run(b).counts.matrix_ops > 0


def test_characterize_captures_scopes_and_unknown_errors() -> None:
    i, hw = inputs()
    b = prepare(i, hw)
    report = importlib.import_module("rkuarch.workload.characterize").characterize(b)
    assert report["prepared_bundle_hash"] == b.bundle_hash
    assert report["results"][0]["counts"]["matrix_ops"] == 1184
    assert all(o["scope"]["op_class"] for r in report["results"] for o in r["per_op"])
    assert report["capacity"][0]["total_peak_bytes"] is None
    err = importlib.import_module("rkuarch.workload.deviations").unmeasured_errors()
    assert err.cold_vs_steady.n_samples == 0 and err.cold_vs_steady.max_rel is None


def test_h2_fp8_named_model_preparation() -> None:
    import yaml
    from uarch_contract.precision import Precision, PrecisionFormat

    root = Path(__file__).resolve().parents[2]
    hw = HardwareSpec.model_validate(
        yaml.safe_load((root / "hw/designs/npu-m256.yaml").read_text())
    )
    identity = importlib.import_module("rkuarch.workload.identity")
    model, shape = identity.load_model_shape(
        root / "contract/fixtures/model_shapes/llama-3.1-70b.json"
    )
    i, _ = inputs()
    raw = i.model_dump(mode="json")
    raw.update(
        model=model.model_dump(),
        model_shape=shape.model_dump(),
        hardware_spec_hash=spec_hash(hw),
        component_id="npu-m256",
        tp=8,
        precision=Precision(compute=PrecisionFormat.FP8, kv_cache=PrecisionFormat.FP8).model_dump(),
    )
    if hw.shared_sram is not None:
        raw["uarch_fidelity"]["shared_sram"] = "unrepresented"
    else:
        raw["uarch_fidelity"].pop("shared_sram", None)
    b = prepare(RequestIntent.model_validate(raw), hw, synthetic_assignment=True)
    r = run(b)
    assert len(r.per_op) == 17
    assert all(o.scope.op_class for o in r.per_op)
    assert r.counts.matrix_ops > 0


@pytest.mark.parametrize("ratio", [0.5, 1.0, 1.5, 2.0])
def test_frequency_counts_invariant_and_timing_monotone(ratio: float) -> None:
    i, hw = inputs()
    raw = i.model_dump(mode="json")
    raw["grid"]["frequency_ratio"] = [ratio]
    varied = run(prepare(RequestIntent.model_validate(raw), hw))
    base = run(prepare(i, hw))
    assert varied.counts == base.counts
    for a, b in zip(varied.per_op, base.per_op, strict=True):
        assert a.compute_time_ps == pytest.approx(b.compute_time_ps / ratio)
        assert a.memory_time_ps == b.memory_time_ps
    assert (
        (varied.duration_ps >= base.duration_ps)
        if ratio < 1
        else (varied.duration_ps <= base.duration_ps)
    )


def test_property_embedding_conservation() -> None:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    @settings(max_examples=12, derandomize=True, database=None, deadline=None)
    @given(st.integers(min_value=1, max_value=9), st.integers(min_value=0, max_value=1))
    def check(tokens: int, rank: int) -> None:
        i, hw = inputs(tp=2)
        raw = i.model_dump(mode="json")
        raw["grid"]["decode"]["batch"] = [tokens]
        raw["grid"]["prefill"]["n"] = [tokens]
        b = prepare(
            RequestIntent.model_validate(raw), hw, synthetic_assignment=True, rank_index=rank
        )
        assert all(sum(p.embedding_hits) == tokens for p in b.points)
        assert run(b).per_op[0].counts.memory_read_bytes == b.points[0].embedding_hits[rank] * 8

    check()


def test_imported_padding_must_connect_physical_ffn_extents() -> None:
    from rkuarch.workload.prepared import validate_execution_bundle

    i, hw = inputs()
    raw = prepare(i, hw).model_dump(mode="json")
    for point in raw["points"]:
        for group in point["graph"]["groups"]:
            for op in group["ops"]:
                if op["spec"]["operator"] == "ffn_up":
                    op["spec"]["dimensions"]["N"] = 10
                    op["padding"] = [dict(dimension="N", logical=8, physical=10)]
    with pytest.raises(ValueError, match="correspondence"):
        validate_execution_bundle(reseal(raw))
    # A fully connected captured padded FFN remains authoritative; producer is not consulted.
    for point in raw["points"]:
        for group in point["graph"]["groups"]:
            for op in group["ops"]:
                name = op["spec"]["operator"]
                axis = {"ffn_gate": "N", "activation": "D", "ffn_down": "K"}.get(name)
                if axis:
                    op["spec"]["dimensions"][axis] = 10
                    op["padding"] = [dict(dimension=axis, logical=8, physical=10)]
    b = validate_execution_bundle(reseal(raw))
    assert run(b).counts.matrix_ops == 1280
    assert run(b).counts.vector_ops == 596


def test_subprocess_capture_uses_transport_not_parent_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rkuarch.engines.analytic import core
    from rkuarch.table.build import capture

    i, hw = inputs()
    bundle = prepare(i, hw)
    monkeypatch.setattr(core, "run_analytic", lambda *a: pytest.fail("parent engine executed"))
    c = capture(bundle, assumptions=physical_assumptions(), subprocess_engine=True)
    assert c.results[0].counts.matrix_ops == 1184


def test_attribution_source_capture_is_complete() -> None:
    from rkuarch.table.build import capture, source_scopes, table_recipes

    i, hw = inputs()
    c = capture(prepare(i, hw), assumptions=physical_assumptions())
    recipes, sources = table_recipes(c)
    scopes = source_scopes(c, family="test-only")
    for ri, result in enumerate(c.results):
        for name in ("compute", "memory", "noc", "sync", "overhead"):
            pointer = "/attribution_ps/" + name
            assert any(
                s.artifact_hash == result.result_hash and s.recipe.metric_path == pointer
                for s in sources
            )
            assert any(r.metric_path == f"/rows/{ri}/attribution_s/{name}" for r in recipes)
            assert scopes[(result.result_hash, pointer)]


def test_empty_logical_vocab_shard_refuses_instead_of_fabricating_padding() -> None:
    i, hw = inputs(tp=2)
    raw = i.model_dump(mode="json")
    raw["model_shape"]["vocab_size"] = 1
    raw["model"].update(total_params=316, active_params=316)
    with pytest.raises(ValueError, match="empty logical vocabulary"):
        prepare(RequestIntent.model_validate(raw), hw, synthetic_assignment=True, rank_index=1)


def test_h2_mixed_compute_and_kv_storage_preserve_roles() -> None:
    import yaml
    from uarch_contract.precision import Precision, PrecisionFormat

    root = Path(__file__).resolve().parents[2]
    hw = HardwareSpec.model_validate(
        yaml.safe_load((root / "hw/designs/npu-m256.yaml").read_text())
    )
    i, _ = inputs()
    raw = i.model_dump(mode="json")
    raw.update(
        hardware_spec_hash=spec_hash(hw),
        component_id=hw.id,
        precision=Precision(
            compute=PrecisionFormat.BF16, kv_cache=PrecisionFormat.FP8
        ).model_dump(),
    )
    if hw.shared_sram is not None:
        raw["uarch_fidelity"]["shared_sram"] = "unrepresented"
    b = prepare(RequestIntent.model_validate(raw), hw)
    result = run(b)
    # 136 KV read elements and8 appended write elements save one byte each; compute stays BF16.
    assert result.counts.model_dump() == dict(
        matrix_ops=1184.0, vector_ops=572.0, memory_read_bytes=1160.0, memory_write_bytes=280.0
    )
    assert "precision_conversion" in result.unrepresented
    c = importlib.import_module("rkuarch.workload.characterize").capacity_summary(b, b.points[0])
    assert c.weight_bytes == 744 and c.kv_bytes == 256
