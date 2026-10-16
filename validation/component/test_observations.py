"""SYNTHETIC CHECKER-ONLY views, not EngineResults, invocations, receipts or native passes."""

from copy import deepcopy

import pytest

from validation.component.checks import CheckFailure
from validation.component.corpus import base
from validation.component.observations import check_observations


class SyntheticView:
    def __init__(self, raw):
        self.raw = raw

    def model_dump(self, **kwargs):
        return deepcopy(self.raw)


def synthetic_resident():
    b = base("resident")
    g = b["points"][0]["task_graph"]
    c = g["jobs"][0]
    owner_ids = {"sram": 8, "accumulator": 0}
    allocations = [
        dict(
            buffer_id=x["id"],
            space=x["space"],
            owner_id=owner_ids[x["space"]],
            offset_bytes=x["offset_bytes"],
            size_bytes=x["size_bytes"],
            allocate_ps=0,
            free_ps=None,
            initially_live=x["initial_residency"] == "preloaded",
            last_consumer_ids=x["final_consumer_ids"],
        )
        for x in g["buffers"]
    ]
    row = dict(
        job_id="c",
        op_id="g0",
        group_id=None,
        repeat_index=0,
        tile_origin=c["tile_origin"],
        tile_extents=c["tile_extents"],
        release_ps=0,
        ready_ps=0,
        start_ps=0,
        end_ps=547000,
        owner_id=0,
        blocking_predecessor_ids=[],
        useful_matrix_ops=210,
        issued_matrix_ops=393216,
        vector_arithmetic_ops=0,
        cast_ops=0,
    )
    resource = dict(
        owner_id=0,
        job_id="c",
        start_ps=0,
        end_ps=547000,
        activity="SYNTHETIC-compute-checker-control",
        limiting_resource_id=0,
        service_start_ps_ratio=None,
        service_end_ps_ratio=None,
    )
    critical = dict(
        kind="service",
        start_ps=0,
        end_ps=547000,
        cause_job_id="c",
        predecessor_id=None,
        limiting_resource_id=0,
        category="compute",
    )
    obs = {
        k: dict(status="observed", records=v)
        for k, v in dict(
            events=[dict(job_id="c", t_ps=547000, kind="COMPUTE_DONE")],
            jobs=[row],
            dma=[],
            transfers=[],
            allocations=allocations,
            queue_membership=[
                dict(
                    queue_id="SYNTHETIC-service",
                    item_id="c",
                    population="service",
                    enter_ps=0,
                    leave_ps=547000,
                    owner_id=0,
                    clock_domain="core",
                )
            ],
            resource_intervals=[resource],
            critical_path=[critical],
        ).items()
    }
    r = dict(
        duration_ps=547000,
        simulator_metrics=dict(event_count=1, completed_job_count=1),
        completed_jobs=["c"],
        per_op=[
            dict(
                op_id="g0", counts=dict(matrix_ops=210), work_counts=dict(issued_matrix_ops=393216)
            )
        ],
        counts=dict(matrix_ops=210),
        work_counts=dict(completed_mac_count=105, issued_matrix_ops=393216),
        traffic_counts=dict(
            read_payload_bytes=0,
            write_payload_bytes=0,
            read_transaction_bytes=0,
            write_transaction_bytes=0,
            unicast_payload_bytes=0,
        ),
        busy_time_ps=[dict(owner_id=0, busy_time_ps=547000), dict(owner_id=8, busy_time_ps=0)],
        attribution_ps=dict(compute=547000),
        observations=obs,
        fidelity_detail=dict(compute=1, noc=0, dram=0, sync="exact", layer_reuse=False),
        u_c0_duration_ps=None,
        unrepresented=["SYNTHETIC-checker-only-contract"],
        diagnostics={
            k: None
            for k in (
                "energy_pj",
                "vector_util_ratio",
                "sram_bank_conflict_stall_ratio",
                "noc_max_link_util_ratio",
                "dram_row_hit_ratio",
            )
        },
    )
    j = dict(
        state_model="resource_intervals/1",
        mapped_point=b["points"][0],
        workload_closure=b,
        owners=[dict(owner_id=0, resource="matrix:0"), dict(owner_id=8, resource="sram:0")],
    )
    expectation = dict(
        owner_categories={"0": ["compute", "overhead"], "8": ["memory"]},
        unrepresented=["SYNTHETIC-checker-only-contract"],
        transfer_boundaries=[],
        boundary_requests={},
        allocation_owners={x["buffer_id"]: x["owner_id"] for x in allocations},
        observations={"observations/critical_path/records/0/category": "compute"},
    )
    return j, r, expectation


