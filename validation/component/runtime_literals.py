"""Closed frozen-literal vocabulary; input premises are not output measurements."""

from typing import Any

from rkuarch.verification.component.checks import need

METADATA = frozenset({"premise", "native_status", "representation"})
INPUTS = frozenset({"capacity_bytes", "required_accumulator_bytes", "accumulator_bytes"})
OUTPUTS = frozenset(
    """outcome duration_ps attribution_ps useful_ops issued_ops
read_payload_bytes write_payload_bytes read_transaction_bytes write_transaction_bytes
unicast_payload_bytes sram_read_bytes sram_write_bytes hbm_payload_bytes useful_floor_ps
reservation_ps issue_ps complete_ps max_inflight final_inflight response_ps job_times_ps
job_ready_ps barrier_ready_ps transient_bacc channel_end_ps channel_end_ratios crossings_ps
opportunities opportunity_cursor_time credit_causes fragments payload_bytes transaction_bytes
tile_durations_ps forbidden_serial_duration_ps wrong_alignment_ps""".split()
)


def check_extended_literals(
    job: dict[str, Any], result: dict[str, Any], expected: dict[str, Any]
) -> None:
    need(not (set(expected) - METADATA - INPUTS - OUTPUTS), "unknown expectation keys")
    graph = job["mapped_point"]["task_graph"]
    hardware = job["workload_closure"]["hardware_spec"]
    buffers = graph["buffers"]
    allocations = {a["buffer_id"]: a for a in result["observations"]["allocations"]["records"]}
    for key in ("accumulator_bytes", "required_accumulator_bytes"):
        if key in expected:
            acc = [b for b in buffers if b["space"] == "accumulator"]
            need(len(acc) == 1 and acc[0]["size_bytes"] == expected[key], "input literal " + key)
            need(
                allocations[acc[0]["id"]]["size_bytes"] == expected[key],
                "allocation literal " + key,
            )
    if "capacity_bytes" in expected:
        boundary = next(b for b in buffers if b["id"] == "zz-boundary")
        space = boundary["space"]
        capacity = (
            hardware["memory"]["dram"]["capacity_bytes"]
            if space == "hbm"
            else hardware["cores"]["core_type"]["sram"]["bytes"]
        )["value"]
        need(capacity == expected["capacity_bytes"], "input literal capacity_bytes")
        a = allocations[boundary["id"]]
        need(a["offset_bytes"] + a["size_bytes"] == capacity, "allocation capacity boundary")
    obs = result["observations"]
    dma = sorted(
        (d for d in obs["dma"]["records"] if d["direction"] != "unicast"),
        key=lambda d: d["request_id"],
    )
    if "fragments" in expected:
        owners = {o["owner_id"]: o["resource"] for o in job["owners"]}
        channels = {
            a["request_id"]: int(owners[a["owner_id"]].split(":")[1])
            for a in obs["activities"]["records"]
            if a["kind"] == "service" and a["subphase"] == "channel_service"
        }
        need(
            [[channels[d["request_id"]], d["payload_bytes"], d["transaction_bytes"]] for d in dma]
            == expected["fragments"],
            "literal fragments",
        )
    for key in ("payload_bytes", "transaction_bytes"):
        if key in expected:
            need(sum(d[key] for d in dma) == expected[key], "literal " + key)
            counts = result["traffic_counts"]
            need(
                counts["read_" + key] + counts["write_" + key] == expected[key],
                "traffic literal " + key,
            )
    if "tile_durations_ps" in expected:
        tasks = {t["id"] for t in graph["jobs"] if t["kind"] == "compute"}
        rows = sorted(
            (r for r in obs["jobs"]["records"] if r["job_id"] in tasks), key=lambda r: r["job_id"]
        )
        need(
            [r["end_ps"] - r["start_ps"] for r in rows] == expected["tile_durations_ps"],
            "literal tile_durations_ps",
        )
    for key in ("forbidden_serial_duration_ps", "wrong_alignment_ps"):
        if key in expected:
            need(result["duration_ps"] != expected[key], "forbidden literal " + key)
