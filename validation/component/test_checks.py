"""Synthetic observation mutations exercise B's checker; zero native executions."""

from copy import deepcopy
from fractions import Fraction

import pytest

from validation.component.checks import (
    CheckFailure,
    check_allocations,
    check_causal_path,
    check_credits,
    check_work,
    conservation,
    queue_window,
    reduce_evidence,
    union_time,
)


def test_finite_windows_and_initial_inventory():
    assert queue_window([(0, 4000), (2000, 6000)], 0, 8000) == (8000, Fraction(1))
    assert queue_window([(0, 4000), (2000, 6000)], 1000, 5000) == (6000, Fraction(3, 2))
    assert queue_window([(0, None)], 1000, 5000) == (4000, Fraction(1))
    assert conservation([(0, 4000, 32), (2000, 6000, 64)], 1000, 5000) == (32, 64, 32, 64)
    assert union_time([(0, 4000), (2000, 6000), (6000, 7000)]) == 7000


def test_credit_release_at_commit_and_half_open_reuse():
    rows = [
        dict(
            request_id="r0",
            dma_engine_id=0,
            issue_ps=0,
            complete_ps=60000,
            credit_acquire_ps=0,
            credit_release_ps=60000,
        ),
        dict(
            request_id="r1",
            dma_engine_id=0,
            issue_ps=60000,
            complete_ps=120000,
            credit_acquire_ps=60000,
            credit_release_ps=120000,
        ),
    ]
    check_credits(rows, 1)
    wrong = deepcopy(rows)
    wrong[1]["issue_ps"] = wrong[1]["credit_acquire_ps"] = 0
    with pytest.raises(CheckFailure, match="credit capacity"):
        check_credits(wrong, 1)
    wrong = deepcopy(rows)
    wrong[0]["credit_release_ps"] = 54250
    with pytest.raises(CheckFailure, match="credit lifecycle"):
        check_credits(wrong, 1)


def test_completed_work_comes_from_exact_input_tiles():
    jobs = [
        dict(
            id="c",
            kind="compute",
            op_id="g",
            group_id=None,
            repeat_index=0,
            tile_origin=dict(M=0, K=0, N=0),
            tile_extents=dict(M=3, K=5, N=7),
            physical_extents=dict(M=3, K=256, N=256),
        )
    ]
    rows = [
        dict(
            job_id="c",
            op_id="g",
            group_id=None,
            repeat_index=0,
            tile_origin=dict(M=0, K=0, N=0),
            tile_extents=dict(M=3, K=5, N=7),
            useful_matrix_ops=210,
            issued_matrix_ops=393216,
            vector_arithmetic_ops=0,
            cast_ops=0,
        )
    ]
    assert check_work(jobs, rows) == (210, 393216)
    for field, value in [("useful_matrix_ops", 393216), ("issued_matrix_ops", 210)]:
        wrong = deepcopy(rows)
        wrong[0][field] = value
        with pytest.raises(CheckFailure, match="work"):
            check_work(jobs, wrong)
    with pytest.raises(CheckFailure, match="inventory"):
        check_work(jobs, [])


def test_live_allocation_and_last_consumer():
    allocations = [
        dict(
            buffer_id="a",
            space="sram",
            owner_id=0,
            offset_bytes=0,
            size_bytes=256,
            allocate_ps=0,
            free_ps=60000,
            initially_live=True,
            last_consumer_ids=["c"],
        )
    ]
    check_allocations(allocations, {("sram", 0): 256}, {"c": 60000}, 120000)
    for field, value, reason in [
        ("size_bytes", 257, "capacity"),
        ("free_ps", 59000, "last consumer"),
    ]:
        bad = deepcopy(allocations)
        bad[0][field] = value
        with pytest.raises(CheckFailure, match=reason):
            check_allocations(bad, {("sram", 0): 256}, {"c": 60000}, 120000)
    bad = deepcopy(allocations)
    bad.append(dict(bad[0], buffer_id="b", allocate_ps=59000, initially_live=False))
    with pytest.raises(CheckFailure, match="live alias"):
        check_allocations(bad, {("sram", 0): 256}, {"c": 60000}, 120000)


def test_causal_partition_checks_assignment_not_only_sum():
    rows = [
        dict(job_id="b", start_ps=0, end_ps=5000, blocking_predecessor_ids=[]),
        dict(job_id="c", start_ps=5000, end_ps=7000, blocking_predecessor_ids=["b"]),
    ]
    resources = [
        dict(job_id="b", owner_id=1, start_ps=0, end_ps=5000),
        dict(job_id="c", owner_id=0, start_ps=5000, end_ps=7000),
    ]
    path = [
        dict(
            cause_job_id="b",
            predecessor_id=None,
            limiting_resource_id=1,
            start_ps=0,
            end_ps=5000,
            category="compute",
            kind="service",
        ),
        dict(
            cause_job_id="c",
            predecessor_id="b",
            limiting_resource_id=0,
            start_ps=5000,
            end_ps=7000,
            category="compute",
            kind="service",
        ),
    ]
    check_causal_path(
        path, rows, resources, 7000, {"compute": 7000}, {1: {"compute"}, 0: {"compute"}}
    )
    wrong = deepcopy(path)
    wrong[0]["category"] = "memory"
    with pytest.raises(CheckFailure, match="causal category"):
        check_causal_path(
            wrong,
            rows,
            resources,
            7000,
            {"memory": 5000, "compute": 2000},
            {1: {"compute"}, 0: {"compute"}},
        )
    wrong = deepcopy(path)
    wrong[1]["predecessor_id"] = None
    with pytest.raises(CheckFailure, match="causal predecessor"):
        check_causal_path(
            wrong, rows, resources, 7000, {"compute": 7000}, {1: {"compute"}, 0: {"compute"}}
        )


def test_reductions_preserve_failures_and_incomplete_coverage():
    assert reduce_evidence([], required=1) == "not_run"
    assert reduce_evidence(["passed", "unsupported"], required=2) == "not_run"
    assert reduce_evidence(["passed"], required=2) == "not_run"
    assert reduce_evidence(["failed", "not_run"], required=2) == "failed"
    assert reduce_evidence(["setup_error"], required=1) == "not_run"
    assert reduce_evidence(["passed", "passed"], required=2) == "passed"


def test_synthetic_prospective_nonclocked_population_controls():
    from validation.component.checks import check_queue_domain

    owners = {0: "channel:6", 1: "dma:0:0"}
    requests = {"r": dict(channel_id=6, dma_engine_id=0)}
    channel = dict(
        queue_id="channel_service:6",
        owner_id=0,
        item_id="r",
        population="service",
        clock_domain=None,
    )
    credit = dict(
        queue_id="dma_inflight:0", owner_id=1, item_id="r", population="inflight", clock_domain=None
    )
    for control in (channel, credit):
        with pytest.raises(CheckFailure, match="not admitted"):
            check_queue_domain(control, owners, requests, 2)
        check_queue_domain(control, owners, requests, 2, allow_nonclocked=True)
        for field, value in [
            ("owner_id", 1 - control["owner_id"]),
            ("item_id", "absent"),
            ("population", "inflight" if control is channel else "service"),
        ]:
            with pytest.raises(CheckFailure):
                check_queue_domain(
                    dict(control, **{field: value}), owners, requests, 2, allow_nonclocked=True
                )
        check_queue_domain(control, owners, requests, 2, allow_nonclocked=True)
