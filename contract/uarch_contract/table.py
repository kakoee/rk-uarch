"""One chip's shard, one iteration, all layers; never inter-chip collectives."""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from .common import (
    FrozenModel,
    Hash,
    JsonFloat,
    NonEmpty,
    reject_cycles,
)
from .common import (
    JsonNonNegativeFloat as NonNegativeFloat,
)
from .common import (
    JsonNonNegativeInt as NonNegativeInt,
)
from .common import (
    JsonPositiveFloat as PositiveFloat,
)
from .common import (
    JsonPositiveInt as PositiveInt,
)
from .common import (
    JsonRatio as Ratio,
)
from .errors import NonFiniteRow
from .fidelity import FidelityDetail
from .hardware import hardware_unit_rule
from .model_card import EmbeddedModelCard
from .request import KvLayout
from .sourced import SourcedValue

DECLARED_OMISSIONS = (
    "Host and runtime time outside the device is unmodelled.",
    "Address translation is unmodelled.",
    "Cache coherence is unmodelled.",
    "Mixed prefill/decode iterations are unmodelled.",
)
MOE_OMISSION = "MoE routing, imbalance and all-to-all are unmodelled."


class Diagnostics(FrozenModel):
    matrix_util_ratio: Ratio | None = None
    vector_util_ratio: Ratio | None = None
    dma_compute_overlap_ratio: Ratio | None = None
    sram_bank_conflict_stall_ratio: Ratio | None = None
    noc_latency_p50_s: NonNegativeFloat | None = None
    noc_latency_p99_s: NonNegativeFloat | None = None
    noc_max_link_util_ratio: Ratio | None = None
    dram_bw_util_ratio: Ratio | None = None
    dram_row_hit_ratio: Ratio | None = None


class Counts(FrozenModel):
    matrix_ops: NonNegativeFloat
    vector_ops: NonNegativeFloat | None
    memory_read_bytes: NonNegativeFloat
    memory_write_bytes: NonNegativeFloat | None


class ExtCounts(FrozenModel):
    sram_read_bytes: NonNegativeFloat | None
    sram_write_bytes: NonNegativeFloat | None
    noc_flit_hop_count: NonNegativeFloat | None


class Row(FrozenModel):
    """A row is one chip's shard, one iteration, all layers, without inter-chip collectives."""

    frequency_ratio: PositiveFloat
    duration_s: NonNegativeFloat
    u_c0_duration_s: NonNegativeFloat
    attribution_s: dict[Literal["compute", "memory", "noc", "sync", "overhead"], NonNegativeFloat]
    counts: Counts
    ext_counts: ExtCounts
    peak_resident_bytes: dict[Literal["hbm", "sram"], NonNegativeFloat | None]
    diagnostics: Diagnostics

    @model_validator(mode="before")
    @classmethod
    def finite_nonnegative(cls, data: Any) -> Any:
        def walk(value: Any) -> None:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not math.isfinite(value) or value < 0:
                    raise NonFiniteRow()
            elif isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, (tuple, list)):
                for child in value:
                    walk(child)

        walk(data)
        return data

    @model_validator(mode="after")
    def attribution(self) -> Row:
        if set(self.attribution_s) != {"compute", "memory", "noc", "sync", "overhead"}:
            raise ValueError("attribution_s requires compute, memory, noc, sync and overhead.")
        if not math.isclose(
            sum(self.attribution_s.values()), self.duration_s, rel_tol=1e-9, abs_tol=1e-15
        ):
            raise ValueError("attribution_s critical-path parts must sum to duration_s.")
        if set(self.peak_resident_bytes) != {"hbm", "sram"}:
            raise ValueError("peak_resident_bytes requires hbm and sram (null if unmodelled).")
        return self


class DecodeRow(Row):
    phase: Literal["decode"]
    batch: PositiveInt
    total_context_tokens: PositiveInt

    @model_validator(mode="after")
    def canonical_batch(self) -> DecodeRow:
        if self.total_context_tokens % self.batch:
            raise ValueError("Canonical decode total_context_tokens must be divisible by batch.")
        return self


class PrefillRow(Row):
    phase: Literal["prefill"]
    n_prompts: PositiveInt
    prompt_tokens: PositiveInt


class Interpolation(FrozenModel):
    decode: Literal["bilinear in (log B, log T); linear in 1/f"]
    prefill: Literal["bilinear in (log n, log L); linear in 1/f"]
    outside_grid: Literal["refuse"]


class SampledError(FrozenModel):
    median_rel: NonNegativeFloat | None
    max_rel: NonNegativeFloat | None
    n_samples: NonNegativeInt

    @model_validator(mode="after")
    def sampled(self) -> SampledError:
        if self.n_samples == 0:
            if self.median_rel is not None or self.max_rel is not None:
                raise ValueError("An unsampled error must be null, never zero.")
        elif self.median_rel is None or self.max_rel is None:
            raise ValueError("A sampled error requires median_rel and max_rel.")
        elif self.median_rel > self.max_rel:
            raise ValueError("median_rel must not exceed max_rel.")
        return self


