"""Actual inherited c67 job/result versus cc899 inventory. Identity discrimination only."""

import hashlib
import json
import sys
from pathlib import Path

from validation.component import runtime_checks

root = Path(sys.argv[1])
pkg = Path(sys.argv[2])
new = Path("/tmp/u4-a-runtime-build-cc899d2/source/private-component")
old = Path("/tmp/u4-a-runtime-build-c67d558")
case = "v3:cc0-v3"
old_raw = (old / "source/private-component/jobs" / (case + ".json")).read_bytes()
old_result = (old / "outputs/debug/selected" / (case + ".json")).read_bytes()
new_raw = (new / "jobs" / (case + ".json")).read_bytes()
job, result, current = json.loads(old_raw), json.loads(old_result), json.loads(new_raw)
row = next(
    r for r in json.loads((new / "selection.json").read_bytes())["rows"] if r["case_id"] == case
)
assert {k: v for k, v in job.items() if k not in {"engine", "job_hash"}} == {
    k: v for k, v in current.items() if k not in {"engine", "job_hash"}
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


kwargs = dict(
    checker_id=runtime_checks.CHECKER,
    source=root,
    pins=json.loads((pkg / "prospective-consumer-bindings-v1.json").read_bytes())["files"],
    expected=json.loads((new / "observation-contract.json").read_bytes()),
    input_sha256=digest(old_raw),
    raw_input=old_raw,
    admitted=dict(
        case_id=case,
        raw_input_sha256=digest(new_raw),
        job_hash=current["job_hash"],
        engine=current["engine"],
    ),
)
report = dict(
    case_id=case,
    old_input_sha256=digest(old_raw),
    old_result_sha256=digest(old_result),
    admitted_input_sha256=digest(new_raw),
    old_engine=job["engine"],
    admitted_engine=current["engine"],
    native_execution="inherited A c67d558; no new native run",
    discrimination="consumer identity, not a behavioral checker kill",
)


def refused():
    try:
        runtime_checks.consume_case(job, result, row, **kwargs)
    except ValueError as error:
        assert str(error) == "separately frozen admitted input/engine"
        return str(error)
    raise AssertionError("stale identity accepted")


report["refusal"] = refused()
guard = runtime_checks.need
try:
    runtime_checks.need = lambda ok, why: (
        None if why == "separately frozen admitted input/engine" else guard(ok, why)
    )
    runtime_checks.consume_case(job, result, row, **kwargs)
    report["disconnected_inventory_guard_accepts_old_pair"] = True
finally:
    runtime_checks.need = guard
report["restored_refusal"] = refused()
print(json.dumps(report, indent=2))
