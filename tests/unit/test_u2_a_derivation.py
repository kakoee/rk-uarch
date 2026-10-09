"""Hand-derived hardware/export expectations, authored before runtime bodies."""

import copy
import importlib
import json
from pathlib import Path

import pytest
import yaml
from uarch_contract.common import RK_SCHEMA_SNAPSHOT
from uarch_contract.exports import ExecutionModelInput
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, sha256, spec_hash, verify_identity
from uarch_contract.precision import Precision

ROOT = Path(__file__).resolve().parents[2]


def hardware():
    return HardwareSpec.model_validate(
        yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_text())
    )


def execution(factor=1.0):
    value = dict(
        format="uarch-execution-model/1",
        execution_model_hash="sha256:" + "0" * 64,
        acceptance="accepted_input",
        kind="scalar_efficiency",
        memory=None,
        compute=dict(
            value=factor,
            unit="ratio",
            provenance="stub",
            kind="claim",
            source=None,
            date=None,
            rationale=None,
        ),
        evidence_hashes=[],
        assumption_note="Accepted new npu-l4 nominal 1.0; unvalidated, not hardware fact.",
    )
    value["execution_model_hash"] = content_hash(value, exclude=("execution_model_hash",))
    return ExecutionModelInput.model_validate(value)


def derive():
    return importlib.import_module("rkuarch.hw.derive")


def test_accepted_h1_literals_and_exact_contributors():
    result = derive().derive_rk_params(hardware())
    assert {p.name: p.value.value for p in result.parameters} == {
        "bf16_tflops": 524.288,
        "hbm_bw": 1.0,
        "hbm_capacity": 32.0,
        "tdp": 300.0,
    }
    peak = result.parameters[0]
    assert peak.contributor_paths == (
        "clock_domains.core.freq_hz",
        "cores.core_type.matrix_engine.macs_per_cycle.bf16",
        "cores.grid.cols",
        "cores.grid.rows",
    )
    assert peak.conditional_paths == peak.contributor_paths
    assert peak.claim_badge is None
    assert peak.value.kind == "stipulation"
    assert peak.value.provenance is None
    assert peak.value.rationale == "matrix-peak/1: " + ", ".join(peak.conditional_paths)
    assert result.hardware_spec_hash == spec_hash(hardware())
    verify_identity(result, "derivation_hash")


def test_mixed_sources_preserve_stub_and_ignore_unrelated_tdp():
    value = hardware().model_dump(mode="json")
    value["clock_domains"]["core"]["freq_hz"] = dict(value=1e9, unit="Hz", provenance="stub")
    result = derive().derive_rk_params(HardwareSpec.model_validate(value))
    peak = result.parameters[0]
    assert peak.claim_badge == "stub" and peak.value.kind == "stipulation"
    assert "clock_domains.core.freq_hz" not in peak.conditional_paths
    value["tdp_w"]["value"] = 500.0
    assert derive().derive_rk_params(HardwareSpec.model_validate(value)).parameters[0] == peak


def test_all_claims_worst_source_and_reference():
    data = hardware().model_dump(mode="json")

    def claims(obj):
        if isinstance(obj, dict):
            if "kind" in obj and "value" in obj:
                obj.update(
                    kind="claim",
                    provenance="measured",
                    source="https://example.org/test",
                    rationale=None,
                )
            else:
                for child in obj.values():
                    claims(child)
        elif isinstance(obj, list):
            for child in obj:
                claims(child)

    claims(data)
    data["design_status"] = "reference"
    data["clock_domains"]["core"]["freq_hz"]["provenance"] = "spec_derived"
    spec = HardwareSpec.model_validate(data)
    peak = derive().derive_rk_params(spec).parameters[0]
    assert peak.claim_badge == "spec_derived" and peak.value.kind == "claim"
    assert peak.value.source == "uarch-derive:" + spec_hash(spec) + ":matrix-peak/1"
    assert peak.conditional_paths == () and peak.value.date is None


