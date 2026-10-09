"""Acceptance checks against the human-generated, committed oracle, never rk-sim."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.vendor_rk import ROOT, SOURCES, digest

from .parity import rank_counts, run_parity


def test_eventual_u0001_uses_same_pin(request: pytest.FixtureRequest) -> None:
    from scripts.vendor_rk import check_contract_pin

    check_contract_pin(ROOT, pre_contract=request.config.getoption("--pre-contract"))


def test_current_snapshot_generator_compatibility(snapshot: Path) -> None:
    from scripts.vendor_rk import check_generator

    check_generator(snapshot)


def test_committed_manifest_matrix_and_component_provenance(snapshot: Path) -> None:
    for name in (*SOURCES, "schema.json"):
        assert (snapshot / name).is_file(), name
    rows = json.loads((snapshot / "parity/fixtures.json").read_text())
    from scripts.vendor_rk import check_snapshot_inputs

    # Validates the exact retained matrix or authenticated explicit U2 declarations.
    # Unknown components still refuse; never infer a new component's precision.
    check_snapshot_inputs(snapshot)
    for row in rows:
        assert (
            digest((snapshot / row["component_params_file"]).read_bytes())
            == (row["component_params_sha256"])
        )
        sidecar = json.loads((snapshot / "model_shapes" / (row["model_id"] + ".json")).read_text())
        assert row["model"] == sidecar["model"]
        assert row["model_shape"] == sidecar["shape"]
        assert row["model_sources"] == sidecar["sources"]
        assert sidecar == json.loads(
            (ROOT / "contract/fixtures/model_shapes" / (row["model_id"] + ".json")).read_text()
        )


def test_committed_parity_harness_self_test(snapshot: Path) -> None:
    """A fixture echoes itself: this verifies the harness, NOT a workload implementation."""
    rows = json.loads((snapshot / "parity/fixtures.json").read_text())
    for row in rows:
        result = run_parity([row], lambda *args, row=row: rank_counts(row), self_test=True)
        assert result["kind"] == "harness self-test (not workload parity)"

        def wrong(*args: Any, row: dict[str, Any] = row) -> dict[str, float | None]:
            counts = rank_counts(row)
            assert counts["matrix_ops"] is not None
            counts["matrix_ops"] *= 1.1
            return counts

        with pytest.raises(AssertionError, match=row["id"]):
            run_parity([row], wrong)


def test_all_sourced_sidecars_pass_lane_a_check_parity(lane_a: dict[str, Any]) -> None:
    paths = sorted((ROOT / "contract/fixtures/model_shapes").glob("*.json"))
    assert len(paths) >= 3
    for path in paths:
        sidecar = json.loads(path.read_text())
        assert sidecar["sources"]
        model = lane_a["model_shape"].ModelSpec.model_validate(sidecar["model"])
        shape = lane_a["model_shape"].ModelShape.model_validate(sidecar["shape"])
        lane_a["model_shape"].check_parity(model, shape)


def test_placeholder_refuses_unsupported_compute_precision(snapshot: Path) -> None:
    """Human bridge asserted rk-sim's actual exception; CI checks its committed evidence."""
    from scripts.vendor_rk import validate_refusals

    expanded = (snapshot / "u2-inputs").is_dir()
    validate_refusals(
        json.loads((snapshot / "parity/refusals.json").read_text()),
        expanded=expanded,
        callable_source_sha256=digest((snapshot / "rk/engine/f0/compute.py").read_bytes())
        if expanded
        else None,
    )
