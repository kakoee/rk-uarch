"""Conservative projection into the existing shared ModelCard; no new ledger."""

from __future__ import annotations

from typing import Literal, cast

from uarch_contract.model_card import (
    ApplicabilityScope,
    ModelCard,
    ModelId,
    ValidatedErrorBand,
    Verification,
)

from .applicability import EvidenceAssessment
from .badge import ORDER


def build_model_card(
    model_id: ModelId,
    assessments: tuple[EvidenceAssessment, ...],
    *,
    verification: Verification | None = None,
    band_scope: ApplicabilityScope | None = None,
) -> ModelCard:
    """Synthetic evaluator results cannot upgrade a real serialized model card.

    The caller must supply every contributing metric/operator assessment. Explicit legacy
    scope projection is required to carry an observed band; none is guessed from a label.
    """
    badge = min((a.badge for a in assessments), key=ORDER.__getitem__, default="stub")
    if any(a.synthetic for a in assessments):
        badge = "stub"
    bands = {a.error_band for a in assessments}
    band = None
    if (
        badge != "stub"
        and band_scope is not None
        and len(bands) == 1
        and None not in bands
        and all(a.purpose == "duration" for a in assessments)
    ):
        selected = next(iter(bands))
        assert selected is not None
        low, high = selected
        band = ValidatedErrorBand(low_rel=low, high_rel=high, scope=band_scope)
    return ModelCard(
        model_id=model_id,
        badge=cast(Literal["stub", "estimated", "measured"], badge),
        evidence=tuple(sorted({e for a in assessments for e in a.evidence_ids})),
        verification=verification or Verification(),
        validated_error_band=band,
        energy_verification=None,
    )
