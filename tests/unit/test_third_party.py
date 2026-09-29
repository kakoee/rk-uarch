"""Every directory under third_party/ is registered, and every registered licence is allowed."""
from pathlib import Path

ALLOWED = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "Apache-2.0 WITH LLVM-exception"}
ROOT = Path(__file__).resolve().parents[2] / "third_party"


def _register() -> dict[str, str]:
    rows = [line for line in (ROOT / "LICENSES.md").read_text().splitlines()
            if line.startswith("|") and not line.startswith("|---")][1:]
    return {r.split("|")[1].strip(): r.split("|")[3].strip() for r in rows}


def test_every_registered_licence_is_allowed() -> None:
    bad = {k: v for k, v in _register().items() if v not in ALLOWED}
    assert not bad, f"licences outside the allow-list: {bad}"


def test_every_third_party_directory_is_registered() -> None:
    dirs = {p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "patches"}
    missing = dirs - set(_register())
    assert not missing, f"unregistered third_party directories: {sorted(missing)}"
