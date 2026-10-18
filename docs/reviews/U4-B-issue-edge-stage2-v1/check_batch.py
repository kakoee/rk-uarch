"""Bounded B-only affected checks; A final combined-candidate closure remains separate.
Usage: python -I check_batch.py SOURCE BASELINE_RUNS A7 NEW_OUTPUT
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

source, runs, a7, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
out.mkdir(exist_ok=False)
here = Path(__file__).resolve().parent
venv = Path("/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin")
runner = Path("/tmp/u4-b-stage2-review-01/probes/runner.py")
manifest = json.loads((here / "manifest.json").read_text())
for row in manifest["files"]:
    assert (
        hashlib.sha256((source / row["path"]).read_bytes()).hexdigest() == row["postimage_sha256"]
    )
files = [row["path"] for row in manifest["files"]]
commands = [
    (
        "pytest",
        [
            str(venv / "python"),
            "-I",
            str(runner),
            str(source),
            "pytest",
            "validation/component/test_issue_checks.py",
            "-q",
        ],
    ),
    ("lint", [str(venv / "ruff"), "check", *files]),
    ("format", [str(venv / "ruff"), "format", "--check", *files]),
    ("types", [str(venv / "mypy"), "--strict", "--follow-imports=silent", *files[:2]]),
    (
        "consumer",
        [
            str(venv / "python"),
            "-I",
            str(runner),
            str(source),
            "script",
            str(here / "consume.py"),
            str(source),
            str(runs),
            str(a7),
            str(out / "consumer.json"),
        ],
    ),
    (
        "literal",
        [
            str(venv / "python"),
            "-I",
            str(here / "literal.py"),
            str(runs),
            str(out / "literal.json"),
        ],
    ),
    (
        "first-use",
        [
            str(venv / "python"),
            "-I",
            str(runner),
            str(source),
            "script",
            str(here / "first_use_controls.py"),
            str(source),
            str(runs),
            str(out / "first-use.json"),
        ],
    ),
    (
        "fault",
        [
            str(venv / "python"),
            "-I",
            str(here / "fault.py"),
            str(source),
            str(runs),
            str(a7),
            str(out / "fault"),
        ],
    ),
]
records = []
for name, argv in commands:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(argv, cwd=source, env=env, capture_output=True, timeout=120)
    (out / (name + ".stdout")).write_bytes(proc.stdout)
    (out / (name + ".stderr")).write_bytes(proc.stderr)
    row = {
        "name": name,
        "argv": argv,
        "cwd": str(source),
        "exit_code": proc.returncode,
        "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(),
    }
    records.append(row)
    (out / "checks.json").write_text(json.dumps(records, indent=2) + "\n")
    assert proc.returncode == 0, (name, proc.stdout, proc.stderr)
    print(name, "pass", flush=True)
cases = {x["case"]: x for x in json.loads((out / "consumer.json").read_text())["cases"]}
assert all(
    cases[n + "-" + m]["independent"] == "pass"
    for n in ("cc0-v3", "cc-v3", "sr-v3")
    for m in ("debug", "release")
)
assert (
    cases["A7-post-reservation-credit"]["independent"] == "CheckFailure: complete eligible causes"
)
assert (
    cases["A1-pre-release-grant"]["independent"]
    == "CheckFailure: opportunity eligible grants / ready tie"
)
# Expected old-A structural refusal is a declared remaining candidate dependency.
assert (
    cases["cc0-v3-debug"]["structural"]
    == "ValueError: AttributionMismatch: strict waiting credit causes"
)
for row in manifest["files"]:
    assert (
        hashlib.sha256((source / row["path"]).read_bytes()).hexdigest() == row["postimage_sha256"]
    )
