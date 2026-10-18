"""Independent input/transition witnesses. No carrier validator or timing engine calls."""

from collections import defaultdict
from typing import Any

from validation.component.checks import need
from validation.component.issue_checks import credit_predecessors


def phase_binding(j: dict[str, Any], a: Any) -> tuple[str, str, str | None, bool]:
    g = j["mapped_point"]["task_graph"]
    t = next(t for t in g["jobs"] if t["id"] == a["job_id"])
    core = j["workload_closure"]["hardware_spec"]["cores"]
    cols = int(core["grid"]["cols"]["value"])
    engines = int(core["core_type"]["dma"]["engines"]["value"])
    domain: str | None
    p = a["subphase"]
    if t["kind"] == "compute":
        owner, category, domain, occupied = f"matrix:{t['core_id']}", "compute", "core", True
        if p == "compute_overhead":
            category = "overhead"
    elif t["kind"] == "barrier":
        owner, category, domain, occupied = f"barrier:{t['id']}", "sync", "noc", False
    else:
        if t["kind"] == "dma":
            f = next(f for f in t["fragments"] if f["request_id"] == a["request_id"])
            core_id, route_id = t["dma_engine_id"] // engines, f["route_id"]
        else:
            b = next(b for b in g["buffers"] if b["id"] == t["source"]["buffer_id"])
            core_id, route_id = b["core_id"], t["route_id"]
        if p == "dma_issue":
            engine = t["dma_engine_id"]
            owner, category, domain, occupied = (
                f"dma:{engine // engines}:{engine % engines}",
                "memory",
                "core",
                False,
            )
        elif p.endswith("_noc"):
            route = next(r for r in g["routes"] if r["id"] == route_id)
            owner, category, domain, occupied = (
                f"router:0:{core_id // cols}:{core_id % cols}",
                "noc",
                "noc",
                len(route["core_ids"]) > 1,
            )
        elif p in ("dram_latency", "channel_service"):
            owner, category, domain, occupied = (
                f"channel:{f['channel_id']}",
                "memory",
                "dram" if p == "dram_latency" else None,
                p == "channel_service",
            )
        else:
            owner, category, domain, occupied = f"dma_port:{core_id}", "memory", "core", p != "ack"
    return owner, category, domain, occupied and a["kind"] == "service"


