"""Characterization of one chip's shard, for exactly one tensor parallel degree."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    FrozenModel,
    Hash,
    NonEmpty,
    Sha,
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
from .errors import EnvelopeExceedsGrid, ShardIndivisible
from .fidelity import FidelityDetail
from .model_shape import ModelShape, ModelSpec, check_parity
from .precision import Precision

Axis = Annotated[tuple[PositiveInt, ...], Field(min_length=1)]
FrequencyAxis = Annotated[tuple[PositiveFloat, ...], Field(min_length=1)]


class DecodeEnvelope(FrozenModel):
    batch_max: PositiveInt
    context_per_seq_max: PositiveInt


class PrefillEnvelope(FrozenModel):
    prompt_tokens_max: PositiveInt
    prompts_per_iteration_max: PositiveInt


class Envelope(FrozenModel):
    decode: DecodeEnvelope
    prefill: PrefillEnvelope


class DecodeGrid(FrozenModel):
    batch: Axis
    context_per_seq: Axis


class PrefillGrid(FrozenModel):
    n: Axis
    L: Axis


class Grid(FrozenModel):
    decode: DecodeGrid
    prefill: PrefillGrid
    frequency_ratio: FrequencyAxis

    @model_validator(mode="after")
    def unique(self) -> Grid:
        for axis in (
            self.decode.batch,
            self.decode.context_per_seq,
            self.prefill.n,
            self.prefill.L,
            self.frequency_ratio,
        ):
            if len(set(axis)) != len(axis):
                raise ValueError("Grid axes must not repeat points.")
        return self


class KvLayout(FrozenModel):
    block_size_tokens: PositiveInt


class DecodeVisitWeight(FrozenModel):
    batch: PositiveInt
    total_context_tokens: PositiveInt
    weight_ratio: PositiveFloat


class PrefillVisitWeight(FrozenModel):
    n_prompts: PositiveInt
    prompt_tokens: PositiveInt
    weight_ratio: PositiveFloat


class VisitWeights(FrozenModel):
    decode: tuple[DecodeVisitWeight, ...]
    prefill: tuple[PrefillVisitWeight, ...]


class CharacterizationRequest(FrozenModel):
    contract: Literal["uarch-contract/0.1"]
    rk_schema_snapshot: Sha
    component_id: NonEmpty
    hardware_spec_hash: Hash
    model: ModelSpec
    model_shape: ModelShape
    precision: Precision
    tp: PositiveInt
    envelope: Envelope
    grid: Grid
    mapping_policy: Annotated[str, Field(pattern=r"^\S+@\S+$")]
    uarch_fidelity: FidelityDetail
    initial_state: Literal["steady", "cold"] = "steady"
    kv_layout: KvLayout
    visit_weights: VisitWeights | None = None
    seed: NonNegativeInt

    @model_validator(mode="after")
    def shape_and_shard(self) -> CharacterizationRequest:
        check_parity(self.model, self.model_shape)
        dimensions = {"n_heads": self.model.n_heads, "d_ff": self.model_shape.d_ff}
        if self.model_shape.expert_d_ff is not None:
            dimensions["expert_d_ff"] = self.model_shape.expert_d_ff
        if self.model.kv_heads >= self.tp:
            dimensions["kv_heads"] = self.model.kv_heads
        elif self.tp % self.model.kv_heads:
            raise ShardIndivisible(
                f"kv_heads={self.model.kv_heads} cannot replicate evenly over tp={self.tp}."
            )
        for name, size in dimensions.items():
            if size % self.tp:
                raise ShardIndivisible(f"{name}={size} is not divisible by tp={self.tp}.")
        limits = (
            (self.envelope.decode.batch_max, self.grid.decode.batch, "decode.batch"),
            (
                self.envelope.decode.context_per_seq_max,
                self.grid.decode.context_per_seq,
                "decode.context_per_seq",
            ),
            (self.envelope.prefill.prompt_tokens_max, self.grid.prefill.L, "prefill.L"),
            (self.envelope.prefill.prompts_per_iteration_max, self.grid.prefill.n, "prefill.n"),
        )
        for limit, axis, name in limits:
            if limit > max(axis):
                raise EnvelopeExceedsGrid(
                    f"{name} envelope maximum {limit} exceeds grid {max(axis)}."
                )
        return self
