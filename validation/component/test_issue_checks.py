"""Synthetic local witnesses; mapped opportunity regressions are separately recorded."""

from copy import deepcopy

import pytest

from validation.component import issue_checks as checks
from validation.component.checks import CheckFailure


@pytest.mark.parametrize(
    "ready,reservation,issue,wanted",
    [(59999, 60000, 60000, {"old"}), (60000, 60000, 60000, set()), (60001, 60001, 61000, set())],
)
def test_strict_wait_credit_cause(ready, reservation, issue, wanted):
    rows = {
        "old": dict(job_id="a", dma_engine_id=0, reservation_ps=0, issue_ps=0, complete_ps=60000),
        "new": dict(
            job_id="b",
            dma_engine_id=0,
            reservation_ps=reservation,
            issue_ps=issue,
            complete_ps=120000,
        ),
    }
    assert (
        checks.credit_predecessors(
            "new",
            rows,
            {"a": {"ready_ps": 0}, "b": {"ready_ps": ready}},
            1,
            52,
            {"old": 50, "new": 93},
        )
        == wanted
    )


def witness(dependent="r00"):
    initial = "r01" if dependent == "r00" else "r00"
    rows = {
        key: dict(job_id=key, dma_engine_id=0, reservation_ps=60000 if key == dependent else 0)
        for key in ("r00", "r01")
    }
    jobs = {key: {"ready_ps": 0} for key in rows}
    events = [
        {"observation_ordinal": i, "t_ps": t, "phase": ph}
        for i, (t, ph) in enumerate([(0, 2), (0, 2), (60000, 0), (120000, 0)])
    ]
    opportunities = [
        dict(opportunity_ordinal=i, t_ps=t, event_cursor=c, granted_request_ids=g)
        for i, (t, c, g) in enumerate(
            [(0, 0, [initial]), (0, 2, []), (60000, 3, [dependent]), (120000, 4, [])]
        )
    ]
    ends = {initial: 2, dependent: 3}
    return dict(
        rows=rows,
        jobs=jobs,
        limit=1,
        opportunities=opportunities,
        events=events,
        job_ends={"unicast": 1, **ends},
        request_ends=ends,
        dependencies={dependent: ["unicast"]},
    )


def verify(w):
    fn = getattr(checks, "check_reservation_opportunities", None)
    assert fn is not None, "missing actual eligibility opportunity checker"
    fn(**w)


@pytest.mark.parametrize("dependent", ["r00", "r01"])
def test_inline_actual_eligibility_and_pair(dependent):
    verify(witness(dependent))


def test_consistent_ineligible_first_opportunity_forgery():
    w = witness("r01")
    # All reservation/credit records remain internally joined as the paired control;
    # only dependency completion makes its initial r00 grant impossible.
    w["dependencies"] = {"r00": ["unicast"]}
    with pytest.raises(CheckFailure, match="opportunity eligible grants"):
        verify(w)


@pytest.mark.parametrize("change", ["omit", "move", "late_grant", "duplicate"])
def test_opportunity_inventory_and_earliest_grant(change):
    w = witness()
    if change == "omit":
        del w["opportunities"][1]
    elif change == "move":
        w["opportunities"][0]["event_cursor"] = 2
    elif change == "late_grant":
        w["opportunities"][0]["granted_request_ids"] = []
        w["opportunities"][1]["granted_request_ids"] = ["r01"]
    else:
        w["opportunities"].insert(1, deepcopy(w["opportunities"][0]))
    with pytest.raises(CheckFailure, match="opportunity"):
        verify(w)


