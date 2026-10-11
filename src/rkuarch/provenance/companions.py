"""Pure externally reviewed STUB companion assembly; no review issuance or IO.

The entire explicit artifact intake is retained. Comparison hashes enumerate ALL
supplied comparison artifacts; absence says nothing about withheld external history.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from uarch_contract.comparison import ComparisonArtifact, validate_comparison
from uarch_contract.errors import ArtifactHashMismatch, IncompleteMetricContributors
from uarch_contract.evidence import ReviewRecord
from uarch_contract.hashing import (
    artifact_identity,
    canonical_json,
    content_hash,
    resolve_artifact,
    sha256,
    strict_json_loads,
    verify_identity,
    verify_review,
)
from uarch_contract.model_card import ModelCard
from uarch_contract.registry import FamilyRegistry
from uarch_contract.report_context import (
    DependencySelector,
    MetricDependencies,
    MetricRecipe,
    ReportContext,
    validate_metric_dependencies,
)
from uarch_contract.request import CharacterizationRequest

from rkuarch.table.artifacts import verify_report_inputs
from rkuarch.table.build import (
    CapturedWork,
    build_table,
    captured_artifacts,
    consumed_energy_families,
    source_scopes,
    table_recipes,
)

from .model_card import validate_production_model_card


def _put(store: dict[str, Any], value: Any) -> None:
    data = strict_json_loads(canonical_json(value))
    key = artifact_identity(data)
    resolve_artifact(key, {key: data})
    if key in store and store[key] != data:
        raise ArtifactHashMismatch("ArtifactHashMismatch: companion collision")
    store[key] = data


def _accepted_review(value: MetricDependencies | FamilyRegistry, store: Mapping[str, Any]) -> None:
    verify_review(value, store)
    review = ReviewRecord.model_validate(resolve_artifact(value.review_hash, store))
    if review.decision != "accepted" or not review.independent:
        raise ValueError("UnacceptedReview: exact independent accepted declaration review required")


def _key(selector: DependencySelector) -> tuple[str, str, str]:
    return selector.kind, selector.artifact_hash, selector.json_pointer


def _scope(recipe: MetricRecipe) -> tuple[str, str, frozenset[str]]:
    return recipe.purpose, recipe.granularity, frozenset(recipe.applicable_dimensions)


def _intrinsic(captured: CapturedWork, dependencies: MetricDependencies, family: str) -> None:
    """Match A's actual declarations; allow reviewed recursive factoring, not source borrowing."""
    exact, expected_sources = table_recipes(captured)
    generic, _ = table_recipes(captured, generic_rows=True)
    sources = {(s.artifact_hash, s.recipe.metric_path): s for s in dependencies.source_recipes}
    recipes = {r.metric_path: r for r in dependencies.recipes}
    scopes = source_scopes(captured, family=family)

    def leaves(recipe: MetricRecipe, model: str) -> set[tuple[str, str, str]]:
        # validate_metric_dependencies already authenticates pointers and rejects cycles.
        result = set()
        for selector in recipe.selectors:
            if selector.kind == "result_field":
                child = sources[(selector.artifact_hash, selector.json_pointer)]
                if child.model_identity_hash != model or _scope(child.recipe) != _scope(recipe):
                    raise IncompleteMetricContributors("IncompleteMetricContributors: source model")
                result.update(leaves(child.recipe, model))
            else:
                result.add(_key(selector))
        return result

    for expected in expected_sources:
        key = expected.artifact_hash, expected.recipe.metric_path
        supplied = sources.get(key)
        if (
            supplied is None
            or supplied.model_identity_hash != expected.model_identity_hash
            or _scope(supplied.recipe) != _scope(expected.recipe)
            or leaves(supplied.recipe, expected.model_identity_hash)
            != {_key(s) for s in expected.recipe.selectors}
        ):
            raise IncompleteMetricContributors(
                "IncompleteMetricContributors: exact captured source"
            )
        if not scopes[key] or any(
            case.family != family
            or case.model_identity_hash != expected.model_identity_hash
            or case.hardware_spec_hash != captured.request.hardware_spec_hash
            or case.prepared_bundle_hash != captured.bundle.bundle_hash
            for case in scopes[key]
        ):
            raise IncompleteMetricContributors("IncompleteMetricContributors: captured scopes")
    allowed = {r.metric_path: r for r in (*exact, *generic)}
    for path, recipe in recipes.items():
        if path.startswith("/comparisons/"):
            continue
        expected_recipe = allowed.get(path)
        if (
            expected_recipe is None
            or _scope(recipe) != _scope(expected_recipe)
            or {_key(s) for s in recipe.selectors} != {_key(s) for s in expected_recipe.selectors}
        ):
            raise IncompleteMetricContributors("IncompleteMetricContributors: exact row recipe")
    for expected_recipe in exact:
        path = expected_recipe.metric_path
        wildcard = "/rows/*/" + path.split("/", 3)[3]
        if sum(p in recipes for p in (path, wildcard)) != 1:
            raise IncompleteMetricContributors(
                "IncompleteMetricContributors: missing/ambiguous row"
            )


