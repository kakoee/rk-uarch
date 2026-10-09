"""Full report tests over actual saved A3 captures; synthetic reviews confer no accuracy."""

import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import RenderSpec

from rkuarch.report.badged import badged
from rkuarch.report.complete import render_verified, write_report
from rkuarch.report.plot import roofline
from rkuarch.report.render import lint_template
from rkuarch.table.artifacts import load_verified_report_inputs
from tests.unit.test_u2_b_display_permissions import assessed, permissions

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json"


@pytest.fixture(scope="module")
def inputs():
    return load_verified_report_inputs(TABLE)


@pytest.fixture(scope="module")
def reports(inputs):
    return render_verified(inputs), render_verified(inputs, show_unvalidated_predictions=True)


def test_complete_default_and_opt_in_literals(reports):
    default, shown = reports
    for text in (default.html, default.markdown):
        for literal in (
            "C0",
            "steady",
            "KV layout",
            "interpolation_loo",
            "composition_reduction",
            "layer_reuse",
            "cold_vs_steady",
            "not modelled",
            "unknown",
            "energy unverified",
            "Nominal compatibility",
            "Physical discrepancies",
            "not_attempted",
            "What this table does not claim",
        ):
            assert literal in text.replace("\\_", "_")
        assert "1.892e-06" not in text and "666666666.6666666" not in text
        assert "±0" not in text
    assert "<circle " not in default.html
    for text in (shown.html, shown.markdown):
        assert "1.892e-06" in text
        assert "64.0" in text
        assert "STUB — unvalidated model prediction" in text
        assert "durations do not add to aggregate latency" in text
        assert "not a hardware measurement" in text
    assert "<circle " in shown.html
    assert default.render_spec.render_hash != shown.render_spec.render_hash
    assert default.render_spec.table_hash == shown.render_spec.table_hash


def test_source_specific_scopes_and_ratio_contributors(inputs, reports):
    _, shown = reports
    q = shown.metrics["/rows/0/op_results/2/operational_intensity_ops_per_byte"]
    assert q.number == "0.6666666666666666"
    assert {m.model_identity_hash for m in q.assessment.models} == {
        content_hash(inputs.jobs[0].engine.model)
    }
    assert all(s.op_class == "q_projection" for m in q.assessment.models for s in m.scopes)
    pointers = {s.json_pointer for s in q.assessment.contributors}
    assert "/per_op/2/counts/matrix_ops" in pointers
    assert "/per_op/2/counts/memory_read_bytes" in pointers
    assert "/per_op/2/counts/memory_write_bytes" in pointers
    whole = shown.metrics["/rows/0/duration_s"]
    assert len(whole.assessment.models[0].scopes) == 17


def test_plot_hidden_values_cannot_change_geometry_or_accessibility():
    p = permissions()
    values = []
    for sentinel in (137.0625, 1e80, 0.0):
        x = badged(sentinel, "op/byte", assessed(), p, execution="executed")
        y = badged(sentinel, "op/s", assessed(), p, execution="executed")
        values.append(roofline((("hidden", x, y, x, y),), p))
    assert values[0] == values[1] == values[2]
    assert "137.0625" not in values[0].svg and "<circle " not in values[0].svg
    p = permissions(True)
    x = badged(None, "op/byte", assessed(), p, execution="executed")
    y = badged(12, "op/s", assessed(), p, execution="executed")
    assert "<circle " not in roofline((("null", x, y, x, y),), p).svg


def test_full_templates_refuse_raw_numeric_values():
    for template in (
        "{{ row.duration_s }}",
        "{{ row.counts.matrix_ops }}",
        "{{ plot.raw }}",
        "{{ metric.number }}",
    ):
        with pytest.raises(ValueError, match="UnbadgedTemplateValue"):
            lint_template(template)


def test_bound_render_identity(inputs):
    v = render_verified(inputs)
    data = v.render_spec.model_dump(mode="json", exclude={"render_hash"})
    data["table_hash"] = "sha256:" + "0" * 64
    wrong = RenderSpec(**data, render_hash=content_hash(data))
    with pytest.raises(ValueError, match="Render.*Binding"):
        render_verified(inputs, render_spec=wrong)


