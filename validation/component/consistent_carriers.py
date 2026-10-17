"""Finite synthetic controls and consistent attacks. Never generated native results.

The synchronizer copies joined values, never computes correct service timing or causes.
Tests supply literal times and predecessor edges; resealing is integrity, not authority.
"""

from copy import deepcopy
from typing import Any

from uarch_contract.hashing import content_hash

from validation.component.checks import union_time
from validation.component.synthetic_carrier import (
    synthetic_job,
    synthetic_port_pair,
    synthetic_resident_result,
    synthetic_result,
)

EXPECTED = dict(unrepresented=["SYNTHETIC-unit-carrier-only"])


def activity(result: Any, name: Any) -> Any:
    return next(
        a for a in result["observations"]["activities"]["records"] if a["activity_id"] == name
    )


def seal(result: Any) -> Any:
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    return result


def synchronize(result: Any) -> Any:
    """Copy supplied activity times/owners into all joined tables, then reseal."""
    obs = result["observations"]
    acts = {a["activity_id"]: a for a in obs["activities"]["records"]}

    def tie(a: Any) -> Any:
        return a["owner_id"], a["job_id"], a["request_id"] or "", a["subphase"], a["activity_id"]

    for resource in obs["resource_intervals"]["records"]:
        a = acts[resource["activity_id"]]
        for k in ("owner_id", "job_id", "start_ps", "end_ps"):
            resource[k] = a[k]
        resource["limiting_resource_id"] = a["owner_id"]
    obs["resource_intervals"]["records"] = [
        x
        for x in obs["resource_intervals"]["records"]
        if acts[x["activity_id"]]["occupies_resource"]
    ]
    for row in result["busy_time_ps"]:
        row["busy_time_ps"] = union_time(
            (a["start_ps"], a["end_ps"])
            for a in obs["resource_intervals"]["records"]
            if a["owner_id"] == row["owner_id"]
        )
    for row in obs["clocks"]["records"]:
        a = acts[row["activity_id"]]
        row.update(
            grant_ps=a["start_ps"],
            completion_ps=a["end_ps"],
            aligned_start_ps=a["end_ps"] if a["kind"] == "alignment" else a["start_ps"],
        )
    requests = {x["request_id"]: x for x in obs["dma"]["records"]}
    for req, row in requests.items():
        row["complete_ps"] = max(a["end_ps"] for a in acts.values() if a["request_id"] == req)
        if row["direction"] != "unicast":
            row["credit_release_ps"] = row["complete_ps"]
    for row in obs["jobs"]["records"]:
        row["end_ps"] = max(a["end_ps"] for a in acts.values() if a["job_id"] == row["job_id"])
    result["duration_ps"] = max(x["end_ps"] for x in obs["jobs"]["records"])
    for row in obs["queue_membership"]["records"]:
        if row["activity_id"] is not None:
            a = acts[row["activity_id"]]
            row.update(
                owner_id=a["owner_id"],
                queue_id=f"activity:{a['subphase']}:{a['owner_id']}",
                enter_ps=a["ready_ps"] if row["population"] == "waiting" else a["start_ps"],
                leave_ps=a["start_ps"] if row["population"] == "waiting" else a["end_ps"],
            )
        elif row["queue_id"].startswith("dma_inflight:"):
            row["enter_ps"] = requests[row["item_id"]]["issue_ps"]
            row["leave_ps"] = requests[row["item_id"]]["complete_ps"]
        else:
            a = next(
                a
                for a in acts.values()
                if a["request_id"] == row["item_id"] and a["subphase"] == "channel_service"
            )
            row.update(
                enter_ps=a["ready_ps"] if row["population"] == "waiting" else a["start_ps"],
                leave_ps=a["start_ps"] if row["population"] == "waiting" else a["end_ps"],
            )
    for row in obs["transfers"]["records"]:
        phases = {
            "dram": ("dram_latency", "channel_service"),
            "core_port": ("read_port", "read_port"),
        }.get(row["boundary_id"], (row["boundary_id"], row["boundary_id"]))
        relevant = [a for a in acts.values() if a["request_id"] == row["request_id"]]
        first = [a for a in relevant if a["subphase"] == phases[0]]
        row["enter_ps"] = next(
            (a["ready_ps"] for a in first if a["kind"] == "alignment"), first[0]["ready_ps"]
        )
        row["leave_ps"] = max(a["end_ps"] for a in relevant if a["subphase"] == phases[1])
    # Order the supplied event graph. This repairs ordinal joins even for swapped port grants.
    events = {x["observation_ordinal"]: x for x in obs["events"]["records"]}
    pending: dict[Any, Any] = {}
    for a in acts.values():
        d, c = a["dispatch_ordinal"], a["completion_ordinal"]
        for ordinal, time in ((d, a["start_ps"]), (c, a["end_ps"])):
            events[ordinal].update(t_ps=time, target_id=a["owner_id"], job_id=a["job_id"])
        pending[d] = {acts[p["activity_id"]]["completion_ordinal"] for p in a["predecessors"]}
        pending[c] = {d}
    order: list[Any] = []
    while pending:
        candidates = [k for k, deps in pending.items() if not deps.intersection(pending)]
        assert candidates, "synthetic event cycle"
        key = min(candidates, key=lambda k: (events[k]["t_ps"], k))
        order.append(key)
        del pending[key]
    renumber = {old: new for new, old in enumerate(order)}
    for a in acts.values():
        for field in ("dispatch_ordinal", "completion_ordinal"):
            a[field] = renumber[a[field]]
    for old, e in events.items():
        e["event_seq"] = e["observation_ordinal"] = renumber[old]
    obs["events"]["records"] = [events[k] for k in order]
    # Canonical path over the SUPPLIED causes, including forgeries. No eligibility oracle here.
    current = min((a for a in acts.values() if a["end_ps"] == result["duration_ps"]), key=tie)
    chain, seen = [], set()
    while True:
        assert current["activity_id"] not in seen
        seen.add(current["activity_id"])
        if current["end_ps"] > current["start_ps"]:
            chain.append(current)
        if not current["predecessors"]:
            break
        current = min((acts[p["activity_id"]] for p in current["predecessors"]), key=tie)
    critical: list[Any] = []
    totals = dict(compute=0, memory=0, noc=0, sync=0, overhead=0)
    for a in reversed(chain):
        critical.append(
            dict(
                kind="service",
                start_ps=a["start_ps"],
                end_ps=a["end_ps"],
                cause_job_id=a["job_id"],
                predecessor_id=None,
                limiting_resource_id=a["owner_id"],
                category=a["category"],
                activity_id=a["activity_id"],
            )
        )
        totals[a["category"]] += a["end_ps"] - a["start_ps"]
    obs["critical_path"]["records"] = critical
    result["attribution_ps"] = totals
    return seal(result)


