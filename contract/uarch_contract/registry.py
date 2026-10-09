"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenModel


class FamilyRegistryEntriesItem(FrozenModel):
    family: Annotated[str, Field(min_length=1, pattern="\\S")]
    hardware_spec_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


class FamilyRegistry(FrozenModel):
    entries: Annotated[tuple[FamilyRegistryEntriesItem, ...], Field(min_length=1)]
    format: Literal["uarch-family-registry/1"]
    registry_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    review_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    version: Annotated[str, Field(min_length=1, pattern="\\S")]

    @model_validator(mode="after")
    def accepted_semantics(self) -> FamilyRegistry:
        if len({entry.hardware_spec_hash for entry in self.entries}) != len(self.entries):
            raise ValueError("AmbiguousFamily: entries must have unique hardware identities")
        return self


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (FamilyRegistry,)

for _model in (
    FamilyRegistryEntriesItem,
    FamilyRegistry,
):
    _model.model_rebuild()
