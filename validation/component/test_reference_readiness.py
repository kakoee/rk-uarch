"""Prospective suite coverage checks, never reference execution."""

import json

from uarch_contract.operators import Operator

from validation.component.corpus import ROOT


def test_required_reference_suite_is_not_shrunk():
    raw = json.loads((ROOT / "validation/L3_silicon/tpu-v5e/suite.json").read_bytes())
    rows = raw["benchmarks"]
    assert len(rows) == len({x["id"] for x in rows}) == 70
    assert {x["benchmark_class"] for x in rows} == {
        "matrix",
        "memory",
        "operator",
        "end-to-end",
        "DRAM gather",
        "launch overhead",
    }
    for op in Operator:
        for mode in ("decode", "prefill"):
            assert f"operator-{op.value}-{mode}" in {x["id"] for x in rows}
    assert all(
        x["native_status"] == "not_run"
        and x["mapping_match"] == "compiler-chosen"
        and x["measurement_unit"]
        and x["native_gap"]
        for x in rows
    )
    assert raw["signatures"]["lane_A"] is None