def control(case: Any = "D01") -> Any:
    j = synthetic_job(case)
    r = (
        synthetic_port_pair(j)
        if case == "D08"
        else synthetic_resident_result(j)
        if case == "C02"
        else synthetic_result(j)
    )
    events = {e["observation_ordinal"]: e for e in r["observations"]["events"]["records"]}
    for a in r["observations"]["activities"]["records"]:
        if a["kind"] == "alignment":
            kinds = ("TASK_READY", "DEPENDENCY_READY")
        elif a["subphase"].startswith("compute_"):
            kinds = ("OWNER_GRANT", "COMPUTE_DONE")
        elif a["subphase"].endswith("_noc"):
            kinds = ("NOC_HEAD", "NOC_TAIL")
        elif a["subphase"] == "read_port":
            kinds = ("OWNER_GRANT", "DMA_DONE")
        else:
            kinds = ("MEM_REQ", "MEM_RESP")
        for field, kind in zip(("dispatch_ordinal", "completion_ordinal"), kinds, strict=True):
            events[a[field]]["kind"] = kind
    return j, synchronize(r)


def attack(name: Any) -> Any:
    case = (
        "D10-read"
        if name == "M1"
        else "D08"
        if name in ("M3", "V1", "V2", "port_overlap", "port_reverse")
        else "D01"
    )
    j, r = control(case)
    if name == "M1":
        activity(r, "back-a")["category"] = "memory"
    elif name == "M2":
        activity(r, "out")["owner_id"] = next(
            o.owner_id for o in j.owners if o.resource == "dma_port:0"
        )
    elif name == "M3":
        activity(r, "r1:back-a")["predecessors"] = []
    elif name == "V1":
        activity(r, "r1:port")["predecessors"].append(
            dict(activity_id="r0:port", relation="credit")
        )
    elif name == "V2":
        activity(r, "r0:port-a")["predecessors"] = [dict(activity_id="r1:back", relation="credit")]
    elif name in ("M4a", "M4b"):
        activity(r, "channel")["occupies_resource"] = False
        if name == "M4b":
            activity(r, "channel")["end_ps"] = 54500
            activity(r, "back-a").update(ready_ps=54500, start_ps=54500)
    elif name in ("port_overlap", "port_reverse"):
        # Both requests arrive at the shared read port at 59000; each needs 1000 ps.
        activity(r, "r1:port-a").update(
            start_ps=59000,
            end_ps=59000,
            predecessors=[dict(activity_id="r1:back", relation="sequence")],
        )
        activity(r, "r1:port").update(ready_ps=59000, start_ps=59000, end_ps=60000)
        if name == "port_overlap":
            for prefix in ("r0:", "r1:"):
                activity(r, prefix + "port")["occupies_resource"] = False
        else:
            activity(r, "r0:port-a").update(
                start_ps=60000,
                end_ps=60000,
                predecessors=[dict(activity_id="r1:port", relation="resource")],
            )
            activity(r, "r0:port").update(ready_ps=60000, start_ps=60000, end_ps=61000)
            # Add the now nonempty r00 wait (r01's old wait is allowed to become empty).
            q = deepcopy(
                next(
                    x
                    for x in r["observations"]["queue_membership"]["records"]
                    if x["activity_id"] == "r0:port-a"
                )
            )
            q["population"] = "waiting"
            r["observations"]["queue_membership"]["records"].append(q)
    else:
        raise ValueError(name)
    for a in r["observations"]["activities"]["records"]:
        a["predecessors"].sort(key=lambda p: (p["activity_id"], p["relation"]))
    return j, synchronize(r)


