"""Private saved-byte seam and unapplied D3 proposal; no native execution."""

import json
import runpy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, sha256

from native.tools.component_private_adapter import saved_input
from rkuarch.engines.native.records import FileBinding

ROOT = Path(__file__).resolve().parents[2]


def test_saved_replay_uses_retained_bytes_without_preparation(tmp_path, monkeypatch):
    raw = b'{"private":"saved"}'
    saved = tmp_path / "retained.json"
    saved.write_bytes(raw)
    binding = FileBinding(path="not-present.json", byte_hash=sha256(raw))
    initial = {"saved_input_path": str(saved), "raw_input_sha256": sha256(raw).split(":")[1]}

    def unavailable(*args, **kwargs):
        raise AssertionError("original input preparation unavailable")

    monkeypatch.setattr("native.tools.component_private_adapter._read", unavailable)
    assert saved_input(tmp_path, binding, initial, 1024) == raw
    saved.write_bytes(b'{"private":"changed"}')
    with pytest.raises(ValueError, match="private independent raw inventory"):
        saved_input(tmp_path, binding, initial, 1024)
    initial["raw_input_sha256"] = sha256(saved.read_bytes()).split(":")[1]
    with pytest.raises(ValueError, match="durable replay inventory digest"):
        saved_input(tmp_path, binding, initial, 1024)


def test_unapplied_d3_exact_envelope_and_version():
    proposal = (
        ROOT
        / "docs/reviews/U4-A-component-runtime-stage2-v1/proposals/component_negative-v4.py.txt"
    )
    namespace = runpy.run_path(str(proposal))
    envelope = {"code": "CapacityExceeded", "message": "synthetic finite guard", "pointer": None}
    file = {"path": "private.json", "byte_hash": "sha256:" + "a" * 64}
    case = namespace["NegativeCase"].model_validate(
        {
            "case_id": "SYNTHETIC",
            "raw": file,
            "profile": file,
            "expected_envelope": envelope,
            "expectation_provenance": file,
            "layer": "resource-preflight",
        }
    )
    consume = namespace["_consume_negative"]
    assert consume(b"", canonical_json(envelope).encode(), 2, case) == envelope
    for message in ("other finite guard", "complete output byte limit"):
        with pytest.raises(ValueError, match="exact negative envelope"):
            consume(b"", canonical_json(dict(envelope, message=message)).encode(), 2, case)
    inventory = {"format": "uarch-component-negative-inventory/2", "cases": [case.model_dump()]}
    assert namespace["NegativeInventory"].model_validate(inventory).cases == (case,)
    inventory["format"] = "uarch-component-negative-inventory/1"
    with pytest.raises(ValueError):
        namespace["NegativeInventory"].model_validate(inventory)
    manifest = json.loads((proposal.parent / "D3-manifest.json").read_bytes())
    assert sha256(proposal.read_bytes()).split(":")[1] == manifest["postimage_v4_sha256"]
