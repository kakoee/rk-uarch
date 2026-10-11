"""Refuse semantic tampering even after self hashes are repaired."""

from __future__ import annotations

from copy import deepcopy

import pytest

from rkuarch.workload.prepared_v2 import validate_execution_bundle

from .test_boundary import CASES, active_bundle


@pytest.mark.parametrize(
    "case",
    [
        "rope-target",
        "rope-alias",
        "rope-operand",
        "rope-access",
        "rope-layout",
        "rope-block",
        "rope-dtype",
        "rope-cos-dtype",
        "rope-reduction",
        "rope-weight-copies",
        "rope-fusion",
        "rope-P",
        "rope-too-wide",
        "rope-extra-dim",
        "rope-extra-binding",
        "no-binding",
        "projection-padding",
        "cache-append-shape",
        "rank-equivalence",
        "duplicate-point",
        "kv-page-policy",
        "hardware-rate",
        "block-format",
        "undefined-dependency",
        "duplicate-dependency",
        "group-order",
        "group-repeat",
        "nonrotary-work-repeat",
        "nonrotary-weight-copies",
        "nonrotary-format",
        "missing-reduction",
        "missing-operand",
    ],
)
def test_fully_rehashed_mutations(case):
    good = active_bundle()
    validate_execution_bundle(good)
    b = good.model_dump(mode="json")
    p = b["points"][0]
    g = p["graph"]["groups"][1]
    ops = {o["id"]: o for o in g["ops"]}
    q = ops["rope_q"]
    if case == "rope-target":
        q["rotary"]["target"] = "k"
    elif case == "rope-alias":
        q["id"] = "renamed-q"
    elif case == "rope-operand":
        q["spec"]["operands"]["X"]["dimensions"] = ["B", "S", "H", "D"]
    elif case == "rope-access":
        q["operand_access"]["Cos"] = "read_write"
    elif case == "rope-layout":
        q["spec"]["operands"]["X"]["layout"] = "strided"
    elif case == "rope-block":
        q["spec"]["operands"]["X"].update(layout="paged", block_size_tokens=16)
    elif case == "rope-dtype":
        q["spec"]["operands"]["Y"]["dtype"] = "fp16"
    elif case == "rope-cos-dtype":
        q["spec"]["operands"]["Cos"]["dtype"] = "bf16"
    elif case == "rope-reduction":
        q["spec"]["reduction_axes"] = ["R"]
    elif case == "rope-weight-copies":
        q["weight_copies"] = 2
    elif case == "rope-fusion":
        q["fusion"] = "qk_softmax_av"
    elif case == "rope-P":
        q["spec"]["dimensions"]["P"] = 2
    elif case == "rope-too-wide":
        q["spec"]["dimensions"].update(R=4, P=2)
    elif case == "rope-extra-dim":
        q["spec"]["dimensions"]["unused"] = 1
    elif case == "rope-extra-binding":
        ops["q"]["rotary"] = deepcopy(q["rotary"])
    elif case == "no-binding":
        q["rotary"] = None
    elif case == "projection-padding":
        ops["q"]["spec"]["dimensions"]["N"] = 8
        ops["q"]["padding"] = [dict(dimension="N", logical=4, physical=8)]
    elif case == "cache-append-shape":
        ops["kv"]["spec"]["dimensions"]["S"] = 2
    elif case == "rank-equivalence":
        b["rank"]["equivalent_ranks"] = []
    elif case == "duplicate-point":
        b["points"].append(deepcopy(p))
    elif case == "kv-page-policy":
        ops["attn"]["kv_access"]["last_page_valid_tokens"] = 16
    elif case == "hardware-rate":
        b["hardware_spec"]["cores"]["core_type"]["vector_engine"]["ops_per_cycle"]["value"] = 0
    elif case == "block-format":
        b["hardware_spec"]["formats"]["bf16"]["block_scale_bytes"]["value"] = 1
    elif case == "undefined-dependency":
        q["depends_on"] = ["undefined"]
    elif case == "duplicate-dependency":
        q["depends_on"] *= 2
    elif case == "group-order":
        g["depends_on"] = []
    elif case == "group-repeat":
        p["graph"]["groups"][0]["repeat"] = 2
    elif case == "nonrotary-work-repeat":
        ops["q"]["work_repeat"] = 2
    elif case == "nonrotary-weight-copies":
        ops["q"]["weight_copies"] = 2
    elif case == "nonrotary-format":
        ops["q"]["spec"]["operands"]["X"]["dtype"] = "fp16"
    elif case == "missing-reduction":
        ops["q"]["spec"]["reduction_axes"] = []
    elif case == "missing-operand":
        ops["q"]["spec"]["operands"].pop("W")
        ops["q"]["operand_access"].pop("W")
    if case in ("hardware-rate", "block-format"):
        from uarch_contract.hashing import content_hash

        # Same canonical spec hashing, without parsing so invalid storage remains testable.
        b["intent"]["hardware_spec_hash"] = content_hash(b["hardware_spec"])
    CASES["rehash"](b)
    with pytest.raises(ValueError):
        validate_execution_bundle(b)
