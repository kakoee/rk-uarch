"""One private digest fault, paired positive and exact restoration; never native."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

root, output = (Path(value).resolve() for value in sys.argv[1:])
assert root.is_relative_to(Path("/tmp")) and output.is_relative_to(Path("/tmp"))
target = root / "validation/component/ordinary_build_acceptance.py"
original = target.read_bytes()
needle = '    need(sha256(binary) == artifact["byte_hash"], "actual executable digest")'
assert original.decode().count(needle) == 1
runner = root / "docs/reviews/U4-B-activation-orchestration-v1/probes/isolated_runner.py"
command = [
    sys.executable,
    "-I",
    str(runner),
    str(root),
    "pytest",
    "-q",
    "validation/component/test_ordinary_build_acceptance.py",
    "-k",
    "ordinary_diagnostics_and_absent_trace or wrong-executable",
]
try:
    target.write_text(
        original.decode().replace(
            needle, "    # targeted fault: omit actual executable digest equality"
        )
    )
    with (output / "fault-removed.log").open("w") as log:
        result = subprocess.run(
            command + ["--basetemp=" + str(output / "pytest-fault")],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    assert result.returncode == 1
    raw = (output / "fault-removed.log").read_text()
    assert "DID NOT RAISE" in raw and "1 failed, 1 passed" in raw
finally:
    target.write_bytes(original)
assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(original).digest()
with (output / "fault-restored.log").open("w") as log:
    result = subprocess.run(
        command + ["--basetemp=" + str(output / "pytest-restored")],
        cwd=root,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
assert result.returncode == 0
(output / "fault.json").write_text(
    json.dumps(
        {
            "removed_guard": "actual executable digest equality",
            "removed": (
                "wrong actual executable unsafely accepted; negative DID NOT RAISE; "
                "ordinary-output positive passes"
            ),
            "restored": "2 affected controls pass",
            "exact_restored_sha256": hashlib.sha256(original).hexdigest(),
            "native_execution": False,
            "authority": None,
        },
        indent=2,
    )
    + "\n"
)
