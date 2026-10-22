"""Additive R /5 carriers. Existing B /4 and v2 mathematical carriers are unchanged."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from .common import FrozenModel, Hash, JsonFloat, NonEmpty
from .mapped import (
    Buffer,
    BufferRange,
    Compute,
    Coverage,
    Dependency,
    MappingPolicy,
    require,
)
from .operators import Operand, OpSpec
from .ordinary import SoftwareProducer
from .prepared import RankScope
from .reference_json import content_hash, verify_identity
from .rotary_v2 import PreparedOpV2, RotaryCoefficients, RotaryEncoding
from .sourced import SourcedValue

Positive = Annotated[int, Field(strict=True, ge=1, le=2**64 - 1)]
U64 = Annotated[int, Field(strict=True, ge=0, le=2**64 - 1)]
Storage = Literal["bf16", "fp32", "int8", "int32"]


class TpuV5eReference(FrozenModel):
    identity: Literal["tpu-v5e"]
    design_status: Literal["reference"]
    tensorcore_count: SourcedValue
    mxu_count: SourcedValue
    mxu_rows: SourcedValue
    mxu_cols: SourcedValue
    bf16_peak_ops_per_s: SourcedValue
    int8_peak_ops_per_s: SourcedValue
    hbm_peak_bytes_per_s: SourcedValue
    vmem_capacity_bytes: SourcedValue
    smem_capacity_bytes: SourcedValue
    hbm_capacity_bytes: SourcedValue
    bf16_mxu_mac_per_s: SourcedValue
    int8_mxu_mac_per_s: SourcedValue
    matrix_fill_equivalent_macs: SourcedValue
    vmem_bytes_per_s: SourcedValue
    hbm_latency_ps: SourcedValue
    hbm_issue_interval_ps: SourcedValue
    hbm_max_outstanding: SourcedValue
    vector_tile_ps: SourcedValue
    vector_group_startup_ps: SourcedValue
    reduction_cost_ratio: SourcedValue
    exp_cost_ratio: SourcedValue
    reciprocal_cost_ratio: SourcedValue
    rsqrt_cost_ratio: SourcedValue
    scalar_op_ps: SourcedValue
    kernel_startup_ps: SourcedValue
    barrier_latency_ps: SourcedValue

    @model_validator(mode="after")
    def values(self) -> Any:
        from .reference_laws import validate_hardware

        validate_hardware(self.model_dump(mode="json"))
        return self


class ReferenceOperand(Operand):
    dtype: Storage  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.


class ReferenceOpSpec(OpSpec):
    operator: Literal[  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.
        "q_projection",
        "k_projection",
        "v_projection",
        "output_projection",
        "ffn_up",
        "ffn_gate",
        "ffn_down",
        "normalization",
        "residual_addition",
        "activation",
        "kv_write",
        "qk_score",
        "softmax",
        "av_application",
        "attention_fused",
        "rotary_embedding",
        "stream_read_sum",
        "stream_fill",
        "stream_copy",
        "paged_gather",
        "scalar_add",
    ]
    operands: dict[NonEmpty, ReferenceOperand]  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.


class ReferencePreparedOp(PreparedOpV2):
    spec: ReferenceOpSpec


class ReferenceSource(FrozenModel):
    source_hash: Hash
    scalar_inputs: dict[NonEmpty, JsonFloat]
    scope: Literal["individual", "decoder"]
    ops: Annotated[tuple[ReferencePreparedOp, ...], Field(min_length=1)]
    attention_mask: Literal["full_square", "causal"]
    coefficients: RotaryCoefficients | None
    kv_key_encoding: RotaryEncoding | None
    page_indices: tuple[U64, ...]
    context_before: U64
    context_after: Positive

    @model_validator(mode="after")
    def closure(self) -> Any:
        verify_identity(self, "source_hash")
        from .reference_laws import validate_source

        validate_source(self.model_dump(mode="json"))
        return self


class ReferenceBuffer(Buffer):
    space: Literal["hbm", "vmem", "smem"]  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.
    dtype: Storage
    persistent: bool
    layout: Literal["contiguous", "tile-packed", "paged"]
    accumulator: bool


class ReferenceCompute(Compute):
    engine: Literal["matrix"]
    core_id: Literal[0]
    matrix_engine_index: Annotated[int, Field(strict=True, ge=0, le=3)]
    operand_dtypes: dict[NonEmpty, Storage]  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.
    accumulator_dtype: Literal["fp32", "int32"]  # type: ignore[assignment]  # Versioned /5 carrier widens the /4 vocabulary.
    valid_pairs: U64 | None
    member: NonEmpty
    leading_index: U64


class Primitive(FrozenModel):
    kind: Literal[
        "add",
        "subtract",
        "multiply",
        "compare",
        "select",
        "negate",
        "reduction_sum",
        "reduction_max",
        "exp",
        "reciprocal",
        "rsqrt",
        "cast",
        "broadcast",
        "index",
    ]
    rows: Positive
    cols: Positive
    leading: Positive
    repeat: Positive
    source_dtype: Storage | None
    destination_dtype: Storage | None


class VectorTask(FrozenModel):
    kind: Literal["vector"]
    id: NonEmpty
    op_id: NonEmpty
    member: NonEmpty
    core_id: Literal[0]
    primitives: Annotated[tuple[Primitive, ...], Field(min_length=1)]
    inputs: tuple[BufferRange, ...]
    outputs: tuple[BufferRange, ...]
    scratch_bytes: Annotated[int, Field(strict=True, ge=0, le=65536)]


class TransferSpan(FrozenModel):
    source_offset_bytes: U64
    destination_offset_bytes: U64
    payload_bytes: Positive


class ReferenceDma(FrozenModel):
    kind: Literal["dma"]
    id: NonEmpty
    op_id: NonEmpty
    dma_engine_id: Literal[0]
    direction: Literal["read", "write"]
    source: BufferRange
    destination: BufferRange
    payload_bytes: Positive
    spans: Annotated[tuple[TransferSpan, ...], Field(min_length=1)]


class LocalTransfer(FrozenModel):
    kind: Literal["local_transfer"]
    id: NonEmpty
    op_id: NonEmpty
    source: BufferRange
    destination: BufferRange
    purpose: Literal["partial", "staging", "spill", "materialization"]


class ReferenceControl(FrozenModel):
    kind: Literal["control"]
    id: NonEmpty
    op_id: NonEmpty
    instructions: Positive
    page_entries: tuple[U64, ...]


class ReferenceBarrier(FrozenModel):
    kind: Literal["barrier"]
    id: NonEmpty
    op_id: NonEmpty
    participant_job_ids: tuple[NonEmpty, ...]


ReferenceTask = Annotated[
    ReferenceCompute
    | VectorTask
    | ReferenceDma
    | LocalTransfer
    | ReferenceControl
    | ReferenceBarrier,
    Field(discriminator="kind"),
]


class TaskGraphV2(FrozenModel):
    format: Literal["uarch-taskgraph/2"]
    graph_hash: Hash
    buffers: tuple[ReferenceBuffer, ...]
    jobs: Annotated[tuple[ReferenceTask, ...], Field(min_length=1)]
    dependencies: tuple[Dependency, ...]
    coverage: tuple[Coverage, ...]
    routes: tuple[()]  # Aggregate memory; no invented physical routes.
    arbitration: Literal["fifo-ready/1"]

    @model_validator(mode="after")
    def graph_laws(self) -> Any:
        verify_identity(self, "graph_hash")
        from .reference_laws import validate_graph

        validate_graph(self.model_dump(mode="json"))
        return self


class ReferenceAssumptions(FrozenModel):
    assumptions_hash: Hash
    revision: Literal["tpu-v5e-premeasurement/3"]
    hbm_budget_bytes: Positive
    vmem_budget_bytes: Positive
    smem_budget_bytes: Positive
    accumulator_window_bytes: Positive
    transient_scratch_bytes: Literal[65536]
    max_request_bytes: Literal[8192]
    matrix_m_chunk: Annotated[int, Field(strict=True, ge=1, le=1024)]
    matrix_kn_slice: Literal[128]
    vector_rows: Literal[8]
    vector_cols: Literal[128]
    reload_policy: Literal["payload-every-invocation"]
    limitations: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def identity(self) -> Any:
        verify_identity(self, "assumptions_hash")
        return self


class ReferenceAdmission(FrozenModel):
    checkpoint: Literal["R"]
    invocation: Literal["production", "test"]
    eligibility: Literal["reference_suite", "verification_only"]

    @model_validator(mode="after")
    def pair(self) -> Any:
        require(
            self.eligibility
            == ("reference_suite" if self.invocation == "production" else "verification_only"),
            "AdmissionMismatch",
        )
        return self


class ReferencePoint(FrozenModel):
    point_id: NonEmpty
    payload_hash: Hash
    task_graph: TaskGraphV2
    initial_state: Literal["steady", "cold"]
    priming_iterations: Annotated[int, Field(strict=True, ge=0, le=2)]

    @model_validator(mode="after")
    def identity(self) -> Any:
        verify_identity(self, "payload_hash")
        require(
            (self.initial_state == "steady") == (self.priming_iterations > 0),
            "UnsupportedInitialState",
        )
        return self


class ReferenceBundle(FrozenModel):
    format: Literal["uarch-prepared/5"]
    bundle_hash: Hash
    producer: SoftwareProducer
    hardware_spec: TpuV5eReference
    hardware_spec_hash: Hash
    assumptions: ReferenceAssumptions
    assumptions_hash: Hash
    rank: RankScope
    mapping_scope: Literal["task_graph"]
    mapping_policy: MappingPolicy
    source: ReferenceSource
    admission: ReferenceAdmission
    points: Annotated[tuple[ReferencePoint, ...], Field(min_length=1, max_length=1)]

    @model_validator(mode="after")
    def closure(self) -> Any:
        verify_identity(self, "bundle_hash")
        require(self.hardware_spec_hash == content_hash(self.hardware_spec), "HardwareMismatch")
        require(self.assumptions_hash == self.assumptions.assumptions_hash, "ContentHashMismatch")
        from .reference_laws import validate_bundle

        validate_bundle(self.model_dump(mode="json"))
        return self


class ReferenceModelVersion(FrozenModel):
    name: Literal["native-intervals"]
    version: Literal["3"]


class ReferenceSoftwareIdentity(FrozenModel):
    name: Literal["native"]
    version: Literal["native-stage/3"]
    package_version: Literal["0.0.1"]
    model: ReferenceModelVersion


class ReferenceJob(FrozenModel):
    protocol: Literal["uarch-engine/5"]
    job_hash: Hash
    bundle_hash: Hash
    point_hash: Hash
    engine: ReferenceSoftwareIdentity
    workload_closure: ReferenceBundle
    admission: ReferenceAdmission
    seed: U64

    @model_validator(mode="after")
    def closure(self) -> Any:
        verify_identity(self, "job_hash")
        require(
            self.bundle_hash == self.workload_closure.bundle_hash
            and self.point_hash == self.workload_closure.points[0].payload_hash,
            "ContentHashMismatch",
        )
        require(self.admission == self.workload_closure.admission, "AdmissionMismatch")
        return self


class ReferenceActivity(FrozenModel):
    task: U64
    sequence: U64
    phase: NonEmpty
    owner: U64
    ready_ps: U64
    start_ps: U64
    end_ps: U64
    occupies: bool
    ratio_start: (
        tuple[
            Annotated[int, Field(strict=True, ge=0, le=2**128 - 1)],
            Annotated[int, Field(strict=True, ge=1, le=2**128 - 1)],
        ]
        | None
    )
    ratio_end: (
        tuple[
            Annotated[int, Field(strict=True, ge=0, le=2**128 - 1)],
            Annotated[int, Field(strict=True, ge=1, le=2**128 - 1)],
        ]
        | None
    )
    causes: tuple[tuple[U64, NonEmpty], ...]


class CriticalPart(FrozenModel):
    activity: U64
    start_ps: U64
    end_ps: U64
    cause: Literal["service", "issue_spacing"]


class ReferenceObservations(FrozenModel):
    format: Literal["uarch-native-observations/4"]
    activities: tuple[ReferenceActivity, ...]
    jobs: tuple[tuple[U64, U64, U64], ...]
    sequences: tuple[tuple[U64, U64, U64, U64], ...]
    allocation_intervals: tuple[tuple[U64, U64], ...]
    critical_path: tuple[CriticalPart, ...]
    priming_iterations: U64
    state_before: Hash
    state_after: Hash
    max_live_events: U64
    persistent_before: tuple[NonEmpty, ...]
    persistent_after: tuple[NonEmpty, ...]
    context_before: U64
    context_after: U64


class ReferenceResult(FrozenModel):
    protocol: Literal["uarch-engine/5"]
    result_hash: Hash
    job_hash: Hash
    bundle_hash: Hash
    point_hash: Hash
    engine: ReferenceSoftwareIdentity
    duration_ps: U64
    counts: dict[NonEmpty, U64]
    per_op_counts: dict[NonEmpty, dict[NonEmpty, U64]]
    consumed_stubs: tuple[NonEmpty, ...]
    calibration: Literal["stub"]
    error: Literal["unknown"]
    energy: Literal["unverified"]
    physical_transactions: None
    energy_pj: None
    observations: ReferenceObservations

    @model_validator(mode="after")
    def identity(self) -> Any:
        verify_identity(self, "result_hash")
        return self
