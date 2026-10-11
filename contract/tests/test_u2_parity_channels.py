"""Read actual adopted omission evidence; no new comparator or oracle invocation."""

import json
from pathlib import Path

from contract.tests.historical_snapshot import historical_snapshot

ROOT = Path(__file__).resolve().parents[2]
VENDOR = historical_snapshot()


def test_actual_declared_unknown_channels_do_not_include_matrix() -> None:
    rows = json.loads((VENDOR / "parity/fixtures.json").read_text())
    assert len(rows) == 864
    assert all("vector_ops" not in row["counts"] for row in rows)
    decode = [row for row in rows if row["query"]["phase"] == "decode"]
    prefill = [row for row in rows if row["query"]["phase"] == "prefill"]
    assert len(decode) == len(prefill) == 432
    assert all(row["counts"]["memory_write_bytes"] is None for row in decode)
    assert all("decode KV writes" in row["omissions"] for row in decode)
    assert all(row["counts"]["memory_write_bytes"] > 0 for row in prefill)
    assert all(row["counts"]["matrix_ops"] > 0 for row in rows)
    assert all(row["counts"]["memory_read_bytes"] > 0 for row in rows)


def test_existing_refusals_are_recorded_events_not_four_new_checks() -> None:
    refusals = json.loads((VENDOR / "parity/refusals.json").read_text())
    assert len(refusals) == 2
    assert {(r["compute"], r["kv_cache"]) for r in refusals} == {("bf16", "bf16"), ("fp8", "fp8")}
    assert all(r["exception"] == "UnsupportedPrecision" for r in refusals)
    assert all(r["component_params_file"] == "components/asic_placeholder.yaml" for r in refusals)
