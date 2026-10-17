"""Consistently resealed synthetic carriers; never component outputs/native evidence.
Inputs independently hand constructed by B; attacks reproduce reviewer M1/M2/M3/M4/V1.
"""

from copy import deepcopy
from typing import Any

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import validate_result

from validation.component import synthetic_carrier

synthetic_job: Any = synthetic_carrier.synthetic_job
synthetic_result: Any = synthetic_carrier.synthetic_result
synthetic_port_pair: Any = synthetic_carrier.synthetic_port_pair


def records(r: Any, section: Any) -> Any:
    return r["observations"][section]["records"]


def act(r: Any, name: Any) -> Any:
    return next(a for a in records(r, "activities") if a["activity_id"] == name)


def seal(r: Any) -> Any:
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


def sample(case: Any = "D01") -> Any:
    j = synthetic_job(case)
    r = synthetic_port_pair(j) if case == "D08" else synthetic_result(j)
    # Explicit proposed endpoint encoding, independent of production implementation.
    kinds = {
        "read_port": ("OWNER_GRANT", "DMA_DONE"),
        "write_port": ("OWNER_GRANT", "MEM_RESP"),
        "channel_service": ("MEM_REQ", "MEM_RESP"),
        "dram_latency": ("MEM_REQ", "MEM_RESP"),
        "ack": ("TASK_READY", "DMA_DONE"),
        "barrier": ("SYNC_ARRIVE", "BARRIER_RELEASE"),
    }
    ev = {e["observation_ordinal"]: e for e in records(r, "events")}
    for a in records(r, "activities"):
        pair = (
            ("TASK_READY", "DEPENDENCY_READY")
            if a["kind"] == "alignment"
            else (
                ("NOC_HEAD", "NOC_TAIL")
                if a["subphase"].endswith("_noc")
                else ("OWNER_GRANT", "COMPUTE_DONE")
                if a["subphase"].startswith("compute_")
                else kinds[a["subphase"]]
            )
        )
        ev[a["dispatch_ordinal"]]["kind"], ev[a["completion_ordinal"]]["kind"] = pair
    for c in records(r, "critical_path"):
        c["predecessor_id"] = None
    return j, seal(r)


def rebusy(r: Any) -> Any:
    for b in r["busy_time_ps"]:
        end = total = 0
        for lo, hi in sorted(
            (x["start_ps"], x["end_ps"])
            for x in records(r, "resource_intervals")
            if x["owner_id"] == b["owner_id"]
        ):
            total += max(0, hi - max(lo, end))
            end = max(end, hi)
        b["busy_time_ps"] = total


@pytest.mark.parametrize("case", ["D01", "D08", "D10-read"])
def test_structural_positive(case: Any) -> None:
    j, r = sample(case)
    validate_result(r, j)


@pytest.mark.parametrize("part", ["category", "domain"])
def test_M1_relabel(part: Any) -> None:
    j, r = sample("D10-read")
    a = act(r, "back-a")
    if part == "category":
        a["category"] = "memory"
        for c in records(r, "critical_path"):
            if c["activity_id"] == "back-a":
                c["category"] = "memory"
                delta = c["end_ps"] - c["start_ps"]
                r["attribution_ps"]["noc"] -= delta
                r["attribution_ps"]["memory"] += delta
    else:
        a["receiving_domain"] = "dram"
        for c in records(r, "clocks"):
            if c["activity_id"] == "back-a":
                c["domain"] = "dram"
        for q in records(r, "queue_membership"):
            if q["activity_id"] == "back-a":
                q["clock_domain"] = "dram"
    with pytest.raises(ValueError, match="^IncompleteObservations: activity category/domain$"):
        validate_result(seal(r), j)


