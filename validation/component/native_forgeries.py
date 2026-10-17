"""Synthetic attacks on saved native output; never relabel a forgery as an engine result."""

from copy import deepcopy
from typing import Any

from uarch_contract.hashing import content_hash

from validation.component.consistent_carriers import synchronize


def forge(raw: dict[str, Any], name: str) -> dict[str, Any]:
    result = deepcopy(raw)
    obs = result["observations"]

    def phase(subphase: str, kind: str = "service") -> Any:
        return next(
            a
            for a in obs["activities"]["records"]
            if a["subphase"] == subphase and a["kind"] == kind
        )

    if name.startswith("o2-"):
        row = next(a for a in obs["allocations"]["records"] if a["buffer_id"] == "bacc")
        field, value = {
            "o2-early-allocation": ("allocate_ps", 0),
            "o2-late-free": ("free_ps", 2735000),
            "o2-persistent": ("free_ps", None),
            "o2-first-consumer": ("free_ps", 1641000),
        }[name]
        row[field] = value
    elif name == "duration-law":
        response, port = phase("response_noc"), phase("read_port", "alignment")
        assert (response["start_ps"], response["end_ps"]) == (55000, 59000)
        response["end_ps"] = 58500
        port.update(ready_ps=58500, start_ps=58500)
        # This repairs only joins to the deliberately false timing; no law is recomputed.
        result = synchronize(result)
    elif name == "missing-occupancy":
        phase("request_noc")["occupies_resource"] = False
        result = synchronize(result)
    elif name == "false-latency-occupancy":
        a = phase("dram_latency")
        a["occupies_resource"] = True
        obs["resource_intervals"]["records"].append(
            dict(
                activity_id=a["activity_id"],
                owner_id=a["owner_id"],
                job_id=a["job_id"],
                start_ps=a["start_ps"],
                end_ps=a["end_ps"],
                activity=a["subphase"],
                limiting_resource_id=a["owner_id"],
                service_start_ps_ratio=None,
                service_end_ps_ratio=None,
            )
        )
        result = synchronize(result)
    elif name == "missing-cause":
        # O2 c starts at b's end, with both dependency and matrix-resource causes.
        a = next(
            a
            for a in obs["activities"]["records"]
            if a["job_id"] == "c"
            and a["subphase"] == "compute_overhead"
            and a["kind"] == "alignment"
        )
        assert {p["relation"] for p in a["predecessors"]} == {"dependency", "resource"}
        a["predecessors"] = [p for p in a["predecessors"] if p["relation"] != "dependency"]
    elif name in ("channel-clock", "dma-clock", "ordinary-clock", "channel-population"):
        prefix = (
            "activity:read_port:"
            if name == "ordinary-clock"
            else ("dma_inflight:" if name == "dma-clock" else "channel_service:")
        )
        row = next(
            q for q in obs["queue_membership"]["records"] if q["queue_id"].startswith(prefix)
        )
        if name == "channel-population":
            row["population"] = "inflight"
        else:
            row["clock_domain"] = None if name == "ordinary-clock" else "dram"
    else:
        raise ValueError("unknown finite native-output forgery: " + name)
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    return result
