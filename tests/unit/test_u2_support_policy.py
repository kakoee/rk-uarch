"""Prospective support-policy controls; no oracle or candidate generation."""

import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts import u2_inputs as ui
from scripts import u2_support as policy
from scripts import vendor_rk as vendor

REAL_ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def source_write_denial(root):
    """Enforce read-only real source during each test, not post-hoc restoration."""
    active = [True]
    protected = [root / p for p in ("src", "scripts", "contract", "hw", "tests",
                                         "validation", "docs", "native", "measure",
                                         "third_party", "containers", "pyproject.toml", "uv.lock")]

    def audit(event, args):
        if not active[0]:
            return
        paths = ()
        if event == "open":
            path, mode, flags = args
            if (mode and any(c in mode for c in "wax+")) or flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            ):
                paths = (path,)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.rename",
                       "os.symlink", "os.link"}:
            paths = args[:2] if event in {"os.rename", "os.symlink", "os.link"} else args[:1]
        for path in paths:
            if isinstance(path, (str, bytes, os.PathLike)):
                resolved = Path(os.fsdecode(path)).resolve()
                if "__pycache__" in resolved.parts:
                    continue  # Interpreter cache is not source/data.
                if (resolved.parent == root
                        or any(resolved == p or resolved.is_relative_to(p) for p in protected)):
                    raise PermissionError("test attempted write to real source root")

    sys.addaudithook(audit)
    try:
        yield
    finally:
        active[0] = False


@pytest.fixture(autouse=True)
def deny_source_writes():
    with source_write_denial(REAL_ROOT):
        yield


def test_real_source_write_guard():
    with pytest.raises(PermissionError, match="write to real source root"):
        (REAL_ROOT / "src/rkuarch/hw/derive.py").open("a")


@pytest.fixture
def isolated_root(tmp_path, monkeypatch):
    root = tmp_path / "isolated-source"
    assert not root.is_relative_to(REAL_ROOT)
    names = {p.relative_to(REAL_ROOT) for p in ui.support_files()}
    names.update(p.relative_to(REAL_ROOT) for p in policy.support_files(root=REAL_ROOT))
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REAL_ROOT / name, target)
    # Only specific read inputs/artifacts, not a repository checkpoint copy.
    shutil.copytree(REAL_ROOT / "contract/vendor", root / "contract/vendor")
    matches = list((REAL_ROOT / "docs/decisions").glob("U0001-*.md"))
    assert len(matches) == 1
    adr = matches[0].relative_to(REAL_ROOT)
    (root / adr).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REAL_ROOT / adr, root / adr)
    monkeypatch.setattr(ui, "ROOT", root)
    monkeypatch.setattr(vendor, "ROOT", root)
    return root


def test_import_origins_and_read_only_real_inventory():
    import uarch_contract

    import rkuarch.hw.derive as derive
    from scripts import u2_import_guard

    for module in (ui, policy, vendor, u2_import_guard, derive, uarch_contract):
        assert Path(module.__file__).resolve().is_relative_to(REAL_ROOT)
    assert "PYTHONPATH" not in os.environ and "MYPYPATH" not in os.environ
    policy.verify(policy.inventory(root=REAL_ROOT), root=REAL_ROOT)


def test_valid_inventory_includes_initializers_and_stage_data(isolated_root):
    names = policy.inventory(root=isolated_root)
    assert "contract/uarch_contract/__init__.py" in names
    assert "src/rkuarch/hw/derive.py" in names
    assert "contract/tests/fixtures/u2_b/a2-export/npu-l4.binding.json" in names
    assert "src/rkuarch/report/render.py" not in names
    policy.verify(names, root=isolated_root)


