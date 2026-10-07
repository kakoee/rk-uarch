"""Pinned ModelSpec copy and proposed bias-free decoder shape accounting."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .common import FrozenModel, JsonPositiveInt, NonNegativeInt, PositiveInt


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
            raise ValueError(f"kv_heads ({self.kv_heads}) cannot exceed n_heads ({self.n_heads})")
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


class ModelShape(FrozenModel):
    d_ff: JsonPositiveInt
    gated_mlp: bool
    vocab_size: JsonPositiveInt
    attention: Literal["mha", "gqa"]
    tie_embeddings: bool
    expert_d_ff: JsonPositiveInt | None = None


def implied_params(spec: ModelSpec, shape: ModelShape) -> tuple[int, int]:
    """Global, pre-shard counts: Q/K/V/O, two RMS norms/layer, final norm, embeddings.

    MoE replaces the FFN with n_experts FFNs and a d_model*n_experts router.
    This counts parameters only; it does not model routing performance. See U0001.
    """
    if (shape.attention == "mha") != (spec.kv_heads == spec.n_heads):
        raise ValueError("attention must be mha exactly when kv_heads equals n_heads.")
    if bool(spec.n_experts) != (shape.expert_d_ff is not None):
        raise ValueError("expert_d_ff is required for MoE and forbidden for dense models.")
    if spec.n_experts and shape.d_ff != shape.expert_d_ff:
        raise ValueError("MoE d_ff must equal expert_d_ff: both denote one expert's width.")
    d = spec.d_model
    attention = 2 * d * d + 2 * d * spec.kv_heads * spec.head_dim
    common = spec.n_layers * (attention + 2 * d) + d
    common += shape.vocab_size * d * (1 if shape.tie_embeddings else 2)
    projections = 3 if shape.gated_mlp else 2
    if spec.n_experts:
        assert shape.expert_d_ff is not None
        common += spec.n_layers * d * spec.n_experts
        expert = spec.n_layers * projections * d * shape.expert_d_ff
        return common + expert * spec.n_experts, common + expert * spec.experts_per_token
    total = common + spec.n_layers * projections * d * shape.d_ff
    return total, total


def check_parity(spec: ModelSpec, shape: ModelShape) -> None:
    """Reject either count outside the inclusive one-percent identity tolerance."""
    total, active = implied_params(spec, shape)
    if (
        abs(total - spec.total_params) > spec.total_params * 0.01
        or abs(active - spec.active_params) > spec.active_params * 0.01
    ):
        raise ValueError(
            f"ModelShape implies total={total}, active={active}; ModelSpec declares "
            f"total={spec.total_params}, active={spec.active_params}; both must agree within 1%."
        )
