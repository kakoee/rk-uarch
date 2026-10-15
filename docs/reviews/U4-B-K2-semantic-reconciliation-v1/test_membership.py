"""Check the prospective delta against immutable historical bytes, in memory only."""

import copy
import hashlib
import json
from pathlib import Path

from literals import CASES

PACKAGE = Path(__file__).resolve().parent


def read(name):
    return json.loads((PACKAGE / name).read_bytes())


def test_all_original_members_and_witnesses_accounted_for(pytestconfig):
    root = Path(pytestconfig.rootpath)
    old = json.loads(
        (root / "docs/reviews/U4-B-K2-first-use-v1/fixtures/identity.json").read_bytes()
    )
    ledger = read("membership.json")
    assert len(old["cases"]) == 113
    assert set(ledger["historical_cases"]) == set(old["cases"])
    assert sum(k.startswith("K07-") for k in ledger["historical_cases"]) == 100
    assert ledger["private_wheel_schedules"]["count"] == 100
    assert ledger["additional_independent_witnesses"] == list(CASES)
    assert len(CASES) == 17
    for field in (
        "selected_profile_hash",
        "selected_registry_hash",
        "engine_identity",
        "human_authority",
    ):
        assert ledger[field] is None


def test_exact_guarded_delta_only_changes_owned_projection(pytestconfig):
    delta = read("candidate-delta.json")
    source = Path(pytestconfig.rootpath) / delta["input"]
    before = source.read_bytes()
    assert hashlib.sha256(before).hexdigest() == delta["input_sha256"]
    original = json.loads(before)
    changed = copy.deepcopy(original)
    for op in delta["operations"]:
        keys = op["path"].strip("/").split("/")
        target = changed
        for key in keys[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        key = int(keys[-1]) if isinstance(target, list) else keys[-1]
        if op["op"] == "test":
            assert target[key] == op["value"]
        else:
            assert op["op"] == "replace"
            target[key] = op["value"]
    assert changed["K06-02"] == read("membership.json")["prospective_owned_obligation"]["after"]
    assert {k for k in changed if changed[k] != original[k]} == {"K06-02"}
    assert original["K06-02"]["duration_ps"] == 1667
    assert changed["K06-02"]["duration_ps"] == 835
    assert source.read_bytes() == before
    assert delta["install_operations"] == delta["profile_registry_operations"] == []
