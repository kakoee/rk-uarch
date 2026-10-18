"""Synthetic saved-output controls; no new native result or execution authority."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash

from validation.component.checks import CheckFailure
from validation.component.native_inputs import policy_item, private_job
from validation.component.runtime_checks import CHECKER, consume_case

ROOT = Path(__file__).resolve().parents[2]


def inputs(profile2=True):
    base = ROOT / "contract/tests/mapped/fixtures/issue_capacity"
    raw = (base / "sr2-v3-job.json").read_bytes()
    job = json.loads(raw)
    result = json.loads((base / "sr2-v3-result.json").read_bytes())
    if profile2:
        # Explicit synthetic rebound of the inherited carrier, never new native output.
        item = policy_item(job["workload_closure"], {"outcome": "success"}, "v3:sr2-v3")
        rebound = private_job(item, job["registry"])
        rebound["engine"] = deepcopy(job["engine"])
        rebound["job_hash"] = content_hash(rebound, exclude=("job_hash",))
        job = rebound
        raw = canonical_json(job).encode()
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
    pins = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in (
            "contract/uarch_contract",
            "validation/component",
            "src/rkuarch/engines/native",
        )
        for p in (ROOT / folder).glob("*.py")
        if not p.name.startswith("test_")
    }
    expected = json.loads(
        (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
    )["observation_contract"]
    return (
        job,
        result,
        row,
        dict(
            checker_id=CHECKER,
            source=ROOT,
            pins=pins,
            expected=expected,
            input_sha256=hashlib.sha256(raw).hexdigest(),
            raw_input=raw,
            admitted=dict(
                case_id=row["case_id"],
                raw_input_sha256=hashlib.sha256(raw).hexdigest(),
                job_hash=job["job_hash"],
                engine=deepcopy(job["engine"]),
            ),
        ),
    )


def test_valid_saved_fixture_consumes_with_explicit_bindings():
    job, result, row, kwargs = inputs()
    consume_case(job, result, row, **kwargs)


def test_wrong_checker_refuses_before_consumption():
    job, result, row, kwargs = inputs()
    kwargs["checker_id"] = "validation.component.observations_v2:check_v2"
    with pytest.raises(CheckFailure, match="model/format/checker route"):
        consume_case(job, result, row, **kwargs)


@pytest.mark.parametrize(
    "attack", ["stale", "missing", "missing-transitive", "wrong-input", "wrong-definition"]
)
def test_binding_failure_is_identity_only(attack):
    job, result, row, kwargs = inputs()
    if attack == "stale":
        kwargs["pins"]["validation/component/issue_checks.py"] = "0" * 64
        message = "consumer source mismatch"
    elif attack == "missing":
        kwargs["pins"].pop("contract/uarch_contract/mapped_issue.py")
        message = "complete matching"
    elif attack == "missing-transitive":
        kwargs["pins"].pop("validation/component/arithmetic.py")
        message = "complete matching"
    elif attack == "wrong-input":
        kwargs["raw_input"] += b" "
        message = "exact selected input"
    else:
        row["point_hash"] = "sha256:" + "0" * 64
        message = "selected definition"
    with pytest.raises(CheckFailure, match=message):
        consume_case(job, result, row, **kwargs)


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


def test_profile1_cannot_silently_enter_prospective_profile2_route():
    job, result, row, kwargs = inputs(profile2=False)
    with pytest.raises(CheckFailure, match="prospective profile/2 required"):
        consume_case(job, result, row, **kwargs)


@pytest.mark.parametrize("attack", ["stale-engine-pair", "caller-rehash"])
def test_separately_frozen_input_refuses_consistent_foreign_pair(attack):
    job, result, row, kwargs = inputs()
    if attack == "stale-engine-pair":
        job["engine"]["implementation_hash"] = "sha256:" + "1" * 64
        result["engine"] = deepcopy(job["engine"])
    else:
        pass  # Foreign exact input bytes with the same parsed carrier.
    job["job_hash"] = content_hash(job, exclude=("job_hash",))
    result["job_hash"] = job["job_hash"]
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    kwargs["raw_input"] = canonical_json(job).encode()
    if attack == "caller-rehash":
        kwargs["raw_input"] += b" "
    kwargs["input_sha256"] = hashlib.sha256(kwargs["raw_input"]).hexdigest()
    with pytest.raises(CheckFailure, match="separately frozen admitted"):
        consume_case(job, result, row, **kwargs)


def test_unknown_literal_is_not_silently_ignored():
    job, result, row, kwargs = inputs()
    row["expected"]["duration_sp"] = 1
    with pytest.raises(CheckFailure, match="unknown expectation keys"):
        consume_case(job, result, row, **kwargs)


def test_unjoined_legacy_caller_fails_closed_without_inventory():
    job, result, row, kwargs = inputs()
    kwargs.pop("admitted")
    with pytest.raises(CheckFailure, match="admitted inventory required"):
        consume_case(job, result, row, **kwargs)