def assemble_stub_context(
    captured: CapturedWork,
    *,
    dependencies: MetricDependencies,
    registry: FamilyRegistry,
    model_card: ModelCard,
    comparison_hashes: tuple[str, ...],
    artifacts: Mapping[str, Any],
) -> tuple[ReportContext, Mapping[str, Any]]:
    """Authenticate externally reviewed declarations through existing public validators.

    Recipes must already address comparisons in lexicographically sorted hash order.
    Sorting the requested hashes cannot rewrite reviewed recipe paths or subjects.
    The returned mapping owns detached JSON values and retains every supplied member.
    No evidence, review, family assignment, measurement or positive badge is inferred.
    """
    store: dict[str, Any] = {}
    for key, value in artifacts.items():
        if isinstance(value, bytes):
            if sha256(value) != key:
                raise ArtifactHashMismatch("ArtifactHashMismatch: supplied raw blob")
            store[key] = value
        else:
            store[key] = strict_json_loads(canonical_json(resolve_artifact(key, artifacts)))
    dependencies = MetricDependencies.model_validate(dependencies.model_dump(mode="json"))
    registry = FamilyRegistry.model_validate(registry.model_dump(mode="json"))
    model_card = ModelCard.model_validate(model_card.model_dump(mode="json"))
    verify_identity(dependencies, "dependencies_hash")
    verify_identity(registry, "registry_hash")
    _accepted_review(dependencies, store)
    _accepted_review(registry, store)
    if (
        not captured.jobs
        or len(captured.jobs) != len(captured.results)
        or tuple(j.point.payload_hash for j in captured.jobs)
        != tuple(p.payload_hash for p in captured.bundle.points)
        or any(
            r.job_hash != j.job_hash for j, r in zip(captured.jobs, captured.results, strict=True)
        )
        or captured.request
        != CharacterizationRequest(
            **captured.bundle.intent.model_dump(mode="json"),
            prepared_input_hash=captured.bundle.bundle_hash,
        )
    ):
        raise ValueError("CapturedWorkMismatch: complete ordered request/job/result correspondence")
    for value in captured_artifacts(captured).values():
        _put(store, value)
    for value in (captured.bundle.hardware_spec, dependencies, registry, model_card):
        _put(store, value)
    families = [
        e.family
        for e in registry.entries
        if e.hardware_spec_hash == captured.request.hardware_spec_hash
    ]
    if len(families) != 1:
        raise ValueError("AmbiguousFamily: exactly one reviewed hardware family required")
    supplied = {
        h
        for h, value in store.items()
        if isinstance(value, dict) and value.get("format") == "uarch-comparison/1"
    }
    if len(set(comparison_hashes)) != len(comparison_hashes) or supplied != set(comparison_hashes):
        raise ValueError(
            "ComparisonIntakeMismatch: enumerate every supplied comparison exactly once"
        )
    ordered = tuple(sorted(comparison_hashes))
    expected_paths: set[str] = set()
    for index, identity in enumerate(ordered):
        value = ComparisonArtifact.model_validate(resolve_artifact(identity, store))
        comparison = validate_comparison(
            value, resolve_artifact(value.reference_inventory_hash, store), store
        )
        expected_paths.update(
            f"/comparisons/{index}/fixtures/{fi}/channels/{ci}/{quantity}"
            for fi, fixture in enumerate(comparison.fixtures)
            for ci, _ in enumerate(fixture.channels)
            for quantity in (
                "raw_rel",
                "residual_rel",
                "signed_adjustment_rel",
                "absolute_adjustment_rel",
            )
        )
    actual_paths = {
        r.metric_path for r in dependencies.recipes if r.metric_path.startswith("/comparisons/")
    }
    if actual_paths != expected_paths:
        raise IncompleteMetricContributors(
            "IncompleteMetricContributors: complete comparison recipes"
        )
    validate_metric_dependencies(dependencies, store)
    _intrinsic(captured, dependencies, families[0])
    data = dict(
        format="uarch-report-context/2",
        context_hash="sha256:" + "0" * 64,
        request_hash=content_hash(captured.request),
        assumptions_hash=captured.assumptions.assumptions_hash,
        model_identity=captured.assumptions.model.model_dump(mode="json"),
        metric_dependencies_hash=dependencies.dependencies_hash,
        family_registry_hash=registry.registry_hash,
        comparison_hashes=ordered,
        evidence_index={},
        verification_hashes=[],
        used_energy_families=consumed_energy_families(captured),
        limitations=[
            "Externally reviewed declarations; no measurement or model-accuracy validation.",
            "All supplied comparisons retained; withheld external attempt history "
            "is not authenticated.",
            "STUB predictions; error band unknown; energy unverified.",
        ],
    )
    data["context_hash"] = content_hash(data, exclude=("context_hash",))
    context = ReportContext.model_validate(data)
    _put(store, context)
    validate_production_model_card(model_card, captured=captured, context=context, artifacts=store)
    package = build_table(captured, context=context, model_card=model_card, artifacts=store)
    verified = verify_report_inputs(package.table, package.artifacts)
    for value in verified.artifacts.values():
        if not isinstance(value, bytes):
            _put(store, value)
    return context, MappingProxyType(dict(sorted(store.items())))
