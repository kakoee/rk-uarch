"""Hand-authored SYNTHETIC carrier control; no engine invocation or native evidence.

Uses real job/result parsers with visibly synthetic unit anchors. Never export as a run.
"""

from fractions import Fraction
from functools import cache

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import (
    MappedBundle,
    MappedEngineJob,
    canonical_owners,
    hardware_projection,
    resolve_frequencies,
)

from validation.component.checks import union_time
from validation.component.corpus import build


def observed(rows):
    return dict(status="observed", records=rows)


@cache
def synthetic_job(case="D01"):
    corpus = build()
    item = corpus["items"][case]
    b = MappedBundle.model_validate(item["bundle"])
    p = b.points[0]
    raw = dict(
        protocol="uarch-engine/3",
        bundle_hash=b.bundle_hash,
        point_hash=p.payload_hash,
        request_hash=None,
        assumptions_hash=b.assumptions_hash,
        engine=dict(
            name="native",
            version="native-stage/1",
            model=dict(
                name="native-intervals",
                version="1",
                implementation_hash=content_hash("SYNTHETIC UNIT NO MODEL"),
            ),
            implementation_hash=content_hash("SYNTHETIC UNIT NO ENGINE"),
            compiler_lock_hash=content_hash("SYNTHETIC UNIT NO BUILD"),
        ),
        mapped_point=p.model_dump(mode="json"),
        workload_closure=b.model_dump(mode="json"),
        assumptions=b.assumptions.model_dump(mode="json"),
        hardware=hardware_projection(b.hardware_spec).model_dump(mode="json"),
        hardware_spec_hash=b.hardware_spec_hash,
        rank=b.rank.model_dump(mode="json"),
        precision="bf16",
        fidelity_detail=dict(compute=1, noc=0, dram=0, sync="exact", layer_reuse=False),
        frequency_ratio=p.frequency_ratio,
        freq_hz=resolve_frequencies(b.hardware_spec, p.frequency_ratio).model_dump(mode="json"),
        initial_state=p.initial_state,
        priming_iterations=0,
        seed=0,
        admission=b.admission.model_dump(mode="json"),
        state_model="resource_intervals/1",
        clock_setup=[],
        owner_enumeration="native-owners/1",
        owners=[x.model_dump(mode="json") for x in canonical_owners(b.hardware_spec, p.task_graph)],
        registry=corpus["registry"],
        profile=item["profile"],
    )
    raw["job_hash"] = content_hash(raw)
    return MappedEngineJob.model_validate(raw)


