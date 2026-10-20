"""Independent literals and historical installed refusals. No native evidence."""

from copy import deepcopy

import pytest
from uarch_contract.mapped import MappedBundle, admit, validate_resources

from rkuarch.verification.component.arithmetic import resident
from validation.component.corpus import build, graph
from validation.component.join_inputs import prospective_inputs, reseal


def test_mixed_work_traffic_and_exact_allocations():
    inputs = prospective_inputs()
    pairs = {
        "B2-C04-transient": ((256, 256), (1, 256)),
        "B2-255-256": ((256, 255), (256, 256)),
        "B2-equal": ((256, 256), (256, 256)),
    }
    for name, item in inputs.items():
        e = item["expected"]
        values = [resident(m, 256, n) for m, n in pairs[name]]
        assert sum(v[0] for v in values) == e["useful_ops"]
        assert sum(v[2] for v in values) == e["sram_read_bytes"]
        assert sum(v[3] for v in values) == e["sram_write_bytes"]
        assert sum(v[5] for v in values) == e["duration_ps"]
        g = graph(item["bundle"])
        acc = [b for b in g["buffers"] if b["space"] == "accumulator"]
        assert [(b["offset_bytes"], b["size_bytes"]) for b in acc] == [(0, v[4]) for v in values]
        assert [(b["producer_id"], b["final_consumer_ids"]) for b in acc] == [
            ("c", ["c"]),
            ("z", ["z"]),
        ]
        assert g["dependencies"] == [dict(before="c", after="z")]
        assert all(j["kind"] == "compute" for j in g["jobs"])


def test_old_c04_capacity_and_arithmetic_remain_history():
    old = build()["items"]["C04-carrier"]
    b = MappedBundle.model_validate(old["bundle"])
    with pytest.raises(ValueError, match="CapacityExceeded"):
        validate_resources(b, b.points[0])
    assert resident(256, 256, 256)[-1] + resident(1, 256, 256)[-1] == 1855000


def test_rehash_is_not_positive_authority():
    corpus = build()
    item = corpus["items"]["C06-fit"]
    b = deepcopy(item["bundle"])
    next(x for x in graph(b)["buffers"] if x["space"] == "accumulator")["size_bytes"] += 1
    reseal(b)
    with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
        admit(
            b,
            invocation="test",
            checkpoint="B",
            registry=corpus["registry"],
            profile=item["profile"],
            trusted_registry_hash=corpus["registry"]["registry_hash"],
            trusted_profile_hash=item["profile"]["profile_hash"],
        )
