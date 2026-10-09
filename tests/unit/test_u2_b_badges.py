"""B1 input prerequisites only. Future badge evaluator cases are in badge-cases.json."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from uarch_contract.errors import StipulationOnReference
from uarch_contract.hardware import HardwareSpec

ROOT = Path(__file__).resolve().parents[2]
HARDWARE_REVIEW = ROOT / "tests/fixtures/u2_b/hardware-review"
SPECS = ("designs/npu-l4.yaml", "designs/npu-m256.yaml",
         "references/tpu-v5e.yaml", "references/blackhole-p100a.yaml")


def leaves(value, path=""):
    if isinstance(value, dict):
        if "kind" in value and "value" in value:
            yield path, value
        else:
            for key, child in value.items():
                yield from leaves(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, f"{path}[{index}]")


@pytest.mark.parametrize("relative", SPECS)
def test_hardware_inputs_validate_and_source_inventory_is_complete(relative):
    # Draft references are schema/provenance fixtures, never active runtime specs.
    path = (ROOT / "hw" / relative if relative.startswith("designs/")
            else HARDWARE_REVIEW / Path(relative).name)
    raw = yaml.safe_load(path.read_text())
    HardwareSpec.model_validate(raw)
    inventory = (HARDWARE_REVIEW / "U2-sourcing-inventory.md").read_text()
    section = inventory.split(f"### hw/{relative}\n", 1)[1].split("\n### ", 1)[0]
    for pointer, value in leaves(raw):
        assert f"| `{pointer}` | {value['value']} |" in section
        if raw["design_status"] == "reference":
            assert value["kind"] == "claim"
            if value["provenance"] == "stub":
                assert value["source"] is None
                assert f"unknown for this chip: {pointer} " in path.read_text()
            else:
                assert value["provenance"] == "spec_derived"
                assert value["source"].startswith("https://")
        else:
            assert value["kind"] == "stipulation"
            assert value["rationale"].strip()
            assert all(value[key] is None for key in ("source", "provenance", "date"))


def test_reference_deep_stipulation_is_refused():
    raw = yaml.safe_load((HARDWARE_REVIEW / "tpu-v5e.yaml").read_text())
    mutated = deepcopy(raw)
    mutated["memory"]["dram"]["timing"]["t_rfc_cycles"] = dict(
        value=2.0, unit="cycle", kind="stipulation", rationale="negative test",
        provenance=None, source=None, date=None,
    )
    with pytest.raises((StipulationOnReference, ValidationError)):
        HardwareSpec.model_validate(mutated)


def test_design_precision_declarations_do_not_invent_l4_fp8_storage():
    raw = yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_text())
    assert set(raw["formats"]) == {"bf16"}
    assert set(raw["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]) == {"bf16"}
    many = yaml.safe_load((ROOT / "hw/designs/npu-m256.yaml").read_text())
    assert set(many["formats"]) == {"bf16", "fp8"}
    assert set(many["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]) == {"bf16", "fp8"}
