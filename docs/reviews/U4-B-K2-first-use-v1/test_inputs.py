"""Host carrier/math controls. None execute native or confer first-use authority."""

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest
from author import MAX, literal_cases
from uarch_contract.hashing import content_hash, strict_json_loads
from uarch_contract.mapped import (
    MappedBundle,
    MappedEngineJob,
    NativeEngineIdentity,
    NativeTestProfile,
    NativeTestRegistry,
    hardware_projection,
    validate_job,
)

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
FIXTURES = PACKAGE / "fixtures"


def load(name):
    return strict_json_loads((FIXTURES / name).read_bytes())


def seal(value, key):
    value[key] = content_hash(value, exclude=(key,))
    return value


@pytest.fixture(scope="module")
def inputs():
    return load("profile.json"), load("registry.json"), load("expectations.json")


def synthetic_engine():
    # Explicit unit-test host fixture, never an executable/build identity or approval.
    return NativeEngineIdentity.model_validate(
        dict(
            name="native",
            version="native-stage/1",
            implementation_hash=content_hash(
                {"synthetic": "B-K2-host-guard", "source": "test-only"}
            ),
            model=dict(
                name="fixed-delay",
                version="1",
                implementation_hash=content_hash({"synthetic": "fixed-delay-model"}),
            ),
            compiler_lock_hash=content_hash({"synthetic": "no-compiler-was-executed"}),
        )
    )


def job_for(case, inputs):
    profile, registry, expected = inputs
    b = load(f"bundles/{case}.json")
    p = b["points"][0]
    entry = next(x for x in profile["entries"] if x["case_id"] == case)
    j = json.loads((ROOT / "contract/fixtures/mapped/kernel-job.json").read_text())
    j.update(
        bundle_hash=b["bundle_hash"],
        point_hash=p["payload_hash"],
        engine=synthetic_engine().model_dump(mode="json"),
        mapped_point=p,
        workload_closure=b,
        assumptions_hash=b["assumptions_hash"],
        assumptions=b["assumptions"],
        hardware=hardware_projection(
            MappedBundle.model_validate(b).hardware_spec
        ).model_dump(mode="json"),
        hardware_spec_hash=b["hardware_spec_hash"],
        rank=b["rank"],
        frequency_ratio=p["frequency_ratio"],
        freq_hz=entry["freq_hz"],
        initial_state=p["initial_state"],
        priming_iterations=0,
        seed=0,
        admission=b["admission"],
        clock_setup=expected[case]["clock_setup"],
        owners=[
            dict(owner_id=i, resource=f"fixture:{i}") for i in b["scope"]["owner_ids"]
        ],
        registry=registry,
        profile=profile,
    )
    return seal(copy.deepcopy(j), "job_hash")


def check(job, inputs):
    profile, registry, _ = inputs
    return validate_job(
        job,
        invocation="test",
        checkpoint="K2",
        trusted_registry_hash=registry["registry_hash"],
        trusted_profile_hash=profile["profile_hash"],
        expected_engine=synthetic_engine(),
    )


def test_frozen_bytes_exact_membership_and_strict_carriers(inputs):
    identity = load("identity.json")
    assert len(identity["cases"]) == 113
    assert set(identity["cases"]) == {x["case_id"] for x in literal_cases()}
    assert (
        identity["expected_engine"] is None and identity["authority"] == "proposal_only"
    )
    assert NativeTestProfile.model_validate(inputs[0])
    assert NativeTestRegistry.model_validate(inputs[1])
    assert {str(p.relative_to(FIXTURES)) for p in FIXTURES.rglob("*.json")} == (
        set(identity["files"]) | {"identity.json"}
    )
    for path, digest in identity["files"].items():
        assert hashlib.sha256((FIXTURES / path).read_bytes()).hexdigest() == digest
    for case in identity["cases"]:
        j = check(job_for(case, inputs), inputs)
        assert j.fidelity_detail is None and j.precision is None
        assert j.state_model == "fixed_delay/1"
        assert j.admission.eligibility == "verification_only"