def pair_control(case: Any) -> Any:
    """Two finite same-channel/credit witnesses, using independent literal worksheets."""
    j = synthetic_job(case)
    r = synthetic_port_pair(j)
    # Normalize endpoint kinds with the already explicit D08 table, by activity identity.
    _, template = control("D08")
    kinds = {
        a["activity_id"]: tuple(
            next(
                e["kind"]
                for e in template["observations"]["events"]["records"]
                if e["observation_ordinal"] == a[k]
            )
            for k in ("dispatch_ordinal", "completion_ordinal")
        )
        for a in template["observations"]["activities"]["records"]
    }
    events = {e["observation_ordinal"]: e for e in r["observations"]["events"]["records"]}
    for a in r["observations"]["activities"]["records"]:
        for k, kind in zip(
            ("dispatch_ordinal", "completion_ordinal"), kinds[a["activity_id"]], strict=True
        ):
            events[a[k]]["kind"] = kind
    if case == "D05-two":
        activity(r, "r1:channel").update(
            start_ps=54250,
            end_ps=56500,
            predecessors=[dict(activity_id="r0:channel", relation="resource")],
        )
        activity(r, "r1:back-a").update(ready_ps=56500, start_ps=56500, end_ps=57000)
        activity(r, "r1:back").update(ready_ps=57000, start_ps=57000, end_ps=61000)
        activity(r, "r1:port-a").update(
            ready_ps=61000,
            start_ps=61000,
            end_ps=61000,
            predecessors=[dict(activity_id="r1:back", relation="sequence")],
        )
        activity(r, "r1:port").update(ready_ps=61000, start_ps=61000, end_ps=62000)
        for x in r["observations"]["resource_intervals"]["records"]:
            if x["activity_id"] == "r1:channel":
                x.update(
                    service_start_ps_ratio=dict(numerator=3851744, denominator=71),
                    service_end_ps_ratio=dict(numerator=4011488, denominator=71),
                )
    elif case == "D05-one":
        _, first = control()
        literals = {a["activity_id"]: a for a in first["observations"]["activities"]["records"]}
        for a in r["observations"]["activities"]["records"]:
            if a["activity_id"].startswith("r1:"):
                original = literals[a["activity_id"][3:]]
                for key in ("ready_ps", "start_ps", "end_ps"):
                    a[key] = original[key] + 60000
                a["predecessors"] = [
                    dict(activity_id="r1:" + p["activity_id"], relation=p["relation"])
                    for p in original["predecessors"]
                ]
        activity(r, "r1:out-a")["predecessors"] = [dict(activity_id="r0:port", relation="credit")]
        r["observations"]["dma"]["records"][1].update(issue_ps=60000, credit_acquire_ps=60000)
        r["observations"]["jobs"]["records"][1]["start_ps"] = 60000
        for x in r["observations"]["resource_intervals"]["records"]:
            if x["activity_id"] == "r1:channel":
                x.update(
                    service_start_ps_ratio=dict(numerator=112000, denominator=1),
                    service_end_ps_ratio=dict(numerator=8111744, denominator=71),
                )
    else:
        raise ValueError(case)
    return j, synchronize(r)