def test_M2_owner_forgery() -> None:
    j, r = sample()
    port = next(o.owner_id for o in j.owners if o.resource == "dma_port:0")
    a = act(r, "out")
    a["owner_id"] = port
    for e in records(r, "events"):
        if e["observation_ordinal"] in (a["dispatch_ordinal"], a["completion_ordinal"]):
            e["target_id"] = port
    for x in records(r, "resource_intervals"):
        if x["activity_id"] == "out":
            x["owner_id"] = x["limiting_resource_id"] = port
    for q in records(r, "queue_membership"):
        if q["activity_id"] == "out":
            q.update(owner_id=port, queue_id=f"activity:request_noc:{port}")
    for c in records(r, "critical_path"):
        if c["activity_id"] == "out":
            c["limiting_resource_id"] = port
    rebusy(r)
    with pytest.raises(ValueError, match="^InvalidResource: activity owner$"):
        validate_result(seal(r), j)


def test_M3_missing_off_chain_cause() -> None:
    j, r = sample("D08")
    act(r, "r1:back-a")["predecessors"] = []
    with pytest.raises(ValueError, match="^AttributionMismatch: missing tight cause$"):
        validate_result(seal(r), j)


def test_M4_nonoccupying_channel() -> None:
    j, r = sample()
    ch, ba = act(r, "channel"), act(r, "back-a")
    ch.update(occupies_resource=False, end_ps=54500)
    ba.update(ready_ps=54500, start_ps=54500)
    r["observations"]["resource_intervals"]["records"] = [
        x for x in records(r, "resource_intervals") if x["activity_id"] != "channel"
    ]
    for e in records(r, "events"):
        if e["observation_ordinal"] in (ch["completion_ordinal"], ba["dispatch_ordinal"]):
            e["t_ps"] = 54500
    for q in records(r, "queue_membership"):
        if q["queue_id"].startswith("channel_service:") and q["population"] == "service":
            q["leave_ps"] = 54500
        if q["activity_id"] == "back-a":
            q["enter_ps"] = 54500
            if q["population"] == "waiting":
                q["leave_ps"] = 54500
    for t in records(r, "transfers"):
        if t["boundary_id"] == "dram":
            t["leave_ps"] = 54500
        if t["boundary_id"] == "response_noc":
            t["enter_ps"] = 54500
    for c in records(r, "clocks"):
        if c["activity_id"] == "back-a":
            c["grant_ps"] = 54500
    for c in records(r, "critical_path"):
        if c["activity_id"] == "channel":
            c["end_ps"] = 54500
        if c["activity_id"] == "back-a":
            c["start_ps"] = 54500
    r["attribution_ps"]["memory"] += 250
    r["attribution_ps"]["noc"] -= 250
    rebusy(r)
    with pytest.raises(ValueError, match="^IncompleteObservations: phase occupancy$"):
        validate_result(seal(r), j)


def test_V1_credit_only_first_from_last() -> None:
    j, r = sample("D08")
    a = act(r, "r1:port")
    a["predecessors"].append(dict(activity_id="r0:port", relation="credit"))
    a["predecessors"].sort(key=lambda p: (p["activity_id"], p["relation"]))
    with pytest.raises(ValueError, match="^AttributionMismatch: credit endpoints$"):
        validate_result(seal(r), j)


@pytest.mark.parametrize(
    "field,detail",
    [
        ("owner", "job owner"),
        ("release", "component release"),
        ("blocking", "unrepresented job predecessors"),
        ("critical", "unrepresented critical predecessor"),
        ("event", "activity event kind"),
    ],
)
def test_F8_resealed_fields(field: Any, detail: Any) -> None:
    j, r = sample("D08")
    row = records(r, "jobs")[0]
    if field == "owner":
        row["owner_id"] = next(o.owner_id for o in j.owners if o.resource == "channel:6")
    if field == "release":
        row["release_ps"] = 50000
    if field == "blocking":
        row["blocking_predecessor_ids"] = ["r01"]
    if field == "critical":
        records(r, "critical_path")[-1]["predecessor_id"] = "FORGED"
    if field == "event":
        next(e for e in records(r, "events") if e["kind"] == "DMA_DONE")["kind"] = "STAT_SAMPLE"
    with pytest.raises(
        ValueError,
        match="^(IncompleteObservations|AttributionMismatch|InvalidResource): " + detail + "$",
    ):
        validate_result(seal(r), j)
    validate_result(sample("D08")[1], j)


