"""Small executed-command receipt; never substitutes expected support failure for tests."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

root = Path.cwd()
out = root / "docs/reviews/U2-A-RR-C1"
python = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=".:contract:src",
           MYPY_CACHE_DIR="/tmp/u2-a-rr-c1-mypy", XDG_CACHE_HOME="/tmp/u2-a-rr-c1-cache",
           HYPOTHESIS_STORAGE_DIRECTORY="/tmp/u2-a-rr-c1-hypothesis")
commands = [
    ("focused", [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=short",
                 "tests/integration/test_u2_a_condition_order.py"]),
    ("affected-regression", [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=short",
        "tests/integration/test_u2_a_replay.py", "tests/unit/test_u2_a_prepared.py",
        "tests/unit/test_u2_a_loader.py", "tests/unit/test_u2_a_artifacts.py",
        "tests/unit/test_u2_a_resolution_session.py"]),
    ("lint", [python, "-B", "-m", "ruff", "check", "--no-cache", "src/rkuarch/table/build.py",
              "tests/integration/test_u2_a_condition_order.py"]),
    ("types", [python, "-B", "-m", "mypy", "--no-incremental"]),
    ("strict-support-expected-refusal", [python, "-B", str(out / "support_lifecycle.py")]),
    ("diff-check", ["git", "diff", "--check"]),
]
record = dict(cwd=str(root), environment={k: env[k] for k in ["PYTHONDONTWRITEBYTECODE",
    "PYTHONPATH", "MYPY_CACHE_DIR", "XDG_CACHE_HOME", "HYPOTHESIS_STORAGE_DIRECTORY"]},
    source_hashes={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
        ["src/rkuarch/table/build.py", "tests/integration/test_u2_a_condition_order.py"]}, runs=[])
for name, argv in commands:
    start = time.monotonic()
    p = subprocess.run(argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / (name + ".log")).write_bytes(p.stdout)
    record["runs"].append(dict(name=name, argv=argv, returncode=p.returncode,
                              seconds=time.monotonic()-start, log=name + ".log"))
    (out / "checks.json").write_text(json.dumps(record, indent=2) + "\n")
    print(name, p.returncode, flush=True)