def test_resolved_clocks_peak_and_dram_not_scaled_by_channels():
    resolved = derive().resolve_hardware(
        hardware(), Precision(compute="bf16", kv_cache="bf16"), frequency_ratio=0.5
    )
    assert resolved.core_freq_hz == 500_000_000
    assert resolved.noc_freq_hz == resolved.dram_freq_hz == 1_000_000_000
    assert resolved.matrix_peak_ops_per_s == 262_144_000_000_000.0
    assert resolved.vector_peak_ops_per_s == 512_000_000_000.0
    assert resolved.dram_bw_bytes_per_s == 1_000_000_000_000.0
    assert resolved.dram_capacity_bytes == 32_000_000_000
    assert resolved.array_rows == resolved.array_cols == 256


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("dram", "UnsupportedDramFrequencyScaling"),
        ("zero", "UnsupportedFrequency"),
        ("width", "UnsupportedPrecision"),
        ("block", "UnsupportedBlockScaleGeometry"),
        ("peak", "UnsupportedPrecision"),
        ("kv", "UnsupportedKvStorage"),
    ],
)
def test_capability_refusals(mutation, match):
    data = hardware().model_dump(mode="json")
    ratio, precision = 0.5, Precision(compute="bf16", kv_cache="bf16")
    if mutation == "dram":
        data["clock_domains"]["dram"]["scales_with_core"] = True
    elif mutation == "zero":
        data["clock_domains"]["core"]["freq_hz"]["value"] = 0.1
    elif mutation == "width":
        data["formats"]["bf16"]["bytes"] = 1.0
    elif mutation == "block":
        data["formats"]["bf16"]["block_scale_bytes"]["value"] = 1.0
    elif mutation == "peak":
        precision = Precision(compute="fp16", kv_cache="bf16")
    else:
        precision = Precision(compute="bf16", kv_cache="fp8")
    with pytest.raises(ValueError, match=match):
        derive().resolve_hardware(
            HardwareSpec.model_validate(data), precision, frequency_ratio=ratio
        )


def test_round_once_ties_to_even_and_extra_compute_map_refused():
    data = hardware().model_dump(mode="json")
    data["clock_domains"]["core"]["freq_hz"]["value"] = 5.0
    result = derive().resolve_hardware(
        HardwareSpec.model_validate(data),
        Precision(compute="bf16", kv_cache="bf16"),
        frequency_ratio=0.5,
    )
    assert result.core_freq_hz == 2
    data["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]["fp8"] = copy.deepcopy(
        data["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]["bf16"]
    )
    with pytest.raises(ValueError, match="UnsupportedPrecision"):
        derive().derive_rk_params(HardwareSpec.model_validate(data))


def test_export_truth_projection_bytes_bindings_and_efficiency():
    module = importlib.import_module("rkuarch.hw.export")
    truth, derivation = module.export_component(
        hardware(), execution(), component_id="compute.asic.npu-l4"
    )
    data, binding = module.project_for_oracle(
        hardware(), truth, derivation, execution(), upstream_sha=RK_SCHEMA_SNAPSHOT
    )
    assert data.endswith(b"\n") and not data.endswith(b"\n\n")
    descriptor = json.loads(data)
    assert descriptor["id"] == "compute.asic.npu-l4"
    assert descriptor["params"]["bf16_tflops"] == dict(
        value=524.288, unit="TFLOPS", provenance="stub", source=None, date=None
    )
    assert descriptor["fidelity_available"] == ["STUB"] and descriptor["calibration"] == []
    assert descriptor["execution_model"]["value"]["value"] == 1.0
    assert binding.projected_descriptor_bytes_sha256 == sha256(data)
    assert binding.projected_descriptor_content_hash == content_hash(descriptor)
    assert binding.primary_export_hash == truth.export_hash
    assert binding.supported_kv_storage == ("bf16",)
    assert len(binding.losses) == 5  # four params AND execution-model factor
    assert all(p.value.kind == "stipulation" for p in truth.params)
    assert {loss.reason for loss in binding.losses} == {
        "stipulation_not_in_upstream",
        "strip_extensions_only",
    }
    for value, field in [(truth, "export_hash"), (binding, "binding_hash")]:
        verify_identity(value, field)
    assert (data, binding) == module.project_for_oracle(
        hardware(), truth, derivation, execution(), upstream_sha=RK_SCHEMA_SNAPSHOT
    )
    old, old_derivation = module.export_component(
        hardware(), execution(0.55), component_id="compute.asic.npu-l4"
    )
    old_bytes, _ = module.project_for_oracle(
        hardware(), old, old_derivation, execution(0.55), upstream_sha=RK_SCHEMA_SNAPSHOT
    )
    assert json.loads(old_bytes)["execution_model"]["value"]["value"] == 0.55
    assert old.params == truth.params and old.export_hash != truth.export_hash


def test_rehashed_wrong_derivation_and_wrong_execution_are_refused():
    module = importlib.import_module("rkuarch.hw.export")
    truth, derivation = module.export_component(
        hardware(), execution(), component_id="compute.asic.npu-l4"
    )
    altered = derivation.model_dump(mode="json")
    altered["parameters"][0]["value"]["value"] = 123.0
    altered["derivation_hash"] = content_hash(altered, exclude=("derivation_hash",))
    from uarch_contract.derivation import Derivation

    with pytest.raises(ValueError, match="ParamsMismatch"):
        module.project_for_oracle(
            hardware(),
            truth,
            Derivation.model_validate(altered),
            execution(),
            upstream_sha=RK_SCHEMA_SNAPSHOT,
        )
    with pytest.raises(ValueError, match="ExecutionModelMismatch"):
        module.project_for_oracle(
            hardware(), truth, derivation, execution(0.55), upstream_sha=RK_SCHEMA_SNAPSHOT
        )
