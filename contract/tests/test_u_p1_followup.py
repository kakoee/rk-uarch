"""Approved A-F1/A-F2 and B-F8 carrier regressions, written before implementation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError
from uarch_contract import table as models
from uarch_contract.hashing import legacy_table_hash

from .test_u_p1 import hardware, request_data, sv, toy


def not_run() -> dict[str, Any]:
    return dict(
        kind="not_run",
        reference_basis="rk_sim_aggregate_divided_by_tp",
        fixture_set_id=None,
        oracle_manifest_sha256=None,
        candidate_identity=None,
        n_fixtures=0,
        max_rel=None,
        comparisons=[],
    )


def comparison() -> dict[str, Any]:
    return dict(
        fixture_id="synthetic/adjusted",
        channel="matrix_ops",
        unit="op",
        actual=105.5,
        reference=100.0,
        reference_state="positive",
        raw_rel=0.055,
        signed_adjustment_rel=0.05,
        absolute_adjustment_rel=0.05,
        residual_rel=0.055 - 0.05,
        declared_deviations=[
            dict(id="a", deviation_rel=0.03, reason="Synthetic counted term A"),
            dict(id="b", deviation_rel=0.02, reason="Synthetic counted term B"),
        ],
    )


def parity(kind: str = "harness_self_test") -> dict[str, Any]:
    return not_run() | dict(
        kind=kind,
        fixture_set_id="synthetic:fixture-set-v1",
        candidate_identity="synthetic:callable-v1",
        n_fixtures=1,
        max_rel=0.055,
        comparisons=[comparison()],
        oracle_manifest_sha256="a" * 64 if kind == "workload_parity" else None,
    )


@pytest.mark.parametrize(
    "path,unit",
    [
        ("nocs[0].link_bytes_per_cycle", "byte/cycle"),
        ("cores.core_type.job_overhead_cycles", "cycle"),
        ("cores.core_type.matrix_engine.macs_per_cycle.bf16", "MAC/cycle"),
    ],
)
def test_cycle_hardware_conditions_round_trip(path: str, unit: str) -> None:
    data = toy()
    echo = sv(64, unit, kind="stipulation", provenance=None, rationale="synthetic design")
    data["provenance"]["conditional_on"] = [{"path": path, "value": echo}]
    model = models.LegacyUarchCostTable.model_validate(data)
    assert model.provenance.conditional_on[0].value.unit == unit
    assert model.provenance.conditional_on[0].value.value == 64
    assert models.LegacyUarchCostTable.model_validate_json(model.model_dump_json()) == model


@pytest.mark.parametrize("location", ["params", "row", "diagnostics", "top", "condition_extra"])
def test_cycle_exception_cannot_escape_condition_value(location: str) -> None:
    data = toy()
    data["provenance"]["conditional_on"] = [
        {
            "path": "cores.core_type.job_overhead_cycles",
            "value": sv(1, "cycle", kind="stipulation", provenance=None, rationale="synthetic"),
        }
    ]
    models.LegacyUarchCostTable.model_validate(data)  # valid echo must not mask the negative case
    if location == "params":
        data["provenance"]["params"] = [{"name": "computed", "value": sv(1, "cycle")}]
    elif location == "row":
        data["rows"][0]["duration_cycles"] = 1
    elif location == "diagnostics":
        data["rows"][0]["diagnostics"]["latency_cycles"] = 1
    elif location == "top":
        data["computed_cycles"] = 1
    else:
        data["provenance"]["conditional_on"][0]["computed_cycles"] = 1
    with pytest.raises(ValidationError):
        models.LegacyUarchCostTable.model_validate(data)


@pytest.mark.parametrize("change", ["claim", "wrong_unit"])
def test_condition_exception_preserves_stipulation_and_unit_rules(change: str) -> None:
    from uarch_contract.hardware import HardwareSpec

    data = toy()
    value = sv(1, "cycle", kind="stipulation", provenance=None, rationale="synthetic")
    condition = {"path": "cores.core_type.job_overhead_cycles", "value": value}
    data["provenance"]["conditional_on"] = [condition]
    models.LegacyUarchCostTable.model_validate(data)
    if change == "claim":
        condition["value"] = sv(1, "cycle")
    else:
        value["unit"] = "ns"
        spec = hardware()
        spec["design_status"] = "proposed"
        spec["cores"]["core_type"]["job_overhead_cycles"] = value
        with pytest.raises(ValidationError, match="job_overhead_cycles.*unit"):
            HardwareSpec.model_validate(spec)
    with pytest.raises(ValidationError):
        models.LegacyUarchCostTable.model_validate(data)


def test_table_requires_hardware_identity() -> None:
    data = toy()
    data.pop("hardware_spec_hash", None)
    with pytest.raises(ValidationError, match="hardware_spec_hash"):
        models.LegacyUarchCostTable.model_validate(data)


@pytest.mark.parametrize("value", [None, "", "a" * 64, "sha256:" + "a" * 63, "sha256:" + "G" * 64])
def test_table_refuses_malformed_hardware_identity(value: Any) -> None:
    with pytest.raises(ValidationError, match="hardware_spec_hash"):
        models.LegacyUarchCostTable.model_validate(toy() | {"hardware_spec_hash": value})


def test_hardware_identity_round_trip_schema_and_digest() -> None:
    data = toy() | {"hardware_spec_hash": request_data()["hardware_spec_hash"]}
    model = models.LegacyUarchCostTable.model_validate(data)
    assert models.LegacyUarchCostTable.model_validate_json(model.model_dump_json()) == model
    assert model.hardware_spec_hash == request_data()["hardware_spec_hash"]
    assert "hardware_spec_hash" in models.LegacyUarchCostTable.model_json_schema()["required"]
    assert legacy_table_hash(data) != legacy_table_hash(
        data | {"hardware_spec_hash": "sha256:" + "b" * 64}
    )


@pytest.mark.parametrize("kind", ["not_run", "harness_self_test", "workload_parity"])
def test_parity_kind_and_all_quantities_round_trip(kind: str) -> None:
    data = not_run() if kind == "not_run" else parity(kind)
    model = models.FlopParity.model_validate(data)
    assert model.model_dump(mode="json") == data
    assert models.FlopParity.model_validate_json(model.model_dump_json()) == model
    del data["kind"]
    with pytest.raises(ValidationError, match="kind"):
        models.FlopParity.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_rel", 0),
        ("signed_adjustment_rel", 0),
        ("absolute_adjustment_rel", 0),
        ("residual_rel", 0),
        ("unit", "byte"),
        ("channel", "made_up"),
        ("reference_state", "zero"),
        ("actual", None),
        ("reference", -1),
        ("raw_rel", "0.055"),
        ("actual", float("inf")),
    ],
)
def test_comparison_refuses_inconsistent_evidence(field: str, value: Any) -> None:
    models.FlopParity.model_validate(parity())
    data = parity()
    data["comparisons"][0][field] = value
    with pytest.raises(ValidationError):
        models.FlopParity.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("n_fixtures", 2),
        ("max_rel", 0.005),
        ("fixture_set_id", None),
        ("candidate_identity", " "),
        ("oracle_manifest_sha256", "sha256:" + "a" * 64),
    ],
)
def test_run_summary_must_match_comparisons(field: str, value: Any) -> None:
    models.FlopParity.model_validate(parity())
    data = parity() | {field: value}
    with pytest.raises(ValidationError):
        models.FlopParity.model_validate(data)


def test_actual_workload_needs_manifest_identity() -> None:
    models.FlopParity.model_validate(parity("workload_parity"))
    with pytest.raises(ValidationError, match="manifest"):
        models.FlopParity.model_validate(
            parity("workload_parity") | {"oracle_manifest_sha256": None}
        )


def test_duplicate_fixture_channel_and_deviation_ids_refused() -> None:
    models.FlopParity.model_validate(parity())
    data = parity()
    data["comparisons"].append(deepcopy(data["comparisons"][0]))
    with pytest.raises(ValidationError, match="fixture/channel"):
        models.FlopParity.model_validate(data)
    data = parity()
    data["comparisons"][0]["declared_deviations"][1]["id"] = "a"
    with pytest.raises(ValidationError, match="deviation ids"):
        models.FlopParity.model_validate(data)


@pytest.mark.parametrize("state,value", [("zero", 0), ("unmodelled", None)])
def test_zero_and_null_references_preserve_undefined_relative_error(state: str, value: Any) -> None:
    data = parity()
    data["max_rel"] = None
    row = data["comparisons"][0]
    row.update(
        actual=value,
        reference=value,
        reference_state=state,
        raw_rel=None,
        residual_rel=None,
        signed_adjustment_rel=0,
        absolute_adjustment_rel=0,
        declared_deviations=[],
    )
    model = models.FlopParity.model_validate(data)
    assert model.comparisons[0].actual == value
    assert model.max_rel is None
    for field, invalid in (
        ("raw_rel", 0),
        ("residual_rel", 0),
        ("actual", 1),
        ("declared_deviations", [comparison()["declared_deviations"][0]]),
    ):
        wrong = deepcopy(data)
        wrong["comparisons"][0][field] = invalid
        with pytest.raises(ValidationError):
            models.FlopParity.model_validate(wrong)


@pytest.mark.parametrize(
    "changes",
    [
        {"fixture_set_id": "synthetic"},
        {"candidate_identity": "synthetic"},
        {"oracle_manifest_sha256": "a" * 64},
        {"max_rel": 0},
        {"n_fixtures": 1},
        {"comparisons": [comparison()]},
    ],
)
def test_not_run_has_no_comparison_claim(changes: dict[str, Any]) -> None:
    models.FlopParity.model_validate(not_run())
    with pytest.raises(ValidationError):
        models.FlopParity.model_validate(not_run() | changes)


@pytest.mark.parametrize(
    "deltas,actual,ok",
    [
        ([0.03, 0.02], 105.5, True),  # total 5%, residual exactly .5%
        ([0.03, -0.02], 101.0, True),  # opposing terms spend the entire 5% budget
        ([0.05, -0.05], 101.0, False),
        ([0.05] * 20, 200.0, False),
        ([0.003], 100.3, False),  # unnecessary even if physically named
        ([0.03, 0.02], 105.5001, False),
        ([], 100.5, True),
        ([], 100.5001, False),
    ],
)
def test_adjustment_budget_residual_and_unnecessary_terms(
    deltas: list[float],
    actual: float,
    ok: bool,
) -> None:
    import math

    models.FlopParity.model_validate(parity())
    data = parity()
    raw = (actual - 100.0) / 100.0
    signed = math.fsum(deltas)
    data["max_rel"] = abs(raw)
    data["comparisons"][0].update(
        actual=actual,
        raw_rel=raw,
        signed_adjustment_rel=signed,
        absolute_adjustment_rel=math.fsum(abs(d) for d in deltas),
        residual_rel=raw - signed,
        declared_deviations=[
            dict(id=str(i), deviation_rel=d, reason="Synthetic term") for i, d in enumerate(deltas)
        ],
    )
    if ok:
        models.FlopParity.model_validate(data)
    else:
        with pytest.raises(ValidationError):
            models.FlopParity.model_validate(data)


def test_per_fixture_channel_budget_cannot_pool() -> None:
    models.FlopParity.model_validate(parity())
    data = parity()
    second = deepcopy(data["comparisons"][0])
    second.update(fixture_id="other", actual=110, raw_rel=0.1, residual_rel=0.05)
    data.update(n_fixtures=2, max_rel=0.1, comparisons=[data["comparisons"][0], second])
    with pytest.raises(ValidationError):
        models.FlopParity.model_validate(data)


def test_table_preserves_comparison_classification_and_attribution() -> None:
    data = toy() | {"flop_parity": parity()}
    model = models.LegacyUarchCostTable.model_validate(data)
    assert model.flop_parity.kind == "harness_self_test"
    assert model.flop_parity.comparisons[0].fixture_id == "synthetic/adjusted"
    assert model.flop_parity.comparisons[0].channel == "matrix_ops"


@pytest.mark.parametrize("tp,pad", [(16, False), (8, True)])
def test_a_f12_oracle_scope_does_not_restrict_legitimate_shapes(tp: int, pad: bool) -> None:
    from uarch_contract.request import LegacyCharacterizationRequest

    data = request_data() | {"tp": tp}
    if pad:
        data["model_shape"]["vocab_size"] += 1
    model = LegacyCharacterizationRequest.model_validate(data)
    assert model.tp == tp
    if pad:
        assert model.model_shape.vocab_size % tp != 0
    else:
        assert model.model.kv_heads < tp


def test_condition_carrier_does_not_claim_to_verify_unavailable_hardware() -> None:
    # The typed vocabulary/unit is known, but whether NoC 999 exists is not in this payload.
    data = toy()
    data["provenance"]["conditional_on"] = [
        {
            "path": "nocs[999].link_bytes_per_cycle",
            "value": sv(
                64,
                "byte/cycle",
                kind="stipulation",
                provenance=None,
                rationale="synthetic input echo; producer must verify referenced spec",
            ),
        }
    ]
    model = models.LegacyUarchCostTable.model_validate(data)
    assert model.provenance.conditional_on[0].path == "nocs[999].link_bytes_per_cycle"
