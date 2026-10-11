"""Real read-only vendor entry points; recorded integrity is not current compatibility.

Only this checkout's installed-package roots are exposed to subprocesses. The repository
root must not be supplied through PYTHONPATH to hide a broken direct script entry point.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def invoke_python(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    for name in ("PYTHONPATH", "MYPYPATH", "UARCH_HUMAN", "SHA", "RK", "PARAMS"):
        env.pop(name, None)
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / p) for p in ("src", "contract"))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def invoke(mode: str, *args: str) -> subprocess.CompletedProcess[str]:
    entry = ["scripts/vendor_rk.py"] if mode == "direct" else ["-m", "scripts.vendor_rk"]
    return invoke_python(*entry, *args)


@pytest.mark.parametrize("mode", ["direct", "module"])
def test_current_check_matches_strict_library_validation(mode: str) -> None:
    expected = strict_library_result()
    result = invoke(mode, "--check")
    assert (result.returncode, result.stdout, result.stderr) == (
        expected.returncode, expected.stdout, expected.stderr
    )


@pytest.mark.parametrize("mode", ["direct", "module"])
def test_historical_check_authenticates_recorded_bytes_only(mode: str) -> None:
    result = invoke(mode, "--check", "--historical")
    assert result.returncode == 0, result.stderr
    assert "historical integrity and recorded identity ONLY; current compatibility not checked" in (
        result.stdout
    )
    assert "current compatibility verified" not in result.stdout
    assert not result.stderr


@pytest.mark.parametrize("mode", ["direct", "module"])
def test_writer_refuses_before_generation(mode: str) -> None:
    # No upstream or output arguments, no human flag; main must stop at its writer guard.
    result = invoke(mode)
    assert result.returncode == 1
    assert "human-only vendor operation" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


@pytest.mark.parametrize("mode", ["direct", "module"])
def test_historical_requires_check(mode: str) -> None:
    result = invoke(mode, "--historical")
    assert result.returncode == 1
    assert "--historical requires --check" in result.stderr


def strict_library_result() -> subprocess.CompletedProcess[str]:
    # Authentic canonical bytes may be stale or legitimately current. Only a validation
    # ValueError is translated to CLI form; imports/setup and integrity must succeed.
    code = """
import sys
from pathlib import Path
before = list(sys.path)
from scripts import vendor_rk
assert sys.path == before
assert vendor_rk.ROOT == Path.cwd()
assert vendor_rk.__name__ == 'scripts.vendor_rk'
from scripts import u2_inputs
assert u2_inputs.vendor is vendor_rk
assert u2_inputs.ROOT == vendor_rk.ROOT
adopted = vendor_rk.ROOT / 'contract/vendor' / ('rk-sim@' + vendor_rk.PIN)
vendor_rk.check_manifest(adopted)
vendor_rk.check_snapshot_inputs(adopted)
vendor_rk.check_generator(adopted, current=False)
try:
    vendor_rk.check_contract_pin(vendor_rk.ROOT)
    vendor_rk.check_manifest(adopted, vendor_rk.PIN)
    vendor_rk.check_snapshot_inputs(adopted)
    vendor_rk.check_generator(adopted, current=True)
except ValueError as exc:
    sys.stderr.write(f'vendor-rk: {exc}\\n')
    sys.exit(1)
print(f'snapshot manifest, matrix and current compatibility verified: {adopted}')
"""
    result = invoke_python("-c", code)
    assert result.returncode in (0, 1), result
    if result.returncode == 0:
        assert "snapshot manifest, matrix and current compatibility verified: " in result.stdout
        assert not result.stderr
    else:
        assert not result.stdout
        assert result.stderr.startswith("vendor-rk: "), result.stderr
        assert "Traceback" not in result.stderr
    return result


def test_library_import_preserves_path_and_root() -> None:
    strict_library_result()
