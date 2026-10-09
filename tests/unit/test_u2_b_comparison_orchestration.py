"""Real nominal execution on adopted references; synthetic attacks never oracle generation."""

from pathlib import Path

import pytest

from contract.tests.historical_snapshot import historical_snapshot
from scripts import u2_inputs
from tests import u2_comparison as comparison

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def historical(monkeypatch):
    """Bind only the requesting test; the production historical identity guard stays active."""
    root = historical_snapshot()
    monkeypatch.setattr(u2_inputs, "ADOPTED", root)
    return root


@pytest.fixture(scope="module")
def inputs(tmp_path_factory):
    directory = tmp_path_factory.mktemp("inputs") / "staged"
    return u2_inputs.load_inputs(directory, u2_inputs.prepare_inputs(directory))


def test_all_retained_references_use_actual_nominal_candidate(historical, inputs):
    result = comparison.run_historical(inputs)
    assert result["reference_manifest_sha256"] == u2_inputs.ADOPTED_MANIFEST
    assert result["current_fingerprint_compatible"] is False
    assert len(result["nominal"].fixtures) == 864
    assert all(f.execution == "executed" for f in result["nominal"].fixtures)
    assert all(
        c.outcome == "passed"
        for f in result["nominal"].fixtures
        for c in f.channels
        if c.reference.state == "positive"
    )
    assert all(
        c.outcome in ("unassessed", "modelled_absence")
        for f in result["nominal"].fixtures
        for c in f.channels
        if c.reference.state in ("null", "absent")
    )
    assert result["nominal"].evidence_outcome == "unassessed"
    assert (
        result["nominal"].gate_outcome == "compatibility_fail"
    )  # direct observations have NOT run
    assert len(result["physical"].fixtures) == 864
    assert all(f.execution == "not_run" for f in result["physical"].fixtures)
    assert all(f.result_hash is None for f in result["physical"].fixtures)


def test_candidate_cannot_read_expected_files(historical, inputs, monkeypatch):
    def illicit(value):
        (u2_inputs.ADOPTED / "parity/fixtures.json").read_bytes()
        raise AssertionError("unreachable")

    monkeypatch.setattr(comparison.nominal, "evaluate_nominal", illicit)
    result = comparison.run_historical(inputs, fixture_ids=(comparison.adopted_rows()[0]["id"],))
    assert result["nominal"].fixtures[0].execution == "execution_failed"
    assert "candidate file access" in result["errors"][0]["reason"]


def test_no_timing_adjustments_and_count_budget():
    with pytest.raises(ValueError):
        comparison.channel(
            "duration_s",
            1.1,
            1.0,
            "sha256:" + "1" * 64,
            "/duration_s",
            deviations=[dict(id="invalid", reason="not a count", deviation_rel=0.01)],
        )
    with pytest.raises(ValueError):
        comparison.channel(
            "matrix_ops",
            110,
            100,
            "sha256:" + "1" * 64,
            "/counts/matrix_ops",
            deviations=[
                dict(id="a", reason="term", deviation_rel=0.05),
                dict(id="b", reason="opposed", deviation_rel=-0.05),
            ],
        )


def test_af12_refuses_before_candidate(historical, inputs, monkeypatch):
    row = comparison.adopted_rows()[0]
    row["tp"] = 16  # stored kv_heads=8 -> genuine replicated KV guard
    monkeypatch.setattr(
        comparison.nominal, "evaluate_nominal", lambda v: pytest.fail("candidate called")
    )
    assert comparison.nominal_attempt(row, inputs, {})[0] == "pre_call_refusal"


def test_actual_H1_capture_is_physical_and_not_nominal(inputs):
    c = comparison.capture_h1(inputs, model_id="llama-3.1-8b", tp=1, compact=True)
    assert len(c.results) == 2
    assert c.bundle.hardware_spec.id == "npu-l4"
    assert c.bundle.intent.precision.compute.value == "bf16"
    assert c.results[0].counts.vector_ops > 0
    assert c.results[0].counts.memory_write_bytes > 0
    assert c.jobs[0].engine.model.name == "physical-resolved"
    assert all(r.engine.model != comparison.nominal.candidate_identity() for r in c.results)


