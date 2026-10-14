"""Read-only scratch repair checks; never stages inputs or runs generation."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
PYTHON = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "MYPYPATH", "UARCH_HUMAN"}}
env["PYTHONDONTWRITEBYTECODE"] = "1"


def snapshot(root):
    return {
        str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


runs = []
for name in ("pristine", "repair"):
    root = PACKAGE / "scratch" / name
    before = snapshot(root)
    commands = [
        [
            PYTHON,
            "-B",
            "-c",
            "import sys; sys.path[:0]=['.', 'src', 'contract']; "
            "from scripts import vendor_rk; vendor_rk.main()",
            "--check",
        ]
    ]
    if name == "repair":
        commands += [
            [
                PYTHON,
                "-B",
                "-m",
                "pytest",
                "-c",
                "pyproject.toml",
                "--rootdir",
                ".",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(PACKAGE / "scratch/test-tmp"),
                "-q",
                "-rs",
                "tests/unit/test_u2_support_policy.py",
                "tests/unit/test_vendor_script_entry.py",
            ],
            [
                PYTHON,
                "-B",
                "-c",
                "import sys,json; "
                "sys.path[:0]=['.', 'src', 'contract']; "
                "from scripts import u2_support as p,u2_inputs as u,vendor_rk as v; "
                "import rkuarch.hw.derive as d,uarch_contract as c; "
                "print(json.dumps({'origins':[m.__file__ for m in (p,u,v,d,c)],"
                "'closure':p.inventory()},sort_keys=True))",
            ],
        ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
        output = result.stdout + result.stderr
        (PACKAGE / f"{name}-{index}.log").write_text(output)
        runs.append(
            {
                "export": name,
                "argv": command,
                "exit_code": result.returncode,
                "log": f"{name}-{index}.log",
            }
        )
        print(name, index, result.returncode, output[-1200:], flush=True)
    after = snapshot(root)
    assert before == after, name + " export changed during checks"
    runs.append({"export": name, "files_checked": len(before), "bytes_and_mtime_unchanged": True})
(PACKAGE / "checks.json").write_text(
    json.dumps(
        {
            "base_commit": "f58e07828fa7a953b06800b227b948d7e9e71a88",
            "environment": PYTHON,
            "runs": runs,
        },
        indent=2,
    )
    + "\n"
)
