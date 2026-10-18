"""Prospective /3 preparation tests; synthetic jobs confer no authority."""

import hashlib
import json
from collections import Counter

import pytest
from uarch_contract.mapped import PRODUCTION_HARDWARE, admit

from validation.component.runtime_selection import HISTORY, PRIOR, ROOT, definitions


@pytest.fixture(scope="module")
def frozen():
    return definitions()


def test_complete_history_and_distinct_d13(frozen):
    selection = frozen["selection"]
    rows = selection["rows"]
    old = json.loads((ROOT / HISTORY).read_bytes())
    assert {r["historical_case"] for r in rows if r["historical_case"]} == {
        r["case_id"] for r in old["cases"]
    }
    prior = json.loads((ROOT / PRIOR).read_bytes())
    assert {r["prior_case"] for r in rows if r["prior_case"]} == {r["case"] for r in prior["rows"]}
    corrected = next(r for r in rows if r["historical_case"] == "D13-barrier")
    assert corrected["case_id"] == "v3:B-native-D13-canonical-owner"
    assert corrected["historical_row"]["graph_hash"] != corrected["graph_hash"]
    assert (
        selection["historical_selection_sha256"]
        == hashlib.sha256((ROOT / HISTORY).read_bytes()).hexdigest()
    )


def test_profile_resource_and_schedule_are_distinct(frozen):
    rows = frozen["selection"]["rows"]
    assert Counter(r["expected_layer"] for r in rows) == {
        "result": 104,
        "profile": 4,
        "resource-preflight": 16,
    }
    assert frozen["selection"]["six_way_calls"] == 744
    assert frozen["selection"]["replay_calls"] == 624
    assert frozen["selection"]["total_planned_native_calls"] == 1368
    for r in rows:
        p = r["profile"]["entries"][0]
        assert p["mapping_policy"] == r["policy"]
        assert p["expected_outcome"] == (
            r["expected"]["outcome"] if r["expected_layer"] == "profile" else "success"
        )
        assert r["authority"] is None and r["public_raw_sha256"] is None


def test_all_inputs_are_explicit_model2(frozen):
    for payload in frozen["jobs"].values():
        job = payload["job"]
        assert job["engine"]["model"]["name"] == "native-intervals"
        assert job["engine"]["model"]["version"] == "2"
        assert job["profile"]["format"] == "uarch-native-test-profile/2"


def test_registry_covers_every_selected_variant(frozen):
    selection = frozen["selection"]
    declared = {r["hardware_spec_hash"] for r in selection["registry"]["test_only_specs"]}
    wanted = {p["job"]["hardware_spec_hash"] for p in frozen["jobs"].values()}
    assert wanted - {PRODUCTION_HARDWARE} <= declared
    before = selection["registry_transition"]["before"]
    old = {r["hardware_spec_hash"]: r for r in before["test_only_specs"]}
    new = {r["hardware_spec_hash"]: r for r in selection["registry"]["test_only_specs"]}
    assert all(new[k] == v for k, v in old.items())
    assert len(new) == 13 and len(set(new) - set(old)) == 4


def test_old_registry_reproduces_real_python_admission_refusal(frozen):
    item = frozen["jobs"]["v3:cc0-v3"]["item"]
    before = frozen["selection"]["registry_transition"]["before"]
    with pytest.raises(ValueError, match="TestProfileMismatch: synthetic spec must be registered"):
        admit(
            item["bundle"],
            invocation="test",
            checkpoint="B",
            registry=before,
            profile=item["profile"],
            trusted_registry_hash=before["registry_hash"],
            trusted_profile_hash=item["profile"]["profile_hash"],
        )


def test_corrected_extra_inputs_reach_python_resource_admission(frozen):
    # Python admission only. Native reach must be independently established by A/B final runs.
    registry = frozen["selection"]["registry"]
    extra = [r for r in frozen["selection"]["rows"] if r["source_input"]]
    assert len(extra) == 13
    for row in extra:
        item = frozen["jobs"][row["case_id"]]["item"]
        admit(
            item["bundle"],
            invocation="test",
            checkpoint="B",
            registry=registry,
            profile=item["profile"],
            trusted_registry_hash=registry["registry_hash"],
            trusted_profile_hash=item["profile"]["profile_hash"],
        )