@pytest.mark.parametrize(
    "name",
    [
        "scripts/vendor_rk.py",
        "src/rkuarch/hw/derive.py",
        "contract/uarch_contract/hashing.py",
        "contract/uarch_contract/__init__.py",
        "hw/designs/npu-l4.yaml",
        "uv.lock",
        "pyproject.toml",
        "contract/tests/fixtures/u2_b/component-precisions.json",
    ],
)
def test_relevant_bytes_refuse(name, isolated_root):
    expected = policy.inventory(root=isolated_root)
    p = isolated_root / name
    original = p.read_bytes()
    try:
        if name == "src/rkuarch/hw/derive.py":
            assert b"2 * cores * rate.value" in original
            changed = original.replace(b"2 * cores * rate.value", b"3 * cores * rate.value")
        elif name == "contract/uarch_contract/hashing.py":
            assert b"sort_keys=True" in original
            changed = original.replace(b"sort_keys=True", b"sort_keys=False")
        elif name == "scripts/vendor_rk.py":
            assert b"for b in (1, 8, 32)" in original
            changed = original.replace(b"for b in (1, 8, 32)", b"for b in (1, 8, 16)")
        else:
            changed = original + b"\n# dependency audit fault\n"
        p.write_bytes(changed)
        with pytest.raises(ValueError, match="support bytes changed"):
            policy.verify(expected, root=isolated_root)
    finally:
        p.write_bytes(original)
    policy.verify(expected, root=isolated_root)


@pytest.mark.parametrize(
    "name",
    [
        "src/rkuarch/report/readiness_unrelated.py",
        "src/rkuarch/engines/native/readiness_unrelated.py",
        "contract/uarch_contract/mapped_future_audit.py",
    ],
)
def test_unimported_addition_does_not_change_policy(name, isolated_root):
    expected = policy.inventory(root=isolated_root)
    p = isolated_root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists()
    try:
        p.write_text("VALUE = 1\n")
        policy.verify(expected, root=isolated_root)
    finally:
        p.unlink()


def test_unrelated_existing_edit(isolated_root):
    expected = policy.inventory(root=isolated_root)
    p = isolated_root / "src/rkuarch/cli.py"
    original = p.read_bytes()
    try:
        p.write_bytes(original + b"\n# unrelated CLI documentation\n")
        policy.verify(expected, root=isolated_root)
    finally:
        p.write_bytes(original)


def test_new_local_import_cannot_evade_inventory(isolated_root):
    expected = policy.inventory(root=isolated_root)
    p = isolated_root / "src/rkuarch/hw/derive.py"
    added = p.with_name("audit_new_formula.py")
    original = p.read_bytes()
    assert not added.exists()
    try:
        added.write_text("VALUE = 1\n")
        p.write_bytes(original + b"\nfrom .audit_new_formula import VALUE\n")
        assert str(added.relative_to(isolated_root)) in policy.inventory(root=isolated_root)
        with pytest.raises(ValueError, match="support inventory changed"):
            policy.verify(expected, root=isolated_root)
    finally:
        p.write_bytes(original)
        added.unlink()


@pytest.mark.parametrize(
    "statement",
    [
        "import importlib\nimportlib.import_module('new_dependency')\n",
        "__import__('new_dependency')\n",
        "exec('import new_dependency')\n",
    ],
)
def test_dynamic_edges_require_review(statement, isolated_root):
    p = isolated_root / "src/rkuarch/hw/derive.py"
    original = p.read_bytes()
    try:
        p.write_bytes(original + statement.encode())
        with pytest.raises(ValueError, match="dynamic dependency"):
            policy.inventory(root=isolated_root)
    finally:
        p.write_bytes(original)


@pytest.mark.parametrize("name", ["yaml.py", "src/pydantic/__init__.py", "scripts/json.py"])
def test_external_module_shadow_refuses(name, isolated_root):
    p = isolated_root / name
    existed = p.parent.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists()
    try:
        p.write_text("# shadow\n")
        with pytest.raises(ValueError, match="unreviewed import name"):
            policy.inventory(root=isolated_root)
    finally:
        p.unlink()
        if not existed:
            p.parent.rmdir()


def test_missing_inventory_entry_and_substituted_hash(isolated_root):
    expected = policy.inventory(root=isolated_root)
    del expected["src/rkuarch/hw/derive.py"]
    with pytest.raises(ValueError, match="support inventory changed"):
        policy.verify(expected, root=isolated_root)
    expected = policy.inventory(root=isolated_root)
    expected["src/rkuarch/hw/derive.py"] = "0" * 64
    with pytest.raises(ValueError, match="support bytes changed"):
        policy.verify(expected, root=isolated_root)


def test_additional_stage_data_and_symlink_refuse(tmp_path, isolated_root):
    expected = policy.inventory(root=isolated_root)
    p = isolated_root / "contract/tests/fixtures/u2_b/a2-export/audit-extra.json"
    try:
        p.write_text("{}")
        with pytest.raises(ValueError, match="support inventory changed"):
            policy.verify(expected, root=isolated_root)
        p.unlink()
        p.symlink_to(tmp_path / "absent")
        with pytest.raises(ValueError, match="symlink"):
            policy.inventory(root=isolated_root)
    finally:
        p.unlink(missing_ok=True)