def synthetic() -> Any:
    j, r = sample()
    rows = records(r, "queue_membership")
    rows.sort(key=lambda q: not q["queue_id"].startswith("channel_service:"))
    return j, r


def check(job: Any, raw: Any) -> Any:
    raw = deepcopy(raw)
    raw["result_hash"] = content_hash(raw, exclude=("result_hash",))
    return validate_result(raw, job)


def test_synthetic_null_channel_dma_and_clocked_controls() -> None:
    j, r = synthetic()
    assert check(j, r)
    q = r["observations"]["queue_membership"]["records"][0]
    t = next(t for t in j.mapped_point.task_graph.jobs if t.kind == "dma")
    owner = next(
        o.owner_id
        for o in j.owners
        if o.resource == f"dma:{t.dma_engine_id // 4}:{t.dma_engine_id % 4}"
    )
    q.update(queue_id=f"dma_inflight:{t.dma_engine_id}", population="inflight", owner_id=owner)
    assert check(j, r)
    a = r["observations"]["activities"]["records"][0]
    q.update(
        queue_id=f"activity:{a['subphase']}:{a['owner_id']}",
        item_id=a["request_id"] or a["job_id"],
        owner_id=a["owner_id"],
        population="waiting",
        clock_domain=a["receiving_domain"],
        enter_ps=a["ready_ps"],
        leave_ps=a["start_ps"],
        activity_id=a["activity_id"],
    )
    assert check(j, r)


@pytest.mark.parametrize("domain", [None, "dram"])
@pytest.mark.parametrize(
    "fault", ["owner", "channel", "engine", "request", "population", "invented_queue"]
)
def test_synthetic_queue_attacks_restored(fault: Any, domain: Any) -> None:
    j, r = synthetic()
    assert check(j, r)
    bad = deepcopy(r)
    q = bad["observations"]["queue_membership"]["records"][0]
    q["clock_domain"] = domain
    if fault == "owner":
        q["owner_id"] = 0
    if fault == "channel":
        q["queue_id"] = "channel_service:7"
    if fault == "engine":
        q.update(queue_id="dma_inflight:15", population="inflight")
    if fault == "request":
        q["item_id"] = "undeclared"
    if fault == "population":
        q["population"] = "inflight"
    if fault == "invented_queue":
        q["queue_id"] = "arbitrary"
    with pytest.raises(ValueError, match="IncompleteObservations"):
        check(j, bad)
    assert check(j, r)


def test_synthetic_activity_dispatch_and_cycle_attacks() -> None:
    j, r = synthetic()
    assert check(j, r)
    for fault in ("request", "ordinal", "cycle"):
        bad = deepcopy(r)
        acts = bad["observations"]["activities"]["records"]
        a = acts[0]
        if fault == "request":
            a["request_id"] = "undeclared"
        if fault == "ordinal":
            a["dispatch_ordinal"] = 999
        if fault == "cycle":
            a["predecessors"] = [dict(activity_id=a["activity_id"], relation="sequence")]
        with pytest.raises(ValueError):
            check(j, bad)
        assert check(j, r)


def test_stale_result_binding_precedes_queue_guard() -> None:
    j, raw = synthetic()
    good = check(j, raw).model_dump(mode="json")
    bad = deepcopy(good)
    bad["observations"]["queue_membership"]["records"][0]["item_id"] = "forged"
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        validate_result(bad, j)
    with pytest.raises(ValueError, match="IncompleteObservations"):
        check(j, bad)
    assert validate_result(good, j)


