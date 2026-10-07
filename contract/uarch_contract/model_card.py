"""Evidence identity and scope. None means unknown; energy None means unverified.

No numeric defaults. L0-L2 verification cannot promote a badge. Ledger applicability
and promotion belong to U-P4, not the carrier parser.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenModel, Hash, NonEmpty
from .common import JsonNonNegativeFloat as NonNegativeFloat
from .common import JsonPositiveFloat as PositiveFloat
from .fidelity import FidelityDetail
from .precision import PrecisionFormat


class ModelId(FrozenModel):
    engine: NonEmpty
    engine_version: NonEmpty
    fidelity_detail: FidelityDetail
    mapping_policy: NonEmpty


class Verification(FrozenModel):
    L0: Hash | None = None
    L0m: Hash | None = None
    L1: Hash | None = None
    L2: Hash | None = None


class ApplicabilityScope(FrozenModel):
    family: NonEmpty
    op_classes: tuple[NonEmpty, ...]
    precisions: tuple[PrecisionFormat, ...]
    shape_regimes: tuple[NonEmpty, ...]
    load_regimes: tuple[NonEmpty, ...]
    mapping_match: Literal["matched", "compiler-chosen"]


class ValidatedErrorBand(FrozenModel):
    low_rel: NonNegativeFloat
    high_rel: PositiveFloat
    scope: ApplicabilityScope

    @model_validator(mode="after")
    def ordered(self) -> ValidatedErrorBand:
        if self.low_rel > self.high_rel:
            raise ValueError("validated_error_band.low_rel must not exceed high_rel.")
        return self


CoefficientFamily = Literal["mac", "sram", "noc_hop", "dram", "static"]


class EnergyVerification(FrozenModel):
    L0: Annotated[dict[CoefficientFamily, Hash | None], Field(min_length=1)]
    L2: Annotated[dict[CoefficientFamily, Hash | None], Field(min_length=1)]


class ModelCard(FrozenModel):
    model_id: ModelId
    badge: Literal["stub", "estimated", "measured"]
    evidence: tuple[NonEmpty, ...]
    verification: Verification
    validated_error_band: ValidatedErrorBand | None = None
    energy_verification: EnergyVerification | None = None

    @model_validator(mode="after")
    def evidence_required(self) -> ModelCard:
        if self.badge != "stub" and not self.evidence:
            raise ValueError("A model badge above stub requires ledger evidence, not verification.")
        return self


class EmbeddedModelCard(FrozenModel):
    hash: Hash
    badge: Literal["stub", "estimated", "measured"]
    evidence: tuple[NonEmpty, ...]
    validated_error_band: ValidatedErrorBand | None = None
    energy_verification: EnergyVerification | None = None

    @model_validator(mode="after")
    def evidence_required(self) -> EmbeddedModelCard:
        if self.badge != "stub" and not self.evidence:
            raise ValueError("An embedded badge above stub requires ledger evidence.")
        return self
