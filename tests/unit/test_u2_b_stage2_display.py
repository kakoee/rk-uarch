"""Declared metadata is distinct from computed predictions and arbitrary prose."""

from pathlib import Path

import pytest
from uarch_contract.hardware import HardwareSpec, sourced_leaves

from rkuarch.report.complete import Document, _render, permissions
from rkuarch.table.artifacts import load_verified_report_inputs
from tests.unit.test_u2_b_report_surfaces import comparison_inputs  # noqa: F401


@pytest.fixture(scope="module")
def saved():
    return load_verified_report_inputs(
        Path(__file__).parents[1] / "fixtures/u2_b/a3-proof-capture/table.json"
    )


@pytest.mark.parametrize("count", [0, 1, 3])
@pytest.mark.parametrize("show", [False, True])
def test_declared_stipulation_count_is_integer_in_both_modes(saved, count, show):
    # Isolated provenance surface; actual captured computations are unchanged.
    data = saved.hardware.model_dump(mode="json")
    data["design_status"] = "proposed"
    chosen = list(sourced_leaves(saved.hardware))[:count]
    for path, _ in chosen:
        current = data
        parts = path.split(".")
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]].update(
            kind="stipulation",
            provenance=None,
            source=None,
            date=None,
            rationale="Explicit synthetic surface condition, not measurement.",
        )
    hw = HardwareSpec.model_validate(data)
    v = saved._replace(
        hardware=hw,
        table=saved.table.model_copy(
            update={
                "provenance": saved.table.provenance.model_copy(
                    update={"conditional_on": tuple(chosen)}
                )
            }
        ),
    )
    out = _render(v, permissions(v, show, False))
    for text in (out.html, out.markdown):
        assert f"conditional · {count} stipulations" in text
        assert f"{count}.0 stipulations" not in text
        assert "Energy is unverified" in text
    count_metric = out.metrics["/hardware/stipulation_inventory_count"]
    assert count_metric.number == str(count)
    for path, _ in chosen:
        assert (out.metrics["/hardware/" + path].number is not None) == show
    assert (out.metrics["/rows/0/duration_s"].number is not None) == show


@pytest.mark.parametrize(
    "name", ["llama-3.1-8b", "llama-3.1-70b", "llama-3.1-8b<script>alert(137)</script>"]
)
def test_categorical_model_identity_is_preserved_and_escaped(saved, name):
    request = saved.request.model_copy(
        update={"model": saved.request.model.model_copy(update={"name": name})}
    )
    v = saved._replace(request=request)
    out = _render(v, permissions(v, False, False))
    assert name.replace("<", "&lt;").replace(">", "&gt;") in out.html
    assert "<script>" not in out.html and "<script>" not in out.markdown
    assert "analytic-ops@1" in out.html
    assert all(op.id in out.html for op in saved.table.rows[0].op_results)
    d = Document(v, permissions(v, False, False))
    assert "137" not in d.text("latency137.0625ns; throughput999").text
    assert "999" not in d.text("latency137.0625ns; throughput999").text


def test_fixture_coordinates_are_source_bound_declared_inputs(comparison_inputs):  # noqa: F811
    v = comparison_inputs
    d = Document(v, permissions(v, False, False))
    d.comparisons()
    labels = {label for _, entries in d.sections for label, _ in entries}
    for ci, comparison in enumerate(v.comparisons):
        for fi, fixture in enumerate(comparison.fixtures):
            assert fixture.fixture_id in labels
            path = f"/comparisons/{ci}/fixtures/{fi}/tp"
            metric = d.number(path, fixture.tp, "ranks")
            assert metric.number == str(fixture.tp)
            assert "declared captured input" in metric.text
            assert comparison.reference_inventory_hash in {
                s.artifact_hash for s in metric.assessment.contributors
            }
            with pytest.raises(ValueError, match="CapturedInputBindingMismatch"):
                d.number(path, fixture.tp + 1, "ranks")
    assert all(m.number is None for p, m in d.metrics.items() if p.endswith("/raw_rel"))