def test_C1_two_activity_zero_duration_cycle() -> None:
    """A genuine two-node cycle. Final endpoint eligibility also excludes it (redundant)."""
    j, r = sample("D08")
    left, right = act(r, "r0:out-a"), act(r, "r1:out-a")
    assert left["start_ps"] == left["end_ps"] == right["start_ps"] == right["end_ps"] == 0
    left["predecessors"] = [dict(activity_id=right["activity_id"], relation="resource")]
    right["predecessors"] = [dict(activity_id=left["activity_id"], relation="resource")]
    with pytest.raises(ValueError, match="^AttributionMismatch: activity cycle$"):
        validate_result(seal(r), j)
    validate_result(sample("D08")[1], j)


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate_id",
        "duplicate_phase",
        "event_join",
        "endpoint_order",
        "occupied_join",
        "missing_occupied",
        "ratio_pair",
        "ratio_required",
        "ratio_rounding",
        "queue_times",
        "clock_join",
        "canonical_chain",
        "critical_fields",
        "sequence",
        "dependency",
    ],
)
def test_additional_consistent_structural_witnesses(fault: Any) -> None:
    j, r = sample("D08" if fault in ("canonical_chain", "critical_fields", "dependency") else "D01")
    if fault == "duplicate_id":
        records(r, "activities").append(deepcopy(act(r, "out-a")))
    elif fault == "duplicate_phase":
        clone = deepcopy(act(r, "out-a"))
        clone["activity_id"] = "zz:clone"
        records(r, "activities").append(clone)
        for section in ("clocks", "queue_membership"):
            for row in list(records(r, section)):
                if row["activity_id"] == "out-a":
                    clone_row = deepcopy(row)
                    clone_row["activity_id"] = "zz:clone"
                    records(r, section).append(clone_row)
        act(r, "out")["predecessors"] = [dict(activity_id="zz:clone", relation="sequence")]
    elif fault == "event_join":
        a = act(r, "out")
        next(e for e in records(r, "events") if e["observation_ordinal"] == a["dispatch_ordinal"])[
            "job_id"
        ] = "FORGED"
    elif fault == "endpoint_order":
        a = act(r, "out-a")
        a["dispatch_ordinal"], a["completion_ordinal"] = (
            a["completion_ordinal"],
            a["dispatch_ordinal"],
        )
        ev = {e["observation_ordinal"]: e for e in records(r, "events")}
        ev[a["dispatch_ordinal"]]["kind"] = "TASK_READY"
        ev[a["completion_ordinal"]]["kind"] = "DEPENDENCY_READY"
    elif fault == "occupied_join":
        x = next(x for x in records(r, "resource_intervals") if x["activity_id"] == "out")
        x["job_id"] = "FORGED"
    elif fault == "missing_occupied":
        r["observations"]["resource_intervals"]["records"] = [
            x for x in records(r, "resource_intervals") if x["activity_id"] != "out"
        ]
        rebusy(r)
    elif fault.startswith("ratio_"):
        row = next(x for x in records(r, "resource_intervals") if x["activity_id"] == "channel")
        if fault == "ratio_pair":
            row["service_end_ps_ratio"] = None
        elif fault == "ratio_required":
            row["service_end_ps_ratio"] = row["service_start_ps_ratio"] = None
        else:
            row["service_end_ps_ratio"] = dict(numerator=54500, denominator=1)
    elif fault == "queue_times":
        next(q for q in records(r, "queue_membership") if q["activity_id"] == "out")["leave_ps"] = (
            3999
        )
    elif fault == "clock_join":
        next(c for c in records(r, "clocks") if c["activity_id"] == "out")["grant_ps"] = 1
    elif fault == "canonical_chain":
        row = next(c for c in records(r, "critical_path") if c["activity_id"] == "r0:out")
        row["activity_id"] = "r1:out"
        row["cause_job_id"] = "r01"
    elif fault == "critical_fields":
        next(c for c in records(r, "critical_path") if c["activity_id"] == "r0:out")[
            "cause_job_id"
        ] = "r01"
    elif fault == "sequence":
        act(r, "port")["predecessors"] = [dict(activity_id="back", relation="sequence")]
    elif fault == "dependency":
        next(p for p in act(r, "r1:port-a")["predecessors"] if p["relation"] == "resource")[
            "relation"
        ] = "dependency"
    code = (
        "AttributionMismatch"
        if fault in ("canonical_chain", "critical_fields", "sequence", "dependency")
        else "IncompleteObservations"
    )
    with pytest.raises(ValueError, match="^" + code + "(:|$)"):
        validate_result(seal(r), j)
    validate_result(
        sample("D08" if fault in ("canonical_chain", "critical_fields", "dependency") else "D01")[
            1
        ],
        j,
    )


