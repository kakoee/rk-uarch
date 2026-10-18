"""Prospective /3 preparation tests; synthetic jobs confer no authority."""

import hashlib
import json
from collections import Counter

import pytest

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
