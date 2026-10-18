"""Toy process/receipt tests only. No native engine, HostRecord or public invocation."""

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

from validation.component.runtime_campaign import (
    ROOT,
    check_replay_admission,
    run_private,
    schedule,
    verify_group,
)


class Toy:
    def __init__(self, fail=False):
        self.fail = fail

    def preflight(self, selection, policy):
        return dict(
            evidence_kind="private-synthetic-test",
            pids_limit=64,
            execution_binding="toy-only-no-native",
            input_hashes={
                r["case_id"]: hashlib.sha256(r["case_id"].encode()).hexdigest()
                for r in selection["rows"]
            },
            files={__file__: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        )

    def call(self, slot, row, initial, policy):
        if self.fail and slot["repetition"] == 1:
            raise ValueError("toy deliberate failure")
        return dict(
            process_identity=f"toy-worker-{os.getpid()}-slot-{slot['ordinal']}",
            raw_input=row["case_id"].encode(),
            stdout=b"toy result",
            stderr=b"",
            checked=True,
            outcome=row["expected_code"],
            producers_disabled=slot["phase"] == "replay",
            expected_pointer_verified=True,
            zero_dispatch_evidence="toy-only",
        )


def selection():
    return dict(
        selection_hash="toy-selection",
        rows=[
            dict(case_id="positive", expected_layer="result", expected_code="success"),
            dict(
                case_id="negative",
                expected_layer="resource-preflight",
                expected_code="CapacityExceeded",
            ),
        ],
    )


def test_actual_schedule_counts():
    full = json.loads(
        (ROOT / "docs/reviews/U4-B-component-runtime-preparation-v1/selection.json").read_bytes()
    )
    slots = schedule(full)
    assert len(slots) == 1368
    assert sum(s["phase"] == "initial" for s in slots) == 744
    assert sum(s["phase"] == "replay" for s in slots) == 624
    assert [s["ordinal"] for s in slots] == list(range(len(slots)))


def test_toy_parallel_receipts_and_deterministic_schedule(tmp_path):
    out = tmp_path / "run"
    result = run_private(selection(), Toy(), out, resources={"workers": 2})
    assert result["complete"] and not result["acceptance_gate"]
    assert result["completed_calls"] == 18
    records = [json.loads(p.read_bytes()) for p in sorted((out / "calls").glob("*.json"))]
    assert [r["ordinal"] for r in records] == list(range(18))
    assert all(r["evidence_kind"] == "private-synthetic-test" for r in records)
    assert not (out / "incomplete.json").exists()


def test_worker_failure_records_incomplete_and_no_retry(tmp_path):
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="worker failure"):
        run_private(selection(), Toy(fail=True), out, resources={"workers": 2})
    assert (out / "launch.json").exists() and (out / "incomplete.json").exists()
    assert not (out / "complete.json").exists()
    assert len(list((out / "calls").glob("*.json"))) <= 2


def test_developer_subset_never_claims_complete_gate(tmp_path):
    out = tmp_path / "subset"
    value = run_private(selection(), Toy(), out, cases=["positive"], resources={"workers": 1})
    assert value["completed_calls"] == 12 and value["acceptance_gate"] is False


def test_missing_and_duplicate_slots_and_replay_drift_refuse(tmp_path):
    out = tmp_path / "slots"
    run_private(selection(), Toy(), out, cases=["positive"], resources={"workers": 1})
    rows = [json.loads(p.read_bytes()) for p in sorted((out / "calls").glob("*.json"))]
    for bad in (rows[:-1], rows + [rows[0]]):
        with pytest.raises(ValueError, match="slot membership"):
            verify_group(bad, replay=True)
    bad = deepcopy(rows)
    bad[-1]["stdout_sha256"] = "wrong"
    with pytest.raises(ValueError, match="canonical output"):
        verify_group(bad, replay=True)
    bad = deepcopy(rows)
    bad[-1]["producers_disabled"] = False
    with pytest.raises(ValueError, match="producer-disabled"):
        verify_group(bad, replay=True)


def test_failed_or_misbound_receipt_cannot_admit_replay():
    good = dict(
        complete=True,
        outcome="success",
        evidence_kind="private-synthetic-test",
        execution_binding="bound",
        raw_input_sha256="input",
    )
    kwargs = dict(
        input_sha256="input", execution_binding="bound", evidence_kind="private-synthetic-test"
    )
    check_replay_admission(good, **kwargs)
    for field, value in [
        ("complete", False),
        ("outcome", "CapacityExceeded"),
        ("execution_binding", "stale"),
        ("raw_input_sha256", "changed"),
        ("evidence_kind", "public-component"),
    ]:
        with pytest.raises(ValueError):
            check_replay_admission(good | {field: value}, **kwargs)


def test_public_claim_is_not_an_authority_capability(tmp_path):
    class Claimed(Toy):
        def preflight(self, *args):
            return dict(super().preflight(*args), evidence_kind="public-component")

    with pytest.raises(ValueError, match="no public execution"):
        run_private(selection(), Claimed(), tmp_path / "claim", resources={"workers": 1})


def test_public_replay_claim_cannot_substitute_authority():
    receipt = dict(
        complete=True,
        outcome="success",
        evidence_kind="public-component",
        execution_binding="claimed",
        raw_input_sha256="input",
        authority_receipt_sha256="caller-claim",
    )
    with pytest.raises(ValueError, match="public replay authority join unavailable"):
        check_replay_admission(
            receipt,
            input_sha256="input",
            execution_binding="claimed",
            evidence_kind="public-component",
        )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("raw_input", b"different-job", "immutable selected raw input"),
        ("outcome", "success", "wrong refusal/result outcome"),
        ("expected_pointer_verified", False, "exact refusal pointer"),
        ("zero_dispatch_evidence", None, "separate native zero-dispatch"),
    ],
)
def test_adapter_mismatches_fail_closed(tmp_path, field, value, reason):
    class Broken(Toy):
        def call(self, *args):
            return dict(super().call(*args), **{field: value})

    with pytest.raises(ValueError, match=reason):
        run_private(
            selection(),
            Broken(),
            tmp_path / "bad-adapter",
            cases=["negative"],
            resources={"workers": 1},
        )
    assert not (tmp_path / "bad-adapter/complete.json").exists()