@pytest.mark.parametrize(
    "fault",
    [
        "job_readiness",
        "job_span",
        "activity_ready",
        "unreferenced_event",
        "queue_window",
        "nonclocked_domain",
        "ordinary_name",
        "tight_ordinal",
        "resource_boundary",
    ],
)
def test_summary_boundary_and_population_guards(fault: Any) -> None:
    from validation.component import consistent_carriers

    pair_control: Any = consistent_carriers.pair_control
    j, r = (
        pair_control("D05-one")
        if fault == "job_readiness"
        else sample("D08" if fault == "resource_boundary" else "D01")
    )
    if fault == "job_readiness":
        records(r, "jobs")[1]["ready_ps"] = 1
    elif fault == "job_span":
        records(r, "jobs")[0]["start_ps"] = 1
    elif fault == "activity_ready":
        act(r, "out-a")["ready_ps"] = 1
    elif fault == "unreferenced_event":
        e = deepcopy(records(r, "events")[-1])
        e.update(observation_ordinal=999, event_seq=999, kind="STAT_SAMPLE")
        records(r, "events").append(e)
        r["simulator_metrics"]["event_count"] += 1
    elif fault == "queue_window":
        q = next(
            q
            for q in records(r, "queue_membership")
            if q["queue_id"].startswith("channel_service:")
        )
        q["leave_ps"] = q["enter_ps"] - 1
    elif fault == "nonclocked_domain":
        next(
            q
            for q in records(r, "queue_membership")
            if q["queue_id"].startswith("channel_service:")
        )["clock_domain"] = "dram"
    elif fault == "ordinary_name":
        next(q for q in records(r, "queue_membership") if q["activity_id"] == "out")["queue_id"] = (
            "activity:FORGED"
        )
    elif fault == "tight_ordinal":
        before, after = act(r, "port-a"), act(r, "port")
        b, a = before["completion_ordinal"], after["dispatch_ordinal"]
        ev = {e["observation_ordinal"]: e for e in records(r, "events")}
        ev[b]["kind"], ev[a]["kind"] = ev[a]["kind"], ev[b]["kind"]
        before["completion_ordinal"], after["dispatch_ordinal"] = a, b
    elif fault == "resource_boundary":
        # Same-time, same-owner port service is not an acquisition alignment boundary.
        act(r, "r1:port")["predecessors"] = [dict(activity_id="r0:port", relation="resource")]
    with pytest.raises(ValueError, match="^(IncompleteObservations|AttributionMismatch)(:|$)"):
        validate_result(seal(r), j)


@pytest.mark.parametrize("fault", ["request", "owner"])
def test_compute_binding_consistent_forgery(fault: Any) -> None:
    from validation.component import consistent_carriers

    control: Any = consistent_carriers.control
    synchronize: Any = consistent_carriers.synchronize
    j, r = control("C02")
    validate_result(r, j)
    port = next(o.owner_id for o in j.owners if o.resource == "dma_port:0")
    for a in records(r, "activities"):
        if fault == "request":
            a["request_id"] = "FORGED"
        else:
            a["owner_id"] = port
    if fault == "request":
        for q in records(r, "queue_membership"):
            q["item_id"] = "FORGED"
    with pytest.raises(ValueError, match="^IncompleteObservations(:|$)"):
        validate_result(synchronize(r), j)


