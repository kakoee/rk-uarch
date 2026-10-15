"""Exercise patch application/postimage checks without writing repository sources."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "patch_check", ROOT / ".github/check_third_party_patches.py"
)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture
def export(tmp_path):
    record = json.loads((ROOT / checker.RECORD).read_text())
    chain = json.loads((ROOT / checker.CHAIN).read_text())
    names = [checker.RECORD, checker.CHAIN, record["path"], record["patch"]]
    names.extend(step["patch"] for step in chain["followups"])
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    return tmp_path, record


def test_exact_patch_application_preserves_inputs(export):
    root, record = export
    before = {
        str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()
    }
    assert checker.check(root) == record
    assert before == {
        str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "change", ["patch", "register", "extra", "missing", "base", "followup", "chain"]
)
def test_patch_or_identity_drift_refuses(export, change):
    root, record = export
    if change in ("patch", "register"):
        path = root / record["patch" if change == "patch" else "path"]
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
    elif change == "extra":
        (root / "third_party/patches/9999-unknown.patch").write_text("unreviewed")
    elif change == "missing":
        (root / record["patch"]).unlink()
    elif change == "followup":
        chain = json.loads((root / checker.CHAIN).read_text())
        (root / chain["followups"][0]["patch"]).write_text("changed")
    elif change == "chain":
        path = root / checker.CHAIN
        chain = json.loads(path.read_text())
        chain["followups"][0]["before_sha256"] = "0" * 64
        path.write_text(json.dumps(chain))
    else:
        record["before_sha256"] = "0" * 64
        (root / checker.RECORD).write_text(json.dumps(record))
    with pytest.raises(ValueError):
        checker.check(root)
