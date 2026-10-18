"""Synthetic saved-output adapters; no native execution, authority or cleanup proof."""

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json

from validation.component.runtime_campaign import ROOT, digest, run_private, schedule
from validation.component.runtime_evidence import exact_refusal, replay_admission
from validation.component.test_runtime_checks import inputs


class Synthetic:
    def __init__(self, tmp_path, attack=None):
        job, result, row, kwargs = inputs()
        row.update(expected_layer="result", expected_code="success")
        self.case, self.kwargs = row["case_id"], kwargs
        self.raw, self.stdout = kwargs["raw_input"], canonical_json(result).encode()
        self.original = tmp_path / "producer-input"
        self.original.write_bytes(self.raw)
        self.output, self.attack = tmp_path / "run", attack
        self.selection = dict(selection_hash="synthetic-selection", rows=[row])
        self.acceptance = dict(
            format="component-private-acceptance/1",
            evidence_kind="private-synthetic-test",
            selection_sha256=digest(canonical_json(self.selection).encode()),
            execution_binding="synthetic-execution",
            inputs={self.case: kwargs["admitted"]},
            negatives={},
            source=str(ROOT),
            pins=kwargs["pins"],
            observation_contract=kwargs["expected"],
            executables=dict(debug="synthetic-debug", release="synthetic-release"),
            witness_kind="synthetic-unit-anchor",
        )

    def preflight(self, selection, policy):
        return dict(
            evidence_kind="private-synthetic-test",
            pids_limit=64,
            execution_binding=self.acceptance["execution_binding"],
            files={__file__: digest(Path(__file__).read_bytes())},
            input_hashes={self.case: digest(self.raw)},
        )

    def cleanup(self):
        return dict(verified_stopped=True, outstanding=[], evidence="synthetic-no-process")

    def call(self, slot, row, initial, policy):
        if self.attack == "call-failure" and slot["ordinal"] == 3:
            raise ValueError("synthetic transport failed")
        # No producer is callable in replay: saved artifact alone is sufficient.
        raw = (
            Path(initial["saved_input_path"]).read_bytes()
            if initial
            else self.original.read_bytes()
        )
        if slot["ordinal"] == 5 and self.attack == "no-producer":
            self.original.unlink()
        if slot["ordinal"] == 5 and self.attack == "missing-receipt":
            (self.output / "calls/00000.json").unlink()
        if slot["ordinal"] == 5 and self.attack == "corrupt-saved":
            (self.output / "blobs" / digest(self.raw)).write_bytes(b"corrupt")
        stdout = self.stdout
        if self.attack == "unparseable-all" or (
            self.attack == "unparseable" and slot["ordinal"] == 3
        ):
            stdout = b"FAILING-CALL-EVIDENCE"
        pid = f"synthetic-{os.getpid()}-{slot['ordinal']}"
        if self.attack == "group-drift" and slot["ordinal"] == 11:
            pid = f"synthetic-{os.getpid()}-0"
        witness = dict(
            case_id=self.case,
            mode=slot["mode"],
            raw_input_sha256=digest(raw),
            semantic_output_sha256=digest(stdout),
            executable_sha256=self.acceptance["executables"][slot["mode"]],
            process_identity=pid,
            transport_complete=True,
            runtime_entries=1,
            evidence="synthetic-unit-anchor",
        )
        if self.attack == "fake-witness":
            witness = "/nonexistent/zero-entry"
        if self.attack == "non-json-witness":
            witness = Path("/nonexistent/zero-entry")
        return dict(
            raw_input=raw,
            stdout=stdout,
            stderr=b"",
            status=0,
            process_identity=pid,
            witness=witness,
            cleanup=dict(container_id="synthetic", process_identity=pid, verified_stopped=True),
            checked=True,
            producers_disabled=True,
            expected_pointer_verified=True,
        )


def run(adapter):
    return run_private(
        adapter.selection,
        adapter,
        adapter.output,
        acceptance=adapter.acceptance,
        resources={"workers": 1},
    )


def test_historical_schedule_unchanged():
    full = json.loads(
        (ROOT / "docs/reviews/U4-B-component-runtime-preparation-v1/selection.json").read_bytes()
    )
    slots = schedule(full)
    assert len(slots) == 1368 and sum(s["phase"] == "replay" for s in slots) == 624


def test_actual_consumption_and_durable_replay_with_producer_unavailable(tmp_path):
    a = Synthetic(tmp_path, "no-producer")
    r = run(a)
    assert r["complete"] and r["completed_calls"] == 12 and not r["acceptance_gate"]
    assert len(list((a.output / "attempts").glob("*.json"))) == 12


@pytest.mark.parametrize(
    "attack,reason",
    [
        ("unparseable", "JSONDecodeError"),
        ("fake-witness", "saved witness"),
        ("call-failure", "transport failed"),
        ("missing-receipt", "FileNotFoundError"),
        ("corrupt-saved", "blob collision"),
        ("group-drift", "fresh process identity"),
    ],
)
def test_campaign_rejects_and_preserves_failed_group(tmp_path, attack, reason):
    a = Synthetic(tmp_path, attack)
    with pytest.raises(ValueError, match=reason):
        run(a)
    report = json.loads((a.output / "incomplete.json").read_bytes())
    assert not report["complete"] and report["incomplete_groups"]
    assert not (a.output / "complete.json").exists()
    if attack == "unparseable":
        attempt = json.loads((a.output / "attempts/00003.json").read_bytes())
        assert (a.output / attempt["stdout_blob"]).read_bytes() == b"FAILING-CALL-EVIDENCE"
        assert not attempt["validation_passed"]
        assert report["incomplete_groups"][0]["unresolved_slots"] == list(range(3, 12))
    if attack == "group-drift":
        assert report["validated_calls"] == 12
        assert report["incomplete_groups"][0]["unresolved_slots"] == []
        assert list((a.output / "groups").glob("*/failed.json"))