def mechanism_attack(name: Any) -> Any:
    j, r = control()
    if name == "duration":
        activity(r, "port")["end_ps"] = 61000
        r["observations"]["clocks"]["records"][-1]["n_cycles"] = 2
        return j, synchronize(r)
    if name == "carry":
        res = next(
            x
            for x in r["observations"]["resource_intervals"]["records"]
            if x["activity_id"] == "channel"
        )
        res.update(
            service_start_ps_ratio=dict(numerator=5199999, denominator=100),
            service_end_ps_ratio=dict(numerator=385174329, denominator=7100),
        )
    elif name == "rational":
        res = next(
            x
            for x in r["observations"]["resource_intervals"]["records"]
            if x["activity_id"] == "channel"
        )
        res["service_end_ps_ratio"] = dict(numerator=54250, denominator=1)
    elif name == "busy":
        next(x for x in r["busy_time_ps"] if x["busy_time_ps"])["busy_time_ps"] += 1
    elif name == "null_floor":
        r["u_c0_duration_ps"] = 1
    elif name == "fidelity":
        r["fidelity_detail"]["compute"] = 2
    elif name == "diagnostic":
        r["diagnostics"]["energy_pj"] = 0
    elif name == "unrepresented":
        r["unrepresented"] = []
    elif name == "critical":
        r["observations"]["critical_path"]["records"][-1]["predecessor_id"] = "r00"
    elif name == "job_owner":
        r["observations"]["jobs"]["records"][0]["owner_id"] = activity(r, "channel")["owner_id"]
    elif name == "release":
        r["observations"]["jobs"]["records"][0]["release_ps"] = 50000
    elif name == "blockers":
        r["observations"]["jobs"]["records"][0]["blocking_predecessor_ids"] = ["r00"]
    elif name == "event":
        r["observations"]["events"]["records"][-1]["kind"] = "STAT_SAMPLE"
    elif name.startswith("queue_"):
        q = next(
            x
            for x in r["observations"]["queue_membership"]["records"]
            if x["population"] == "inflight"
        )
        if name == "queue_clock":
            q["clock_domain"] = "core"
        if name == "queue_owner":
            q["owner_id"] = activity(r, "port")["owner_id"]
        if name == "queue_engine":
            q["queue_id"] = "dma_inflight:1"
        if name == "queue_population":
            q["population"] = "service"
    else:
        raise ValueError(name)
    return j, seal(r)


