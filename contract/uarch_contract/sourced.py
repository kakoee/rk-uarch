"""rk-sim's five carrier fields plus claim/stipulation semantics; see U0001."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import field_validator, model_validator

from .common import FrozenModel
from .errors import ClaimWithoutSource


class Calibration(StrEnum):
    MEASURED = "measured"
    SPEC_DERIVED = "spec_derived"
    ESTIMATED = "estimated"
    STUB = "stub"


class SourcedValue(FrozenModel):
    value: float
    unit: str
    provenance: Calibration | None = None
    source: str | None = None
    date: str | None = None
    kind: Literal["claim", "stipulation"] = "claim"
    rationale: str | None = None

    @field_validator("value")
    @classmethod
    def finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("value must be finite.")
        return value

    @field_validator("unit")
    @classmethod
    def unit_present(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("unit must be non-empty; units live in names and in this field.")
        return value

    @model_validator(mode="after")
    def kind_rules(self) -> SourcedValue:
        if self.kind == "stipulation":
            if any(v is not None for v in (self.provenance, self.source, self.date)):
                raise ValueError("A stipulation requires provenance=None, source=None, date=None.")
            if self.rationale is None or not self.rationale.strip():
                raise ValueError("A stipulation requires a non-empty rationale.")
        else:
            if self.rationale is not None:
                raise ValueError("A claim forbids rationale; use a source for evidence.")
            if self.provenance is None:
                raise ValueError("A claim requires provenance.")
            if self.provenance == Calibration.STUB:
                # Deliberately stricter than the pinned implementation's blank-string loophole.
                if self.source is not None:
                    raise ValueError("provenance=stub requires source=None.")
            elif self.source is None or not self.source.strip():
                raise ClaimWithoutSource()
        return self
