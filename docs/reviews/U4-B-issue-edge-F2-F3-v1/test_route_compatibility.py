"""New restriction coupling to the accepted F4 route; no native replay."""

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("f2_policy_route", HERE / "restriction.py")
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def test_actual_model2_classification_keeps_accepted_f4_route():
    # Accepted /3 fixture is reused, not rerun or repaired. New policy is orthogonal
    # to the existing model/format/checker route and does not mint execution trust.
    old = HERE.parent / "U4-B-issue-edge-stage2-v1"
    raw_job = (old / "private-probes/cc0-v3/job.json").read_bytes()
    r = policy.classify(raw_job)
    assert r["status"] == "outside_F2_model2" and not r["execution_authorized"]
    spec = importlib.util.spec_from_file_location("unchanged_f4", old / "first_use.py")
    route = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(route)
    job = json.loads(raw_job)
    result = json.loads((old / "private-probes/cc0-v3/result.json").read_text())["result"]
    route.required_route(job, result, "validation.component.observations_v3:check_v3")
    with pytest.raises(
        ValueError, match="model / observation format / independent checker mismatch"
    ):
        route.required_route(job, result, "validation.component.observations_v2:check_v2")
