"""Stage 2 regressions: public guarantees and independently chosen invalid inputs."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pydantic
import pytest
import yaml
from pydantic import ValidationError
from uarch_contract import errors
from uarch_contract.fidelity import FidelityDetail
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, legacy_request_hash, legacy_table_hash
from uarch_contract.model_card import EmbeddedModelCard, ModelCard, ValidatedErrorBand
from uarch_contract.model_shape import ModelShape, ModelSpec, check_parity, implied_params
from uarch_contract.operators import OpSpec
from uarch_contract.request import LegacyCharacterizationRequest
from uarch_contract.table import Condition, LegacyDecodeRow, LegacyUarchCostTable

from .test_u_p1 import FIXTURES, hardware, request_data, sv, toy

ROOT = Path(__file__).resolve().parents[2]


def example(name: str) -> Any:
    return json.loads((FIXTURES / "model_examples.json").read_text())[name]


def assert_cause(caught: pytest.ExceptionInfo[ValidationError], cls: type[Exception]) -> None:
    assert any(isinstance(e.get("ctx", {}).get("error"), cls) for e in caught.value.errors())


@pytest.mark.parametrize("badge", ["estimated", "measured"])
@pytest.mark.parametrize("embedded", [False, True])
def test_badge_above_stub_requires_evidence(badge: str, embedded: bool) -> None:
    data = toy()["provenance"]["model_card"] if embedded else example("card")
    data.update(badge=badge, evidence=[])
    # Existing verification hashes must not substitute for ledger evidence.
    cls = EmbeddedModelCard if embedded else ModelCard
    with pytest.raises(ValidationError, match="requires.*evidence"):
        cls.model_validate(data)


@pytest.mark.parametrize("omission", range(4))
def test_each_declared_omission_is_required(omission: int) -> None:
    data = toy()
    data["warnings"].remove(
        (
            "Host and runtime time outside the device is unmodelled.",
            "Address translation is unmodelled.",
            "Cache coherence is unmodelled.",
            "Mixed prefill/decode iterations are unmodelled.",
        )[omission]
    )
    with pytest.raises(ValidationError, match="every declared contract omission"):
        LegacyUarchCostTable.model_validate(data)


def test_conditions_are_stipulations_not_claims() -> None:
    with pytest.raises(ValidationError, match="requires a stipulation"):
        Condition.model_validate({"path": "tdp_w", "value": sv(100, "W")})


def test_envelope_exceeds_grid_reports_contract_error() -> None:
    data = request_data()
    data["envelope"]["decode"]["batch_max"] = 3
    with pytest.raises(ValidationError) as caught:
        LegacyCharacterizationRequest.model_validate(data)
    assert_cause(caught, errors.EnvelopeExceedsGrid)


@pytest.mark.parametrize("value", [-0.001, float("inf"), float("nan")])
def test_invalid_row_reports_nonfinite_row(value: float) -> None:
    data = toy()["rows"][0]
    data["counts"]["memory_read_bytes"] = value
    with pytest.raises(ValidationError) as caught:
        LegacyDecodeRow.model_validate(data)
    assert_cause(caught, errors.NonFiniteRow)


def test_unbalanced_kv_replication_reports_shard_error() -> None:
    data = request_data()
    data["model"].update(n_heads=24, kv_heads=8, d_model=3072)
    data["model_shape"]["d_ff"] = 12288
    spec = ModelSpec.model_validate(data["model"])
    shape = ModelShape.model_validate(data["model_shape"])
    total, active = implied_params(spec, shape)
    data["model"].update(total_params=total, active_params=active)
    data["tp"] = 12
    with pytest.raises(ValidationError, match="cannot replicate evenly") as caught:
        LegacyCharacterizationRequest.model_validate(data)
    assert_cause(caught, errors.ShardIndivisible)


def test_decode_context_is_divisible_by_batch() -> None:
    row = toy()["rows"][0] | {"batch": 3, "total_context_tokens": 128}
    with pytest.raises(ValidationError, match="divisible by batch"):
        LegacyDecodeRow.model_validate(row)


def test_grid_points_cannot_repeat() -> None:
    data = request_data()
    data["grid"]["frequency_ratio"] = [1.0, 1.0]
    with pytest.raises(ValidationError, match="must not repeat"):
        LegacyCharacterizationRequest.model_validate(data)


def test_controller_attachment_must_exist() -> None:
    data = hardware()
    data["memory"]["controllers"][0]["attach"] = [0, 1]
    with pytest.raises(ValidationError, match="outside cores.grid"):
        HardwareSpec.model_validate(data)


def test_error_band_ordering() -> None:
    band = example("additional")["ValidatedErrorBand"] | {"low_rel": 0.3, "high_rel": 0.2}
    with pytest.raises(ValidationError, match="must not exceed"):
        ValidatedErrorBand.model_validate(band)


@pytest.mark.parametrize("case", ["median", "composition", "priming_unsampled", "priming_sampled"])
def test_error_statistics_are_coherent(case: str) -> None:
    data = toy()
    e = data["measured_error"]
    if case == "median":
        e["layer_reuse"].update(n_samples=2, median_rel=0.3, max_rel=0.2)
        message = "median_rel must not exceed"
    elif case == "composition":
        e["composition_reduction"]["n_samples"] = 1
        message = "must equal decode plus prefill"
    elif case == "priming_unsampled":
        e["cold_vs_steady"]["priming_2_vs_1_max_rel"] = 0.1
        message = "null exactly when unsampled"
    else:
        e["cold_vs_steady"].update(n_samples=1, median_rel=0.1, max_rel=0.1)
        message = "null exactly when unsampled"
    with pytest.raises(ValidationError, match=message):
        LegacyUarchCostTable.model_validate(data)


def test_parameter_names_are_unique() -> None:
    data = toy()
    data["provenance"]["params"] = [{"name": "tdp_w", "value": sv(100, "W")}] * 2
    with pytest.raises(ValidationError, match="must not repeat parameter names"):
        LegacyUarchCostTable.model_validate(data)


def test_paged_operand_needs_page_size() -> None:
    data = example("op")
    data["operands"]["K"].update(layout="paged", block_size_tokens=None)
    with pytest.raises(ValidationError, match="paged operand requires"):
        OpSpec.model_validate(data)


def test_reduction_axis_must_be_defined() -> None:
    data = example("op")
    data["reduction_axes"].append("undefined")
    with pytest.raises(ValidationError, match="Undefined dimensions.*undefined"):
        OpSpec.model_validate(data)


def test_mha_cannot_describe_grouped_kv_heads() -> None:
    data = request_data()
    with pytest.raises(ValueError, match="mha exactly when"):
        check_parity(
            ModelSpec.model_validate(data["model"]),
            ModelShape.model_validate(data["model_shape"] | {"attention": "mha"}),
        )


@pytest.mark.parametrize("key", ["hbm", "sram"])
def test_peak_residency_names_unknown_resources(key: str) -> None:
    data = toy()["rows"][0]
    del data["peak_resident_bytes"][key]
    with pytest.raises(ValidationError, match="requires hbm and sram"):
        LegacyDecodeRow.model_validate(data)


@pytest.mark.parametrize(
    "carrier", ["FidelityDetail", "LegacyUarchCostTable", "LegacyCharacterizationRequest"]
)
def test_shared_sram_schema_excludes_explicit_null(carrier: str) -> None:
    schema = json.loads((ROOT / "contract/schema" / f"{carrier}.json").read_text())
    detail = schema if carrier == "FidelityDetail" else schema["$defs"]["FidelityDetail"]
    field = detail["properties"]["shared_sram"]
    assert "shared_sram" not in detail["required"]
    assert field["enum"] == [0, 1, "1+ts", "unrepresented"]
    assert "default" not in field
    assert "anyOf" not in field


@pytest.mark.parametrize("field,value", [("tp", True), ("tp", "8"), ("seed", "7")])
def test_request_wire_numbers_reject_boolean_and_string(field: str, value: Any) -> None:
    with pytest.raises(ValidationError):
        LegacyCharacterizationRequest.model_validate(request_data() | {field: value})


@pytest.mark.parametrize("field,value", [("batch", True), ("duration_s", "0.001")])
def test_row_wire_numbers_reject_boolean_and_string(field: str, value: Any) -> None:
    with pytest.raises(ValidationError):
        LegacyDecodeRow.model_validate(toy()["rows"][0] | {field: value})


def test_json_integral_number_remains_compatible() -> None:
    assert LegacyCharacterizationRequest.model_validate(request_data() | {"tp": 8.0}).tp == 8
    assert (
        LegacyDecodeRow.model_validate(toy()["rows"][0] | {"duration_s": 0.001}).duration_s == 0.001
    )


def test_core_domain_always_scales_and_omitted_flag_defaults_true() -> None:
    data = hardware()
    del data["clock_domains"]["core"]["scales_with_core"]
    assert HardwareSpec.model_validate(data).clock_domains.core.scales_with_core is True
    data["clock_domains"]["core"]["scales_with_core"] = False
    with pytest.raises(ValidationError):
        HardwareSpec.model_validate(data)


def test_build_spec_fidelity_fragments_validate() -> None:
    text = (ROOT / "docs/build-spec.md").read_text()
    for name in ("uarch_fidelity", "fidelity_detail"):
        match = re.search(rf"^{name}: (\{{[^\n]*\}})", text, re.M)
        assert match is not None
        detail = FidelityDetail.model_validate(yaml.safe_load(match[1]))
        assert detail.conservative_composite() == "C2"
        assert "shared_sram" not in detail.model_dump(mode="json")


def test_error_band_cannot_claim_zero_error() -> None:
    band = example("additional")["ValidatedErrorBand"] | {"low_rel": 0, "high_rel": 0}
    with pytest.raises(ValidationError):
        ValidatedErrorBand.model_validate(band)


@pytest.mark.parametrize("empty", ["L0", "L2", "both"])
def test_energy_verification_requires_named_families(empty: str) -> None:
    data = toy()["provenance"]["model_card"]
    maps = {"L0": {"mac": None}, "L2": {"mac": None}}
    for rung in ("L0", "L2") if empty == "both" else (empty,):
        maps[rung] = {}
    data["energy_verification"] = maps
    with pytest.raises(ValidationError):
        EmbeddedModelCard.model_validate(data)


def test_readme_cycle_rule_distinguishes_hardware_from_results() -> None:
    # Executable hardware/results examples establish the distinction the README must explain.
    assert (
        HardwareSpec.model_validate(hardware()).cores.core_type.job_overhead_cycles.unit == "cycle"
    )
    with pytest.raises(ValidationError):
        LegacyDecodeRow.model_validate(toy()["rows"][0] | {"duration_cycles": 1})
    readme = (ROOT / "contract/README.md").read_text()
    assert "HardwareSpec" in readme and "execution results" in readme
    assert "no field carries cycles" not in readme


def test_negative_zero_has_one_canonical_identity() -> None:
    a, b = toy(), toy()
    a["rows"][0]["attribution_s"]["noc"] = -0.0
    assert legacy_table_hash(a) == legacy_table_hash(b)
    assert canonical_json({"nested": [-0.0, {"value": -0.0}]}) == '{"nested":[0.0,{"value":0.0}]}'
    assert a["rows"][0]["attribution_s"]["noc"].hex().startswith("-"), "do not mutate inputs"


def test_grid_order_is_preserved_in_request_identity() -> None:
    a, b = request_data(), request_data()
    b["grid"]["decode"]["batch"] = [2, 1]
    assert LegacyCharacterizationRequest.model_validate(b).grid.decode.batch == (2, 1)
    assert legacy_request_hash(a) != legacy_request_hash(b)


def test_voltage_keys_cannot_collapse_after_parsing() -> None:
    data = hardware()
    data["energy"]["voltage_ratio"] = {"0.6": sv(0.8, "ratio"), "0.60": sv(0.9, "ratio")}
    with pytest.raises(ValidationError, match="duplicate.*voltage_ratio"):
        HardwareSpec.model_validate(data)
    del data["energy"]["voltage_ratio"]["0.60"]
    assert HardwareSpec.model_validate(data).energy.voltage_ratio[0.6].value == 0.8


def test_fidelity_round_trip_without_exclude_if_api(monkeypatch: pytest.MonkeyPatch) -> None:
    # Emulate only the absent newer Field keyword; not a claim to test all of Pydantic 2.0.
    original = pydantic.Field

    def old_field(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("exclude_if", None)
        return original(*args, **kwargs)

    monkeypatch.setattr(pydantic, "Field", old_field)
    module_spec = importlib.util.spec_from_file_location(
        "uarch_contract._old_field_probe", ROOT / "contract/uarch_contract/fidelity.py"
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    monkeypatch.setitem(sys.modules, module_spec.name, module)
    module_spec.loader.exec_module(module)
    detail = module.FidelityDetail(compute=2, noc=2, dram=2, sync="exact", layer_reuse=False)
    dumped = detail.model_dump(mode="json")
    assert "shared_sram" not in dumped
    assert module.FidelityDetail.model_validate(dumped) == detail


def moe_pair() -> tuple[ModelSpec, ModelShape]:
    return (
        ModelSpec(
            name="synthetic-moe",
            total_params=3048,
            active_params=1896,
            n_experts=4,
            experts_per_token=2,
            n_layers=2,
            d_model=8,
            n_heads=4,
            kv_heads=2,
        ),
        ModelShape(
            d_ff=12,
            expert_d_ff=12,
            gated_mlp=True,
            vocab_size=16,
            attention="gqa",
            tie_embeddings=False,
        ),
    )


@pytest.mark.parametrize("width", [8, 24, 1_000_000_000])
def test_moe_widths_are_redundant_compatibility_fields(width: int) -> None:
    spec, shape = moe_pair()
    with pytest.raises(ValueError, match="d_ff.*expert_d_ff"):
        check_parity(spec, ModelShape.model_validate(shape.model_dump() | {"d_ff": width}))


def test_moe_total_and_active_account_experts_once() -> None:
    spec, shape = moe_pair()
    # Independent hand calculation: shared weights=744; each expert adds 576.
    assert implied_params(spec, shape) == (744 + 4 * 576, 744 + 2 * 576)
    one_active = ModelSpec.model_validate(spec.model_dump() | {"experts_per_token": 1})
    total, active = implied_params(one_active, shape)
    assert total == 3048 and active == 1320
    # More experts change the router (16 per expert) and total FFNs, not active FFNs.
    six = ModelSpec.model_validate(spec.model_dump() | {"n_experts": 6})
    assert implied_params(six, shape) == (776 + 6 * 576, 776 + 2 * 576)


def full_hardware() -> dict[str, Any]:
    data = hardware()
    data["shared_sram"] = {
        "bytes": sv(128, "byte"),
        "banks": sv(1, "count"),
        "bytes_per_cycle_per_bank": sv(1, "byte/cycle"),
        "latency_cycles": sv(1, "cycle"),
        "attach": [[0, 0]],
    }
    data["energy"]["voltage_ratio"] = {"0.6": sv(0.8, "ratio")}
    return data


# Explicit examples for every dimension, including scaled units and same-suffix traps.
UNIT_CASES = [
    (("clock_domains", "core", "freq_hz"), "Hz", "MHz"),
    (("memory", "dram", "capacity_bytes"), "byte", "GB"),
    (("cores", "core_type", "sram", "bytes"), "B", "bit"),
    (("memory", "dram", "timing", "t_rcd_cycles"), "cycle", "ns"),
    (("cores", "core_type", "matrix_engine", "macs_per_cycle", "bf16"), "MAC/cycle", "op/cycle"),
    (("cores", "core_type", "vector_engine", "ops_per_cycle"), "op/cycle", "MAC/cycle"),
    (("nocs", 0, "link_bytes_per_cycle"), "byte/cycle", "byte/s"),
    (("shared_sram", "bytes_per_cycle_per_bank"), "byte/cycle", "byte"),
    (("memory", "dram", "bw_bytes_per_s"), "byte/s", "GB/s"),
    (("cores", "grid", "rows"), "count", "byte"),
    (("energy", "pj_per_mac", "bf16"), "pJ/MAC", "pJ/op"),
    (("energy", "pj_per_byte", "sram"), "pJ/byte", "pJ/bit"),
    (("energy", "voltage_ratio", "0.6"), "ratio", "V"),
    (("static_power_w",), "W", "mW"),
]


@pytest.mark.parametrize("path,allowed,wrong", UNIT_CASES)
@pytest.mark.parametrize("stipulated", [False, True])
def test_hardware_units_match_explicit_field_meaning(
    path: tuple[Any, ...],
    allowed: str,
    wrong: str,
    stipulated: bool,
) -> None:
    data = full_hardware()
    leaf = data
    for part in path:
        leaf = leaf[part]
    leaf["unit"] = allowed
    if stipulated:
        data["design_status"] = "proposed"
        leaf.update(kind="stipulation", provenance=None, rationale="synthetic design choice")
    spec = HardwareSpec.model_validate(data)
    serialized = spec.model_dump(mode="json")
    actual = serialized
    for part in path:
        actual = actual[part]
    assert actual["unit"] == allowed  # aliases are preserved, never converted
    leaf["unit"] = wrong
    with pytest.raises(ValidationError) as caught:
        HardwareSpec.model_validate(data)
    message = str(caught.value)
    assert str(path[-1]) in message and repr(wrong) in message and "allowed" in message


def test_every_sourced_hardware_leaf_has_a_unit_rule() -> None:
    from uarch_contract.hardware import sourced_leaves

    # A nonsense unit must fail at every populated leaf, not just three suffix examples.
    def replace_unit(value: Any, wanted: str, path: str = "") -> None:
        if path == wanted:
            value["unit"] = "wrong-dimension"
        elif isinstance(value, dict):
            for k, child in value.items():
                replace_unit(child, wanted, f"{path}.{k}" if path else k)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                replace_unit(child, wanted, f"{path}[{i}]")

    spec = HardwareSpec.model_validate(full_hardware())
    for path, _ in sourced_leaves(spec):
        data = full_hardware()
        replace_unit(data, path)
        with pytest.raises(ValidationError, match=re.escape(path)):
            HardwareSpec.model_validate(data)


def test_unit_walk_follows_foreign_schema_references() -> None:
    from .test_u_p1 import schema_float_paths

    schema = {
        "properties": {"foreign": {"$ref": "#/$defs/Foreign"}},
        "$defs": {"Foreign": {"properties": {"latency": {"type": "number"}}}},
    }
    assert schema_float_paths(schema) == [("foreign", "latency")]


@pytest.mark.parametrize("key", ["duration_cycles", "unit"])
def test_request_extra_keys_preserve_cycle_boundary(key: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        LegacyCharacterizationRequest.model_validate(request_data() | {key: "cycle"})


def test_verification_hashes_do_not_replace_model_evidence() -> None:
    data = example("card")
    data.update(badge="estimated", evidence=[])
    data["verification"] = {rung: "sha256:" + "b" * 64 for rung in ("L0", "L0m", "L1", "L2")}
    with pytest.raises(ValidationError, match="ledger evidence, not verification"):
        ModelCard.model_validate(data)


def test_pinned_numeric_carriers_remain_compatible_standalone_and_embedded() -> None:
    from uarch_contract.hashing import spec_hash
    from uarch_contract.sourced import SourcedValue

    raw, normalized = request_data(), request_data()
    raw["model"]["n_layers"] = "80"
    assert ModelSpec.model_validate(raw["model"]) == ModelSpec.model_validate(normalized["model"])
    assert LegacyCharacterizationRequest.model_validate(
        raw
    ) == LegacyCharacterizationRequest.model_validate(normalized)
    assert legacy_request_hash(raw) == legacy_request_hash(normalized)
    assert ModelSpec.model_json_schema()["properties"]["n_layers"]["type"] == "integer"

    claim = sv(1.25, "W")
    textual = claim | {"value": "1.25"}
    assert SourcedValue.model_validate(textual) == SourcedValue.model_validate(claim)
    assert SourcedValue.model_json_schema()["properties"]["value"]["type"] == "number"
    a, b = toy(), toy()
    a["provenance"]["params"] = [{"name": "tdp_w", "value": textual}]
    b["provenance"]["params"] = [{"name": "tdp_w", "value": claim}]
    assert LegacyUarchCostTable.model_validate(a) == LegacyUarchCostTable.model_validate(b)
    assert legacy_table_hash(a) == legacy_table_hash(b)
    hw = hardware()
    plain = hardware()
    hw["clock_domains"]["core"]["freq_hz"]["value"] = "1000000000"
    assert spec_hash(hw) == spec_hash(plain)


@pytest.mark.parametrize("case", ["shape", "operator", "card", "deviation", "coordinate", "format"])
def test_other_a_owned_numeric_fields_do_not_coerce(case: str) -> None:
    with pytest.raises(ValidationError):
        if case == "shape":
            ModelShape.model_validate(request_data()["model_shape"] | {"d_ff": "28672"})
        elif case == "operator":
            data = example("op")
            data["dimensions"]["M"] = True
            OpSpec.model_validate(data)
        elif case == "card":
            ValidatedErrorBand.model_validate(
                example("additional")["ValidatedErrorBand"] | {"high_rel": "0.2"}
            )
        elif case == "deviation":
            from uarch_contract.table import FlopDeviation

            FlopDeviation.model_validate(
                {"id": "test", "deviation_rel": "0.01", "reason": "synthetic"}
            )
        elif case == "coordinate":
            data = hardware()
            data["memory"]["controllers"][0]["attach"] = [False, 0]
            HardwareSpec.model_validate(data)
        else:
            data = hardware()
            data["formats"]["bf16"]["bytes"] = "2"
            HardwareSpec.model_validate(data)