def synthetic_result(job, request_index=0):
    j = job.model_dump(mode="json")
    task = j["mapped_point"]["task_graph"]["jobs"][request_index]
    req = task["fragments"][0]["request_id"]
    owners = {x["resource"]: x["owner_id"] for x in j["owners"]}
    router, channel, port, dma = [
        owners[x]
        for x in (
            "router:0:0:0",
            f"channel:{task['fragments'][0]['channel_id']}",
            "dma_port:0",
            "dma:0:0",
        )
    ]
    activities = []
    events = []
    clocks = []
    resources = []
    queues = []
    # Explicit finite D01 phases. Zero alignments are preserved as causal links.
    rows = [
        ("out-a", "request_noc", "alignment", 0, 0, router, "noc", "noc", False, 0),
        ("out", "request_noc", "service", 0, 4000, router, "noc", "noc", True, 4),
        ("lat-a", "dram_latency", "alignment", 4000, 4000, channel, "memory", "dram", False, 0),
        ("lat", "dram_latency", "service", 4000, 52000, channel, "memory", "dram", False, 48),
        (
            "channel",
            "channel_service",
            "service",
            52000,
            54250,
            channel,
            "memory",
            None,
            True,
            None,
        ),
        ("back-a", "response_noc", "alignment", 54250, 55000, router, "noc", "noc", False, 0),
        ("back", "response_noc", "service", 55000, 59000, router, "noc", "noc", True, 4),
        ("port-a", "read_port", "alignment", 59000, 59000, port, "memory", "core", False, 0),
        ("port", "read_port", "service", 59000, 60000, port, "memory", "core", True, 1),
    ]
    previous = None
    for name, phase, kind, start, end, owner, category, domain, occupied, cycles in rows:
        a = dict(
            activity_id=name,
            job_id=task["id"],
            request_id=req,
            subphase=phase,
            kind=kind,
            ready_ps=start,
            start_ps=start,
            end_ps=end,
            owner_id=owner,
            category=category,
            receiving_domain=domain,
            occupies_resource=occupied,
            dispatch_ordinal=len(events),
            completion_ordinal=len(events) + 1,
            predecessors=[]
            if previous is None
            else [dict(activity_id=previous, relation="sequence")],
        )
        activities.append(a)
        for time, eventkind in [
            (start, "TASK_READY"),
            (end, "DMA_DONE" if name == "port" else "MEM_RESP"),
        ]:
            events.append(
                dict(
                    event_seq=len(events),
                    observation_ordinal=len(events),
                    t_ps=time,
                    phase=1,
                    target_id=owner,
                    kind=eventkind,
                    job_id=task["id"],
                )
            )
        if cycles is not None:
            clocks.append(
                dict(
                    activity_id=name,
                    job_id=task["id"],
                    domain=domain,
                    grant_ps=start,
                    n_cycles=cycles,
                    raw_edge_outcome="success",
                    aligned_start_ps=end if kind == "alignment" else start,
                    completion_ps=end,
                )
            )
        if occupied:
            exact = (
                (Fraction(52000), Fraction(3851744, 71))
                if phase == "channel_service"
                else (None, None)
            )
            resources.append(
                dict(
                    activity_id=name,
                    owner_id=owner,
                    job_id=task["id"],
                    start_ps=start,
                    end_ps=end,
                    activity=phase,
                    limiting_resource_id=owner,
                    service_start_ps_ratio=None
                    if exact[0] is None
                    else dict(numerator=exact[0].numerator, denominator=exact[0].denominator),
                    service_end_ps_ratio=None
                    if exact[1] is None
                    else dict(numerator=exact[1].numerator, denominator=exact[1].denominator),
                )
            )
        if domain is not None:
            queues.append(
                dict(
                    queue_id=f"activity:{phase}:{owner}",
                    item_id=req,
                    population="service",
                    enter_ps=start,
                    leave_ps=end,
                    owner_id=owner,
                    clock_domain=domain,
                    activity_id=name,
                )
            )
        previous = name
    queues += [
        dict(
            queue_id=f"channel_service:{task['fragments'][0]['channel_id']}",
            item_id=req,
            population=pop,
            enter_ps=a,
            leave_ps=z,
            owner_id=channel,
            clock_domain=None,
            activity_id=None,
        )
        for pop, a, z in [("waiting", 52000, 52000), ("service", 52000, 54250)]
    ]
    queues.append(
        dict(
            queue_id="dma_inflight:0",
            item_id=req,
            population="inflight",
            enter_ps=0,
            leave_ps=60000,
            owner_id=dma,
            clock_domain=None,
            activity_id=None,
        )
    )
    zero_counts = dict(
        matrix_ops=0.0, vector_ops=0.0, memory_read_bytes=256.0, memory_write_bytes=0.0
    )
    work = dict(
        format="uarch-native-work-counts/1",
        completed_mac_count=0,
        issued_matrix_ops=0,
        vector_arithmetic_ops=0,
        cast_ops=0,
    )
    traffic = dict(
        format="uarch-native-traffic-counts/1",
        read_payload_bytes=256,
        write_payload_bytes=0,
        read_transaction_bytes=256,
        write_transaction_bytes=0,
        unicast_payload_bytes=0,
    )
    jr = dict(
        job_id=task["id"],
        op_id=None,
        group_id=None,
        repeat_index=None,
        tile_origin=None,
        tile_extents=None,
        release_ps=0,
        ready_ps=0,
        start_ps=0,
        end_ps=60000,
        owner_id=dma,
        blocking_predecessor_ids=[],
        useful_matrix_ops=0,
        issued_matrix_ops=0,
        vector_arithmetic_ops=0,
        cast_ops=0,
    )
    request = dict(
        request_id=req,
        job_id=task["id"],
        dma_engine_id=0,
        direction="read",
        source_buffer_id=task["source"]["buffer_id"],
        destination_buffer_id=task["destination"]["buffer_id"],
        payload_bytes=256,
        transaction_bytes=256,
        credit_acquire_ps=0,
        issue_ps=0,
        complete_ps=60000,
        credit_release_ps=60000,
        route_id=task["fragments"][0]["route_id"],
    )
    transfers = [
        dict(
            request_id=req,
            boundary_id=boundary,
            direction="read",
            payload_bytes=payload,
            transaction_bytes=txn,
            enter_ps=a,
            leave_ps=z,
        )
        for boundary, payload, txn, a, z in [
            ("request_noc", 0, 0, 0, 4000),
            ("dram", 256, 256, 4000, 54250),
            ("response_noc", 256, 0, 54250, 59000),
            ("core_port", 256, 0, 59000, 60000),
        ]
    ]
    allocations = [
        dict(
            buffer_id=b["id"],
            space=b["space"],
            owner_id=owners["channel:0" if b["space"] == "hbm" else "sram:0"],
            offset_bytes=b["offset_bytes"],
            size_bytes=b["size_bytes"],
            allocate_ps=0,
            free_ps=None,
            initially_live=b["initial_residency"] == "preloaded",
            last_consumer_ids=b["final_consumer_ids"],
        )
        for b in j["mapped_point"]["task_graph"]["buffers"]
    ]
    critical = [
        dict(
            kind="service",
            start_ps=a["start_ps"],
            end_ps=a["end_ps"],
            cause_job_id=task["id"],
            predecessor_id=None,
            limiting_resource_id=a["owner_id"],
            category=a["category"],
            activity_id=a["activity_id"],
        )
        for a in activities
        if a["end_ps"] > a["start_ps"]
    ]
    result = dict(
        protocol="uarch-engine/3",
        job_hash=job.job_hash,
        engine=j["engine"],
        scope=j["workload_closure"]["scope"]["kind"],
        completion="complete",
        duration_ps=60000,
        completed_jobs=[task["id"]],
        admission=j["admission"],
        counts=zero_counts,
        ext_counts=dict(sram_read_bytes=0.0, sram_write_bytes=256.0, noc_flit_hop_count=None),
        work_counts=work,
        traffic_counts=traffic,
        per_op=[],
        busy_time_ps=[
            dict(
                owner_id=o["owner_id"],
                busy_time_ps=union_time(
                    (r["start_ps"], r["end_ps"])
                    for r in resources
                    if r["owner_id"] == o["owner_id"]
                ),
            )
            for o in j["owners"]
        ],
        attribution_ps=dict(compute=0, memory=51250, noc=8750, sync=0, overhead=0),
        diagnostics={
            k: None
            for k in (
                "matrix_util_ratio",
                "vector_util_ratio",
                "dma_compute_overlap_ratio",
                "sram_bank_conflict_stall_ratio",
                "noc_latency_p50_ps",
                "noc_latency_p99_ps",
                "noc_max_link_util_ratio",
                "dram_bw_util_ratio",
                "dram_row_hit_ratio",
                "energy_pj",
            )
        },
        fidelity_detail=j["fidelity_detail"],
        unrepresented=["SYNTHETIC-unit-carrier-only"],
        simulator_metrics=dict(event_count=len(events), completed_job_count=1, max_live_events=1),
        trace_hash=None,
        u_c0_duration_ps=None,
        owners=j["owners"],
        observations=dict(
            format="uarch-native-observations/2",
            **{
                k: observed(v)
                for k, v in dict(
                    events=events,
                    jobs=[jr],
                    activities=activities,
                    clocks=clocks,
                    dma=[request],
                    transfers=transfers,
                    allocations=allocations,
                    queue_membership=queues,
                    resource_intervals=resources,
                    critical_path=critical,
                ).items()
            },
        ),
    )
    if j["freq_hz"] == dict(core=800000000, noc=1200000000, dram=900000000):
        # Finite independent D10 read worksheet; no general timing computation.
        times = {
            4000: 3334,
            52000: 56667,
            54250: 58917,
            55000: 59167,
            59000: 62500,
            60000: 63750,
            3851744: 4183101,
            51250: 56833,
            8750: 6917,
        }

        def replace(value):
            if isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            if isinstance(value, list):
                return [replace(v) for v in value]
            if type(value) is int:
                return times.get(value, value)
            return value

        result = replace(result)
        # Busy is a union of occupied records, excluding response alignment.
        pieces = result["observations"]["resource_intervals"]["records"]
        result["busy_time_ps"] = [
            dict(
                owner_id=o["owner_id"],
                busy_time_ps=union_time(
                    (x["start_ps"], x["end_ps"]) for x in pieces if x["owner_id"] == o["owner_id"]
                ),
            )
            for o in j["owners"]
        ]
    result["result_hash"] = content_hash(result)
    return result