def test_file_loadable_both_tracks_with_authentic_manifest(
    historical, inputs, tmp_path, monkeypatch
):
    from rkuarch.table.artifacts import load_verified_report_inputs
    from rkuarch.table.build import write_table

    c = comparison.capture_h1(inputs, model_id="llama-3.1-8b", tp=1, compact=True)
    selected = comparison.run_historical(inputs, fixture_ids=(comparison.adopted_rows()[0]["id"],))
    package = comparison.report_package(c, selected, inputs)
    path = tmp_path / "table.json"
    write_table(package, path)
    v = load_verified_report_inputs(path)
    assert {x.track for x in v.comparisons} == {"nominal_compatibility", "physical_discrepancy"}
    assert (
        v.artifacts["sha256:" + u2_inputs.ADOPTED_MANIFEST]
        == (u2_inputs.ADOPTED / "MANIFEST.json").read_bytes()
    )
    assert v.comparisons[0].fixtures[0].execution == "executed"
    assert v.comparisons[1].fixtures[0].execution == "not_run"
    assert len(v.table.provenance.conditional_on) == 59
    assert v.model_card.badge == "stub"


def test_real_physical_af12_refuses_before_engine(inputs, monkeypatch):
    from rkuarch.workload import prepared

    bundle, assumptions = comparison.prepare_h1(
        inputs, model_id="llama-3.1-8b", tp=16, compact=True
    )
    monkeypatch.setattr(
        prepared, "execute_prepared_point", lambda *a, **k: pytest.fail("engine called")
    )
    with pytest.raises(ValueError, match="ProjectionScope"):
        comparison.physical_point(bundle, assumptions, bundle.points[0])


def test_selected_rank_embedding_is_explicit_and_conserved(inputs):
    bundle, _ = comparison.prepare_h1(inputs, model_id="llama-3.1-8b", tp=8, compact=True)
    assert bundle.rank.rank_index == 0
    assert bundle.rank.kind == "balanced_tp_selected_rank"
    point = bundle.points[0]
    assert point.query.batch == 1
    embedding = next(
        op
        for group in point.graph.groups
        for op in group.ops
        if str(op.spec.operator) == "embedding"
    )
    assert embedding.embedding_local_tokens == 1
    # The captured mapping retains the explicit producer assumption and operator scope;
    # no one borrows nominal/reference bins to claim mapping correspondence.
    assert bundle.producer.name


@pytest.mark.parametrize(
    "field", ["component_params_sha256", "model", "model_shape", "model_sources", "precision"]
)
def test_candidate_input_join_refuses_substitution(historical, inputs, monkeypatch, field):
    row = comparison.adopted_rows()[0]
    if field == "component_params_sha256":
        row[field] = "0" * 64
    elif field == "model":
        row[field]["active_params"] += 1
    elif field == "model_shape":
        row[field]["d_ff"] += 1
    elif field == "model_sources":
        row[field] = []
    else:
        row[field] = dict(compute="bf16", kv_cache="bf16")
    monkeypatch.setattr(
        comparison.nominal, "evaluate_nominal", lambda v: pytest.fail("candidate called")
    )
    with pytest.raises(ValueError, match="join differs"):
        comparison.nominal_attempt(row, inputs, {})


def test_physical_adapter_uses_saved_bundle_with_prepare_disabled(inputs, monkeypatch):
    from rkuarch.workload import prepare as producer

    bundle, assumptions = comparison.prepare_h1(inputs, model_id="llama-3.1-8b", tp=1, compact=True)

    def denied(*args, **kwargs):
        pytest.fail("physical adapter re-prepared captured input")

    monkeypatch.setattr(producer, "prepare", denied)
    monkeypatch.setattr(comparison, "prepare_h1", denied)
    job, result = comparison.physical_point(bundle, assumptions, bundle.points[0])
    assert job.bundle_hash == bundle.bundle_hash
    assert result.counts.vector_ops > 0