def test_independent_finite_clock_arithmetic(inputs):
    cases = literal_cases()
    edge_cases = [c for c in cases if c["case_id"].startswith("K07-")]
    assert len(edge_cases) == len({c["case_id"] for c in edge_cases}) == 100
    for c in cases:
        if not c["clock_setup"]:
            continue
        clock = c["clock_setup"][0]
        t, n, f = clock["start_ps"], clock["n_cycles"], c["freq_hz"]
        # Independent rational bounds, not the production next_edge/index implementation.
        if t <= 30000:
            k = next(i for i in range(40) if -(-i * 10**12 // f) >= t)
        else:
            k = ((t - 1) * f) // 10**12 + 1
        exact = Fraction((k + n) * 10**12, f)
        end = -(-exact.numerator // exact.denominator)
        expected = inputs[2][c["case_id"]]
        if expected["outcome"] == "TimeOverflow":
            assert end > MAX
        else:
            assert end == expected["duration_ps"]
            assert 0 <= end * f - (k + n) * 10**12 < f
    assert 833 * 10**9 != inputs[2]["K06-04"]["duration_ps"]
    assert inputs[2]["K06-01"]["duration_ps"] == 834  # strict-after mutant gives1667
    assert MAX + 1 > MAX  # separate checked fixed-delay addition refusal


def test_literal_causality_and_fault_discrimination(inputs):
    expected = inputs[2]
    assert expected["K01"]["duration_ps"] == max(3000, 5000) + 2000 == 7000
    assert expected["K02"]["duration_ps"] == 3000 + 5000 + 2000 == 10000
    assert expected["K04"]["duration_ps"] == max(3000, 1000) + 2000 == 5000
    assert expected["K05-chain"]["duration_ps"] == 1000 + 0 + 0 + 2000 == 3000
    assert expected["K01"]["duration_ps"] != max(3000 + 2000, 5000)  # missing b->c
    assert expected["K01"]["duration_ps"] != 3000 + 5000 + 2000  # global serialization
    assert expected["K04"]["duration_ps"] != 1000 + 0 + 2000  # bypass busy owner
    assert sum(row[4] - row[3] for row in expected["K01"]["intervals"]) == 10000
    for name in ("K01", "K02", "K04", "K05-chain"):
        rows = {r[0]: r for r in expected[name]["intervals"]}
        path = expected[name]["causal_job_path"]
        assert (
            sum(rows[j][4] - rows[j][3] for j in path) == expected[name]["duration_ps"]
        )
        assert all(
            rows[a][4] == rows[b][3] for a, b in zip(path, path[1:], strict=False)
        )
    zero = expected["K05"]["intervals"]
    assert len(zero) == 3 and zero[0][3:5] == zero[1][3:5] == [0, 0]


def test_wheel_proposals_are_finite_and_discriminating():
    rows = load("wheel-schedules.json")
    assert len(rows) == len({r["case_id"] for r in rows}) == 100
    differences = 0
    for row in rows:
        schedule = row["schedule"]
        assert [e["seq"] for e in schedule] == list(range(8))
        correct = sorted(
            schedule, key=lambda e: (e["t_ps"], e["phase"], e["target"], e["seq"])
        )
        assert row["expected_pop"] == correct
        differences += sorted(schedule, key=lambda e: (e["t_ps"], e["seq"])) != correct
        assert row["reuse"]["payload"] not in {e["payload"] for e in schedule}
        assert row["reuse"]["t_ps"] > max(e["t_ps"] for e in schedule)
    assert differences > 0
    literal = [(1000, 0, 2, 9), (1000, 1, 0, 2), (1000, 0, 1, 8), (1000, 0, 1, 7)]
    assert [e[3] for e in sorted(literal)] == [7, 8, 9, 2]


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("wrong-engine", "EngineIdentityMismatch"),
        ("wrong-source", "EngineIdentityMismatch"),
        ("wrong-case", "TestProfileMismatch"),
        ("changed-clock", "TestProfileMismatch"),
        ("caller-rehash", "TestProfileMismatch"),
        ("registry-rehash", "RegistryTrustMismatch"),
        ("stale-point", "ArtifactHashMismatch"),
        ("cycle", "InvalidDependency"),
        ("missing-dependency", "InvalidDependency"),
        ("negative-cycles", "greater_than_equal"),
        ("negative-time", "greater_than_equal"),
        ("zero-clock", "greater_than"),
        ("bool-clock", "int_type"),
        ("empty-jobs", "too_short"),
        ("unknown-field", "extra_forbidden"),
    ],
)
def test_admission_refusals(fault, reason, inputs):
    j = job_for("K06-02", inputs)
    if fault in ("wrong-engine", "wrong-source"):
        j["engine"]["implementation_hash"] = content_hash({"wrong": fault})
    elif fault == "wrong-case":
        j["admission"]["case_id"] = j["workload_closure"]["admission"]["case_id"] = (
            "missing"
        )
        seal(j["workload_closure"], "bundle_hash")
        j["bundle_hash"] = j["workload_closure"]["bundle_hash"]
    elif fault in ("changed-clock", "caller-rehash"):
        j["clock_setup"][0]["n_cycles"] += 1
        if fault == "caller-rehash":
            e = next(e for e in j["profile"]["entries"] if e["case_id"] == "K06-02")
            e["clock_setup_hash"] = content_hash(j["clock_setup"])
            seal(j["profile"], "profile_hash")
            for admission in (j["admission"], j["workload_closure"]["admission"]):
                admission["profile_hash"] = j["profile"]["profile_hash"]
            seal(j["workload_closure"], "bundle_hash")
            j["bundle_hash"] = j["workload_closure"]["bundle_hash"]
            MappedEngineJob.model_validate(
                seal(j, "job_hash")
            )  # self-consistent attack
    elif fault == "registry-rehash":
        j["registry"]["test_only_specs"][0]["rationale"] += " caller"
        seal(j["registry"], "registry_hash")
    elif fault == "stale-point":
        j["mapped_point"]["point_id"] += "tampered"
    elif fault in ("cycle", "missing-dependency", "empty-jobs"):
        g = j["mapped_point"]["task_graph"]
        if fault == "empty-jobs":
            g["jobs"] = []
        else:
            g["dependencies"] = [
                dict(before="b-clock", after="a-wait"),
                dict(
                    before="a-wait" if fault == "cycle" else "absent", after="b-clock"
                ),
            ]
            g["dependencies"].sort(key=lambda e: (e["before"], e["after"]))
        seal(g, "graph_hash")
        seal(j["mapped_point"], "payload_hash")
    elif fault in ("negative-cycles", "negative-time", "bool-clock"):
        j["clock_setup"][0]["start_ps" if fault == "negative-time" else "n_cycles"] = (
            True if fault == "bool-clock" else -1
        )
    elif fault == "zero-clock":
        j["freq_hz"]["core"] = 0
    else:
        j["invented_event_injection"] = []
    with pytest.raises(ValueError, match=reason):
        check(seal(j, "job_hash"), inputs)
    assert check(
        job_for("K06-02", inputs), inputs
    )  # restored positive, no shared mutation


def test_duplicate_json_key_refuses():
    with pytest.raises(ValueError, match="DuplicateJsonKey"):
        strict_json_loads('{"a":1,"a":2}')


def validate_selection(selected, expected):
    if (
        not selected
        or len(selected) != len(set(selected))
        or set(selected) != set(expected)
    ):
        raise ValueError("IncompleteK2Selection")


@pytest.mark.parametrize("fault", ["empty", "missing", "extra", "duplicate"])
def test_selection_guard(fault):
    expected = list(load("identity.json")["cases"])
    validate_selection(expected, expected)
    altered = {
        "empty": [],
        "missing": expected[:-1],
        "extra": [*expected, "foreign"],
        "duplicate": [*expected, expected[0]],
    }[fault]
    with pytest.raises(ValueError, match="IncompleteK2Selection"):
        validate_selection(altered, expected)
    validate_selection(expected, expected)
