"""Test every presentation projection from a complete B assessment, not raw floats."""

from dataclasses import replace

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.report_context import RenderSpec
from uarch_contract.sourced import SourcedValue

from rkuarch.provenance.badge import badge_for
from rkuarch.report.badged import badged
from rkuarch.report.render import render_metrics
from tests.fixtures.u2_b.b2_support import ZERO


def permissions(show=False, synthetic=False):
    data = dict(
        format="uarch-render/1",
        renderer_version="B2-unit",
        table_hash=ZERO,
        report_context_hash=ZERO,
        show_unvalidated_predictions=show,
        allow_synthetic_presentation=synthetic,
        locale="en",
        number_format="roundtrip-display/1",
    )
    return RenderSpec.model_validate(dict(data, render_hash=content_hash(data)))


def assessed():
    value = SourcedValue(value=1, unit="ratio", kind="claim", provenance="stub")
    return badge_for((value,), (), design_status="proposed")


def test_D01_D02_hidden_magnitude_cannot_change_any_output_surface():
    outputs = []
    for value in [137.0625, 1e80, 0.0]:
        metric = badged(value, "s", assessed(), permissions(), execution="executed")
        assert metric.number is None
        outputs.append(render_metrics({"duration": metric}, permissions()))
    assert outputs[0] == outputs[1] == outputs[2]
    metric = badged(137.0625, "s", assessed(), permissions(True), execution="executed")
    html, md = render_metrics({"duration": metric}, permissions(True))
    assert "137.0625" in html and "137.0625" in md
    assert "STUB" in html and "unvalidated model prediction" in html


@pytest.mark.parametrize("execution", ["not_run", "refused", "execution_failed"])
def test_D03_D05_unknown_and_unexecuted_never_become_zero(execution):
    m = badged(None, "s", assessed(), permissions(True), execution=execution)
    assert m.number is None
    assert "unknown" in m.text or "not modelled" in m.text


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_D03_nonfinite_never_renders(value):
    with pytest.raises(ValueError):
        badged(value, "s", assessed(), permissions(True), execution="executed")


def test_D03_total_empty_and_D04_unlisted_raw_values_stay_hidden():
    empty = badge_for((), (), design_status="proposed")
    assert badged(137.0625, "s", empty, permissions(True), execution="executed").number is None
    missing = replace(assessed(), display_recipe=False)
    assert badged(137.0625, "s", missing, permissions(True), execution="executed").number is None


def test_D06_synthetic_requires_separate_flag_and_label():
    assessment = replace(assessed(), synthetic=True)
    assert badged(137.0625, "s", assessment, permissions(True), execution="executed").number is None
    shown = badged(137.0625, "s", assessment, permissions(True, True), execution="executed")
    assert shown.number == "137.0625"
    assert "synthetic fixture — not executed" in shown.text


def test_D08_deterministic_order_and_renderer_permission_binding():
    p = permissions(True)
    a = badged(1.25, "s", assessed(), p, execution="executed")
    b = badged(0.0, "s", assessed(), p, execution="executed")
    assert render_metrics({"a": a, "b": b}, p) == render_metrics({"b": b, "a": a}, p)
    with pytest.raises(ValueError, match="Render"):
        render_metrics({"a": a}, permissions())


def test_D03_incomplete_contributor_result_blocks_opt_in():
    incomplete = replace(assessed(), complete=False)
    assert badged(137.0625, "s", incomplete, permissions(True), execution="executed").number is None


def test_D08_fresh_processes_and_locations_keep_fragment_bytes(tmp_path):
    import os
    import subprocess
    import sys

    from tests.fixtures.u2_b.b2_support import ROOT

    program = """
import json
from tests.unit.test_u2_b_display_permissions import assessed, permissions
from rkuarch.report.badged import badged
from rkuarch.report.render import render_metrics
p=permissions(True)
print(json.dumps(render_metrics({'duration':badged(137.0625,'s',assessed(),p,execution='executed')},p)))
"""
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(map(str, [ROOT, ROOT / "contract", ROOT / "src"])),
        PYTHONDONTWRITEBYTECODE="1",
    )
    outputs = []
    for name in ["first", "second"]:
        path = tmp_path / name
        path.mkdir()
        outputs.append(
            subprocess.check_output([sys.executable, "-B", "-c", program], cwd=path, env=env)
        )
    assert outputs[0] == outputs[1]
