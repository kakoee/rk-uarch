"""Independent host-only corpus/admission controls; no public mapped execution."""

import copy
import json
import os
from pathlib import Path

import pytest
from first_use_checks import exact_selection, fixture_job, synthetic_engine
from uarch_contract.hashing import canonical_json, content_hash

from rkuarch.workload.mapped import loads_fixed_delay_job

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(os.environ["B_K2_FIXTURES"])
MANIFEST = json.loads((FIXTURES / "candidate.json").read_bytes())
ANSWERS = json.loads((FIXTURES / "expectations.json").read_bytes())
ENGINE = synthetic_engine()
AUTH = dict(
    trusted_profile_hash=MANIFEST["profile_hash"],
    trusted_registry_hash=MANIFEST["registry_hash"],
    expected_engine=ENGINE,
)


def job(case="K06-02"):
    return fixture_job(ROOT, FIXTURES, case, ENGINE)


def seal(raw, field="job_hash"):
    raw[field] = content_hash(raw, exclude=(field,))
    return raw


@pytest.mark.parametrize("case", sorted(MANIFEST["cases"]))
def test_exact_corpus_admission_and_operational_caps(case):
    raw = job(case)
    loaded = loads_fixed_delay_job(canonical_json(raw), **AUTH)
    assert canonical_json(loaded) == canonical_json(raw)
    assert loaded.fidelity_detail is None and loaded.precision is None
    graph = raw["mapped_point"]["task_graph"]
    n, d, c = len(graph["jobs"]), len(graph["dependencies"]), len(raw["clock_setup"])
    assert n and n <= 100000 and len(raw["owners"]) <= 100000
    assert 3 * n + d + c <= 1000000 and 9 * n + d + c <= 2000000
    assert len(canonical_json(raw).encode()) < 64 * 1024 * 1024
    if ANSWERS[case]["outcome"] == "success":
        assert len(ANSWERS[case]["queue_rows"]) == 2 * n
        assert all(row[-1] is None for row in ANSWERS[case]["queue_rows"])


def test_membership_and_literal_boundaries():
    assert len(MANIFEST["original_ids"]) == 113
    assert len(MANIFEST["added_ids"]) == 20
    assert sum(x.startswith("K07-") for x in ANSWERS) == 100
    assert sum(x.startswith("S") for x in ANSWERS) == 17
    assert sum(a["outcome"] == "TimeOverflow" for a in ANSWERS.values()) == 3
    assert ANSWERS["K06-02"]["duration_ps"] == 835
    assert ANSWERS["K06-02"]["raw_clock_edge_ps"] == 1667
    assert MANIFEST["original_K06_02"]["duration_ps"] == 1667
    assert ANSWERS["K05-chain"]["chosen_predecessors"] == dict(a=None, b="a", c="a", d="b")
    assert ANSWERS["ZMAX-raw-overflow-owned-zero"]["duration_ps"] == 2**64 - 1
    assert ANSWERS["ZMAX-positive-overflow"]["outcome"] == "TimeOverflow"
    assert MANIFEST["expected_engine"] is None and MANIFEST["human_host_record"] is None


@pytest.mark.parametrize("actual", [[], ["a"], ["a", "b", "c"], ["a", "b", "b"], ["b", "a"]])
def test_selection_refuses(actual):
    with pytest.raises(ValueError, match="exact ordered"):
        exact_selection(["a", "b"], actual)
    exact_selection(["a", "b"], ["a", "b"])


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("clock", "TestProfileMismatch"),
        ("case", "TestProfileMismatch"),
        ("source", "EngineIdentityMismatch"),
        ("model", "EngineIdentityMismatch"),
        ("registry", "RegistryTrustMismatch"),
        ("full-rehash", "TestProfileMismatch"),
    ],
)
def test_rehashed_caller_cannot_choose_authority(fault, reason):
    raw = job()
    if fault == "clock":
        raw["clock_setup"][0]["n_cycles"] += 1
    elif fault == "case":
        raw["admission"]["case_id"] = "foreign"
        raw["workload_closure"]["admission"]["case_id"] = "foreign"
        seal(raw["workload_closure"], "bundle_hash")
        raw["bundle_hash"] = raw["workload_closure"]["bundle_hash"]
    elif fault == "source":
        raw["engine"]["implementation_hash"] = content_hash({"foreign": "source"})
    elif fault == "model":
        raw["engine"]["model"]["implementation_hash"] = content_hash({"foreign": "model"})
    elif fault == "registry":
        raw["registry"]["test_only_specs"][0]["rationale"] += " changed"
        seal(raw["registry"], "registry_hash")
    else:
        raw["clock_setup"][0]["n_cycles"] = 1
        entry = next(e for e in raw["profile"]["entries"] if e["case_id"] == "K06-02")
        entry["clock_setup_hash"] = content_hash(raw["clock_setup"])
        seal(raw["profile"], "profile_hash")
        raw["admission"]["profile_hash"] = raw["profile"]["profile_hash"]
        raw["workload_closure"]["admission"] = copy.deepcopy(raw["admission"])
        seal(raw["workload_closure"], "bundle_hash")
        raw["bundle_hash"] = raw["workload_closure"]["bundle_hash"]
        seal(raw)
        # Positive internal consistency with explicitly synthetic attacker anchor.
        assert loads_fixed_delay_job(
            canonical_json(raw), **dict(AUTH, trusted_profile_hash=raw["profile"]["profile_hash"])
        )
    with pytest.raises(ValueError, match=reason):
        loads_fixed_delay_job(canonical_json(seal(raw)), **AUTH)
    assert loads_fixed_delay_job(canonical_json(job()), **AUTH)
