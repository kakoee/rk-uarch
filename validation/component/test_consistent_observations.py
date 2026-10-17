"""Independent behavior tests; identity-only tests are excluded from mutation scores."""

import pytest
from uarch_contract.mapped import validate_result

from validation.component.checks import CheckFailure
from validation.component.consistent_carriers import EXPECTED, attack, control
from validation.component.observations_v2 import check_v2


@pytest.mark.parametrize("case", ["D01", "D10-read", "D08", "C02"])
def test_positive_controls(case):
    j, r = control(case)
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, EXPECTED)


@pytest.mark.parametrize(
    "name,detail",
    [
        ("M1", "activity category/domain"),
        ("M2", "activity owner"),
        ("M3", "complete eligible causes"),
        ("V1", "complete eligible causes"),
        ("V2", "complete eligible causes"),
        ("M4a", "required occupancy"),
        ("M4b", "channel integer mechanism"),
        ("port_overlap", "exclusive mechanism intervals"),
        ("port_reverse", "port FIFO tie"),
    ],
)
def test_consistent_checker_forgery(name, detail):
    j, r = attack(name)
    with pytest.raises(CheckFailure, match=detail):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)


@pytest.mark.parametrize("case,ends", [("D05-two", [60000, 62000]), ("D05-one", [60000, 120000])])
def test_channel_and_credit_controls(case, ends):
    from validation.component.consistent_carriers import pair_control

    j, r = pair_control(case)
    assert [x["complete_ps"] for x in r["observations"]["dma"]["records"]] == ends
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, EXPECTED)


@pytest.mark.parametrize(
    "name,detail",
    [
        ("duration", "mechanism duration"),
        ("carry", "rational channel carry/readiness"),
        ("rational", "channel mechanism"),
        ("busy", "busy union"),
        ("null_floor", "fidelity/null floor"),
        ("fidelity", "fidelity/null floor"),
        ("diagnostic", "unmodeled diagnostics"),
        ("unrepresented", "unrepresented paths"),
        ("critical", "unrepresented critical predecessor"),
        ("job_owner", "job owner binding"),
        ("release", "job release binding"),
        ("blockers", "unrepresented job blockers"),
        ("event", "event transition binding"),
        ("queue_clock", "nonclocked exact binding"),
        ("queue_owner", "nonclocked exact binding"),
        ("queue_engine", "nonclocked exact binding"),
        ("queue_population", "nonclocked exact binding"),
    ],
)
def test_mechanism_and_field_forgery(name, detail):
    from validation.component.consistent_carriers import mechanism_attack

    j, r = mechanism_attack(name)
    with pytest.raises(CheckFailure, match=detail):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)


@pytest.mark.parametrize(
    "name,detail",
    [
        ("channel_fifo", "channel FIFO tie"),
        ("readiness", "service readiness after alignment"),
        ("critical_partition", "mechanism causal partition"),
        ("allocation_lifetime", "allocation access lifetime"),
        ("channel_population", "channel population lifecycle"),
        ("ordinary_population", "ordinary queue exact binding"),
    ],
)
def test_transition_and_population_forgery(name, detail):
    from validation.component.consistent_carriers import extra_attack

    j, r = extra_attack(name)
    with pytest.raises(CheckFailure, match=detail):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)


def test_zero_hop_dependency_control():
    from validation.component.consistent_carriers import activity, seal, zero_hop_control

    j, r = zero_hop_control()
    assert r["duration_ps"] == 61000
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, EXPECTED)
    activity(r, "zero")["predecessors"] = []
    with pytest.raises(CheckFailure, match="complete eligible causes"):
        check_v2(j.model_dump(mode="json"), seal(r), EXPECTED)


def test_credit_requires_exhaustion_at_first_transition():
    from validation.component.consistent_carriers import pair_control, seal
    from validation.component.synthetic_carrier import synthetic_job

    j = synthetic_job("D05-two")
    _, r = pair_control("D05-one")
    # Same request inventory, but cap=2; only one prior request occupies a credit.
    r["job_hash"] = j.job_hash
    r["admission"] = j.admission.model_dump(mode="json")
    r = seal(r)
    validate_result(r, j)  # Structural first/last eligibility alone intentionally admits.
    with pytest.raises(CheckFailure, match="complete eligible causes"):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)


def test_causal_attribution_totals():
    from validation.component.consistent_carriers import seal

    j, r = control()
    r["attribution_ps"]["noc"] += 1
    r["attribution_ps"]["memory"] -= 1
    with pytest.raises(CheckFailure, match="causal attribution totals"):
        check_v2(j.model_dump(mode="json"), seal(r), EXPECTED)


def test_unicast_request_inventory_and_ownership():
    from validation.component.consistent_carriers import seal, zero_hop_control

    j, r = zero_hop_control()
    r["observations"]["dma"]["records"][-1]["source_buffer_id"] = "sd"
    with pytest.raises(CheckFailure, match="unicast request binding"):
        check_v2(j.model_dump(mode="json"), seal(r), EXPECTED)


def test_barrier_complete_terminal_dependencies():
    from validation.component.consistent_carriers import activity, barrier_control, seal

    j, r = barrier_control()
    assert r["duration_ps"] == 94000
    assert activity(r, "barrier-a")["predecessors"] == [
        dict(activity_id="r1:port", relation="dependency")
    ]
    validate_result(r, j)
    check_v2(j.model_dump(mode="json"), r, EXPECTED)
    activity(r, "barrier-a")["predecessors"] = []
    with pytest.raises(CheckFailure, match="complete eligible causes"):
        check_v2(j.model_dump(mode="json"), seal(r), EXPECTED)


def test_waiting_ready_cannot_be_invented_under_port_blocking():
    from validation.component.consistent_carriers import activity, synchronize

    j, r = control("D08")
    activity(r, "r1:port-a")["ready_ps"] = 59500
    r = synchronize(r)
    # Actual response completion is 59000. A real port wait to 60000 must not hide
    # an invented later arrival and lost waiting-area/transfer attribution.
    with pytest.raises(CheckFailure, match="phase ready transition"):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)


def test_receiving_alignment_cannot_end_between_edges():
    from validation.component.consistent_carriers import activity, synchronize

    j, r = control("D10-read")
    activity(r, "back-a")["end_ps"] = 59000
    activity(r, "back").update(ready_ps=59000, start_ps=59000)
    r = synchronize(r)
    with pytest.raises(CheckFailure, match="receiving-clock alignment"):
        check_v2(j.model_dump(mode="json"), r, EXPECTED)
