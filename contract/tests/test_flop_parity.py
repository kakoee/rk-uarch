"""Harness self-tests only. U-P3 supplies the first real workload callable."""

from __future__ import annotations

from typing import Any

import pytest

from .parity import Deviation, compare_counts, run_parity


def sample() -> dict[str, Any]:
    return {
        "id": "synthetic/decode/tp8",
        "tp": 8,
        "model": {"n_heads": 64, "kv_heads": 8},
        "model_shape": {"vocab_size": 128256, "d_ff": 28672, "expert_d_ff": None},
        "precision": {"compute": "fp16", "kv_cache": "fp16"},
        "query": {"phase": "decode", "batch": 1, "total_context_tokens": 512},
        "counts": {"matrix_ops": 800.0, "memory_read_bytes": 160.0, "memory_write_bytes": None},
    }


def test_parity_harness_self_test() -> None:
    result = run_parity(
        [sample()],
        lambda model, shape, precision, query: {
            "matrix_ops": 100.0,
            "memory_read_bytes": 20.0,
            "memory_write_bytes": None,
        },
        self_test=True,
    )
    assert result["kind"] == "harness self-test (not workload parity)"


def test_wrong_callable_names_fixture_and_both_numbers() -> None:
    with pytest.raises(AssertionError, match=r"synthetic/decode/tp8.*110.0.*100.0"):
        run_parity(
            [sample()],
            lambda *args: {
                "matrix_ops": 110.0,
                "memory_read_bytes": 20.0,
                "memory_write_bytes": None,
            },
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0, None])
def test_nonfinite_negative_or_missing_count_fails(bad: float | None) -> None:
    with pytest.raises(AssertionError):
        compare_counts("fixture", {"matrix_ops": bad}, {"matrix_ops": 100.0})


def test_null_is_not_zero() -> None:
    with pytest.raises(AssertionError, match="memory_write_bytes"):
        compare_counts("fixture", {"memory_write_bytes": 0.0}, {"memory_write_bytes": None})


def test_declared_deviations_must_explain_signed_channel_delta() -> None:
    deviation = Deviation("extra-op", "matrix_ops", 0.04, "An explicitly counted operator")
    compare_counts("fixture", {"matrix_ops": 104.0}, {"matrix_ops": 100.0}, [deviation])
    with pytest.raises(AssertionError):
        compare_counts("fixture", {"matrix_ops": 110.0}, {"matrix_ops": 100.0}, [deviation])
    with pytest.raises(ValueError, match="5%"):
        Deviation("too-large", "matrix_ops", 0.06, "Reason")
    with pytest.raises(ValueError):
        Deviation("", "matrix_ops", 0.01, "")


def test_harness_supplies_tp_and_never_mutates_oracle() -> None:
    fixture = sample()

    def candidate(model: Any, shape: Any, precision: Any, query: Any) -> dict[str, Any]:
        assert query["tp"] == 8
        query["batch"] = 999
        return {"matrix_ops": 100.0, "memory_read_bytes": 20.0, "memory_write_bytes": None}

    run_parity([fixture], candidate)
    assert fixture["query"]["batch"] == 1


def test_unknown_deviation_fixture_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown fixture"):
        run_parity(
            [sample()],
            lambda *args: {},
            deviations={"typo": [Deviation("extra", "matrix_ops", 0.01, "Reason")]},
        )
