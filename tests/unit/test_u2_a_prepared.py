"""Authoritative captured replay and pre-execution refusal tests."""

import copy
import importlib
import json
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.prepared import PreparedBundle

ROOT = Path(__file__).resolve().parents[2]


def prepared():
    return importlib.import_module("rkuarch.workload.prepared")


def captured():
    b = json.loads((ROOT / "contract/tests/fixtures/u2/independent-bundle.json").read_text())
    assumptions = prepared().physical_assumptions()
    b["intent"]["assumptions_hash"] = assumptions.assumptions_hash
    return seal(b), assumptions


def seal(b):
    for p in b["points"]:
        p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    b["intent_hash"] = content_hash(b["intent"])
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    return PreparedBundle.model_validate(b)


def test_captured_execution_preserves_input_and_does_not_prepare(monkeypatch):
    b, a = captured()
    before = b.model_dump_json()
    import builtins

    original = builtins.__import__

    def guard(name, *args, **kwargs):
        assert name not in ("rkuarch.workload.prepare", "rk", "rkuarch.mapping")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guard)
    job, result = prepared().execute_prepared_point(b, b.points[0].payload_hash, assumptions=a)
    assert job.point == b.points[0] and job.producer == b.producer
    assert result.counts.matrix_ops == 1184
    assert before == b.model_dump_json()
    assert (
        result == prepared().execute_prepared_point(b, b.points[0].payload_hash, assumptions=a)[1]
    )


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("width", "InvalidPreparedGraph"),
        ("missing", "InvalidPreparedGraph"),
        ("wrong_dtype", "UnsupportedPrecision"),
        ("mapping", "UnsupportedMappingScope"),
        ("assumptions", "AssumptionMismatch"),
    ],
)
def test_rehashed_invalid_inputs_refuse_before_core(monkeypatch, mutation, match):
    b, a = captured()
    data = b.model_dump(mode="json")
    if mutation == "width":
        data["points"][0]["graph"]["groups"][1]["ops"][1]["spec"]["dimensions"]["N"] = 3
    elif mutation == "missing":
        data["points"][0]["graph"]["groups"][0]["ops"] = [
            copy.deepcopy(data["points"][0]["graph"]["groups"][2]["ops"][0])
        ]
    elif mutation == "wrong_dtype":
        data["points"][0]["graph"]["groups"][1]["ops"][1]["spec"]["operands"]["W"]["dtype"] = "fp8"
    elif mutation == "mapping":
        data["intent"]["mapping_policy"] = "detailed-policy@1"
    else:
        a = a.model_copy(update={"algorithms": {"traffic": "retained-intermediates/1"}})
        a = a.model_copy(
            update={"assumptions_hash": content_hash(a, exclude=("assumptions_hash",))}
        )
        data["intent"]["assumptions_hash"] = a.assumptions_hash
    b = seal(data)
    from rkuarch.engines.analytic import core

    monkeypatch.setattr(
        core, "run_analytic", lambda *args: pytest.fail("engine called on bad input")
    )
    with pytest.raises(ValueError, match=match):
        prepared().execute_prepared_point(b, b.points[0].payload_hash, assumptions=a)


def test_strict_import_and_relocation(tmp_path):
    b, a = captured()
    path = tmp_path / "capture.json"
    path.write_text(b.model_dump_json())
    assert prepared().load_prepared_input(path) == b
    moved = tmp_path / "moved.json"
    path.rename(moved)
    assert prepared().load_prepared_input(moved) == b
    moved.write_text('{"format":"uarch-prepared/1","format":"uarch-prepared/1"}')
    with pytest.raises(ValueError, match="DuplicateJsonKey"):
        prepared().load_prepared_input(moved)


def test_adapter_exact_selection_and_a_f12_before_core(monkeypatch):
    adapter = importlib.import_module("contract.tests.u2_prepared_adapter")
    b, a = captured()
    selector = dict(
        model=b.intent.model,
        model_shape=b.intent.model_shape,
        query=b.points[0].query,
        precision=b.intent.precision,
        tp=b.intent.tp,
        component_id=b.intent.component_id,
        assumptions=a,
    )
    job, result = adapter.evaluate_captured(b, **selector)
    assert job.point == b.points[0] and result.counts.matrix_ops == 1184
    with pytest.raises(ValueError, match="CapturedSelectionMismatch"):
        adapter.evaluate_captured(b, **dict(selector, component_id="other"))
    data = b.model_dump(mode="json")
    data["intent"]["tp"] = 2  # A-F12 must run before any attempted comparison execution.
    data["rank"]["tp"] = 2
    b2 = seal(data)
    monkeypatch.setattr(
        prepared(),
        "execute_prepared_point",
        lambda *args, **kwargs: pytest.fail("A-F12 ran too late"),
    )
    with pytest.raises(ValueError, match="ProjectionScope"):
        adapter.evaluate_captured(b2, **dict(selector, tp=2))


def selected_rank(rank):
    b, a = captured()
    data = b.model_dump(mode="json")
    data["intent"]["tp"] = 2
    data["rank"].update(
        tp=2, rank_index=rank, equivalent_ranks=[rank], kind="balanced_tp_selected_rank"
    )
    for point in data["points"]:
        point["embedding_hits"] = [1, 0]
        point["hit_source"] = "provided_counts"
        for group in point["graph"]["groups"]:
            for op in group["ops"]:
                name, dims = op["spec"]["operator"], op["spec"]["dimensions"]
                if name == "embedding":
                    dims["V"] = 4
                    op["embedding_local_tokens"] = 1 - rank
                elif name == "lm_head":
                    dims["N"] = 4
                elif name in ("q_projection", "ffn_up", "ffn_gate"):
                    dims["N"] //= 2
                elif name in ("output_projection", "ffn_down"):
                    dims["K"] //= 2
                elif name == "activation":
                    dims["D"] //= 2
                elif name == "attention_fused":
                    dims["Hq"] = 1
                if name in ("k_projection", "v_projection", "kv_write", "attention_fused"):
                    axis = "N" if name in ("k_projection", "v_projection") else "Hkv"
                    extent = 2 if axis == "N" else 1
                    op["replication"] = [
                        dict(dimension=axis, global_extent=extent, rank_extent=extent, replicas=2)
                    ]
    return seal(data), a


def test_d7_selected_unequal_hits_are_preserved_and_conserved():
    b0, a = selected_rank(0)
    b1, _ = selected_rank(1)
    _, r0 = prepared().execute_prepared_point(b0, b0.points[0].payload_hash, assumptions=a)
    _, r1 = prepared().execute_prepared_point(b1, b1.points[0].payload_hash, assumptions=a)
    assert r0.per_op[0].counts.memory_read_bytes == 8
    assert r1.per_op[0].counts.memory_read_bytes == 0
    assert r0.counts.memory_read_bytes - r1.counts.memory_read_bytes == 8
    assert r0.counts.matrix_ops == r1.counts.matrix_ops
    assert r0.per_op[0].counts.memory_write_bytes == r1.per_op[0].counts.memory_write_bytes == 8
    bad = b0.model_dump(mode="json")
    bad["points"][0]["embedding_hits"] = [1, 1]
    with pytest.raises(ValueError, match="UnsupportedRankScope"):
        prepared().execute_prepared_point(seal(bad), b0.points[0].payload_hash, assumptions=a)
