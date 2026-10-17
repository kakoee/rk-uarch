"""Exercise telemetry with real child pytest runs, including incomplete/failing runs."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def invoke(tmp_path, stages):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(stages))
    out = tmp_path / "receipt"
    run = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".github/verification_run.py"),
            "--plan",
            str(plan),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return run, out


def test_stage_progress_retains_failures_and_runs_restoration(tmp_path):
    run, out = invoke(
        tmp_path,
        [
            {"name": "control", "argv": [sys.executable, "-c", "print('control')"]},
            {"name": "fault", "argv": [sys.executable, "-c", "raise ValueError('distinct fault')"]},
            {"name": "not-run", "argv": [sys.executable, "-c", "raise AssertionError"]},
            {
                "name": "restore",
                "always": True,
                "argv": [sys.executable, "-c", "print('restored')"],
            },
        ],
    )
    assert run.returncode == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["complete"] and not summary["passed"]
    assert [s["outcome"] for s in summary["stages"]] == ["passed", "failed", "not_run", "passed"]
    assert "distinct fault" in (out / "002-fault.stderr.log").read_text()
    events = [json.loads(line) for line in (out / "progress.jsonl").read_text().splitlines()]
    assert events[0]["event"] == "start" and events[-1]["event"] == "finish"
    assert "restore" in run.stdout and "completed" in run.stdout
    elapsed = [event["elapsed_s"] for event in events]
    assert elapsed == sorted(elapsed)
    assert all("stage_elapsed_s" in e for e in events if e["event"] == "stage_finish")


def test_expected_failure_requires_identity_and_exact_exit(tmp_path):
    run, out = invoke(
        tmp_path,
        [
            {
                "name": "mutant",
                "argv": [sys.executable, "-c", "print('wrong fault'); exit(1)"],
                "expected_exit": 1,
                "contains": ["expected fault"],
            },
        ],
    )
    assert run.returncode == 1
    assert not json.loads((out / "summary.json").read_text())["passed"]


def test_expected_failure_and_restore_pass(tmp_path):
    run, out = invoke(
        tmp_path,
        [
            {
                "name": "mutant",
                "argv": [sys.executable, "-c", "print('guard failed'); exit(1)"],
                "expected_exit": 1,
                "contains": ["guard failed"],
            },
            {"name": "restore", "always": True, "argv": [sys.executable, "-c", "exit(0)"]},
        ],
    )
    assert run.returncode == 0, run.stderr
    assert json.loads((out / "summary.json").read_text())["passed"]
    # A prior receipt is never silently reused or overwritten.
    again = subprocess.run(run.args, cwd=ROOT, capture_output=True)
    assert again.returncode != 0


def test_empty_plan_cannot_pass(tmp_path):
    run, out = invoke(tmp_path, [])
    assert run.returncode != 0
    assert not (out / "summary.json").exists()


def test_phase_telemetry_records_skip_failure_and_selected_nodes(tmp_path):
    sample = tmp_path / "test_sample.py"
    sample.write_text(
        "import pytest\ndef test_ok(): pass\n"
        "@pytest.mark.skip(reason='explicit reason')\ndef test_skip(): pass\n"
        "def test_bad(): assert False, 'distinct assertion'\n"
    )
    events = tmp_path / "events.jsonl"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "tests.verification_timing",
            "--timing-jsonl",
            str(events),
            str(sample),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1, run.stdout + run.stderr
    rows = [json.loads(line) for line in events.read_text().splitlines()]
    selected = next(r for r in rows if r["event"] == "collection")
    assert len(selected["nodeids"]) == 3
    phases = [r for r in rows if r["event"] == "phase"]
    assert {r["when"] for r in phases} == {"setup", "call", "teardown"}
    assert any(r["outcome"] == "skipped" and "explicit reason" in r["detail"] for r in phases)
    assert any(r["outcome"] == "failed" and "distinct assertion" in r["detail"] for r in phases)
    assert rows[-1]["event"] == "finish" and rows[-1]["exitstatus"] == 1
    assert all(r["duration_s"] >= 0 for r in phases)


def test_empty_pytest_exit_cannot_be_expected_success(tmp_path):
    run, out = invoke(
        tmp_path,
        [
            {
                "name": "empty",
                "argv": [sys.executable, "-c", "print('no tests'); exit(5)"],
                "expected_exit": 5,
                "contains": ["no tests"],
            },
        ],
    )
    assert run.returncode != 0
    assert not (out / "summary.json").exists()


def test_unfinished_telemetry_is_not_a_pass_receipt(tmp_path):
    sample = tmp_path / "test_interrupted.py"
    sample.write_text("import os\ndef test_abort(): os._exit(7)\n")
    events = tmp_path / "partial.jsonl"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "tests.verification_timing",
            "--timing-jsonl",
            str(events),
            str(sample),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
    )
    assert run.returncode == 7
    rows = [json.loads(line) for line in events.read_text().splitlines()]
    assert any(r["event"] == "test_start" for r in rows)
    assert not any(r["event"] == "finish" for r in rows)
