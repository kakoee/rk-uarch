"""Independent prospective inputs; no mapper, scheduler, native identity or authority.

Historical corpus/1 bytes are immutable. These are new literal representations.
"""

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

from validation.component.corpus import graph, materialize, resident_input, seal, two_tiles


def reseal(b: dict[str, Any]) -> dict[str, Any]:
    """Content identity only. This cannot update an external trusted profile anchor."""
    for p in b["points"]:
        g = p["task_graph"]
        for key, field in (("buffers", "id"), ("jobs", "id"), ("routes", "id")):
            g[key].sort(key=lambda x: x[field])
        g["dependencies"].sort(key=lambda x: (x["before"], x["after"]))
        seal(g, "graph_hash")
        seal(p, "payload_hash")
    return seal(b, "bundle_hash")


def transient_c04() -> dict[str, Any]:
    b = two_tiles(same_core=True)
    g = graph(b)
    for buf in g["buffers"]:
        if buf["space"] == "accumulator":
            name = "c" if buf["id"] == "acc" else "z"
            buf.update(offset_bytes=0, producer_id=name, final_consumer_ids=[name])
    g["dependencies"] = [dict(before="c", after="z")]
    return b


def pair(n0: int = 255, n1: int = 256, *, ordered: bool = True) -> dict[str, Any]:
    """Two explicit ops, separate SRAM, exact different/equal accumulator footprints."""
    b, second = resident_input(256, 256, n0), resident_input(256, 256, n1)
    g, t = graph(b), graph(second)
    op = deepcopy(second["scope"]["ops"][0])
    op["id"] = "g1"
    b["scope"]["ops"].append(op)
    b["scope"]["op_ids"].append("g1")
    b["points"][0]["identity"]["op_ids"].append("g1")
    for buf in t["buffers"]:
        buf["id"] = "z" + buf["id"]
        buf["op_id"] = "g1" if buf["op_id"] is not None else None
        if buf["space"] == "sram":
            buf["offset_bytes"] += 786432
            buf["bank"] = buf["offset_bytes"] // 524288
        if buf["producer_id"] == "c":
            buf["producer_id"] = "z"
        buf["final_consumer_ids"] = ["z" if x == "c" else x for x in buf["final_consumer_ids"]]
    c = t["jobs"][0]
    c.update(id="z", op_id="g1", accumulator_buffer_id="zacc")
    c["operand_buffers"] = {k: "z" + v for k, v in c["operand_buffers"].items()}
    t["coverage"][0].update(job_id="z", op_id="g1")
    for key in ("buffers", "jobs", "coverage"):
        g[key] += t[key]
    for buf in g["buffers"]:
        if buf["space"] == "accumulator":
            job = "c" if buf["id"] == "acc" else "z"
            buf.update(offset_bytes=0, producer_id=job, final_consumer_ids=[job])
    g["dependencies"] = [dict(before="c", after="z")] if ordered else []
    return b


def prospective_inputs() -> dict[str, Any]:
    definitions = {
        "B2-C04-transient": (transient_c04(), 1855000, 33685504, 393728, 131584),
        "B2-255-256": (pair(), 2364000, 66977792, 523776, 261632),
        "B2-equal": (pair(256, 256), 2364000, 67108864, 524288, 262144),
    }
    result = {
        name: materialize(
            name,
            b,
            dict(
                outcome="success",
                duration_ps=time,
                useful_ops=work,
                sram_read_bytes=read,
                sram_write_bytes=write,
                native_status="not_run",
                representation="prospective transient accumulator",
            ),
        )
        for name, (b, time, work, read, write) in definitions.items()
    }

    for item in result.values():
        b = item["bundle"]
        b["mapping_policy"]["version"] = "2"
        b["producer"] = dict(
            name="B-independent-join-inputs",
            version="2",
            implementation_hash="sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        )
        reseal(b)
    return result