def synthetic_resident_result(job):
    """Finite hand-written C02 /2 control, not native output."""
    from copy import deepcopy

    r = synthetic_result(synthetic_job())
    j = job.model_dump(mode="json")
    task = j["mapped_point"]["task_graph"]["jobs"][0]
    obs = r["observations"]
    for key in obs:
        if key != "format":
            obs[key] = observed([])
    activities = []
    clocks = []
    resources = []
    queues = []
    events = []
    previous = None
    for index, (phase, start, end, cycles) in enumerate(
        [
            ("compute_overhead", 0, 32000, 32),
            ("compute_stage", 32000, 33000, 1),
            ("compute_wave", 33000, 546000, 513),
            ("compute_drain", 546000, 547000, 1),
        ]
    ):
        category = "overhead" if index == 0 else "compute"
        for kind, a, z, n in [("alignment", start, start, 0), ("service", start, end, cycles)]:
            name = phase + ":" + kind
            activity = dict(
                activity_id=name,
                job_id=task["id"],
                request_id=None,
                subphase=phase,
                kind=kind,
                ready_ps=a,
                start_ps=a,
                end_ps=z,
                owner_id=0,
                category=category,
                receiving_domain="core",
                occupies_resource=kind == "service",
                dispatch_ordinal=len(events),
                completion_ordinal=len(events) + 1,
                predecessors=[]
                if previous is None
                else [dict(activity_id=previous, relation="sequence")],
            )
            activities.append(activity)
            for time, eventkind in [(a, "OWNER_GRANT"), (z, "COMPUTE_DONE")]:
                events.append(
                    dict(
                        event_seq=len(events),
                        observation_ordinal=len(events),
                        t_ps=time,
                        phase=1,
                        target_id=0,
                        kind=eventkind,
                        job_id=task["id"],
                    )
                )
            clocks.append(
                dict(
                    activity_id=name,
                    job_id=task["id"],
                    domain="core",
                    grant_ps=a,
                    n_cycles=n,
                    raw_edge_outcome="success",
                    aligned_start_ps=a,
                    completion_ps=z,
                )
            )
            queues.append(
                dict(
                    queue_id=f"activity:{phase}:0",
                    item_id=task["id"],
                    population="service",
                    enter_ps=a,
                    leave_ps=z,
                    owner_id=0,
                    clock_domain="core",
                    activity_id=name,
                )
            )
            if kind == "service":
                resources.append(
                    dict(
                        activity_id=name,
                        owner_id=0,
                        job_id=task["id"],
                        start_ps=a,
                        end_ps=z,
                        activity=phase,
                        limiting_resource_id=0,
                        service_start_ps_ratio=None,
                        service_end_ps_ratio=None,
                    )
                )
            previous = name
    row = dict(
        job_id=task["id"],
        op_id=task["op_id"],
        group_id=None,
        repeat_index=0,
        tile_origin=task["tile_origin"],
        tile_extents=task["tile_extents"],
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
    owners = {x["resource"]: x["owner_id"] for x in j["owners"]}
    allocations = [
        dict(
            buffer_id=b["id"],
            space=b["space"],
            owner_id=owners["matrix:0" if b["space"] == "accumulator" else "sram:0"],
            offset_bytes=b["offset_bytes"],
            size_bytes=b["size_bytes"],
            allocate_ps=0,
            free_ps=None,
            initially_live=b["initial_residency"] == "preloaded",
            last_consumer_ids=b["final_consumer_ids"],
        )
        for b in j["mapped_point"]["task_graph"]["buffers"]
    ]
    critical = [
        dict(
            kind="service",
            start_ps=a["start_ps"],
            end_ps=a["end_ps"],
            cause_job_id=task["id"],
            predecessor_id=None,
            limiting_resource_id=0,
            category=a["category"],
            activity_id=a["activity_id"],
        )
        for a in activities
        if a["kind"] == "service"
    ]
    obs.update(
        {
            k: observed(v)
            for k, v in dict(
                events=events,
                jobs=[row],
                activities=activities,
                clocks=clocks,
                allocations=allocations,
                resource_intervals=resources,
                queue_membership=queues,
                critical_path=critical,
            ).items()
        }
    )
    r.update(
        job_hash=job.job_hash,
        engine=j["engine"],
        scope="component",
        duration_ps=547000,
        completed_jobs=[task["id"]],
        admission=j["admission"],
        owners=j["owners"],
    )
    r["counts"].update(matrix_ops=210.0, memory_read_bytes=0.0)
    r["ext_counts"].update(sram_read_bytes=100.0, sram_write_bytes=42.0)
    r["work_counts"].update(completed_mac_count=105, issued_matrix_ops=393216)
    r["traffic_counts"].update(read_payload_bytes=0, read_transaction_bytes=0)
    r["per_op"] = [
        dict(
            op_id=task["op_id"],
            **{
                k: deepcopy(r[k]) for k in ("counts", "ext_counts", "work_counts", "traffic_counts")
            },
        )
    ]
    r["busy_time_ps"] = [
        dict(owner_id=o["owner_id"], busy_time_ps=547000 if o["owner_id"] == 0 else 0)
        for o in j["owners"]
    ]
    r["attribution_ps"].update(compute=515000, overhead=32000, memory=0, noc=0)
    r["simulator_metrics"].update(event_count=len(events))
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


def synthetic_port_pair(job):
    """D08 finite two-channel overlap/port-wait witness; hand-authored unit control."""
    from copy import deepcopy

    pieces = [synthetic_result(job, index) for index in (0, 1)]
    for index, result in enumerate(pieces):
        obs = result["observations"]
        prefix = f"r{index}:"
        for section in (
            "activities",
            "clocks",
            "resource_intervals",
            "queue_membership",
            "critical_path",
        ):
            for row in obs[section]["records"]:
                if row.get("activity_id") is not None:
                    row["activity_id"] = prefix + row["activity_id"]
                for link in row.get("predecessors", []):
                    link["activity_id"] = prefix + link["activity_id"]
        if index:
            for a in obs["activities"]["records"]:
                if a["activity_id"] == "r1:port-a":
                    a.update(
                        start_ps=60000,
                        end_ps=60000,
                        predecessors=[dict(activity_id="r0:port", relation="resource")],
                    )
                elif a["activity_id"] == "r1:port":
                    a.update(ready_ps=60000, start_ps=60000, end_ps=61000)
            for c in obs["clocks"]["records"]:
                if c["activity_id"] in ("r1:port-a", "r1:port"):
                    c.update(
                        grant_ps=60000,
                        aligned_start_ps=60000,
                        completion_ps=60000 if c["activity_id"].endswith("-a") else 61000,
                    )
            for res in obs["resource_intervals"]["records"]:
                if res["activity_id"] == "r1:port":
                    res.update(start_ps=60000, end_ps=61000)
            for q in obs["queue_membership"]["records"]:
                if q["activity_id"] == "r1:port-a":
                    q.update(enter_ps=60000, leave_ps=60000)
                    waiting = deepcopy(q)
                    waiting.update(population="waiting", enter_ps=59000, leave_ps=60000)
                elif q["activity_id"] == "r1:port":
                    q.update(enter_ps=60000, leave_ps=61000)
                elif q["population"] == "inflight":
                    q["leave_ps"] = 61000
            obs["queue_membership"]["records"].append(waiting)
            obs["jobs"]["records"][0]["end_ps"] = 61000
            obs["dma"]["records"][0].update(complete_ps=61000, credit_release_ps=61000)
            next(t for t in obs["transfers"]["records"] if t["boundary_id"] == "core_port")[
                "leave_ps"
            ] = 61000
        # Ordinal values initially local; reassign in actual time order after combining.
        for a in obs["activities"]["records"]:
            for key, time in (
                ("dispatch_ordinal", a["start_ps"]),
                ("completion_ordinal", a["end_ps"]),
            ):
                obs["events"]["records"][a[key]]["t_ps"] = time
    result = deepcopy(pieces[0])
    obs = result["observations"]
    for section in (
        "jobs",
        "dma",
        "transfers",
        "activities",
        "clocks",
        "resource_intervals",
        "queue_membership",
    ):
        obs[section]["records"] = sum(
            [deepcopy(p["observations"][section]["records"]) for p in pieces], []
        )
    events = []
    for index, piece in enumerate(pieces):
        for e in piece["observations"]["events"]["records"]:
            events.append((e["t_ps"], index, e["observation_ordinal"], deepcopy(e)))
    events.sort(key=lambda x: x[:3])
    ordinals = {}
    for ordinal, (_, index, old, e) in enumerate(events):
        ordinals[index, old] = ordinal
        e.update(observation_ordinal=ordinal, event_seq=ordinal)
    obs["events"] = observed([x[3] for x in events])
    for a in obs["activities"]["records"]:
        index = int(a["activity_id"][1])
        a["dispatch_ordinal"] = ordinals[index, a["dispatch_ordinal"]]
        a["completion_ordinal"] = ordinals[index, a["completion_ordinal"]]
    obs["critical_path"]["records"].append(
        dict(
            kind="service",
            start_ps=60000,
            end_ps=61000,
            cause_job_id=obs["jobs"]["records"][1]["job_id"],
            predecessor_id=obs["jobs"]["records"][0]["job_id"],
            limiting_resource_id=next(
                a["owner_id"] for a in obs["activities"]["records"] if a["activity_id"] == "r1:port"
            ),
            category="memory",
            activity_id="r1:port",
        )
    )
    result.update(duration_ps=61000, completed_jobs=[x["job_id"] for x in obs["jobs"]["records"]])
    result["counts"]["memory_read_bytes"] = 512.0
    result["ext_counts"]["sram_write_bytes"] = 512.0
    result["traffic_counts"].update(read_payload_bytes=512, read_transaction_bytes=512)
    result["attribution_ps"]["memory"] = 52250
    result["simulator_metrics"].update(event_count=len(events), completed_job_count=2)
    resources = obs["resource_intervals"]["records"]
    result["busy_time_ps"] = [
        dict(
            owner_id=o["owner_id"],
            busy_time_ps=union_time(
                (x["start_ps"], x["end_ps"]) for x in resources if x["owner_id"] == o["owner_id"]
            ),
        )
        for o in result["owners"]
    ]
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    return result
