"""Run only host checks in an explicit disposable export; receipts outside that export."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {
        str(p.relative_to(root)): (sha(p), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def main(root, out):
    root, out = root.resolve(), out.resolve()
    package = Path(__file__).resolve().parent
    assert root.is_relative_to(Path("/tmp")) and not (root / ".git").exists()
    assert out.is_relative_to(Path("/tmp")) and not out.is_relative_to(root)
    out.mkdir(exist_ok=True, parents=True)
    env = dict(os.environ)
    for name in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"):
        env.pop(name, None)
    setup = (
        "import sys; from pathlib import Path; "
        f"r=Path({str(root)!r}); "
        f'sys.path[:0]=[{str(package)!r},str(r),str(r/"src"),str(r/"contract")]; '
    )
    selection = [
        str(package / "test_literals.py"),
        str(package / "test_boundary.py"),
        str(package / "test_membership.py"),
        "contract/tests/mapped",
        "contract/tests/test_u2_resource_isolation.py",
    ]
    args = [
        "-q",
        "-c",
        str(root / "pyproject.toml"),
        "--rootdir=" + str(root),
        "-p",
        "no:cacheprovider",
        "--basetemp=" + str(out / "pytest"),
        *selection,
    ]
    py = [sys.executable, "-I", "-B"]
    commands = {
        "host-tests": py
        + ["-c", setup + "import pytest; raise SystemExit(pytest.main(" + repr(args) + "))"],
        "source-audit": py + [str(package / "audit.py"), str(root), str(out / "audit.json")],
        "currentness": py + [str(root / "scripts/vendor_rk.py"), "--check"],
        "schema": py
        + [
            "-c",
            setup + 'import runpy; sys.argv=["generate_mapped","--check"]; '
            'runpy.run_module("uarch_contract.generate_mapped",run_name="__main__")',
        ],
        "ruff": [
            str(Path(sys.executable).parent / "ruff"),
            "check",
            "--no-cache",
            "--config",
            str(root / "pyproject.toml"),
            str(package),
        ],
    }
    before = snapshot(root)
    rows = []
    for name, command in commands.items():
        start = time.monotonic()
        result = subprocess.run(
            command, cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        log = out / (name + ".log")
        log.write_text(result.stdout)
        rows.append(
            dict(
                name=name,
                command=command,
                cwd=str(root),
                exit_code=result.returncode,
                seconds=round(time.monotonic() - start, 3),
                log_sha256=sha(log),
            )
        )
        print(name, result.returncode, result.stdout[-400:], flush=True)
    after = snapshot(root)
    preservation = dict(
        files=len(before),
        added=sorted(after.keys() - before.keys()),
        removed=sorted(before.keys() - after.keys()),
        bytes_or_mtimes_changed=sorted(
            k for k in before.keys() & after.keys() if before[k] != after[k]
        ),
    )
    receipt = dict(
        source_commit="418d6972f6bc367d648b811227b0e97829a8b292",
        python=sys.version,
        environment_unset=["PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"],
        commands=rows,
        preservation=preservation,
        native_executed=False,
    )
    (out / "checks.json").write_text(json.dumps(receipt, indent=2) + "\n")
    assert all(row["exit_code"] == 0 for row in rows), rows
    assert not any(preservation[k] for k in ("added", "removed", "bytes_or_mtimes_changed"))


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
