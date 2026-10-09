"""Worst real claims plus independently scoped source models; stipulated conditions survive."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.errors import MissingMetricRecipe
from uarch_contract.evidence import EvidenceScopeCase
from uarch_contract.hashing import content_hash, resolve_artifact, resolve_pointer
from uarch_contract.report_context import (
    DependencySelector,
    MetricDependencies,
    MetricRecipe,
    ReportContext,
    validate_report_context,
)
from uarch_contract.sourced import SourcedValue

from .applicability import EvidenceAssessment, _accepted_review, assess_evidence

ORDER = {"stub": 0, "estimated": 1, "spec_derived": 2, "measured": 3}


@dataclass(frozen=True)
class MetricAssessment:
    """Computed local result, never a substitute shared artifact or loader schema."""

    badge: str
    claim_badge: str | None
    claims: tuple[SourcedValue, ...]
    conditional_on: tuple[SourcedValue, ...]
    models: tuple[EvidenceAssessment, ...]
    contributors: tuple[DependencySelector, ...] = ()
    complete: bool = True
    display_recipe: bool = True
    synthetic: bool = False
    error_band: tuple[float, float] | None = None
    unvalidated_assumptions: tuple[DependencySelector, ...] = ()

    @property
    def nonempty(self) -> bool:
        return bool(self.claims or self.conditional_on or self.models)


def badge_for(
    values: tuple[SourcedValue, ...], models: tuple[EvidenceAssessment, ...], *, design_status: str
) -> MetricAssessment:
    if design_status not in ("proposed", "reference"):
        raise ValueError("unknown design status")
    claims = tuple(v for v in values if v.kind == "claim")
    conditions = tuple(v for v in values if v.kind == "stipulation")
    if design_status == "reference" and conditions:
        raise ValueError("StipulationOnReference")
    claim_badge = min((str(v.provenance) for v in claims), key=ORDER.__getitem__, default=None)
    badges = [m.badge for m in models] + ([claim_badge] if claim_badge is not None else [])
    badge = min(badges, key=ORDER.__getitem__) if badges else "stub"
    if design_status == "proposed" and ORDER[badge] > ORDER["estimated"]:
        badge = "estimated"
    return MetricAssessment(
        badge, claim_badge, claims, conditions, models, synthetic=any(m.synthetic for m in models)
    )


def _sourced(value: Any) -> list[SourcedValue]:
    if isinstance(value, dict):
        if {"value", "unit"} <= value.keys() and ("kind" in value or "provenance" in value):
            return [SourcedValue.model_validate(value)]
        return [v for item in value.values() for v in _sourced(item)]
    if isinstance(value, list):
        return [v for item in value for v in _sourced(item)]
    return []


def assess_metric(
    context: ReportContext,
    metric_path: str,
    *,
    scopes: Mapping[tuple[str, str, str], tuple[EvidenceScopeCase, ...]],
    channel: str | None,
    artifacts: Mapping[str, Any],
    design_status: str,
    allow_synthetic: bool = False,
) -> MetricAssessment:
    """Traverse typed source recipes without flattening away model/purpose/granularity.

    Scope keys are (model identity, purpose, granularity), supplied from real captured
    inputs by the eventual A2 consumer. Each case must name that source model;
    purpose/granularity come from its recipe and must survive evidence evaluation.
    This function is not a file-loading fallback.
    """
    context = validate_report_context(context, artifacts)
    dependencies = MetricDependencies.model_validate(
        resolve_artifact(context.metric_dependencies_hash, artifacts)
    )
    if not _accepted_review(dependencies, artifacts):
        raise ValueError("ReviewNotAccepted: metric dependencies")
    recipe = next((r for r in dependencies.recipes if r.metric_path == metric_path), None)
    if recipe is None:
        raise MissingMetricRecipe(f"MissingMetricRecipe: {metric_path}")
    sources = {(s.artifact_hash, s.recipe.metric_path): s for s in dependencies.source_recipes}
    values: dict[tuple[str, str], list[SourcedValue]] = {}
    contributors: dict[tuple[str, str, str], DependencySelector] = {}
    models: list[EvidenceAssessment] = []
    unvalidated: list[DependencySelector] = []

    def visit(current: MetricRecipe, source_model: str) -> None:
        for selector in current.selectors:
            artifact = resolve_artifact(selector.artifact_hash, artifacts)
            target = resolve_pointer(artifact, selector.json_pointer)
            if selector.kind == "result_field":
                source = sources[(selector.artifact_hash, selector.json_pointer)]
                visit(source.recipe, source.model_identity_hash)
                continue
            contributors[(selector.kind, selector.artifact_hash, selector.json_pointer)] = selector
            if selector.kind == "model_evidence":
                model = ModelIdentity.model_validate(target)
                identity = content_hash(model)
                if identity != source_model:
                    raise ValueError("IncompleteMetricContributors: source model identity")
                key = (identity, current.purpose, current.granularity)
                source_scopes = scopes.get(key, ())
                if any(scope.model_identity_hash != identity for scope in source_scopes):
                    raise ValueError(f"SourceScopeMismatch: {key}")
                if not source_scopes:
                    models.append(
                        EvidenceAssessment(
                            "stub",
                            identity,
                            current.purpose,
                            current.granularity,
                            reasons=("source scope unavailable",),
                        )
                    )
                else:
                    assessment = assess_evidence(
                        context,
                        source_scopes,
                        purpose=current.purpose,
                        channel=channel,
                        granularity=current.granularity,
                        dimensions=current.applicable_dimensions,
                        artifacts=artifacts,
                        allow_synthetic=allow_synthetic,
                    )
                    if (
                        assessment.model_identity_hash,
                        assessment.purpose,
                        assessment.granularity,
                    ) != key:
                        raise ValueError(f"EvidenceAssessmentBindingMismatch: {key}")
                    models.append(assessment)
            else:
                values[(selector.artifact_hash, selector.json_pointer)] = _sourced(target)
                if (
                    selector.kind == "model_assumption"
                    and artifact.get("format") == "uarch-comparison/1"
                    and target
                ):
                    # Declarations without their own validation cannot inherit a source's rung.
                    unvalidated.append(selector)

    visit(recipe, dependencies.model_identity_hash)
    result = badge_for(
        tuple(v for group in values.values() for v in group),
        tuple(models),
        design_status=design_status,
    )
    complete = recipe.purpose == "input" or bool(models)
    # Ratios never copy source error bands; only a separately supplied ratio band could apply.
    band = None
    if not metric_path.startswith("/comparisons/") and len(models) == 1:
        band = models[0].error_band
    return replace(
        result,
        contributors=tuple(contributors.values()),
        complete=complete,
        error_band=band,
        badge="stub" if unvalidated else result.badge,
        unvalidated_assumptions=tuple(unvalidated),
    )
