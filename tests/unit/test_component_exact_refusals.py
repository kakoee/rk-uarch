"""Synthetic stable envelopes: site evidence remains a separate obligation."""

import pytest
from uarch_contract.hashing import canonical_json

from rkuarch.engines.native.component_runner import require_negative_envelope

EXPECTED = {
    "code": "CapacityExceeded",
    "message": "DMA fragment count exceeds limit",
    "pointer": None,
}


def test_exact_refusal():
    assert (
        require_negative_envelope(b"", canonical_json(EXPECTED).encode(), 2, EXPECTED) == EXPECTED
    )


@pytest.mark.parametrize(
    "message", ["complete output byte limit", "DMA request count exceeds limit"]
)
def test_same_code_wrong_guard_refuses(message):
    borrowed = dict(EXPECTED, message=message)
    with pytest.raises(ValueError, match="exact negative envelope"):
        require_negative_envelope(b"", canonical_json(borrowed).encode(), 2, EXPECTED)


@pytest.mark.parametrize("status,stdout,stderr", [(0, b"{}", b""), (2, b"x", b"{}"), (1, b"", b"")])
def test_negative_framing_is_mandatory(status, stdout, stderr):
    with pytest.raises(ValueError):
        require_negative_envelope(stdout, stderr, status, EXPECTED)
