"""Execute the proposed minimal A4 registration in memory; never edit A-owned cli.py."""

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]


def adapted_app():
    proposal = json.loads(
        (
            ROOT / "docs/reviews/U2-inputs/B-report-3b1d03b6cba2"
            / "docs/reviews/U2-B-report-checkpoint/cli-adapter.json"
        ).read_text()
    )
    source = (ROOT / "src/rkuarch/cli.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() in (
        proposal["before_sha256"], proposal["proposed_after_sha256"]
    )
    patched = source.decode()
    if hashlib.sha256(source).hexdigest() == proposal["before_sha256"]:
        for edit in proposal["edits"]:
            assert patched.count(edit["needle"]) == 1
            patched = patched.replace(edit["needle"], edit["replacement"])
    assert hashlib.sha256(patched.encode()).hexdigest() == proposal["proposed_after_sha256"]
    namespace = {"__name__": "u2_report_adapter_test"}
    exec(compile(patched, str(ROOT / "src/rkuarch/cli.py"), "exec"), namespace)
    return namespace["app"]


def test_proposed_A4_report_invocation(tmp_path):
    html = tmp_path / "report.html"
    md = tmp_path / "report.md"
    result = CliRunner().invoke(
        adapted_app(),
        [
            "report",
            str(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json"),
            "--output",
            str(html),
            "--markdown",
            str(md),
            "--show-unvalidated-predictions",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "STUB — unvalidated model prediction" in html.read_text()
    assert "1.892e-06" in md.read_text()
    repeat = CliRunner().invoke(
        adapted_app(), ["report", "missing.json", "--output", str(html), "--markdown", str(md)]
    )
    assert repeat.exit_code == 2 and "OutputConflict" in repeat.output


def test_proposed_report_help_and_original_validate_registration():
    app = adapted_app()
    assert CliRunner().invoke(app, ["report", "--help"]).exit_code == 0
    assert CliRunner().invoke(app, ["validate", "--help"]).exit_code == 0
