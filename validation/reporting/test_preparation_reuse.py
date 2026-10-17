"""Preparation reuse is private to one validation; changed inputs and outputs revalidate."""

from copy import deepcopy

import pytest
from uarch_contract.hashing import canonical_json

from validation.reporting import analytic_report as report
from validation.strategies import fixed_bundle


def test_preparation_reuse_returns_isolated_equal_jobs_and_rejects_drift(monkeypatch):
    bundle = fixed_bundle("aggregate")
    original = report.jobs
    calls = []

    def observed(value):
        calls.append(value.bundle_hash)
        return original(value)

    monkeypatch.setattr(report, "jobs", observed)
    preparation = report._ValidationPreparation()
    first = preparation.jobs(bundle)
    baseline = canonical_json([report.as_json(job) for job in first])
    # Frozen models contain mutable dictionaries. A consumer cannot poison later cases.
    first[0].point.graph.groups[0].ops[0].spec.dimensions["sentinel"] = 123
    again = preparation.jobs(bundle)
    assert canonical_json([report.as_json(job) for job in again]) == baseline
    assert calls == [bundle.bundle_hash]
    changed = deepcopy(bundle)
    changed.points[0].graph.groups[0].ops[0].spec.dimensions["sentinel"] = 456
    with pytest.raises(ValueError):
        preparation.jobs(changed)  # Same claimed bundle hash does not authorize changed bytes.
    assert len(calls) == 2
    assert canonical_json([report.as_json(j) for j in preparation.jobs(bundle)]) == baseline
    report._ValidationPreparation().jobs(bundle)
    assert len(calls) == 3  # New public validation gets a new preparation scope.


def test_current_assumptions_and_engine_are_part_of_preparation_key(monkeypatch):
    from validation import strategies

    bundle = fixed_bundle("aggregate")
    preparation = report._ValidationPreparation()
    expected = preparation.jobs(bundle)
    wrong = report.physical_assumptions().model_copy(
        update={"assumptions_hash": "sha256:" + "0" * 64}
    )
    with monkeypatch.context() as patch:
        patch.setattr(report, "physical_assumptions", lambda: wrong)
        patch.setattr(strategies, "physical_assumptions", lambda: wrong)
        with pytest.raises(ValueError):
            preparation.jobs(bundle)
    engine = report.core.engine_identity().model_copy(
        update={"implementation_hash": "sha256:" + "1" * 64}
    )
    with monkeypatch.context() as patch:
        patch.setattr(report.core, "engine_identity", lambda: engine)
        changed = preparation.jobs(bundle)
        assert changed[0].engine == engine and changed != expected
    assert preparation.jobs(bundle) == expected


def test_job_order_and_mandatory_repeats_are_identical():
    preparation = report._ValidationPreparation()
    plan = report.profile("analytic-l0-smoke")
    checked = 0
    for cell in plan["cells"]:
        if report.disposition(cell):
            continue
        bundle = fixed_bundle(cell["modes"][0])
        expected = report.expected_jobs(cell, [bundle])
        actual = report.expected_jobs(cell, [bundle], preparation=preparation)
        assert actual == expected
        checked += 1
        if report.relation_name(cell) in ("analytic.repeat_bytes", "analytic.saved_replay"):
            assert len(actual) == 4
            assert actual[0] == actual[1] and actual[2] == actual[3]
    assert checked == 14
