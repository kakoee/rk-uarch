"""A-F12 scope regressions; synthetic probes and oracle echoes are not U2 parity."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from . import parity
from .historical_snapshot import historical_snapshot
from .test_flop_parity import sample


def supported(tp: int = 8) -> dict[str, Any]:
    return sample() | {
        "tp": tp,
        "model": {"n_heads": 64, "kv_heads": 8},
        "model_shape": {"vocab_size": 128256, "d_ff": 28672, "expert_d_ff": None},
    }


@pytest.mark.parametrize("tp", [1, 2, 4, 8])
def test_supported_uniform_shards_remain_comparable(tp: int) -> None:
    row = supported(tp)
    report = parity.run_parity([row], lambda *a: parity.rank_counts(row))
    assert report["coverage"][row["id"]]["status"] == "passed"
    assert report["outcome"] == "passed"
    assert report["comparison_kind"] == "harness_self_test"


@pytest.mark.parametrize("self_test", [True, False])
def test_replicated_kv_refused_before_even_an_exact_echo(self_test: bool) -> None:
    row = supported(16)
    calls: list[int] = []

    def echo(*args: Any) -> dict[str, float | None]:
        calls.append(1)
        return parity.rank_counts(row)

    with pytest.raises(AssertionError, match="unsupported_projection") as caught:
        parity.run_parity([row], echo, self_test=self_test)
    assert calls == []
    status = caught.value.report["coverage"][row["id"]]  # type: ignore[attr-defined]
    assert status["status"] == "unsupported_projection"
    assert any("kv_heads=8" in reason and "tp=16" in reason for reason in status["reasons"])


def test_reproduced_a_f12_read_difference_is_an_unsupported_projection(lane_a: Any) -> None:
    from uarch_contract.request import LegacyCharacterizationRequest

    from .test_u_p1 import request_data

    request = LegacyCharacterizationRequest.model_validate(request_data() | {"tp": 16})
    model = request.model
    weights = model.active_params * 2
    kv = 2 * model.n_layers * model.kv_heads * model.head_dim * 2 * 32768
    aggregate_projected = (weights + kv) / request.tp
    actual = weights / request.tp + kv / model.kv_heads
    assert aggregate_projected == 9490301952.0
    assert actual == 10161390592.0
    assert (actual - aggregate_projected) / aggregate_projected == pytest.approx(0.0707130967)
    # Arithmetic reproduces the review probe; it does NOT create a frozen oracle fixture.
    row = supported(16) | {
        "id": "synthetic:A-F12-70b-tp16",
        "model": model.model_dump(mode="json"),
        "model_shape": request.model_shape.model_dump(mode="json"),
        "counts": {"memory_read_bytes": aggregate_projected * 16},
    }
    with pytest.raises(AssertionError, match="unsupported_projection"):
        parity.run_parity([row], lambda *a: {"memory_read_bytes": actual}, self_test=False)


@pytest.mark.parametrize(
    "field,value", [("vocab_size", 128257), ("d_ff", 28673), ("expert_d_ff", 14337)]
)
def test_padding_cannot_pass_via_aggregate_echo(field: str, value: int) -> None:
    row = supported()
    row["model_shape"][field] = value
    with pytest.raises(AssertionError, match=field) as caught:
        parity.run_parity([row], lambda *a: parity.rank_counts(row), self_test=False)
    assert caught.value.report["coverage"][row["id"]]["status"] == "unsupported_projection"  # type: ignore[attr-defined]


def test_missing_projection_dimensions_fail_closed() -> None:
    row = supported() | {"model_shape": {}}
    with pytest.raises(AssertionError, match="missing or invalid"):
        parity.run_parity([row], lambda *a: parity.rank_counts(row), self_test=False)


def test_complete_coverage_keeps_unsupported_and_numerical_failure(lane_a: Any) -> None:
    rows = [supported(), supported(16), supported(), supported()]
    for row, name in zip(
        rows, ("baseline", "replication", "embedding-probe", "padding"), strict=True
    ):
        row["id"] = name
        row["query"]["case"] = name
    rows[3]["model_shape"]["vocab_size"] += 1
    seen: list[str] = []

    def candidate(model: Any, shape: Any, precision: Any, query: Any) -> dict[str, float | None]:
        seen.append(query["case"])
        # Synthetic >budget discrepancy, NOT a measured embedding-operation offset.
        return parity.rank_counts(rows[0]) | {
            "matrix_ops": 106.54 if query["case"] == "embedding-probe" else 100.0
        }

    before = deepcopy(rows)
    with pytest.raises(AssertionError) as caught:
        parity.run_parity(rows, candidate, self_test=False)
    report = caught.value.report  # type: ignore[attr-defined]
    assert report["outcome"] == "failed"
    assert report["n_fixtures"] == len(rows)
    assert {k: v["status"] for k, v in report["coverage"].items()} == {
        "baseline": "passed",
        "replication": "unsupported_projection",
        "embedding-probe": "failed",
        "padding": "unsupported_projection",
    }
    assert seen == ["baseline", "embedding-probe"]
    assert report["comparisons"]["embedding-probe"]["matrix_ops"]["raw_rel"] == pytest.approx(
        0.0654
    )
    assert rows == before
    with pytest.raises(ValueError, match="complete passing coverage"):
        parity.contract_payload(
            report,
            fixture_set_id="synthetic",
            candidate_identity="synthetic",
            oracle_manifest_sha256="0" * 64,
        )


def test_all_864_preserved_fixtures_retain_supported_coverage() -> None:
    rows = json.loads((historical_snapshot() / "parity/fixtures.json").read_text())
    iterator = iter(rows)
    report = parity.run_parity(rows, lambda *a: parity.rank_counts(next(iterator)))
    assert len(rows) == report["n_fixtures"] == len(report["coverage"]) == 864
    assert set(report["coverage"]) == {r["id"] for r in rows}
    assert {c["status"] for c in report["coverage"].values()} == {"passed"}
    assert report["comparison_kind"] == "harness_self_test"


def test_incomplete_coverage_cannot_serialize_as_workload(lane_a: Any) -> None:
    row = supported()
    report = parity.run_parity([row], lambda *a: parity.rank_counts(row), self_test=False)
    report["coverage"] = {}
    with pytest.raises(ValueError, match="complete passing coverage"):
        parity.contract_payload(
            report,
            fixture_set_id="synthetic",
            candidate_identity="echo",
            oracle_manifest_sha256="0" * 64,
        )


def test_duplicate_fixture_ids_are_refused_before_coverage_can_collapse() -> None:
    row = supported()
    with pytest.raises(ValueError, match="duplicate fixture"):
        parity.run_parity([row, row], lambda *a: parity.rank_counts(row))


def test_valid_a_padded_vocabulary_is_unsupported_not_invalid_contract(lane_a: Any) -> None:
    from uarch_contract.request import LegacyCharacterizationRequest

    from .test_u_p1 import request_data

    data = request_data()
    data["model_shape"]["vocab_size"] += 1
    request = LegacyCharacterizationRequest.model_validate(data)
    row = supported(request.tp) | {
        "model": request.model.model_dump(mode="json"),
        "model_shape": request.model_shape.model_dump(mode="json"),
    }
    with pytest.raises(AssertionError, match="vocab_size"):
        parity.run_parity([row], lambda *a: parity.rank_counts(row), self_test=False)


def test_over_budget_stays_failed_and_later_fixture_is_reported() -> None:
    first = supported() | {"id": "over-budget"}
    last = supported() | {"id": "later-supported"}
    rows = [first, last]
    iterator = iter(rows)

    def candidate(*args: Any) -> dict[str, float | None]:
        row = next(iterator)
        return parity.rank_counts(row) | {"matrix_ops": 106.0 if row is first else 100.0}

    deviations = [
        parity.Deviation("one", "matrix_ops", 0.03, "Synthetic term one"),
        parity.Deviation("two", "matrix_ops", 0.03, "Synthetic term two"),
    ]
    with pytest.raises(AssertionError, match="total absolute") as caught:
        parity.run_parity(rows, candidate, deviations={first["id"]: deviations})
    report = caught.value.report  # type: ignore[attr-defined]
    assert report["coverage"][first["id"]]["status"] == "failed"
    assert report["coverage"][last["id"]]["status"] == "passed"
    comparison = report["comparisons"][first["id"]]["matrix_ops"]
    assert comparison["raw_rel"] == 0.06
    assert comparison["signed_adjustment_rel"] == 0.06
    assert comparison["absolute_adjustment_rel"] == 0.06
    assert comparison["residual_rel"] == 0.0
