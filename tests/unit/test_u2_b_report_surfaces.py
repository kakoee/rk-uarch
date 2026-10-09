"""Independent report surface controls; synthetic comparisons are not file-complete or adopted."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from uarch_contract.comparison import validate_comparison
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import MetricDependencies, ReportContext

from rkuarch.provenance.applicability import EvidenceAssessment
from rkuarch.provenance.badge import badge_for
from rkuarch.report.badged import badged
from rkuarch.report.complete import Document, permissions
from rkuarch.report.evaluation import combine_assessments
from rkuarch.table.artifacts import load_verified_report_inputs
from tests.fixtures.u2_b.b2_support import proposal_artifacts, put, review
from tests.unit.test_u2_b_display_permissions import assessed
from tests.unit.test_u2_b_display_permissions import permissions as display_permissions

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def comparison_inputs():
    v = load_verified_report_inputs(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json")
    store = proposal_artifacts()
    store.update(v.artifacts)
    c = json.loads(
        (ROOT / "docs/reviews/U2-U0003-proposal/fixtures/r2-semantic-context.json").read_text()
    )
    old = store[c["metric_dependencies_hash"]]
    deps = v.dependencies.model_dump(mode="json")
    deps["recipes"] += [r for r in old["recipes"] if r["metric_path"].startswith("/comparisons/")]
    deps["source_recipes"] += old["source_recipes"]
    review(store, deps, "dependencies_hash")
    context = v.context.model_dump(mode="json")
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    context["comparison_hashes"] = c["comparison_hashes"]
    put(store, context, "context_hash")
    comparisons = tuple(
        validate_comparison(store[h], store[store[h]["reference_inventory_hash"]], store)
        for h in c["comparison_hashes"]
    )
    return v._replace(
        context=ReportContext.model_validate(context),
        dependencies=MetricDependencies.model_validate(deps),
        artifacts=store,
        comparisons=comparisons,
    )


def test_comparison_outcomes_sources_and_unknowns(comparison_inputs):
    v = comparison_inputs
    d = Document(v, permissions(v, True, True))
    d.comparisons()
    text = " ".join(m.text for _, entries in d.sections for _, m in entries)
    assert "discrepancy_record_complete" in text
    assert "failed" in text and "unassessed" in text and "refused" in text
    assert "reference null" in text and "reference absent" in text
    assert content_hash(v.comparisons[0].candidate) in text
    assert content_hash(v.comparisons[0].reference_model) in text
    metric = d.metrics["/comparisons/0/fixtures/0/channels/0/raw_rel"]
    assert len({m.model_identity_hash for m in metric.assessment.models}) == 2
    assert all(m.badge == "stub" for m in metric.assessment.models)
    assert "synthetic fixture — not executed" in metric.text
    assert "unvalidated model prediction" not in metric.text
    assert any("/values/matrix_ops/value" in s.json_pointer for s in metric.assessment.contributors)
    assert d.metrics["/comparisons/0/fixtures/0/channels/0/actual/value"].assessment.models
    assert d.metrics["/comparisons/0/fixtures/0/channels/0/reference/value"].assessment.models
    # D04: source recipes authorize contributors, not a new raw-value display surface.
    for side in ("actual", "reference"):
        raw = d.metrics[f"/comparisons/0/fixtures/0/channels/0/{side}/value"]
        assert raw.number is None
        assert "unsupported presentation" in raw.text


def test_compound_assessment_cannot_raise_unvalidated_adjustment():
    m = EvidenceAssessment("estimated", "sha256:" + "0" * 64, "counts", "operator")
    source = replace(badge_for((), (m,), design_status="proposed"), badge="stub")
    joined = combine_assessments((source,), "proposed")
    assert joined.badge == "stub"


def test_synthetic_display_is_not_named_prediction():
    metric = badged(
        64,
        "op",
        replace(assessed(), synthetic=True),
        display_permissions(True, True),
        execution="executed",
    )
    assert "synthetic fixture — not executed" in metric.text
    assert "unvalidated model prediction" not in metric.text


def test_raw_proof_contradiction_propagates(comparison_inputs):
    from uarch_contract.evidence import SourceRecord
    from uarch_contract.hashing import canonical_json, sha256

    from rkuarch.report.proofs import proof_statuses

    raw = canonical_json(
        {
            "format": "u2-proof-bundle/2",
            "kind": "verification",
            "classification": "synthetic_fixture",
            "members": [],
        }
    ).encode()
    source = dict(
        format="uarch-reference-source/1",
        kind="synthetic_fixture",
        reference_identity="invalid-member-control",
        reference_version="1",
        raw_blob_sha256=sha256(raw),
        independence_from_candidate=True,
        limitation="Malformed structural negative only.",
    )
    source["source_hash"] = content_hash(source)
    store = dict(comparison_inputs.artifacts)
    store[sha256(raw)] = raw
    v = comparison_inputs._replace(sources=(SourceRecord.model_validate(source),), artifacts=store)
    with pytest.raises(ValueError, match="MALFORMED"):
        proof_statuses(v, allow_synthetic=True)


def test_precision_names_survive_while_unbound_numeric_prose_is_hidden():
    from rkuarch.report.complete import safe_prose

    text = safe_prose("bf16 fp8, latency137.0625ns and 137.0625 s")
    assert "bf16" in text and "fp8" in text
    assert "137" not in text and "0625" not in text


def test_original_stipulations_are_explicit_input_quotes(comparison_inputs):
    # Isolated provenance surface over unchanged approved H1 inputs, NOT a new table/capture.
    import yaml
    from uarch_contract.hardware import HardwareSpec, sourced_leaves

    v = comparison_inputs
    hardware = HardwareSpec.model_validate(
        yaml.safe_load((ROOT / "hw/designs/npu-l4.yaml").read_text())
    )
    originals = tuple(sourced_leaves(hardware))
    assert originals and all(value.kind == "stipulation" for _, value in originals)
    d = Document(v, permissions(v, True, False))
    d.v = v._replace(
        hardware=hardware,
        table=v.table.model_copy(
            update={
                "hardware_spec_hash": content_hash(hardware),
                "provenance": v.table.provenance.model_copy(
                    update={"conditional_on": ("unit-surface-only",)}
                ),
            }
        ),
    )
    d.provenance()
    text = " ".join(m.text for _, entries in d.sections for _, m in entries)
    assert "conditional: if built as specified" in text
    assert "not a hardware measurement" in text
    assert "unvalidated model prediction" not in text
    inventory = d.metrics["/hardware/stipulation_inventory_count"]
    assert inventory.number == repr(float(len(originals)))
    assert "input inventory; not a prediction" in inventory.text
    for path, original in originals:
        quote = d.metrics["/hardware/" + path]
        assert quote.assessment.conditional_on == (original,)
        assert quote.assessment.claims == ()
        assert quote.number == repr(float(original.value))


def test_plot_prose_cannot_bypass_numeric_guard():
    from rkuarch.report.plot import roofline

    p = display_permissions(True)
    m = badged(64, "op", assessed(), p, execution="executed")
    plot = roofline((("latency137.0625ns bf16", m, m, m, m),), p)
    assert "137" not in plot.svg and "0625" not in plot.markdown
    assert "bf16" in plot.svg