def check_transitions(j: dict[str, Any], r: dict[str, Any], expanded: list[list[Any]]) -> None:
    obs = r["observations"]
    tasks = {t["id"]: t for t in j["mapped_point"]["task_graph"]["jobs"]}
    jobs = {x["job_id"]: x for x in obs["jobs"]["records"]}
    acts = {a["activity_id"]: a for a in obs["activities"]["records"]}
    owners = {x["resource"]: x["owner_id"] for x in j["owners"]}
    hardware = j["workload_closure"]["hardware_spec"]["cores"]
    engines = int(hardware["core_type"]["dma"]["engines"]["value"])
    requests = {x["request_id"]: x for x in obs["dma"]["records"] if x["direction"] != "unicast"}
    deps: dict[str, list[str]] = defaultdict(list)
    for edge in j["mapped_point"]["task_graph"]["dependencies"]:
        deps[edge["after"]].append(edge["before"])
    firsts: dict[str, list[Any]] = defaultdict(list)
    lasts: dict[str, list[Any]] = defaultdict(list)
    eligible: dict[str, set[tuple[str, str]]] = {key: set() for key in acts}

    def cause(before: Any, after: Any, relation: str) -> None:
        if before["end_ps"] == after["start_ps"]:
            eligible[after["activity_id"]].add((before["activity_id"], relation))

    for seq in expanded:
        firsts[seq[0]["job_id"]].append(seq[0])
        lasts[seq[-1]["job_id"]].append(seq[-1])
        for before, after in zip(seq, seq[1:], strict=False):
            cause(before, after, "sequence")
    # Resource predecessors are derived at acquisition, never inferred from claimed links.
    acquisitions: dict[int, list[tuple[Any, Any]]] = defaultdict(list)
    for seq in expanded:
        if tasks[seq[0]["job_id"]]["kind"] == "compute":
            acquisitions[seq[0]["owner_id"]].append((seq[0], seq[-1]))
        for a in seq:
            if a["kind"] == "service" and a["subphase"] in (
                "channel_service",
                "read_port",
                "write_port",
            ):
                index = seq.index(a)
                first = seq[index - 1] if index and seq[index - 1]["kind"] == "alignment" else a
                acquisitions[a["owner_id"]].append((first, a))
    for pairs in acquisitions.values():
        pairs.sort(key=lambda pair: (pair[0]["start_ps"], pair[0]["dispatch_ordinal"]))
        for (_, before), (after, _) in zip(pairs, pairs[1:], strict=False):
            cause(before, after, "resource")
    for tid, starts in firsts.items():
        for start in starts:
            for predecessor in deps[tid]:
                for end in lasts[predecessor]:
                    if end["end_ps"] == jobs[predecessor]["end_ps"]:
                        cause(end, start, "dependency")
    limit = int(hardware["core_type"]["dma"]["max_outstanding"]["value"])
    request_ends = {seq[-1]["request_id"]: seq[-1] for seq in expanded}
    reservation_cursors = {
        req: opportunity["event_cursor"]
        for opportunity in obs["reservation_opportunities"]["records"]
        for req in opportunity["granted_request_ids"]
    }
    terminal_ordinals = {
        req: end["completion_ordinal"] for req, end in request_ends.items() if req in requests
    }
    for req, row in requests.items():
        first = next(x for x in firsts[row["job_id"]] if x["request_id"] == req)
        for old in credit_predecessors(
            req, requests, jobs, limit, reservation_cursors[req], terminal_ordinals
        ):
            cause(request_ends[old], first, "credit")
    for a in acts.values():
        supplied = [(p["activity_id"], p["relation"]) for p in a["predecessors"]]
        need(
            len(supplied) == len(set(supplied)) and set(supplied) == eligible[a["activity_id"]],
            "complete eligible causes",
        )
    need(
        all(a["start_ps"] == 0 or eligible[a["activity_id"]] for a in acts.values()),
        "actual nonzero-start cause",
    )
    # Explicit DAG verification includes all off-chain zero-duration links.
    pending = set(acts)
    while pending:
        ready = {key for key in pending if not any(p in pending for p, _ in eligible[key])}
        need(bool(ready), "causal activity cycle")
        pending -= ready
    for tid, t in tasks.items():
        row = jobs[tid]
        if t["kind"] == "dma":
            owner = owners[f"dma:{t['dma_engine_id'] // engines}:{t['dma_engine_id'] % engines}"]
        else:
            owner = firsts[tid][0]["owner_id"]
        need(row["owner_id"] == owner, "job owner binding")
        need(row["release_ps"] == 0, "job release binding")
        need(row["blocking_predecessor_ids"] == [], "unrepresented job blockers")
        need(
            row["ready_ps"] == max((jobs[p]["end_ps"] for p in deps[tid]), default=0),
            "job dependency readiness",
        )
        need(
            (row["start_ps"], row["end_ps"])
            == (min(a["start_ps"] for a in firsts[tid]), max(a["end_ps"] for a in lasts[tid])),
            "job transition endpoints",
        )
    need(
        all(c["predecessor_id"] is None for c in obs["critical_path"]["records"]),
        "unrepresented critical predecessor",
    )
    events = {e["observation_ordinal"]: e for e in obs["events"]["records"]}
    endpoints = []
    for a in acts.values():
        kinds = (
            ("TASK_READY", "DEPENDENCY_READY")
            if a["kind"] == "alignment"
            else {
                "compute_overhead": ("OWNER_GRANT", "COMPUTE_DONE"),
                "compute_stage": ("OWNER_GRANT", "COMPUTE_DONE"),
                "compute_wave": ("OWNER_GRANT", "COMPUTE_DONE"),
                "compute_drain": ("OWNER_GRANT", "COMPUTE_DONE"),
                "dma_issue": ("TASK_READY", "DMA_ISSUE"),
                "read_port": ("OWNER_GRANT", "DMA_DONE"),
                "write_port": ("OWNER_GRANT", "MEM_RESP"),
                "dram_latency": ("MEM_REQ", "MEM_RESP"),
                "channel_service": ("MEM_REQ", "MEM_RESP"),
                "request_noc": ("NOC_HEAD", "NOC_TAIL"),
                "response_noc": ("NOC_HEAD", "NOC_TAIL"),
                "unicast_noc": ("NOC_HEAD", "NOC_TAIL"),
                "ack": ("TASK_READY", "DMA_DONE"),
                "barrier": ("SYNC_ARRIVE", "BARRIER_RELEASE"),
            }[a["subphase"]]
        )
        for field, time, kind in zip(
            ("dispatch_ordinal", "completion_ordinal"),
            (a["start_ps"], a["end_ps"]),
            kinds,
            strict=True,
        ):
            endpoints.append(a[field])
            e = events.get(a[field])
            need(
                e is not None
                and (e["kind"], e["job_id"], e["target_id"], e["t_ps"])
                == (kind, a["job_id"], a["owner_id"], time),
                "event transition binding",
            )
    need(
        len(endpoints) == len(set(endpoints)) and set(endpoints) == events.keys(),
        "event endpoint inventory",
    )
