"""Literal expectations for saved historical model-2 observations; no source gates."""
from fractions import Fraction
from typing import Any

from rkuarch.verification.component.checks import need
from validation.component.runtime_literals import check_extended_literals


def assert_literals(job: dict[str, Any], result: dict[str, Any], expected: dict[str, Any]) -> None:
    check_extended_literals(job, result, expected)
    need(expected["outcome"] == "success", "expected refusal cannot consume success")
    obs = result["observations"]
    dma = sorted(obs["dma"]["records"], key=lambda r: r["request_id"])
    # New reservation/issue/complete triples describe DMA credits only. Historical
    # issue/complete vectors without reservation_ps retain their original population,
    # including D14's unicast. Null unicast reservations are never a DMA credit.
    if "reservation_ps" in expected:
        dma = [r for r in dma if r["direction"] != "unicast"]
    for key in ("duration_ps", "attribution_ps"):
        if key in expected:
            need(result[key] == expected[key], "literal " + key)
    for key, section, field in [
        ("useful_ops", "counts", "matrix_ops"),
        ("issued_ops", "work_counts", "issued_matrix_ops"),
    ]:
        if key in expected:
            need(result[section][field] == expected[key], "literal " + key)
    for section, fields in [
        (
            "traffic_counts",
            (
                "read_payload_bytes",
                "write_payload_bytes",
                "read_transaction_bytes",
                "write_transaction_bytes",
                "unicast_payload_bytes",
            ),
        ),
        ("ext_counts", ("sram_read_bytes", "sram_write_bytes")),
    ]:
        for field in fields:
            if field in expected:
                need(result[section][field] == expected[field], "literal " + field)
    if "hbm_payload_bytes" in expected:
        need(
            result["traffic_counts"]["read_payload_bytes"]
            + result["traffic_counts"]["write_payload_bytes"]
            == expected["hbm_payload_bytes"],
            "literal HBM payload",
        )
    if "useful_floor_ps" in expected:
        need(result["duration_ps"] >= expected["useful_floor_ps"], "component floor")
    for key in ("reservation_ps", "issue_ps", "complete_ps"):
        if key in expected:
            need([r[key] for r in dma] == expected[key], "literal " + key)
    if "max_inflight" in expected or "final_inflight" in expected:
        credits = [r for r in obs["dma"]["records"] if r["credit_acquire_ps"] is not None]

        def population(t: int) -> int:
            return sum(r["credit_acquire_ps"] <= t < r["credit_release_ps"] for r in credits)

        if "max_inflight" in expected:
            need(
                max((population(r["credit_acquire_ps"]) for r in credits), default=0)
                == expected["max_inflight"],
                "literal maximum acquired credits",
            )
        if "final_inflight" in expected:
            need(
                population(result["duration_ps"]) == expected["final_inflight"],
                "literal terminal acquired credits",
            )
    if "response_ps" in expected:
        responses = {
            a["request_id"]: a["end_ps"]
            for a in obs["activities"]["records"]
            if a["subphase"] == "response_noc" and a["kind"] == "service"
        }
        need(
            [responses[r["request_id"]] for r in dma] == expected["response_ps"],
            "literal port-contention response endpoints",
        )
    jobs = obs["jobs"]["records"]
    if "job_times_ps" in expected:
        need(
            {j["job_id"]: [j["start_ps"], j["end_ps"]] for j in jobs} == expected["job_times_ps"],
            "literal job spans",
        )
    if "job_ready_ps" in expected:
        need(
            {j["job_id"]: j["ready_ps"] for j in jobs} == expected["job_ready_ps"],
            "literal readiness",
        )
    if "barrier_ready_ps" in expected:
        barriers = {
            j["id"] for j in job["mapped_point"]["task_graph"]["jobs"] if j["kind"] == "barrier"
        }
        need(
            [j["ready_ps"] for j in jobs if j["job_id"] in barriers]
            == [expected["barrier_ready_ps"]],
            "literal barrier readiness",
        )
    if "transient_bacc" in expected:
        rows = [a for a in obs["allocations"]["records"] if a["buffer_id"] == "bacc"]
        need(
            len(rows) == 1
            and [rows[0]["allocate_ps"], rows[0]["free_ps"]] == expected["transient_bacc"],
            "literal complete-final-consumer lifetime",
        )
    owners = {r["owner_id"]: r["resource"] for r in job["owners"]}
    channels = sorted(
        (
            r
            for r in obs["resource_intervals"]["records"]
            if owners[r["owner_id"]].startswith("channel:") and r["service_end_ps_ratio"]
        ),
        key=lambda r: Fraction(
            r["service_end_ps_ratio"]["numerator"], r["service_end_ps_ratio"]["denominator"]
        ),
    )
    if "channel_end_ps" in expected:
        need(
            [r["end_ps"] for r in channels] == expected["channel_end_ps"],
            "literal channel ceilings",
        )
    if "channel_end_ratios" in expected:
        need(
            [
                [r["service_end_ps_ratio"]["numerator"], r["service_end_ps_ratio"]["denominator"]]
                for r in channels
            ]
            == expected["channel_end_ratios"],
            "literal rational carry",
        )
    if "crossings_ps" in expected:
        need(len(dma) == 1, "crossing exact request")
        phases = {
            a["subphase"]: a
            for a in obs["activities"]["records"]
            if a["request_id"] == dma[0]["request_id"] and a["kind"] == "service"
        }
        port, arrival, latency, channel, response, done = expected["crossings_ps"]
        need(
            [
                phases[k]["end_ps"]
                for k in ("request_noc", "dram_latency", "channel_service", "response_noc")
            ]
            == [arrival, latency, channel, response],
            "literal request-bound crossings",
        )
        if port:
            need(phases["write_port"]["end_ps"] == port, "literal write port")
        need(dma[0]["complete_ps"] == done, "literal commit/ack")
    ops = obs["reservation_opportunities"]["records"]
    if "opportunities" in expected:
        need(
            [[o["event_cursor"], o["t_ps"], o["granted_request_ids"]] for o in ops]
            == expected["opportunities"],
            "literal opportunities",
        )
    if "opportunity_cursor_time" in expected:
        need(
            [[o["event_cursor"], o["t_ps"]] for o in ops] == expected["opportunity_cursor_time"],
            "literal opportunity cursor/time",
        )
    if "credit_causes" in expected:
        activities = {a["activity_id"]: a for a in obs["activities"]["records"]}
        causes = {
            a["job_id"]: sorted(
                [
                    [
                        activities[p["activity_id"]]["job_id"],
                        activities[p["activity_id"]]["subphase"],
                    ]
                    for p in a["predecessors"]
                    if p["relation"] == "credit"
                ]
            )
            for a in activities.values()
            if a["subphase"] == "dma_issue" and a["kind"] == "alignment"
        }
        need(causes == expected["credit_causes"], "literal a1 release attribution sets")
