"""O2: independent synthetic /2 transient @2 lifetime controls, never native output."""

from copy import deepcopy

import pytest
from uarch_contract.mapped import validate_result

from rkuarch.verification.component.checks import CheckFailure
from validation.component.consistent_carriers import EXPECTED
from validation.component.observations_v2 import check_v2
from validation.component.transient_carrier import READY, SPANS, transient_attack, transient_control


def test_transient_two_final_consumers_control() -> None:
    job, result = transient_control()
    assert job.workload_closure.mapping_policy.version == "2"
    buf = next(b for b in job.mapped_point.task_graph.buffers if b.id == "bacc")
    assert (buf.producer_id, list(buf.final_consumer_ids)) == ("b", ["c", "d"])
    assert (buf.size_bytes, buf.offset_bytes) == (84, 256)
    row = next(
        a for a in result["observations"]["allocations"]["records"] if a["buffer_id"] == "bacc"
    )
    assert (row["allocate_ps"], row["free_ps"], row["initially_live"]) == (547000, 2188000, False)
    assert result["duration_ps"] == 2735000
    assert {
        j["job_id"]: (j["start_ps"], j["end_ps"]) for j in result["observations"]["jobs"]["records"]
    } == SPANS
    assert {j["job_id"]: j["ready_ps"] for j in result["observations"]["jobs"]["records"]} == READY
    assert result["counts"]["matrix_ops"] == 1050
    assert result["work_counts"]["issued_matrix_ops"] == 1966080
    assert (result["ext_counts"]["sram_read_bytes"], result["ext_counts"]["sram_write_bytes"]) == (
        500,
        210,
    )
    assert result["counts"]["memory_read_bytes"] == result["counts"]["memory_write_bytes"] == 0
    validate_result(deepcopy(result), job)
    check_v2(job.model_dump(mode="json"), deepcopy(result), EXPECTED)


@pytest.mark.parametrize(
    "field,value", [("allocate_ps", 0), ("free_ps", 2735000), ("free_ps", None)]
)
def test_transient_overlong_lifetime_is_not_persistent(field: str, value: int | None) -> None:
    job, result = transient_attack(field, value)
    _, valid = transient_control()
    # All timing, consumer inventory, useful work and traffic joins are truthful;
    # only the named allocation endpoint and integrity seal differ.
    expected = deepcopy(valid)
    next(a for a in expected["observations"]["allocations"]["records"] if a["buffer_id"] == "bacc")[
        field
    ] = value
    expected["result_hash"] = result["result_hash"]
    assert result == expected
    validate_result(deepcopy(result), job)
    with pytest.raises(CheckFailure, match="^accumulator lifetime mechanism$"):
        check_v2(job.model_dump(mode="json"), result, EXPECTED)


def test_transient_free_at_first_final_consumer_is_too_early() -> None:
    job, result = transient_attack("free_ps", 1641000)
    validate_result(deepcopy(result), job)
    # The second terminal consumer d ends at 2188000. Access bounds refuse first;
    # this is not an essential-guard witness for accumulator lifetime mechanism.
    with pytest.raises(CheckFailure, match="^allocation access lifetime$"):
        check_v2(job.model_dump(mode="json"), result, EXPECTED)