class InterpolationError(SampledError):
    weighted_median_rel: NonNegativeFloat | None

    @model_validator(mode="after")
    def weighted_sample(self) -> InterpolationError:
        if self.n_samples == 0 and self.weighted_median_rel is not None:
            raise ValueError("An unsampled weighted error must be null, never zero.")
        return self


class CompositionError(FrozenModel):
    decode: SampledError
    prefill: SampledError
    n_samples: NonNegativeInt

    @model_validator(mode="after")
    def total_samples(self) -> CompositionError:
        if self.n_samples != self.decode.n_samples + self.prefill.n_samples:
            raise ValueError("composition_reduction.n_samples must equal decode plus prefill.")
        return self


class ColdVsSteadyError(SampledError):
    priming_2_vs_1_max_rel: NonNegativeFloat | None

    @model_validator(mode="after")
    def priming_sample(self) -> ColdVsSteadyError:
        if (self.n_samples == 0) != (self.priming_2_vs_1_max_rel is None):
            raise ValueError("priming_2_vs_1_max_rel is null exactly when unsampled.")
        return self


class MeasuredError(FrozenModel):
    interpolation_loo: InterpolationError
    composition_reduction: CompositionError
    layer_reuse: SampledError
    cold_vs_steady: ColdVsSteadyError


class FlopDeviation(FrozenModel):
    id: NonEmpty
    deviation_rel: Annotated[JsonFloat, Field(ge=-0.05, le=0.05)]
    reason: NonEmpty


class ParityChannelComparison(FrozenModel):
    """One successful fixture/channel comparison against a projected oracle count.

    Ratios use reference as denominator; positive adjustment means extra actual work.
    Arithmetic follows B's binary64 division and math.fsum, without widening its limits.
    The carrier verifies supplied arithmetic, not oracle/candidate authenticity.
    """

    fixture_id: NonEmpty
    channel: Literal["matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes"]
    unit: Literal["op", "byte"]
    actual: NonNegativeFloat | None
    reference: NonNegativeFloat | None
    reference_state: Literal["positive", "zero", "unmodelled"]
    raw_rel: JsonFloat | None
    signed_adjustment_rel: JsonFloat
    absolute_adjustment_rel: Annotated[NonNegativeFloat, Field(le=0.05)]
    residual_rel: Annotated[JsonFloat, Field(ge=-0.005, le=0.005)] | None
    declared_deviations: tuple[FlopDeviation, ...]

    @model_validator(mode="after")
    def consistent_comparison(self) -> ParityChannelComparison:
        expected_unit = "op" if self.channel in ("matrix_ops", "vector_ops") else "byte"
        if self.unit != expected_unit:
            raise ValueError(f"{self.channel} requires unit {expected_unit!r}.")
        ids = [item.id for item in self.declared_deviations]
        if len(set(ids)) != len(ids):
            raise ValueError("A fixture/channel must not repeat deviation ids.")
        signed = math.fsum(item.deviation_rel for item in self.declared_deviations)
        absolute = math.fsum(abs(item.deviation_rel) for item in self.declared_deviations)
        if absolute > 0.05:
            raise ValueError("Total absolute adjustments exceed 5% for this fixture/channel.")
        if self.signed_adjustment_rel != signed or self.absolute_adjustment_rel != absolute:
            raise ValueError("Reported signed/absolute adjustments disagree with declarations.")
        state = (
            "unmodelled"
            if self.reference is None
            else "zero"
            if self.reference == 0
            else "positive"
        )
        if self.reference_state != state:
            raise ValueError("reference_state disagrees with reference.")
        if self.reference is None or self.reference == 0:
            if self.actual != self.reference or self.declared_deviations:
                raise ValueError("Zero/null references require matching actual and no adjustments.")
            if self.raw_rel is not None or self.residual_rel is not None:
                raise ValueError("No positive denominator: raw_rel and residual_rel must be null.")
        else:
            if self.actual is None:
                raise ValueError("A positive reference requires a non-null actual count.")
            raw = (self.actual - self.reference) / self.reference
            residual = raw - signed
            if not math.isfinite(raw) or self.raw_rel != raw or self.residual_rel != residual:
                raise ValueError(
                    "raw_rel/residual_rel disagree with actual, reference or adjustments."
                )
            if self.declared_deviations and abs(raw) <= 0.005:
                raise ValueError("Unnecessary adjustments inside the 0.5% raw tolerance.")
            if abs(residual) > 0.005:
                raise ValueError("Residual exceeds 0.5% for this fixture/channel.")
        return self


