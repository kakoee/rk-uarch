"""Public production registration, independent of historical A4 proposal source hashes.

Saved A3 bytes stay historical. The current control uses an actual local analytic
capture with explicitly synthetic administrative reviews, not accuracy evidence.
"""

import copy
from functools import wraps
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rkuarch.cli import app
from rkuarch.table.build import build_table, captured_artifacts, write_table
from tests.integration.test_u2_a_replay import captured, companions

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_TABLE = ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json"


@pytest.fixture(params=["saved_A3", "current_capture"])
def report_table(request, tmp_path):
    if request.param == "saved_A3":
        return HISTORICAL_TABLE
    c = captured()
    context, card, artifacts = companions(c)
    artifacts.update(captured_artifacts(c))
    artifacts[c.request.hardware_spec_hash] = c.bundle.hardware_spec.model_dump(mode="json")
    package = build_table(c, context=context, model_card=card, artifacts=artifacts)
    # Independent tiny workload expectation, not a number scraped from rendered output.
    assert package.table.rows[0].duration_s == 0.000001892
    assert card.badge == "stub" and not card.evidence
    assert card.validated_error_band is None and card.energy_verification is None
    path = tmp_path / "current/table.json"
    write_table(package, path)
    return path


def assert_report_invocation(cli_app, table, tmp_path):
    html = tmp_path / "report.html"
    md = tmp_path / "report.md"
    result = CliRunner().invoke(
        cli_app,
        [
            "report",
            str(table),
            "--output",
            str(html),
            "--markdown",
            str(md),
            "--show-unvalidated-predictions",
        ],
    )
    assert result.exit_code == 0, result.output
    assert html.is_file() and md.is_file(), "report registration did not write both outputs"
    assert "STUB — unvalidated model prediction" in html.read_text()
    assert "1.892e-06" in md.read_text()
    before = html.read_bytes(), md.read_bytes()
    repeat = CliRunner().invoke(
        cli_app, ["report", "missing.json", "--output", str(html), "--markdown", str(md)]
    )
    assert repeat.exit_code == 2 and "OutputConflict" in repeat.output
    assert (html.read_bytes(), md.read_bytes()) == before


def assert_registration_help(cli_app):
    for command in ("report", "validate"):
        result = CliRunner().invoke(cli_app, [command, "--help"])
        assert result.exit_code == 0, result.output


def test_registered_report_invocation(report_table, tmp_path):
    assert_report_invocation(app, report_table, tmp_path)


def test_registered_report_help_and_original_validate_registration():
    assert_registration_help(app)


@pytest.mark.parametrize("mutation", ["missing_report", "no_output_handler"])
def test_invocation_assertions_detect_broken_registration(mutation, tmp_path):
    mutant = copy.deepcopy(app)
    registration = next(c for c in mutant.registered_commands if c.name == "report")
    if mutation == "missing_report":
        mutant.registered_commands.remove(registration)
        expected = "No such command"
    else:

        @wraps(registration.callback)
        def broken_report(*args, **kwargs):
            pass

        registration.callback = broken_report
        expected = "did not write both outputs"
    # Exercise the SAME assertions as the positive control, on isolated registrations.
    with pytest.raises(AssertionError, match=expected):
        assert_report_invocation(mutant, HISTORICAL_TABLE, tmp_path)
    assert not (tmp_path / "report.html").exists()
    assert not (tmp_path / "report.md").exists()


@pytest.mark.parametrize("command", ["report", "validate"])
def test_help_assertions_detect_missing_registration(command):
    mutant = copy.deepcopy(app)
    mutant.registered_commands = [c for c in mutant.registered_commands if c.name != command]
    with pytest.raises(AssertionError, match="No such command"):
        assert_registration_help(mutant)
