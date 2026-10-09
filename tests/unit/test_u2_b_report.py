"""B2 contributor/context regressions, including independently chosen R2 attacks."""

from copy import deepcopy
from itertools import product

import pytest
from uarch_contract.comparison import validate_comparison
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import ReportContext, validate_metric_dependencies
from uarch_contract.sourced import SourcedValue

from rkuarch.provenance.applicability import EvidenceAssessment
from rkuarch.provenance.badge import ORDER, assess_metric, badge_for
from rkuarch.report.render import lint_template
from tests.fixtures.u2_b.b2_support import (
    ROOT,
    metric_fixture,
    proposal_artifacts,
    put,
    review,
)


def evaluate(context, scopes, store, path):
    return assess_metric(
        context,
        path,
        scopes=scopes,
        channel="matrix_ops" if path == "/count" else "duration_s",
        artifacts=store,
        design_status="proposed",
        allow_synthetic=True,
    )


def rebind(context, store, deps):
    deps = review(store, deps, "dependencies_hash")
    c = context.model_dump(mode="json")
    c["metric_dependencies_hash"] = deps["dependencies_hash"]
    put(store, c, "context_hash")
    return ReportContext.model_validate(c)


def test_R206_S04_D07_independent_models_count_evidence_cannot_validate_zero_timing():
    context, scopes, store, deps = metric_fixture()
    count = evaluate(context, scopes, store, "/count")
    assert count.badge == "estimated" and count.claim_badge is None
    assert len({m.model_identity_hash for m in count.models}) == 2
    timing = evaluate(context, scopes, store, "/timing")
    assert timing.badge == "stub" and timing.error_band is None
    assert all(m.purpose == "duration" and m.badge == "stub" for m in timing.models)
    assert any(s.json_pointer == "/memory/dram/bw_bytes_per_s" for s in timing.contributors)
    c = context.model_dump(mode="json")
    del c["evidence_index"]["B-reference-count"]
    put(store, c, "context_hash")
    assert evaluate(ReportContext.model_validate(c), scopes, store, "/count").badge == "stub"


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("timing-hardware", "IncompleteMetricContributors"),
        ("reference-model", "IncompleteMetricContributors"),
        ("cycle", "CyclicMetricRecipe"),
        ("duplicate", "AmbiguousSourceMetricRecipe"),
        ("missing", "MissingSourceMetricRecipe"),
        ("purpose", "MetricPurposeMismatch"),
        ("review", "ReviewSubjectMismatch"),
    ],
)
def test_R201_R208_fresh_reviews_cannot_authorize_incomplete_dependencies(mutation, error):
    context, scopes, store, deps = metric_fixture()
    evaluate(context, scopes, store, "/count")
    deps = deepcopy(deps)
    if mutation == "timing-hardware":
        deps["source_recipes"][1]["recipe"]["selectors"].pop()
    elif mutation == "reference-model":
        deps["source_recipes"][2]["recipe"]["selectors"].pop()
    elif mutation == "duplicate":
        deps["source_recipes"].append(deepcopy(deps["source_recipes"][0]))
    elif mutation == "missing":
        deps["source_recipes"].pop(2)
    elif mutation == "purpose":
        deps["source_recipes"][2]["recipe"]["purpose"] = "duration"
    elif mutation == "cycle":
        # Three existing source nodes, independently reshaped into A -> B -> C -> A.
        for index in [0, 2, 3]:
            deps["source_recipes"][index]["recipe"]["purpose"] = "counts"
        for left, right in [(0, 2), (2, 3), (3, 0)]:
            target = deps["source_recipes"][right]
            deps["source_recipes"][left]["recipe"]["selectors"].append(
                dict(
                    kind="result_field",
                    artifact_hash=target["artifact_hash"],
                    json_pointer=target["recipe"]["metric_path"],
                )
            )
    elif mutation == "review":
        deps["version"] = "tampered but rehashed"
    if mutation == "review":
        put(store, deps, "dependencies_hash")
        c = context.model_dump()
        c["metric_dependencies_hash"] = deps["dependencies_hash"]
        put(store, c, "context_hash")
        context = ReportContext.model_validate(c)
    else:
        context = rebind(context, store, deps)
    with pytest.raises(ValueError, match=error):
        evaluate(context, scopes, store, "/count")


