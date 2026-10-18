"""Private export of an UNAPPLIED D3 module; no installed negative transport."""

import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def proposal(tmp_path):
    source = ROOT / "docs/reviews/U4-A-component-runtime-v1/proposals/component_negative-v2.py.txt"
    exported = tmp_path / "component_negative.py"
    exported.write_bytes(source.read_bytes())
    name = "private_negative_proposal"
    loader = SourceFileLoader(name, str(exported))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    yield module
    del sys.modules[name]


def case(module):
    return module.NegativeCase(
        case_id="synthetic-negative",
        raw={"path": "raw.json", "byte_hash": "sha256:" + "a" * 64},
        profile={"path": "profile.json", "byte_hash": "sha256:" + "b" * 64},
        expected_code="CapacityExceeded",
        expected_pointer=None,
        layer="resource-preflight",
    )


def test_d3_exact_refusal_and_no_zero_dispatch_claim(proposal):
    expected = {"code": "CapacityExceeded", "pointer": None, "message": "synthetic"}
    assert (
        proposal._consume_negative(b"", canonical_json(expected).encode(), 2, case(proposal))
        == expected
    )


@pytest.mark.parametrize(
    "status,code,pointer",
    [
        (0, "CapacityExceeded", None),
        (2, "TestProfileMismatch", None),
        (2, "CapacityExceeded", "/wrong"),
    ],
)
def test_d3_success_or_wrong_refusal_fails(proposal, status, code, pointer):
    error = canonical_json({"code": code, "pointer": pointer, "message": "synthetic"}).encode()
    with pytest.raises(ValueError):
        proposal._consume_negative(
            b"" if status == 2 else error, error if status == 2 else b"", status, case(proposal)
        )


def test_d3_has_no_raw_or_positive_authority_bypass(proposal, tmp_path, monkeypatch):
    monkeypatch.setattr(proposal, "_SELECTOR", tmp_path / "absent")
    with pytest.raises((ValueError, OSError)):
        proposal.prepare_negative(mode="debug")
    with pytest.raises(ValueError, match="separate D3 authority"):
        proposal.run_negative("synthetic-negative", session=object())
    with pytest.raises(TypeError):
        proposal.run_negative("synthetic-negative", raw=b"{}", session=object())


def test_d3_malformed_refusal_fails(proposal):
    with pytest.raises(ValueError):
        proposal._consume_negative(b"", b'{"code":"CapacityExceeded"}', 2, case(proposal))
