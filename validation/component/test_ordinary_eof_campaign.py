"""Finite synthetic harness controls; no Docker, real campaign or execution authority."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, cast

import pytest
from uarch_contract.hashing import canonical_json, sha256

from validation.component import ordinary_eof_campaign as campaign
from validation.component import test_ordinary_eof_acceptance as fixtures


@pytest.fixture
def setup(tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Any:
    make, row, config, _ = cast(Any, fixtures.synthetic).__wrapped__(tmp_path, request, monkeypatch)
    selection = {"rows": [row]}
    config["selection_byte_hash"] = sha256(canonical_json(selection).encode())
    h = campaign.helpers()
    h["discover"] = lambda *_: {"workers": 1, "synthetic": True}
    monkeypatch.setattr(campaign, "helpers", lambda: h)

    class SyntheticAdapter:
        def preflight(self, selection: Any, policy: Any) -> None:
            assert policy == campaign.POLICY

        def call(
            self,
            slot: Any,
            row: Any,
            evidence_root: Path,
            initial_references: Any,
            remaining_seconds: float,
        ) -> None:
            assert remaining_seconds <= campaign.POLICY["per_call_seconds"]
            descriptor = None
            if initial_references:
                descriptor = {
                    "phase": "replay",
                    "initial_receipts": [
                        {"path": r["path"], "byte_hash": r["byte_hash"]} for r in initial_references
                    ],
                    "raw_input_byte_hash": "sha256:"
                    + config["inputs"][row["case_id"]]["raw_input_sha256"],
                }
            make(str(evidence_root), slot["mode"], slot["repetition"], descriptor)

    return selection, config, SyntheticAdapter()


def test_mock_twelve_slots_replay_and_parent_cleanup(setup: Any, tmp_path: Path) -> None:
    selection, config, adapter = setup
    root = tmp_path / "campaign"
    value = campaign.run_campaign(selection, adapter, root, acceptance=config)
    assert value["complete"] and value["groups"][0]["calls"] == 12
    assert len(list(root.rglob("created.json"))) == 12
    assert all(
        json.loads(p.read_bytes())["runtime_entries"] is None for p in root.rglob("attempt.json")
    )
    cleanup = json.loads((root / "cleanup.json").read_bytes())
    assert cleanup["complete"] and len(cleanup["container_ids"]) == 12


@pytest.mark.parametrize("attack", ["raise", "corrupt", "replay", "budget", "cleanup"])
def test_failed_group_preserves_attempts_and_refuses_completion(
    setup: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    selection, config, adapter = setup
    original = adapter.call

    def call(slot: Any, row: Any, evidence_root: Path, refs: Any, seconds: float) -> None:
        if attack == "replay" and refs:
            (Path(refs[0]["path"]).parent / "stdout").write_bytes(b"changed saved output")
        original(slot, row, evidence_root, refs, seconds)
        if attack == "raise":
            raise RuntimeError("synthetic post-retention failure")
        if attack == "corrupt":
            (evidence_root / "stdout").write_bytes(b"forged")
        if attack == "budget":
            (evidence_root / "oversize").write_bytes(b"x" * 200000)
        if attack == "cleanup":
            path = evidence_root / "container/cleanup.json"
            value = json.loads(path.read_bytes())
            value["removed"] = False
            path.write_text(canonical_json(value))

    adapter.call = call
    if attack == "budget":
        monkeypatch.setitem(campaign.POLICY, "receipt_bytes", 100000)
    root = tmp_path / "campaign"
    with pytest.raises((ValueError, RuntimeError)):
        campaign.run_campaign(selection, adapter, root, acceptance=config)
    assert (root / "incomplete.json").exists()
    assert not (root / "complete.json").exists()
    assert list(root.rglob("attempt.json"))  # Original failed observations retained.
    assert (root / "cleanup.json").exists()


@pytest.mark.parametrize("deadline", ["per_call_seconds", "case_seconds", "total_seconds"])
def test_hanging_mock_is_bounded_and_incomplete(
    setup: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, deadline: str
) -> None:
    selection, config, adapter = setup
    monkeypatch.setitem(campaign.POLICY, deadline, 0.05)

    def hung(*args: Any) -> None:
        time.sleep(1)

    adapter.call = hung
    root = tmp_path / "campaign"
    began = time.monotonic()
    with pytest.raises(ValueError):
        campaign.run_campaign(selection, adapter, root, acceptance=config)
    assert time.monotonic() - began < 6
    assert (root / "incomplete.json").exists() and not (root / "complete.json").exists()


def test_session_bridge_cannot_turn_objects_into_authority(tmp_path: Path) -> None:
    adapter = campaign.SessionAdapter({"case": tmp_path / "unused"}, lambda _: object())
    with pytest.raises(ValueError, match="authority"):
        adapter.call(
            {"case_id": "case", "mode": "debug", "phase": "initial", "repetition": 0},
            {"case_id": "case", "expected_layer": "result"},
            tmp_path / "attempt",
            None,
            1,
        )
    assert not (tmp_path / "attempt").exists()


def test_preflight_is_inside_global_deadline(
    setup: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selection, config, adapter = setup
    monkeypatch.setitem(campaign.POLICY, "total_seconds", 0.05)
    adapter.preflight = lambda *_: time.sleep(1)
    root = tmp_path / "campaign"
    began = time.monotonic()
    with pytest.raises(ValueError):
        campaign.run_campaign(selection, adapter, root, acceptance=config)
    assert time.monotonic() - began < 1
    assert not list(root.rglob("intent.json"))
    assert (root / "incomplete.json").exists() and not (root / "complete.json").exists()