class FlopParity(FrozenModel):
    """Explicit classification; self-tests never establish actual workload parity.

    All fields are required, including nullable identities. Manifest digests use B's
    raw 64-hex spelling, unlike hardware_spec_hash's sha256: prefix. External oracle,
    fixture completeness, projection eligibility and callable identity need B/U-P3 checks.
    """

    kind: Literal["not_run", "harness_self_test", "workload_parity"]
    reference_basis: Literal["rk_sim_aggregate_divided_by_tp"]
    fixture_set_id: NonEmpty | None
    oracle_manifest_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None
    candidate_identity: NonEmpty | None
    n_fixtures: NonNegativeInt
    max_rel: NonNegativeFloat | None
    comparisons: tuple[ParityChannelComparison, ...]

    @model_validator(mode="after")
    def consistent_summary(self) -> FlopParity:
        if self.kind == "not_run":
            if (
                self.comparisons
                or self.n_fixtures != 0
                or any(
                    value is not None
                    for value in (
                        self.max_rel,
                        self.fixture_set_id,
                        self.oracle_manifest_sha256,
                        self.candidate_identity,
                    )
                )
            ):
                raise ValueError(
                    "not_run requires no comparisons, zero fixtures and null identities/max."
                )
            return self
        if not self.comparisons or self.fixture_set_id is None or self.candidate_identity is None:
            raise ValueError("A run requires comparisons, fixture_set_id and candidate_identity.")
        if self.kind == "workload_parity" and self.oracle_manifest_sha256 is None:
            raise ValueError("workload_parity requires oracle_manifest_sha256.")
        pairs = {(item.fixture_id, item.channel) for item in self.comparisons}
        if len(pairs) != len(self.comparisons):
            raise ValueError("Duplicate fixture/channel comparison.")
        if self.n_fixtures != len({item.fixture_id for item in self.comparisons}):
            raise ValueError("n_fixtures disagrees with distinct comparison fixture ids.")
        raw = [abs(item.raw_rel) for item in self.comparisons if item.raw_rel is not None]
        if self.max_rel != (max(raw) if raw else None):
            raise ValueError(
                "max_rel must be the maximum absolute raw error, or null without a denominator."
            )
        return self


class Parameter(FrozenModel):
    name: NonEmpty
    value: SourcedValue


class Condition(FrozenModel):
    path: NonEmpty
    value: SourcedValue

    @model_validator(mode="after")
    def stipulated(self) -> Condition:
        if self.value.kind != "stipulation":
            raise ValueError("conditional_on requires a stipulation with its rationale.")
        allowed = hardware_unit_rule(self.path)
        if self.value.unit not in allowed:
            raise ValueError(
                f"{self.path}: supplied unit {self.value.unit!r}; allowed units {allowed!r}."
            )
        return self


class Provenance(FrozenModel):
    params: tuple[Parameter, ...]
    model_card: EmbeddedModelCard
    conditional_on: tuple[Condition, ...]

    @model_validator(mode="after")
    def unique_names(self) -> Provenance:
        if len({p.name for p in self.params}) != len(self.params):
            raise ValueError("provenance.params must not repeat parameter names.")
        return self


class UarchCostTable(FrozenModel):
    contract: Literal["uarch-contract/0.1"]
    uarch_version: NonEmpty
    hardware_spec_hash: Annotated[
        Hash, Field(description="Canonical HardwareSpec identity; contents verified by U-P3/U-P19.")
    ]
    request_hash: Hash
    table_hash: Hash
    tp: PositiveInt
    initial_state: Literal["steady", "cold"]
    kv_layout: KvLayout
    rows: Annotated[
        tuple[Annotated[DecodeRow | PrefillRow, Field(discriminator="phase")], ...],
        Field(min_length=1),
    ]
    interpolation: Interpolation
    measured_error: MeasuredError
    flop_parity: FlopParity
    composite_fidelity: Literal["C0", "C1", "C2"]
    fidelity_detail: FidelityDetail
    provenance: Provenance
    warnings: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def row_contract(self) -> UarchCostTable:
        # Only stipulated hardware input values are exempt; Condition checks kind/unit.
        # U-P3 must resolve the path/value against the actual referenced HardwareSpec.
        boundary = self.model_dump(
            mode="json", exclude={"provenance": {"conditional_on": {"__all__": {"value"}}}}
        )
        reject_cycles(boundary)
        if self.composite_fidelity != self.fidelity_detail.conservative_composite():
            raise ValueError("composite_fidelity disagrees with fidelity_detail.")
        keys: set[tuple[Any, ...]] = set()
        for row in self.rows:
            key = (
                (row.phase, row.batch, row.total_context_tokens, row.frequency_ratio)
                if isinstance(row, DecodeRow)
                else (row.phase, row.n_prompts, row.prompt_tokens, row.frequency_ratio)
            )
            if key in keys:
                raise ValueError(f"Duplicate row key {key}.")
            keys.add(key)
            if self.composite_fidelity == "C2" and row.duration_s < row.u_c0_duration_s:
                raise ValueError("A C2 duration_s must not be below its own u_c0_duration_s.")
        if not set(DECLARED_OMISSIONS).issubset(self.warnings):
            raise ValueError("warnings must include every declared contract omission.")
        return self
