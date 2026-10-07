"""U-P1 acceptance, written before implementation; all data is synthetic."""

from __future__ import annotations

import importlib
import json
import math
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError
from uarch_contract import errors
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, table_hash
from uarch_contract.model_shape import ModelShape, ModelSpec, check_parity, implied_params
from uarch_contract.request import CharacterizationRequest
from uarch_contract.sourced import SourcedValue
from uarch_contract.table import UarchCostTable

FIXTURES = Path(__file__).parent / "fixtures"
MODULES = (
    "sourced",
    "hardware",
    "operators",
    "model_shape",
    "precision",
    "request",
    "table",
    "model_card",
    "errors",
    "common",
)


def sv(value: float = 1, unit: str = "count", **changes: Any) -> dict[str, Any]:
    return dict(value=value, unit=unit, provenance="stub", source=None, date=None) | changes


def hardware() -> dict[str, Any]:
    """Minimal complete synthetic reference; no invented sourced hardware claims."""
    return {
        "id": "synthetic",
        "design_status": "reference",
        "clock_domains": {
            key: {"freq_hz": sv(1e9, "Hz"), "scales_with_core": key == "core"}
            for key in ("core", "noc", "dram")
        },
        "cores": {
            "grid": {"rows": sv(), "cols": sv()},
            "core_type": {
                "matrix_engine": {
                    "array": {"rows": sv(), "cols": sv()},
                    "dataflows": ["weight_stationary"],
                    "macs_per_cycle": {"bf16": sv(1, "MAC/cycle")},
                    "accumulator_bytes": sv(64, "byte"),
                    "operand_buffer_bytes": sv(64, "byte"),
                    "operand_bytes_per_cycle": sv(1, "byte/cycle"),
                },
                "vector_engine": {"ops_per_cycle": sv(1, "op/cycle")},
                "sram": {
                    "bytes": sv(128, "byte"),
                    "banks": sv(),
                    "bytes_per_cycle_per_bank": sv(1, "byte/cycle"),
                },
                "dma": {
                    "engines": sv(),
                    "bytes_per_cycle": sv(1, "byte/cycle"),
                    "max_outstanding": sv(),
                    "request_bytes": sv(64, "byte"),
                },
                "job_overhead_cycles": sv(0, "cycle"),
            },
        },
        "sync": {"mechanism": "noc_semaphore", "barrier_latency_cycles": sv(1, "cycle")},
        "nocs": [
            {
                "topology": "mesh",
                "direction": "bidirectional",
                "link_bytes_per_cycle": sv(1, "byte/cycle"),
                "router_latency_cycles": sv(1, "cycle"),
                "virtual_channels": sv(),
                "buffer_flits": sv(),
            }
        ],
        "memory": {
            "interleave": {"granularity_bytes": sv(64, "byte"), "scheme": "channel_hash"},
            "controllers": [
                {
                    "attach": [0, 0],
                    "scheduler": "fr_fcfs",
                    "page_policy": "open",
                    "read_queue_depth": sv(),
                    "write_queue_depth": sv(),
                    "noc_credits": sv(),
                }
            ],
            "dram": {
                "standard": "gddr6",
                "channels": sv(),
                "bw_bytes_per_s": sv(1e9, "byte/s"),
                "capacity_bytes": sv(1e9, "byte"),
                "organization": {
                    "ranks": sv(),
                    "bank_groups": sv(),
                    "banks_per_group": sv(),
                    "row_bytes": sv(64, "byte"),
                },
                "timing_source": "direct",
                "timing_preset": None,
                "timing": {
                    key: sv(1, "cycle")
                    for key in (
                        "t_rcd_cycles",
                        "t_rp_cycles",
                        "t_cl_cycles",
                        "t_rfc_cycles",
                        "t_refi_cycles",
                    )
                },
            },
        },
        "formats": {
            "bf16": {
                "bytes": 2,
                "accumulate_bytes": sv(4, "byte"),
                "block_scale_bytes": sv(0, "byte"),
            }
        },
        "energy": {
            "pj_per_mac": {"bf16": sv(1, "pJ/MAC")},
            "pj_per_byte": {key: sv(1, "pJ/byte") for key in ("sram", "noc_hop", "dram")},
            "voltage_ratio": {},
        },
        "static_power_w": sv(1, "W"),
        "tdp_w": sv(2, "W"),
    }


