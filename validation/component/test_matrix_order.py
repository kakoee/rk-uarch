"""Synthetic projections isolate FIFO-ready law from carrier/hash defenses."""

from copy import deepcopy

import pytest

from validation.component.matrix_order import check_matrix_order


def projection():
    graph = dict(
        arbitration="fifo-ready/1",
        dependencies=[],
        jobs=[dict(id=i, kind="compute", core_id=0) for i in ("c", "z")],
    )
    rows = [
        dict(job_id="c", ready_ps=0, start_ps=0, end_ps=547000),
        dict(job_id="z", ready_ps=0, start_ps=547000, end_ps=1094000),
    ]
    return dict(mapped_point=dict(task_graph=graph)), dict(
        observations=dict(jobs=dict(records=rows))
    )


def test_matrix_equal_ready_tie_and_wrong_order():
    job, result = projection()
    check_matrix_order(job, result)
    bad = deepcopy(result)
    a, b = bad["observations"]["jobs"]["records"]
    a["start_ps"], b["start_ps"] = b["start_ps"], a["start_ps"]
    a["end_ps"], b["end_ps"] = b["end_ps"], a["end_ps"]
    with pytest.raises(ValueError, match="matrix FIFO-ready grant"):
        check_matrix_order(job, bad)


def test_matrix_dependency_readiness_precedes_id_and_independent_core():
    job, result = projection()
    graph, rows = job["mapped_point"]["task_graph"], result["observations"]["jobs"]["records"]
    graph["jobs"].append(dict(id="before", kind="barrier"))
    graph["dependencies"] = [dict(before="before", after="c")]
    rows[:] = [
        dict(job_id="before", end_ps=1000),
        dict(job_id="z", ready_ps=0, start_ps=0, end_ps=547000),
        dict(job_id="c", ready_ps=1000, start_ps=547000, end_ps=1094000),
    ]
    check_matrix_order(job, result)
    graph["jobs"][0]["core_id"] = 1
    rows[-1].update(start_ps=1000, end_ps=548000)
    check_matrix_order(job, result)
    rows[-1]["ready_ps"] = 0
    with pytest.raises(ValueError, match="dependency readiness"):
        check_matrix_order(job, result)