def test_request_belongs_to_declared_job() -> None:
    from validation.component import consistent_carriers

    pair_control: Any = consistent_carriers.pair_control
    j, r = pair_control("D05-two")
    validate_result(r, j)
    request = next(a["request_id"] for a in records(r, "activities") if a["job_id"] == "r01")
    changed = set()
    for a in records(r, "activities"):
        if a["job_id"] == "r00":
            a["request_id"] = request
            changed.add(a["activity_id"])
    for q in records(r, "queue_membership"):
        if q["activity_id"] in changed:
            q["item_id"] = request
    with pytest.raises(ValueError, match="^IncompleteObservations: activity request$"):
        validate_result(seal(r), j)


def test_unclocked_channel_cannot_acquire_alignment() -> None:
    from validation.component import consistent_carriers

    synchronize: Any = consistent_carriers.synchronize
    j, r = sample()
    service = act(r, "channel")
    alignment = deepcopy(service)
    alignment.update(
        activity_id="channel-a",
        kind="alignment",
        occupies_resource=False,
        end_ps=service["start_ps"],
        dispatch_ordinal=1000,
        completion_ordinal=1001,
    )
    service["predecessors"] = [dict(activity_id="channel-a", relation="sequence")]
    records(r, "activities").append(alignment)
    for ordinal, kind in [(1000, "TASK_READY"), (1001, "DEPENDENCY_READY")]:
        e = deepcopy(records(r, "events")[0])
        e.update(
            observation_ordinal=ordinal,
            event_seq=ordinal,
            kind=kind,
            t_ps=alignment["start_ps"],
            target_id=alignment["owner_id"],
            job_id=alignment["job_id"],
        )
        records(r, "events").append(e)
    r["simulator_metrics"]["event_count"] += 2
    with pytest.raises(ValueError, match="^IncompleteObservations: alignment is not busy$"):
        validate_result(synchronize(r), j)


@pytest.mark.parametrize(
    "fault,code",
    [
        ("activity_job", "InvalidResource"),
        ("activity_owner", "InvalidResource"),
        ("request", "IncompleteObservations"),
        ("dispatch", "IncompleteObservations"),
        ("link", "AttributionMismatch"),
        ("interval", "IncompleteObservations"),
        ("queue", "IncompleteObservations"),
        ("clock", "IncompleteObservations"),
        ("missing_job_activities", "IncompleteObservations"),
    ],
)
def test_malformed_witness_refuses_without_lookup_crash(fault: Any, code: Any) -> None:
    """Totality/error-order controls, not unsafe-admission mutation evidence."""
    j, r = sample()
    if fault == "activity_job":
        act(r, "out")["job_id"] = "unknown"
    elif fault == "activity_owner":
        act(r, "out")["owner_id"] = 2**63
    elif fault == "request":
        act(r, "out")["request_id"] = "unknown"
    elif fault == "dispatch":
        act(r, "out")["dispatch_ordinal"] = 999
    elif fault == "link":
        act(r, "out")["predecessors"] = [dict(activity_id="unknown", relation="sequence")]
    elif fault == "interval":
        records(r, "resource_intervals")[0]["activity_id"] = "unknown"
    elif fault == "queue":
        records(r, "queue_membership")[0]["activity_id"] = "unknown"
    elif fault == "clock":
        records(r, "clocks")[0]["activity_id"] = "unknown"
    elif fault == "missing_job_activities":
        records(r, "activities").clear()
    with pytest.raises(ValueError, match="^" + code + "(:|$)"):
        validate_result(seal(r), j)