def model_pair() -> tuple[ModelSpec, ModelShape]:
    return (
        ModelSpec(
            name="Llama-3.1-70B-shaped",
            total_params=70_553_706_496,
            active_params=70_553_706_496,
            n_layers=80,
            d_model=8192,
            n_heads=64,
            kv_heads=8,
        ),
        ModelShape(
            d_ff=28672,
            gated_mlp=True,
            vocab_size=128256,
            attention="gqa",
            tie_embeddings=False,
            expert_d_ff=None,
        ),
    )


def request_data() -> dict[str, Any]:
    spec, shape = model_pair()
    return {
        "contract": "uarch-contract/0.1",
        "rk_schema_snapshot": "1e5706e0ebfcc67c1a7333079a35b75f693e9963",
        "component_id": "synthetic",
        "hardware_spec_hash": "sha256:" + "a" * 64,
        "model": spec.model_dump(mode="json"),
        "model_shape": shape.model_dump(mode="json"),
        "precision": {"compute": "bf16", "kv_cache": "bf16"},
        "tp": 8,
        "envelope": {
            "decode": {"batch_max": 2, "context_per_seq_max": 128},
            "prefill": {"prompt_tokens_max": 128, "prompts_per_iteration_max": 1},
        },
        "grid": {
            "decode": {"batch": [1, 2], "context_per_seq": [128]},
            "prefill": {"n": [1], "L": [128]},
            "frequency_ratio": [1.0],
        },
        "mapping_policy": "synthetic@1",
        "uarch_fidelity": {
            "compute": 0,
            "noc": 0,
            "dram": 0,
            "sync": "exact",
            "layer_reuse": False,
        },
        "initial_state": "steady",
        "kv_layout": {"block_size_tokens": 16},
        "visit_weights": None,
        "seed": 7,
    }


def toy() -> dict[str, Any]:
    return json.loads((FIXTURES / "toy_table.json").read_text())  # type: ignore[no-any-return]


def walk_models(value: Any) -> list[BaseModel]:
    if isinstance(value, BaseModel):
        return [value] + [
            m for key in type(value).model_fields for m in walk_models(getattr(value, key))
        ]
    if isinstance(value, dict):
        return [m for child in value.values() for m in walk_models(child)]
    if isinstance(value, (tuple, list)):
        return [m for child in value for m in walk_models(child)]
    return []


def test_round_trip_all_models() -> None:
    from uarch_contract.errors import ErrorRecord
    from uarch_contract.generate import exported_models
    from uarch_contract.model_card import ModelCard
    from uarch_contract.operators import OpSpec

    extra = json.loads((FIXTURES / "model_examples.json").read_text())
    examples: list[BaseModel] = [
        HardwareSpec.model_validate(hardware()),
        CharacterizationRequest.model_validate(request_data()),
        UarchCostTable.model_validate(toy()),
        OpSpec.model_validate(extra["op"]),
        ModelCard.model_validate(extra["card"]),
        ErrorRecord.model_validate(extra["error"]),
    ]
    examples += [
        cls.model_validate(payload)
        for name, payload in extra["additional"].items()
        for cls in exported_models()
        if cls.__name__ == name
    ]
    seen = set()
    for model in walk_models(examples):
        cls = type(model)
        seen.add(cls)
        assert cls.model_validate(model.model_dump(mode="json")) == model
        assert cls.model_config["frozen"] is True
        assert cls.model_config["extra"] == "forbid"
    assert set(exported_models()) <= seen, "Each concrete model needs a round-trip example"


