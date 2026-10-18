"""Independent /3 reservation witness checks; no engine or carrier-validator imports."""

from typing import Any

from validation.component.arithmetic import edge_after
from validation.component.checks import need


def credit_predecessors(
    req: str,
    rows: dict[str, Any],
    jobs: dict[str, Any],
    limit: int,
    reservation_cursor: int,
    terminal_ordinals: dict[str, int],
) -> set[str]:
    """All eligible same-time releases, not exclusive assignment of a freed slot.

    Saturation includes pending reservations. A credit cause must have been acquired
    and its terminal observed strictly before this reservation opportunity, including
    releases before earlier opportunities at the same time. Dispatch is not the cursor.
    """
    row = rows[req]
    time = row["reservation_ps"]
    occupied = {
        key: old
        for key, old in rows.items()
        if key != req
        and old["dma_engine_id"] == row["dma_engine_id"]
        and old["reservation_ps"] < time <= old["complete_ps"]
    }
    if time <= jobs[row["job_id"]]["ready_ps"] or len(occupied) != limit:
        return set()
    return {
        key
        for key, old in occupied.items()
        if old["issue_ps"] < time
        and old["complete_ps"] == time
        and terminal_ordinals[key] < reservation_cursor
    }


def check_reservation_opportunities(
    rows: dict[str, Any],
    jobs: dict[str, Any],
    limit: int,
    opportunities: list[Any],
    events: list[Any],
    job_ends: dict[str, int],
    request_ends: dict[str, int],
    dependencies: dict[str, list[str]],
) -> None:
    """Check observed eligibility transitions, without executing payload mechanisms.

    Job terminal completion and credit release are checked against endpoint positions,
    not just equal timestamps or the claimed reservation/alignment order.
    """
    need(
        [e["observation_ordinal"] for e in events] == list(range(len(events))),
        "opportunity endpoint inventory",
    )
    # Initial opportunity plus exactly the terminal-sequence transitions. Scheduled
    # phase0 completions drain together; inline completions each create a new epoch.
    expected_boundaries = {(0, 0)}
    for ordinal in set(job_ends.values()) | set(request_ends.values()):
        need(0 <= ordinal < len(events), "opportunity terminal endpoint")
        event = events[ordinal]
        cursor = ordinal + 1
        if event["phase"] == 0:
            while (
                cursor < len(events)
                and events[cursor]["phase"] == 0
                and events[cursor]["t_ps"] == event["t_ps"]
            ):
                cursor += 1
        else:
            need(event["phase"] == 2, "opportunity terminal phase")
        expected_boundaries.add((cursor, event["t_ps"]))
    expected = sorted(expected_boundaries)
    need(len(opportunities) == len(expected), "opportunity transition inventory")
    granted: set[str] = set()
    for index, (opportunity, (cursor, time)) in enumerate(
        zip(opportunities, expected, strict=True)
    ):
        need(
            (opportunity["opportunity_ordinal"], opportunity["event_cursor"], opportunity["t_ps"])
            == (index, cursor, time),
            "opportunity transition binding",
        )
        occupied: dict[int, int] = {}
        for request in granted:
            # Prior reservations hold capacity through pending and acquired states.
            # Only a terminal completion already observed at this cursor releases it.
            if request_ends[request] >= cursor:
                engine = rows[request]["dma_engine_id"]
                occupied[engine] = occupied.get(engine, 0) + 1
        eligible = sorted(
            (
                request
                for request, row in rows.items()
                if request not in granted
                and jobs[row["job_id"]]["ready_ps"] <= time
                and all(job_ends[p] < cursor for p in dependencies.get(row["job_id"], []))
            ),
            key=lambda request: (
                jobs[rows[request]["job_id"]]["ready_ps"],
                rows[request]["dma_engine_id"],
                request,
            ),
        )
        wanted = []
        for request in eligible:
            engine = rows[request]["dma_engine_id"]
            if occupied.get(engine, 0) < limit:
                wanted.append(request)
                occupied[engine] = occupied.get(engine, 0) + 1
        need(
            opportunity["granted_request_ids"] == wanted, "opportunity eligible grants / ready tie"
        )
        for request in wanted:
            need(
                rows[request]["reservation_ps"] == time and request_ends[request] >= cursor,
                "opportunity reservation endpoint",
            )
        granted.update(wanted)
    need(granted == rows.keys(), "opportunity complete request inventory")


