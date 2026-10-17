"""Real /2 carrier validators on synthetic controls, never generated native results."""

from copy import deepcopy

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import validate_result

from validation.component.consistent_carriers import control as current_control
from validation.component.synthetic_carrier import synthetic_job


def fixture_result(job):
    for case in ("D01", "D10-read"):
        if job.job_hash == synthetic_job(case).job_hash:
            return current_control(case)[1]
    raise AssertionError("not one of this finite synthetic worksheet's jobs")


FIXTURE = dict(
    synthetic_job=synthetic_job,
    synthetic_result=fixture_result,
    synthetic_resident_result=lambda job: current_control("C02")[1],
    synthetic_port_pair=lambda job: current_control("D08")[1],
)


def control():
    j = FIXTURE["synthetic_job"]()
    return j, FIXTURE["synthetic_result"](j)


def seal(r):
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


def test_real_synthetic_control():
    j, r = control()
    assert validate_result(r, j).duration_ps == 60000


@pytest.mark.parametrize("queue", ["channel_service:6", "dma_inflight:0", "ordinary"])
@pytest.mark.parametrize("fault", ["owner", "request", "population", "name", "clock"])
def test_queue_bindings_and_restoration(queue, fault):
    j, r = control()
    validate_result(r, j)
    bad = deepcopy(r)
    q = next(
        x
        for x in bad["observations"]["queue_membership"]["records"]
        if (
            x["queue_id"].startswith("activity:read_port:")
            if queue == "ordinary"
            else x["queue_id"] == queue
        )
    )
    if fault == "owner":
        q["owner_id"] = 31
    if fault == "request":
        q["item_id"] = "forged-request"
    if fault == "population":
        q["population"] = "inflight" if q["population"] != "inflight" else "service"
    if fault == "name":
        q["queue_id"] += "-forged"
    if fault == "clock":
        q["clock_domain"] = "dram" if q["clock_domain"] is None else None
    with pytest.raises(ValueError, match="IncompleteObservations"):
        validate_result(seal(bad), j)
    validate_result(r, j)


@pytest.mark.parametrize(
    "fault",
    [
        "request",
        "owner",
        "population_busy",
        "wrong_category",
        "loose_cause",
        "clock_phase",
        "forged_ratio",
        "dispatch",
    ],
)
def test_phase_binding_and_restoration(fault):
    j, r = control()
    bad = deepcopy(r)
    obs = bad["observations"]
    a = next(x for x in obs["activities"]["records"] if x["activity_id"] == "back-a")
    if fault == "request":
        a["request_id"] = "forged"
    if fault == "owner":
        a["owner_id"] = 31
    if fault == "population_busy":
        a["occupies_resource"] = True
    if fault == "wrong_category":
        a["category"] = "memory"
    if fault == "loose_cause":
        a["predecessors"] = [dict(activity_id="lat", relation="sequence")]
    if fault == "clock_phase":
        obs["clocks"]["records"][-1]["activity_id"] = "out"
    if fault == "forged_ratio":
        obs["resource_intervals"]["records"][1]["service_end_ps_ratio"]["numerator"] += 71
    if fault == "dispatch":
        a["dispatch_ordinal"] = 0
    with pytest.raises(ValueError):
        validate_result(seal(bad), j)
    validate_result(r, j)


def test_independent_mechanisms_on_real_synthetic_carrier():
    from validation.component.observations_v2 import check_v2

    j, r = control()
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, dict(unrepresented=["SYNTHETIC-unit-carrier-only"]))


@pytest.mark.parametrize(
    "fault",
    [
        "channel_duration",
        "drop_clock",
        "transfer_control_bytes",
        "inflight_end",
        "allocation_owner",
        "clock_cycles",
    ],
)
def test_independent_mechanism_discrimination(fault):
    from validation.component.checks import CheckFailure
    from validation.component.observations_v2 import check_v2

    j, r = control()
    bad = deepcopy(r)
    obs = bad["observations"]
    if fault == "channel_duration":
        res = next(
            x for x in obs["resource_intervals"]["records"] if x["activity"] == "channel_service"
        )
        res["service_end_ps_ratio"] = dict(numerator=54250, denominator=1)
    if fault == "drop_clock":
        obs["clocks"]["records"].pop()
    if fault == "transfer_control_bytes":
        obs["transfers"]["records"][0]["payload_bytes"] = 256
    if fault == "inflight_end":
        obs["queue_membership"]["records"][-1]["leave_ps"] = 54250
    if fault == "allocation_owner":
        obs["allocations"]["records"][0]["owner_id"] += 1
    if fault == "clock_cycles":
        obs["clocks"]["records"][-1]["n_cycles"] = 2
    with pytest.raises(CheckFailure):
        check_v2(
            j.model_dump(mode="json"), bad, dict(unrepresented=["SYNTHETIC-unit-carrier-only"])
        )
    check_v2(j.model_dump(mode="json"), r, dict(unrepresented=["SYNTHETIC-unit-carrier-only"]))


def test_resident_real_carrier_and_independent_mechanisms():
    from validation.component.observations_v2 import check_v2

    j = FIXTURE["synthetic_job"]("C02")
    r = FIXTURE["synthetic_resident_result"](j)
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, dict(unrepresented=["SYNTHETIC-unit-carrier-only"]))


def test_unequal_clock_real_carrier_and_independent_mechanisms():
    from validation.component.observations_v2 import check_v2

    j = FIXTURE["synthetic_job"]("D10-read")
    r = FIXTURE["synthetic_result"](j)
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, dict(unrepresented=["SYNTHETIC-unit-carrier-only"]))


def test_port_contention_overlap_real_carrier_and_independent_mechanisms():
    from validation.component.observations_v2 import check_v2

    j = FIXTURE["synthetic_job"]("D08")
    r = FIXTURE["synthetic_port_pair"](j)
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, dict(unrepresented=["SYNTHETIC-unit-carrier-only"]))
