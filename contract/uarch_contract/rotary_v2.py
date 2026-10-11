"""Additive U0022 carriers, NOT execution admission or automatic v1 migration.

Coefficient shape/finite bits/content identity and inherited request/operand checks
execute here. Graph semantics, closure joins, hardware/rank support, job/result admission
and analytic replay require the separately reviewed v2 validators. Do not dispatch an
engine merely because model_validate succeeds. V1 roots/generators remain untouched.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenModel, Hash, JsonFloat, JsonNonNegativeInt, JsonPositiveInt, NonEmpty
from .hardware import HardwareSpec
from .hashing import verify_identity
from .operators import Operand, OpSpec
from .prepared import KvAccess, Padding, Producer, Query, RankScope, Replication
from .request import _RequestFields

Bits32 = Annotated[str, Field(pattern=r"^[0-9a-f]{8}$")]
BitRow = Annotated[tuple[Bits32, ...], Field(min_length=1)]
BitTable = Annotated[tuple[BitRow, ...], Field(min_length=1)]
Pairing = Literal["adjacent", "split_halves"]
NumericPolicy = Literal["fp32-separate-round-rne/1"]
_Id = Annotated[str, Field(min_length=1)]
_Positive = Annotated[int, Field(strict=True, ge=1)]
_Nonnegative = Annotated[int, Field(strict=True, ge=0)]


class RotaryCoefficients(FrozenModel):
    format: Literal["uarch-rotary-coefficients/1"]
    coefficients_hash: Hash
    position_count: JsonPositiveInt
    rotary_dim: JsonPositiveInt
    dtype: Literal["fp32"]
    cos_bits: BitTable
    sin_bits: BitTable
    producer: Producer

    @model_validator(mode="after")
    def table_shape_bits_and_identity(self) -> RotaryCoefficients:
        if self.rotary_dim < 2 or self.rotary_dim % 2:
            raise ValueError("rotary_dim must be positive even and >=2")
        for table in (self.cos_bits, self.sin_bits):
            if len(table) != self.position_count:
                raise ValueError("position_count mismatch")
            for row in table:
                if len(row) != self.rotary_dim // 2:
                    raise ValueError("coefficient row width mismatch")
                if any(int(bits, 16) & 0x7F800000 == 0x7F800000 for bits in row):
                    raise ValueError("nonfinite binary32 coefficient")
        verify_identity(self, "coefficients_hash")
        return self


class RotaryEncoding(FrozenModel):
    kind: Literal["rope-precomputed/1"]
    rotary_dim: JsonPositiveInt
    pairing: Pairing
    coefficients_hash: Hash
    position_policy: Literal["zero-origin-contiguous/1"]
    cache_key_state: Literal["rotated-before-store"]
    numeric_policy: NumericPolicy


class RotaryBinding(FrozenModel):
    target: Literal["q", "k"]
    coefficients_hash: Hash
    pairing: Pairing
    numeric_policy: NumericPolicy
    position_ids: Annotated[
        tuple[Annotated[tuple[JsonNonNegativeInt, ...], Field(min_length=1)], ...],
        Field(min_length=1),
    ]
    input_op_id: NonEmpty


class RotaryOpSpec(FrozenModel):
    operator: Literal["rotary_embedding"]
    dimensions: dict[NonEmpty, JsonPositiveInt]
    operands: dict[NonEmpty, Operand]
    reduction_axes: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def named_dimensions(self) -> RotaryOpSpec:
        # Same structural guard as OpSpec; exact rotary axes are an admission obligation.
        if not self.dimensions or not self.operands:
            raise ValueError("An operator requires named dimensions and operands.")
        used = set(self.reduction_axes)
        for operand in self.operands.values():
            used.update(operand.dimensions)
        if used - self.dimensions.keys():
            raise ValueError(f"Undefined dimensions: {sorted(used - self.dimensions.keys())}.")
        return self


class PreparedOpV2(FrozenModel):
    depends_on: Annotated[tuple[_Id, ...], Field(min_length=0)]
    embedding_local_tokens: _Nonnegative | None
    fusion: Literal["none", "qk_softmax_av"]
    id: _Id
    kv_access: KvAccess | None
    operand_access: dict[str, Literal["read", "write", "read_write"]]
    padding: Annotated[tuple[Padding, ...], Field(min_length=0)]
    replication: Annotated[tuple[Replication, ...], Field(min_length=0)]
    spec: OpSpec | RotaryOpSpec
    weight_copies: _Positive
    work_repeat: _Positive
    rotary: RotaryBinding | None


class OpGroupV2(FrozenModel):
    depends_on: Annotated[tuple[_Id, ...], Field(min_length=0)]
    id: _Id
    kind: Literal["head", "decoder", "tail"]
    ops: Annotated[tuple[PreparedOpV2, ...], Field(min_length=1)]
    repeat: _Positive


class PreparedGraphV2(FrozenModel):
    attention_mask: Literal["full_square", "causal"]
    groups: Annotated[tuple[OpGroupV2, ...], Field(min_length=1)]
    lm_head_tokens: _Positive
    omissions: Annotated[tuple[_Id, ...], Field(min_length=4)]
    kv_key_encoding: RotaryEncoding


class PreparedPointV2(FrozenModel):
    embedding_hits: Annotated[tuple[_Nonnegative, ...], Field(min_length=1)]
    frequency_ratio: Annotated[JsonFloat, Field(gt=0)]
    graph: PreparedGraphV2
    hit_source: Literal["provided_counts", "synthetic_balanced_assignment", "tp1_trivial"]
    initial_state: Literal["steady", "cold"]
    payload_hash: Hash
    query: Query


class RequestIntentV3(_RequestFields):
    accounting: Literal["resolved-ops/2"]
    analytic_mode: Literal["aggregate", "per_op"]
    assumptions_hash: Hash
    contract: Literal["uarch-contract/0.3"]
    preparation_policy: Literal["balanced-tp/1"]
    mapping_policy: Literal["analytic-ops@2"]
    position_encoding: RotaryEncoding


class CharacterizationRequestV3(RequestIntentV3):
    prepared_input_hash: Hash


class PreparedBundleV2(FrozenModel):
    bundle_hash: Hash
    format: Literal["uarch-prepared/2"]
    hardware_spec: HardwareSpec
    intent: RequestIntentV3
    intent_hash: Hash
    mapping_scope: Literal["analytic_ops"]
    points: Annotated[tuple[PreparedPointV2, ...], Field(min_length=1)]
    producer: Producer
    rank: RankScope
    coefficients: RotaryCoefficients


# Dedicated generator only: never add this module to the v1 generate.MODULES inventory.
SCHEMA_ROOTS = (
    RotaryCoefficients,
    RotaryEncoding,
    RotaryBinding,
    RotaryOpSpec,
    PreparedOpV2,
    OpGroupV2,
    PreparedGraphV2,
    PreparedPointV2,
    RequestIntentV3,
    CharacterizationRequestV3,
    PreparedBundleV2,
)