def test_pinned_legacy_integrity_is_not_current_generator_compatibility():
    from contract.tests.historical_snapshot import historical_snapshot
    from scripts import vendor_rk as vendor

    # Fixed, authenticated U1 bytes, independent of the mutable ui.ADOPTED path.
    legacy = historical_snapshot()
    vendor.check_manifest(legacy)
    vendor.check_generator(legacy, current=False)
    vendor.check_snapshot_inputs(legacy)
    with pytest.raises(
        ValueError, match="^GENERATOR current incompatibility: generator script fingerprint differs"
    ):
        vendor.check_generator(legacy, current=True)


def test_current_new_policy_adoption_requires_strict_validation():
    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    # A real positive gate, never satisfied by the synthetic controls below.
    vendor.check_manifest(ui.ADOPTED)
    vendor.check_generator(ui.ADOPTED, current=False)
    vendor.check_snapshot_inputs(ui.ADOPTED)
    if not (ui.ADOPTED / "u2-inputs/support-policy.json").exists():
        pytest.skip("real new-policy human generation/adoption has not occurred")
    vendor.check_generator(ui.ADOPTED, current=True)


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"format": "unknown"},
        {**policy.POLICY, "ignore": ["changed-file"]},
        {**policy.POLICY, "selection": "trust-output-equality"},
    ],
)
def test_policy_substitution_refuses(value, isolated_root):
    with pytest.raises(ValueError, match="support policy"):
        policy.verify({}, policy=value, root=isolated_root)


@pytest.mark.parametrize("member", ["PIN", "component-precisions.json", "support-files.json"])
def test_frozen_input_substitution_refuses_without_rehash(tmp_path, member):
    import shutil

    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    replica = tmp_path / "artifact-control"
    shutil.copytree(ui.ADOPTED, replica)
    frozen = replica / "u2-inputs"
    identity = vendor.digest((frozen / "SHA256SUMS").read_bytes())
    vendor.check_manifest(replica)
    # Structural control only; does not assert current source compatibility.
    ui.load_inputs(frozen, identity, check_support=False)
    path = frozen / member
    path.chmod(0o644)
    path.write_bytes(path.read_bytes() + b"\nsubstitution\n")
    with pytest.raises(ValueError):
        vendor.check_manifest(replica)
    with pytest.raises(ValueError, match="input bytes changed"):
        ui.load_inputs(frozen, identity, check_support=False)


