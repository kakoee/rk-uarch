"""Ordinary component carriers /4: software versions and input/result provenance.

Historical /3 carriers remain strict and unchanged. This is a transport transition,
not a new workload IR: mapped points, TaskGraph, model laws and observations are shared.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from . import mapped as m
from .common import FrozenModel, Hash, NonEmpty
from .hardware import HardwareSpec
from .hashing import spec_hash, verify_identity
from .prepared import RankScope


class SoftwareProducer(FrozenModel):
    name: NonEmpty
    version: NonEmpty


class ModelVersion(FrozenModel):
    name: Literal["native-intervals"]
    version: Literal["2"]


class SoftwareIdentity(FrozenModel):
    name: Literal["native"]
    version: Literal["native-stage/2"]
    package_version: Literal["0.0.1"]
    model: ModelVersion


class OrdinaryAdmission(FrozenModel):
    checkpoint: Literal["B"]
    invocation: Literal["production", "test"]
    eligibility: Literal["component_only", "verification_only"]

    @model_validator(mode="after")
    def binding(self) -> OrdinaryAdmission:
        m.require(
            self.eligibility
            == ("verification_only" if self.invocation == "test" else "component_only"),
            "AdmissionMismatch",
        )
        return self


class OrdinaryBundle(FrozenModel):
    format: Literal["uarch-prepared/4"]
    bundle_hash: Hash
    producer: SoftwareProducer
    hardware_spec: HardwareSpec
    hardware_spec_hash: Hash
    assumptions_hash: Hash
    rank: RankScope
    mapping_scope: Literal["task_graph"]
    mapping_policy: m.MappingPolicy
    scope: Annotated[m.ComponentScope | m.TransportScope, Field(discriminator="kind")]
    source: None
    assumptions: m.MappedAssumptions
    admission: OrdinaryAdmission
    points: Annotated[tuple[m.MappedPoint, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def closure(self) -> OrdinaryBundle:
        verify_identity(self, "bundle_hash")
        m.require(self.assumptions_hash == self.assumptions.assumptions_hash, "ContentHashMismatch")
        m.require(spec_hash(self.hardware_spec) == self.hardware_spec_hash, "HardwareMismatch")
        m.ordered(self.points, lambda x: x.point_id, "MissingCoverage")
        if isinstance(self.scope, m.ComponentScope):
            m.require(self.scope.op_ids == tuple(op.id for op in self.scope.ops), "InvalidCoverage")
            m.ordered(self.scope.ops, lambda x: x.id, "InvalidCoverage")
            m.require(
                all(set(op.operand_access) == {"X", "W", "Y"} for op in self.scope.ops),
                "InvalidCoverage",
                "operand access",
            )
            for point in self.points:
                m.require(
                    isinstance(point.identity, m.ComponentIdentity)
                    and point.identity.op_ids == self.scope.op_ids,
                    "InvalidCoverage",
                )
        # The independent model-2 checker supports exactly these E3 overhead laws.
        m.require(
            self.hardware_spec.cores.core_type.job_overhead_cycles.value == 32
            and self.hardware_spec.sync.barrier_latency_cycles.value == 32,
            "UnsupportedHardware",
            "model-2 checker requires 32-cycle job overhead and barrier latency",
        )
        production = self.admission.invocation == "production"
        if production:
            m.require(self.scope.kind == "component", "UnsupportedCheckpointScope")
            # This is model/hardware capability, not human approval of a request.
            m.require(self.hardware_spec_hash == m.PRODUCTION_HARDWARE, "UnsupportedHardware")
        for point in self.points:
            m.require(
                point.initial_state in ({"cold"} if production else {"cold", "fixture_resident"})
                and point.priming_iterations == 0,
                "UnsupportedInitialState",
            )
            if production:
                m.require(
                    point.frequency_ratio == 1
                    and m.resolve_frequencies(self.hardware_spec, 1).model_dump()
                    == {"core": 10**9, "noc": 10**9, "dram": 10**9},
                    "UnsupportedFrequency",
                )
            m.require(
                not any(isinstance(j, m.FixedDelay) for j in point.task_graph.jobs), "TestOnlyScope"
            )
            m.validate_resources(self, point)
        return self


class OrdinaryJob(FrozenModel):
    protocol: Literal["uarch-engine/4"]
    job_hash: Hash
    bundle_hash: Hash
    point_hash: Hash
    request_hash: Hash | None
    assumptions_hash: Hash
    engine: SoftwareIdentity
    mapped_point: m.MappedPoint
    workload_closure: OrdinaryBundle
    assumptions: m.MappedAssumptions
    hardware: m.ResolvedMappedHardware
    hardware_spec_hash: Hash
    rank: RankScope
    precision: Literal["bf16"] | None
    fidelity_detail: m.NativeFidelity | None
    frequency_ratio: m.Ratio
    freq_hz: m.Frequencies
    initial_state: m.State
    priming_iterations: m.U64
    seed: m.U64
    admission: OrdinaryAdmission
    state_model: Literal["resource_intervals/1", "fixed_delay/1"]
    clock_setup: tuple[m.ClockSetup, ...]
    owner_enumeration: Literal["native-owners/1"]
    owners: tuple[m.Owner, ...]

    @model_validator(mode="after")
    def closure(self) -> OrdinaryJob:
        verify_identity(self, "job_hash")
        b, p = self.workload_closure, self.mapped_point
        m.require(
            self.bundle_hash == b.bundle_hash
            and self.point_hash == p.payload_hash
            and p in b.points
            and self.assumptions_hash == b.assumptions_hash
            and self.assumptions == b.assumptions,
            "ContentHashMismatch",
        )
        m.require(
            self.hardware_spec_hash == b.hardware_spec_hash
            and self.hardware == m.hardware_projection(b.hardware_spec),
            "HardwareMismatch",
        )
        m.require(self.rank == b.rank and self.admission == b.admission, "AdmissionMismatch")
        m.require(
            self.frequency_ratio == p.frequency_ratio
            and self.initial_state == p.initial_state
            and self.priming_iterations == p.priming_iterations,
            "AdmissionMismatch",
        )
        m.require(
            self.freq_hz == m.resolve_frequencies(b.hardware_spec, p.frequency_ratio),
            "UnsupportedFrequency",
        )
        m.require(
            self.state_model == "resource_intervals/1",
            "UnsupportedFidelity",
        )
        m.require(
            self.fidelity_detail is not None and self.engine.model.name == "native-intervals",
            "UnsupportedFidelity",
        )
        m.require(self.request_hash is None, "UnsupportedWorkloadScope")
        m.require(self.precision == "bf16", "UnsupportedPrecision")
        m.ordered(self.owners, lambda x: x.owner_id, "InvalidResource")
        m.ordered(self.clock_setup, lambda x: x.job_id, "InvalidResource")
        m.require(
            self.owners == m.canonical_owners(b.hardware_spec, p.task_graph), "InvalidResource"
        )
        m.require(not self.clock_setup, "TestOnlyScope")
        return self


class OrdinaryResult(FrozenModel):
    protocol: Literal["uarch-engine/4"]
    result_hash: Hash
    job_hash: Hash
    engine: SoftwareIdentity
    scope: Literal["component", "transport_fixture"]
    completion: Literal["complete"]
    duration_ps: m.U64
    completed_jobs: tuple[NonEmpty, ...]
    admission: OrdinaryAdmission
    counts: m.NativeCounts
    ext_counts: m.NativeExtCounts
    work_counts: m.WorkCounts
    traffic_counts: m.TrafficCounts
    per_op: tuple[m.PerOp, ...]
    busy_time_ps: tuple[m.BusyTime, ...]
    attribution_ps: m.Attribution
    diagnostics: m.NativeDiagnostics
    fidelity_detail: m.NativeFidelity | None
    unrepresented: tuple[NonEmpty, ...]
    simulator_metrics: m.SimulatorMetrics
    trace_hash: Hash | None
    u_c0_duration_ps: None
    observations: m.ComponentObservationsV3
    owners: tuple[m.Owner, ...]

    @model_validator(mode="after")
    def counts_and_identity(self) -> OrdinaryResult:
        verify_identity(self, "result_hash")
        m.ordered(self.completed_jobs, lambda x: x, "IncompleteExecution")
        m.ordered(self.unrepresented, lambda x: x, "IncompleteObservations")
        m.ordered(self.per_op, lambda x: x.op_id, "InvalidCoverage")
        m.ordered(self.busy_time_ps, lambda x: x.owner_id, "IncompleteObservations")
        m.require(
            self.counts.matrix_ops == 2 * self.work_counts.completed_mac_count
            and self.counts.vector_ops
            == self.work_counts.vector_arithmetic_ops + self.work_counts.cast_ops
            and self.counts.memory_read_bytes == self.traffic_counts.read_payload_bytes
            and self.counts.memory_write_bytes == self.traffic_counts.write_payload_bytes,
            "CountsMismatch",
        )
        m.require(self.ext_counts.noc_flit_hop_count is None, "UnsupportedFidelity")
        m.require(
            sum(self.attribution_ps.model_dump().values()) == self.duration_ps,
            "AttributionMismatch",
        )
        m.require(
            self.simulator_metrics.completed_job_count == len(self.completed_jobs),
            "IncompleteExecution",
        )
        return self


def validate_result(value: object, job: OrdinaryJob) -> OrdinaryResult:
    result = OrdinaryResult.model_validate(value)
    m.validate_result_semantics(result, job)
    return result
