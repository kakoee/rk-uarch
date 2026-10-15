"""Proposed M carriers. Parsing/admission is not execution or evidence qualification.

No producer, file discovery, environment lookup or analytic timing call occurs here.
Use explicit submodule imports; the legacy registry and package exports stay unchanged.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, model_validator

from .assumptions import AssumptionSet
from .common import FrozenModel, Hash, JsonFloat, NonEmpty
from .hardware import HardwareSpec
from .hashing import content_hash, spec_hash, verify_identity
from .prepared import PreparedBundle, PreparedOp, Producer, Query, RankScope, validate_prepared_op
from .rotary_v2 import PreparedBundleV2
from .table import Counts, ExtCounts

U64 = Annotated[int, Field(strict=True, ge=0, le=18446744073709551615)]
Positive = Annotated[int, Field(strict=True, ge=1, le=18446744073709551615)]
Ratio = Annotated[JsonFloat, Field(gt=0)]
ScopeName = Literal["component", "prepared_model", "kernel_fixture", "transport_fixture"]
State = Literal["cold", "steady", "fixture_cold", "fixture_resident"]
JobKind = Literal["compute", "dma", "noc_transfer", "barrier", "fixed_delay"]
PRODUCTION_HARDWARE = "sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9"
SEMANTICS = "U0011-stage2/1"


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ValueError(code + ": " + detail)


def ordered(values: Any, key: Any, code: str) -> None:
    keys = [key(value) for value in values]
    require(keys == sorted(set(keys)), code, "sorted unique inventory required")


class Admission(FrozenModel):
    checkpoint: Literal["K2", "B"]
    invocation: Literal["production", "test"]
    profile_hash: Hash | None
    case_id: NonEmpty | None
    eligibility: Literal["component_only", "verification_only"]

    @model_validator(mode="after")
    def binding(self) -> Admission:
        test = self.invocation == "test"
        require(
            (self.profile_hash is not None) == test and (self.case_id is not None) == test,
            "TestProfileMismatch",
        )
        require(
            self.eligibility == ("verification_only" if test else "component_only"),
            "AdmissionMismatch",
        )
        return self


class MappingPolicy(FrozenModel):
    name: NonEmpty
    version: NonEmpty
    buffer_depth: Positive


class Tile(FrozenModel):
    M: U64
    K: U64
    N: U64


class Extent(FrozenModel):
    M: Positive
    K: Positive
    N: Positive


class Buffer(FrozenModel):
    id: NonEmpty
    space: Literal["hbm", "sram", "accumulator"]
    size_bytes: Positive
    alignment_bytes: Positive
    core_id: U64 | None
    channel_id: U64 | None
    offset_bytes: U64
    bank: U64 | None
    op_id: NonEmpty | None
    operand: NonEmpty | None
    slot_index: Literal[0, 1] | None
    initial_residency: Literal["uninitialized", "preloaded"]
    producer_id: NonEmpty | None
    final_consumer_ids: tuple[NonEmpty, ...]

    @model_validator(mode="before")
    @classmethod
    def strict_literal_type(cls, value: Any) -> Any:
        if isinstance(value, dict) and "slot_index" in value:
            require(
                type(value["slot_index"]) in (int, type(None)),
                "InvalidResource",
                "strict slot_index",
            )
        return value


class FixedDelay(FrozenModel):
    kind: Literal["fixed_delay"]
    id: NonEmpty
    duration_ps: U64
    owner_id: U64


class Compute(FrozenModel):
    kind: Literal["compute"]
    id: NonEmpty
    op_id: NonEmpty
    group_id: NonEmpty | None
    repeat_index: U64
    core_id: U64
    engine: Literal["matrix", "vector"]
    tile_origin: Tile
    tile_extents: Extent
    physical_extents: Extent
    operand_buffers: dict[NonEmpty, NonEmpty]
    operand_dtypes: dict[NonEmpty, Literal["bf16", "fp16", "fp32", "fp8", "int8"]]
    accumulator_buffer_id: NonEmpty
    accumulator_dtype: Literal["fp32"]
    dataflow: Literal["weight_stationary", "output_stationary"]


class BufferRange(FrozenModel):
    buffer_id: NonEmpty
    offset_bytes: U64
    size_bytes: Positive


class Route(FrozenModel):
    id: NonEmpty
    noc_index: U64
    source_core_id: U64
    destination_core_id: U64
    core_ids: tuple[U64, ...]


class Fragment(FrozenModel):
    request_id: NonEmpty
    source_offset_bytes: U64
    destination_offset_bytes: U64
    payload_bytes: Annotated[int, Field(strict=True, ge=1, le=256)]
    transaction_bytes: Literal[256]
    channel_id: U64
    route_id: NonEmpty


class Dma(FrozenModel):
    kind: Literal["dma"]
    id: NonEmpty
    op_id: NonEmpty | None
    dma_engine_id: U64
    direction: Literal["read", "write"]
    source: BufferRange
    destination: BufferRange
    fragments: Annotated[tuple[Fragment, ...], Field(min_length=1)]


class NocTransfer(FrozenModel):
    kind: Literal["noc_transfer"]
    id: NonEmpty
    op_id: NonEmpty | None
    source: BufferRange
    destination: BufferRange
    payload_bytes: Positive
    route_id: NonEmpty
    multicast: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def strict_literal_type(cls, value: Any) -> Any:
        if isinstance(value, dict) and "multicast" in value:
            require(type(value["multicast"]) in (bool,), "UnsupportedMapping", "strict multicast")
        return value


class Barrier(FrozenModel):
    kind: Literal["barrier"]
    id: NonEmpty
    participant_job_ids: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]
    owner_id: U64


Job = Annotated[Compute | Dma | NocTransfer | Barrier | FixedDelay, Field(discriminator="kind")]


class Dependency(FrozenModel):
    before: NonEmpty
    after: NonEmpty


class Coverage(FrozenModel):
    job_id: NonEmpty
    op_id: NonEmpty
    group_id: NonEmpty | None
    repeat_index: U64
    tile_origin: Tile
    tile_extents: Extent


class TaskGraph(FrozenModel):
    format: Literal["uarch-taskgraph/1"]
    graph_hash: Hash
    buffers: tuple[Buffer, ...]
    jobs: Annotated[tuple[Job, ...], Field(min_length=1)]
    dependencies: tuple[Dependency, ...]
    coverage: tuple[Coverage, ...]
    routes: tuple[Route, ...]
    arbitration: Literal["fifo-ready/1"]

    @model_validator(mode="after")
    def graph_laws(self) -> TaskGraph:
        verify_identity(self, "graph_hash")
        ordered(self.jobs, lambda x: x.id, "InvalidDependency")
        ordered(self.buffers, lambda x: x.id, "InvalidResource")
        ordered(self.routes, lambda x: x.id, "InvalidRoute")
        ordered(self.dependencies, lambda x: (x.before, x.after), "InvalidDependency")
        ordered(self.coverage, lambda x: x.job_id, "InvalidCoverage")
        ids = {job.id for job in self.jobs}
        predecessors: dict[str, set[str]] = {key: set() for key in ids}
        for edge in self.dependencies:
            require(
                edge.before in ids and edge.after in ids and edge.before != edge.after,
                "InvalidDependency",
            )
            predecessors[edge.after].add(edge.before)
        done: set[str] = set()
        while len(done) < len(ids):
            ready = {key for key in ids - done if predecessors[key] <= done}
            require(bool(ready), "InvalidDependency", "cycle")
            done.update(ready)
        computes = {job.id: job for job in self.jobs if isinstance(job, Compute)}
        require(set(computes) == {c.job_id for c in self.coverage}, "InvalidCoverage")
        for c in self.coverage:
            j = computes[c.job_id]
            require(
                all(
                    getattr(c, key) == getattr(j, key)
                    for key in ("op_id", "group_id", "repeat_index", "tile_origin", "tile_extents")
                ),
                "InvalidCoverage",
            )
        for job in self.jobs:
            if isinstance(job, Barrier):
                ordered(job.participant_job_ids, lambda x: x, "InvalidDependency")
                require(set(job.participant_job_ids) == predecessors[job.id], "InvalidDependency")
        return self


class ComponentScope(FrozenModel):
    kind: Literal["component"]
    operator_version: Literal["prepared-op/1"]
    ops: Annotated[tuple[PreparedOp, ...], Field(min_length=1, max_length=16)]
    op_ids: tuple[NonEmpty, ...]
    repeat: Literal[1]

    @model_validator(mode="before")
    @classmethod
    def strict_literal_type(cls, value: Any) -> Any:
        if isinstance(value, dict) and "repeat" in value:
            require(type(value["repeat"]) in (int,), "UnsupportedScope", "strict repeat")
        return value


class ModelScope(FrozenModel):
    kind: Literal["prepared_model"]
    selected_point_hashes: Annotated[tuple[Hash, ...], Field(min_length=1)]


class KernelScope(FrozenModel):
    kind: Literal["kernel_fixture"]
    owner_ids: Annotated[tuple[U64, ...], Field(min_length=1)]


class TransportScope(FrozenModel):
    kind: Literal["transport_fixture"]


Scope = Annotated[
    ComponentScope | ModelScope | KernelScope | TransportScope, Field(discriminator="kind")
]
Source = Annotated[PreparedBundle | PreparedBundleV2, Field(discriminator="format")]


class ComponentIdentity(FrozenModel):
    kind: Literal["component"]
    op_ids: tuple[NonEmpty, ...]


class ModelPointIdentity(FrozenModel):
    kind: Literal["prepared_model"]
    original_point_hash: Hash
    query: Query


class FixtureIdentity(FrozenModel):
    kind: Literal["fixture"]
    fixture_id: NonEmpty


class MappedAssumptions(FrozenModel):
    format: Literal["uarch-mapped-assumptions/1"]
    assumptions_hash: Hash
    semantics_revision: Literal["U0011-stage2/1"]
    owner_enumeration: Literal["native-owners/1"]
    arbitration: Literal["fifo-ready/1"]
    hbm_addressing: Literal["stripe256-channel8-controller-pairs/1"]
    bank_placement: Literal["contiguous-equal-regions/1"]
    compute: Literal["ws-stage-overhead-wave-drain/1"]
    transport: Literal["E4-named-edges-rational-service/2"]
    limitations: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def identity_check(self) -> MappedAssumptions:
        verify_identity(self, "assumptions_hash")
        return self


class OriginalV1Source(FrozenModel):
    format: Literal["uarch-prepared/1"]
    bundle_hash: Hash
    bundle: PreparedBundle
    assumptions: AssumptionSet


class OriginalV2Source(FrozenModel):
    format: Literal["uarch-prepared/2"]
    bundle_hash: Hash
    bundle: PreparedBundleV2
    assumptions: AssumptionSet


OriginalSource = Annotated[OriginalV1Source | OriginalV2Source, Field(discriminator="format")]


class MappedPoint(FrozenModel):
    payload_hash: Hash
    point_id: NonEmpty
    identity: Annotated[
        ComponentIdentity | ModelPointIdentity | FixtureIdentity, Field(discriminator="kind")
    ]
    frequency_ratio: Ratio
    initial_state: State
    priming_iterations: U64
    task_graph: TaskGraph

    @model_validator(mode="after")
    def identity_check(self) -> MappedPoint:
        verify_identity(self, "payload_hash")
        return self


class MappedBundle(FrozenModel):
    format: Literal["uarch-prepared/3"]
    bundle_hash: Hash
    producer: Producer
    hardware_spec: HardwareSpec
    hardware_spec_hash: Hash
    assumptions_hash: Hash
    rank: RankScope
    mapping_scope: Literal["task_graph"]
    mapping_policy: MappingPolicy
    scope: Scope
    source: OriginalSource | None
    assumptions: MappedAssumptions
    admission: Admission
    points: Annotated[tuple[MappedPoint, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def closure(self) -> MappedBundle:
        verify_identity(self, "bundle_hash")
        require(self.assumptions_hash == self.assumptions.assumptions_hash, "ContentHashMismatch")
        require(spec_hash(self.hardware_spec) == self.hardware_spec_hash, "HardwareMismatch")
        ordered(self.points, lambda x: x.point_id, "MissingCoverage")
        if isinstance(self.scope, ModelScope):
            require(self.source is not None, "MissingClosure")
            assert self.source is not None
            original = self.source.bundle
            verify_identity(original, "bundle_hash")
            verify_identity(self.source.assumptions, "assumptions_hash")
            require(
                self.source.bundle_hash == original.bundle_hash
                and self.source.assumptions.assumptions_hash == original.intent.assumptions_hash,
                "ContentHashMismatch",
            )
            require(content_hash(original.intent) == original.intent_hash, "ContentHashMismatch")
            require(
                spec_hash(original.hardware_spec) == original.intent.hardware_spec_hash,
                "HardwareMismatch",
            )
            if isinstance(original, PreparedBundleV2):
                coefficient_hash = original.coefficients.coefficients_hash
                require(
                    original.intent.position_encoding.coefficients_hash == coefficient_hash,
                    "CoefficientHashMismatch",
                )
                for source_point_v2 in original.points:
                    require(
                        source_point_v2.graph.kv_key_encoding == original.intent.position_encoding,
                        "CoefficientHashMismatch",
                    )
                    for group in source_point_v2.graph.groups:
                        for op in group.ops:
                            if op.rotary is not None:
                                require(
                                    op.rotary.coefficients_hash == coefficient_hash,
                                    "CoefficientHashMismatch",
                                )
            for source_point in original.points:
                verify_identity(source_point, "payload_hash")
            selected = {p.payload_hash: p for p in original.points}
            require(set(self.scope.selected_point_hashes) <= selected.keys(), "MissingCoverage")
            require(
                len(set(self.scope.selected_point_hashes)) == len(self.scope.selected_point_hashes),
                "MissingCoverage",
            )
            require(
                {
                    p.identity.original_point_hash
                    for p in self.points
                    if isinstance(p.identity, ModelPointIdentity)
                }
                == set(self.scope.selected_point_hashes),
                "MissingCoverage",
            )
            for p in self.points:
                require(isinstance(p.identity, ModelPointIdentity), "MissingCoverage")
                assert isinstance(p.identity, ModelPointIdentity)
                require(
                    p.identity.query == selected[p.identity.original_point_hash].query,
                    "MissingCoverage",
                )
        else:
            require(self.source is None, "UnexpectedClosure")
        if isinstance(self.scope, ComponentScope):
            require(self.scope.op_ids == tuple(op.id for op in self.scope.ops), "InvalidCoverage")
            ordered(self.scope.ops, lambda x: x.id, "InvalidCoverage")
            for p in self.points:
                require(
                    isinstance(p.identity, ComponentIdentity)
                    and p.identity.op_ids == self.scope.op_ids,
                    "InvalidCoverage",
                )
        return self


class Frequencies(FrozenModel):
    core: Positive
    noc: Positive
    dram: Positive


class ProfileEntry(FrozenModel):
    case_id: NonEmpty
    checkpoint: Literal["K2", "B"]
    scope: ScopeName
    initial_state: State
    priming_iterations: U64
    hardware_spec_hash: Hash
    hardware_spec: HardwareSpec
    frequency_ratio: Ratio
    freq_hz: Frequencies
    graph_hash: Hash
    point_hash: Hash
    allowed_job_kinds: tuple[JobKind, ...]
    clock_setup_hash: Hash
    expected_outcome: Literal[
        "success",
        "UnsupportedProtocol",
        "UnsupportedWorkloadScope",
        "UnsupportedPrecision",
        "UnsupportedRankScope",
        "UnsupportedOperator",
        "InvalidOperatorSchema",
        "UnsupportedInitialState",
        "UnsupportedShape",
        "UnsupportedScope",
        "UnsupportedMapping",
        "SramCapacityExceeded",
        "LiveBufferAlias",
        "InvalidResource",
        "InvalidRoute",
        "InvalidTransfer",
        "InvalidDependency",
        "InvalidCoverage",
        "ContentHashMismatch",
        "CoefficientHashMismatch",
        "HardwareMismatch",
        "MissingCoverage",
        "TestOnlyScope",
        "IncompleteExecution",
        "UnsupportedFidelity",
        "UnsupportedHardware",
        "UnsupportedCapability",
        "IncompleteObservations",
        "UnsupportedFrequency",
        "TimeOverflow",
        "TestProfileMismatch",
        "TestVariantNotAdmitted",
        "UnsupportedCheckpointScope",
        "TestOnlyHardware",
        "AdmissionMismatch",
        "CapacityExceeded",
        "InvalidBank",
    ]
    seed: U64
    case_selection_revision: NonEmpty


class NativeTestProfile(FrozenModel):
    format: Literal["uarch-native-test-profile/1"]
    profile_hash: Hash
    semantics_revision: Literal["U0011-stage2/1"]
    owner: NonEmpty
    entries: Annotated[tuple[ProfileEntry, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def identities(self) -> NativeTestProfile:
        verify_identity(self, "profile_hash")
        ordered(self.entries, lambda x: x.case_id, "TestProfileMismatch")
        for entry in self.entries:
            require(spec_hash(entry.hardware_spec) == entry.hardware_spec_hash, "HardwareMismatch")
            ordered(entry.allowed_job_kinds, lambda x: x, "TestProfileMismatch")
            require(
                entry.freq_hz == resolve_frequencies(entry.hardware_spec, entry.frequency_ratio),
                "TestVariantNotAdmitted",
            )
            require(
                "*" not in entry.case_id and "*" not in entry.expected_outcome,
                "TestProfileMismatch",
            )
        return self


class RegistryEntry(FrozenModel):
    hardware_spec_hash: Hash
    rationale: NonEmpty


class NativeTestRegistry(FrozenModel):
    format: Literal["uarch-native-test-registry/1"]
    registry_hash: Hash
    semantics_revision: Literal["U0011-stage2/1"]
    test_only_specs: tuple[RegistryEntry, ...]

    @model_validator(mode="after")
    def identities(self) -> NativeTestRegistry:
        verify_identity(self, "registry_hash")
        ordered(self.test_only_specs, lambda x: x.hardware_spec_hash, "TestProfileMismatch")
        require(
            PRODUCTION_HARDWARE not in {x.hardware_spec_hash for x in self.test_only_specs},
            "TestProfileMismatch",
            "baseline is not test-only hardware",
        )
        return self


def resolve_frequencies(spec: HardwareSpec, ratio: float) -> Frequencies:
    raw = spec.model_dump(mode="json")["clock_domains"]
    values = {}
    for name in ("core", "noc", "dram"):
        leaf = raw[name]
        value = Fraction(str(leaf["freq_hz"]["value"]))
        if leaf["scales_with_core"]:
            value *= Fraction(str(ratio))
        require(value.denominator == 1 and value > 0, "UnsupportedFrequency")
        values[name] = int(value)
    return Frequencies.model_validate(values)


class RationalValue(FrozenModel):
    numerator: Annotated[int, Field(strict=True, ge=0, lt=2**128)]
    denominator: Annotated[int, Field(strict=True, ge=1, lt=2**128)]

    @model_validator(mode="after")
    def reduced(self) -> RationalValue:
        from math import gcd

        require(gcd(self.numerator, self.denominator) == 1, "InvalidRatio")
        return self


class NumericLeaf(FrozenModel):
    path: NonEmpty
    value: RationalValue | StrictInt | StrictStr | StrictBool | None


class ResolvedMappedHardware(FrozenModel):
    """Complete scalar projection; includes source metadata, never implicit numeric defaults."""

    format: Literal["uarch-resolved-hardware/1"]
    hardware_spec_hash: Hash
    leaves: tuple[NumericLeaf, ...]


def hardware_projection(spec: HardwareSpec) -> ResolvedMappedHardware:
    leaves: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                walk(child, path + "/" + key.replace("~", "~0").replace("/", "~1"))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + "/" + str(index))
        else:
            if isinstance(value, float):
                ratio = Fraction(str(value))
                value = {"numerator": ratio.numerator, "denominator": ratio.denominator}
            leaves.append({"path": path, "value": value})

    walk(spec.model_dump(mode="json"), "")
    return ResolvedMappedHardware.model_validate(
        {
            "format": "uarch-resolved-hardware/1",
            "hardware_spec_hash": spec_hash(spec),
            "leaves": leaves,
        }
    )


class NativeModelIdentity(FrozenModel):
    name: Literal["fixed-delay", "native-intervals"]
    version: Literal["1"]
    implementation_hash: Hash


class NativeEngineIdentity(FrozenModel):
    name: Literal["native"]
    version: Literal["native-stage/1"]
    implementation_hash: Hash
    model: NativeModelIdentity
    compiler_lock_hash: Hash


class NativeFidelity(FrozenModel):
    compute: Literal[1]
    noc: Literal[0]
    dram: Literal[0]
    sync: Literal["exact"]
    layer_reuse: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def strict_levels(cls, value: Any) -> Any:
        if isinstance(value, dict):
            require(
                all(type(value.get(k)) is int for k in ("compute", "noc", "dram"))
                and type(value.get("layer_reuse")) is bool,
                "UnsupportedFidelity",
            )
        return value


class ClockSetup(FrozenModel):
    job_id: NonEmpty
    domain: Literal["core", "noc", "dram"]
    start_ps: U64
    n_cycles: U64


class Owner(FrozenModel):
    owner_id: U64
    resource: NonEmpty


class MappedEngineJob(FrozenModel):
    protocol: Literal["uarch-engine/3"]
    job_hash: Hash
    bundle_hash: Hash
    point_hash: Hash
    request_hash: Hash | None
    assumptions_hash: Hash
    engine: NativeEngineIdentity
    mapped_point: MappedPoint
    workload_closure: MappedBundle
    assumptions: MappedAssumptions
    hardware: ResolvedMappedHardware
    hardware_spec_hash: Hash
    rank: RankScope
    precision: Literal["bf16"] | None
    fidelity_detail: NativeFidelity | None
    frequency_ratio: Ratio
    freq_hz: Frequencies
    initial_state: State
    priming_iterations: U64
    seed: U64
    admission: Admission
    state_model: Literal["resource_intervals/1", "fixed_delay/1"]
    clock_setup: tuple[ClockSetup, ...]
    owner_enumeration: Literal["native-owners/1"]
    owners: tuple[Owner, ...]
    registry: NativeTestRegistry
    profile: NativeTestProfile | None

    @model_validator(mode="after")
    def closure(self) -> MappedEngineJob:
        verify_identity(self, "job_hash")
        b, p = self.workload_closure, self.mapped_point
        require(
            self.bundle_hash == b.bundle_hash
            and self.point_hash == p.payload_hash
            and p in b.points
            and self.assumptions_hash == b.assumptions_hash
            and self.assumptions == b.assumptions,
            "ContentHashMismatch",
        )
        require(
            self.hardware_spec_hash == b.hardware_spec_hash
            and self.hardware == hardware_projection(b.hardware_spec),
            "HardwareMismatch",
        )
        require(self.rank == b.rank and self.admission == b.admission, "AdmissionMismatch")
        require(
            self.frequency_ratio == p.frequency_ratio
            and self.initial_state == p.initial_state
            and self.priming_iterations == p.priming_iterations,
            "AdmissionMismatch",
        )
        require(
            self.freq_hz == resolve_frequencies(b.hardware_spec, p.frequency_ratio),
            "UnsupportedFrequency",
        )
        if self.profile is not None:
            entries = [e for e in self.profile.entries if e.case_id == self.admission.case_id]
            require(
                len(entries) == 1
                and entries[0].clock_setup_hash
                == content_hash([x.model_dump(mode="json") for x in self.clock_setup]),
                "TestProfileMismatch",
                "job-only clock setup",
            )
        fixed = b.scope.kind == "kernel_fixture"
        require(
            self.state_model == ("fixed_delay/1" if fixed else "resource_intervals/1"),
            "UnsupportedFidelity",
        )
        require(
            (self.fidelity_detail is None) == fixed
            and self.engine.model.name == ("fixed-delay" if fixed else "native-intervals"),
            "UnsupportedFidelity",
        )
        require(self.request_hash is None, "UnsupportedWorkloadScope")
        require(self.precision == (None if fixed else "bf16"), "UnsupportedPrecision")
        ordered(self.owners, lambda x: x.owner_id, "InvalidResource")
        ordered(self.clock_setup, lambda x: x.job_id, "InvalidResource")
        if fixed:
            assert isinstance(b.scope, KernelScope)
            require(tuple(x.owner_id for x in self.owners) == b.scope.owner_ids, "InvalidResource")
            require(
                {x.job_id for x in self.clock_setup} <= {j.id for j in p.task_graph.jobs},
                "InvalidResource",
            )
        else:
            require(
                self.owners == canonical_owners(b.hardware_spec, p.task_graph), "InvalidResource"
            )
            require(not self.clock_setup, "TestOnlyScope")
        admit(
            b,
            invocation=self.admission.invocation,
            checkpoint=self.admission.checkpoint,
            registry=self.registry,
            profile=self.profile,
            point_hash=self.point_hash,
            seed=self.seed,
            trusted_registry_hash=self.registry.registry_hash,
            trusted_profile_hash=None if self.profile is None else self.profile.profile_hash,
        )
        return self


class NativeCounts(Counts):
    @model_validator(mode="before")
    @classmethod
    def exact_numbers(cls, value: Any) -> Any:
        if isinstance(value, dict):
            require(
                all(x is None or type(x) in (int, float) for x in value.values()), "InvalidCount"
            )
        return value


class NativeExtCounts(ExtCounts):
    @model_validator(mode="before")
    @classmethod
    def exact_numbers(cls, value: Any) -> Any:
        if isinstance(value, dict):
            require(
                all(x is None or type(x) in (int, float) for x in value.values()), "InvalidCount"
            )
        return value


class WorkCounts(FrozenModel):
    format: Literal["uarch-native-work-counts/1"]
    completed_mac_count: U64
    issued_matrix_ops: U64
    vector_arithmetic_ops: U64
    cast_ops: U64


class TrafficCounts(FrozenModel):
    format: Literal["uarch-native-traffic-counts/1"]
    read_payload_bytes: U64
    write_payload_bytes: U64
    read_transaction_bytes: U64
    write_transaction_bytes: U64
    unicast_payload_bytes: U64


class EventObservation(FrozenModel):
    event_seq: U64
    observation_ordinal: U64
    t_ps: U64
    phase: Annotated[int, Field(strict=True, ge=0, le=3)]
    target_id: U64
    kind: Literal[
        "TASK_READY",
        "COMPUTE_DONE",
        "DMA_ISSUE",
        "DMA_DONE",
        "NOC_HEAD",
        "NOC_TAIL",
        "MEM_REQ",
        "MEM_RESP",
        "MEM_TICK",
        "SYNC_ARRIVE",
        "BARRIER_RELEASE",
        "STAT_SAMPLE",
        "END",
    ]
    job_id: NonEmpty | None


class JobObservation(FrozenModel):
    job_id: NonEmpty
    op_id: NonEmpty | None
    group_id: NonEmpty | None
    repeat_index: U64 | None
    tile_origin: Tile | None
    tile_extents: Extent | None
    ready_ps: U64
    start_ps: U64
    end_ps: U64
    owner_id: U64
    blocking_predecessor_ids: tuple[NonEmpty, ...]
    useful_matrix_ops: U64
    issued_matrix_ops: U64
    vector_arithmetic_ops: U64
    cast_ops: U64


class DmaObservation(FrozenModel):
    request_id: NonEmpty
    job_id: NonEmpty
    dma_engine_id: U64 | None
    direction: Literal["read", "write", "unicast"]
    source_buffer_id: NonEmpty
    destination_buffer_id: NonEmpty
    payload_bytes: U64
    transaction_bytes: U64
    credit_acquire_ps: U64 | None
    issue_ps: U64
    complete_ps: U64
    credit_release_ps: U64 | None
    route_id: NonEmpty


class TransferObservation(FrozenModel):
    request_id: NonEmpty
    boundary_id: NonEmpty
    direction: Literal["read", "write", "unicast"]
    payload_bytes: U64
    transaction_bytes: U64
    enter_ps: U64
    leave_ps: U64


class AllocationObservation(FrozenModel):
    buffer_id: NonEmpty
    space: Literal["hbm", "sram", "accumulator"]
    owner_id: U64
    offset_bytes: U64
    size_bytes: U64
    allocate_ps: U64
    free_ps: U64 | None
    initially_live: StrictBool
    last_consumer_ids: tuple[NonEmpty, ...]


class QueueObservation(FrozenModel):
    queue_id: NonEmpty
    item_id: NonEmpty
    population: Literal["waiting", "service", "inflight"]
    enter_ps: U64
    leave_ps: U64 | None
    owner_id: U64
    clock_domain: Literal["core", "noc", "dram"]


class TimeRatio(RationalValue):
    @model_validator(mode="after")
    def reduced(self) -> TimeRatio:
        from math import gcd

        require(gcd(self.numerator, self.denominator) == 1, "InvalidRatio")
        return self


class ResourceInterval(FrozenModel):
    owner_id: U64
    job_id: NonEmpty
    start_ps: U64
    end_ps: U64
    activity: NonEmpty
    limiting_resource_id: U64
    service_start_ps_ratio: TimeRatio | None
    service_end_ps_ratio: TimeRatio | None


class CriticalInterval(FrozenModel):
    start_ps: U64
    end_ps: U64
    cause_job_id: NonEmpty
    predecessor_id: NonEmpty | None
    limiting_resource_id: U64
    category: Literal["compute", "memory", "noc", "sync", "overhead"]


class Observed[T](FrozenModel):
    status: Literal["observed"]
    records: tuple[T, ...]


class Unrepresented(FrozenModel):
    status: Literal["unrepresented"]
    reason: NonEmpty


class Observations(FrozenModel):
    format: Literal["uarch-native-observations/1"]
    events: Observed[EventObservation]
    jobs: Observed[JobObservation]
    dma: Annotated[Observed[DmaObservation] | Unrepresented, Field(discriminator="status")]
    transfers: Annotated[
        Observed[TransferObservation] | Unrepresented, Field(discriminator="status")
    ]
    allocations: Annotated[
        Observed[AllocationObservation] | Unrepresented, Field(discriminator="status")
    ]
    queue_membership: Annotated[
        Observed[QueueObservation] | Unrepresented, Field(discriminator="status")
    ]
    resource_intervals: Observed[ResourceInterval]
    critical_path: Observed[CriticalInterval]


class Attribution(FrozenModel):
    compute: U64
    memory: U64
    noc: U64
    sync: U64
    overhead: U64


class NativeDiagnostics(FrozenModel):
    matrix_util_ratio: Annotated[JsonFloat, Field(ge=0, le=1)] | None
    vector_util_ratio: None
    dma_compute_overlap_ratio: Annotated[JsonFloat, Field(ge=0, le=1)] | None
    sram_bank_conflict_stall_ratio: None
    noc_latency_p50_ps: U64 | None
    noc_latency_p99_ps: U64 | None
    noc_max_link_util_ratio: None
    dram_bw_util_ratio: Annotated[JsonFloat, Field(ge=0, le=1)] | None
    dram_row_hit_ratio: None
    energy_pj: None


class SimulatorMetrics(FrozenModel):
    event_count: U64
    completed_job_count: U64
    max_live_events: U64


class PerOp(FrozenModel):
    op_id: NonEmpty
    counts: NativeCounts
    ext_counts: NativeExtCounts
    work_counts: WorkCounts
    traffic_counts: TrafficCounts


class BusyTime(FrozenModel):
    owner_id: U64
    busy_time_ps: U64


class MappedEngineResult(FrozenModel):
    protocol: Literal["uarch-engine/3"]
    result_hash: Hash
    job_hash: Hash
    engine: NativeEngineIdentity
    scope: ScopeName
    completion: Literal["complete"]
    duration_ps: U64
    completed_jobs: tuple[NonEmpty, ...]
    admission: Admission
    counts: NativeCounts
    ext_counts: NativeExtCounts
    work_counts: WorkCounts
    traffic_counts: TrafficCounts
    per_op: tuple[PerOp, ...]
    busy_time_ps: tuple[BusyTime, ...]
    attribution_ps: Attribution
    diagnostics: NativeDiagnostics
    fidelity_detail: NativeFidelity | None
    unrepresented: tuple[NonEmpty, ...]
    simulator_metrics: SimulatorMetrics
    trace_hash: Hash | None
    u_c0_duration_ps: None
    observations: Observations
    owners: tuple[Owner, ...]

    @model_validator(mode="after")
    def counts_and_identity(self) -> MappedEngineResult:
        verify_identity(self, "result_hash")
        ordered(self.completed_jobs, lambda x: x, "IncompleteExecution")
        ordered(self.unrepresented, lambda x: x, "IncompleteObservations")
        ordered(self.per_op, lambda x: x.op_id, "InvalidCoverage")
        ordered(self.busy_time_ps, lambda x: x.owner_id, "IncompleteObservations")
        require(
            self.counts.matrix_ops == 2 * self.work_counts.completed_mac_count
            and self.counts.vector_ops
            == self.work_counts.vector_arithmetic_ops + self.work_counts.cast_ops
            and self.counts.memory_read_bytes == self.traffic_counts.read_payload_bytes
            and self.counts.memory_write_bytes == self.traffic_counts.write_payload_bytes,
            "CountsMismatch",
        )
        require(self.ext_counts.noc_flit_hop_count is None, "UnsupportedFidelity")
        require(
            sum(self.attribution_ps.model_dump().values()) == self.duration_ps,
            "AttributionMismatch",
        )
        require(
            self.simulator_metrics.completed_job_count == len(self.completed_jobs),
            "IncompleteExecution",
        )
        return self


def validate_result(value: object, job: MappedEngineJob) -> MappedEngineResult:
    r = MappedEngineResult.model_validate(value)
    require(r.job_hash == job.job_hash and r.engine == job.engine, "ResultBindingMismatch")
    require(r.admission == job.admission, "AdmissionMismatch")
    require(
        r.fidelity_detail == job.fidelity_detail and r.scope == job.workload_closure.scope.kind,
        "UnsupportedFidelity",
    )
    require(r.owners == job.owners, "InvalidResource")
    ids = tuple(j.id for j in job.mapped_point.task_graph.jobs)
    require(r.completed_jobs == ids, "IncompleteExecution")
    require(tuple(j.job_id for j in r.observations.jobs.records) == ids, "IncompleteObservations")
    require(bool(r.observations.events.records), "IncompleteObservations")
    if job.state_model == "resource_intervals/1":
        for section in ("dma", "transfers", "allocations", "queue_membership"):
            require(getattr(r.observations, section).status == "observed", "IncompleteObservations")
    records = r.observations.jobs.records
    require(
        all(x.ready_ps <= x.start_ps <= x.end_ps <= r.duration_ps for x in records),
        "IncompleteObservations",
        "job time order",
    )
    require(
        r.counts.matrix_ops == sum(x.useful_matrix_ops for x in records)
        and r.work_counts.issued_matrix_ops == sum(x.issued_matrix_ops for x in records)
        and r.work_counts.vector_arithmetic_ops == sum(x.vector_arithmetic_ops for x in records)
        and r.work_counts.cast_ops == sum(x.cast_ops for x in records),
        "CountsMismatch",
    )
    owner_ids = {x.owner_id for x in job.owners}
    require({x.owner_id for x in r.busy_time_ps} == owner_ids, "IncompleteObservations")
    require(all(x.owner_id in owner_ids for x in records), "InvalidResource")
    require(
        all(
            e.target_id in owner_ids and e.t_ps <= r.duration_ps
            for e in r.observations.events.records
        ),
        "InvalidResource",
    )
    event_keys = [
        (x.t_ps, x.phase, x.target_id, x.event_seq, x.observation_ordinal)
        for x in r.observations.events.records
    ]
    # Inline zero closure remains in the current phase; ordinal records actual dispatch.
    require(
        len({x.observation_ordinal for x in r.observations.events.records}) == len(event_keys),
        "IncompleteObservations",
    )
    require(
        all(
            (a.t_ps, a.phase) <= (z.t_ps, z.phase)
            for a, z in zip(
                r.observations.events.records, r.observations.events.records[1:], strict=False
            )
        ),
        "IncompleteObservations",
        "time/phase regression",
    )
    cursor = 0
    category_totals = {key: 0 for key in Attribution.model_fields}
    for interval in r.observations.critical_path.records:
        require(
            interval.start_ps == cursor
            and interval.end_ps >= cursor
            and interval.cause_job_id in ids
            and interval.limiting_resource_id in owner_ids,
            "AttributionMismatch",
        )
        category_totals[interval.category] += interval.end_ps - interval.start_ps
        cursor = interval.end_ps
    require(
        cursor == r.duration_ps and category_totals == r.attribution_ps.model_dump(),
        "AttributionMismatch",
    )
    intervals = r.observations.resource_intervals.records
    for busy in r.busy_time_ps:
        pieces = sorted((x.start_ps, x.end_ps) for x in intervals if x.owner_id == busy.owner_id)
        total, end = 0, 0
        for start, stop in pieces:
            require(start <= stop <= r.duration_ps, "IncompleteObservations")
            total += max(0, stop - max(start, end))
            end = max(end, stop)
        require(total == busy.busy_time_ps, "IncompleteObservations", "busy interval union")
    if isinstance(r.observations.dma, Observed):
        dma = r.observations.dma.records
        ordered(dma, lambda x: x.request_id, "IncompleteObservations")
        declared = {
            f.request_id
            for j in job.mapped_point.task_graph.jobs
            if isinstance(j, Dma)
            for f in j.fragments
        }
        require(
            {x.request_id for x in dma if x.direction != "unicast"} == declared,
            "IncompleteExecution",
            "request inventory",
        )
        for direction in ("read", "write"):
            require(
                getattr(r.traffic_counts, direction + "_payload_bytes")
                == sum(x.payload_bytes for x in dma if x.direction == direction)
                and getattr(r.traffic_counts, direction + "_transaction_bytes")
                == sum(x.transaction_bytes for x in dma if x.direction == direction),
                "CountsMismatch",
            )
        require(
            all(x.issue_ps <= x.complete_ps <= r.duration_ps for x in dma), "IncompleteObservations"
        )
    return r


def admit(
    value: object,
    *,
    invocation: str,
    checkpoint: str,
    registry: object,
    profile: object | None,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    point_hash: str | None = None,
    hardware_hash: str | None = None,
    seed: int = 0,
    product: bool = False,
) -> MappedBundle:
    """Validate saved inputs; never remap, fetch data, run a producer or compute a duration."""
    b = MappedBundle.model_validate(value)
    reg = NativeTestRegistry.model_validate(registry)
    require(reg.registry_hash == trusted_registry_hash, "RegistryTrustMismatch")
    a = b.admission
    require(a.invocation == invocation and a.checkpoint == checkpoint, "AdmissionMismatch")
    if product:
        require(a.eligibility != "verification_only", "TestOnlyScope")
        require(False, "UnsupportedWorkloadScope", "components have no table/model row")
    if hardware_hash is not None:
        require(hardware_hash == b.hardware_spec_hash, "HardwareMismatch")
    points = (
        b.points
        if point_hash is None
        else tuple(p for p in b.points if p.payload_hash == point_hash)
    )
    require(bool(points), "MissingCoverage")
    require(b.scope.kind != "prepared_model", "UnsupportedWorkloadScope")
    if invocation == "production":
        require(
            b.hardware_spec_hash not in {x.hardware_spec_hash for x in reg.test_only_specs},
            "TestOnlyHardware",
        )
        require(checkpoint == "B" and b.scope.kind == "component", "UnsupportedCheckpointScope")
        require(b.hardware_spec_hash == PRODUCTION_HARDWARE, "UnsupportedHardware")
    else:
        require(profile is not None, "TestProfileMismatch")
        prof = NativeTestProfile.model_validate(profile)
        require(prof.profile_hash == a.profile_hash == trusted_profile_hash, "TestProfileMismatch")
        entries = [e for e in prof.entries if e.case_id == a.case_id]
        require(len(entries) == 1, "TestProfileMismatch")
        e = entries[0]
        require(len(points) == 1, "TestVariantNotAdmitted")
        p = points[0]
        require(
            (
                checkpoint,
                b.scope.kind,
                p.initial_state,
                p.priming_iterations,
                b.hardware_spec_hash,
                p.frequency_ratio,
                p.task_graph.graph_hash,
                p.payload_hash,
                seed,
            )
            == (
                e.checkpoint,
                e.scope,
                e.initial_state,
                e.priming_iterations,
                e.hardware_spec_hash,
                e.frequency_ratio,
                e.graph_hash,
                e.point_hash,
                e.seed,
            ),
            "TestVariantNotAdmitted",
        )
        require(
            {j.kind for j in p.task_graph.jobs} <= set(e.allowed_job_kinds),
            "TestVariantNotAdmitted",
        )
        require(
            e.expected_outcome == "success",
            "TestVariantNotAdmitted",
            "negative manifest is not admission",
        )
        if b.hardware_spec_hash != PRODUCTION_HARDWARE:
            require(
                b.hardware_spec_hash in {x.hardware_spec_hash for x in reg.test_only_specs},
                "TestProfileMismatch",
                "synthetic spec must be registered",
            )
    require(checkpoint != "K2" or b.scope.kind == "kernel_fixture", "UnsupportedCheckpointScope")
    for p in points:
        fixed = b.scope.kind == "kernel_fixture"
        states = (
            {"fixture_cold"}
            if fixed
            else ({"cold"} if invocation == "production" else {"cold", "fixture_resident"})
        )
        require(p.initial_state in states and p.priming_iterations == 0, "UnsupportedInitialState")
        if invocation == "production":
            require(
                p.frequency_ratio == 1
                and resolve_frequencies(b.hardware_spec, 1).model_dump()
                == {"core": 10**9, "noc": 10**9, "dram": 10**9},
                "UnsupportedFrequency",
            )
        if fixed:
            assert isinstance(b.scope, KernelScope)
            ordered(b.scope.owner_ids, lambda x: x, "InvalidResource")
            require(
                not p.task_graph.buffers and not p.task_graph.coverage and not p.task_graph.routes,
                "UnsupportedCheckpointScope",
            )
            require(
                all(
                    isinstance(j, FixedDelay) and j.owner_id in b.scope.owner_ids
                    for j in p.task_graph.jobs
                ),
                "UnsupportedCheckpointScope",
            )
        else:
            require(not any(isinstance(j, FixedDelay) for j in p.task_graph.jobs), "TestOnlyScope")
            validate_resources(b, p)
    return b


def validate_resources(b: MappedBundle, p: MappedPoint) -> None:
    g = p.task_graph
    raw = b.hardware_spec.model_dump(mode="json")
    core = raw["cores"]["core_type"]
    rows, cols = (int(raw["cores"]["grid"][x]["value"]) for x in ("rows", "cols"))
    ncores = rows * cols
    sram = int(core["sram"]["bytes"]["value"])
    bank_size = sram // int(core["sram"]["banks"]["value"])
    buffers = {x.id: x for x in g.buffers}
    jobs = {x.id: x for x in g.jobs}
    routes = {x.id: x for x in g.routes}
    ancestors: dict[str, set[str]] = {key: set() for key in jobs}
    for edge in g.dependencies:
        ancestors[edge.after].add(edge.before)
    for _ in jobs:
        for key in jobs:
            ancestors[key].update(set().union(*(ancestors[x] for x in tuple(ancestors[key]))))
    for buf in g.buffers:
        require(buf.offset_bytes % buf.alignment_bytes == 0, "InvalidResource", buf.id)
        require(buf.alignment_bytes == 256, "InvalidResource", "B aligned slot base")
        require(buf.producer_id is None or buf.producer_id in jobs, "InvalidDependency")
        require(set(buf.final_consumer_ids) <= jobs.keys(), "InvalidDependency")
        if buf.space == "hbm":
            require(buf.core_id is None and buf.bank is None, "InvalidResource")
            capacity = int(raw["memory"]["dram"]["capacity_bytes"]["value"])
        else:
            require(buf.core_id is not None and buf.core_id < ncores, "InvalidResource", buf.id)
            capacity = (
                sram
                if buf.space == "sram"
                else int(core["matrix_engine"]["accumulator_bytes"]["value"])
            )
        require(
            buf.offset_bytes + buf.size_bytes <= capacity,
            "SramCapacityExceeded" if buf.space == "sram" else "CapacityExceeded",
            f"{buf.id}: requested end {buf.offset_bytes + buf.size_bytes}; available {capacity}",
        )
        if buf.space == "sram":
            require(buf.bank == buf.offset_bytes // bank_size, "InvalidBank", buf.id)
            require(
                p.initial_state != "cold" or buf.initial_residency == "uninitialized",
                "UnsupportedInitialState",
            )
    readers: dict[str, set[str]] = {key: set() for key in buffers}
    for job in g.jobs:
        if isinstance(job, Compute):
            for name in ("X", "W"):
                buffer_key = job.operand_buffers.get(name)
                require(buffer_key in buffers, "InvalidResource")
                assert buffer_key is not None
                readers[buffer_key].add(job.id)
        elif isinstance(job, (Dma, NocTransfer)):
            require(job.source.buffer_id in buffers, "InvalidResource")
            readers[job.source.buffer_id].add(job.id)
    for key, buf in buffers.items():
        terminal = {j for j in readers[key] if not any(j in ancestors[k] for k in readers[key])}
        require(
            set(buf.final_consumer_ids) == terminal, "InvalidDependency", "final consumers " + key
        )
    for i, a in enumerate(g.buffers):
        for z in g.buffers[i + 1 :]:
            if (a.space, a.core_id) != (z.space, z.core_id):
                continue
            overlap = (
                a.offset_bytes < z.offset_bytes + z.size_bytes
                and z.offset_bytes < a.offset_bytes + a.size_bytes
            )
            if overlap:

                def ends_before(x: Buffer, y: Buffer) -> bool:
                    return (
                        bool(x.final_consumer_ids)
                        and y.producer_id is not None
                        and all(j in ancestors[y.producer_id] for j in x.final_consumer_ids)
                    )

                require(
                    ends_before(a, z) or ends_before(z, a), "LiveBufferAlias", a.id + "/" + z.id
                )
    for route in g.routes:
        require(
            route.noc_index == 0
            and route.source_core_id < ncores
            and route.destination_core_id < ncores,
            "InvalidResource",
        )
        current = route.source_core_id
        expected = [current]
        # XY dimension order: columns first, then rows.
        while current % cols != route.destination_core_id % cols:
            current += 1 if current % cols < route.destination_core_id % cols else -1
            expected.append(current)
        while current // cols != route.destination_core_id // cols:
            current += cols if current < route.destination_core_id else -cols
            expected.append(current)
        require(tuple(expected) == route.core_ids, "InvalidRoute", route.id)
    ops: dict[str, PreparedOp] = {}
    if isinstance(b.scope, ComponentScope):
        require(
            b.rank.tp == 1 and b.rank.rank_index == 0 and b.rank.equivalent_ranks == (0,),
            "UnsupportedRankScope",
        )
        require(
            b.mapping_policy.name == "ws-rowsplit"
            and b.mapping_policy.version == "1"
            and b.mapping_policy.buffer_depth == 2,
            "UnsupportedMapping",
        )
        ops = {op.id: op for op in b.scope.ops}
        for op in b.scope.ops:
            require(op.spec.operator == "q_projection", "UnsupportedOperator", op.id)
            require(
                all(x.dtype == "bf16" for x in op.spec.operands.values()), "UnsupportedPrecision"
            )
            require(
                op.work_repeat == op.weight_copies == 1
                and not op.replication
                and op.fusion == "none"
                and op.kv_access is None
                and op.embedding_local_tokens is None,
                "UnsupportedCapability",
            )
            require(not op.padding, "UnsupportedShape")
            require(
                all(x.layout == "contiguous" for x in op.spec.operands.values()),
                "UnsupportedCapability",
            )
            validate_prepared_op(op)
            d = op.spec.dimensions
            require(
                1 <= d["M"] <= 1024 and 1 <= d["K"] <= 256 and 1 <= d["N"] <= 256,
                "UnsupportedShape",
            )
            require(
                set(op.depends_on) <= ops.keys() and op.id not in op.depends_on, "InvalidDependency"
            )
            tiles = sorted(
                (j for j in g.jobs if isinstance(j, Compute) and j.op_id == op.id),
                key=lambda j: j.tile_origin.M,
            )
            cursor = 0
            for tile in tiles:
                require(
                    tile.tile_origin == Tile(M=cursor, K=0, N=0)
                    and tile.tile_extents.K == d["K"]
                    and tile.tile_extents.N == d["N"]
                    and tile.tile_extents.M <= 256,
                    "InvalidCoverage",
                )
                cursor += tile.tile_extents.M
            require(cursor == d["M"], "InvalidCoverage", op.id)
    else:
        require(
            not g.coverage and not any(isinstance(j, Compute) for j in g.jobs),
            "UnsupportedCheckpointScope",
        )
    for op in ops.values():
        own_jobs = [j for j in g.jobs if getattr(j, "op_id", None) == op.id]
        for dependency in op.depends_on:
            previous = [j.id for j in g.jobs if getattr(j, "op_id", None) == dependency]
            roots = [j for j in own_jobs if not any(k.id in ancestors[j.id] for k in own_jobs)]
            require(
                bool(previous) and all(set(previous) <= ancestors[j.id] for j in roots),
                "InvalidDependency",
                "operator dependency closure",
            )
    request_ids: set[str] = set()
    for job in g.jobs:
        if isinstance(job, Compute):
            require(job.core_id < ncores, "InvalidResource")
            require(
                job.op_id in ops and job.group_id is None and job.repeat_index == 0,
                "InvalidCoverage",
            )
            require(
                job.engine == "matrix" and job.dataflow == "weight_stationary", "UnsupportedMapping"
            )
            require(
                job.operand_dtypes == {"X": "bf16", "W": "bf16", "Y": "bf16"},
                "UnsupportedPrecision",
            )
            require(set(job.operand_buffers) == {"X", "W", "Y"}, "InvalidCoverage")
            require(
                job.physical_extents == Extent(M=job.tile_extents.M, K=256, N=256),
                "UnsupportedShape",
            )
            require(job.accumulator_buffer_id in buffers, "InvalidResource")
            acc = buffers[job.accumulator_buffer_id]
            require(
                acc.space == "accumulator"
                and acc.core_id == job.core_id
                and acc.size_bytes == 4 * job.tile_extents.M * job.tile_extents.N,
                "CapacityExceeded",
            )
            sizes = {
                "X": 2 * job.tile_extents.M * job.tile_extents.K,
                "W": 2 * job.tile_extents.K * job.tile_extents.N,
                "Y": 2 * job.tile_extents.M * job.tile_extents.N,
            }
            require(
                sizes["X"] + sizes["W"] <= core["matrix_engine"]["operand_buffer_bytes"]["value"],
                "CapacityExceeded",
                "operand buffer",
            )
            require(all(key in buffers for key in job.operand_buffers.values()), "InvalidResource")
            slots = {buffers[key].slot_index for key in job.operand_buffers.values()}
            require(
                len(slots) == 1 and None not in slots,
                "InvalidResource",
                "one explicit input/output slot",
            )
            slot = next(iter(slots))
            assert slot is not None
            require(
                any(
                    buf.space == "sram"
                    and buf.core_id == job.core_id
                    and buf.slot_index == 1 - slot
                    and buf.operand is None
                    and buf.size_bytes >= sum(sizes.values())
                    for buf in g.buffers
                ),
                "CapacityExceeded",
                "second slot reservation missing",
            )
            for name, key in job.operand_buffers.items():
                require(key in buffers, "InvalidResource")
                buf = buffers[key]
                require(
                    buf.space == "sram"
                    and buf.core_id == job.core_id
                    and buf.size_bytes == sizes[name]
                    and buf.operand == name
                    and buf.op_id == job.op_id,
                    "InvalidCoverage",
                )
                if name != "Y":
                    require(
                        buf.initial_residency == "preloaded"
                        or buf.producer_id in ancestors[job.id],
                        "InvalidDependency",
                        "uninitialized operand",
                    )
                else:
                    require(buf.producer_id == job.id, "InvalidDependency")
        if isinstance(job, (Dma, NocTransfer)):
            require(
                job.source.buffer_id in buffers and job.destination.buffer_id in buffers,
                "InvalidResource",
            )
            src, dst = buffers[job.source.buffer_id], buffers[job.destination.buffer_id]
            for region, buf in ((job.source, src), (job.destination, dst)):
                require(
                    region.offset_bytes + region.size_bytes <= buf.size_bytes, "InvalidTransfer"
                )
            require(job.source.size_bytes == job.destination.size_bytes, "InvalidTransfer")
            require(
                src.initial_residency == "preloaded" or src.producer_id in ancestors[job.id],
                "InvalidDependency",
            )
            require(dst.producer_id == job.id, "InvalidDependency")
            if isinstance(job, Dma):
                require(
                    (src.space, dst.space)
                    == (("hbm", "sram") if job.direction == "read" else ("sram", "hbm")),
                    "InvalidTransfer",
                )
                local = dst if job.direction == "read" else src
                require(
                    job.dma_engine_id // int(core["dma"]["engines"]["value"]) == local.core_id,
                    "InvalidResource",
                )
                cursor = 0
                for fragment in job.fragments:
                    require(fragment.request_id not in request_ids, "InvalidTransfer")
                    request_ids.add(fragment.request_id)
                    require(fragment.route_id in routes, "InvalidRoute")
                    require(
                        fragment.source_offset_bytes == job.source.offset_bytes + cursor
                        and fragment.destination_offset_bytes
                        == job.destination.offset_bytes + cursor,
                        "InvalidTransfer",
                    )
                    address = (
                        src.offset_bytes + fragment.source_offset_bytes
                        if job.direction == "read"
                        else dst.offset_bytes + fragment.destination_offset_bytes
                    )
                    require(
                        fragment.channel_id == (address // 256) % 8
                        and address % 256 + fragment.payload_bytes <= 256,
                        "InvalidTransfer",
                    )
                    route = routes[fragment.route_id]
                    attach = raw["memory"]["controllers"][fragment.channel_id // 2]["attach"]
                    controller = attach[0] * cols + attach[1]
                    require(
                        route.source_core_id == local.core_id
                        and route.destination_core_id == controller,
                        "InvalidRoute",
                    )
                    cursor += fragment.payload_bytes
                require(cursor == job.source.size_bytes, "InvalidTransfer")
            else:
                require(src.space == dst.space == "sram" and src.id != dst.id, "InvalidTransfer")
                require(
                    job.route_id in routes and job.payload_bytes == job.source.size_bytes,
                    "InvalidRoute",
                )
                route = routes[job.route_id]
                require(
                    (route.source_core_id, route.destination_core_id) == (src.core_id, dst.core_id),
                    "InvalidRoute",
                )


def canonical_owners(spec: HardwareSpec, graph: TaskGraph) -> tuple[Owner, ...]:
    """Accepted dense owner class order, independent of JSON source field order."""
    raw = spec.model_dump(mode="json")
    rows, cols = (int(raw["cores"]["grid"][x]["value"]) for x in ("rows", "cols"))
    cores = range(rows * cols)
    engines = int(raw["cores"]["core_type"]["dma"]["engines"]["value"])
    resources = [f"{kind}:{core}" for kind in ("matrix", "vector", "sram") for core in cores]
    resources += [f"dma:{core}:{engine}" for core in cores for engine in range(engines)]
    resources += [f"dma_port:{core}" for core in cores]
    resources += [
        f"channel:{channel}" for channel in range(int(raw["memory"]["dram"]["channels"]["value"]))
    ]
    resources += [
        f"router:{noc}:{row}:{col}"
        for noc in range(len(raw["nocs"]))
        for row in range(rows)
        for col in range(cols)
    ]
    links = [
        (noc, a, z)
        for noc in range(len(raw["nocs"]))
        for a in cores
        for z in cores
        if abs(a // cols - z // cols) + abs(a % cols - z % cols) == 1
    ]
    resources += [f"link:{noc}:{a}:{z}" for noc, a, z in links]
    resources += [f"barrier:{j.id}" for j in graph.jobs if isinstance(j, Barrier)]
    return tuple(Owner(owner_id=i, resource=name) for i, name in enumerate(resources))


def validate_job(
    value: object,
    *,
    invocation: str,
    checkpoint: str,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Launch admission needs host-owned anchors; model parsing alone is insufficient."""
    job = MappedEngineJob.model_validate(value)
    require(job.engine == expected_engine, "EngineIdentityMismatch")
    admit(
        job.workload_closure,
        invocation=invocation,
        checkpoint=checkpoint,
        registry=job.registry,
        profile=job.profile,
        point_hash=job.point_hash,
        seed=job.seed,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
    )
    return job


SCHEMA_ROOTS = (
    MappedAssumptions,
    MappedBundle,
    MappedPoint,
    TaskGraph,
    MappedEngineJob,
    MappedEngineResult,
    NativeTestProfile,
    NativeTestRegistry,
    ResolvedMappedHardware,
    WorkCounts,
    TrafficCounts,
    Observations,
)
