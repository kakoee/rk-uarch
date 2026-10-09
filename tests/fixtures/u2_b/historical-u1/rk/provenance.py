"""Provenance types: Fidelity/Calibration enums, SourcedValue, Metric, combine().

The spine. Every other module imports this one; it imports nothing from rk.

Two types carry every number in the system, and they point in opposite directions:

    SourcedValue   the ONLY way a number enters   (a claim about the world)
    Metric         the ONLY way a number leaves   (a claim we computed)

Between them sits `combine()`, which propagates a badge as the *worst* of its
contributors. Display code may never improve a badge; see CLAUDE.md invariant 3.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

__all__ = [
    "Calibration",
    "ComputeFidelity",
    "MemoryFidelity",
    "Metric",
    "NetworkFidelity",
    "RuntimeFidelity",
    "SourcedValue",
    "combine",
]


# --------------------------------------------------------------------------------------
# Calibration — how much evidence a number has
# --------------------------------------------------------------------------------------

# Higher rank = stronger evidence. build-spec §2.3.3 writes the ordering as
# MEASURED > SPEC_DERIVED > ESTIMATED > STUB, and the comparison operators below mean
# exactly that, so `a > b` reads "a has stronger evidence than b".
_CALIBRATION_RANK: dict[str, int] = {
    "measured": 3,
    "spec_derived": 2,
    "estimated": 1,
    "stub": 0,
}


class Calibration(StrEnum):
    """How a number came to be known. Serializes lower_snake in YAML and JSON.

    There is no `spec` member — the vendor-datasheet value is `SPEC_DERIVED`.
    """

    MEASURED = "measured"
    SPEC_DERIVED = "spec_derived"
    ESTIMATED = "estimated"
    STUB = "stub"

    @property
    def rank(self) -> int:
        """Evidence strength, 3 (measured) down to 0 (stub)."""
        return _CALIBRATION_RANK[self.value]

    # str already defines the comparison operators, and its lexicographic answers are
    # wrong here in a way that fails silently: "estimated" < "measured" is True, but
    # ESTIMATED is the *weaker* badge. Override all four so `<` means "less evidence".
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Calibration):
            return NotImplemented
        return self.rank < other.rank

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Calibration):
            return NotImplemented
        return self.rank <= other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Calibration):
            return NotImplemented
        return self.rank > other.rank

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Calibration):
            return NotImplemented
        return self.rank >= other.rank


def combine(badges: Iterable[Calibration]) -> Calibration:
    """Propagate a badge as the worst of its contributors.

    An empty input returns STUB, deliberately: a derived number that cannot name a
    single contributor has no evidence behind it, and badging it MEASURED because
    nothing argued otherwise is the exact failure this project exists to prevent.
    """
    worst = Calibration.MEASURED
    seen = False
    for badge in badges:
        seen = True
        if badge.rank < worst.rank:
            worst = badge
    return worst if seen else Calibration.STUB


# --------------------------------------------------------------------------------------
# Fidelity — which model ran, per axis
# --------------------------------------------------------------------------------------
# Uppercase labels on both sides (`fidelity_available: [C0]`): these are identifiers,
# not prose. Which levels are actually implemented is a schema concern, not this
# module's — see rk/schema/fidelity.py.


class ComputeFidelity(StrEnum):
    """C0 analytical · C1 contention-aware · C2 cycle-approximate · C3 external/RTL."""

    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    STUB = "STUB"


class MemoryFidelity(StrEnum):
    """M0 analytical capacity+bandwidth · M1 queueing/contention."""

    M0 = "M0"
    M1 = "M1"
    STUB = "STUB"


class NetworkFidelity(StrEnum):
    """N0 analytical transfer · N1 flow-level · N2 packet · N3 flit/credit."""

    N0 = "N0"
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
    STUB = "STUB"


class RuntimeFidelity(StrEnum):
    """R0 ideal scheduler · R1 native-policy DES · R2 trace replay."""

    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    STUB = "STUB"


# --------------------------------------------------------------------------------------
# The two carriers
# --------------------------------------------------------------------------------------


def _reject_non_finite(value: float, field: str) -> float:
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{field} must be finite, got {value!r}")
    return value


class SourcedValue(BaseModel):
    """A number entering the system, with the evidence that lets it in.

    Exactly five fields. `extra="forbid"` is load-bearing: it is what rejects the
    stray `note:` key that earlier drafts of the component YAML carried.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float
    unit: str
    provenance: Calibration
    source: str | None = None
    date: str | None = None

    @field_validator("value")
    @classmethod
    def _finite(cls, v: float) -> float:
        return _reject_non_finite(v, "value")

    @field_validator("unit")
    @classmethod
    def _unit_present(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("unit must be non-empty; units live in names and in this field")
        return v

    @model_validator(mode="after")
    def _source_matches_provenance(self) -> SourcedValue:
        """A stub may not cite a source; everything else must.

        This is what turns library/README.md's provenance table from an aspiration
        into a machine check. A stub carrying a source is a lie about having evidence,
        and a spec_derived value without one is a claim nobody can check.
        """
        has_source = self.source is not None and self.source.strip() != ""
        if self.provenance is Calibration.STUB:
            if has_source:
                raise ValueError(
                    "provenance=stub requires source=None: a stub is the absence of "
                    f"evidence, but this one cites {self.source!r}. If the source is real, "
                    "use estimated or spec_derived."
                )
        elif not has_source:
            raise ValueError(
                f"provenance={self.provenance.value} requires a non-empty source. "
                "If you cannot source it, the honest value is provenance=stub with "
                "source=None (CLAUDE.md: don't invent hardware numbers)."
            )
        return self


class Metric(BaseModel):
    """A number leaving the engine, with how much to trust it.

    `contributors` is required and has no default: a metric that cannot name what fed
    it is exactly the case `combine([])` badges STUB.

    `ci95_low`/`ci95_high` stay None until the R1 DES reports replications in P5. They
    exist in v0 so S4's error bars are not a schema break.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float
    unit: str
    badge: Calibration
    contributors: tuple[str, ...]
    ci95_low: float | None = None
    ci95_high: float | None = None

    @field_validator("value")
    @classmethod
    def _finite(cls, v: float) -> float:
        return _reject_non_finite(v, "value")

    @field_validator("ci95_low", "ci95_high")
    @classmethod
    def _finite_bounds(cls, v: float | None, info: Any) -> float | None:
        return None if v is None else _reject_non_finite(v, str(info.field_name))

    @model_validator(mode="after")
    def _ci_is_coherent(self) -> Metric:
        low, high = self.ci95_low, self.ci95_high
        if (low is None) != (high is None):
            raise ValueError(
                "ci95_low and ci95_high must both be set or both be None; "
                "half an interval is not an interval"
            )
        if low is not None and high is not None:
            if low > high:
                raise ValueError(f"ci95_low ({low}) must not exceed ci95_high ({high})")
            if not (low <= self.value <= high):
                raise ValueError(
                    f"value ({self.value}) must lie within [{low}, {high}]"
                )
        return self