def test_synthetic_checker_control_only():
    j, r, e = synthetic_resident()
    assert check_observations(SyntheticView(j), SyntheticView(r), e) == {
        "conservation_windows": {},
        "queue_areas": {"('SYNTHETIC-service', 'service', 0, 'core')": (547000, 1)},
    }


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("drop_work", "inventory"),
        ("useful_as_issued", "work"),
        ("traffic", "traffic"),
        ("capacity", "allocation input"),
        ("early_free", "access lifetime"),
        ("missing_buffer", "inventory"),
        ("missing_consumer", "consumer inventory"),
        ("busy_double", "busy union"),
        ("bad_cause", "causal partition"),
        ("wrong_category", "literal"),
        ("null_zero", "unrepresented diagnostic"),
        ("floor", "analytic floor null"),
        ("noc_contention", "fidelity"),
        ("missing_observations", "required observations"),
        ("wrong_labels", "unrepresented paths"),
    ],
)
def test_synthetic_mutation_and_restored_control(fault, reason):
    j, r, e = synthetic_resident()
    check_observations(SyntheticView(j), SyntheticView(r), e)
    bad = deepcopy(r)
    obs = bad["observations"]
    if fault == "drop_work":
        obs["jobs"]["records"] = []
    elif fault == "useful_as_issued":
        obs["jobs"]["records"][0]["useful_matrix_ops"] = 393216
        bad["counts"]["matrix_ops"] = 393216
    elif fault == "traffic":
        bad["traffic_counts"]["read_payload_bytes"] = 100
    elif fault == "capacity":
        obs["allocations"]["records"][0]["size_bytes"] = 16777217
    elif fault == "early_free":
        obs["allocations"]["records"][0]["free_ps"] = 10
    elif fault == "missing_buffer":
        obs["allocations"]["records"].pop()
    elif fault == "missing_consumer":
        next(x for x in obs["allocations"]["records"] if x["buffer_id"] == "sx")[
            "last_consumer_ids"
        ] = []
    elif fault == "busy_double":
        bad["busy_time_ps"][0]["busy_time_ps"] *= 2
    elif fault == "bad_cause":
        obs["critical_path"]["records"][0]["cause_job_id"] = "missing"
    elif fault == "wrong_category":
        obs["critical_path"]["records"][0]["category"] = "overhead"
        bad["attribution_ps"] = dict(overhead=547000)
    elif fault == "null_zero":
        bad["diagnostics"]["energy_pj"] = 0
    elif fault == "floor":
        bad["u_c0_duration_ps"] = 0
    elif fault == "noc_contention":
        bad["fidelity_detail"]["noc"] = 1
    elif fault == "missing_observations":
        obs["allocations"]["status"] = "unrepresented"
    elif fault == "wrong_labels":
        bad["unrepresented"] = []
    with pytest.raises(CheckFailure, match=reason):
        check_observations(SyntheticView(j), SyntheticView(bad), e)
    check_observations(SyntheticView(j), SyntheticView(r), e)


def test_synthetic_noc0_busy_union_allows_latency_overlap():
    j, r, e = synthetic_resident()
    j["owners"].append(dict(owner_id=32, resource="router:0:0:0"))
    r["busy_time_ps"].append(dict(owner_id=32, busy_time_ps=6000))
    e["owner_categories"]["32"] = ["noc"]
    for i, (start, end) in enumerate([(0, 4000), (2000, 6000)]):
        r["observations"]["resource_intervals"]["records"].append(
            dict(
                owner_id=32,
                job_id="c",
                start_ps=start,
                end_ps=end,
                activity="SYNTHETIC-NoC0-latency",
                limiting_resource_id=32,
                service_start_ps_ratio=None,
                service_end_ps_ratio=None,
            )
        )
        r["observations"]["queue_membership"]["records"].append(
            dict(
                queue_id=f"SYNTHETIC-noc-{i}",
                item_id="c",
                population="service",
                enter_ps=start,
                leave_ps=end,
                owner_id=32,
                clock_domain="noc",
            )
        )
    check_observations(SyntheticView(j), SyntheticView(r), e)
