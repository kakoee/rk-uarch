"""ExecutionPlan — the HOW. Thin by design, and loud about what it does not model.

ADR 0002 §2. Fusion, tiling, layout, sparsity, kernel selection and placement are declared
and left unmodelled so their absence is visible rather than implied.

`precision` LEFT that list in ADR 0015 — it is now a real `Precision` object read by the
roofline, the KV sizing and the capacity gate. Its defaults are fp16/fp16, which is what
the engine hardcoded before, so the shape changed and no number did.

`placement` joined that list in ADR 0011 §2, closing finding F5. Until then it was the odd
one out: a `dict[str, str]` accepted silently, read by nothing, announced by nothing, while
its six siblings errored on being set. Two unmodelled mapping concerns, opposite treatment,
in the same class — and the validator's own rationale applied to it verbatim.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rk.schema.hashing import content_hash
from rk.schema.versions import VersionedInput

__all__ = [
    "DEFERRED_FIELDS",
    "Batching",
    "BatchingPolicy",
    "Collective",
    "EvictionPolicy",
    "ExecutionPlan",
    "KVPolicy",
    "Parallelism",
    "Precision",
    "PrecisionFormat",
]

PositiveInt = Annotated[int, Field(ge=1)]


class PrecisionFormat(StrEnum):
    """The numeric formats a plan may ask for. ADR 0015 §1.

    EXACTLY these eight. There is deliberately no FP64 member: rk-sim is an inference
    simulator and nothing in scope runs fp64, so a declared fp64 peak could be loaded and
    unit-checked and then never selected by any plan — a dead number in a library whose
    whole point is that numbers are accountable. Decided 2026-09-13, ADR 0015 §7.6 item 2.
    P3b asserts one peak-param name per member of this enum, which is what keeps the set
    and the library in agreement by construction rather than by care.

    `tf32` is 4 bytes. It is a 19-BIT FORMAT (1 sign + 8 exponent + 10 mantissa) held in a
    32-bit slot, so its saving is in the multiplier array and not in memory. It is the one
    a reader gets wrong, which is why it is called out here and in P3b's byte table.
    """

    FP32 = "fp32"
    TF32 = "tf32"
    BF16 = "bf16"
    FP16 = "fp16"
    FP8 = "fp8"
    INT8 = "int8"
    FP4 = "fp4"
    INT4 = "int4"


class Precision(BaseModel):
    """What the plan asks the hardware to compute in, and to store the KV cache in.

    Two fields, not one: `compute` moves the compute roof and the weight bytes together,
    `kv_cache` moves the memory roof's KV term on its own. ADR 0015's items 1 and 3 are
    separate for exactly that reason — either alone leaves one roof precision-blind.

    `compute` COVERS WEIGHTS AS WELL. A stack running fp8 GEMMs holds fp8 weights.
    W8A16 — quantized weights with higher-precision compute — is NOT modelled, and is
    recorded in ADR 0015 §1 as the first thing this shape would need to grow. It would be
    a third field here, not a redesign.

    Defaults are fp16/fp16, which is what `BYTES_PER_WEIGHT_FP16` and
    `BYTES_PER_KV_ELEM_FP16` hardcoded before P3b, so an existing plan resolves to the
    numbers it already produced.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    compute: PrecisionFormat = PrecisionFormat.FP16
    kv_cache: PrecisionFormat = PrecisionFormat.FP16


class BatchingPolicy(StrEnum):
    STATIC = "static"
    CONTINUOUS = "continuous"


class EvictionPolicy(StrEnum):
    NONE = "none"
    LRU = "lru"
    FIFO = "fifo"


class Parallelism(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tp: PositiveInt = 1
    pp: PositiveInt = 1
    ep: PositiveInt = 1
    dp: PositiveInt = 1


class Batching(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy: BatchingPolicy
    max_batch: PositiveInt
    max_tokens_in_flight: PositiveInt


class KVPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    block_size: PositiveInt
    placement_order: tuple[str, ...]
    eviction: EvictionPolicy
    prefix_reuse: bool

    @model_validator(mode="after")
    def _placement_is_declared(self) -> KVPolicy:
        if not self.placement_order:
            raise ValueError(
                "kv.placement_order must name at least one memory tier: KV blocks have "
                "to live somewhere, and leaving it empty hides a capacity decision."
            )
        return self


class Collective(BaseModel):
    """Names only, never costs. The cost is the fabric model's business (N0, P3)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allreduce: str
    alltoall: str


# Named in the IR so a reader can see they exist and are not modelled (build-spec §1.3).
DEFERRED_FIELDS: Final[tuple[str, ...]] = (
    "fusion",
    "tiling",
    "layout",
    "sparsity",
    "kernel_selection",
    "placement",
)


class ExecutionPlan(VersionedInput):
    """WHERE + **HOW** + WHAT. This is the HOW."""

    input_kind = "execution_plan"
    schema_version: Literal['1'] = '1'

    model_config = ConfigDict(frozen=True, extra="forbid")

    parallelism: Parallelism = Parallelism()
    batching: Batching
    kv: KVPolicy
    collective: Collective

    # Modelled as of ADR 0015, and defaulted so it moves nothing on its own. P3b wires it
    # into the roofline (`compute` picks the peak and the weight width), `kv_bytes`
    # (`kv_cache` picks the element width) and the M0 capacity gate.
    precision: Precision = Precision()

    # ---- Deferred. Declared so their absence is visible; setting one is an error. ----
    # `placement` keeps its eventual dict shape rather than collapsing to a string: the
    # field is deferred, not undesigned, and the type is what it will be when a model
    # reads it. `None` (not `{}`) is the unset state, so the validator below can tell
    # "no placement asked for" from "an empty placement asked for".
    placement: dict[str, str] | None = None
    fusion: str | None = None
    tiling: str | None = None
    layout: str | None = None
    sparsity: str | None = None
    kernel_selection: str | None = None

    @model_validator(mode="after")
    def _deferred_fields_are_unset(self) -> ExecutionPlan:
        """Accepting and ignoring these would let a config claim an effect that does not exist.

        A plan asking for fp8 and silently getting fp16 numbers produces an
        authoritative-looking answer to a different question. Sub-decision B, ADR 0003 §4.
        """
        for name in DEFERRED_FIELDS:
            if getattr(self, name) is not None:
                raise ValueError(
                    f"execution_plan.{name} is declared but not modelled in the prototype "
                    f"(deferred — build-spec §1.3). Setting it would imply an effect that "
                    f"does not exist. Leave it None."
                )
        return self

    @property
    def plan_hash(self) -> str:
        return content_hash(self)
