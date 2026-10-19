"""Unapplied D3 v6 transport wiring with synthetic streams; no native/public execution."""

import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from types import SimpleNamespace

import pytest
from uarch_contract.hashing import canonical_json

from rkuarch.engines.native import component_host, component_image
from tests.unit import test_component_runtime as fixtures


@pytest.mark.parametrize("wrong_message", [False, True])
def test_proposed_d3_image_transport_retains_exact_comparator(
    tmp_path, request, monkeypatch, wrong_message
):
    source = fixtures.ROOT / (
        "docs/reviews/U4-A-component-activation-readiness-v1/proposals/component_negative-v6.py.txt"
    )
    name = "synthetic_D3_image_proposal"
    loader = SourceFileLoader(name, str(source))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    loader.exec_module(module)
    root, binding, _, _ = fixtures.prepared_payload.__wrapped__(tmp_path, request)
    component = component_host._prepare_payload(root, binding, mode="debug")
    envelope = dict(
        code="CapacityExceeded", message="DMA fragment count exceeds limit", pointer=None
    )
    case = module.NegativeCase(
        case_id="synthetic-wiring-only",
        raw={"path": "job.json", "byte_hash": "sha256:" + "1" * 64},
        profile={"path": "profile.json", "byte_hash": "sha256:" + "2" * 64},
        expectation_provenance={"path": "provenance.json", "byte_hash": "sha256:" + "3" * 64},
        expected_envelope=envelope,
        layer="resource-preflight",
    )
    # Inherited v5 admission/provenance controls are unchanged. This tests the transport join.
    monkeypatch.setattr(module, "_selected_raw", lambda *args: (root / "job.json").read_bytes())
    received = dict(envelope, message="complete output byte limit") if wrong_message else envelope

    def transport(directory, args, **kwargs):
        assert component_image.IMAGE in args
        assert kwargs["stdin_bytes"] == (root / "job.json").read_bytes()
        directory.mkdir()
        (directory / "stdout").write_bytes(b"")
        (directory / "stderr").write_bytes(canonical_json(received).encode())
        return dict(
            exit_code=2,
            container_id="c" * 64,
            owner="synthetic",
            stopped=True,
            removed=True,
            reason="completed",
        )

    monkeypatch.setattr(component_image, "run_container", transport)
    prepared = SimpleNamespace(component=component, refresh=lambda: None)
    attempt = tmp_path / "negative-attempt"
    if wrong_message:
        with pytest.raises(ValueError, match="exact negative envelope"):
            module._run_negative_image(prepared, case, attempt, timeout_s=5, repetition=0)
    else:
        result = module._run_negative_image(prepared, case, attempt, timeout_s=5, repetition=0)
        assert result["error"] == envelope
    retained = json.loads((attempt / "attempt.json").read_bytes())
    assert retained["validation_passed"] is (not wrong_message)
    assert retained["runtime_entries"] is None
    assert retained["status"] == 2
    assert (attempt / "stderr").read_bytes() == canonical_json(received).encode()
    with pytest.raises(ValueError, match="separate D3 authority"):
        module.run_negative(case.case_id, session=object(), evidence_root=tmp_path / "public")
    assert not (tmp_path / "public").exists()
