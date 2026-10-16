"""Fresh published source check with explicit module roots; no native invocation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main() -> None:
    os.nice(10)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    destination = Path(tempfile.mkdtemp(prefix="u4-component-fresh-")) / "source"
    subprocess.run(
        ["git", "clone", "--quiet", "--local", "--no-hardlinks", str(ROOT), str(destination)],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=destination, text=True
    ).strip()
    script = """
import pathlib, sys
root = pathlib.Path.cwd()
sys.path[:0] = [str(root), str(root/'src'), str(root/'contract')]
import rkuarch.mapping.component, rkuarch.workload.component, rkuarch.workload.mapped
import uarch_contract.mapped
for module in (rkuarch.mapping.component, rkuarch.workload.component,
               rkuarch.workload.mapped,uarch_contract.mapped):
    path = pathlib.Path(module.__file__).resolve()
    assert path.is_relative_to(root),path
    print(module.__name__,str(path),flush=True)
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',
    'tests/unit/test_u4_a_component_mapper.py','tests/unit/test_u4_a_mapped_loader.py',
    'contract/tests/mapped']))
"""
    env = dict(os.environ)
    for name in ("PYTHONPATH", "MYPYPATH"):
        env.pop(name, None)
    with (OUT / "fresh.log").open("wb") as log:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=destination,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    data = (OUT / "fresh.log").read_bytes()
    receipt = dict(
        source_commit=commit,
        root=str(destination),
        executable=sys.executable,
        bootstrap="python -I -B; explicit fresh root/src/contract",
        exit_code=result.returncode,
        log_sha256=hashlib.sha256(data).hexdigest(),
        last_lines=data.decode().splitlines()[-8:],
        native_calls=0,
        affinity=sorted(os.sched_getaffinity(0)),
    )
    (OUT / "fresh.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
