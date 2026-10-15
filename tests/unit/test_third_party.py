"""Every directory under third_party/ is registered, and every registered licence is allowed."""
from pathlib import Path

ALLOWED = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "Apache-2.0 WITH LLVM-exception"}
ROOT = Path(__file__).resolve().parents[2] / "third_party"


def _register() -> dict[str, str]:
    rows = [line for line in (ROOT / "LICENSES.md").read_text().splitlines()
            if line.startswith("|") and not line.startswith("|---")][1:]
    return {r.split("|")[1].strip(): r.split("|")[3].strip() for r in rows}


UNICODE_PIN = "1.0.27; sha256:a2c754d6c33795a1c324727428e5a7dedb5b06195f9890bdbcba760d3e246563"


def _allowed(component: str, pin: str, licence: str) -> bool:
    # Installed U0011: exact crate/version/checksum exception, never a global allowance.
    return licence in ALLOWED or (
        component == "unicode-ident" and pin == UNICODE_PIN
        and licence == "MIT AND Unicode-3.0"
    )


def test_unicode_exception_is_exact() -> None:
    assert _allowed("unicode-ident", UNICODE_PIN, "MIT AND Unicode-3.0")
    assert not _allowed("another-crate", UNICODE_PIN, "MIT AND Unicode-3.0")
    assert not _allowed("unicode-ident", "1.0.28", "MIT AND Unicode-3.0")
    assert not _allowed("unicode-ident", UNICODE_PIN, "Unicode-3.0")
    assert not _allowed("unicode-ident", UNICODE_PIN, "GPL-3.0-only")


def test_every_registered_licence_is_allowed() -> None:
    rows = [line.split("|") for line in (ROOT / "LICENSES.md").read_text().splitlines()
            if line.startswith("|") and not line.startswith("|---")][1:]
    bad = {r[1].strip(): r[3].strip() for r in rows
           if not _allowed(r[1].strip(), r[2].strip(), r[3].strip())}
    assert not bad, f"licences outside the allow-list: {bad}"


def test_every_third_party_directory_is_registered() -> None:
    dirs = {p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "patches"}
    missing = dirs - set(_register())
    assert not missing, f"unregistered third_party directories: {sorted(missing)}"
