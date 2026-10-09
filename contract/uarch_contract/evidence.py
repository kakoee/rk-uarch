"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .common import FrozenModel, JsonFloat


class EvidencePrecision(FrozenModel):
    compute: Annotated[str, Field(min_length=1, pattern="\\S")]
    kv_cache: Annotated[str, Field(min_length=1, pattern="\\S")] | None
    operands: dict[str, Annotated[str, Field(min_length=1, pattern="\\S")]]


class EvidenceScopeCase(FrozenModel):
    array_fill: Literal["underfilled", "full"] | None
    dram_load_regime: Literal["low", "middle", "high"] | None
    family: Annotated[str, Field(min_length=1, pattern="\\S")]
    frequency_ratio: Annotated[JsonFloat, Field(ge=0)]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    initial_state: Literal["steady", "cold"]
    intensity_regime: Literal["low", "middle", "high"] | None
    kv_block_size_tokens: Annotated[int, Field(strict=True, ge=1)]
    mapping_correspondence_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    mapping_match: Literal["matched", "compiler-chosen"] | None
    model_identity_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    noc_load_regime: Literal["low", "middle", "high"] | None
    op_class: Annotated[str, Field(min_length=1, pattern="\\S")] | None
    precision: EvidencePrecision
    prepared_bundle_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None


class ArtifactPointer(FrozenModel):
    artifact_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    json_pointer: Annotated[str, Field(pattern="^(/.*)?$")]


class EvidenceRecordErrorBand0(FrozenModel):
    high_rel: Annotated[JsonFloat, Field(gt=0)]
    low_rel: Annotated[JsonFloat, Field(ge=0)]


class EvidenceRecord(FrozenModel):
    channel: Annotated[str, Field(min_length=1, pattern="\\S")] | None
    classification: Literal["real", "synthetic_fixture"]
    energy_family: Literal["mac", "sram", "noc_hop", "dram", "static"] | None
    error_band: EvidenceRecordErrorBand0 | None
    evidence_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    evidence_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    format: Literal["uarch-evidence/1"]
    granularity: Literal["operator", "subsystem", "whole_iteration"]
    ordering_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    purpose: Literal["duration", "counts", "diagnostics", "energy"]
    review_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    rung: Literal["L0", "L0m", "L1", "L2", "L3", "L4"]
    scope: Annotated[tuple[EvidenceScopeCase, ...], Field(min_length=1)]
    source_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    verification_hashes: Annotated[
        tuple[Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")], ...], Field(min_length=0)
    ]


class SourceRecord(FrozenModel):
    format: Literal["uarch-reference-source/1"]
    independence_from_candidate: Annotated[bool, Field(strict=True)]
    kind: Literal[
        "silicon_measurement",
        "independent_simulator",
        "hand_derived",
        "contract_test",
        "synthetic_fixture",
    ]
    limitation: Annotated[str, Field(min_length=1, pattern="\\S")]
    raw_blob_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    reference_identity: Annotated[str, Field(min_length=1, pattern="\\S")]
    reference_version: Annotated[str, Field(min_length=1, pattern="\\S")]
    source_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


class ReviewRecord(FrozenModel):
    decision: Literal["accepted", "rejected", "pending"]
    format: Literal["uarch-evidence-review/1"]
    independent: Annotated[bool, Field(strict=True)]
    rationale: Annotated[str, Field(min_length=1, pattern="\\S")]
    review_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    reviewed_subject_hashes: Annotated[
        tuple[Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")], ...], Field(min_length=1)
    ]
    reviewer: Annotated[str, Field(min_length=1, pattern="\\S")]


class OrderingRecord(FrozenModel):
    format: Literal["uarch-ordering/1"]
    ordering_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    prediction_commit: Annotated[str, Field(pattern="^[0-9a-f]{40}$")]
    prediction_is_ancestor: Annotated[bool, Field(strict=True)]
    prediction_tree_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    result_commit: Annotated[str, Field(pattern="^[0-9a-f]{40}$")]
    verification_source_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


class VerificationRecord(FrozenModel):
    format: Literal["uarch-verification/1"]
    model_identity_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    outcome: Literal["passed", "failed", "not_run"]
    purpose: Literal["duration", "counts", "diagnostics", "energy"]
    review_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    rung: Literal["L0", "L0m", "L1", "L2"]
    scope: Annotated[tuple[EvidenceScopeCase, ...], Field(min_length=1)]
    source_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    verification_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    EvidencePrecision,
    EvidenceScopeCase,
    ArtifactPointer,
    EvidenceRecord,
    SourceRecord,
    ReviewRecord,
    OrderingRecord,
    VerificationRecord,
)

for _model in (
    EvidencePrecision,
    EvidenceScopeCase,
    ArtifactPointer,
    EvidenceRecordErrorBand0,
    EvidenceRecord,
    SourceRecord,
    ReviewRecord,
    OrderingRecord,
    VerificationRecord,
):
    _model.model_rebuild()
