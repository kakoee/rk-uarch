"""Historical ADR preservation; current source is not a runtime approval token."""
from hashlib import sha256
from pathlib import Path

ADR = "docs/decisions/U0011-the-native-engine-core.md"
INSTALLED_BYTES = 32221
INSTALLED_SHA = "afae0ebea7dfdfe761ec76ae374a35441db989f866a4ca4f5c29f0169a49e69b"
COMPONENT_SHA = "ad9b5369073403fa8a881a04e628db620c89f21d66ec062e90c3bc753c7eadba"
ISSUE_ADR_SHA = "79ec2b939d5cdd02905861c03e1a8f32733648f47cfbb4db2d1d477dd0a414a7"
ISSUE_APPENDIX_SHA = "b6f868c5dcd7ee610d85da2396bb5f617687fc8dbb0aa6f84941d62f6a057247"
ISSUE_ADR_BYTES = 67486

def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()

ROOT = Path(__file__).resolve().parents[2]


def test_historical_adr_bytes_are_preserved() -> None:
    raw = (ROOT / ADR).read_bytes()
    historical = raw[:ISSUE_ADR_BYTES]
    assert digest(historical) == ISSUE_ADR_SHA
    assert digest(historical[:INSTALLED_BYTES]) == INSTALLED_SHA
    assert digest(historical[INSTALLED_BYTES:48294]) == COMPONENT_SHA
    assert digest(historical[48294:]) == ISSUE_APPENDIX_SHA
    assert b"Basic provenance and ordinary native execution" in raw[ISSUE_ADR_BYTES:]
