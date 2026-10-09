"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field, model_validator

from .assumptions import ModelIdentity
from .common import FrozenModel
from .hashing import _detach_json, _ResolutionSession

if TYPE_CHECKING:
    from .comparison import ComparisonArtifact, ReferenceInventory


class DependencySelector(FrozenModel):
    artifact_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    json_pointer: Annotated[str, Field(min_length=1, pattern="\\S")]
    kind: Literal[
        "hardware_leaf", "prepared_content", "model_assumption", "model_evidence", "result_field"
    ]


class MetricRecipe(FrozenModel):
    applicable_dimensions: Annotated[
        Annotated[
            tuple[Annotated[str, Field(min_length=1, pattern="\\S")], ...], Field(min_length=1)
        ],
        Field(json_schema_extra={"uniqueItems": True}),
    ]
    granularity: Literal["operator", "whole_iteration", "input"]
    metric_path: Annotated[str, Field(min_length=1, pattern="\\S")]
    purpose: Literal["duration", "counts", "diagnostics", "energy", "input"]
    selectors: Annotated[tuple[DependencySelector, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def accepted_semantics(self) -> MetricRecipe:
        if len(set(self.applicable_dimensions)) != len(self.applicable_dimensions):
            raise ValueError("IncompleteMetricContributors: duplicate applicable dimension")
        return self


class SourceMetricRecipe(FrozenModel):
    artifact_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    model_identity_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    recipe: MetricRecipe


class MetricDependencies(FrozenModel):
    dependencies_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-metric-dependencies/1"]
    model_identity_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    recipes: Annotated[tuple[MetricRecipe, ...], Field(min_length=1)]
    review_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    source_recipes: tuple[SourceMetricRecipe, ...]
    version: Annotated[str, Field(min_length=1, pattern="\\S")]


class ReportContext(FrozenModel):
    assumptions_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    comparison_hashes: Annotated[
        tuple[Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")], ...], Field(min_length=0)
    ]
    context_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    evidence_index: dict[str, Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]]
    family_registry_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-report-context/2"]
    limitations: Annotated[
        tuple[Annotated[str, Field(min_length=1, pattern="\\S")], ...], Field(min_length=1)
    ]
    metric_dependencies_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    model_identity: ModelIdentity
    request_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    used_energy_families: Annotated[
        Annotated[
            tuple[Literal["mac", "sram", "noc_hop", "dram", "static"], ...], Field(min_length=0)
        ],
        Field(json_schema_extra={"uniqueItems": True}),
    ]
    verification_hashes: Annotated[
        tuple[Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")], ...], Field(min_length=0)
    ]

    @model_validator(mode="after")
    def unique_values(self) -> ReportContext:
        if len(set(self.used_energy_families)) != len(self.used_energy_families):
            raise ValueError("Duplicate values: used_energy_families")
        return self


class RenderSpec(FrozenModel):
    allow_synthetic_presentation: Annotated[bool, Field(strict=True)]
    format: Literal["uarch-render/1"]
    locale: Literal["en"]
    number_format: Literal["roundtrip-display/1"]
    render_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    renderer_version: Annotated[str, Field(min_length=1, pattern="\\S")]
    report_context_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    show_unvalidated_predictions: Annotated[bool, Field(strict=True)]
    table_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    DependencySelector,
    MetricRecipe,
    SourceMetricRecipe,
    MetricDependencies,
    ReportContext,
    RenderSpec,
)

for _model in (
    DependencySelector,
    MetricRecipe,
    SourceMetricRecipe,
    MetricDependencies,
    ReportContext,
    RenderSpec,
):
    _model.model_rebuild()


class _ReportResolution(_ResolutionSession):
    """Parsed models/indexes are private to the same authenticated resolution lifetime."""

    def __init__(self, artifacts: object) -> None:
        super().__init__(artifacts)
        self._comparisons: dict[str, ComparisonArtifact] = {}
        self._inventories: dict[str, ReferenceInventory] = {}
        self._fixture_indices: dict[str, dict[str, int]] = {}

    def _comparison(self, identity: str) -> ComparisonArtifact:
        from .comparison import ComparisonArtifact

        if identity not in self._comparisons:
            self._comparisons[identity] = ComparisonArtifact.model_validate(self._resolve(identity))
        return self._comparisons[identity]

    def _inventory(self, identity: str, path: str) -> tuple[ReferenceInventory, dict[str, int]]:
        from .comparison import ReferenceInventory, _refuse

        if identity not in self._inventories:
            inventory = ReferenceInventory.model_validate(self._resolve(identity))
            indices = {fixture.fixture_id: i for i, fixture in enumerate(inventory.fixtures)}
            if len(indices) != len(inventory.fixtures):
                _refuse("IncompleteMetricContributors", path + "/reference fixture")
            self._inventories[identity] = inventory
            self._fixture_indices[identity] = indices
        return self._inventories[identity], self._fixture_indices[identity]


def _ratio_location(recipe: MetricRecipe) -> tuple[int, int, int] | None:
    import re

    from .comparison import _refuse

    if not recipe.metric_path.startswith("/comparisons/"):
        return None
    match = re.fullmatch(
        r"/comparisons/(0|[1-9][0-9]*)/fixtures/(0|[1-9][0-9]*)/channels/(0|[1-9][0-9]*)/"
        r"(raw_rel|residual_rel|signed_adjustment_rel|absolute_adjustment_rel)",
        recipe.metric_path,
    )
    if match is None:
        _refuse("MissingMetricRecipe", recipe.metric_path)
    return int(match[1]), int(match[2]), int(match[3])


def _reachable_selectors(
    recipe: MetricRecipe, sources: dict[tuple[str, str], SourceMetricRecipe]
) -> tuple[DependencySelector, ...]:
    """Retain intermediate source identities as well as terminal contributors."""
    from .comparison import _refuse

    def walk(current: MetricRecipe, stack: tuple[tuple[str, str], ...]) -> list[DependencySelector]:
        result = list(current.selectors)
        for selector in current.selectors:
            if selector.kind != "result_field":
                continue
            key = selector.artifact_hash, selector.json_pointer
            if key in stack:
                _refuse("CyclicMetricRecipe", str(key))
            if key not in sources:
                _refuse("MissingSourceMetricRecipe", str(key))
            result.extend(walk(sources[key].recipe, stack + (key,)))
        return result

    return tuple(walk(recipe, ()))


def _verify_ratio_sources(
    recipe: MetricRecipe,
    comparison_hash: str,
    artifacts: object,
    sources: dict[tuple[str, str], SourceMetricRecipe],
) -> None:
    """Require the exact actual/reference/adjustment identities in this ratio's closure."""
    from .comparison import _refuse, _validate_actual_source
    from .hashing import content_hash, resolve_artifact

    if not isinstance(artifacts, _ReportResolution):
        artifacts = _ReportResolution(artifacts)
    location = _ratio_location(recipe)
    assert location is not None
    _, fixture_index, channel_index = location
    comparison = artifacts._comparison(comparison_hash)
    if fixture_index >= len(comparison.fixtures):
        _refuse("IncompleteMetricContributors", recipe.metric_path + "/fixture index")
    fixture = comparison.fixtures[fixture_index]
    if channel_index >= len(fixture.channels):
        _refuse("IncompleteMetricContributors", recipe.metric_path + "/channel index")
    channel = fixture.channels[channel_index]
    purpose = "duration" if channel.channel == "duration_s" else "counts"
    if recipe.purpose != purpose:
        _refuse("MetricPurposeMismatch", recipe.metric_path)
    inventory, indices = artifacts._inventory(
        comparison.reference_inventory_hash, recipe.metric_path
    )
    if fixture.fixture_id not in indices:
        _refuse("IncompleteMetricContributors", recipe.metric_path + "/reference fixture")
    reference_index = indices[fixture.fixture_id]
    reference = inventory.fixtures[reference_index]
    if (
        inventory.reference_model != comparison.reference_model
        or any(
            getattr(reference, key) != getattr(fixture, key)
            for key in ("component_binding_hash", "precision", "query", "tp", "projection_scope")
        )
        or channel.reference != getattr(reference.values, channel.channel)
    ):
        _refuse("RefusalSourceMismatch", recipe.metric_path + "/reference inventory channel")
    _validate_actual_source(channel, fixture, comparison.track, artifacts)
    selectors = _reachable_selectors(recipe, sources)
    reachable = {(s.kind, s.artifact_hash, s.json_pointer) for s in selectors}
    anchors = {
        selector.artifact_hash
        for selector in selectors
        if selector.kind == "model_assumption"
        and resolve_artifact(selector.artifact_hash, artifacts).get("format")
        == "uarch-comparison/1"
    }
    if anchors != {comparison_hash}:
        _refuse("IncompleteMetricContributors", recipe.metric_path + "/bound comparison identity")
    reference_pointer = f"/fixtures/{reference_index}/values/{channel.channel}/value"
    required = [
        (inventory.inventory_hash, reference_pointer, content_hash(inventory.reference_model))
    ]
    if channel.actual.state == "known":
        assert channel.actual.source_hash is not None and channel.actual.source_pointer is not None
        required.append(
            (
                channel.actual.source_hash,
                channel.actual.source_pointer,
                content_hash(comparison.candidate),
            )
        )
    for identity, pointer, model_hash in required:
        if ("result_field", identity, pointer) not in reachable:
            _refuse(
                "IncompleteMetricContributors", recipe.metric_path + "/required source " + pointer
            )
        source = sources[(identity, pointer)]
        if source.model_identity_hash != model_hash:
            _refuse("IncompleteMetricContributors", recipe.metric_path + "/source model identity")
    adjustment_pointer = f"/fixtures/{fixture_index}/channels/{channel_index}/declared_deviations"
    if (
        channel.declared_deviations
        and ("model_assumption", comparison_hash, adjustment_pointer) not in reachable
    ):
        _refuse("IncompleteMetricContributors", recipe.metric_path + "/adjustment declarations")
    # An empty list adds no phantom claim, but a supplied declaration still names this channel.
    for selector in selectors:
        if selector.kind == "model_assumption" and selector.artifact_hash == comparison_hash:
            if selector.json_pointer != adjustment_pointer:
                _refuse("IncompleteMetricContributors", recipe.metric_path + "/adjustment source")


def validate_metric_dependencies(
    value: object, artifacts: object
) -> dict[str, tuple[DependencySelector, ...]]:
    """Verify reviewed source-recipe closure and return original terminal selectors.

    This is not an applicability/badge evaluator. B must retain each source recipe's
    model, granularity and scope when evaluating the returned union; it must not use
    the primary context model in place of a source model. Source recipes do not grant
    display permission. Only top-level recipes appear as keys in the return value.
    Comparison ratios require their exact actual/reference sources in the recursive
    closure, under the explicitly declared comparison identity. ReportContext additionally
    binds that identity to the comparison index; no ambient artifact search is used.
    """
    return _validate_metric_dependencies(_detach_json(value), _ReportResolution(artifacts))


def _validate_metric_dependencies(
    value: object, artifacts: _ReportResolution
) -> dict[str, tuple[DependencySelector, ...]]:
    from .comparison import _refuse
    from .hashing import (
        content_hash,
        resolve_artifact,
        resolve_pointer,
        verify_identity,
        verify_review,
    )

    d = MetricDependencies.model_validate(value)
    verify_identity(d, "dependencies_hash")
    verify_review(d, artifacts)
    sources: dict[tuple[str, str], SourceMetricRecipe] = {}
    for source in d.source_recipes:
        key = (source.artifact_hash, source.recipe.metric_path)
        if key in sources:
            _refuse("AmbiguousSourceMetricRecipe", str(key))
        sources[key] = source
    if len({r.metric_path for r in d.recipes}) != len(d.recipes):
        _refuse("MissingMetricRecipe", "duplicate render target")

    def visit(
        recipe: MetricRecipe, stack: tuple[tuple[str, str], ...], model: str | None = None
    ) -> tuple[DependencySelector, ...]:
        if len(set(recipe.applicable_dimensions)) != len(recipe.applicable_dimensions):
            _refuse("IncompleteMetricContributors", "duplicate applicable_dimensions")
        leaves: list[DependencySelector] = []
        for selector in recipe.selectors:
            artifact = resolve_artifact(selector.artifact_hash, artifacts)
            target = resolve_pointer(artifact, selector.json_pointer)
            if selector.kind == "result_field":
                key = (selector.artifact_hash, selector.json_pointer)
                if key in stack:
                    _refuse("CyclicMetricRecipe", str(key))
                if key not in sources:
                    _refuse("MissingSourceMetricRecipe", str(key))
                source = sources[key]
                if source.recipe.purpose != recipe.purpose:
                    _refuse("MetricPurposeMismatch", str(key))
                leaves.extend(visit(source.recipe, stack + (key,), source.model_identity_hash))
            else:
                if selector.kind == "model_evidence" and model is not None:
                    from .assumptions import ModelIdentity

                    identity = ModelIdentity.model_validate(target)
                    if content_hash(identity) != model:
                        _refuse("IncompleteMetricContributors", "source model identity")
                if selector.kind == "hardware_leaf":
                    from .sourced import SourcedValue

                    SourcedValue.model_validate(target)
                leaves.append(selector)
        if model is not None:
            kinds = {x.kind for x in leaves}
            if not {"prepared_content", "model_assumption", "model_evidence"} <= kinds:
                _refuse("IncompleteMetricContributors", recipe.metric_path + "/model/workload")
            models = [
                resolve_pointer(resolve_artifact(x.artifact_hash, artifacts), x.json_pointer)
                for x in leaves
                if x.kind == "model_evidence"
            ]
            if recipe.purpose == "duration" and any(
                x["name"] == "physical-resolved" for x in models
            ):
                # Required original physical timing inputs; a new review cannot remove these.
                paths = {x.json_pointer for x in leaves if x.kind == "hardware_leaf"}
                required = {
                    "/cores/grid/rows",
                    "/cores/grid/cols",
                    "/clock_domains/core/freq_hz",
                    "/cores/core_type/vector_engine/ops_per_cycle",
                    "/memory/dram/bw_bytes_per_s",
                }
                if not required <= paths or not any(
                    x.startswith("/cores/core_type/matrix_engine/macs_per_cycle/") for x in paths
                ):
                    _refuse("IncompleteMetricContributors", recipe.metric_path + "/timing inputs")
        return tuple({(x.kind, x.artifact_hash, x.json_pointer): x for x in leaves}.values())

    # Verify all declared source recipes, including currently undisplayed sources.
    for key, source in sources.items():
        resolve_pointer(
            resolve_artifact(source.artifact_hash, artifacts), source.recipe.metric_path
        )
        visit(source.recipe, (key,), source.model_identity_hash)
    result = {recipe.metric_path: visit(recipe, ()) for recipe in d.recipes}
    for recipe in d.recipes:
        if _ratio_location(recipe) is None:
            continue
        # Standalone dependency validation has no ambient ReportContext. The existing
        # explicit comparison declaration selector supplies its comparison identity.
        anchors = {
            selector.artifact_hash
            for selector in _reachable_selectors(recipe, sources)
            if selector.kind == "model_assumption"
            and resolve_artifact(selector.artifact_hash, artifacts).get("format")
            == "uarch-comparison/1"
        }
        if len(anchors) != 1:
            _refuse("IncompleteMetricContributors", recipe.metric_path + "/comparison identity")
        _verify_ratio_sources(recipe, next(iter(anchors)), artifacts, sources)
    return result


def validate_report_context(value: object, artifacts: object) -> ReportContext:
    """Bind exact comparison display paths to channels before dependency evaluation.

    Verifies identities and reviewed recipe declarations; B owns evidence applicability,
    badges, error bands and whether an otherwise verified metric may be displayed.
    """
    artifacts = _ReportResolution(artifacts)
    value = _detach_json(value)
    from .comparison import _refuse
    from .hashing import (
        content_hash,
        resolve_artifact,
        verify_identity,
        verify_review,
    )

    context = ReportContext.model_validate(value)
    verify_identity(context, "context_hash")
    d = MetricDependencies.model_validate(
        resolve_artifact(context.metric_dependencies_hash, artifacts)
    )
    verify_review(d, artifacts)
    if d.model_identity_hash != content_hash(context.model_identity):
        _refuse("IncompleteMetricContributors", "primary model identity")
    _validate_metric_dependencies(d, artifacts)
    sources = {(s.artifact_hash, s.recipe.metric_path): s for s in d.source_recipes}
    for recipe in d.recipes:
        location = _ratio_location(recipe)
        if location is None:
            continue
        comparison_index = location[0]
        if comparison_index >= len(context.comparison_hashes):
            _refuse("IncompleteMetricContributors", "comparison index")
        _verify_ratio_sources(
            recipe, context.comparison_hashes[comparison_index], artifacts, sources
        )
    return context
