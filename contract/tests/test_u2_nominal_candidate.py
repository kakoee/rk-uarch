"""Independent literal algebra for the isolated nominal model; no oracle expectations."""

import builtins
import copy
import importlib
import json
import socket
from pathlib import Path
from types import ModuleType
from typing import Any, NoReturn

import pytest
from uarch_contract.hashing import content_hash, verify_identity

from contract.tests.nominal_candidate import NominalInput

ZERO = "sha256:" + "0" * 64


def candidate() -> ModuleType:
    return importlib.import_module("contract.tests.nominal_candidate")


def nominal_input(**changes: Any) -> NominalInput:
    c = candidate()

    def sourced(value: float, unit: str) -> dict[str, Any]:
        return dict(
            value=value,
            unit=unit,
            kind="claim",
            provenance="stub",
            source=None,
            date=None,
            rationale=None,
        )

    execution: dict[str, Any] = dict(
        format="uarch-execution-model/1",
        execution_model_hash=ZERO,
        kind="scalar_efficiency",
        compute=sourced(0.5, "ratio"),
        memory=None,
        evidence_hashes=[],
        acceptance="accepted_input",
        assumption_note="Independent tiny literal, unvalidated model assumption.",
    )
    value = dict(
        format="uarch-nominal-input/1",
        input_hash=ZERO,
        component_binding_hash=ZERO,
        model_identity=c.candidate_identity().model_dump(),
        model=dict(
            name="literal",
            total_params=100,
            active_params=100,
            n_experts=0,
            experts_per_token=0,
            d_model=4,
            n_layers=2,
            n_heads=2,
            kv_heads=1,
        ),
        precision=dict(compute="bf16", kv_cache="bf16"),
        tp=1,
        query=dict(phase="decode", batch=2, total_context_tokens=6),
        selected_peak=sourced(1e-9, "TFLOPS"),
        bandwidth=sourced(1e-10, "TB/s"),
        execution_model=execution,
    )
    value.update(copy.deepcopy(changes))
    value["execution_model"]["execution_model_hash"] = content_hash(
        value["execution_model"], exclude=("execution_model_hash",)
    )
    value = c.NominalInput.model_validate(value).model_dump(mode="json")
    value["input_hash"] = content_hash(value, exclude=("input_hash",))
    return NominalInput.model_validate(value)


def test_decode_literal() -> None:
    result = candidate().evaluate_nominal(nominal_input())
    assert result.counts.model_dump() == dict(
        matrix_ops=592.0, memory_read_bytes=296.0, memory_write_bytes=None, vector_ops=None
    )
    assert result.duration_s == pytest.approx(2.96)
    verify_identity(result, "output_hash")


def test_prefill_literal_includes_writes_and_full_square() -> None:
    value = nominal_input(query=dict(phase="prefill", n_prompts=2, prompt_tokens=3))
    result = candidate().evaluate_nominal(value)
    assert result.counts.model_dump() == dict(
        matrix_ops=1488.0, memory_read_bytes=200.0, memory_write_bytes=96.0, vector_ops=None
    )
    assert result.duration_s == pytest.approx(2.976)
    slow = value.model_dump(mode="json")
    slow["bandwidth"]["value"] = 5e-11
    assert candidate().evaluate_nominal(nominal_input(**slow)).duration_s == pytest.approx(5.92)


@pytest.mark.parametrize(
    "change,matrix,reads,duration",
    [
        ({"query": dict(phase="decode", batch=3, total_context_tokens=6)}, 792, 296, 2.96),
        ({"query": dict(phase="decode", batch=2, total_context_tokens=8)}, 656, 328, 3.28),
        ({"precision": dict(compute="fp8", kv_cache="bf16")}, 592, 196, 1.96),
        ({"precision": dict(compute="bf16", kv_cache="fp8")}, 592, 248, 2.48),
        ({"precision": dict(compute="int4", kv_cache="int4")}, 592, 74, 1.184),
    ],
)
def test_independent_perturbations(
    change: dict[str, Any], matrix: float, reads: float, duration: float
) -> None:
    value = nominal_input(**change)
    if value.precision.compute.value.startswith("int"):
        data = value.model_dump(mode="json")
        data["selected_peak"]["unit"] = "TOPS"
        value = nominal_input(**data)
    result = candidate().evaluate_nominal(value)
    assert result.counts.matrix_ops == matrix
    assert result.counts.memory_read_bytes == reads
    assert result.duration_s == pytest.approx(duration)