def test_hash_fresh_processes_and_key_order() -> None:
    script = (
        "import json; from uarch_contract.hashing import table_hash; "
        f"print(table_hash(json.load(open({str(FIXTURES / 'toy_table.json')!r}))))"
    )
    outputs = [
        subprocess.check_output([sys.executable, "-c", script], text=True).strip() for _ in range(2)
    ]
    assert outputs[0] == outputs[1] == toy()["table_hash"]
    assert table_hash(dict(reversed(list(toy().items())))) == outputs[0]
    assert table_hash(UarchCostTable.model_validate(toy())) == outputs[0]
    assert canonical_json({"b": 1.25, "a": 1e-20}) == canonical_json({"a": 1e-20, "b": 1.25})
    with pytest.raises(ValueError):
        canonical_json({"x": math.nan})


@pytest.mark.parametrize(
    "name",
    [
        "NoTableForComponent",
        "EnvelopeExceedsGrid",
        "SpecHashMismatch",
        "ParamsMismatch",
        "TpMismatch",
        "ContractMajorMismatch",
        "ContractMinorMismatch",
        "ResidencyExceedsCapacity",
        "NonFiniteRow",
        "MissingFrequencyAxis",
        "InitialStateMismatch",
        "KvLayoutMismatch",
        "StipulationOnReference",
        "ClaimWithoutSource",
        "SramCapacityExceeded",
        "UnnamedPreset",
        "ShardIndivisible",
    ],
)
def test_error_schema(name: str) -> None:
    cls = getattr(errors, name)
    exc = cls()
    assert str(exc).endswith(".")
    record = exc.to_record()
    assert errors.ErrorRecord.model_validate_json(record.model_dump_json()) == record
    assert type(record.to_exception()) is cls
    assert str(record.to_exception()) == str(exc)
    assert record.code == name
    if name == "ContractMinorMismatch":
        assert isinstance(exc, Warning)


