"""One affected Python/static check batch, independent of private native executions."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

SOURCE = Path("/tmp/u4-b-issue-edge-01/source")
OUT = Path("/tmp/u4-b-issue-edge-checks-01")
VENV = Path("/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin")
OUT.mkdir(exist_ok=False)
files = [
    "contract/uarch_contract/mapped.py",
    "contract/uarch_contract/mapped_issue.py",
    "contract/tests/mapped/test_component_issue_v3.py",
    "validation/component/observations_v3.py",
    "validation/component/transition_checks_v3.py",
    "validation/component/issue_checks.py",
    "validation/component/test_issue_checks.py",
    "validation/component/installation_identity.py",
    "validation/component/test_installation_identity.py",
    "native/tools/export_carriers.py",
]
commands = {
    "affected": [
        str(VENV / "python"),
        "-m",
        "pytest",
        "-q",
        "validation/component/test_installation_identity.py",
        "validation/component/test_stage2_selection.py",
        "contract/tests/mapped/test_component_issue_v3.py",
        "validation/component/test_issue_checks.py",
        "contract/tests/mapped/test_component_semantics_v2.py::test_component_refuses_legacy_observation_shape",
        "--junitxml=" + str(OUT / "affected.xml"),
    ],
    "schema": [str(VENV / "python"), "-m", "uarch_contract.generate_mapped", "--check"],
    "snapshot-k2": [str(VENV / "python"), "native/tools/export_carriers.py", "--check"],
    "snapshot-v2": [
        str(VENV / "python"),
        "native/tools/export_carriers.py",
        "--component",
        "--check",
    ],
    "snapshot-v3": [
        str(VENV / "python"),
        "native/tools/export_carriers.py",
        "--component-v3",
        "--check",
    ],
    "format": [str(VENV / "ruff"), "format", "--check", *files],
    "lint": [str(VENV / "ruff"), "check", *files],
    "mypy": [
        str(VENV / "mypy"),
        "--strict",
        "--follow-imports=silent",
        *[x for x in files if "/test_" not in x and not x.startswith("native/")],
    ],
}
rows = []
for name, argv in commands.items():
    p = subprocess.run(
        argv,
        cwd=SOURCE,
        env={
            **os.environ,
            "PYTHONPATH": str(SOURCE / "contract") + ":" + str(SOURCE / "src") + ":" + str(SOURCE),
        },
        capture_output=True,
        timeout=180,
    )
    (OUT / (name + ".stdout")).write_bytes(p.stdout)
    (OUT / (name + ".stderr")).write_bytes(p.stderr)
    rows.append(
        dict(
            name=name,
            argv=argv,
            cwd=str(SOURCE),
            exit_code=p.returncode,
            stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),
        )
    )
    (OUT / "checks.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(name, p.returncode, p.stdout.decode()[-200:], flush=True)
assert all(r["exit_code"] == 0 for r in rows)
