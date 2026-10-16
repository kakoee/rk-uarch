"""Consume actual installed component results; no runner or result fabrication.

Call validate_result at the public boundary first. This additional independent checker
reads inputs only for declared inventory, then checks completed observations against it.
It cannot confer native execution authority or a U-REVIEW verdict.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any

from uarch_contract.mapped import MappedEngineJob, MappedEngineResult, validate_result

from validation.component.arithmetic import edge_after
from validation.component.checks import (
    check_allocations,
    check_causal_path,
    check_credits,
    check_queue_domain,
    check_work,
    conservation,
    need,
    queue_window,
    union_time,
    unique,
)


def check_observations(
    job: MappedEngineJob, result: MappedEngineResult, expected: dict[str, Any]
) -> dict[str, Any]:
    """Return finite-window diagnostics only; no pass receipt or inferred physical cause."""
    r = result.model_dump(mode="json")
    j = job.model_dump(mode="json")
    if r["observations"].get("format") == "uarch-native-observations/2":
        from validation.component.observations_v2 import check_v2

        return check_v2(j, r, expected)
    need(j["state_model"] == "resource_intervals/1", "component state model")
    g = j["mapped_point"]["task_graph"]
    obs = r["observations"]
    need(
        all(
            obs[k]["status"] == "observed"
            for k in (
                "events",
                "jobs",
                "dma",
                "transfers",
                "allocations",
                "queue_membership",
                "resource_intervals",
                "critical_path",
            )
        ),
        "required observations",
    )
    duration = r["duration_ps"]
    need(
        r["simulator_metrics"]["event_count"] == len(obs["events"]["records"])
        and r["simulator_metrics"]["completed_job_count"] == len(obs["jobs"]["records"]),
        "observed metric inventory",
    )
    jobs, records = g["jobs"], obs["jobs"]["records"]
    observed = unique(records, "job_id")
    useful, issued = check_work(jobs, records)
    need(r["completed_jobs"] == sorted(observed), "completed IDs")
    need(
        r["counts"]["matrix_ops"] == useful
        and r["work_counts"]["completed_mac_count"] * 2 == useful
        and r["work_counts"]["issued_matrix_ops"] == issued,
        "completed work totals",
    )
    need(
        all(
            0 <= x["release_ps"] <= x["ready_ps"] <= x["start_ps"] <= x["end_ps"] <= duration
            for x in records
        ),
        "job ordering",
    )
    need(max(x["end_ps"] for x in records) == duration, "makespan")
    completion_kinds = {"COMPUTE_DONE", "DMA_DONE", "NOC_TAIL", "BARRIER_RELEASE", "TASK_RELEASE"}
    for record in records:
        need(
            any(
                e["job_id"] == record["job_id"]
                and e["t_ps"] == record["end_ps"]
                and e["kind"] in completion_kinds
                for e in obs["events"]["records"]
            ),
            "missing completion event",
        )
    if obs.get("clocks", {}).get("status") == "observed":
        for clock in obs["clocks"]["records"]:
            need(clock["raw_edge_outcome"] == "success", "unexpected component clock overflow")
            hz = j["freq_hz"][clock["domain"]]
            need(
                clock["aligned_start_ps"] == edge_after(hz, clock["grant_ps"], 0)
                and clock["completion_ps"] == edge_after(hz, clock["grant_ps"], clock["n_cycles"]),
                "clock edge observation",
            )
    declared_ops = {x["op_id"] for x in jobs if x["kind"] == "compute"}
    per_op = unique(r["per_op"], "op_id")
    need(per_op.keys() == declared_ops, "per-op inventory")
    for op, report in per_op.items():
        op_records = [x for x in records if x["op_id"] == op]
        need(
            report["counts"]["matrix_ops"] == sum(x["useful_matrix_ops"] for x in op_records)
            and report["work_counts"]["issued_matrix_ops"]
            == sum(x["issued_matrix_ops"] for x in op_records),
            "per-op work",
        )
    deps = {(x["before"], x["after"]) for x in g["dependencies"]}
    for before, after in deps:
        need(observed[before]["end_ps"] <= observed[after]["ready_ps"], "dropped dependency")
    for record in records:
        for predecessor in record["blocking_predecessor_ids"]:
            need(
                predecessor in observed and observed[predecessor]["end_ps"] <= record["start_ps"],
                "blocking predecessor time",
            )
            need(
                (predecessor, record["job_id"]) in deps
                or observed[predecessor]["owner_id"] == record["owner_id"]
                or bool(
                    {
                        x["owner_id"]
                        for x in obs["resource_intervals"]["records"]
                        if x["job_id"] == predecessor
                    }
                    & {
                        x["owner_id"]
                        for x in obs["resource_intervals"]["records"]
                        if x["job_id"] == record["job_id"]
                    }
                ),
                "blocking predecessor cause",
            )
    requests = unique(obs["dma"]["records"], "request_id")
    declared = {f["request_id"]: (x, f) for x in jobs if x["kind"] == "dma" for f in x["fragments"]}
    actual = {k: v for k, v in requests.items() if v["direction"] != "unicast"}
    need(actual.keys() == declared.keys(), "DMA inventory")
    for key, (task, fragment) in declared.items():
        row = actual[key]
        fields = dict(
            job_id=task["id"],
            dma_engine_id=task["dma_engine_id"],
            direction=task["direction"],
            source_buffer_id=task["source"]["buffer_id"],
            destination_buffer_id=task["destination"]["buffer_id"],
            payload_bytes=fragment["payload_bytes"],
            transaction_bytes=fragment["transaction_bytes"],
            route_id=fragment["route_id"],
        )
        need(all(row[k] == v for k, v in fields.items()), f"DMA input binding {key}")
        need(
            observed[task["id"]]["start_ps"]
            <= row["issue_ps"]
            <= row["complete_ps"]
            <= observed[task["id"]]["end_ps"],
            "DMA job interval",
        )
    for direction in ("read", "write"):
        for quantity in ("payload", "transaction"):
            field = quantity + "_bytes"
            need(
                r["traffic_counts"][direction + "_" + field]
                == sum(x[field] for x in actual.values() if x["direction"] == direction),
                "traffic totals",
            )
    unicasts = [x for x in requests.values() if x["direction"] == "unicast"]
    declared_unicast = [x for x in jobs if x["kind"] == "noc_transfer"]
    need(len(unicasts) == len(declared_unicast), "unicast inventory")
    for task in declared_unicast:
        matches = [x for x in unicasts if x["job_id"] == task["id"]]
        need(
            len(matches) == 1
            and matches[0]["payload_bytes"] == task["payload_bytes"]
            and matches[0]["source_buffer_id"] == task["source"]["buffer_id"]
            and matches[0]["destination_buffer_id"] == task["destination"]["buffer_id"]
            and matches[0]["route_id"] == task["route_id"],
            "unicast binding",
        )
    need(
        r["traffic_counts"]["unicast_payload_bytes"] == sum(x["payload_bytes"] for x in unicasts),
        "unicast total",
    )
    spec = j["workload_closure"]["hardware_spec"]
    core = spec["cores"]["core_type"]
    check_credits(list(requests.values()), int(core["dma"]["max_outstanding"]["value"]))
    transfers = obs["transfers"]["records"]
    need(
        sorted({x["boundary_id"] for x in transfers}) == expected["transfer_boundaries"],
        "transfer boundary coverage",
    )
    need(
        {
            boundary: sorted(x["request_id"] for x in transfers if x["boundary_id"] == boundary)
            for boundary in expected["transfer_boundaries"]
        }
        == expected["boundary_requests"],
        "boundary request inventory",
    )
    seen = set()
    windows: dict[str, Any] = {}
    for x in transfers:
        key = x["boundary_id"], x["direction"], x["request_id"]
        need(key not in seen and x["request_id"] in requests, "transfer boundary inventory")
        seen.add(key)
        req = requests[x["request_id"]]
        need(
            x["direction"] == req["direction"]
            and x["payload_bytes"] == req["payload_bytes"]
            and x["transaction_bytes"] == req["transaction_bytes"],
            "transfer bytes",
        )
        need(
            req["issue_ps"] <= x["enter_ps"] <= x["leave_ps"] <= req["complete_ps"],
            "transfer lifecycle",
        )
    need({x["request_id"] for x in transfers} == requests.keys(), "missing transfer observation")
    for boundary, direction in {(x["boundary_id"], x["direction"]) for x in transfers}:
        for quantity in ("payload_bytes", "transaction_bytes"):
            for start, end in ((0, duration + 1), (duration // 2, duration + 1)):
                windows[f"{boundary}/{direction}/{quantity}/{start}:{end}"] = conservation(
                    [
                        (x["enter_ps"], x["leave_ps"], x[quantity])
                        for x in transfers
                        if (x["boundary_id"], x["direction"]) == (boundary, direction)
                    ],
                    start,
                    end,
                )
    allocations = obs["allocations"]["records"]
    declared_buffers = unique(g["buffers"], "id")
    need(unique(allocations, "buffer_id").keys() == declared_buffers.keys(), "allocation inventory")
    capacities = {}
    for row in allocations:
        b = declared_buffers[row["buffer_id"]]
        need(
            row["owner_id"] == expected["allocation_owners"][row["buffer_id"]],
            "allocation owner binding",
        )
        need(
            all(row[k] == b[k] for k in ("space", "offset_bytes", "size_bytes")),
            "allocation input binding",
        )
        need(set(row["last_consumer_ids"]) == set(b["final_consumer_ids"]), "consumer inventory")
        if b["initial_residency"] == "preloaded":
            need(row["initially_live"], "resident initial inventory")
        capacity = (
            spec["memory"]["dram"]["capacity_bytes"]
            if b["space"] == "hbm"
            else core["sram"]["bytes"]
            if b["space"] == "sram"
            else core["matrix_engine"]["accumulator_bytes"]
        )
        capacities[b["space"], row["owner_id"]] = int(capacity["value"])
        users = [
            x["id"]
            for x in jobs
            if x["kind"] == "compute"
            and (b["id"] in x["operand_buffers"].values() or b["id"] == x["accumulator_buffer_id"])
        ]
        users += [
            x["id"]
            for x in jobs
            if x["kind"] in ("dma", "noc_transfer")
            and b["id"] in (x["source"]["buffer_id"], x["destination"]["buffer_id"])
        ]
        free = duration if row["free_ps"] is None else row["free_ps"]
        need(
            all(
                row["allocate_ps"] <= observed[x]["start_ps"] and observed[x]["end_ps"] <= free
                for x in users
            ),
            "allocation access lifetime",
        )
    check_allocations(
        allocations, capacities, {k: v["end_ps"] for k, v in observed.items()}, duration
    )
    queue_groups: dict[tuple[str, str, int, str | None], list[tuple[int, int | None]]] = (
        defaultdict(list)
    )
    queue_seen = set()
    for row in obs["queue_membership"]["records"]:
        key = row["queue_id"], row["population"], row["owner_id"], row["clock_domain"]
        item = (*key, row["item_id"], row["enter_ps"])
        need(item not in queue_seen, "duplicate queue residence")
        queue_seen.add(item)
        check_queue_domain(
            row,
            {x["owner_id"]: x["resource"] for x in j["owners"]},
            {
                key: dict(channel_id=fragment["channel_id"], dma_engine_id=task["dma_engine_id"])
                for key, (task, fragment) in declared.items()
            },
            int(core["dma"]["engines"]["value"]),
            allow_nonclocked=expected.get("allow_nonclocked_queues", False),
        )
        need(row["item_id"] in observed or row["item_id"] in requests, "queue item inventory")
        queue_groups[key].append((row["enter_ps"], row["leave_ps"]))
    for req in actual.values():
        need(
            any(
                x["item_id"] == req["request_id"]
                and x["population"] == "inflight"
                and x["enter_ps"] == req["issue_ps"]
                and x["leave_ps"] == req["complete_ps"]
                for x in obs["queue_membership"]["records"]
            ),
            "missing inflight queue",
        )
    for record in records:
        if record["ready_ps"] < record["start_ps"]:
            need(
                any(
                    x["item_id"] == record["job_id"]
                    and x["population"] == "waiting"
                    and x["enter_ps"] == record["ready_ps"]
                    and x["leave_ps"] == record["start_ps"]
                    for x in obs["queue_membership"]["records"]
                ),
                "missing waiting queue",
            )
    # Empty waiting populations are legitimate; service and inflight cannot disappear.
    queue_areas = {str(k): queue_window(v, 0, duration or 1) for k, v in queue_groups.items()}
    resources = obs["resource_intervals"]["records"]
    busy = unique(r["busy_time_ps"], "owner_id")
    owners = {x["owner_id"]: x["resource"] for x in j["owners"]}
    need(busy.keys() == owners.keys(), "busy owner inventory")
    for owner in owners:
        pieces = [(x["start_ps"], x["end_ps"]) for x in resources if x["owner_id"] == owner]
        need(busy[owner]["busy_time_ps"] == union_time(pieces), "busy union")
        # Matrix engines and core ports serialize. NoC0 latency and DMA inflight
        # intervals may overlap; forcing them exclusive would invent contention.
        if owners[owner].startswith(("matrix:", "dma_port:")):
            need(sum(b - a for a, b in pieces) == union_time(pieces), "exclusive owner overlap")
        if owners[owner].startswith("channel:"):
            exact = sorted(
                (
                    Fraction(
                        x["service_start_ps_ratio"]["numerator"],
                        x["service_start_ps_ratio"]["denominator"],
                    ),
                    Fraction(
                        x["service_end_ps_ratio"]["numerator"],
                        x["service_end_ps_ratio"]["denominator"],
                    ),
                )
                for x in resources
                if x["owner_id"] == owner
                and x["service_start_ps_ratio"] is not None
                and x["service_end_ps_ratio"] is not None
            )
            need(
                all(a[1] <= z[0] for a, z in zip(exact, exact[1:], strict=False)),
                "exclusive rational channel service",
            )
    for owner in owners:
        services = [
            (x["enter_ps"], x["leave_ps"])
            for x in obs["queue_membership"]["records"]
            if x["owner_id"] == owner and x["population"] == "service"
        ]
        need(all(b is not None for _, b in services), "unfinished service population")
        need(union_time(services) == busy[owner]["busy_time_ps"], "service queue window")
    for resource in resources:
        need(resource["job_id"] in observed and resource["owner_id"] in owners, "resource binding")
        a, b = resource["service_start_ps_ratio"], resource["service_end_ps_ratio"]
        need((a is None) == (b is None), "rational service pair")
        if a is not None:
            start, end = (
                Fraction(a["numerator"], a["denominator"]),
                Fraction(b["numerator"], b["denominator"]),
            )
            need(
                start <= end
                and -(-start.numerator // start.denominator) == resource["start_ps"]
                and -(-end.numerator // end.denominator) == resource["end_ps"],
                "rational service",
            )
    categories = {int(k): set(v) for k, v in expected["owner_categories"].items()}
    check_causal_path(
        obs["critical_path"]["records"],
        records,
        resources,
        duration,
        r["attribution_ps"],
        categories,
    )
    need(
        r["fidelity_detail"] == dict(compute=1, noc=0, dram=0, sync="exact", layer_reuse=False),
        "fidelity",
    )
    need(r["u_c0_duration_ps"] is None, "component analytic floor null")
    for field in (
        "energy_pj",
        "vector_util_ratio",
        "sram_bank_conflict_stall_ratio",
        "noc_max_link_util_ratio",
        "dram_row_hit_ratio",
    ):
        need(r["diagnostics"][field] is None, "unrepresented diagnostic " + field)
    need(r["unrepresented"] == expected["unrepresented"], "unrepresented paths")
    # Exact frozen field selectors bind every discriminating observation, including category.
    for pointer, value in expected["observations"].items():
        selected: Any = r
        for part in pointer.split("/"):
            selected = selected[int(part)] if isinstance(selected, list) else selected[part]
        need(selected == value, "literal " + pointer)
    return dict(conservation_windows=windows, queue_areas=queue_areas)


def consume(job: MappedEngineJob, raw: object, expected: dict[str, Any]) -> dict[str, Any]:
    return check_observations(job, validate_result(raw, job), expected)
