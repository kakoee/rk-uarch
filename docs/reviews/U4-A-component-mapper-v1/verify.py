"""Bounded sequential Python verification; no native builds/jobs or CI polling."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COMMANDS = [
    ("lint", ["ruff", "check", "."]),
    ("imports", ["lint-imports"]),
    ("mypy-source", ["mypy", "src", "contract/uarch_contract", "scripts"]),
    ("mypy-contract", ["mypy", "--no-explicit-package-bases", "contract/tests"]),
    ("schema", ["python", "-m", "uarch_contract.generate", "--check"]),
    ("schema-rotary", ["python", "-m", "uarch_contract.generate_rotary_v2", "--check"]),
    ("schema-mapped", ["python", "-m", "uarch_contract.generate_mapped", "--check"]),
    ("vendor", ["python", "scripts/vendor_rk.py", "--check"]),
    (
        "integrated",
        [
            "pytest",
            "-q",
            "-rs",
            "--require-vendor",
            "tests/unit/test_u4_a_component_mapper.py",
            "tests/unit/test_u4_a_mapped_loader.py",
            "tests/integration/test_u2_a_replay.py",
            "tests/rotary_v2/test_boundary.py",
            "contract/tests/mapped",
        ],
    ),
]


def main() -> None:
    # One low-priority CPU; no competing full campaign or native selection.
    os.nice(10)
    allowed = os.sched_getaffinity(0)
    os.sched_setaffinity(0, {min(allowed)})
    env = dict(os.environ)
    for name in ("PYTHONPATH", "MYPYPATH"):
        env.pop(name, None)
    records = []
    receipt = dict(
        platform=platform.platform(),
        python=sys.version,
        executable=sys.executable,
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        affinity=sorted(os.sched_getaffinity(0)),
        nice=os.getpriority(os.PRIO_PROCESS, 0),
        environment_unset=["PYTHONPATH", "MYPYPATH"],
        native_calls=0,
        commands=records,
    )
    for name, command in COMMANDS:
        argv = ["uv", "run", "--no-sync", *command]
        start = time.monotonic()
        with (OUT / (name + ".log")).open("wb") as stream:
            result = subprocess.run(
                argv, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT
            )
        data = (OUT / (name + ".log")).read_bytes()
        record = dict(
            name=name,
            argv=argv,
            exit_code=result.returncode,
            elapsed_s=round(time.monotonic() - start, 3),
            log_sha256=hashlib.sha256(data).hexdigest(),
            last_lines=data.decode(errors="replace").splitlines()[-8:],
        )
        records.append(record)
        (OUT / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(name, result.returncode, record["elapsed_s"], flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
