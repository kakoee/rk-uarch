"""A's unmasked lifetime regressions; multi-reader construction attributed to B joins-v2.
Synthetic resources only. No admission authority or native execution.
"""

from copy import deepcopy
from typing import Any

import pytest
from uarch_contract.mapped import MappedBundle, validate_resources

from validation.component.corpus import graph
from validation.component.join_inputs import pair, reseal


def check(raw: Any) -> Any:
    b = MappedBundle.model_validate(reseal(deepcopy(raw)))
    validate_resources(b, b.points[0])


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


def test_partial_terminal_reuse() -> None:
    good = multiple_consumers()
    check(good)
    bad = deepcopy(good)
    g = graph(bad)
    next(b for b in g["buffers"] if b["id"] == "acc")["final_consumer_ids"] = ["d"]
    g["dependencies"].remove(dict(before="e", after="z"))
    with pytest.raises(ValueError, match="^InvalidDependency: final consumers acc$"):
        check(bad)
    check(good)


@pytest.mark.parametrize("ordered", [False, True], ids=["A3c-unordered", "A3b-before-producer"])
def test_equal_footprint_use_before_production(ordered: Any) -> None:
    good = pair(256, 256)
    good["mapping_policy"]["version"] = "2"
    check(good)
    bad = deepcopy(good)
    g = graph(bad)
    next(j for j in g["jobs"] if j["id"] == "z")["accumulator_buffer_id"] = "acc"
    g["buffers"] = [b for b in g["buffers"] if b["id"] != "zacc"]
    next(b for b in g["buffers"] if b["id"] == "acc")["final_consumer_ids"] = (
        ["c"] if ordered else ["c", "z"]
    )
    g["dependencies"] = [dict(before="z", after="c")] if ordered else []
    with pytest.raises(ValueError, match="^InvalidDependency: accumulator use before production$"):
        check(bad)
    check(good)
