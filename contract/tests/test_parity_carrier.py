"""B adapter regressions against A's actual proposed parity carrier, not a stand-in."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.vendor_rk import ROOT

from . import parity
from .test_flop_parity import sample


def carrier_api(lane_a: dict[str, Any]) -> Any:
    cls = lane_a["table"].FlopParity
    assert "comparisons" in cls.model_fields, "A's revised parity carrier is required"
    return cls


def test_f8_representative_payloads_round_trip(lane_a: dict[str, Any]) -> None:
    cls = carrier_api(lane_a)
    examples = json.loads((ROOT / "docs/reviews/U1-lane-B-flop-parity-payloads.json").read_text())
    for name in ("not_run", "self_test", "hypothetical_workload_classification"):
        payload = examples[name]
        assert (
            cls.model_validate_json(cls.model_validate(payload).model_dump_json()).model_dump(
                mode="json"
            )
            == payload
        )


def test_f8_adapter_preserves_attribution_metrics_and_self_test(lane_a: dict[str, Any]) -> None:
    cls = carrier_api(lane_a)
    row = sample()
    ds = [
        parity.Deviation("a", "matrix_ops", 0.03, "Synthetic term a"),
        parity.Deviation("b", "matrix_ops", 0.02, "Synthetic term b"),
    ]
    calls: list[str] = []

    def candidate(*args: Any) -> dict[str, float | None]:
        calls.append("called")
        return parity.rank_counts(row) | {"matrix_ops": 105.5}

    result = parity.run_parity([row], candidate, deviations={row["id"]: ds})
    payload = parity.contract_payload(
        result, fixture_set_id="synthetic:u1", candidate_identity="synthetic:echo"
    )
    assert calls == ["called"]  # adapter must not rerun the candidate
    recovered = cls.model_validate_json(cls.model_validate(payload).model_dump_json()).model_dump(
        mode="json"
    )
    assert recovered == payload
    assert recovered["kind"] == "harness_self_test"
    assert recovered["oracle_manifest_sha256"] is None
    matrix = next(c for c in recovered["comparisons"] if c["channel"] == "matrix_ops")
    assert matrix["fixture_id"] == row["id"]
    assert matrix["unit"] == "op"
    assert matrix["actual"] == 105.5 and matrix["reference"] == 100.0
    for field in ("raw_rel", "signed_adjustment_rel", "absolute_adjustment_rel", "residual_rel"):
        assert matrix[field] == result["comparisons"][row["id"]]["matrix_ops"][field]
    assert [d["id"] for d in matrix["declared_deviations"]] == ["a", "b"]
    null = next(c for c in recovered["comparisons"] if c["channel"] == "memory_write_bytes")
    assert null["actual"] is None and null["reference"] is None
    assert null["raw_rel"] is None and null["residual_rel"] is None


def test_f8_adapter_requires_explicit_structured_kind(lane_a: dict[str, Any]) -> None:
    carrier_api(lane_a)
    row = sample()
    report = parity.run_parity([row], lambda *a: parity.rank_counts(row))
    report.pop("comparison_kind", None)
    with pytest.raises(ValueError, match="classification"):
        parity.contract_payload(report, fixture_set_id="synthetic", candidate_identity="echo")


def test_f8_zero_reference_serializes_without_relative_max(lane_a: dict[str, Any]) -> None:
    cls = carrier_api(lane_a)
    row = sample() | {"counts": {"matrix_ops": 0.0}}
    report = parity.run_parity([row], lambda *a: {"matrix_ops": 0.0})
    payload = parity.contract_payload(report, fixture_set_id="synthetic", candidate_identity="zero")
    assert cls.model_validate_json(json.dumps(payload)).model_dump(mode="json") == payload
    assert payload["max_rel"] is None
    assert payload["comparisons"][0]["reference_state"] == "zero"


def test_f8_preserved_oracle_echo_stays_self_test(snapshot: Path, lane_a: dict[str, Any]) -> None:
    cls = carrier_api(lane_a)
    rows = json.loads((snapshot / "parity/fixtures.json").read_text())
    iterator = iter(rows)
    report = parity.run_parity(rows, lambda *a: parity.rank_counts(next(iterator)))
    payload = parity.contract_payload(
        report, fixture_set_id="preserved-U1-oracle", candidate_identity="synthetic:oracle-echo"
    )
    recovered = cls.model_validate_json(cls.model_validate(payload).model_dump_json())
    assert recovered.kind == "harness_self_test"
    assert recovered.n_fixtures == 864
    assert len(recovered.comparisons) == 864 * 3


def test_f8_opposing_adjustments_keep_absolute_spend(lane_a: dict[str, Any]) -> None:
    cls = carrier_api(lane_a)
    row = sample()
    deviations = [
        parity.Deviation("addition", "matrix_ops", 0.03, "Synthetic addition"),
        parity.Deviation("omission", "matrix_ops", -0.02, "Synthetic omission"),
    ]
    report = parity.run_parity(
        [row],
        lambda *a: parity.rank_counts(row) | {"matrix_ops": 101.0},
        deviations={row["id"]: deviations},
    )
    payload = parity.contract_payload(
        report, fixture_set_id="synthetic", candidate_identity="cancellation"
    )
    restored = cls.model_validate_json(cls.model_validate(payload).model_dump_json())
    matrix = next(c for c in restored.comparisons if c.channel == "matrix_ops")
    assert matrix.absolute_adjustment_rel == 0.05
    assert matrix.signed_adjustment_rel == pytest.approx(0.01)
    assert matrix.signed_adjustment_rel != matrix.absolute_adjustment_rel
    assert [d.id for d in matrix.declared_deviations] == ["addition", "omission"]


def test_f8_explicit_workload_classification_requires_identity(lane_a: dict[str, Any]) -> None:
    """Classification protocol only; this synthetic echo is NOT a workload parity result."""
    carrier_api(lane_a)
    row = sample()
    report = parity.run_parity([row], lambda *a: parity.rank_counts(row), self_test=False)
    with pytest.raises(ValueError, match="oracle_manifest_sha256"):
        parity.contract_payload(report, fixture_set_id="synthetic", candidate_identity="synthetic")
    payload = parity.contract_payload(
        report,
        fixture_set_id="synthetic",
        candidate_identity="synthetic",
        oracle_manifest_sha256="0" * 64,
    )
    assert payload["kind"] == "workload_parity"  # caller assertion, not authenticated by echo
