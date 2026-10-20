"""Stdlib-only preparation checks; no engine import, prediction, or device access.

Run from any directory. --write-shapes regenerates the count-only worksheet.
The arithmetic literals below are synthetic interface checks, not human L1 workings.
"""

import hashlib
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def shape(ident, m, k, n, precision):
    # One useful read of each input and one final output, no assumed physical traffic.
    in_bytes, out_bytes = (1, 4) if precision == "int8" else (2, 2)
    work = 2 * m * k * n
    payload = in_bytes * (m * k + k * n) + out_bytes * m * n
    peak = 393_000_000_000_000 if precision == "int8" else 197_000_000_000_000
    ratio = Fraction(work * 858_993_459_200, payload * peak)
    return {
        "id": ident,
        "M": m,
        "K": k,
        "N": n,
        "precision": precision,
        "useful_operations": work,
        "logical_payload_bytes": payload,
        "intensity_ops_per_byte": float(Fraction(work, payload)),
        "intensity_over_nominal_ridge": float(ratio),
        "intensity_regime": "low" if ratio < Fraction(1, 2) else "middle" if ratio <= 2 else "high",
        "array_fill": "underfilled" if m < 128 or n < 128 else "full",
    }


def main():
    historical = read("../suite.json")
    proposal = read("suite-proposed.json")
    dispositions = read("candidate-dispositions.json")
    old = {r["id"]: r for r in historical["benchmarks"]}
    selected = {r["id"]: r for r in proposal["benchmarks"]}
    assert len(old) == len(historical["benchmarks"]) == 70
    assert len(selected) == len(proposal["benchmarks"]) == 52
    assert (
        proposal["historical_suite_sha256"]
        == hashlib.sha256((HERE.parent / "suite.json").read_bytes()).hexdigest()
    )
    assert len(dispositions) == 70
    assert {d["candidate_id"] for d in dispositions} == set(old)
    assert all(set(d["selected_units"]) <= set(selected) and d["reason"] for d in dispositions)
    assert {s for d in dispositions for s in d["selected_units"]} == set(selected)
    assert Counter(r["benchmark_class"] for r in selected.values()) == {
        "matrix": 12,
        "memory": 9,
        "operator": 24,
        "end-to-end": 4,
        "DRAM gather": 2,
        "launch overhead": 1,
    }
    assert Counter(d["disposition"] for d in dispositions) == {
        "retain": 50,
        "replace_shape": 2,
        "merge": 12,
        "omit_optional": 4,
        "correctness_only": 2,
    }
    assert all(value is None for value in proposal["signatures"].values())
    required = {
        "mathematics",
        "work",
        "precision_policy",
        "native_support",
        "unit_kind",
        "mapping",
        "mapping_match",
        "state_procedure",
        "initial_state",
        "measurement_unit",
    }
    for row in selected.values():
        assert required <= row.keys()
        assert all(row[key] for key in required)
        assert row["observability"] == "not_demonstrated"
        assert row["native_status"] == "not_run"
        assert row["initial_state"] == "steady"
        assert row["mapping_match"] == "compiler-chosen"
    for mode in ("decode", "prefill"):
        for op in ("qk_score", "softmax", "av_application"):
            d = next(d for d in dispositions if d["candidate_id"] == f"operator-{op}-{mode}")
            assert d["selected_units"] == [f"operator-attention_fused-{mode}"]
        for op in ("rope", "cast-bf16-fp32", "cast-fp32-bf16"):
            d = next(d for d in dispositions if d["candidate_id"] == f"operator-{op}-{mode}")
            assert d["selected_units"] == [
                f"operator-q_projection-{mode}",
                f"operator-k_projection-{mode}",
            ]
    matrix = []
    for row in selected.values():
        if row["benchmark_class"] == "matrix":
            w = row["work"]
            matrix.append(shape(row["id"], w["M"], w["K"], w["N"], w["precision"]))
    for precision in ("bf16", "int8"):
        points = [s for s in matrix if s["precision"] == precision]
        assert len({(s["M"], s["K"], s["N"]) for s in points}) == 6
        assert {(s["intensity_regime"], s["array_fill"]) for s in points} == {
            ("low", "underfilled"),
            ("low", "full"),
            ("middle", "full"),
            ("high", "full"),
        }
    projections = []
    dims = {
        "q_projection": (4096, 4096),
        "k_projection": (4096, 1024),
        "v_projection": (4096, 1024),
        "output_projection": (4096, 4096),
        "ffn_up": (4096, 14336),
        "ffn_gate": (4096, 14336),
        "ffn_down": (14336, 4096),
    }
    for m in (1, 8, 32, 128):
        for name, (k, n) in dims.items():
            projections.append(shape(f"{name}-M{m}", m, k, n, "bf16"))
    worksheet = {
        "kind": "count-only selection worksheet; no EngineResult or durations",
        "source_policy": (
            "Cloud v5e nominal chip peaks and binary-unit HBM rate; "
            "source conflict retained in REFERENCE.md"
        ),
        "limits": (
            "projection suboperations only, excludes enclosing rotary traffic; "
            "no compiler padding/physical traffic/load or saturation claim; "
            "final characterize binding pending"
        ),
        "matrix": matrix,
        "decoder_projection_suboperations": projections,
        "noc_load_regime": None,
        "dram_load_regime": None,
    }
    encoded = json.dumps(worksheet, indent=2) + "\n"
    if sys.argv[1:] == ["--write-shapes"]:
        (HERE / "shape-regimes.json").write_text(encoded)
    else:
        assert not sys.argv[1:], "only --write-shapes is supported"
        assert (HERE / "shape-regimes.json").read_text() == encoded
    # Independent literal expectations, without production count/mapping helpers.
    assert (2 * 3 * 5 * 7, 2 * 3 * 5, 2 * 5 * 7, 2 * 3 * 7, 4 * 3 * 7) == (210, 30, 70, 42, 84)
    assert (3 * 5, 5 * 7, 4 * 3 * 7) == (15, 35, 84)
    assert sum(3 * k * 7 for k in (128, 2)) == 2730
    assert (2 * 3 * 130, 2 * 130 * 7, 2 * 3 * 7) == (780, 1820, 42)
    assert (3 * 12, 2 * 12, 2 * 12, 2 * 12, 2 * 2 * 2 * 4) == (36, 24, 24, 24, 32)
    assert (3 * 5120, 2 * 5120) == (15360, 10240)
    assert (2 * 17 * 2 * 4 * 2, 2 * 32 * 2 * 4 * 2, 2 * 2 * 4 * 2) == (544, 1024, 32)
    assert (4 * 4 * 3 * 2, 2 * 3 * 2 * 2 * 2, 5 * 4 * 3) == (96, 48, 60)
    pairs = 2 * 3 * (3 + 1) // 2
    assert (pairs, 4 * pairs * 2, 5 * pairs) == (12, 96, 60)
    assert (4 * 2, 4, 4 - 1, 4) == (8, 4, 3, 4)
    assert 4096 * 7 * 7 == 200704 < 2**31
    print(
        "PASS: 70 dispositions; 52 units in six classes; "
        "12 matrix and 28 projection shape rows; 10 synthetic arithmetic groups; "
        "historical suite hash unchanged."
    )


if __name__ == "__main__":
    main()
