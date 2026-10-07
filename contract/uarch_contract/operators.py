"""P16 vocabulary plus tiling carriers; this is not a workload graph or execution IR.

A multiply-add is two operations (rk-sim P7b, not a new decision). attention_fused
means QK score -> softmax -> AV across KV tiles. Its operation count is the sum
of those three parts; its only DRAM operands are Q, K, V, O. Scores stay on chip.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import model_validator

from .common import FrozenModel, NonEmpty
from .common import JsonPositiveInt as PositiveInt
from .precision import PrecisionFormat


class Operator(StrEnum):
    Q_PROJECTION = "q_projection"
    K_PROJECTION = "k_projection"
    V_PROJECTION = "v_projection"
    QK_SCORE = "qk_score"
    SOFTMAX = "softmax"
    AV_APPLICATION = "av_application"
    OUTPUT_PROJECTION = "output_projection"
    NORMALIZATION = "normalization"
    RESIDUAL_ADDITION = "residual_addition"
    FFN_UP = "ffn_up"
    FFN_GATE = "ffn_gate"
    FFN_DOWN = "ffn_down"
    ACTIVATION = "activation"
    KV_WRITE = "kv_write"
    EMBEDDING = "embedding"
    LM_HEAD = "lm_head"
    ATTENTION_FUSED = "attention_fused"


class Operand(FrozenModel):
    dtype: PrecisionFormat
    dimensions: tuple[NonEmpty, ...]
    layout: Literal["contiguous", "paged"]
    block_size_tokens: PositiveInt | None = None

    @model_validator(mode="after")
    def page_size(self) -> Operand:
        if (self.layout == "paged") != (self.block_size_tokens is not None):
            raise ValueError("Only a paged operand requires block_size_tokens.")
        return self


class OpSpec(FrozenModel):
    operator: Operator
    dimensions: dict[NonEmpty, PositiveInt]
    operands: dict[NonEmpty, Operand]
    reduction_axes: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def named_dimensions(self) -> OpSpec:
        if not self.dimensions or not self.operands:
            raise ValueError("An operator requires named dimensions and operands.")
        used = set(self.reduction_axes)
        for operand in self.operands.values():
            used.update(operand.dimensions)
        if used - self.dimensions.keys():
            raise ValueError(f"Undefined dimensions: {sorted(used - self.dimensions.keys())}.")
        if self.operator == Operator.ATTENTION_FUSED and set(self.operands) != {"Q", "K", "V", "O"}:
            raise ValueError("attention_fused DRAM operands must be exactly Q, K, V and O.")
        return self