@pytest.fixture
def synthetic_public_inputs(tmp_path, monkeypatch, isolated_root):
    """Rehashed carrier copies ONLY: no generator metadata, provenance or adoption.

    Existing typed carriers remain intact. Recompute the input manifest after every
    intentional support-metadata substitution so tests reach the public policy gate.
    Never invoke prepare_inputs or copy/relabel a whole generated snapshot.
    """
    import shutil

    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    def forbidden(*args, **kwargs):
        pytest.fail("synthetic public-load control must not run a producer")

    for module, name in (
        (ui, "prepare_inputs"),
        (vendor, "run_oracle"),
        (vendor, "collect_snapshot"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    frozen = tmp_path / "synthetic-rehashed-inputs-not-adoption"
    shutil.copytree(ui.ADOPTED / "u2-inputs", frozen)
    for path in frozen.rglob("*"):
        if path.is_file():
            path.chmod(0o644)
    (frozen / "support-policy.json").write_bytes(vendor.canonical(policy.POLICY))
    (frozen / "support-files.json").write_bytes(
        vendor.canonical(policy.inventory(root=isolated_root))
    )
    return frozen


def rehash_synthetic_inputs(frozen):
    from scripts import vendor_rk as vendor

    files = {p.relative_to(frozen).as_posix(): p for p in frozen.rglob("*") if p.is_file()}
    files.pop("SHA256SUMS")
    manifest = "".join(
        vendor.digest(path.read_bytes()) + "  " + name + "\n"
        for name, path in sorted(files.items())
    ).encode()
    (frozen / "SHA256SUMS").write_bytes(manifest)
    return vendor.digest(manifest)


def test_public_load_valid_new_policy(synthetic_public_inputs):
    from scripts import u2_inputs as ui

    identity = rehash_synthetic_inputs(synthetic_public_inputs)
    result = ui.load_inputs(synthetic_public_inputs, identity)
    assert result.manifest_sha256 == identity
    assert result.entries and result.models and result.matrix
    assert result.root == synthetic_public_inputs


@pytest.mark.parametrize("attack", ["bound_bytes", "missing_entry", "wrong_hash", "new_dependency"])
def test_public_load_new_policy_drift_refuses(synthetic_public_inputs, attack, isolated_root):
    import json

    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    frozen = synthetic_public_inputs
    identity = rehash_synthetic_inputs(frozen)
    assert ui.load_inputs(frozen, identity).entries
    name = "src/rkuarch/hw/derive.py"
    source = isolated_root / name
    added = source.with_name("public_load_new_dependency.py")
    assert not added.exists()
    original = source.read_bytes()
    support_file = frozen / "support-files.json"
    support = json.loads(support_file.read_bytes())
    refusal = "^input support bytes changed: src/rkuarch/hw/derive\\.py$"
    try:
        if attack == "bound_bytes":
            assert b"2 * cores * rate.value" in original
            source.write_bytes(
                original.replace(b"2 * cores * rate.value", b"3 * cores * rate.value")
            )
        elif attack == "missing_entry":
            del support[name]
            support_file.write_bytes(vendor.canonical(support))
            refusal = "^input support inventory changed$"
        elif attack == "wrong_hash":
            support[name] = "0" * 64
            support_file.write_bytes(vendor.canonical(support))
        else:
            added.write_text("VALUE = 1\n")
            source.write_bytes(original + b"\nfrom .public_load_new_dependency import VALUE\n")
            refusal = "^input support inventory changed$"
        identity = rehash_synthetic_inputs(frozen)
        # Integrity/typed validation still succeeds; currentness must refuse.
        assert ui.load_inputs(frozen, identity, check_support=False).entries
        with pytest.raises(ValueError, match=refusal):
            ui.load_inputs(frozen, identity, check_support=True)
    finally:
        source.write_bytes(original)
        added.unlink(missing_ok=True)


@pytest.mark.parametrize("check_support", [False, True])
@pytest.mark.parametrize(
    "value",
    [{}, {"format": "unknown"}, {**policy.POLICY, "selection": "trust-output-equality"}],
)
def test_public_load_policy_substitution_refuses(synthetic_public_inputs, value, check_support):
    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    frozen = synthetic_public_inputs
    (frozen / "support-policy.json").write_bytes(vendor.canonical(value))
    with pytest.raises(ValueError, match="^unrecognized input support policy$"):
        ui.load_inputs(frozen, rehash_synthetic_inputs(frozen), check_support=check_support)


@pytest.mark.parametrize("attack", ["bound_bytes", "missing_entry", "new_file"])
def test_public_load_legacy_dispatch(synthetic_public_inputs, monkeypatch, attack, isolated_root):
    from scripts import u2_inputs as ui
    from scripts import vendor_rk as vendor

    def wrong_dispatch(*args, **kwargs):
        pytest.fail("legacy inputs must retain the complete legacy rule")

    monkeypatch.setattr(policy, "verify", wrong_dispatch)
    frozen = synthetic_public_inputs
    (frozen / "support-policy.json").unlink()
    support = {p.relative_to(ui.ROOT).as_posix(): vendor.digest(p.read_bytes())
               for p in ui.support_files()}
    support_file = frozen / "support-files.json"
    support_file.write_bytes(vendor.canonical(support))
    identity = rehash_synthetic_inputs(frozen)
    assert ui.load_inputs(frozen, identity, check_support=True).entries
    name = "src/rkuarch/hw/derive.py"
    source = ui.ROOT / name
    added = source.with_name("public_load_legacy_added.py")
    assert not added.exists()
    original = source.read_bytes()
    try:
        if attack == "bound_bytes":
            source.write_bytes(original + b"\n# changed legacy bound bytes\n")
            refusal = "^input support changed: src/rkuarch/hw/derive\\.py$"
        elif attack == "missing_entry":
            del support[name]
            support_file.write_bytes(vendor.canonical(support))
            refusal = "^input support inventory changed$"
        else:
            added.write_text("VALUE = 1\n")
            refusal = "^input support inventory changed$"
        identity = rehash_synthetic_inputs(frozen)
        assert ui.load_inputs(frozen, identity, check_support=False).entries
        with pytest.raises(ValueError, match=refusal):
            ui.load_inputs(frozen, identity, check_support=True)
    finally:
        source.write_bytes(original)
        added.unlink(missing_ok=True)


@pytest.mark.parametrize("directory", [".", "scripts", "src", "contract"])
@pytest.mark.parametrize("name", ["typing_extensions", "annotated_types"])
@pytest.mark.parametrize("kind", ["module", "package"])
def test_public_load_transitive_shadow_refuses(
    synthetic_public_inputs, isolated_root, directory, name, kind
):
    identity = rehash_synthetic_inputs(synthetic_public_inputs)
    assert ui.load_inputs(synthetic_public_inputs, identity).entries
    base = isolated_root / directory
    base.mkdir(exist_ok=True)
    shadow = base / (name + ".py") if kind == "module" else base / name / "__init__.py"
    shadow.parent.mkdir(exist_ok=True)
    shadow.write_text("raise RuntimeError('SHADOW_BODY_MUST_NOT_EXECUTE')\n")
    with pytest.raises(ValueError, match="^unreviewed import name:"):
        ui.load_inputs(synthetic_public_inputs, identity)


def direct_environment(root):
    env = os.environ.copy()
    for key in ("PYTHONPATH", "MYPYPATH", "UARCH_HUMAN"):
        env.pop(key, None)
    # Explicit isolated subprocess roots replace, never inherit, ambient import paths.
    env["PYTHONPATH"] = os.pathsep.join(str(root / p) for p in ("src", "contract"))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def direct(root, *args, entry="vendor_rk.py"):
    return subprocess.run(
        [sys.executable, "scripts/" + entry, *args],
        cwd=root, env=direct_environment(root), text=True, capture_output=True, check=False,
    )


def test_fresh_direct_valid_controls(isolated_root):
    origins = subprocess.run(
        [sys.executable, "-c", "from pathlib import Path; import scripts.vendor_rk as v; "
         "import scripts.u2_inputs as u; import uarch_contract as c; import rkuarch as r; "
         "assert all(Path(m.__file__).resolve().is_relative_to(Path.cwd()) "
         "for m in (v,u,c,r)); print('isolated origins verified')"],
        cwd=isolated_root, env=direct_environment(isolated_root),
        text=True, capture_output=True, check=False,
    )
    assert origins.returncode == 0, origins.stderr
    assert "isolated origins verified" in origins.stdout
    for args in (("--help",), ("--check", "--historical")):
        result = direct(isolated_root, *args)
        assert result.returncode == 0, result.stderr
    assert direct(isolated_root, "--help", entry="u2_inputs.py").returncode == 0
    result = direct(isolated_root, "--check")
    assert result.returncode == 1
    assert result.stderr.strip() == "vendor-rk: input support inventory changed"


@pytest.mark.parametrize("directory", [".", "scripts", "src", "contract"])
@pytest.mark.parametrize("name", ["typing_extensions", "annotated_types"])
@pytest.mark.parametrize("entry", ["vendor_rk.py", "u2_inputs.py"])
def test_fresh_direct_shadow_refuses_before_body(isolated_root, directory, name, entry):
    path = isolated_root / directory / (name + ".py")
    path.write_text("raise RuntimeError('SHADOW_BODY_MUST_NOT_EXECUTE')\n")
    result = direct(isolated_root, "--check", entry=entry)
    assert result.returncode != 0
    assert "unreviewed import name:" in result.stderr
    assert "SHADOW_BODY_MUST_NOT_EXECUTE" not in result.stderr


def test_unrelated_nested_source_and_document_additions(synthetic_public_inputs, isolated_root):
    identity = rehash_synthetic_inputs(synthetic_public_inputs)
    extra = isolated_root / "src/rkuarch/report/unrelated_stage2.py"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("VALUE = 1\n")
    (isolated_root / "docs/stage2-unrelated.md").write_text("Unrelated prose.\n")
    assert ui.load_inputs(synthetic_public_inputs, identity).entries


def test_complete_scripts_binding(synthetic_public_inputs, isolated_root):
    identity = rehash_synthetic_inputs(synthetic_public_inputs)
    extra = isolated_root / "scripts/hooks/stage2_helper.py"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="^input support inventory changed$"):
        ui.load_inputs(synthetic_public_inputs, identity)


def test_reserved_namespace_initializer_is_bound(synthetic_public_inputs, isolated_root):
    identity = rehash_synthetic_inputs(synthetic_public_inputs)
    path = isolated_root / "contract/__init__.py"
    assert path.is_file()
    path.write_bytes(path.read_bytes() + b"\n# initializer drift\n")
    with pytest.raises(ValueError, match="^input support bytes changed: contract/__init__"):
        ui.load_inputs(synthetic_public_inputs, identity)


@pytest.mark.parametrize("fault", ["old_python", "nonfrozen_os"])
def test_guard_bootstrap_premises_refuse(isolated_root, monkeypatch, fault):
    from types import SimpleNamespace

    from scripts import u2_import_guard as guard

    if fault == "old_python":
        monkeypatch.setattr(guard, "sys", SimpleNamespace(
            implementation=sys.implementation, version_info=(3, 11)))
    else:
        monkeypatch.setattr(guard, "os", SimpleNamespace(
            __spec__=SimpleNamespace(origin="untrusted.py")))
    with pytest.raises(ValueError, match="^unsupported import-guard bootstrap$"):
        guard.check_import_roots(str(isolated_root))


@pytest.mark.parametrize("exists", [False, True])
def test_root_file_write_denied_before_mutation(tmp_path, exists):
    # Deliberate denial probes use a throwaway root, never the checkout being tested.
    root = tmp_path / "guarded-root"
    root.mkdir()
    path = root / "root-file.py"
    if exists:
        path.write_bytes(b"ORIGINAL = 1\n")
    before = (path.read_bytes(), path.stat().st_mtime_ns) if exists else None
    with source_write_denial(root):
        with pytest.raises(PermissionError, match="^test attempted write to real source root$"):
            path.write_bytes(b"MUTATED = 1\n")
        if exists:
            assert (path.read_bytes(), path.stat().st_mtime_ns) == before
        else:
            assert not path.exists()
        # Normal temporary roots and read-only access must remain usable.
        other = tmp_path / "allowed-private-file"
        other.write_text("allowed")
        assert other.read_text() == "allowed"
        other.unlink()


@pytest.mark.parametrize("entry", ["vendor_rk", "u2_inputs"])
@pytest.mark.parametrize("form", ["direct", "module", "library"])
@pytest.mark.parametrize("kind", ["module", "package"])
def test_future_shadow_never_executes(isolated_root, entry, form, kind):
    if form == "direct":
        args = ["scripts/" + entry + ".py", "--help"]
    elif form == "module":
        args = ["-m", "scripts." + entry, "--help"]
    else:
        args = ["-c", "from pathlib import Path; from scripts import " + entry + " as m; "
                "assert Path(m.__file__).resolve() == Path.cwd() / 'scripts' / '"
                + entry + ".py'; print('O1_LIBRARY_ORIGIN_VERIFIED')"]

    def invoke():
        return subprocess.run(
            [sys.executable, "-B", *args], cwd=isolated_root,
            env=direct_environment(isolated_root), text=True, capture_output=True, check=False,
        )

    valid = invoke()
    assert valid.returncode == 0, valid.stderr
    assert ("O1_LIBRARY_ORIGIN_VERIFIED" if form == "library" else "usage:") in valid.stdout
    shadow = isolated_root / "scripts" / (
        "__future__.py" if kind == "module" else "__future__/__init__.py")
    shadow.parent.mkdir(exist_ok=True)
    shadow.write_text("import sys\nprint('O1_FUTURE_BODY_EXECUTED', file=sys.stderr)\n"
                      "annotations = None\n")
    result = invoke()
    assert "O1_FUTURE_BODY_EXECUTED" not in result.stdout + result.stderr
    assert result.returncode != 0
    assert "unreviewed import name: scripts/__future__" in result.stderr


def test_entry_annotations_resolve_without_future_bootstrap():
    from typing import get_type_hints

    from uarch_contract.exports import ComponentPrecision

    assert ui.Inputs.__annotations__["entries"] == tuple[ComponentPrecision, ...]
    assert get_type_hints(ui.load_inputs)["return"] is ui.Inputs
    assert vendor.validate_u2_component_inputs.__annotations__["return"] == (
        "tuple[ComponentPrecision, ...]")
    assert get_type_hints(vendor.validate_u2_component_inputs,
                          localns={"ComponentPrecision": ComponentPrecision})["return"] == (
        tuple[ComponentPrecision, ...])
