"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenModel, JsonFloat
from .precision import PrecisionFormat
from .sourced import SourcedValue
from .table import Parameter


class FiveFieldValue(FrozenModel):
    date: str | None
    provenance: Literal["stub", "estimated", "spec_derived", "measured"]
    source: str | None
    unit: Annotated[str, Field(min_length=1)]
    value: JsonFloat


class ExplicitPrecision(FrozenModel):
    compute: PrecisionFormat
    kv_cache: PrecisionFormat


class ProjectionLoss(FrozenModel):
    original: SourcedValue
    path: Annotated[str, Field(min_length=1, pattern="\\S")]
    projected: FiveFieldValue
    reason: Literal[
        "stipulation_not_in_upstream",
        "citation_not_loader_eligible",
        "measured_anchor_unavailable",
        "strip_extensions_only",
    ]


class ExecutionModelInput(FrozenModel):
    acceptance: Literal["proposed", "accepted_input"]
    assumption_note: Annotated[str, Field(min_length=1, pattern="\\S")]
    compute: SourcedValue
    evidence_hashes: Annotated[
        tuple[Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")], ...], Field(min_length=0)
    ]
    execution_model_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-execution-model/1"]
    kind: Literal["scalar_efficiency", "split_efficiency"]
    memory: SourcedValue | None

    @model_validator(mode="after")
    def accepted_semantics(self) -> ExecutionModelInput:
        if (self.kind == "split_efficiency") != (self.memory is not None):
            raise ValueError("ExecutionModelMismatch: scalar memory is explicitly null")
        for factor in (self.compute, self.memory):
            if factor is not None and (factor.unit != "ratio" or not 0 < factor.value <= 1):
                raise ValueError("ExecutionModelMismatch: efficiency must be in (0, 1]")
        return self


class ComponentExport(FrozenModel):
    component_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    derivation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    design_status: Literal["proposed", "reference"]
    execution_model_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    export_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-component-truth/1"]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    params: Annotated[tuple[Parameter, ...], Field(min_length=1)]


class ExportBinding(FrozenModel):
    binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    component_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    derivation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    design_status: Literal["proposed", "reference"]
    execution_model_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-export-binding/1"]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    kind: Literal["uarch_projection"]
    losses: Annotated[tuple[ProjectionLoss, ...], Field(min_length=0)]
    primary_export_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    projected_descriptor_bytes_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    projected_descriptor_content_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    projection_recipe: Literal["pinned-five-field-test-projection/1"]
    supported_kv_storage: Annotated[
        Annotated[tuple[PrecisionFormat, ...], Field(min_length=1)],
        Field(json_schema_extra={"uniqueItems": True}),
    ]
    upstream_sha: Annotated[str, Field(pattern="^[0-9a-f]{40}$")]

    @model_validator(mode="after")
    def unique_values(self) -> ExportBinding:
        if len(set(self.supported_kv_storage)) != len(self.supported_kv_storage):
            raise ValueError("Duplicate values: supported_kv_storage")
        return self


class UpstreamComponentBinding(FrozenModel):
    binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    component_bytes_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    component_file: Annotated[str, Field(min_length=1, pattern="\\S")]
    component_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    execution_model_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-upstream-component/1"]
    kind: Literal["upstream_only"]
    oracle_manifest_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    supported_kv_storage: Annotated[
        Annotated[tuple[PrecisionFormat, ...], Field(min_length=1)],
        Field(json_schema_extra={"uniqueItems": True}),
    ]
    upstream_sha: Annotated[str, Field(pattern="^[0-9a-f]{40}$")]

    @model_validator(mode="after")
    def unique_values(self) -> UpstreamComponentBinding:
        if len(set(self.supported_kv_storage)) != len(self.supported_kv_storage):
            raise ValueError("Duplicate values: supported_kv_storage")
        return self


class ComponentPrecision(FrozenModel):
    binding: ExportBinding | UpstreamComponentBinding
    component_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    format: Literal["uarch-component-precision/1"]
    precision_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    precisions: Annotated[
        Annotated[tuple[ExplicitPrecision, ...], Field(min_length=1)],
        Field(json_schema_extra={"uniqueItems": True}),
    ]

    @model_validator(mode="after")
    def accepted_semantics(self) -> ComponentPrecision:
        pairs = [(p.compute, p.kv_cache) for p in self.precisions]
        if len(set(pairs)) != len(pairs):
            raise ValueError("DuplicatePrecisionPair: precisions")
        if self.binding.component_id != self.component_id:
            raise ValueError("ComponentBindingMismatch: component_id")
        return self


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    FiveFieldValue,
    ExplicitPrecision,
    ProjectionLoss,
    ExecutionModelInput,
    ComponentExport,
    ExportBinding,
    UpstreamComponentBinding,
    ComponentPrecision,
)

for _model in (
    FiveFieldValue,
    ExplicitPrecision,
    ProjectionLoss,
    ExecutionModelInput,
    ComponentExport,
    ExportBinding,
    UpstreamComponentBinding,
    ComponentPrecision,
):
    _model.model_rebuild()