def test_R209_shared_dag_is_not_a_cycle_and_R210_hash_text_is_not_followed():
    context, scopes, store, deps = metric_fixture()
    deps = deepcopy(deps)
    deps["recipes"][0]["selectors"].append(deepcopy(deps["recipes"][0]["selectors"][0]))
    context = rebind(context, store, deps)
    result = evaluate(context, scopes, store, "/count")
    assert result.badge == "estimated"
    assert (
        len(result.contributors) == 6
    )  # source leaves deduplicated, models independently assessed
    with pytest.raises(ValueError, match="MissingMetricRecipe"):
        evaluate(context, scopes, store, "/actual/raw-value")


def test_C1_missing_reference_rehashed_review_and_valid_control():
    import json

    directory = ROOT / "docs/reviews/U2-U0003-proposal/fixtures"
    deps = json.loads((directory / "metric-dependencies.json").read_text())
    store = proposal_artifacts()
    valid = validate_metric_dependencies(deps, store)
    assert (
        len(
            {
                s.artifact_hash
                for s in valid["/comparisons/0/fixtures/0/channels/4/raw_rel"]
                if s.kind == "model_evidence"
            }
        )
        == 2
    )
    recipe = next(
        r
        for r in deps["recipes"]
        if r["metric_path"] == "/comparisons/0/fixtures/0/channels/4/raw_rel"
    )
    recipe["selectors"].pop(1)
    review(store, deps, "dependencies_hash")
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        validate_metric_dependencies(deps, store)


def test_C2_wrong_channel_source_rehashed_and_valid_control():
    import json

    directory = ROOT / "docs/reviews/U2-U0003-proposal/fixtures"
    c = json.loads((directory / "comparison-physical.json").read_text())
    inv = json.loads((directory / "comparison-inventory.json").read_text())
    store = proposal_artifacts()
    assert validate_comparison(c, inv, store).gate_outcome == "discrepancy_record_complete"
    c["fixtures"][0]["channels"][0]["actual"]["source_pointer"] = "/counts/memory_read_bytes"
    c["comparison_hash"] = content_hash(c, exclude=("comparison_hash",))
    with pytest.raises(ValueError, match="RefusalSourceMismatch"):
        validate_comparison(c, inv, store)


def test_B03_B04_B05_B06_B08_claim_model_and_ceiling_lattice():
    stip = SourcedValue(value=1, unit="ratio", kind="stipulation", rationale="independent question")
    for claim, model, status in product(
        ORDER, ["stub", "estimated", "measured"], ["proposed", "reference"]
    ):
        sv = SourcedValue(
            value=1,
            unit="ratio",
            kind="claim",
            provenance=claim,
            source=None if claim == "stub" else "synthetic-test-citation",
        )
        m = EvidenceAssessment(model, "sha256:" + "a" * 64, "counts", "whole_iteration")
        result = badge_for((sv,), (m,), design_status=status)
        assert ORDER[result.badge] <= min(ORDER[claim], ORDER[model])
        if status == "proposed":
            assert ORDER[result.badge] <= ORDER["estimated"]
            conditional = badge_for((sv, stip), (m,), design_status=status)
            assert conditional.badge == result.badge and conditional.conditional_on == (stip,)
    assert not badge_for((), (), design_status="proposed").nonempty


@pytest.mark.parametrize("source", ["{{ raw }}", "{{ metric.number }}", "{{ 137.0625 }}"])
def test_raw_template_magnitudes_are_rejected(source):
    with pytest.raises(ValueError, match="UnbadgedTemplateValue"):
        lint_template(source)


def test_pending_dependency_review_cannot_grant_display_recipe():
    context, scopes, store, deps = metric_fixture()
    review_record = deepcopy(store[deps["review_hash"]])
    review_record["decision"] = "pending"
    put(store, review_record, "review_hash")
    deps = dict(deps, review_hash=review_record["review_hash"])
    put(store, deps, "dependencies_hash")
    c = context.model_dump()
    c["metric_dependencies_hash"] = deps["dependencies_hash"]
    put(store, c, "context_hash")
    with pytest.raises(ValueError, match="ReviewNotAccepted"):
        evaluate(ReportContext.model_validate(c), scopes, store, "/count")


