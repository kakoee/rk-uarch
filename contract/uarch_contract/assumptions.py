"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .common import FrozenModel


class ModelIdentity(FrozenModel):
    implementation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    name: Literal["physical-resolved", "nominal-rk-compatibility"]
    version: Annotated[str, Field(min_length=1, pattern="\\S")]


class AssumptionSet(FrozenModel):
    algorithms: dict[str, Annotated[str, Field(min_length=1, pattern="\\S")]]
    assumptions_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-assumptions/1"]
    limitations: Annotated[
        tuple[Annotated[str, Field(min_length=1, pattern="\\S")], ...], Field(min_length=1)
    ]
    model: ModelIdentity


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    ModelIdentity,
    AssumptionSet,
)

for _model in (
    ModelIdentity,
    AssumptionSet,
):
    _model.model_rebuild()
