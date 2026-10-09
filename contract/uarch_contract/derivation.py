"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenModel
from .sourced import SourcedValue


class DerivedParameter(FrozenModel):
    claim_badge: Literal["measured", "spec_derived", "estimated", "stub"] | None
    conditional_paths: Annotated[
        tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=0)
    ]
    contributor_paths: Annotated[
        tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=1)
    ]
    formula_id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    value: SourcedValue


class Derivation(FrozenModel):
    derivation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-derivation/1"]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    parameters: Annotated[tuple[DerivedParameter, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def accepted_semantics(self) -> Derivation:
        if len({p.name for p in self.parameters}) != len(self.parameters):
            raise ValueError("ParamsMismatch: duplicate derived parameter")
        return self


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    DerivedParameter,
    Derivation,
)

for _model in (
    DerivedParameter,
    Derivation,
):
    _model.model_rebuild()