def test_synthetic_model_card_never_promotes_real_card_or_verifies_energy():
    import json

    from uarch_contract.model_card import ModelId

    from rkuarch.provenance.model_card import build_model_card

    context, scopes, store, _ = metric_fixture()
    result = evaluate(context, scopes, store, "/count")
    card = json.loads(
        (ROOT / "docs/reviews/U2-U0003-proposal/fixtures/model-card.json").read_text()
    )
    actual = build_model_card(ModelId.model_validate(card["model_id"]), result.models)
    assert actual.badge == "stub"
    assert actual.validated_error_band is None
    assert actual.energy_verification is None


def test_R206_stub_hardware_wins_even_with_two_eligible_duration_models():
    from rkuarch.provenance.applicability import EvidenceAssessment

    context, scopes, store, deps = metric_fixture()
    c = context.model_dump(mode="json")
    for identity in tuple(c["evidence_index"].values()):
        e = deepcopy(store[identity])
        v = deepcopy(store[e["verification_hashes"][0]])
        v["purpose"] = "duration"
        review(store, v, "verification_hash")
        c["verification_hashes"].append(v["verification_hash"])
        e.update(
            evidence_id=e["evidence_id"] + "-duration",
            purpose="duration",
            channel="duration_s",
            verification_hashes=[v["verification_hash"]],
        )
        review(store, e, "evidence_hash")
        c["evidence_index"][e["evidence_id"]] = e["evidence_hash"]
    put(store, c, "context_hash")
    result = evaluate(ReportContext.model_validate(c), scopes, store, "/timing")
    assert all(m.badge == "estimated" for m in result.models)
    assert any(v.provenance == "stub" for v in result.claims)
    assert result.badge == "stub" and result.error_band is None
    assert all(
        isinstance(m, EvidenceAssessment) and m.dimensions and m.scopes for m in result.models
    )


def test_adjustment_assumption_has_no_borrowed_primary_model_identity():
    from uarch_contract.comparison import ProducedValue, ReferenceValue

    from contract.tests.u2_comparison import build_channel

    context, scopes, store, deps = metric_fixture()
    comparison = deepcopy(
        next(v for v in proposal_artifacts().values() if v.get("format") == "uarch-comparison/1")
    )
    c = comparison["fixtures"][0]["channels"][0]
    adjusted = build_channel(
        c["channel"],
        ReferenceValue.model_validate(c["reference"]),
        ProducedValue.model_validate(c["actual"]),
        track=comparison["track"],
        phase="prefill",
        deviations=[
            dict(
                id="B-independent-adjustment",
                deviation_rel=0.01,
                reason="synthetic unvalidated assumption",
            )
        ],
    )
    comparison["fixtures"][0]["channels"][0] = adjusted.model_dump(mode="json")
    put(store, comparison, "comparison_hash")
    selector = dict(
        kind="model_assumption",
        artifact_hash=comparison["comparison_hash"],
        json_pointer="/fixtures/0/channels/0/declared_deviations",
    )
    deps["recipes"][0]["selectors"].append(selector)
    context = rebind(context, store, deps)
    result = evaluate(context, scopes, store, "/count")
    assert result.badge == "stub"
    assert len(result.models) == 2  # actual and reference only, not a forged adjustment model
    assert len(result.unvalidated_assumptions) == 1
    assert all(m.badge == "estimated" for m in result.models)


def test_R210_hash_shaped_assumption_text_is_not_an_artifact_dependency():
    context, scopes, store, deps = metric_fixture()
    old = deps["source_recipes"][2]["recipe"]["selectors"][1]["artifact_hash"]
    assumptions = deepcopy(store[old])
    absent = "sha256:" + "9" * 64
    assert absent not in store
    assumptions["algorithms"]["hash_shaped_literal"] = absent
    put(store, assumptions, "assumptions_hash")
    for source in deps["source_recipes"]:
        for selector in source["recipe"]["selectors"]:
            if selector["artifact_hash"] == old:
                selector["artifact_hash"] = assumptions["assumptions_hash"]
    context = rebind(context, store, deps)
    assert evaluate(context, scopes, store, "/count").badge == "estimated"