@pytest.mark.parametrize("cap", [1, 2])
def test_simultaneous_phase_zero_release_and_ready_tie(cap):
    # Two terminal events at one timestamp are drained before a single opportunity.
    w = witness()
    w["dependencies"] = {"r00": ["unicast"], "r01": ["unicast"]}
    w["events"][0]["phase"] = 0
    w["events"][1]["phase"] = 0
    w["job_ends"]["another"] = 0
    w["limit"] = cap
    w["request_ends"] = {"r00": 2, "r01": 3}
    w["job_ends"].update(w["request_ends"])
    w["rows"]["r00"]["reservation_ps"] = 0
    w["rows"]["r01"]["reservation_ps"] = 60000 if cap == 1 else 0
    # Synthetic phase0 at t0 replaces initialization before any phase2 opportunity.
    w["opportunities"] = [
        dict(opportunity_ordinal=i, t_ps=t, event_cursor=c, granted_request_ids=g)
        for i, (t, c, g) in enumerate(
            [
                (0, 0, []),
                (0, 2, ["r00"] if cap == 1 else ["r00", "r01"]),
                (60000, 3, ["r01"] if cap == 1 else []),
                (120000, 4, []),
            ]
        )
    ]
    verify(w)
    w["opportunities"][1]["granted_request_ids"].reverse()
    if cap == 2:
        with pytest.raises(CheckFailure, match="opportunity eligible grants"):
            verify(w)


def test_independent_pools_and_unlimited_same_edge():
    n = 66
    w = dict(
        rows={
            str(i): dict(job_id=str(i), dma_engine_id=i // 33, reservation_ps=0) for i in range(n)
        },
        jobs={str(i): {"ready_ps": 0} for i in range(n)},
        limit=33,
        dependencies={},
        events=[dict(observation_ordinal=i, t_ps=60000, phase=0) for i in range(n)],
        job_ends={str(i): i for i in range(n)},
        request_ends={str(i): i for i in range(n)},
    )
    granted = sorted(w["rows"], key=lambda k: (w["rows"][k]["dma_engine_id"], k))
    w["opportunities"] = [
        dict(opportunity_ordinal=0, t_ps=0, event_cursor=0, granted_request_ids=granted),
        dict(opportunity_ordinal=1, t_ps=60000, event_cursor=n, granted_request_ids=[]),
    ]
    verify(w)


def test_dependency_ready_but_credit_still_occupied_refuses():
    w = witness()
    w["opportunities"][1]["granted_request_ids"] = ["r00"]
    w["opportunities"][2]["granted_request_ids"] = []
    w["rows"]["r00"]["reservation_ps"] = 0
    with pytest.raises(CheckFailure, match="opportunity eligible grants"):
        verify(w)


@pytest.mark.parametrize(
    "cursor,wanted",
    [(50, set()), (51, {"read"}), (52, {"read"}), (55, {"read"}), (56, {"read", "write"})],
)
def test_mixed_release_cursor_attribution(cursor, wanted):
    # Synthetic helper literal: read terminal 50, inline ACK terminal 55 at 60000.
    # The later opportunity still includes read; it is not an exclusive slot owner.
    rows = {
        key: dict(job_id=key, dma_engine_id=0, reservation_ps=0, issue_ps=0, complete_ps=60000)
        for key in ("read", "write")
    }
    rows["new"] = dict(
        job_id="new", dma_engine_id=0, reservation_ps=60000, issue_ps=60000, complete_ps=120000
    )
    assert (
        checks.credit_predecessors(
            "new", rows, {"new": {"ready_ps": 0}}, 2, cursor, {"read": 50, "write": 55, "new": 93}
        )
        == wanted
    )


@pytest.mark.parametrize(
    "change", ["unsaturated", "other-engine", "not-acquired", "other-time", "equal-readiness"]
)
def test_credit_cursor_is_necessary_not_sufficient(change):
    rows = {
        "old": dict(job_id="old", dma_engine_id=0, reservation_ps=0, issue_ps=0, complete_ps=60000),
        "new": dict(
            job_id="new", dma_engine_id=0, reservation_ps=60000, issue_ps=60000, complete_ps=120000
        ),
    }
    ready, limit = 0, 1
    if change == "unsaturated":
        limit = 2
    elif change == "other-engine":
        rows["old"]["dma_engine_id"] = 1
    elif change == "not-acquired":
        rows["old"]["issue_ps"] = 60000
    elif change == "other-time":
        rows["old"]["complete_ps"] = 59999
    else:
        ready = 60000
    assert (
        checks.credit_predecessors(
            "new", rows, {"new": {"ready_ps": ready}}, limit, 52, {"old": 50, "new": 93}
        )
        == set()
    )