@pytest.mark.parametrize(
    "changes, match",
    [
        (
            {"kind": "stipulation", "provenance": None, "source": "bad", "rationale": "target"},
            "stipulation",
        ),
        ({"rationale": "bad"}, "claim"),
        ({"provenance": "estimated"}, "non-empty source"),
        ({"source": "bad"}, "stub"),
        ({"source": ""}, "stub"),
        ({"source": "   "}, "stub"),
        ({"kind": "stipulation", "provenance": None, "rationale": " "}, "rationale"),
        ({"value": math.inf}, "finite"),
    ],
)
def test_sourced_refusals(changes: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        SourcedValue.model_validate(sv(**changes))


def test_claim_error_cause() -> None:
    with pytest.raises(ValidationError) as caught:
        SourcedValue.model_validate(sv(provenance="estimated"))
    assert isinstance(caught.value.errors()[0]["ctx"]["error"], errors.ClaimWithoutSource)


def test_nested_reference_stipulation() -> None:
    data = hardware()
    data["cores"]["core_type"]["sram"]["banks"] = sv(
        kind="stipulation", provenance=None, rationale="synthetic design choice"
    )
    with pytest.raises(ValidationError, match=r"cores.core_type.sram.banks") as caught:
        HardwareSpec.model_validate(data)
    assert isinstance(caught.value.errors()[0]["ctx"]["error"], errors.StipulationOnReference)
    data["design_status"] = "proposed"
    HardwareSpec.model_validate(data)


@pytest.mark.parametrize(
    "bad_preset",
    [
        {"file": "preset.yaml"},
        {"file": "preset.yaml", "sha": "main"},
        {"file": "preset.yaml", "sha": "a" * 40},
    ],
)
def test_unnamed_preset(bad_preset: dict[str, str]) -> None:
    data = hardware()
    data["memory"]["dram"]["timing_source"] = "preset"
    data["memory"]["dram"]["timing_preset"] = bad_preset
    data["memory"]["dram"]["timing"]["t_cl_cycles"] = sv(
        1, "cycle", provenance="spec_derived", source="other.yaml@" + "a" * 40
    )
    with pytest.raises(ValidationError) as caught:
        HardwareSpec.model_validate(data)
    assert any(
        isinstance(e.get("ctx", {}).get("error"), errors.UnnamedPreset)
        for e in caught.value.errors()
    )


def test_preset_and_sram_energy_and_stub_count() -> None:
    data = hardware()
    data["memory"]["dram"]["timing_source"] = "preset"
    data["memory"]["dram"]["timing_preset"] = {"file": "preset.yaml", "sha": "a" * 40}
    data["memory"]["dram"]["timing"]["t_cl_cycles"] = sv(
        1, "cycle", provenance="spec_derived", source="preset.yaml@" + "a" * 40
    )
    spec = HardwareSpec.model_validate(data)
    assert spec.cores.core_type.sram.banks.provenance == "stub"
    del data["energy"]["pj_per_byte"]["sram"]
    with pytest.raises(ValueError, match=r"sram.bytes.*energy.pj_per_byte.sram"):
        HardwareSpec.model_validate(data)


def test_count_must_be_integral() -> None:
    data = hardware()
    data["cores"]["grid"]["rows"]["value"] = 1.5
    with pytest.raises(ValueError, match="integral"):
        HardwareSpec.model_validate(data)


def test_shape_parity() -> None:
    model, shape = model_pair()
    assert implied_params(model, shape) == (70_553_706_496, 70_553_706_496)
    check_parity(model, shape)
    wrong = ModelShape.model_validate(shape.model_dump() | {"d_ff": round(shape.d_ff * 1.1)})
    with pytest.raises(ValueError) as caught:
        check_parity(model, wrong)
    assert str(model.total_params) in str(caught.value)
    assert str(implied_params(model, wrong)[0]) in str(caught.value)


def test_shard_indivisible() -> None:
    data = request_data() | {"tp": 3}
    with pytest.raises(ValidationError, match="n_heads") as caught:
        CharacterizationRequest.model_validate(data)
    assert isinstance(caught.value.errors()[0]["ctx"]["error"], errors.ShardIndivisible)


def test_toy_semantics_and_nulls() -> None:
    table = UarchCostTable.model_validate(toy())
    assert [row.phase for row in table.rows] == ["decode", "decode", "prefill"]
    assert table.tp == 8 and table.initial_state == "steady"
    assert table.kv_layout.block_size_tokens == 16
    assert len(type(table.measured_error).model_fields) == 4
    assert table.provenance.model_card.badge == "stub"
    assert any(v is None for v in table.rows[0].diagnostics.model_dump().values())
    assert table_hash(table) == table.table_hash


@pytest.mark.parametrize(
    "key,value",
    [("dram", "2+ts"), ("compute", "1+ts"), ("shared_sram", 2), ("sync", "approx"), ("noc", 3)],
)
def test_fidelity_values(key: str, value: Any) -> None:
    data = request_data()
    data["uarch_fidelity"][key] = value
    with pytest.raises(ValueError, match=key):
        CharacterizationRequest.model_validate(data)


def test_no_numeric_defaults() -> None:
    from uarch_contract.table import Diagnostics

    module = importlib.import_module("uarch_contract.model_card")
    classes = [Diagnostics] + [
        cls
        for cls in vars(module).values()
        if isinstance(cls, type)
        and issubclass(cls, BaseModel)
        and cls.__module__ == module.__name__
    ]
    for cls in classes:
        for field in cls.model_fields.values():
            assert not isinstance(field.default, (int, float))


def schema_float_paths(
    schema: dict[str, Any],
    path: tuple[str, ...] = (),
    root: dict[str, Any] | None = None,
) -> list[tuple[str, ...]]:
    """Follow local refs; SourcedValue.value has an explicit required unit carrier."""
    root = schema if root is None else root
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return schema_float_paths(target, path, root)
    found = [path] if schema.get("type") == "number" else []
    properties = schema.get("properties", {})
    explicit_unit = (
        "unit" in schema.get("required", []) and properties.get("unit", {}).get("type") == "string"
    )
    for key, value in properties.items():
        if key in ("value", "actual", "reference") and explicit_unit:
            continue
        found += schema_float_paths(value, (*path, key), root)
    for key in ("items", "additionalProperties"):
        if isinstance(schema.get(key), dict):
            found += schema_float_paths(schema[key], path, root)
    for key in ("anyOf", "oneOf", "allOf"):
        for value in schema.get(key, []):
            found += schema_float_paths(value, path, root)
    return found


def test_unit_and_cycle_boundaries() -> None:
    suffixes = (
        "_s",
        "_ps",
        "_bytes",
        "_hz",
        "_ratio",
        "_rel",
        "_w",
        "_j",
        "_pj",
        "_per_s",
        "_per_cycle",
        "_flits",
        "_count",
    )
    for module_name in ("request", "table"):
        module = importlib.import_module("uarch_contract." + module_name)
        for cls in vars(module).values():
            if not (
                isinstance(cls, type)
                and issubclass(cls, BaseModel)
                and cls.__module__ == module.__name__
            ):
                continue
            schema = cls.model_json_schema()
            for path in schema_float_paths(schema):
                assert (
                    path[-1].endswith(suffixes)
                    or path[-1].startswith("n_")
                    or path[-1] in ("matrix_ops", "vector_ops")
                ), path
            assert not any(name.endswith("_cycles") for name in cls.model_fields)
    for data in (request_data(), toy()):
        assert '"cycle"' not in json.dumps(data)
        assert '_cycles"' not in json.dumps(data)


def test_schema_freshness() -> None:
    subprocess.run([sys.executable, "-m", "uarch_contract.generate", "--check"], check=True)


@pytest.mark.parametrize(
    "field,value", [("duration_s", -1), ("duration_s", math.nan), ("frequency_ratio", 0)]
)
def test_bad_rows(field: str, value: float) -> None:
    data = deepcopy(toy())
    data["rows"][0][field] = value
    with pytest.raises(ValueError):
        UarchCostTable.model_validate(data)


def test_cycle_unit_cannot_hide_in_table_provenance() -> None:
    data = toy()
    data["provenance"]["params"] = [{"name": "bad", "value": sv(1, "cycle")}]
    with pytest.raises(ValueError, match="cycle"):
        UarchCostTable.model_validate(data)


def test_unsampled_weighted_error_cannot_be_zero() -> None:
    data = toy()
    data["measured_error"]["interpolation_loo"]["weighted_median_rel"] = 0
    with pytest.raises(ValueError, match="unsampled"):
        UarchCostTable.model_validate(data)


def test_schema_checker_detects_changed_missing_and_extra_files(tmp_path: Path) -> None:
    from uarch_contract.generate import generate

    generate(tmp_path)
    assert not generate(tmp_path, check=True)
    (tmp_path / "SourcedValue.json").write_text("{}\n")
    (tmp_path / "ModelSpec.json").unlink()
    (tmp_path / "Obsolete.json").write_text("{}\n")
    assert generate(tmp_path, check=True) == [
        "ModelSpec.json",
        "Obsolete.json",
        "SourcedValue.json",
    ]
    assert (tmp_path / "SourcedValue.json").read_text() == "{}\n", "check must not write"


@pytest.mark.parametrize("tp", [1, 8, 16])
def test_divisible_and_replicated_kv_shards(tp: int) -> None:
    CharacterizationRequest.model_validate(request_data() | {"tp": tp})


def test_ffn_shard_error_is_named() -> None:
    data = request_data()
    data["model_shape"]["d_ff"] += 1  # remains inside the parity tolerance
    with pytest.raises(ValueError, match="d_ff"):
        CharacterizationRequest.model_validate(data)


@pytest.mark.parametrize("change", ["duplicate", "attribution", "c2_floor", "composite", "keys"])
def test_row_semantic_refusals(change: str) -> None:
    data = toy()
    if change == "duplicate":
        data["rows"].append(deepcopy(data["rows"][0]))
    elif change == "attribution":
        data["rows"][0]["attribution_s"]["compute"] = 1
    elif change == "c2_floor":
        data["composite_fidelity"] = "C2"
        data["fidelity_detail"].update(compute=2, noc="1+ts", dram=2, shared_sram="1+ts")
        data["rows"][0]["u_c0_duration_s"] = 1
    elif change == "composite":
        data["composite_fidelity"] = "C2"
    else:
        data["rows"][0]["n_prompts"] = 1
    with pytest.raises(ValueError):
        UarchCostTable.model_validate(data)


def test_moe_parameter_count_hand_case() -> None:
    # d=8, h=4, kv=2, layers=2, E=4, active E=2, expert width=12.
    # Shared: 2*(2*64+2*8*2*2+16)+8+2*16*8+2*8*4 = 744.
    # Per expert across layers: 2*3*8*12 = 576.
    model = ModelSpec(
        name="synthetic-moe",
        total_params=3048,
        active_params=1896,
        n_experts=4,
        experts_per_token=2,
        n_layers=2,
        d_model=8,
        n_heads=4,
        kv_heads=2,
    )
    shape = ModelShape(
        d_ff=12,
        expert_d_ff=12,
        gated_mlp=True,
        vocab_size=16,
        attention="gqa",
        tie_embeddings=False,
    )
    assert implied_params(model, shape) == (3048, 1896)
    check_parity(model, shape)
    bad = shape.model_dump() | {"expert_d_ff": None}
    with pytest.raises(ValueError, match="expert_d_ff"):
        implied_params(model, ModelShape.model_validate(bad))


def test_fused_attention_rejects_dram_scores() -> None:
    from uarch_contract.operators import OpSpec

    data = json.loads((FIXTURES / "model_examples.json").read_text())["op"]
    data["operands"]["scores"] = deepcopy(data["operands"]["Q"])
    with pytest.raises(ValueError, match="exactly Q, K, V and O"):
        OpSpec.model_validate(data)


@pytest.mark.parametrize("key,value", [("compute", True), ("shared_sram", None)])
def test_fidelity_rejects_boolean_levels_and_explicit_null(key: str, value: Any) -> None:
    data = request_data()
    data["uarch_fidelity"][key] = value
    with pytest.raises(ValueError, match=key):
        CharacterizationRequest.model_validate(data)


@pytest.mark.parametrize("shared_sram", [None, 0, "unrepresented"])
@pytest.mark.parametrize("sync", ["exact", "approx(Q=1)"])
def test_zero_hardware_detail_is_c0(shared_sram: Any, sync: str) -> None:
    from uarch_contract.fidelity import FidelityDetail

    data = dict(compute=0, noc=0, dram=0, sync=sync, layer_reuse=False)
    if shared_sram is not None:
        data["shared_sram"] = shared_sram
    detail = FidelityDetail.model_validate(data)
    assert detail.conservative_composite() == "C0"
    assert detail.sync == sync
    assert detail.shared_sram == shared_sram
    table = toy() | {"fidelity_detail": detail.model_dump(mode="json")}
    loaded = UarchCostTable.model_validate(table)
    assert loaded.fidelity_detail == detail  # neither sync nor unrepresented is hidden


@pytest.mark.parametrize("layer_reuse", [False, True])
def test_composite_branches_and_sync_monotonicity_for_all_legal_levels(layer_reuse: bool) -> None:
    from itertools import product

    from uarch_contract.fidelity import FidelityDetail

    rank = {"C0": 0, "C1": 1, "C2": 2}
    for compute, noc, dram, shared in product(
        (0, 1, 2),
        (0, 1, "1+ts", 2),
        (0, 1, "1+ts", 2),
        (None, 0, 1, "1+ts", "unrepresented"),
    ):
        data = dict(compute=compute, noc=noc, dram=dram, layer_reuse=layer_reuse)
        if shared is not None:
            data["shared_sram"] = shared
        zero = compute == noc == dram == 0 and shared in (None, 0, "unrepresented")
        c2_resources = compute == 2 and noc in (2, "1+ts") and dram in (2, "1+ts")
        c2_resources = c2_resources and shared in (None, "1+ts")
        exact = FidelityDetail.model_validate(data | {"sync": "exact"}).conservative_composite()
        assert exact == ("C0" if zero else "C2" if c2_resources else "C1"), data
        for sync in ("approx(Q=1)", "approx(Q=1000000)"):
            approx = FidelityDetail.model_validate(data | {"sync": sync}).conservative_composite()
            assert approx == ("C0" if zero else "C1"), data
            assert rank[approx] <= rank[exact], data


@pytest.mark.parametrize(
    "source",
    [
        "https://example.test/vendor.yaml",
        "measurements.yml",
        "timing.cfg",
        "vendor@lab",
        "preset.yaml@" + "a" * 40,
        "https://user@example.test/direct-timing",
    ],
)
def test_direct_timing_never_classifies_reference_strings(source: str) -> None:
    data = hardware()
    data["memory"]["dram"]["timing"]["t_cl_cycles"] = sv(
        1, "cycle", provenance="spec_derived", source=source
    )
    spec = HardwareSpec.model_validate(data)
    assert spec.memory.dram.timing_source == "direct"
    assert spec.memory.dram.timing.t_cl_cycles.source == source


def test_timing_mode_is_required_and_direct_has_no_preset() -> None:
    data = hardware()
    del data["memory"]["dram"]["timing_source"]
    with pytest.raises(ValidationError, match="timing_source"):
        HardwareSpec.model_validate(data)
    data["memory"]["dram"]["timing_source"] = "direct"
    data["memory"]["dram"]["timing_preset"] = {"file": "preset.cfg", "sha": "a" * 40}
    with pytest.raises(ValidationError, match="direct.*timing_preset"):
        HardwareSpec.model_validate(data)


@pytest.mark.parametrize(
    "preset",
    [
        None,
        {},
        {"file": "preset.cfg"},
        {"file": "preset.cfg", "sha": "main"},
        {"file": "preset.cfg", "sha": "a" * 7},
        {"file": "preset.cfg", "sha": "z" * 40},
        {"sha": "a" * 40},
        {"file": " ", "sha": "a" * 40},
    ],
)
def test_explicit_preset_requires_valid_named_pin(preset: Any) -> None:
    data = hardware()
    data["memory"]["dram"].update(timing_source="preset", timing_preset=preset)
    with pytest.raises(ValidationError):
        HardwareSpec.model_validate(data)


def test_preset_mode_without_preset_field_raises_unnamed_preset() -> None:
    data = hardware()
    data["memory"]["dram"]["timing_source"] = "preset"
    del data["memory"]["dram"]["timing_preset"]
    with pytest.raises(ValidationError) as caught:
        HardwareSpec.model_validate(data)
    assert any(
        isinstance(e.get("ctx", {}).get("error"), errors.UnnamedPreset)
        for e in caught.value.errors()
    )


@pytest.mark.parametrize(
    "source", ["datasheet.pdf", "other.cfg@" + "a" * 40, "preset.cfg@" + "b" * 40]
)
def test_preset_mode_rejects_mixed_or_mismatched_claim_citations(source: str) -> None:
    data = hardware()
    data["memory"]["dram"].update(
        timing_source="preset", timing_preset={"file": "preset.cfg", "sha": "a" * 40}
    )
    data["memory"]["dram"]["timing"]["t_cl_cycles"] = sv(
        1, "cycle", provenance="spec_derived", source=source
    )
    with pytest.raises(ValidationError, match="timing.t_cl_cycles") as caught:
        HardwareSpec.model_validate(data)
    assert any(
        isinstance(e.get("ctx", {}).get("error"), errors.UnnamedPreset)
        for e in caught.value.errors()
    )


@pytest.mark.parametrize("mode", ["direct", "preset"])
def test_timing_modes_preserve_provenance_rules(mode: str) -> None:
    data = hardware()
    dram = data["memory"]["dram"]
    dram["timing_source"] = mode
    if mode == "preset":
        dram["timing_preset"] = {"file": "preset.cfg", "sha": "a" * 40}
    source = "preset.cfg@" + "a" * 40 if mode == "preset" else "direct@vendor.yml"
    dram["timing"]["t_cl_cycles"] = sv(1, "cycle", provenance="spec_derived", source=source)
    spec = HardwareSpec.model_validate(data)
    assert spec.memory.dram.timing.t_rcd_cycles.provenance == "stub"
    assert spec.memory.dram.timing.t_rcd_cycles.source is None
    assert HardwareSpec.model_validate(spec.model_dump(mode="json")) == spec
    dram["timing"]["t_cl_cycles"] = sv(
        1, "cycle", kind="stipulation", provenance=None, rationale="synthetic timing design choice"
    )
    with pytest.raises(ValidationError, match="memory.dram.timing.t_cl_cycles") as caught:
        HardwareSpec.model_validate(data)
    assert isinstance(caught.value.errors()[0]["ctx"]["error"], errors.StipulationOnReference)
    data["design_status"] = "proposed"
    assert HardwareSpec.model_validate(data).memory.dram.timing.t_cl_cycles.kind == "stipulation"
    dram["timing"]["t_cl_cycles"]["source"] = source
    with pytest.raises(ValidationError, match="stipulation requires"):
        HardwareSpec.model_validate(data)


def test_synthetic_timing_mode_examples() -> None:
    from uarch_contract.hardware import Dram

    examples = json.loads((FIXTURES / "dram_timing_modes.json").read_text())
    assert set(examples) == {"direct", "preset"}
    for mode, data in examples.items():
        dram = Dram.model_validate(data)
        assert dram.timing_source == mode
        assert Dram.model_validate(dram.model_dump(mode="json")) == dram


@pytest.mark.parametrize(
    "shared_sram,exact_composite",
    [(None, "C2"), ("unrepresented", "C1"), (0, "C1"), (1, "C1"), ("1+ts", "C2")],
)
@pytest.mark.parametrize("sync", ["exact", "approx(Q=1)"])
def test_optional_shared_sram_scenarios(shared_sram: Any, exact_composite: str, sync: str) -> None:
    from uarch_contract.fidelity import FidelityDetail

    data = dict(compute=2, noc="1+ts", dram=2, sync=sync, layer_reuse=False)
    if shared_sram is not None:
        data["shared_sram"] = shared_sram
    detail = FidelityDetail.model_validate(data)
    assert detail.conservative_composite() == (exact_composite if sync == "exact" else "C1")
    dumped = detail.model_dump(mode="json")
    assert dumped["sync"] == sync
    if shared_sram is None:
        assert "shared_sram" not in dumped  # no resource, not unknown/unmodelled
    else:
        assert dumped["shared_sram"] == shared_sram


@pytest.mark.parametrize("below_floor", [False, True])
def test_c2_without_shared_sram_enforces_own_roofline(below_floor: bool) -> None:
    data = toy()
    data["fidelity_detail"].update(compute=2, noc="1+ts", dram=2, sync="exact")
    assert "shared_sram" not in data["fidelity_detail"]
    data["composite_fidelity"] = "C2"
    if below_floor:
        data["rows"][0]["u_c0_duration_s"] = data["rows"][0]["duration_s"] * 2
        with pytest.raises(ValidationError, match="must not be below its own u_c0_duration_s"):
            UarchCostTable.model_validate(data)
    else:
        table = UarchCostTable.model_validate(data)
        assert table.composite_fidelity == "C2"
        assert table.rows[0].duration_s == table.rows[0].u_c0_duration_s
