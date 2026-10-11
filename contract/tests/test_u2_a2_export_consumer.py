"""U2-AB2-C1: actual received export positive, independent rehashed negative mutations."""

import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.exports import ComponentPrecision
from uarch_contract.hashing import artifact_identity, canonical_json, content_hash, sha256

from scripts.vendor_rk import PIN, validate_u2_component_inputs

ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / "contract/tests/fixtures/u2_b/a2-export"


def inputs() -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    artifacts = {}
    for path in EXPORT.glob("*.json"):
        value = json.loads(path.read_text())
        artifacts[artifact_identity(value)] = value
    binding = json.loads((EXPORT / "npu-l4.binding.json").read_text())
    entry = dict(
        format="uarch-component-precision/1",
        binding=binding,
        component_id=binding["component_id"],
        precisions=[dict(compute="bf16", kv_cache="bf16")],
    )
    entry["precision_hash"] = content_hash(entry)
    descriptors = {entry["component_id"]: (EXPORT / "npu-l4.oracle-compat.yaml").read_bytes()}
    return entry, descriptors, artifacts


def rehash(value: Any, field: str) -> None:
    value[field] = content_hash(value, exclude=(field,))


def rebound(
    entry: dict[str, Any],
    descriptors: dict[str, bytes],
    artifacts: dict[str, Any],
    *,
    execution_change: Callable[[dict[str, Any]], None] | None = None,
    join_change: Callable[[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]], None]
    | None = None,
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    entry, descriptors, artifacts = deepcopy((entry, descriptors, artifacts))
    binding = entry["binding"]
    truth = artifacts[binding["primary_export_hash"]]
    execution = artifacts[binding["execution_model_hash"]]
    derivation = artifacts[binding["derivation_hash"]]
    descriptor = json.loads(descriptors[entry["component_id"]])
    if execution_change:
        execution_change(execution)
        rehash(execution, "execution_model_hash")
        artifacts[execution["execution_model_hash"]] = execution
        truth["execution_model_hash"] = binding["execution_model_hash"] = execution[
            "execution_model_hash"
        ]
        compute = execution["compute"]
        projected = {k: compute[k] for k in ("value", "unit", "provenance", "source", "date")}
        if compute["kind"] == "stipulation" or compute["provenance"] == "measured":
            projected.update(provenance="stub", source=None, date=None)
        descriptor["execution_model"]["value"] = projected
        loss = next(x for x in binding["losses"] if x["path"] == "execution_model.value")
        loss.update(
            original=compute,
            projected=projected,
            reason="stipulation_not_in_upstream"
            if compute["kind"] == "stipulation"
            else "measured_anchor_unavailable"
            if compute["provenance"] == "measured"
            else "strip_extensions_only",
        )
    if join_change:
        join_change(binding, truth, derivation, descriptor)
    rehash(derivation, "derivation_hash")
    artifacts[derivation["derivation_hash"]] = derivation
    truth["derivation_hash"] = binding["derivation_hash"] = derivation["derivation_hash"]
    rehash(truth, "export_hash")
    artifacts[truth["export_hash"]] = truth
    binding["primary_export_hash"] = truth["export_hash"]
    raw = (canonical_json(descriptor) + "\n").encode()
    descriptors[entry["component_id"]] = raw
    binding["projected_descriptor_bytes_sha256"] = sha256(raw)
    binding["projected_descriptor_content_hash"] = content_hash(descriptor)
    rehash(binding, "binding_hash")
    rehash(entry, "precision_hash")
    return entry, descriptors, artifacts


def validate(
    values: tuple[dict[str, Any], dict[str, bytes], dict[str, Any]],
) -> tuple[ComponentPrecision, ...]:
    entry, descriptors, artifacts = values
    return validate_u2_component_inputs([entry], descriptors, artifacts, require_full=False)


def test_AB2_C1_actual_A2_export_accepts_unchanged() -> None:
    values = inputs()
    assert (EXPORT / "PIN").read_text().strip() == PIN
    assert sha256(next(iter(values[1].values()))) == (
        "sha256:2ea53cfd0b039908f35e67cc21d658f634e714605cdbc8446e9708736bf738ea"
    )
    before = deepcopy(values)
    assert validate(values)[0].component_id == values[0]["component_id"]
    assert values == before


def stipulation(e: dict[str, Any]) -> None:
    e["compute"].update(kind="stipulation", provenance=None, rationale="negative mutation")


def promoted(e: dict[str, Any]) -> None:
    e["compute"].update(
        provenance="measured", source="https://example.invalid/negative", date="2026-01-01"
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e["compute"].update(value=0.9),
        stipulation,
        promoted,
        lambda e: e.update(evidence_hashes=["sha256:" + "a" * 64]),
        lambda e: e.update(acceptance="proposed"),
        lambda e: e.update(assumption_note="Validated hardware efficiency."),
        lambda e: e["compute"].update(date="2026-01-01"),
    ],
)
def test_AB2_C1_rehashed_wrong_execution_input_refuses(
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    values = inputs()
    validate(values)  # Every mutation has the actual export as a passing control.
    with pytest.raises(ValueError):
        validate(rebound(*values, execution_change=mutate))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b, t, d, p: p["params"][next(iter(p["params"]))].update(value=123.0),
        lambda b, t, d, p: t["params"][0]["value"].update(value=123.0),
        lambda b, t, d, p: d.update(hardware_spec_hash="sha256:" + "a" * 64),
        lambda b, t, d, p: b["losses"][0]["original"].update(value=123.0),
        lambda b, t, d, p: b.update(supported_kv_storage=["bf16", "fp8"]),
        lambda b, t, d, p: b.update(upstream_sha="0" * 40),
    ],
)
def test_AB2_C1_rehashed_inconsistent_source_projection_refuses(
    mutate: Callable[[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]], None],
) -> None:
    values = inputs()
    validate(values)
    with pytest.raises(ValueError):
        validate(rebound(*values, join_change=mutate))


def test_AB2_C1_unsupported_KV_and_changed_pair_refuse() -> None:
    for compute, kv in [("bf16", "fp8"), ("fp16", "bf16")]:
        entry, descriptors, artifacts = inputs()
        entry["precisions"] = [dict(compute=compute, kv_cache=kv)]
        rehash(entry, "precision_hash")
        with pytest.raises(ValueError, match="UnsupportedPrecision|exact seven"):
            validate((entry, descriptors, artifacts))


def test_AB2_C1_full_approved_input_inventory_includes_actual_export() -> None:
    entry, descriptors, artifacts = inputs()
    directory = ROOT / "contract/tests/fixtures/u2_b"
    retained = json.loads((directory / "component-precisions.json").read_text())
    for r in retained:
        descriptors[r["component_id"]] = (
            ROOT / "contract/vendor" / ("rk-sim@" + PIN) / r["binding"]["component_file"]
        ).read_bytes()
    for name in ["asic_placeholder-execution.json", "nvidia_h100_sxm-execution.json"]:
        value = json.loads((directory / name).read_text())
        assert value["compute"]["value"] == 0.55
        artifacts[artifact_identity(value)] = value
    assert len(validate_u2_component_inputs([*retained, entry], descriptors, artifacts)) == 3
