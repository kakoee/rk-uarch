"""Independent checks of prospective component /2 transitions and mechanisms.

No production timing helpers and no scheduling/execution. Validates observed local laws,
resource order, declared inventories, and causal joins after the real carrier validator.
"""

from collections import defaultdict
from fractions import Fraction
from typing import Any

from validation.component.arithmetic import ceil, edge_after
from validation.component.checks import (
    check_allocations,
    check_credits,
    check_work,
    conservation,
    need,
    queue_window,
    union_time,
    unique,
)
from validation.component.phase_laws import channel


def check_v2(j: dict[str, Any], r: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    obs = r["observations"]
    need(obs["format"] == "uarch-native-observations/2", "component observation version")
    g = j["mapped_point"]["task_graph"]
    tasks, jobs = unique(g["jobs"], "id"), unique(obs["jobs"]["records"], "job_id")
    useful, issued = check_work(g["jobs"], obs["jobs"]["records"])
    need(
        (r["counts"]["matrix_ops"], r["work_counts"]["issued_matrix_ops"]) == (useful, issued),
        "work totals",
    )
    need(r["completed_jobs"] == sorted(tasks), "completion inventory")
    need(max(x["end_ps"] for x in jobs.values()) == r["duration_ps"], "job makespan")
    for edge in g["dependencies"]:
        need(
            jobs[edge["before"]]["end_ps"] <= jobs[edge["after"]]["ready_ps"],
            "dependency completion",
        )
    acts = unique(obs["activities"]["records"], "activity_id")
    services: dict[tuple[str, str | None, str], Any] = {}
    aligns: dict[tuple[str, str | None, str], Any] = {}
    for a in acts.values():
        target = services if a["kind"] == "service" else aligns
        key = a["job_id"], a["request_id"], a["subphase"]
        need(key not in target, "duplicate mechanism")
        target[key] = a
        need(
            jobs[a["job_id"]]["start_ps"]
            <= a["ready_ps"]
            <= a["end_ps"]
            <= jobs[a["job_id"]]["end_ps"],
            "phase job lifetime",
        )
    h = j["workload_closure"]["hardware_spec"]
    core, dram = h["cores"]["core_type"], h["memory"]["dram"]

    def val(x: Any) -> int:
        return int(x["value"])

    timing = dram["timing"]
    bandwidth = Fraction(val(dram["bw_bytes_per_s"]), val(dram["channels"])) * Fraction(
        val(timing["t_refi_cycles"]) - val(timing["t_rfc_cycles"]), val(timing["t_refi_cycles"])
    )
    routes = unique(g["routes"], "id")
    requests = unique(obs["dma"]["records"], "request_id")
    declared = {
        f["request_id"]: (t, f)
        for t in tasks.values()
        if t["kind"] == "dma"
        for f in t["fragments"]
    }
    need(
        {k for k, v in requests.items() if v["direction"] != "unicast"} == declared.keys(),
        "declared request inventory",
    )
    check_credits(list(requests.values()), val(core["dma"]["max_outstanding"]))
    phase_specs: dict[tuple[str, str | None, str], tuple[int | None, str | None]] = {}
    sequences = []
    for task in tasks.values():
        tid = task["id"]
        if task["kind"] == "compute":
            d = task["tile_extents"]
            rate = val(core["matrix_engine"]["operand_bytes_per_cycle"])
            parts = [
                ("compute_overhead", 32),
                ("compute_stage", ceil(Fraction(2 * d["M"] * d["K"] + 2 * d["K"] * d["N"], rate))),
                ("compute_wave", 510 + d["M"]),
                ("compute_drain", ceil(Fraction(2 * d["M"] * d["N"], rate))),
            ]
            sequences.append([(tid, None, p) for p, _ in parts])
            phase_specs.update({(tid, None, p): (n, "core") for p, n in parts})
        elif task["kind"] == "barrier":
            phase_specs[tid, None, "barrier"] = (32, "noc")
            sequences.append([(tid, None, "barrier")])
        elif task["kind"] == "noc_transfer":
            hops = len(routes[task["route_id"]]["core_ids"]) - 1
            phase_specs[tid, tid, "unicast_noc"] = (
                hops * val(h["nocs"][0]["router_latency_cycles"]),
                "noc",
            )
            sequences.append([(tid, tid, "unicast_noc")])
        else:
            for f in task["fragments"]:
                req = f["request_id"]
                row = requests[req]
                fields = dict(
                    job_id=tid,
                    dma_engine_id=task["dma_engine_id"],
                    direction=task["direction"],
                    source_buffer_id=task["source"]["buffer_id"],
                    destination_buffer_id=task["destination"]["buffer_id"],
                    payload_bytes=f["payload_bytes"],
                    transaction_bytes=f["transaction_bytes"],
                    route_id=f["route_id"],
                )
                need(all(row[k] == v for k, v in fields.items()), "request input binding")
                hops = len(routes[f["route_id"]]["core_ids"]) - 1
                port = (
                    ceil(Fraction(f["payload_bytes"], val(core["dma"]["bytes_per_cycle"]))),
                    "core",
                )
                for phase in ("request_noc", "response_noc"):
                    phase_specs[tid, req, phase] = (
                        hops * val(h["nocs"][0]["router_latency_cycles"]),
                        "noc",
                    )
                phase_specs[tid, req, "dram_latency"] = (
                    sum(val(timing[x]) for x in ("t_cl_cycles", "t_rcd_cycles", "t_rp_cycles")),
                    "dram",
                )
                phase_specs[tid, req, "channel_service"] = (None, None)
                parts = ["request_noc", "dram_latency", "channel_service", "response_noc"]
                if task["direction"] == "read":
                    phase_specs[tid, req, "read_port"] = port
                    parts.append("read_port")
                else:
                    phase_specs[tid, req, "write_port"] = port
                    phase_specs[tid, req, "ack"] = (0, "core")
                    parts = ["write_port", *parts, "ack"]
                sequences.append([(tid, req, p) for p in parts])
    need(services.keys() == phase_specs.keys(), "complete mechanism inventory")
    clocks = unique(obs["clocks"]["records"], "activity_id")
    expected_clocks = set()
    for key, (cycles, domain) in phase_specs.items():
        a = services[key]
        align = aligns.get(key)
        zero_hop = key[2].endswith("_noc") and cycles == 0
        if domain is None or zero_hop:
            need(align is None, "unclocked or zero-hop alignment")
            if zero_hop:
                need(a["start_ps"] == a["end_ps"] and not a["occupies_resource"], "zero-hop time")
            continue
        need(align is not None, "missing receiving alignment")
        assert align is not None and cycles is not None
        hz = j["freq_hz"][domain]
        need(
            align["end_ps"] == edge_after(hz, align["start_ps"], 0) == a["start_ps"],
            "receiving-clock alignment",
        )
        need(a["end_ps"] == edge_after(hz, a["start_ps"], cycles), "mechanism duration")
        for activity, n in ((align, 0), (a, cycles)):
            expected_clocks.add(activity["activity_id"])
            c = clocks.get(activity["activity_id"])
            need(c is not None, "missing clock witness")
            assert c is not None
            need(
                (
                    c["domain"],
                    c["grant_ps"],
                    c["n_cycles"],
                    c["aligned_start_ps"],
                    c["completion_ps"],
                )
                == (
                    domain,
                    activity["start_ps"],
                    n,
                    edge_after(hz, activity["start_ps"], 0),
                    activity["end_ps"],
                ),
                "clock mechanism binding",
            )
    need(clocks.keys() == expected_clocks, "clock witness inventory")
    need(set(aligns) <= set(phase_specs), "alignment inventory")
    for sequence in sequences:
        tid, req, _ = sequence[0]
        start = requests[req]["issue_ps"] if req in requests else jobs[tid]["start_ps"]
        for key in sequence:
            a = aligns.get(key, services[key])
            need(a["ready_ps"] == start, "phase ready transition")
            start = services[key]["end_ps"]
        if req in requests:
            need(start == requests[req]["complete_ps"], "request completion mechanism")
        else:
            need(start == jobs[tid]["end_ps"], "job completion mechanism")
    owners = {x["owner_id"]: x["resource"] for x in j["owners"]}
    resources = obs["resource_intervals"]["records"]
    groups: dict[int, list[Any]] = defaultdict(list)
    for res in resources:
        groups[res["owner_id"]].append(res)
    for owner, pieces in groups.items():
        if owners[owner].startswith(("matrix:", "dma_port:")):
            ordered = sorted(pieces, key=lambda x: (x["start_ps"], x["end_ps"], x["activity_id"]))
            need(
                all(
                    a["end_ps"] <= b["start_ps"] for a, b in zip(ordered, ordered[1:], strict=False)
                ),
                "exclusive occupied intervals",
            )
        elif owners[owner].startswith("channel:"):
            exact = []
            for res in pieces:
                lo, hi = (
                    Fraction(res[k]["numerator"], res[k]["denominator"])
                    for k in ("service_start_ps_ratio", "service_end_ps_ratio")
                )
                a = acts[res["activity_id"]]
                task, fragment = declared[a["request_id"]]
                channel(lo, hi, fragment["transaction_bytes"], bandwidth)
                exact.append((lo, hi, a))
            previous = Fraction(0)
            for lo, hi, a in sorted(exact, key=lambda x: (x[0], x[2]["request_id"])):
                latency = services[a["job_id"], a["request_id"], "dram_latency"]["end_ps"]
                need(lo == max(Fraction(latency), previous), "rational channel carry/readiness")
                previous = hi
    for busy in r["busy_time_ps"]:
        need(
            busy["busy_time_ps"]
            == union_time((x["start_ps"], x["end_ps"]) for x in groups[busy["owner_id"]]),
            "busy union",
        )
    queues = obs["queue_membership"]["records"]
    keys = [(q["queue_id"], q["item_id"], q["population"], q["activity_id"]) for q in queues]
    need(len(set(keys)) == len(keys), "queue population uniqueness")
    for req, (task, _fragment) in declared.items():
        row = requests[req]
        inflight = [
            q for q in queues if q["queue_id"].startswith("dma_inflight:") and q["item_id"] == req
        ]
        need(
            len(inflight) == 1
            and (inflight[0]["enter_ps"], inflight[0]["leave_ps"])
            == (row["issue_ps"], row["complete_ps"]),
            "inflight lifecycle",
        )
        a = services[task["id"], req, "channel_service"]
        for pop, begin, end in (
            ("waiting", a["ready_ps"], a["start_ps"]),
            ("service", a["start_ps"], a["end_ps"]),
        ):
            matches = [
                q
                for q in queues
                if q["queue_id"].startswith("channel_service:")
                and q["item_id"] == req
                and q["population"] == pop
            ]
            need(
                len(matches) == 1
                and (matches[0]["enter_ps"], matches[0]["leave_ps"]) == (begin, end),
                "channel population lifecycle",
            )
    for a in acts.values():
        if a["receiving_domain"] is not None:
            for population, begin, end in (
                ("service", a["start_ps"], a["end_ps"]),
                ("waiting", a["ready_ps"], a["start_ps"]),
            ):
                matches = [
                    q
                    for q in queues
                    if q["activity_id"] == a["activity_id"] and q["population"] == population
                ]
                # Zero waiting rows are optional; occupied/alignment service rows are explicit.
                need(
                    (
                        len(matches) == 1
                        or (not matches and population == "waiting" and begin == end)
                    )
                    and all(
                        (
                            q["queue_id"],
                            q["item_id"],
                            q["owner_id"],
                            q["clock_domain"],
                            q["enter_ps"],
                            q["leave_ps"],
                        )
                        == (
                            f"activity:{a['subphase']}:{a['owner_id']}",
                            a["request_id"] or a["job_id"],
                            a["owner_id"],
                            a["receiving_domain"],
                            begin,
                            end,
                        )
                        for q in matches
                    ),
                    "ordinary queue exact binding",
                )

    def tie(a: Any) -> tuple[Any, ...]:
        return (a["owner_id"], a["job_id"], a["request_id"] or "", a["subphase"], a["activity_id"])

    terminal = min((a for a in acts.values() if a["end_ps"] == r["duration_ps"]), key=tie)
    chain = []
    seen = set()
    while True:
        need(terminal["activity_id"] not in seen, "causal activity cycle")
        seen.add(terminal["activity_id"])
        if terminal["end_ps"] > terminal["start_ps"]:
            chain.append(terminal)
        predecessors = [acts[p["activity_id"]] for p in terminal["predecessors"]]
        need(all(p["end_ps"] == terminal["start_ps"] for p in predecessors), "tight causal witness")
        if not predecessors:
            need(terminal["start_ps"] == 0, "causal root")
            break
        terminal = min(predecessors, key=tie)
    chain.reverse()
    critical = obs["critical_path"]["records"]
    need(
        [(c["activity_id"], c["start_ps"], c["end_ps"], c["category"]) for c in critical]
        == [(a["activity_id"], a["start_ps"], a["end_ps"], a["category"]) for a in chain],
        "mechanism causal partition",
    )
    cursor = 0
    for a in chain:
        need(a["start_ps"] == cursor, "causal gap")
        cursor = a["end_ps"]
    need(cursor == r["duration_ps"], "causal makespan")
    transfers = obs["transfers"]["records"]
    observed_transfers = {(t["request_id"], t["boundary_id"]): t for t in transfers}
    need(len(observed_transfers) == len(transfers), "transfer uniqueness")
    wanted = set()
    for req, (task, fragment) in declared.items():
        tid = task["id"]
        direction = task["direction"]
        for boundary, phases, payload, txn in [
            (
                "request_noc",
                ["request_noc"],
                fragment["payload_bytes"] if direction == "write" else 0,
                0,
            ),
            (
                "dram",
                ["dram_latency", "channel_service"],
                fragment["payload_bytes"],
                fragment["transaction_bytes"],
            ),
            (
                "response_noc",
                ["response_noc"],
                fragment["payload_bytes"] if direction == "read" else 0,
                0,
            ),
            (
                "core_port",
                ["read_port" if direction == "read" else "write_port"],
                fragment["payload_bytes"],
                0,
            ),
        ]:
            key = req, boundary
            wanted.add(key)
            firstkey = tid, req, phases[0]
            lastkey = tid, req, phases[-1]
            begin = aligns.get(firstkey, services[firstkey])["ready_ps"]
            end = services[lastkey]["end_ps"]
            t = observed_transfers.get(key)
            need(
                t is not None
                and (
                    t["direction"],
                    t["payload_bytes"],
                    t["transaction_bytes"],
                    t["enter_ps"],
                    t["leave_ps"],
                )
                == (direction, payload, txn, begin, end),
                "transfer mechanism binding",
            )
    for task in tasks.values():
        if task["kind"] == "noc_transfer":
            req = task["id"]
            key = req, "unicast_noc"
            wanted.add(key)
            a = services[req, req, "unicast_noc"]
            t = observed_transfers.get(key)
            need(
                t is not None
                and (t["enter_ps"], t["leave_ps"], t["payload_bytes"], t["transaction_bytes"])
                == (jobs[req]["start_ps"], a["end_ps"], task["payload_bytes"], 0),
                "unicast transfer binding",
            )
    need(observed_transfers.keys() == wanted, "transfer boundary inventory")
    allocations = obs["allocations"]["records"]
    need(
        unique(allocations, "buffer_id").keys() == unique(g["buffers"], "id").keys(),
        "allocation inventory",
    )
    capacities = {}
    for a in allocations:
        b = next(x for x in g["buffers"] if x["id"] == a["buffer_id"])
        resource = (
            "channel:0"
            if b["space"] == "hbm"
            else ("matrix:" if b["space"] == "accumulator" else "sram:") + str(b["core_id"])
        )
        need(
            owners[a["owner_id"]] == resource
            and all(a[k] == b[k] for k in ("space", "offset_bytes", "size_bytes")),
            "allocation input binding",
        )
        need(
            a["last_consumer_ids"] == b["final_consumer_ids"]
            and a["initially_live"] == (b["initial_residency"] == "preloaded"),
            "allocation consumer/initial inventory",
        )
        capacity = val(
            dram["capacity_bytes"]
            if b["space"] == "hbm"
            else core["sram"]["bytes"]
            if b["space"] == "sram"
            else core["matrix_engine"]["accumulator_bytes"]
        )
        capacities[b["space"], a["owner_id"]] = capacity
        users = [
            t["id"]
            for t in tasks.values()
            if (
                t["kind"] == "compute"
                and (
                    b["id"] in t["operand_buffers"].values()
                    or b["id"] == t["accumulator_buffer_id"]
                )
            )
            or (
                t["kind"] in ("dma", "noc_transfer")
                and b["id"] in (t["source"]["buffer_id"], t["destination"]["buffer_id"])
            )
        ]
        end = r["duration_ps"] if a["free_ps"] is None else a["free_ps"]
        need(
            all(a["allocate_ps"] <= jobs[u]["start_ps"] <= jobs[u]["end_ps"] <= end for u in users),
            "allocation access lifetime",
        )
        if b["space"] == "accumulator":
            transient = (
                j["workload_closure"]["mapping_policy"]["version"] == "2"
                and b["producer_id"] is not None
            )
            need(
                (a["allocate_ps"], end)
                == (
                    (
                        jobs[b["producer_id"]]["start_ps"],
                        max(jobs[u]["end_ps"] for u in b["final_consumer_ids"]),
                    )
                    if transient
                    else (0, r["duration_ps"])
                ),
                "accumulator lifetime mechanism",
            )
    check_allocations(
        allocations, capacities, {k: v["end_ps"] for k, v in jobs.items()}, r["duration_ps"]
    )
    need(r["unrepresented"] == expected["unrepresented"], "unrepresented paths")
    need(
        r["u_c0_duration_ps"] is None
        and r["fidelity_detail"] == dict(compute=1, noc=0, dram=0, sync="exact", layer_reuse=False),
        "fidelity/null floor",
    )
    windows = {}
    for t in transfers:
        windows[str((t["request_id"], t["boundary_id"]))] = conservation(
            [(t["enter_ps"], t["leave_ps"], t["payload_bytes"])], 0, r["duration_ps"] + 1
        )
    areas = {
        str(k): queue_window([(q["enter_ps"], q["leave_ps"])], 0, r["duration_ps"] or 1)
        for k, q in zip(keys, queues, strict=True)
    }
    return dict(conservation_windows=windows, queue_areas=areas)