def test_typed_input_tampering_refuses(inputs):
    wrong = inputs._replace(results=tuple(reversed(inputs.results)))
    with pytest.raises(ValueError, match="VerifiedInputMismatch"):
        render_verified(wrong)


def test_wrong_source_scope_refuses(inputs, monkeypatch):
    import rkuarch.report.evaluation as ev

    original = ev.source_scopes

    def wrong(*args, **kwargs):
        return {
            k: tuple(x.model_copy(update={"model_identity_hash": "sha256:" + "0" * 64}) for x in s)
            for k, s in original(*args, **kwargs).items()
        }

    monkeypatch.setattr(ev, "source_scopes", wrong)
    with pytest.raises(ValueError, match="SourceScopeMismatch"):
        render_verified(inputs)


def test_file_conflicts_are_preflighted_before_writing(tmp_path):
    html = tmp_path / "report.html"
    md = tmp_path / "report.md"
    md.write_text("keep")
    with pytest.raises(ValueError, match="OutputConflict"):
        write_report(TABLE, html_path=html, markdown_path=md)
    assert not html.exists() and md.read_text() == "keep"
    with pytest.raises(ValueError, match="OutputConflict"):
        write_report(TABLE, html_path=html, markdown_path=html)
    html.symlink_to(TABLE)
    with pytest.raises(ValueError, match="OutputConflict"):
        write_report(TABLE, html_path=html, markdown_path=tmp_path / "new.md")


@pytest.mark.parametrize("mutation", ["missing", "tampered"])
def test_real_offline_loader_refuses_bad_closure(tmp_path, mutation):
    moved = tmp_path / "inputs"
    shutil.copytree(TABLE.parent, moved)
    companion = next((moved / "artifacts").glob("*.json"))
    if mutation == "missing":
        companion.unlink()
    else:
        companion.write_text("{}")
    with pytest.raises(ValueError):
        write_report(
            moved / "table.json", html_path=tmp_path / "x.html", markdown_path=tmp_path / "x.md"
        )
    assert not (tmp_path / "x.html").exists()


def test_fresh_moved_producer_disabled_replay(tmp_path, reports):
    program = """
import sys
from pathlib import Path
import rkuarch.workload.prepared as prepared
import rkuarch.table.build as build
import rkuarch.engines.analytic.core as core
import rkuarch.workload.prepare as producer
import contract.tests.nominal_candidate as nominal
import contract.tests.u2_prepared_adapter as adapter

def denied(*a,**k): raise AssertionError("producer/candidate invoked during report replay")
prepared.execute_prepared_point=denied
producer.prepare=denied
nominal.evaluate_nominal=denied
adapter.evaluate_captured=denied
build.capture=denied
core.run_analytic=denied
from rkuarch.report.complete import write_report
write_report(Path(sys.argv[1]),html_path=Path(sys.argv[2]),markdown_path=Path(sys.argv[3]),show_unvalidated_predictions=True)
"""
    results = []
    for name in ("one", "two"):
        root = tmp_path / name
        shutil.copytree(TABLE.parent, root / "input")
        env = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join(map(str, [ROOT, ROOT / "contract", ROOT / "src"])),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONHASHSEED="1" if name == "one" else "4",
        )
        subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                program,
                str(root / "input/table.json"),
                str(root / "a.html"),
                str(root / "b.md"),
            ],
            cwd=root,
            env=env,
            check=True,
        )
        results.append(((root / "a.html").read_text(), (root / "b.md").read_text()))
    assert results[0] == results[1] == (reports[1].html, reports[1].markdown)


def test_numeric_prose_and_synthetic_controls():
    from rkuarch.report.complete import safe_prose

    assert "137.0625" not in safe_prose("Latency 137.0625 seconds; <script>unsafe</script>")
    p = permissions(True)
    synthetic = replace(assessed(), synthetic=True)
    x = badged(137.0625, "op/byte", synthetic, p, execution="executed")
    assert "<circle " not in roofline((("synthetic", x, x, x, x),), p).svg
    p = permissions(True, True)
    x = badged(137.0625, "op/byte", synthetic, p, execution="executed")
    plot = roofline((("synthetic", x, x, x, x),), p)
    assert "synthetic fixture — not executed" in plot.svg
    assert "executed measurement" not in plot.svg