def test_component_refuses_legacy_observation_shape() -> None:
    j, r = sample()
    obs = r["observations"]
    obs["format"] = "uarch-native-observations/1"
    del obs["activities"]
    for section in ("clocks", "resource_intervals", "queue_membership", "critical_path"):
        for row in records(r, section):
            del row["activity_id"]
    with pytest.raises(ValueError, match="^IncompleteObservations: component /2$"):
        validate_result(seal(r), j)


def zero_transport_shell(case: Any) -> Any:
    """Zero-time STRUCTURAL shell only: deliberately no E4 mechanism/inventory claim."""
    j = synthetic_job(case)
    _, r = sample()
    raw = j.model_dump(mode="json")
    owners = {o.resource: o.owner_id for o in j.owners}
    graph = raw["mapped_point"]["task_graph"]
    buffers = {b["id"]: b for b in graph["buffers"]}
    routes = {p["id"]: p for p in graph["routes"]}
    obs = r["observations"]
    template = deepcopy(records(r, "jobs")[0])
    for section in obs.values():
        if isinstance(section, dict):
            section["records"] = []
    traffic = {k: 0 if isinstance(v, int) else v for k, v in r["traffic_counts"].items()}
    for task in graph["jobs"]:
        if task["kind"] == "dma":
            core = task["dma_engine_id"] // 4
            owner = owners[f"dma_port:{core}"]
            summary_owner = owners[f"dma:{core}:{task['dma_engine_id'] % 4}"]
            phase, category, domain, occupied = "read_port", "memory", "core", True
            kinds = ("OWNER_GRANT", "DMA_DONE")
            requests = [f["request_id"] for f in task["fragments"]]
            for f in task["fragments"]:
                records(r, "dma").append(
                    dict(
                        request_id=f["request_id"],
                        job_id=task["id"],
                        dma_engine_id=task["dma_engine_id"],
                        direction=task["direction"],
                        source_buffer_id=task["source"]["buffer_id"],
                        destination_buffer_id=task["destination"]["buffer_id"],
                        payload_bytes=f["payload_bytes"],
                        transaction_bytes=f["transaction_bytes"],
                        credit_acquire_ps=0,
                        issue_ps=0,
                        complete_ps=0,
                        credit_release_ps=0,
                        route_id=f["route_id"],
                    )
                )
                traffic[task["direction"] + "_payload_bytes"] += f["payload_bytes"]
                traffic[task["direction"] + "_transaction_bytes"] += f["transaction_bytes"]
        elif task["kind"] == "barrier":
            owner = summary_owner = owners[f"barrier:{task['id']}"]
            phase, category, domain, occupied = "barrier", "sync", "noc", False
            kinds, requests = ("SYNC_ARRIVE", "BARRIER_RELEASE"), [None]
        else:
            assert task["kind"] == "noc_transfer"
            core = buffers[task["source"]["buffer_id"]]["core_id"]
            cols = int(j.workload_closure.hardware_spec.cores.grid.cols.value)
            owner = summary_owner = owners[f"router:0:{core // cols}:{core % cols}"]
            phase, category, domain = "unicast_noc", "noc", "noc"
            occupied = len(routes[task["route_id"]]["core_ids"]) > 1
            kinds, requests = ("NOC_HEAD", "NOC_TAIL"), [task["id"]]
        row = deepcopy(template)
        row.update(
            job_id=task["id"],
            op_id=task.get("op_id"),
            owner_id=summary_owner,
            release_ps=0,
            ready_ps=0,
            start_ps=0,
            end_ps=0,
            blocking_predecessor_ids=[],
        )
        records(r, "jobs").append(row)
        for request in requests:
            ordinal = len(records(r, "events"))
            aid = "SYNTHETIC-STRUCTURAL:" + (request or task["id"])
            records(r, "activities").append(
                dict(
                    activity_id=aid,
                    job_id=task["id"],
                    request_id=request,
                    subphase=phase,
                    kind="service",
                    ready_ps=0,
                    start_ps=0,
                    end_ps=0,
                    owner_id=owner,
                    category=category,
                    receiving_domain=domain,
                    occupies_resource=occupied,
                    dispatch_ordinal=ordinal,
                    completion_ordinal=ordinal + 1,
                    predecessors=[],
                )
            )
            for index, kind in enumerate(kinds, ordinal):
                records(r, "events").append(
                    dict(
                        event_seq=index,
                        observation_ordinal=index,
                        t_ps=0,
                        phase=1,
                        target_id=owner,
                        kind=kind,
                        job_id=task["id"],
                    )
                )
            if occupied:
                records(r, "resource_intervals").append(
                    dict(
                        activity_id=aid,
                        owner_id=owner,
                        job_id=task["id"],
                        start_ps=0,
                        end_ps=0,
                        activity=phase,
                        limiting_resource_id=owner,
                        service_start_ps_ratio=None,
                        service_end_ps_ratio=None,
                    )
                )
    r.update(
        job_hash=j.job_hash,
        engine=raw["engine"],
        scope=raw["workload_closure"]["scope"]["kind"],
        admission=raw["admission"],
        fidelity_detail=raw["fidelity_detail"],
        owners=raw["owners"],
        duration_ps=0,
        completed_jobs=[t["id"] for t in graph["jobs"]],
        traffic_counts=traffic,
        unrepresented=["SYNTHETIC-ZERO-STRUCTURAL-SHELL-NOT-MODEL-EVIDENCE"],
    )
    r["counts"].update(
        memory_read_bytes=float(traffic["read_payload_bytes"]),
        memory_write_bytes=float(traffic["write_payload_bytes"]),
    )
    r["busy_time_ps"] = [dict(owner_id=o.owner_id, busy_time_ps=0) for o in j.owners]
    r["attribution_ps"] = {k: 0 for k in r["attribution_ps"]}
    r["simulator_metrics"].update(
        event_count=len(records(r, "events")), completed_job_count=len(graph["jobs"])
    )
    return j, seal(r)


