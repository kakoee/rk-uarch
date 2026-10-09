"""Durable controls for Javid's exact U2-AD-C2-decision-v1 option A.

This exercises the conservative source guard, not hostile-environment security.
Mutations use actual reviewed source bytes; no digest or import is mocked.
"""

import hashlib
from pathlib import Path

import pytest

from .vendor_support import check_production_isolation

ROOT = Path(__file__).resolve().parents[2]
PROOF = Path("src/rkuarch/provenance/proof_raw.py")
REVIEWED_SHA256 = "9f47439f058417e24fcf2891f996d7b9428a69c4c8825c5e3188936c6d659c15"
GENERATOR = Path("contract/uarch_contract/generate.py")


@pytest.fixture
def reviewed_tree(tmp_path: Path) -> Path:
    raw = (ROOT / PROOF).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == REVIEWED_SHA256
    target = tmp_path / PROOF
    target.parent.mkdir(parents=True)
    target.write_bytes(raw)
    # Every negative case has the real passing control, before any mutation.
    check_production_isolation(tmp_path)
    return tmp_path


def test_exact_reviewed_source_is_allowed(reviewed_tree: Path) -> None:
    assert (reviewed_tree / PROOF).read_bytes() == (ROOT / PROOF).read_bytes()
    check_production_isolation(reviewed_tree)


@pytest.mark.parametrize(
    "before,after",
    [
        pytest.param(b"", b"\n# Unreviewed comment only.\n", id="comment-hash-drift"),
        pytest.param(b'files("rkuarch.provenance")', b'files("rk")', id="rk-package"),
        pytest.param(b'files("rkuarch.provenance")', b'files("foreign")', id="foreign-package"),
        pytest.param(b'files("rkuarch.provenance")', b"files(package)", id="dynamic-package"),
        pytest.param(b'"proof_schemas", name', b'"other_schemas", name', id="schema-directory"),
        pytest.param(b'schema("original.json")', b'schema("../original.json")', id="schema-path"),
        pytest.param(
            b"from importlib.resources import files",
            b"from importlib.resources import files as local_files",
            id="import-alias",
        ),
        pytest.param(
            b"from importlib.resources import files",
            b"from importlib.resources import files, as_file",
            id="additional-import",
        ),
        pytest.param(b"", b'\nfiles("other_package")\n', id="extra-resource-call"),
    ],
)
def test_any_unreviewed_source_change_refuses(
    reviewed_tree: Path, before: bytes, after: bytes
) -> None:
    path = reviewed_tree / PROOF
    original = path.read_bytes()
    if before:
        assert original.count(before) == 1
        changed = original.replace(before, after)
    else:
        changed = original + after
    assert hashlib.sha256(changed).hexdigest() != REVIEWED_SHA256
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="production vendor isolation"):
        check_production_isolation(reviewed_tree)


@pytest.mark.parametrize(
    "relative",
    [
        "src/rkuarch/provenance/another.py",
        "src/other/proof_raw.py",
        "contract/uarch_contract/proof_raw.py",
    ],
)
def test_same_reviewed_bytes_at_other_path_refuse(reviewed_tree: Path, relative: str) -> None:
    target = reviewed_tree / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / PROOF).read_bytes())
    assert hashlib.sha256(target.read_bytes()).hexdigest() == REVIEWED_SHA256
    with pytest.raises(ValueError, match="production vendor isolation"):
        check_production_isolation(reviewed_tree)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("from importlib.resources import files\n", id="unrelated-resource-import"),
        pytest.param("import importlib.resources\n", id="resource-module-import"),
        pytest.param("import rk\n", id="direct-rk"),
        pytest.param("from rk.engine import f0\n", id="rk-submodule"),
        pytest.param("import scripts.vendor_rk\n", id="scripts-vendor-import"),
        pytest.param("from scripts.vendor_rk import PIN\n", id="scripts-vendor-from"),
        pytest.param("import scripts\n", id="scripts-root"),
        pytest.param(
            "import importlib\nimportlib.import_module('r' + 'k')\n", id="dynamic-rk"
        ),
        pytest.param(
            "from importlib import import_module as load\nload('rk')\n", id="loader-alias"
        ),
        pytest.param("__import__('rk')\n", id="builtin-import"),
        pytest.param("exec('print(1)')\n", id="exec"),
        pytest.param("eval('1')\n", id="eval"),
        pytest.param("loader.import_module('foreign')\n", id="dynamic-method"),
        pytest.param("VendorLoader(root)\n", id="vendor-loader"),
        pytest.param("p = 'contract/vendor/source.py'\n", id="vendor-path"),
        pytest.param("p = 'rk-sim@pin'\n", id="vendor-pin"),
        pytest.param("p = 'scripts.vendor_rk'\n", id="vendor-script-string"),
    ],
)
def test_unrelated_imports_dynamic_execution_and_vendor_access_refuse(
    reviewed_tree: Path, source: str
) -> None:
    (reviewed_tree / "src/unrelated.py").write_text(source)
    with pytest.raises(ValueError, match="production vendor isolation"):
        check_production_isolation(reviewed_tree)


def test_actual_schema_generator_retains_its_fixed_local_exception(reviewed_tree: Path) -> None:
    target = reviewed_tree / GENERATOR
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / GENERATOR).read_bytes())
    check_production_isolation(reviewed_tree)


@pytest.mark.parametrize(
    "replacement",
    [
        'importlib.import_module("rk")',
        "importlib.import_module(name)",
        'exec("pass")',
    ],
)
def test_schema_generator_still_refuses_other_dynamic_calls(
    reviewed_tree: Path, replacement: str
) -> None:
    target = reviewed_tree / GENERATOR
    target.parent.mkdir(parents=True)
    actual = (ROOT / GENERATOR).read_text()
    target.write_text(actual)
    check_production_isolation(reviewed_tree)
    fixed = 'importlib.import_module(f"uarch_contract.{name}")'
    assert actual.count(fixed) == 1
    target.write_text(actual.replace(fixed, replacement))
    with pytest.raises(ValueError, match="production vendor isolation"):
        check_production_isolation(reviewed_tree)


def test_schema_generator_exception_does_not_move_with_source(reviewed_tree: Path) -> None:
    (reviewed_tree / "src/displaced_generator.py").write_bytes((ROOT / GENERATOR).read_bytes())
    with pytest.raises(ValueError, match="production vendor isolation"):
        check_production_isolation(reviewed_tree)
