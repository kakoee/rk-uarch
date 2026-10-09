"""Authenticated, received U1 test data; no ambient vendor fallback or oracle run."""

import hashlib
import json
from pathlib import Path

HISTORICAL_MANIFEST = "b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d"
ROOT = Path(__file__).resolve().parents[2]


def authenticate_historical(root: Path) -> Path:
    """Check the complete 20-file revision every time, including its raw manifest."""
    manifest = (root / "MANIFEST.json").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != HISTORICAL_MANIFEST:
        raise ValueError("historical test manifest identity")
    expected = json.loads(manifest)["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if len(actual) != 20 or actual != set(expected) | {"MANIFEST.json"}:
        raise ValueError("historical test inventory")
    for name in actual:
        path = root / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("historical test symlink")
        if name in expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]:
            raise ValueError("historical test member identity: " + name)
    return root


def historical_snapshot() -> Path:
    return authenticate_historical(ROOT / "tests/fixtures/u2_b/historical-u1")
