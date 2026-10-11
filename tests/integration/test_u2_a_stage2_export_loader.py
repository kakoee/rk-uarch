"""C10 public disk/memory loader controls; all review companions are synthetic test scaffolding."""

import copy
import json
from pathlib import Path

import pytest
import yaml
from uarch_contract.common import RK_SCHEMA_SNAPSHOT
from uarch_contract.exports import ExecutionModelInput
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, sha256
from uarch_contract.table import UarchCostTable

from rkuarch.hw.export import export_component, project_for_oracle
from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from rkuarch.table.build import build_table
from tests.integration.test_u2_a_condition_order import h1_capture as h1_fixture
from tests.unit.test_u2_a_loader import reviewed

ROOT = Path(__file__).resolve().parents[2]


def seal(value, field):
    value[field] = content_hash(value, exclude=(field,))
    return value[field]


@pytest.fixture
def export_capture():
    return h1_fixture.__wrapped__()


def records(c):
    hw = c.bundle.hardware_spec
    execution = ExecutionModelInput.model_validate(
        json.loads(
            (
                ROOT / ("contract/tests/fixtures/u2_b/a2-export/npu-l4.execution-model.json")
            ).read_text()
        )
    )
    other = HardwareSpec.model_validate(
        yaml.safe_load((ROOT / "hw/designs/npu-m256.yaml").read_text())
    )
    truth, derivation = export_component(hw, execution, component_id="compute.asic.npu-l4")
    raw, binding = project_for_oracle(
        hw, truth, derivation, execution, upstream_sha=RK_SCHEMA_SNAPSHOT
    )
    other_truth, other_der = export_component(other, execution, component_id="compute.asic.npu-l4")
    values = [truth, derivation, execution, other_truth, other_der]
    store = {
        content_hash(hw): hw.model_dump(mode="json"),
        content_hash(other): other.model_dump(mode="json"),
    }
    for value in values:
        field = next(
            f
            for f in ("export_hash", "derivation_hash", "execution_model_hash")
            if hasattr(value, f)
        )
        store[getattr(value, field)] = value.model_dump(mode="json")
    return binding.model_dump(mode="json"), raw, store, other, other_truth, other_der


CASES = [
    "control",
    "peak",
    "provenance",
    "extra",
    "efficiency",
    "loss",
    "spec",
    "design",
    "pin",
    "derivation",
    "truth",
    "content_hash",
]


@pytest.mark.parametrize("boundary", ["disk", "memory"])
@pytest.mark.parametrize("case", CASES)
def test_c10_public_loader_rehashed_projection_mismatches(export_capture, tmp_path, case, boundary):
    c, context, card, base = export_capture
    original = build_table(c, context=context, model_card=card, artifacts=base)
    table, store = original.table.model_dump(mode="json"), copy.deepcopy(dict(original.artifacts))
    binding, raw, exports, other, other_truth, other_der = records(c)
    store.update(exports)
    descriptor = json.loads(raw)
    # Reviewer-independent adversarial literals, with all affected identities rehashed.
    if case == "peak":
        descriptor["params"]["bf16_tflops"]["value"] = 999.0
    elif case == "provenance":
        descriptor["params"]["hbm_bw"].update(
            provenance="spec_derived", source="https://example.invalid"
        )
    elif case == "extra":
        descriptor["params"]["fp8_tflops"] = dict(descriptor["params"]["bf16_tflops"])
    elif case == "efficiency":
        descriptor["execution_model"]["value"]["value"] = 0.55
    elif case == "loss":
        binding["losses"][0]["reason"] = "strip_extensions_only"
    elif case == "spec":
        binding.update(
            hardware_spec_hash=content_hash(other),
            primary_export_hash=other_truth.export_hash,
            derivation_hash=other_der.derivation_hash,
        )
    elif case == "design":
        binding["design_status"] = "reference"
    elif case == "pin":
        binding["upstream_sha"] = "0" * 40
    elif case == "derivation":
        binding["derivation_hash"] = other_der.derivation_hash
    elif case == "truth":
        truth = copy.deepcopy(store[binding["primary_export_hash"]])
        truth["params"][0]["value"]["value"] += 1
        binding["primary_export_hash"] = seal(truth, "export_hash")
        store[truth["export_hash"]] = truth
    raw = (canonical_json(descriptor) + "\n").encode()
    binding["projected_descriptor_bytes_sha256"] = sha256(raw)
    binding["projected_descriptor_content_hash"] = content_hash(descriptor)
    if case == "content_hash":
        binding["projected_descriptor_content_hash"] = "sha256:" + "0" * 64
    store[seal(binding, "binding_hash")] = binding
    store[sha256(raw)] = raw
    deps = copy.deepcopy(store[context.metric_dependencies_hash])
    deps["recipes"].append(
        dict(
            metric_path="/provenance/params",
            purpose="input",
            granularity="input",
            applicable_dimensions=["hardware_spec_hash"],
            selectors=[
                dict(
                    kind="model_assumption",
                    artifact_hash=binding["binding_hash"],
                    json_pointer="/losses",
                )
            ],
        )
    )
    reviewed(deps, "dependencies_hash", store)
    ctx = context.model_dump(mode="json")
    ctx["metric_dependencies_hash"] = deps["dependencies_hash"]
    store[seal(ctx, "context_hash")] = ctx
    table["artifacts"]["report_context_hash"] = ctx["context_hash"]
    seal(table, "table_hash")
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for identity, value in store.items():
        (artifacts / (identity[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else canonical_json(value).encode()
        )
    path = tmp_path / "table.json"
    path.write_text(canonical_json(table))

    def load():
        return (
            load_verified_report_inputs(path)
            if boundary == "disk"
            else verify_report_inputs(UarchCostTable.model_validate(table), store)
        )

    if case == "control":
        verified = load()
        assert verified.table.rows == original.table.rows
        assert binding["binding_hash"] in verified.artifacts
        assert descriptor["params"]["bf16_tflops"]["value"] == 524.288
        assert descriptor["execution_model"]["value"]["value"] == 1.0
    else:
        expected = (
            "unsupported projection pin"
            if case == "pin"
            else "descriptor content/bytes"
            if case == "content_hash"
            else "ParamsMismatch: bound export/derivation"
            if case in ("truth", "derivation")
            else "ComponentBindingMismatch"
        )
        with pytest.raises(ValueError, match=expected):
            load()
