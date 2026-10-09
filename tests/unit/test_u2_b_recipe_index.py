"""Private index equivalence, independently expected ambiguity, no timing thresholds.

Defensive duplicate/missing declarations are constructed below the public dependency
validator intentionally; runtime report entry points still validate all inputs.
"""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from uarch_contract.hashing import content_hash, review_subject_hash
from uarch_contract.report_context import DependencySelector, MetricRecipe

from rkuarch.provenance.badge import MetricAssessment, badge_for
from rkuarch.report.evaluation import Evaluator
from rkuarch.table.artifacts import load_verified_report_inputs

ROOT = Path(__file__).resolve().parents[2]


def prior_scan(self, path: str) -> MetricAssessment:
    exact = [r for r in self.v.dependencies.recipes if r.metric_path == path]
    parts = path.split("/")
    generic = "/rows/*/" + "/".join(parts[3:]) if len(parts) > 3 and parts[1] == "rows" else None
    choices = exact + [r for r in self.v.dependencies.recipes if r.metric_path == generic]
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


@pytest.fixture(scope="module")
def verified():
    return load_verified_report_inputs(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json")


def with_recipes(v, recipes):
    deps = v.dependencies.model_copy(update={"recipes": tuple(recipes)})
    review = dict(
        format="uarch-evidence-review/1",
        reviewer="synthetic index control",
        independent=True,
        decision="accepted",
        rationale="Test only; no real eligibility.",
        reviewed_subject_hashes=[review_subject_hash(deps)],
    )
    review["review_hash"] = content_hash(review)
    deps = deps.model_copy(update={"review_hash": review["review_hash"]})
    deps = deps.model_copy(
        update={"dependencies_hash": content_hash(deps, exclude=("dependencies_hash",))}
    )
    store = dict(v.artifacts, **{review["review_hash"]: review})
    return v._replace(dependencies=deps, artifacts=store)


def declaration(v, path, pointer="/clock_domains/core/freq_hz"):
    return MetricRecipe(
        metric_path=path,
        purpose="input",
        granularity="input",
        applicable_dimensions=("model_identity",),
        selectors=(
            DependencySelector(
                kind="hardware_leaf", artifact_hash=v.table.hardware_spec_hash, json_pointer=pointer
            ),
        ),
    )


@pytest.mark.parametrize("case", ["exact", "generic", "both", "missing", "duplicate", "same"])
def test_exact_generic_order_multiplicity_and_full_assessment(verified, case):
    path = "/rows/0/test_input"
    exact = declaration(verified, path)
    generic = declaration(verified, "/rows/*/test_input")
    recipes = {
        "exact": [exact],
        "generic": [generic],
        "both": [generic, exact],
        "missing": [declaration(verified, "/unrelated")],
        "duplicate": [exact, exact],
        "same": [generic],
    }[case]
    if case == "same":
        path = "/rows/*/test_input"
    v = with_recipes(verified, recipes)
    e = Evaluator(v)
    actual = e.metric(path)
    assert actual == prior_scan(Evaluator(v), path)
    if case in ("exact", "generic"):
        recipe = recipes[0].model_copy(update={"metric_path": path})
        expected = e.recipe(recipe, v.dependencies.model_identity_hash)
        assert actual == expected
        assert actual.complete and actual.display_recipe
        assert actual.contributors == exact.selectors
        assert actual.badge == "stub" and actual.error_band is None
    else:
        expected = replace(
            badge_for((), (), design_status=v.hardware.design_status),
            complete=False,
            display_recipe=False,
        )
        assert actual == expected
        assert not actual.contributors


class CountedRecipes(tuple):
    def __iter__(self):
        self.iterations += 1
        return super().__iter__()


def test_declarations_indexed_once_no_assessment_cache(verified, monkeypatch):
    recipes = CountedRecipes((declaration(verified, "/one"), declaration(verified, "/two")))
    recipes.iterations = 0
    v = with_recipes(verified, recipes)
    # Instrument only the verified declaration sequence, not permission/source checks.
    deps = SimpleNamespace(**v.dependencies.model_dump())
    for name in type(v.dependencies).model_fields:
        setattr(deps, name, getattr(v.dependencies, name))
    deps.recipes = recipes
    e = Evaluator(v)
    # The same tuple observed by the constructor, without changing the reviewed contents.
    recipes.iterations = 0
    # Private index required: this red check does not impose an elapsed-time threshold.
    assert e._recipes_by_path["/one"] == (recipes[0],)
    e.v = v._replace(dependencies=deps)
    calls = []
    original = e.recipe

    def observed(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(e, "recipe", observed)
    for _ in range(3):
        assert e.metric("/one").complete
    assert recipes.iterations == 0
    assert len(calls) == 3


@pytest.mark.parametrize(
    "suffix,pointer",
    [
        ("duration_s", "/duration_ps"),
        ("op_results/0/duration_ps", "/per_op/0/duration_ps"),
        ("counts/matrix_ops", "/counts/matrix_ops"),
    ],
)
def test_generic_row_filter_pointer_expansion_and_all_contributors(verified, suffix, pointer):
    selectors = tuple(
        DependencySelector(kind="result_field", artifact_hash=r.result_hash, json_pointer=pointer)
        for r in verified.results
    )
    terminal = declaration(verified, "/x").selectors[0]
    recipe = MetricRecipe(
        metric_path="/rows/*/" + suffix,
        purpose="duration" if "duration" in suffix else "counts",
        granularity="whole_iteration",
        applicable_dimensions=("model_identity",),
        selectors=selectors + (terminal,),
    )
    v = with_recipes(verified, [recipe])
    e = Evaluator(v)
    seen = []

    # Capture expanded recipes; independent selection asserts each exact identity/pointer.
    # Real assessment/contributor equivalence for all existing recipes is tested separately.
    def record(r, model, scopes=()):
        seen.append(r)
        return replace(
            badge_for((), (), design_status=v.hardware.design_status), contributors=r.selectors
        )

    e.recipe = record
    for i, row in enumerate(v.table.rows):
        path = f"/rows/{i}/" + suffix
        result = e.metric(path)
        expanded = seen[-1]
        assert expanded.metric_path == path
        assert expanded.selectors == tuple(
            s for s in selectors if s.artifact_hash == row.result_hash
        ) + (terminal,)
        assert result == prior_scan(e, path)


def test_all_existing_recipe_assessments_equal_scan(verified):
    indexed = Evaluator(verified)
    scanned = Evaluator(verified)
    for recipe in verified.dependencies.recipes:
        paths = (
            [
                recipe.metric_path.replace("/rows/*/", f"/rows/{i}/")
                for i in range(len(verified.table.rows))
            ]
            if recipe.metric_path.startswith("/rows/*/")
            else [recipe.metric_path]
        )
        for path in paths:
            assert indexed.metric(path) == prior_scan(scanned, path)


def test_index_keeps_original_declaration_order_and_multiplicity(verified):
    first = declaration(verified, "/one")
    other = declaration(verified, "/two")
    distinct = first.model_copy(update={"granularity": "whole_iteration"})
    v = with_recipes(verified, (first, other, distinct, first))
    e = Evaluator(v)
    assert e._recipes_by_path == {"/one": (first, distinct, first), "/two": (other,)}
    actual = e.metric("/one")
    assert actual == prior_scan(Evaluator(v), "/one")
    assert not actual.complete and not actual.display_recipe and not actual.contributors
