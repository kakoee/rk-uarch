"""Authoritative component truth and explicitly lossy, test-only pinned projection."""

from __future__ import annotations

from typing import Any, Literal, cast

from uarch_contract.common import RK_SCHEMA_SNAPSHOT
from uarch_contract.derivation import Derivation
from uarch_contract.exports import (
    ComponentExport,
    ExecutionModelInput,
    ExportBinding,
    FiveFieldValue,
    ProjectionLoss,
)
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, sha256, verify_identity
from uarch_contract.sourced import SourcedValue
from uarch_contract.table import Parameter

from .derive import derive_rk_params, validate_storage


def export_component(
    spec: HardwareSpec, execution_model: ExecutionModelInput, *, component_id: str
) -> tuple[ComponentExport, Derivation]:
    """Return shared truth/derivation carriers without modifying the hardware or model."""
    execution_model = ExecutionModelInput.model_validate(execution_model)
    verify_identity(execution_model, "execution_model_hash")
    derivation = derive_rk_params(spec)
    result = ComponentExport(
        format="uarch-component-truth/1",
        export_hash="sha256:" + "0" * 64,
        component_id=component_id,
        hardware_spec_hash=derivation.hardware_spec_hash,
        design_status=spec.design_status,
        derivation_hash=derivation.derivation_hash,
        execution_model_hash=execution_model.execution_model_hash,
        params=tuple(Parameter(name=p.name, value=p.value) for p in derivation.parameters),
    )
    return result.model_copy(
        update={"export_hash": content_hash(result, exclude=("export_hash",))}
    ), (derivation)


def project_for_oracle(
    spec: HardwareSpec,
    truth: ComponentExport,
    derivation: Derivation,
    execution_model: ExecutionModelInput,
    *,
    upstream_sha: str,
) -> tuple[bytes, ExportBinding]:
    """Return JSON (also valid YAML) descriptor bytes plus accepted binding.

    Empty calibration is deliberate: this interface supplies no measured anchors. Loader
    citation syntax is not authentication; the full original evidence remains in truth.
    No upstream import, oracle execution, filesystem write or artifact adoption occurs.
    """
    for value, field in (
        (truth, "export_hash"),
        (derivation, "derivation_hash"),
        (execution_model, "execution_model_hash"),
    ):
        verify_identity(value, field)
    if upstream_sha != RK_SCHEMA_SNAPSHOT:
        raise ValueError("ComponentBindingMismatch: unsupported projection pin")
    if truth.execution_model_hash != execution_model.execution_model_hash:
        raise ValueError("ExecutionModelMismatch: truth/execution-model")
    expected, expected_derivation = export_component(
        spec, execution_model, component_id=truth.component_id
    )
    if truth != expected or derivation != expected_derivation:
        raise ValueError("ParamsMismatch: source derivation/truth")
    for fmt in spec.formats:
        validate_storage(spec, fmt)
    losses: list[ProjectionLoss] = []

    def project(value: SourcedValue, path: str) -> dict[str, Any]:
        reason: Any = "strip_extensions_only"
        grade: Any = value.provenance
        source, date = value.source, value.date
        if value.kind == "stipulation":
            reason = "stipulation_not_in_upstream"
        elif grade == "measured":
            reason = "measured_anchor_unavailable"
        elif grade == "spec_derived" and not (source or "").startswith(("http://", "https://")):
            reason = "citation_not_loader_eligible"
        elif grade == "estimated" and not (
            "docs/decisions/" in (source or "").lower() or "adr " in (source or "").lower()
        ):
            reason = "citation_not_loader_eligible"
        if reason != "strip_extensions_only":
            grade, source, date = "stub", None, None
        projected = FiveFieldValue(
            value=value.value,
            unit=value.unit,
            provenance=cast(Literal["stub", "estimated", "spec_derived", "measured"], grade),
            source=source,
            date=date,
        )
        losses.append(ProjectionLoss(path=path, original=value, projected=projected, reason=reason))
        return projected.model_dump(mode="json")

    descriptor: dict[str, Any] = dict(
        id=truth.component_id,
        kind="compute_resource",
        role="asic",
        params={p.name: project(p.value, "params." + p.name) for p in truth.params},
        fidelity_available=["STUB"],
        calibration=[],
    )
    if execution_model.kind == "scalar_efficiency":
        descriptor["execution_model"] = dict(
            kind="scalar_efficiency",
            value=project(execution_model.compute, "execution_model.value"),
        )
    else:
        assert execution_model.memory is not None
        descriptor["execution_model"] = dict(
            kind="split_efficiency",
            compute=project(execution_model.compute, "execution_model.compute"),
            memory=project(execution_model.memory, "execution_model.memory"),
        )
    payload = (canonical_json(descriptor) + "\n").encode("utf-8")
    binding = ExportBinding(
        format="uarch-export-binding/1",
        binding_hash="sha256:" + "0" * 64,
        kind="uarch_projection",
        component_id=truth.component_id,
        hardware_spec_hash=truth.hardware_spec_hash,
        design_status=truth.design_status,
        derivation_hash=derivation.derivation_hash,
        primary_export_hash=truth.export_hash,
        projected_descriptor_content_hash=content_hash(descriptor),
        projected_descriptor_bytes_sha256=sha256(payload),
        upstream_sha=upstream_sha,
        execution_model_hash=execution_model.execution_model_hash,
        projection_recipe="pinned-five-field-test-projection/1",
        losses=tuple(losses),
        supported_kv_storage=tuple(sorted(spec.formats)),
    )
    return payload, binding.model_copy(
        update={"binding_hash": content_hash(binding, exclude=("binding_hash",))}
    )
