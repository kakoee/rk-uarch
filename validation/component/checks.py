"""B-owned observation checks; no predicted telemetry and no execution authority.

Raw mappings let these checks diagnose mutations independently of schema admission.
The public result consumer first parses the real installed carrier, then calls these.
All intervals are half-open. At window start, inventory is immediately before events
at start; arrivals/departures at start count in the window, events at end do not.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any

Row = Mapping[str, Any]


class CheckFailure(ValueError):
    pass


def need(ok: bool, detail: str) -> None:
    if not ok:
        raise CheckFailure(detail)


def unique(rows: Sequence[Row], key: str) -> dict[Any, Row]:
    result = {x[key]: x for x in rows}
    need(len(result) == len(rows), f"duplicate {key}")
    return result


def union_time(intervals: Iterable[tuple[int, int]]) -> int:
    cursor, total = 0, 0
    for start, end in sorted(intervals):
        need(0 <= start <= end, "invalid interval")
        total += max(0, end - max(cursor, start))
        cursor = max(cursor, end)
    return total


def queue_window(
    intervals: Iterable[tuple[int, int | None]], start: int, end: int
) -> tuple[int, Fraction]:
    need(0 <= start < end, "empty queue window")
    area = 0
    for enter, leave in intervals:
        need(enter >= 0 and (leave is None or leave >= enter), "queue residence")
        area += max(0, min(end, end if leave is None else leave) - max(start, enter))
    return area, Fraction(area, end - start)


def conservation(
    intervals: Iterable[tuple[int, int, int]], start: int, end: int
) -> tuple[int, int, int, int]:
    need(0 <= start < end, "empty conservation window")
    initial = issued = completed = final = 0
    for enter, leave, amount in intervals:
        need(0 <= enter <= leave and amount >= 0, "invalid transfer interval")
        initial += amount * (enter < start <= leave)
        issued += amount * (start <= enter < end)
        completed += amount * (start <= leave < end)
        final += amount * (enter < end <= leave)
    need(final == initial + issued - completed, "conservation")
    return initial, issued, completed, final


def check_work(jobs: Sequence[Row], rows: Sequence[Row]) -> tuple[int, int]:
    declared, observed = unique(jobs, "id"), unique(rows, "job_id")
    need(declared.keys() == observed.keys(), "completed job inventory")
    useful = issued = 0
    for key, job in declared.items():
        row = observed[key]
        u = i = 0
        if job["kind"] == "compute":
            d, p = job["tile_extents"], job["physical_extents"]
            u, i = 2 * d["M"] * d["K"] * d["N"], 2 * p["M"] * p["K"] * p["N"]
            for field in ("op_id", "group_id", "repeat_index", "tile_origin", "tile_extents"):
                need(row[field] == job[field], f"work {field} {key}")
        need(
            (
                row["useful_matrix_ops"],
                row["issued_matrix_ops"],
                row["vector_arithmetic_ops"],
                row["cast_ops"],
            )
            == (u, i, 0, 0),
            f"work {key}",
        )
        useful += u
        issued += i
    return useful, issued


def check_credits(rows: Sequence[Row], limit: int) -> None:
    need(limit > 0, "credit limit")
    unique(rows, "request_id")
    engines: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r in rows:
        if r["dma_engine_id"] is None:
            need(
                r["credit_acquire_ps"] is None and r["credit_release_ps"] is None, "unicast credit"
            )
            continue
        need(
            r["credit_acquire_ps"] == r["issue_ps"] <= r["complete_ps"] == r["credit_release_ps"],
            "credit lifecycle",
        )
        need(r["complete_ps"] > r["issue_ps"], "DMA positive lifetime")
        engines[r["dma_engine_id"]].extend([(r["issue_ps"], 1), (r["complete_ps"], -1)])
    for events in engines.values():
        live = 0
        for _, delta in sorted(events):  # commit/release precedes same-edge acquisition
            live += delta
            need(0 <= live <= limit, "credit capacity")
        need(live == 0, "final credit inventory")


def check_allocations(
    rows: Sequence[Row],
    capacities: Mapping[tuple[str, int], int],
    job_ends: Mapping[str, int],
    duration: int,
) -> None:
    unique(rows, "buffer_id")
    groups: dict[tuple[str, int], list[Row]] = defaultdict(list)
    for r in rows:
        key = r["space"], r["owner_id"]
        need(
            key in capacities
            and 0 <= r["offset_bytes"]
            and 0 < r["size_bytes"] <= capacities[key] - r["offset_bytes"],
            "allocation capacity",
        )
        free = duration if r["free_ps"] is None else r["free_ps"]
        need(0 <= r["allocate_ps"] <= free <= duration, "allocation lifetime")
        need(not r["initially_live"] or r["allocate_ps"] == 0, "initial allocation")
        need(
            all(x in job_ends and job_ends[x] <= free for x in r["last_consumer_ids"]),
            "allocation last consumer",
        )
        for old in groups[key]:
            old_free = duration if old["free_ps"] is None else old["free_ps"]
            live_overlap = max(r["allocate_ps"], old["allocate_ps"]) < min(free, old_free)
            address_overlap = max(r["offset_bytes"], old["offset_bytes"]) < min(
                r["offset_bytes"] + r["size_bytes"], old["offset_bytes"] + old["size_bytes"]
            )
            need(not (live_overlap and address_overlap), "allocation live alias")
        groups[key].append(r)


def check_causal_path(
    path: Sequence[Row],
    jobs: Sequence[Row],
    resources: Sequence[Row],
    duration: int,
    attribution: Mapping[str, int],
    categories: Mapping[int, set[str]],
) -> None:
    observed = unique(jobs, "job_id")
    cursor, previous = 0, None
    totals: dict[str, int] = defaultdict(int)
    for p in path:
        a, b, cause, owner = (
            p[x] for x in ("start_ps", "end_ps", "cause_job_id", "limiting_resource_id")
        )
        need(a == cursor and b > a and cause in observed, "causal partition")
        row = observed[cause]
        need(p["kind"] == "service", "component release idle unsupported")
        need(p["category"] in categories.get(owner, set()), "causal category")
        need(
            any(
                r["job_id"] == cause
                and r["owner_id"] == owner
                and r["start_ps"] <= a < b <= r["end_ps"]
                for r in resources
            ),
            "causal service witness",
        )
        need(row["start_ps"] <= a < b <= row["end_ps"], "causal job interval")
        if previous is None:
            need(p["predecessor_id"] is None, "causal initial predecessor")
        elif previous != cause:
            need(
                p["predecessor_id"] == previous
                and previous in row["blocking_predecessor_ids"]
                and observed[previous]["end_ps"] == a,
                "causal predecessor",
            )
        totals[p["category"]] += b - a
        cursor, previous = b, cause
    need(cursor == duration, "causal duration")
    need(
        all(totals[k] == attribution.get(k, 0) for k in totals.keys() | attribution.keys()),
        "causal attribution sum",
    )


def reduce_evidence(states: Sequence[str], *, required: int) -> str:
    if "failed" in states or "surviving_mutant" in states:
        return "failed"
    if required <= 0 or len(states) != required or any(x != "passed" for x in states):
        return "not_run"
    return "passed"


def check_queue_domain(
    row: Row,
    owners: Mapping[int, str],
    requests: Mapping[str, Row],
    engines_per_core: int,
    *,
    allow_nonclocked: bool = False,
) -> None:
    """Prospective nonclocked semantics are opt-in; strict installed parsing still gates use."""
    need(row["owner_id"] in owners, "queue owner")
    reserved = row["queue_id"].startswith(("channel_service:", "dma_inflight:"))
    if row["clock_domain"] is not None:
        need(not reserved, "nonclocked population has ordinary clock")
        need(row["clock_domain"] in ("core", "noc", "dram"), "queue domain")
        return
    need(allow_nonclocked and row["item_id"] in requests, "nonclocked queue not admitted")
    declared = requests[row["item_id"]]
    owner = owners[row["owner_id"]]
    channel, engine = declared["channel_id"], declared["dma_engine_id"]
    channel_ok = (
        row["queue_id"] == f"channel_service:{channel}"
        and owner == f"channel:{channel}"
        and row["population"] in ("waiting", "service")
    )
    credit_ok = (
        row["queue_id"] == f"dma_inflight:{engine}"
        and owner == f"dma:{engine // engines_per_core}:{engine % engines_per_core}"
        and row["population"] == "inflight"
    )
    need(channel_ok or credit_ok, "nonclocked population binding")
