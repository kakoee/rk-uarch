"""Inventory construction controls only; no startup substitution or defense revert."""

import hashlib
import json

import pytest

from native.tools.component_startup_inventory import copy_bound, write_manifest


def test_manifest_has_explicit_roots_and_external_binding(tmp_path):
    root = tmp_path / "import-root"
    root.mkdir()
    entry = root / "entry.py"
    entry.write_text("VALUE = 7\n")
    path, expected = write_manifest(tmp_path / "manifest.json", [root], [entry])
    assert expected == hashlib.sha256(path.read_bytes()).hexdigest()
    assert json.loads(path.read_bytes()) == {
        "roots": [str(root)],
        "files": {str(entry): hashlib.sha256(entry.read_bytes()).hexdigest()},
    }
    assert path.stat().st_mode & 0o222 == 0
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 9\n")
    with pytest.raises(ValueError, match="outside explicit roots"):
        write_manifest(tmp_path / "bad.json", [root], [outside])


def test_existing_input_copy_checks_pin_and_retains_origin(tmp_path):
    source = tmp_path / "original"
    source.write_bytes(b"existing accepted input")
    target = tmp_path / "snapshot"
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    record = copy_bound(source, target, "sha256:" + expected)
    assert target.read_bytes() == source.read_bytes()
    assert target.stat().st_mode & 0o222 == 0
    assert record == {
        "origin": str(source),
        "snapshot": str(target),
        "sha256": expected,
        "bytes": 23,
    }
    with pytest.raises(ValueError, match="input digest"):
        copy_bound(source, tmp_path / "wrong", "0" * 64)
    assert not (tmp_path / "wrong").exists()
