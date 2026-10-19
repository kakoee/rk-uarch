"""Synthetic ordinary-EOF preparation/retention controls. No Docker or authority."""

import json

import pytest
from uarch_contract.hashing import sha256

from rkuarch.engines.native import component_host, component_image
from tests.unit import test_component_runtime as fixtures


@pytest.fixture
def prepared(tmp_path, request):
    root, binding, _, _ = fixtures.prepared_payload.__wrapped__(tmp_path, request)
    return component_host._prepare_payload(root, binding, mode="debug")


def fake_guard(monkeypatch, prepared, *, failure=False, invalid=False, forged=False):
    # Fixture intentionally rebinds both job and saved result to synthetic source.
    saved_result = (prepared.root / "output.json").read_bytes()

    if forged:
        from uarch_contract.hashing import canonical_json, content_hash

        value = json.loads(saved_result)
        alignment = next(
            a
            for a in value["observations"]["activities"]["records"]
            if a["request_id"] == "r02.00"
            and a["kind"] == "alignment"
            and a["subphase"] == "dma_issue"
        )
        alignment["predecessors"].append({"activity_id": "activity-00000027", "relation": "credit"})
        value["result_hash"] = content_hash(value, exclude=("result_hash",))
        saved_result = canonical_json(value).encode()
    count = 0

    def run(directory, args, *, timeout, cap, stderr_cap, stdin_bytes):
        nonlocal count
        count += 1
        assert args[-3:] == ["/engine", "--protocol", "uarch-engine/3"]
        for flag, expected in [
            ("--network", "none"),
            ("--memory", "1g"),
            ("--cpus", "1"),
            ("--pids-limit", "64"),
            ("--ulimit", "nofile=256:256"),
        ]:
            assert args[args.index(flag) + 1] == expected
        assert component_image.IMAGE in args
        assert timeout == prepared.payload.budget.timeout_s
        assert cap == prepared.payload.budget.stdout_bytes
        assert stderr_cap == prepared.payload.budget.stderr_bytes
        selected = prepared.payload.jobs[0]
        assert sha256(stdin_bytes) == selected.file.byte_hash
        directory.mkdir()
        (directory / "stdout").write_bytes(
            b"partial" if failure else b"invalid" if invalid else saved_result
        )
        (directory / "stderr").write_bytes(b"diagnostic" if failure else b"")
        if failure:
            raise RuntimeError("synthetic management failure")
        return {
            "container_id": f"{count:064x}",
            "owner": "synthetic-owner",
            "exit_code": 0,
            "reason": "completed",
            "stopped": True,
            "removed": True,
        }

    monkeypatch.setattr(component_image, "run_container", run)


def test_image_entry_requires_existing_authority(tmp_path):
    with pytest.raises(ValueError, match="component authority"):
        component_image.run_component_image(
            tmp_path / "input", session=object(), evidence_root=tmp_path / "attempt"
        )
    assert not (tmp_path / "attempt").exists()


def test_saved_synthetic_result_uses_real_consumers(prepared, tmp_path, monkeypatch):
    fake_guard(monkeypatch, prepared)
    raw = prepared.root / prepared.payload.jobs[0].file.path
    result, record = component_image._run_prepared_image(raw, prepared, tmp_path / "attempt")
    assert result.duration_ps == 121000
    assert record["runtime_entries"] is None
    assert record["transport_kind"] == "ordinary-eof"
    assert record["validation_passed"] is True
    assert record["status"] == 0
    attempt = tmp_path / "attempt" / "attempt.json"
    saved = component_image.saved_input_from_attempt(
        attempt, sha256(attempt.read_bytes()), prepared
    )
    assert saved.read_bytes() == raw.read_bytes()
    saved.chmod(0o644)
    saved.write_bytes(b"changed")
    with pytest.raises(ValueError, match="saved input"):
        component_image.saved_input_from_attempt(attempt, sha256(attempt.read_bytes()), prepared)


@pytest.mark.parametrize("failure", [True, False])
def test_failure_retained_before_consumption(prepared, tmp_path, monkeypatch, failure):
    fake_guard(monkeypatch, prepared, failure=failure, invalid=not failure)
    raw = prepared.root / prepared.payload.jobs[0].file.path
    with pytest.raises((RuntimeError, ValueError)):
        component_image._run_prepared_image(raw, prepared, tmp_path / "attempt")
    record = json.loads((tmp_path / "attempt/attempt.json").read_bytes())
    assert record["validation_passed"] is False
    assert record["runtime_entries"] is None
    assert (tmp_path / "attempt/stdout").read_bytes() == (b"partial" if failure else b"invalid")
    assert record["status"] == (None if failure else 0)
    assert record["transport_complete"] is (not failure)


def test_six_saved_initial_receipts_reconsumed_for_replay(prepared, tmp_path, monkeypatch):
    from dataclasses import replace

    fake_guard(monkeypatch, prepared)
    raw = prepared.root / prepared.payload.jobs[0].file.path
    references = []
    for mode in ("debug", "release"):
        for repetition in range(3):
            root = tmp_path / f"initial-{mode}-{repetition}"
            component_image._run_prepared_image(
                raw, replace(prepared, mode=mode), root, repetition=repetition
            )
            receipt = root / "attempt.json"
            references.append((receipt, sha256(receipt.read_bytes())))
    saved, descriptor = component_image.admit_image_replay(references, prepared)
    assert saved.read_bytes() == raw.read_bytes()
    assert len(descriptor["initial_receipts"]) == 6
    assert descriptor["phase"] == "replay"
    with pytest.raises(ValueError, match="six distinct"):
        component_image.admit_image_replay([references[0]] * 6, prepared)
    first = references[0][0].parent / "stdout"
    first.write_bytes(b"corrupt saved output")
    with pytest.raises(ValueError, match="saved output"):
        component_image.admit_image_replay(references, prepared)


def test_image_real_consumer_refuses_resealed_causal_forgery(prepared, tmp_path, monkeypatch):
    fake_guard(monkeypatch, prepared, forged=True)
    raw = prepared.root / prepared.payload.jobs[0].file.path
    with pytest.raises(ValueError) as error:
        component_image._run_prepared_image(raw, prepared, tmp_path / "forged")
    assert "hash" not in str(error.value).lower()
    assert "predecessor" in str(error.value).lower() or "credit" in str(error.value).lower()
    receipt = json.loads((tmp_path / "forged/attempt.json").read_bytes())
    assert receipt["transport_complete"] is True
    assert receipt["validation_passed"] is False
    assert receipt["failure_stage"] == "consumer"