def extra_attack(name: Any) -> Any:
    if name == "channel_fifo":
        j, r = pair_control("D05-two")
        acts = r["observations"]["activities"]["records"]
        old = {a["activity_id"]: deepcopy(a) for a in acts}
        old_res = {
            a["activity_id"]: deepcopy(a)
            for a in r["observations"]["resource_intervals"]["records"]
        }
        for a in acts:
            if a["subphase"] in ("channel_service", "response_noc", "read_port"):
                other = ("r1:" if a["activity_id"].startswith("r0:") else "r0:") + a["activity_id"][
                    3:
                ]
                for key in ("ready_ps", "start_ps", "end_ps", "predecessors"):
                    a[key] = deepcopy(old[other][key])
                for link in a["predecessors"]:
                    key = link["activity_id"]
                    link["activity_id"] = ("r1:" if key.startswith("r0:") else "r0:") + key[3:]
        for res in r["observations"]["resource_intervals"]["records"]:
            if res["activity"] == "channel_service":
                other = ("r1:" if res["activity_id"].startswith("r0:") else "r0:") + "channel"
                for key in ("service_start_ps_ratio", "service_end_ps_ratio"):
                    res[key] = old_res[other][key]
        return j, synchronize(r)
    j, r = control()
    if name == "readiness":
        activity(r, "port")["ready_ps"] = 58999
        q = deepcopy(
            next(
                q
                for q in r["observations"]["queue_membership"]["records"]
                if q["activity_id"] == "port"
            )
        )
        q.update(population="waiting", enter_ps=58999, leave_ps=59000)
        r["observations"]["queue_membership"]["records"].append(q)
        return j, synchronize(r)
    if name == "critical_partition":
        r["observations"]["critical_path"]["records"].pop(0)
    elif name == "allocation_lifetime":
        j, r = control("C02")
        next(a for a in r["observations"]["allocations"]["records"] if a["space"] == "accumulator")[
            "allocate_ps"
        ] = 1
    elif name == "channel_population":
        q = next(
            q
            for q in r["observations"]["queue_membership"]["records"]
            if q["queue_id"].startswith("channel_service:") and q["population"] == "waiting"
        )
        q["leave_ps"] = 52001
    elif name == "ordinary_population":
        q = next(
            q
            for q in r["observations"]["queue_membership"]["records"]
            if q["activity_id"] == "port"
        )
        q["clock_domain"] = None
    else:
        raise ValueError(name)
    return j, seal(r)


def zero_hop_control() -> Any:
    """D14: two reads, then a dependent same-core unicast at exactly 61000 ps."""
    j = synthetic_job("D14")
    r = synthetic_port_pair(j)
    _, normalized = control("D08")
    for e, template in zip(
        r["observations"]["events"]["records"],
        normalized["observations"]["events"]["records"],
        strict=True,
    ):
        e["kind"] = template["kind"]
    # D14 NoC is 1.2 GHz: request 3334, DRAM edge 4000, response 58334.
    # The 1 GHz port receives at 59000; the second grant and zero hop remain 61000.
    for prefix in ("r0:", "r1:"):
        activity(r, prefix + "out")["end_ps"] = 3334
        activity(r, prefix + "lat-a").update(ready_ps=3334, start_ps=3334, end_ps=4000)
        activity(r, prefix + "back")["end_ps"] = 58334
        activity(r, prefix + "port-a")["ready_ps"] = 58334
    activity(r, "r0:port-a")["start_ps"] = 58334
    obs = r["observations"]
    owner = next(o.owner_id for o in j.owners if o.resource == "router:0:0:0")
    n = len(obs["events"]["records"])
    a = dict(
        activity_id="zero",
        job_id="c",
        request_id="c",
        subphase="unicast_noc",
        kind="service",
        ready_ps=61000,
        start_ps=61000,
        end_ps=61000,
        owner_id=owner,
        category="noc",
        receiving_domain="noc",
        occupies_resource=False,
        dispatch_ordinal=n,
        completion_ordinal=n + 1,
        predecessors=[dict(activity_id="r1:port", relation="dependency")],
    )
    obs["activities"]["records"].append(a)
    for ordinal, kind in [(n, "NOC_HEAD"), (n + 1, "NOC_TAIL")]:
        obs["events"]["records"].append(
            dict(
                event_seq=ordinal,
                observation_ordinal=ordinal,
                t_ps=61000,
                phase=1,
                target_id=owner,
                kind=kind,
                job_id="c",
            )
        )
    row = deepcopy(obs["jobs"]["records"][1])
    row.update(job_id="c", ready_ps=61000, start_ps=61000, end_ps=61000, owner_id=owner)
    obs["jobs"]["records"].append(row)
    obs["dma"]["records"].append(
        dict(
            request_id="c",
            job_id="c",
            dma_engine_id=None,
            direction="unicast",
            source_buffer_id="ss",
            destination_buffer_id="sd",
            payload_bytes=256,
            transaction_bytes=0,
            credit_acquire_ps=None,
            issue_ps=61000,
            complete_ps=61000,
            credit_release_ps=None,
            route_id="r0",
        )
    )
    obs["transfers"]["records"].append(
        dict(
            request_id="c",
            boundary_id="unicast_noc",
            direction="unicast",
            payload_bytes=256,
            transaction_bytes=0,
            enter_ps=61000,
            leave_ps=61000,
        )
    )
    obs["queue_membership"]["records"].append(
        dict(
            queue_id=f"activity:unicast_noc:{owner}",
            item_id="c",
            population="service",
            enter_ps=61000,
            leave_ps=61000,
            owner_id=owner,
            clock_domain="noc",
            activity_id="zero",
        )
    )
    r["completed_jobs"] = ["a", "b", "c"]
    r["traffic_counts"]["unicast_payload_bytes"] = 256
    r["ext_counts"]["sram_read_bytes"] += 256
    r["ext_counts"]["sram_write_bytes"] += 256
    r["simulator_metrics"].update(event_count=n + 2, completed_job_count=3)
    return j, synchronize(r)


