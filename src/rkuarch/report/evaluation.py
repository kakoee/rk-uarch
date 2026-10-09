"""Report-local assessment of verified A carriers; no loader or execution fallback."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.evidence import EvidenceScopeCase
from uarch_contract.hashing import content_hash, resolve_pointer
from uarch_contract.report_context import DependencySelector, MetricRecipe

from rkuarch.provenance.applicability import EvidenceAssessment, _accepted_review, assess_evidence
from rkuarch.provenance.badge import ORDER, MetricAssessment, _sourced, badge_for
from rkuarch.table.artifacts import VerifiedReportInputs
from rkuarch.table.build import CapturedWork, source_scopes


def combine_assessments(
    items: tuple[MetricAssessment, ...], design_status: str
) -> MetricAssessment:
    """Union exact sources, never average badges or transfer an error band to a ratio."""
    result = badge_for(
        tuple(x for a in items for x in a.claims + a.conditional_on),
        tuple(m for a in items for m in a.models),
        design_status=design_status,
    )
    return replace(
        result,
        badge=min(
            (result.badge, *(a.badge for a in items if a.nonempty or a.unvalidated_assumptions)),
            key=ORDER.__getitem__,
        ),
        unvalidated_assumptions=tuple(
            dict.fromkeys(s for a in items for s in a.unvalidated_assumptions)
        ),
        contributors=tuple(dict.fromkeys(s for a in items for s in a.contributors)),
        complete=bool(items) and all(a.complete for a in items),
        display_recipe=bool(items) and all(a.display_recipe for a in items),
        synthetic=any(a.synthetic for a in items),
        error_band=None,
    )


class Evaluator:
    """Uses exact result-pointer scopes, retaining source model/purpose/granularity."""

    def __init__(self, v: VerifiedReportInputs):
        self.v = v
        if not _accepted_review(v.dependencies, v.artifacts) or not _accepted_review(
            v.registry, v.artifacts
        ):
            raise ValueError("ReviewNotAccepted: report dependencies/registry")
        family = [
            e.family
            for e in v.registry.entries
            if e.hardware_spec_hash == v.table.hardware_spec_hash
        ]
        if len(family) != 1:
            raise ValueError("AmbiguousFamily: report hardware")
        captured = CapturedWork(v.bundle, v.assumptions, v.request, v.derivation, v.jobs, v.results)
        self.scopes = source_scopes(captured, family=family[0])
        self.sources = {
            (s.artifact_hash, s.recipe.metric_path): s for s in v.dependencies.source_recipes
        }
        for key, scopes in self.scopes.items():
            source = self.sources.get(key)
            if source is None:
                raise ValueError("MissingSourceMetricRecipe: captured scope")
            if any(s.model_identity_hash != source.model_identity_hash for s in scopes):
                raise ValueError("SourceScopeMismatch: captured source identity")
        by_path: dict[str, list[MetricRecipe]] = {}
        for recipe in v.dependencies.recipes:
            by_path.setdefault(recipe.metric_path, []).append(recipe)
        self._recipes_by_path = {path: tuple(recipes) for path, recipes in by_path.items()}
        self.cache: dict[tuple[str, str], MetricAssessment] = {}
        self.leaves: dict[tuple[str, str], Any] = {}

    def target(self, selector: DependencySelector) -> Any:
        key = (selector.artifact_hash, selector.json_pointer)
        if key not in self.leaves:
            self.leaves[key] = resolve_pointer(
                self.v.artifacts[selector.artifact_hash], selector.json_pointer
            )
        return self.leaves[key]

    def source(self, key: tuple[str, str]) -> MetricAssessment:
        if key in self.cache:
            return self.cache[key]
        source = self.sources[key]
        result = self.recipe(source.recipe, source.model_identity_hash, self.scopes.get(key, ()))
        anchor = DependencySelector(kind="result_field", artifact_hash=key[0], json_pointer=key[1])
        result = replace(result, contributors=(anchor,) + result.contributors)
        self.cache[key] = result
        return result

    def recipe(
        self, r: MetricRecipe, model: str, scopes: tuple[EvidenceScopeCase, ...] = ()
    ) -> MetricAssessment:
        values = []
        models = []
        contributors = []
        nested = []
        unvalidated = []
        for selector in r.selectors:
            if selector.kind == "result_field":
                nested.append(self.source((selector.artifact_hash, selector.json_pointer)))
                continue
            target = self.target(selector)
            contributors.append(selector)
            if selector.kind == "model_evidence":
                identity = content_hash(ModelIdentity.model_validate(target))
                if identity != model:
                    raise ValueError("SourceScopeMismatch: recipe/model")
                if any(s.model_identity_hash != identity for s in scopes):
                    raise ValueError("SourceScopeMismatch: scope/model")
                if scopes:
                    evidence = assess_evidence(
                        self.v.context,
                        scopes,
                        purpose=r.purpose,
                        channel=None,
                        granularity=r.granularity,
                        dimensions=r.applicable_dimensions,
                        artifacts=self.v.artifacts,
                        allow_synthetic=False,
                    )
                else:
                    evidence = EvidenceAssessment(
                        "stub",
                        identity,
                        r.purpose,
                        r.granularity,
                        reasons=("source scope unavailable",),
                    )
                models.append(evidence)
            else:
                values.extend(_sourced(target))
                if (
                    selector.kind == "model_assumption"
                    and self.v.artifacts[selector.artifact_hash].get("format")
                    == "uarch-comparison/1"
                    and target
                ):
                    unvalidated.append(selector)
        result = badge_for(
            tuple(values), tuple(models), design_status=self.v.hardware.design_status
        )
        result = replace(
            result,
            contributors=tuple(contributors),
            complete=r.purpose == "input" or bool(models or nested),
            unvalidated_assumptions=tuple(unvalidated),
        )
        if nested:
            result = combine_assessments((result,) + tuple(nested), self.v.hardware.design_status)
        if unvalidated:
            result = replace(result, badge="stub", error_band=None)
        return result

    def metric(self, path: str) -> MetricAssessment:
        parts = path.split("/")
        generic = (
            "/rows/*/" + "/".join(parts[3:]) if len(parts) > 3 and parts[1] == "rows" else None
        )
        choices = self._recipes_by_path.get(path, ()) + (
            self._recipes_by_path.get(generic, ()) if generic is not None else ()
        )
        if len(choices) != 1:
            return replace(
                badge_for((), (), design_status=self.v.hardware.design_status),
                complete=False,
                display_recipe=False,
            )
        recipe = choices[0]
        if recipe.metric_path == generic:
            row = self.v.table.rows[int(parts[2])]
            # Generic declarations enumerate all exact row sources. Select this row's
            # recorded result while retaining any other explicit terminal contributors.
            pointer = "/" + "/".join(parts[3:])
            pointer = (
                pointer.replace("/op_results/", "/per_op/")
                if pointer.startswith("/op_results/")
                else pointer.replace("_s", "_ps")
            )
            captured_results = {r.result_hash for r in self.v.results}
            selectors = tuple(
                s
                for s in recipe.selectors
                if not (
                    s.kind == "result_field"
                    and s.artifact_hash in captured_results
                    and s.artifact_hash != row.result_hash
                    and s.json_pointer == pointer
                )
            )
            if not selectors:
                raise ValueError("MissingMetricRecipe: exact row expansion")
            recipe = recipe.model_copy(update={"selectors": selectors, "metric_path": path})
        return self.recipe(recipe, self.v.dependencies.model_identity_hash)