@pytest.mark.parametrize(
    "case, fault",
    [
        ("D13-barrier", "owner"),
        ("D13-barrier", "request"),
        ("D13-hop", "owner"),
        ("D13-hop", "request"),
    ],
)
def test_barrier_unicast_structural_bindings(case: Any, fault: Any) -> None:
    j, r = zero_transport_shell(case)
    validate_result(r, j)
    a = next(a for a in records(r, "activities") if a["subphase"] in ("barrier", "unicast_noc"))
    if fault == "request":
        a["request_id"] = "FORGED"
    else:
        owner = next(o.owner_id for o in j.owners if o.resource == "dma_port:0")
        a["owner_id"] = owner
        for e in records(r, "events"):
            if e["observation_ordinal"] in (a["dispatch_ordinal"], a["completion_ordinal"]):
                e["target_id"] = owner
        for row in records(r, "resource_intervals"):
            if row["activity_id"] == a["activity_id"]:
                row["owner_id"] = row["limiting_resource_id"] = owner
    code = "InvalidResource" if case == "D13-hop" and fault == "owner" else "IncompleteObservations"
    with pytest.raises(ValueError, match="^" + code + "(:|$)"):
        validate_result(seal(r), j)
    validate_result(zero_transport_shell(case)[1], j)


def test_missing_makespan_activity_is_a_public_refusal() -> None:
    j, r = sample()
    r["duration_ps"] += 1
    last = records(r, "critical_path")[-1]
    last["end_ps"] += 1
    r["attribution_ps"][last["category"]] += 1
    with pytest.raises(ValueError, match="^AttributionMismatch: missing makespan activity$"):
        validate_result(seal(r), j)


def test_phase_outside_declared_task_is_a_public_refusal() -> None:
    j, r = sample()
    act(r, "out")["subphase"] = "compute_wave"
    with pytest.raises(ValueError, match="^IncompleteObservations: phase inventory$"):
        validate_result(seal(r), j)