def test_exact_refusal_rejects_borrowed_pre_and_post_dispatch_envelopes():
    expected = dict(
        code="InvalidDependency", message="accumulator use before production", pointer=None
    )
    exact_refusal(canonical_json(expected).encode(), expected)
    with pytest.raises(ValueError, match="intended refusal"):
        exact_refusal(
            canonical_json(dict(expected, message="final consumers acc")).encode(), expected
        )
    expected = dict(code="CapacityExceeded", message="zacc", pointer=None)
    with pytest.raises(ValueError, match="intended refusal"):
        exact_refusal(
            canonical_json(dict(expected, message="complete output byte limit")).encode(), expected
        )


def test_replay_rejects_incomplete_misbound_and_corrupt_retained_evidence(tmp_path):
    a = Synthetic(tmp_path)
    run(a)
    refs = [
        dict(
            path=f"calls/{i:05d}.json",
            sha256=digest((a.output / f"calls/{i:05d}.json").read_bytes()),
        )
        for i in range(6)
    ]
    row = a.selection["rows"][0]
    replay_admission(a.output, refs, row, a.acceptance)
    for field, value in [
        ("validation_passed", False),
        ("case_id", "foreign"),
        ("execution_binding", "stale"),
    ]:
        original = (a.output / refs[0]["path"]).read_bytes()
        changed = json.loads(original) | {field: value}
        raw = canonical_json(changed).encode()
        (a.output / refs[0]["path"]).write_bytes(raw)
        altered = deepcopy(refs)
        altered[0]["sha256"] = digest(raw)
        with pytest.raises(ValueError, match="initial receipt binding"):
            replay_admission(a.output, altered, row, a.acceptance)
        (a.output / refs[0]["path"]).write_bytes(original)
    original_blob = a.output / "blobs" / digest(a.raw)
    original_blob.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="retained evidence hash"):
        replay_admission(a.output, refs, row, a.acceptance)
    original_blob.write_bytes(a.raw)
    with pytest.raises(ValueError, match="complete initial"):
        replay_admission(a.output, refs[:-1], row, a.acceptance)


def test_public_execution_stays_unavailable(tmp_path):
    a = Synthetic(tmp_path)
    a.acceptance["evidence_kind"] = "public-component"
    with pytest.raises(ValueError, match="no public execution"):
        run(a)


class Negative(Synthetic):
    def __init__(self, tmp_path, attack=None):
        super().__init__(tmp_path, attack)
        row = self.selection["rows"][0]
        row.update(expected_layer="resource-preflight", expected_code="CapacityExceeded")
        self.envelope = dict(code="CapacityExceeded", message="zacc", pointer=None)
        self.acceptance["selection_sha256"] = digest(canonical_json(self.selection).encode())
        self.acceptance["negatives"] = {self.case: dict(envelope=self.envelope)}

    def call(self, slot, row, initial, policy):
        raw = super().call(slot, row, initial, policy)
        envelope = dict(self.envelope)
        if self.attack == "wrong-guard":
            envelope["message"] = "complete output byte limit"
        raw.update(stdout=b"", stderr=canonical_json(envelope).encode(), status=2)
        raw["witness"]["semantic_output_sha256"] = digest(raw["stderr"])
        raw["witness"]["runtime_entries"] = 7 if self.attack == "fake-zero" else 0
        # Producer assertions deliberately false: actual bytes decide acceptance.
        raw.update(checked=False, expected_pointer_verified=False)
        return raw


def test_negative_actual_bytes_override_adapter_flags(tmp_path):
    assert run(Negative(tmp_path))["completed_calls"] == 6


@pytest.mark.parametrize(
    "attack,reason",
    [("wrong-guard", "intended refusal"), ("fake-zero", "runtime-entry witness population")],
)
def test_negative_campaign_requires_intended_guard_and_bound_zero_entry(tmp_path, attack, reason):
    a = Negative(tmp_path, attack)
    with pytest.raises(ValueError, match=reason):
        run(a)
    attempt = json.loads((a.output / "attempts/00000.json").read_bytes())
    assert (a.output / attempt["stderr_blob"]).read_bytes()
    assert not attempt["validation_passed"]


def test_every_unparseable_positive_refuses_even_when_all_bytes_match(tmp_path):
    a = Synthetic(tmp_path, "unparseable-all")
    with pytest.raises(ValueError, match="JSONDecodeError"):
        run(a)


def test_cancelled_worker_has_incomplete_group_and_parent_cleanup(tmp_path, monkeypatch):
    import time

    from validation.component import runtime_campaign

    class Waiting(Synthetic):
        def call(self, *args):
            time.sleep(2)
            raise AssertionError("worker deadline did not cancel transport")

    monkeypatch.setitem(runtime_campaign.POLICY, "case_seconds", 0.05)
    a = Waiting(tmp_path)
    with pytest.raises(ValueError, match="deadline"):
        run(a)
    report = json.loads((a.output / "incomplete.json").read_bytes())
    assert report["incomplete_groups"][0]["unresolved_slots"] == list(range(12))
    assert json.loads((a.output / "cleanup.json").read_bytes())["verified_stopped"]
    assert not (a.output / "complete.json").exists()


def test_invalid_metadata_cannot_lose_attempt_blob_binding(tmp_path):
    a = Synthetic(tmp_path, "non-json-witness")
    with pytest.raises(ValueError, match="worker failure"):
        run(a)
    attempt = json.loads((a.output / "attempts/00000.json").read_bytes())
    assert (a.output / attempt["stdout_blob"]).read_bytes() == a.stdout
    assert attempt["case_id"] == a.case and not attempt["validation_passed"]