def barrier_control() -> Any:
    """D13 barrier: max(60000, 62000) plus 32 NoC cycles = 94000 ps."""
    j = synthetic_job("D13-barrier")
    _, r = pair_control("D05-two")
    r["job_hash"] = j.job_hash
    r["admission"] = j.admission.model_dump(mode="json")
    r["owners"] = [o.model_dump(mode="json") for o in j.owners]
    owner = next(o.owner_id for o in j.owners if o.resource == "barrier:z")
    r["busy_time_ps"].append(dict(owner_id=owner, busy_time_ps=0))
    obs = r["observations"]
    for name, kind, end, ncycles, kinds, predecessor in [
        (
            "barrier-a",
            "alignment",
            62000,
            0,
            ("TASK_READY", "DEPENDENCY_READY"),
            dict(activity_id="r1:port", relation="dependency"),
        ),
        (
            "barrier",
            "service",
            94000,
            32,
            ("SYNC_ARRIVE", "BARRIER_RELEASE"),
            dict(activity_id="barrier-a", relation="sequence"),
        ),
    ]:
        n = len(obs["events"]["records"])
        obs["activities"]["records"].append(
            dict(
                activity_id=name,
                job_id="z",
                request_id=None,
                subphase="barrier",
                kind=kind,
                ready_ps=62000,
                start_ps=62000,
                end_ps=end,
                owner_id=owner,
                category="sync",
                receiving_domain="noc",
                occupies_resource=False,
                dispatch_ordinal=n,
                completion_ordinal=n + 1,
                predecessors=[predecessor],
            )
        )
        for ordinal, time, eventkind in [(n, 62000, kinds[0]), (n + 1, end, kinds[1])]:
            obs["events"]["records"].append(
                dict(
                    event_seq=ordinal,
                    observation_ordinal=ordinal,
                    t_ps=time,
                    phase=1,
                    target_id=owner,
                    kind=eventkind,
                    job_id="z",
                )
            )
        obs["clocks"]["records"].append(
            dict(
                activity_id=name,
                job_id="z",
                domain="noc",
                grant_ps=62000,
                n_cycles=ncycles,
                raw_edge_outcome="success",
                aligned_start_ps=62000,
                completion_ps=end,
            )
        )
        obs["queue_membership"]["records"].append(
            dict(
                queue_id=f"activity:barrier:{owner}",
                item_id="z",
                population="service",
                enter_ps=62000,
                leave_ps=end,
                owner_id=owner,
                clock_domain="noc",
                activity_id=name,
            )
        )
    row = deepcopy(obs["jobs"]["records"][1])
    row.update(job_id="z", ready_ps=62000, start_ps=62000, end_ps=94000, owner_id=owner)
    obs["jobs"]["records"].append(row)
    r["completed_jobs"] = ["r00", "r01", "z"]
    r["simulator_metrics"].update(event_count=len(obs["events"]["records"]), completed_job_count=3)
    return j, synchronize(r)