def check_issue(j: dict[str, Any], r: dict[str, Any]) -> None:
    need(
        j["engine"]["model"]["name"] == "native-intervals"
        and j["engine"]["model"]["version"] == "2",
        "issue model version",
    )
    obs = r["observations"]
    jobs = {x["job_id"]: x for x in obs["jobs"]["records"]}
    tasks = {x["id"]: x for x in j["mapped_point"]["task_graph"]["jobs"]}
    rows = {x["request_id"]: x for x in obs["dma"]["records"] if x["direction"] != "unicast"}
    acts = obs["activities"]["records"]
    events = {x["observation_ordinal"]: x for x in obs["events"]["records"]}
    queues = obs["queue_membership"]["records"]
    owners = {x["owner_id"]: x["resource"] for x in j["owners"]}
    dma = j["workload_closure"]["hardware_spec"]["cores"]["core_type"]["dma"]
    limit, engines = int(dma["max_outstanding"]["value"]), int(dma["engines"]["value"])
    need(
        all(
            x["reservation_ps"] is None
            for x in obs["dma"]["records"]
            if x["direction"] == "unicast"
        ),
        "unicast reservation absent",
    )
    job_ends = {
        key: max(a["completion_ordinal"] for a in acts if a["job_id"] == key) for key in tasks
    }
    request_ends = {
        key: max(a["completion_ordinal"] for a in acts if a["request_id"] == key) for key in rows
    }
    dependencies: dict[str, list[str]] = {}
    for edge in j["mapped_point"]["task_graph"]["dependencies"]:
        dependencies.setdefault(edge["after"], []).append(edge["before"])
    check_reservation_opportunities(
        rows,
        jobs,
        limit,
        obs["reservation_opportunities"]["records"],
        obs["events"]["records"],
        job_ends,
        request_ends,
        dependencies,
    )
    for req, row in rows.items():
        task = tasks[row["job_id"]]
        members = [
            a
            for a in acts
            if a["job_id"] == task["id"] and a["request_id"] == req and a["subphase"] == "dma_issue"
        ]
        alignment = [a for a in members if a["kind"] == "alignment"]
        service = [a for a in members if a["kind"] == "service"]
        need(len(alignment) == len(service) == 1, "issue inventory including zero alignment")
        a, b = alignment[0], service[0]
        need(
            (a["ready_ps"], a["start_ps"], a["end_ps"])
            == (jobs[task["id"]]["ready_ps"], row["reservation_ps"], row["issue_ps"]),
            "reservation alignment endpoints",
        )
        need(
            row["issue_ps"] == edge_after(j["freq_hz"]["core"], row["reservation_ps"], 0),
            "earliest issue edge / no issue rate cap",
        )
        need(
            (b["ready_ps"], b["start_ps"], b["end_ps"]) == (row["issue_ps"],) * 3,
            "atomic issue conversion",
        )
        need(
            row["credit_acquire_ps"] == row["issue_ps"]
            and row["credit_release_ps"] == row["complete_ps"],
            "acquired not pending lifecycle",
        )
        need(
            a["completion_ordinal"] < b["dispatch_ordinal"] < b["completion_ordinal"],
            "issue endpoint order",
        )
        need(
            events[a["dispatch_ordinal"]]["phase"]
            == events[b["dispatch_ordinal"]]["phase"]
            == events[b["completion_ordinal"]]["phase"]
            == 2,
            "issue phase2 ordering",
        )
        need(
            events[a["completion_ordinal"]]["phase"] == (0 if a["end_ps"] > a["start_ps"] else 2),
            "issue alignment completion phase",
        )
        for prefix, pop, lo, hi in [
            ("dma_waiting", "waiting", jobs[task["id"]]["ready_ps"], row["reservation_ps"]),
            ("dma_pending", "pending", row["reservation_ps"], row["issue_ps"]),
            ("dma_inflight", "inflight", row["issue_ps"], row["complete_ps"]),
        ]:
            matches = [
                q
                for q in queues
                if q["item_id"] == req and q["queue_id"] == f"{prefix}:{row['dma_engine_id']}"
            ]
            need(len(matches) == 1, "three issue population inventory")
            q = matches[0]
            need(
                (q["population"], q["enter_ps"], q["leave_ps"], q["clock_domain"], q["activity_id"])
                == (pop, lo, hi, None, None),
                "issue population lifecycle",
            )
            engine = row["dma_engine_id"]
            need(
                owners[q["owner_id"]] == f"dma:{engine // engines}:{engine % engines}",
                "issue population engine",
            )
    allocations = {a["buffer_id"]: a for a in obs["allocations"]["records"]}
    for buf in j["mapped_point"]["task_graph"]["buffers"]:
        persistent = buf["producer_id"] is None or (
            buf["space"] == "accumulator"
            and j["workload_closure"]["mapping_policy"]["version"] == "1"
        )
        if not persistent:
            a = allocations[buf["id"]]
            end = max((jobs[x]["end_ps"] for x in buf["final_consumer_ids"]), default=None)
            need(
                (a["allocate_ps"], a["free_ps"]) == (jobs[buf["producer_id"]]["start_ps"], end),
                "reservation producer allocation endpoints",
            )
