"""WorkloadSpec and ModelSpec — the WHAT.

Note what is *not* here: these fields are plain ints and floats, not SourcedValues.
The no-bare-floats invariant covers claims about the world — a hardware parameter
someone must have measured or sourced. `n_layers = 80` defines the run; it asserts
nothing about reality and has no provenance to carry.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rk.schema.agentic import AgenticProfile
from rk.schema.hashing import content_hash
from rk.schema.traces import TraceSelection
from rk.schema.versions import VersionedInput

__all__ = [
    "SLO",
    "AnalyticalPoint",
    "ModelSpec",
    "SyntheticGenerator",
    "WorkloadClass",
    "WorkloadSpec",
]

PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class WorkloadClass(StrEnum):
    CHAT = "chat"
    AGENTIC = "agentic"


class ModelSpec(BaseModel):
    """MoE is active-vs-total and nothing more (build-spec §2.3.5)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    total_params: PositiveInt
    active_params: PositiveInt
    n_experts: NonNegativeInt = 0
    experts_per_token: NonNegativeInt = 0
    n_layers: PositiveInt
    d_model: PositiveInt
    n_heads: PositiveInt
    kv_heads: PositiveInt

    @property
    def head_dim(self) -> int:
        """Exact by construction — the divisibility validator below guarantees it."""
        return self.d_model // self.n_heads

    @model_validator(mode="after")
    def _dimensions_are_coherent(self) -> ModelSpec:
        if self.active_params > self.total_params:
            raise ValueError(
                f"active_params ({self.active_params}) cannot exceed total_params "
                f"({self.total_params})"
            )
        if self.d_model % self.n_heads:
            raise ValueError(
                f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads}) "
                f"so head_dim is exact; every KV byte in the roofline depends on it"
            )
        if self.kv_heads > self.n_heads:
            raise ValueError(
                f"kv_heads ({self.kv_heads}) cannot exceed n_heads ({self.n_heads})"
            )
        if self.n_heads % self.kv_heads:
            raise ValueError(
                f"n_heads ({self.n_heads}) must be divisible by kv_heads "
                f"({self.kv_heads}); their ratio is the GQA sharing factor"
            )
        return self

    @model_validator(mode="after")
    def _moe_fields_agree(self) -> ModelSpec:
        if self.n_experts == 0:
            if self.active_params != self.total_params:
                raise ValueError(
                    "a dense model (n_experts=0) must have active_params == total_params; "
                    "if only some parameters are active, say how many experts there are"
                )
            if self.experts_per_token:
                raise ValueError("experts_per_token requires n_experts > 0")
        elif not 1 <= self.experts_per_token <= self.n_experts:
            raise ValueError(
                f"experts_per_token ({self.experts_per_token}) must be between 1 and "
                f"n_experts ({self.n_experts}) for an MoE model"
            )
        return self


class SyntheticGenerator(BaseModel):
    """Seeded synthetic request stream. Real traces arrive as `trace_ref` in P6."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: PositiveInt
    output_tokens: PositiveInt
    n_requests: PositiveInt
    arrival_rate_req_per_s: Annotated[float, Field(gt=0)]


class SLO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ttft_p99_ms: Annotated[float, Field(gt=0)] | None = None
    tpot_p99_ms: Annotated[float, Field(gt=0)] | None = None


class AnalyticalPoint(BaseModel):
    """Declared lengths for a trace run's analytical half; never inferred (ADR 0037)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: PositiveInt
    output_tokens: PositiveInt


class WorkloadSpec(VersionedInput):
    input_kind = "workload"
    schema_version: Literal['1'] = '1'

    model_config = ConfigDict(frozen=True, extra="forbid")

    workload_class: WorkloadClass
    model: ModelSpec
    trace_ref: str | None = None
    generator: SyntheticGenerator | None = None
    analytical_point: AnalyticalPoint | None = None
    # ADR 0044: omit absent additive selection to preserve pre-existing hashes.
    trace_selection: TraceSelection | None = Field(default=None, exclude_if=lambda v: v is None)
    slo: SLO = SLO()
    replications: PositiveInt = 1
    seed: int = 0
    agentic_profile: AgenticProfile | None = Field(default=None, exclude_if=lambda v: v is None)
    episode_horizon_s: Annotated[float, Field(gt=0, allow_inf_nan=False)] | None = Field(
        default=None, exclude_if=lambda v: v is None)

    @model_validator(mode='after')
    def _agentic_contract(self) -> WorkloadSpec:
        if self.workload_class is WorkloadClass.AGENTIC:
            # Legacy catalogue/mock declarations remain readable; execution/preflight
            # refuses them until P8b supplies a complete profile. Never run them as chat.
            if (self.agentic_profile is None) != (self.episode_horizon_s is None):
                raise ValueError('agentic_profile and episode_horizon_s must be supplied together')
        elif self.agentic_profile is not None or self.episode_horizon_s is not None:
            raise ValueError('chat workloads refuse agentic_profile and episode_horizon_s')
        return self

    @property
    def workload_hash(self) -> str:
        """Content address of the WHAT. A property, not a field — a hash cannot cover itself.

        The same mechanism `SystemConfig.config_hash` and `ExecutionPlan.plan_hash` use, and
        added at the S3→S4 boundary for the reason ADR 0036 §2 gives: a `RunResult` carried
        addresses for two of a run's three inputs, so a scenario edited only in its
        `workload:` section produced different numbers under an unchanged identity.
        """
        return content_hash(self)

    @model_validator(mode="after")
    def _exactly_one_request_source(self) -> WorkloadSpec:
        if (self.trace_ref is None) == (self.generator is None):
            raise ValueError(
                "a workload needs exactly one request source: set trace_ref or generator, "
                "not both and not neither"
            )
        return self

    @model_validator(mode="after")
    def _analytical_point_matches_source(self) -> WorkloadSpec:
        if self.trace_ref is not None and self.analytical_point is None:
            raise ValueError("analytical_point is required with trace_ref (ADR 0037)")
        if self.generator is not None and self.trace_selection is not None:
            raise ValueError("trace_selection is refused with generator")
        if self.generator is not None and self.analytical_point is not None:
            raise ValueError("analytical_point is refused with generator (ADR 0037)")
        return self

    @property
    def analytical_lengths(self) -> AnalyticalPoint | SyntheticGenerator:
        """The sole source of analytical lengths; DES requests retain their own lengths."""
        point = self.generator if self.generator is not None else self.analytical_point
        if point is None:
            raise ValueError("analytical_point is required with trace_ref (ADR 0037)")
        return point
