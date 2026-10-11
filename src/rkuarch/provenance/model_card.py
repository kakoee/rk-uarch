"""Conservative projection into the existing shared ModelCard; no new ledger."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, cast

from uarch_contract.hashing import content_hash, resolve_artifact
from uarch_contract.model_card import (
    ApplicabilityScope,
    ModelCard,
    ModelId,
    ValidatedErrorBand,
    Verification,
)
from uarch_contract.registry import FamilyRegistry
from uarch_contract.report_context import ReportContext

from .applicability import EvidenceAssessment, assess_evidence
from .badge import ORDER, badge_for

if TYPE_CHECKING:
    from rkuarch.table.build import CapturedWork


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


def validate_production_model_card(
    card: ModelCard,
    *,
    captured: CapturedWork,
    context: ReportContext,
    artifacts: Mapping[str, Any],
) -> None:
    """Refuse unsupported assertions; never rewrite a caller's hash-bound card.

    This is the accepted bounded U2 profile, not a positive real eligibility path.
    Administrative reviews authenticate declarations, not measurement truth. Assess
    all captured operator scopes with synthetic eligibility disabled. L0–L2 cannot
    raise accuracy, a null band stays unknown, and known-empty energy is unverified.
    """
    from rkuarch.table.build import consumed_energy_families, source_scopes
    from rkuarch.workload.identity import legacy_model_id

    if (
        not captured.jobs
        or card.model_id != legacy_model_id(captured.jobs[0], captured.bundle)
        or context.model_identity != captured.assumptions.model
        or context.request_hash != content_hash(captured.request)
        or context.assumptions_hash != captured.assumptions.assumptions_hash
    ):
        raise ValueError("ModelCardMismatch: captured model/request identity")
    registry = FamilyRegistry.model_validate(
        resolve_artifact(context.family_registry_hash, artifacts)
    )
    families = [
        e.family
        for e in registry.entries
        if e.hardware_spec_hash == captured.request.hardware_spec_hash
    ]
    if len(families) != 1:
        raise ValueError("AmbiguousFamily: model card hardware")
    scopes = tuple(
        {
            content_hash(scope): scope
            for cases in source_scopes(captured, family=families[0]).values()
            for scope in cases
        }.values()
    )
    assessments = tuple(
        assess_evidence(
            context,
            scopes,
            purpose=purpose,
            channel=None,
            granularity="operator",
            dimensions=(),
            artifacts=artifacts,
            allow_synthetic=False,
        )
        for purpose in ("counts", "duration")
    )
    derived = build_model_card(card.model_id, assessments)
    allowed = badge_for((), assessments, design_status=captured.bundle.hardware_spec.design_status)
    if derived.badge != "stub" or allowed.badge != "stub":
        raise ValueError("UnsupportedModelCardAssertion: positive real U2 evidence profile")
    if card.badge != derived.badge:
        raise ValueError("UnsupportedModelCardAssertion: badge has no applicable real evidence")
    if card.validated_error_band is not None:
        raise ValueError("UnsupportedModelCardAssertion: validated band has no real proof")
    # This exact engine's empty consumption supplies no quantity or verification.
    if context.used_energy_families != consumed_energy_families(captured):
        raise ValueError("UnsupportedModelCardAssertion: captured energy family mismatch")
    if card.energy_verification is not None:
        raise ValueError("UnsupportedModelCardAssertion: energy remains unverified")
