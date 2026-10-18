"""Bounded offline F2 controls and narrow-scope regression in a fresh private copy."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
assert out.is_relative_to(Path("/tmp"))
out.mkdir(exist_ok=False)
source = out / "source"
source.mkdir()
for name in ("restriction.py", "test_restriction.py"):
    shutil.copyfile(HERE / name, source / name)
shutil.copytree(HERE / "reproducers", source / "reproducers")
p = source / "restriction.py"
original = p.read_bytes()
guard = b"    if any(n > 1 for n in counts.values()):\n"
assert original.count(guard) == 1
python = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
argv = [
    python,
    "-I",
    "-m",
    "pytest",
    "-c",
    "/tmp/u4-b-f2f3-source-01/pyproject.toml",
    "--rootdir",
    str(source),
    "-p",
    "no:cacheprovider",
    str(source / "test_restriction.py"),
    "-q",
]
records = []


def run(label, expected):
    proc = subprocess.run(argv, capture_output=True, timeout=60)
    (out / (label + ".stdout")).write_bytes(proc.stdout)
    (out / (label + ".stderr")).write_bytes(proc.stderr)
    records.append(
        dict(
            label=label,
            exit_code=proc.returncode,
            source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            stdout_sha256=hashlib.sha256(proc.stdout).hexdigest(),
            argv=argv,
        )
    )
    assert proc.returncode == expected, (label, proc.stdout, proc.stderr)
    return proc.stdout


run("baseline", 0)
try:
    p.write_bytes(
        original.replace(
            guard,
            b'    if any(n > 1 for n in counts.values()) and len({t["direction"] '
            b'for t in jobs if t["kind"] == "dma"}) > 1:\n',
        )
    )
    stdout = run("narrow-mixed-only-fault", 1)
    assert b"6 failed, 14 passed" in stdout and b"AssertionError" in stdout
finally:
    p.write_bytes(original)
assert p.read_bytes() == original
run("restored", 0)
(out / "checks.json").write_text(
    json.dumps(
        dict(
            records=records,
            label="synthetic offline classification only; no validator or native execution",
            unsafe_classification=(
                "mixed-only mutant labels homogeneous multi-request engine outside F2; "
                "six directional controls fail"
            ),
            exact_restoration=True,
        ),
        indent=2,
    )
    + "\n"
)
print("20 controls pass; mixed-only fault fails six controls; exact restoration passes20")
