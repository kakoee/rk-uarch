"""Saved model-2 semantic and literal checks against the shipped checker."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result

from rkuarch.verification.component.checks import CheckFailure
from rkuarch.verification.component.observations_v3 import check_v3
from validation.component.native_inputs import policy_item, private_job
from validation.component.runtime_checks import assert_literals

ROOT = Path(__file__).resolve().parents[2]


def consume_case(job, result, row, *, expected):
    validate_result(result, MappedEngineJob.model_validate(job))
    check_v3(job, result, expected)
    assert_literals(job, result, row["expected"])


def inputs():
    base = ROOT / "contract/tests/mapped/fixtures/issue_capacity"
    raw = (base / "sr2-v3-job.json").read_bytes()
    job = json.loads(raw)
    result = json.loads((base / "sr2-v3-result.json").read_bytes())
    if True:
        # Explicit synthetic rebound of the inherited carrier, never new native output.
        item = policy_item(job["workload_closure"], {"outcome": "success"}, "v3:sr2-v3")
        rebound = private_job(item, job["registry"])
        rebound["engine"] = deepcopy(job["engine"])
        rebound["job_hash"] = content_hash(rebound, exclude=("job_hash",))
        job = rebound
        result["job_hash"], result["admission"] = job["job_hash"], deepcopy(job["admission"])
        result["result_hash"] = content_hash(result, exclude=("result_hash",))
    row = dict(
        case_id=job["admission"]["case_id"],
        profile=job["profile"],
        bundle_hash=job["bundle_hash"],
        point_hash=job["point_hash"],
        expected=json.loads(
            (
                ROOT / "docs/reviews/U4-B-component-runtime-preparation-v1/extra-literals.json"
            ).read_bytes()
        )["sr2-v3"],
    )
    expected = json.loads(
        (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
    )["observation_contract"]
    return job, result, row, {"expected": expected}



def test_A1b_structural_refusal_remains_behavioral():
    job, result, row, kwargs = inputs()
    bad = deepcopy(result)
    early, late = [
        o for o in bad["observations"]["reservation_opportunities"]["records"] if o["t_ps"] == 86000
    ]
    early["granted_request_ids"], late["granted_request_ids"] = ["r02.00"], []
    bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
    assert bad["job_hash"] == job["job_hash"]  # prospective profile2 derivative of A1b
    with pytest.raises(ValueError, match="reservation cursor capacity"):
        consume_case(job, bad, row, **kwargs)


def test_literal_expectation_is_not_retuned_by_result():
    job, result, row, kwargs = inputs()
    row["expected"]["duration_ps"] += 1
    with pytest.raises(CheckFailure, match="literal duration_ps"):
        consume_case(job, result, row, **kwargs)


def test_unknown_literal_is_not_silently_ignored():
    job, result, row, kwargs = inputs()
    row["expected"]["duration_sp"] = 1
    with pytest.raises(CheckFailure, match="unknown expectation keys"):
        consume_case(job, result, row, **kwargs)


def test_valid_saved_fixture_consumes():
    job, result, row, kwargs = inputs()
    consume_case(job, result, row, **kwargs)
