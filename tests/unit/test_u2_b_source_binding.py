"""B2-C1 source-binding regressions; synthetic premises, no runtime/silicon claims."""

from dataclasses import replace

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import ReportContext

from rkuarch.provenance import badge
from tests.fixtures.u2_b.b2_support import metric_fixture


def assess(context, scopes, store, path="/count"):
    return badge.assess_metric(
        context,
        path,
        scopes=scopes,
        channel="matrix_ops",
        artifacts=store,
        design_status="proposed",
        allow_synthetic=True,
    )


def retain_evidence(context, model, store):
    data = context.model_dump(mode="json")
    data["evidence_index"] = {
        name: identity
        for name, identity in data["evidence_index"].items()
        if all(s["model_identity_hash"] == model for s in store[identity]["scope"])
    }
    data["context_hash"] = content_hash(data, exclude=("context_hash",))
    return ReportContext.model_validate(data)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("mixed", ["replacement", "declared-first", "foreign-first"])
def test_B2_C1_wrong_or_mixed_source_scopes_refuse(reverse, mixed):
    context, scopes, store, deps = metric_fixture()
    actual = deps["model_identity_hash"]
    reference = next(key[0] for key in scopes if key[0] != actual)
    target, donor = (reference, actual) if reverse else (actual, reference)
    context = retain_evidence(context, donor, store)
    control = assess(context, scopes, store)
    assert control.badge == "stub"
    assert {m.model_identity_hash for m in control.models} == {actual, reference}
    key = (target, "counts", "whole_iteration")
    foreign = scopes[(donor, "counts", "whole_iteration")]
    altered = dict(scopes)
    altered[key] = {
        "replacement": foreign,
        "declared-first": scopes[key] + foreign,
        "foreign-first": foreign + scopes[key],
    }[mixed]
    with pytest.raises(ValueError, match="SourceScopeMismatch"):
        assess(context, altered, store)


@pytest.mark.parametrize("reference_missing", [False, True])
@pytest.mark.parametrize("empty", [False, True])
def test_B2_C1_missing_scope_preserves_declared_identity(reference_missing, empty):
    context, scopes, store, deps = metric_fixture()
    actual = deps["model_identity_hash"]
    reference = next(key[0] for key in scopes if key[0] != actual)
    missing = reference if reference_missing else actual
    key = (missing, "counts", "whole_iteration")
    if empty:
        scopes[key] = ()
    else:
        del scopes[key]
    result = assess(context, scopes, store)
    assert result.badge == "stub"
    assert len(result.models) == 2
    assert {m.model_identity_hash for m in result.models} == {actual, reference}
    model = next(m for m in result.models if m.model_identity_hash == missing)
    assert (model.badge, model.purpose, model.granularity) == ("stub", "counts", "whole_iteration")
    assert model.reasons == ("source scope unavailable",)


def test_B2_C1_valid_independent_models_no_band_and_purpose_control():
    context, scopes, store, deps = metric_fixture()
    result = assess(context, scopes, store)
    assert result.badge == "estimated" and result.synthetic
    assert result.error_band is None
    assert len(result.models) == 2
    assert {m.model_identity_hash for m in result.models} == {key[0] for key in scopes}
    for model in result.models:
        assert (model.badge, model.purpose, model.granularity) == (
            "estimated", "counts", "whole_iteration"
        )
        assert model.error_band is None
        assert all(scope.model_identity_hash == model.model_identity_hash for scope in model.scopes)
    for model in result.models:
        independent = assess(
            retain_evidence(context, model.model_identity_hash, store), scopes, store
        )
        assert independent.badge == "stub"
        assert {m.model_identity_hash: m.badge for m in independent.models} == {
            m.model_identity_hash: "estimated" if m == model else "stub" for m in result.models
        }
    timing = assess(context, scopes, store, "/timing")
    assert timing.badge == "stub"
    assert all(m.purpose == "duration" and m.badge == "stub" for m in timing.models)


@pytest.mark.parametrize(
    "change",
    [
        {"model_identity_hash": "sha256:" + "f" * 64},
        {"purpose": "duration"},
        {"granularity": "operator"},
    ],
)
def test_B2_C1_returned_assessment_must_preserve_source_binding(monkeypatch, change):
    context, scopes, store, _ = metric_fixture()
    evaluator = badge.assess_evidence

    def wrong_assessment(*args, **kwargs):
        return replace(evaluator(*args, **kwargs), **change)

    monkeypatch.setattr(badge, "assess_evidence", wrong_assessment)
    with pytest.raises(ValueError, match="EvidenceAssessmentBindingMismatch"):
        assess(context, scopes, store)
