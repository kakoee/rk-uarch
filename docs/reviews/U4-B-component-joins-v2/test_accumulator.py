"""Private-candidate acceptance only; synthetic admission anchors, never native receipts."""

from copy import deepcopy

import pytest
from uarch_contract.mapped import MappedBundle, admit, validate_resources

from validation.component.corpus import build, graph, materialize, two_tiles
from validation.component.join_inputs import prospective_inputs, reseal


def check(raw):
    b = MappedBundle.model_validate(reseal(raw))
    validate_resources(b, b.points[0])


def raw():
    return deepcopy(prospective_inputs()["B2-C04-transient"]["bundle"])


@pytest.mark.parametrize("name", list(prospective_inputs()))
def test_new_exact_representations(name):
    check(deepcopy(prospective_inputs()[name]["bundle"]))


@pytest.mark.parametrize(
    "fault,code",
    [
        ("no_order", "LiveBufferAlias"),
        ("missing_consumer", "InvalidDependency"),
        ("false_consumer", "InvalidDependency"),
        ("future_producer", "InvalidDependency"),
        ("other_writer", "InvalidDependency"),
        ("owner", "InvalidResource"),
        ("short", "CapacityExceeded"),
        ("long", "CapacityExceeded"),
        ("offset", "CapacityExceeded"),
        ("persistent_alias", "LiveBufferAlias"),
        ("old_policy", "UnsupportedMapping"),
    ],
)
def test_semantic_attack_and_restored_control(fault, code):
    b = raw()
    g = graph(b)
    a = next(x for x in g["buffers"] if x["id"] == "acc")
    z = next(x for x in g["buffers"] if x["id"] == "zacc")
    if fault == "no_order":
        g["dependencies"] = []
    elif fault == "missing_consumer":
        a["final_consumer_ids"] = []
    elif fault == "false_consumer":
        a["final_consumer_ids"] = ["z"]
    elif fault == "future_producer":
        a["producer_id"] = "z"
    elif fault == "other_writer":
        z["producer_id"] = "c"
    elif fault == "owner":
        z["core_id"] = 1
    elif fault == "short":
        z["size_bytes"] -= 1
    elif fault == "long":
        z["size_bytes"] += 1
    elif fault == "offset":
        a["offset_bytes"] = 256
    elif fault == "persistent_alias":
        for buf in (a, z):
            buf.update(producer_id=None, final_consumer_ids=[])
    elif fault == "old_policy":
        b["mapping_policy"]["version"] = "1"
    with pytest.raises(ValueError, match=code):
        check(b)
    check(raw())


def test_independent_cores_overlap_without_dependency():
    b = two_tiles(same_core=False)
    b["mapping_policy"]["version"] = "2"
    for buf in graph(b)["buffers"]:
        if buf["space"] == "accumulator":
            j = "c" if buf["id"] == "acc" else "z"
            buf.update(producer_id=j, final_consumer_ids=[j])
    check(b)
    assert graph(b)["dependencies"] == []


def test_historical_persistent_scratch_controls():
    items = build()["items"]
    check(deepcopy(items["C04-control"]["bundle"]))
    with pytest.raises(ValueError, match="CapacityExceeded"):
        check(deepcopy(items["C04-carrier"]["bundle"]))


@pytest.mark.parametrize(
    "name,code",
    [
        ("C06-small", "CapacityExceeded"),
        ("C07-sram-1", "SramCapacityExceeded"),
        ("C07-hbm-1", "CapacityExceeded"),
    ],
)
def test_synthetic_positive_context_reaches_resource_guard(name, code):
    corpus = build()
    original = corpus["items"][name]
    args = dict(
        invocation="test",
        checkpoint="B",
        registry=corpus["registry"],
        trusted_registry_hash=corpus["registry"]["registry_hash"],
    )
    with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
        admit(
            original["bundle"],
            profile=original["profile"],
            trusted_profile_hash=original["profile"]["profile_hash"],
            **args,
        )
    # Explicitly synthetic separately anchored context, never caller authority.
    positive = materialize(
        "SYNTHETIC-positive-context-" + name, original["bundle"], dict(outcome="success")
    )
    with pytest.raises(ValueError, match=code):
        admit(
            positive["bundle"],
            profile=positive["profile"],
            trusted_profile_hash=positive["profile"]["profile_hash"],
            **args,
        )
    # Substituting a self-rehashed positive profile under the OLD anchor still refuses.
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        admit(
            positive["bundle"],
            profile=positive["profile"],
            trusted_profile_hash=original["profile"]["profile_hash"],
            **args,
        )


def multiple_consumers():
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


def test_all_terminal_consumers_before_reuse():
    b = multiple_consumers()
    check(deepcopy(b))
    g = graph(b)
    g["dependencies"].remove(dict(before="e", after="z"))
    with pytest.raises(ValueError, match="LiveBufferAlias"):
        check(b)
    check(multiple_consumers())