def test_active_params_and_tp_once() -> None:
    data = nominal_input().model_dump(mode="json")
    data["model"].update(
        total_params=1000, active_params=120, n_experts=4, experts_per_token=1, kv_heads=2
    )
    data["tp"] = 2
    result = candidate().evaluate_nominal(nominal_input(**data))
    # Global matrix=480+192=672, bytes=240+192=432, then one /2.
    assert result.counts.matrix_ops == 336
    assert result.counts.memory_read_bytes == 216
    assert result.duration_s == pytest.approx(2.16)


def test_split_memory_and_retained_point55() -> None:
    data = nominal_input().model_dump(mode="json")
    data["execution_model"]["kind"] = "split_efficiency"
    data["execution_model"]["memory"] = dict(data["execution_model"]["compute"])
    assert candidate().evaluate_nominal(nominal_input(**data)).duration_s == pytest.approx(5.92)
    data = nominal_input(query=dict(phase="prefill", n_prompts=2, prompt_tokens=3)).model_dump(
        mode="json"
    )
    data["execution_model"]["compute"]["value"] = 0.55
    data["bandwidth"]["value"] = 1e-8
    assert candidate().evaluate_nominal(nominal_input(**data)).duration_s == pytest.approx(
        2.7054545454545456
    )


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("input_hash", ZERO, "ArtifactHashMismatch"),
        ("selected_peak", dict(value=1.0, unit="op/s", provenance="stub"), "unit"),
        ("bandwidth", dict(value=0.0, unit="TB/s", provenance="stub"), "positive"),
        ("tp", 2, "ProjectionScope"),
    ],
)
def test_refusals(field: str, value: Any, match: str) -> None:
    data = nominal_input().model_dump(mode="json")
    data[field] = value
    parsed = (
        candidate().NominalInput.model_validate(data)
        if field == "input_hash"
        else (nominal_input(**data))
    )
    with pytest.raises(ValueError, match=match):
        candidate().evaluate_nominal(parsed)


def test_identity_and_extra_expected_fields_refused() -> None:
    data = nominal_input().model_dump(mode="json")
    data["model_identity"]["implementation_hash"] = ZERO
    with pytest.raises(ValueError, match="ModelIdentityMismatch"):
        candidate().evaluate_nominal(nominal_input(**data))
    for name in ("fixture_id", "expected_counts", "duration_s"):
        with pytest.raises(ValueError):
            candidate().NominalInput.model_validate(dict(data, **{name: 0}))


def test_execution_has_no_file_network_or_prohibited_import_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = candidate()
    value = nominal_input()
    original_import = builtins.__import__

    def no_access(*args: Any, **kwargs: Any) -> NoReturn:
        raise AssertionError("candidate attempted external access")

    def restricted_import(name: str, *args: Any, **kwargs: Any) -> ModuleType:
        assert not any(word in name for word in ("vendor", "parity", "rkuarch", "operators"))
        assert name != "rk" and not name.startswith("rk.")
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", no_access)
        m.setattr(Path, "open", no_access)
        m.setattr(socket, "socket", no_access)
        m.setattr(builtins, "__import__", restricted_import)
        assert c.evaluate_nominal(value).duration_s == pytest.approx(2.96)


def test_candidate_source_identity_and_schemas() -> None:
    import hashlib

    c = candidate()
    assert c.__file__ is not None
    source = Path(c.__file__).read_bytes()
    assert (
        c.candidate_identity().implementation_hash == "sha256:" + hashlib.sha256(source).hexdigest()
    )
    expected = json.loads(Path("docs/reviews/U2-U0003-proposal/proposed.schema.json").read_text())
    for name, text in c.schemas().items():
        schema = json.loads(text)
        accepted = expected["$defs"][name.removesuffix(".schema.json")]
        assert set(schema["properties"]) == set(accepted["properties"])
        assert set(schema["required"]) == set(accepted["required"])
        assert Path("contract/tests/fixtures/u2", name).read_text() == text
