"""Finite independent model-preparation arithmetic; no engine, predictions or device work."""

import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    model = json.loads((HERE / "model-parameters.json").read_text())
    facts, estimates = model["published_facts"], model["estimates"]
    assert len(facts) == 9 and len(estimates) == 17
    fields = {"value", "unit", "kind", "provenance", "source", "date", "rationale"}
    for value in facts.values():
        assert set(value) == fields
        assert value["kind"] == "claim" and value["provenance"] == "spec_derived"
        assert value["source"].startswith("https://") and value["rationale"] is None
    for estimate in estimates.values():
        value = estimate["value_record"]
        assert set(value) == fields
        assert value["kind"] == "claim" and value["provenance"] == "stub"
        assert value["source"] is value["date"] is value["rationale"] is None
        assert type(value["value"]) in (int, float) and math.isfinite(value["value"])
        assert value["value"] > 0
        assert estimate["basis"] and estimate["material_to"]
        low, high = estimate["stress_values"]
        assert 0 < low <= value["value"] <= high
    for precision in ("bf16", "int8"):
        rate = estimates[f"{precision}_mxu_mac_per_s"]["value_record"]["value"]
        assert 4 * 2 * rate == facts[f"{precision}_peak_ops_per_s"]["value"]
    assert estimates["matrix_fill_equivalent_macs"]["value_record"]["value"] == 254 * 128**2
    # Model choices, not a physical bandwidth/latency measurement.
    bandwidth_delay_bytes = Fraction(858_993_459_200 * 200_000, 10**12)
    assert 32 * 8192 >= bandwidth_delay_bytes > 8 * 8192
    assert 4 * 4096 * 10**9 == estimates["vmem_bytes_per_s"]["value_record"]["value"]

    # Independent synthetic 4x4 matrix with a K tail; timing is not a TPU estimate.
    useful = 3 * 5 * 3
    issued = 2 * 3 * 4 * 4
    fill = (4 + 4 - 2) * 4 * 4
    assert (useful, issued, fill) == (45, 96, 96)
    assert Fraction(issued + 2 * fill, 32) == 9
    assert Fraction(issued + 2 * fill, 16) == 18
    assert 2 * 3 * 130 * 7 == 5460
    assert (2 * 3 * 130, 2 * 130 * 7, 2 * 3 * 7) == (780, 1820, 42)
    assert 2 * 84 + 84 + 84 == 336
    assert (3 * 130, 130 * 7, 4 * 3 * 7) == (390, 910, 84)
    local = 2 * (1024 * 128 * 2 + 128 * 128 * 2) + 1024 * 128 * (4 + 2)
    assert local == 1_376_256 and 4 * local == 5_505_024 < 96 * 2**20
    assert 2048 * 64 * 2 * 4 == 1_048_576 > 512 * 2**10
    assert 64 * 2 * 4 == 512

    # Layout, typed primitives, and canonical conventions deliberately do not coincide.
    assert math.ceil(12 / 8) * math.ceil(320 / 128) == 6
    assert (12 * 320, 6 * 1024) == (3840, 6144)
    assert math.ceil(1 / 8) * math.ceil(1 / 128) == 1
    assert [math.ceil(5 / 2**s) for s in (1, 2, 3)] == [3, 2, 1]
    assert 2 * (5 - 1) == 8
    assert 3 * 2 * 7 == 42
    assert (1 - 1).bit_length() == 0
    assert (8 + 2 + 8 + 8, 6 + 2, 2, 8 + 4 + 8) == (26, 8, 2, 20)
    assert 26 + 8 + 2 == 36 != 6 * 2 * 4
    assert 5 + 4 + 8 + 3 == 20
    assert 3 + 2 + 3 + 3 + 2 + 1 + 3 == 17 != 5 * 3
    assert (2 * 3 * 4 // 2, 2 * 3 * 3) == (12, 18)
    assert (6 * (2 + 1) * 2, 2 * (2 + 1) * 4) == (36, 24)
    assert (2 * 6 * 1024, 2 * 2 * 1024) == (12288, 4096)

    # Exact valid bytes versus allocated tail pages and logical service spans.
    assert 2049 * 2 * 8 * 128 * 2 == 8_392_704
    assert (math.ceil(2049 / 16) * 65536, math.ceil(2049 / 32) * 131072) == (8_454_144, 8_519_680)
    assert (129 * 4, 65 * 4) == (516, 260)
    assert 8192 + 8192 + 3616 == 20000
    assert 4096 < 8192
    assert 268_435_456 // 8192 == 32768
    assert 4 * 32 * 32 == 4096
    assert 4096 * (32 + 4) == 147456
    assert 4 * 32 * 32 == 4096  # Final-output spans, no hidden K-partial HBM stores.
    # Literal two-request FIFO examples, intentionally not a simulator.
    assert (0 + 10 + 2, max(1 + 10, 12) + 2) == (12, 14)
    assert 12 + 10 + 2 == 24
    endpoints = [Fraction(i, 3) for i in (1, 2, 3)]
    assert list(map(math.ceil, endpoints)) == [1, 1, 1]
    assert endpoints[-1] == 1 != 3 * math.ceil(Fraction(1, 3))
    assert 11 + 3 + 5 == 19 != 2 * 11 + 3 + 5
    assert 2 * 19 == 38
    assert 11 + max(3, 5, 4, 2) == 16  # Native resource-demand floor, not C0.
    print(
        "PASS: 9 fact records, 17 numeric STUBs; independent matrix/vector/reduction/"
        "traffic/rounding/state examples; no engine execution or benchmark durations."
    )


if __name__ == "__main__":
    main()
