"""Pending public first-use obligations; collect only during construction.

Execution requires the separately accepted system HostSelector. No synthetic anchor
or construction-test record can supply that final human authority. B expectations
are independently authored and remain unmodified.
"""

import importlib.util
import json
from pathlib import Path

import pytest
from uarch_contract.mapped import MappedEngineJob

from rkuarch.engines.native.host import resolve_host
from rkuarch.engines.native.runner import NativeRefusal, run_fixed_delay

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus"
CORPUS = json.loads((PACKAGE / "inventory.json").read_bytes())
EXPECTED = json.loads((PACKAGE / "expectations.json").read_bytes())
_spec = importlib.util.spec_from_file_location(
    "independent_B_result_checks",
    ROOT / "docs/reviews/U4-B-K2-construction-audit-v1/first_use_checks.py",
)
assert _spec and _spec.loader
_peer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_peer)
pytestmark = pytest.mark.native


@pytest.fixture(scope="module", params=["debug", "release"])
def host(request):
    try:
        return resolve_host(mode=request.param)
    except FileNotFoundError:
        pytest.skip("exact final human host selector is not installed")


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda c: c["case_id"])
def test_public_fixed_delay_case(host, case):
    inventory = json.loads((host.root / host.record.jobs_inventory.path).read_bytes())
    matches = []
    for item in inventory["jobs"]:
        path = host.root / item["file"]["path"]
        raw = json.loads(path.read_bytes())
        if raw["admission"]["case_id"] == case["case_id"]:
            matches.append((path, raw))
    assert len(matches) == 1, "exact human inventory must contain this case once"
    path, raw = matches[0]
    if case["execution_outcome"] == "TimeOverflow":
        with pytest.raises(NativeRefusal) as failed:
            run_fixed_delay(path, host=host)
        assert failed.value.envelope["code"] == "TimeOverflow"
        return
    result, receipt = run_fixed_delay(path, host=host)
    assert receipt["exit_code"] == 0
    _peer.check_real_result(result, MappedEngineJob.model_validate(raw), EXPECTED[case["case_id"]])
    for clock in result.observations.clocks.records:
        if clock.n_cycles == 0:
            assert clock.completion_ps == clock.grant_ps
    if case["case_id"] == "K06-02":
        clock = result.observations.clocks.records[0]
        assert (clock.aligned_start_ps, clock.completion_ps) == (1667, 835)
