"""Review-only carrier prototype. No preparation, execution, or runtime admission.

Run with --schemas to print the proposed root schemas; otherwise check examples and
syntax refusals. Imports existing carrier primitives, never production count functions.
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError, create_model, model_validator
from uarch_contract.assumptions import ModelIdentity
from uarch_contract.common import FrozenModel, Hash, JsonNonNegativeInt, JsonPositiveInt, NonEmpty
from uarch_contract.hashing import verify_identity
from uarch_contract.operators import OpSpec
from uarch_contract.prepared import (
    OpGroup,
    PreparedBundle,
    PreparedGraph,
    PreparedOp,
    PreparedPoint,
    Producer,
)
from uarch_contract.request import RequestIntent

from rkuarch.engines.protocol import EngineIdentity, EngineJob, EngineResult

Bits32 = Annotated[str, Field(pattern=r"^[0-9a-f]{8}$")]
BitRow = Annotated[tuple[Bits32, ...], Field(min_length=1)]
BitTable = Annotated[tuple[BitRow, ...], Field(min_length=1)]
Pairing = Literal["adjacent", "split_halves"]
NumericPolicy = Literal["fp32-separate-round-rne/1"]


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


# create_model overrides these fields only; inherited fields/extra-forbid stay intact.
# This notation specifies carrier shape, not permission to reuse the v1 graph validator.
RotaryOpSpec = create_model(
    "RotaryOpSpec", __base__=OpSpec, operator=(Literal["rotary_embedding"], ...)
)
PreparedOpV2 = create_model(
    "PreparedOpV2",
    __base__=PreparedOp,
    spec=(OpSpec | RotaryOpSpec, ...),
    rotary=(RotaryBinding | None, ...),
)
OpGroupV2 = create_model(
    "OpGroupV2",
    __base__=OpGroup,
    ops=(Annotated[tuple[PreparedOpV2, ...], Field(min_length=1)], ...),
)
PreparedGraphV2 = create_model(
    "PreparedGraphV2",
    __base__=PreparedGraph,
    groups=(Annotated[tuple[OpGroupV2, ...], Field(min_length=1)], ...),
    kv_key_encoding=(RotaryEncoding, ...),
)
PreparedPointV2 = create_model(
    "PreparedPointV2", __base__=PreparedPoint, graph=(PreparedGraphV2, ...)
)
RequestIntentV3 = create_model(
    "RequestIntentV3",
    __base__=RequestIntent,
    contract=(Literal["uarch-contract/0.3"], ...),
    accounting=(Literal["resolved-ops/2"], ...),
    mapping_policy=(Literal["analytic-ops@2"], ...),
    position_encoding=(RotaryEncoding, ...),
)
CharacterizationRequestV3 = create_model(
    "CharacterizationRequestV3", __base__=RequestIntentV3, prepared_input_hash=(Hash, ...)
)
PreparedBundleV2 = create_model(
    "PreparedBundleV2",
    __base__=PreparedBundle,
    format=(Literal["uarch-prepared/2"], ...),
    intent=(RequestIntentV3, ...),
    points=(Annotated[tuple[PreparedPointV2, ...], Field(min_length=1)], ...),
    coefficients=(RotaryCoefficients, ...),
)
ModelIdentityV2 = create_model(
    "ModelIdentityV2",
    __base__=ModelIdentity,
    name=(Literal["physical-resolved"], ...),
    version=(Literal["2"], ...),
)
EngineIdentityV2 = create_model(
    "EngineIdentityV2",
    __base__=EngineIdentity,
    version=(Literal["resolved-ops/2"], ...),
    model=(ModelIdentityV2, ...),
)
EngineJobV2 = create_model(
    "EngineJobV2",
    __base__=EngineJob,
    accounting=(Literal["resolved-ops/2"], ...),
    protocol=(Literal["uarch-engine/2"], ...),
    point=(PreparedPointV2, ...),
    engine=(EngineIdentityV2, ...),
    coefficients=(RotaryCoefficients, ...),
)
EngineResultV2 = create_model(
    "EngineResultV2",
    __base__=EngineResult,
    protocol=(Literal["uarch-engine/2"], ...),
    engine=(EngineIdentityV2, ...),
)
CONTRACT_ROOTS = (
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
ENGINE_ROOTS = (ModelIdentityV2, EngineIdentityV2, EngineJobV2, EngineResultV2)


def check() -> None:
    examples = json.loads(Path(__file__).with_name("small-inputs.json").read_text())
    pairs = (
        (RotaryCoefficients, examples["coefficients"]),
        (RotaryEncoding, examples["position_encoding"]),
        (PreparedOpV2, examples["rope_q"]),
        (PreparedOpV2, examples["rope_k"]),
    )
    for model, value in pairs:
        model.model_validate(value)
    cases = []
    for label, key, value in (
        ("uppercase bits", "cos_bits", [["3F800000"], ["00000000"], ["3f800000"]]),
        ("NaN bits", "sin_bits", [["7fc00000"], ["3f800000"], ["00000000"]]),
        ("infinity bits", "sin_bits", [["7f800000"], ["3f800000"], ["00000000"]]),
        ("short table", "position_count", 4),
        ("odd R", "rotary_dim", 3),
        ("boolean extent", "position_count", True),
        ("tampered finite bits", "cos_bits", [["00000000"], ["00000000"], ["3f800000"]]),
    ):
        value_copy = deepcopy(examples["coefficients"])
        value_copy[key] = value
        cases.append((label, RotaryCoefficients, value_copy))
    # Isolate the extra-field refusal from the independently tested unknown operator.
    legacy_fixture = Path(__file__).resolve().parents[3] / (
        "contract/tests/fixtures/u2/independent-bundle.json"
    )
    legacy = json.loads(legacy_fixture.read_text())
    old_node_with_new_field = deepcopy(legacy["points"][0]["graph"]["groups"][1]["ops"][1])
    PreparedOp.model_validate(old_node_with_new_field)
    old_node_with_new_field["rotary"] = None
    missing = deepcopy(examples["rope_q"])
    del missing["rotary"]
    cases.extend(
        [
            ("missing required binding", PreparedOpV2, missing),
            ("v1 rejects new operator", OpSpec, examples["rope_q"]["spec"]),
            ("v1 rejects new field even null", PreparedOp, old_node_with_new_field),
        ]
    )
    for label, model, value in cases:
        try:
            model.model_validate(value)
        except ValidationError:
            continue
        raise AssertionError(f"prototype unexpectedly admitted {label}")
    schemas = [model.model_json_schema() for model in (*CONTRACT_ROOTS, *ENGINE_ROOTS)]
    if any(schema.get("additionalProperties") is not False for schema in schemas):
        raise AssertionError("extra-forbid lost")
    print(
        f"carrier prototype only: {len(pairs)} positive, {len(cases)} refusal, "
        f"{len(schemas)} schema-root checks passed; no runtime checks executed"
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--schemas"]:
        print(
            json.dumps(
                {m.__name__: m.model_json_schema() for m in (*CONTRACT_ROOTS, *ENGINE_ROOTS)},
                indent=2,
                sort_keys=True,
            )
        )
    elif not sys.argv[1:]:
        check()
    else:
        raise SystemExit("usage: schema_prototype.py [--schemas]")
