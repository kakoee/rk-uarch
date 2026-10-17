"""Independent transient-lifetime inputs. Synthetic context never confers authority."""

from copy import deepcopy
from typing import Any

from validation.component.corpus import build, graph
from validation.component.join_inputs import pair, reseal


def multiple_consumers() -> Any:
    from validation.component.join_inputs import pair

    b = pair(256, 256)
    g = graph(b)
    first = deepcopy(g["jobs"][0])
    first_buffers = [
        deepcopy(x) for x in g["buffers"] if not x["id"].startswith("z") and x["space"] == "sram"
    ]
    for index, name in enumerate(("d", "e"), 2):
        op = deepcopy(b["scope"]["ops"][0])
        op["id"] = "g" + str(index)
        b["scope"]["ops"].append(op)
        b["scope"]["op_ids"].append(op["id"])
        b["points"][0]["identity"]["op_ids"].append(op["id"])
        j = deepcopy(first)
        j.update(id=name, op_id=op["id"])
        j["operand_buffers"] = {k: name + v for k, v in j["operand_buffers"].items()}
        g["jobs"].append(j)
        cov = deepcopy(g["coverage"][0])
        cov.update(job_id=name, op_id=op["id"])
        g["coverage"].append(cov)
        for buf in deepcopy(first_buffers):
            buf["id"] = name + buf["id"]
            buf["op_id"] = op["id"] if buf["op_id"] is not None else None
            buf["offset_bytes"] += index * 786432
            buf["bank"] = buf["offset_bytes"] // 524288
            buf["producer_id"] = name if buf["producer_id"] == "c" else buf["producer_id"]
            buf["final_consumer_ids"] = [name if x == "c" else x for x in buf["final_consumer_ids"]]
            g["buffers"].append(buf)
    next(x for x in g["buffers"] if x["id"] == "acc")["final_consumer_ids"] = ["d", "e"]
    g["dependencies"] = [
        dict(before=a, after=z) for a, z in [("c", "d"), ("c", "e"), ("d", "z"), ("e", "z")]
    ]
    g["coverage"].sort(key=lambda x: x["job_id"])
    b["mapping_policy"]["version"] = "2"
    return b


def disjoint_writer() -> Any:
    b = deepcopy(build()["items"]["C04-control"]["bundle"])
    b["mapping_policy"]["version"] = "2"
    g = graph(b)
    acc = next(x for x in g["buffers"] if x["space"] == "accumulator")
    acc.update(producer_id="c", final_consumer_ids=["c"])
    second = deepcopy(acc)
    second.update(id="zacc", offset_bytes=256, producer_id="z", final_consumer_ids=["z"])
    g["buffers"].append(second)
    next(t for t in g["jobs"] if t["id"] == "z")["accumulator_buffer_id"] = "zacc"
    g["dependencies"] = [dict(before="c", after="z")]
    return b


def lifetime_inputs() -> Any:
    out: dict[Any, Any] = {}
    b = disjoint_writer()
    out["B3-writer-control"] = reseal(deepcopy(b))
    next(x for x in graph(b)["buffers"] if x["id"] == "zacc")["producer_id"] = "c"
    out["B3-false-writer-disjoint"] = reseal(b)
    b = multiple_consumers()
    out["B3-terminal-control"] = reseal(deepcopy(b))
    next(x for x in graph(b)["buffers"] if x["id"] == "acc")["final_consumer_ids"] = ["d"]
    graph(b)["dependencies"].remove(dict(before="e", after="z"))
    out["B3-terminal-partial-A1"] = reseal(b)
    for name, dependencies, finals in [
        ("B3-use-before-A3b", [dict(before="z", after="c")], ["c"]),
        ("B3-use-unordered-A3c", [], ["c", "z"]),
        ("B3-shared-use-control", [dict(before="c", after="z")], ["z"]),
    ]:
        b = pair(256, 256)
        b["mapping_policy"]["version"] = "2"
        g = graph(b)
        next(t for t in g["jobs"] if t["id"] == "z")["accumulator_buffer_id"] = "acc"
        g["buffers"] = [x for x in g["buffers"] if x["id"] != "zacc"]
        next(x for x in g["buffers"] if x["id"] == "acc")["final_consumer_ids"] = finals
        g["dependencies"] = dependencies
        out[name] = reseal(b)
    return out
