"""F5 clock-consistent duration regression; synthetic carriers, never native results."""

from copy import deepcopy

import pytest
from uarch_contract.mapped import validate_result

from validation.component.checks import CheckFailure
from validation.component.consistent_carriers import EXPECTED, activity, control, synchronize
from validation.component.observations_v2 import check_v2


def test_d01_response_duration_control() -> None:
    job, result = control("D01")
    # Independent literal law: a 1 GHz NoC has 1000 ps edges. Two response hops
    # require four cycles from the already aligned 55000 ps grant: end = 59000.
    assert job.freq_hz.noc == 1_000_000_000
    response = activity(result, "back")
    assert (response["start_ps"], response["end_ps"]) == (55000, 59000)
    clock = next(
        row for row in result["observations"]["clocks"]["records"] if row["activity_id"] == "back"
    )
    assert (clock["grant_ps"], clock["n_cycles"], clock["completion_ps"]) == (55000, 4, 59000)
    assert result["duration_ps"] == 60000
    validate_result(deepcopy(result), job)
    check_v2(job.model_dump(mode="json"), deepcopy(result), EXPECTED)


def test_d01_clock_consistent_response_duration_forgery() -> None:
    job, valid = control("D01")
    result = deepcopy(valid)
    activity(result, "back")["end_ps"] = 58500
    activity(result, "port-a").update(ready_ps=58500, start_ps=58500)
    # Copy all edited joins, including completion in the clock witness, and
    # reseal. Work remains four cycles; the lawful receiving edge stays 59000.
    result = synchronize(result)
    clock = next(
        row for row in result["observations"]["clocks"]["records"] if row["activity_id"] == "back"
    )
    assert (clock["grant_ps"], clock["n_cycles"], clock["completion_ps"]) == (55000, 4, 58500)
    assert activity(result, "port-a")["end_ps"] == 59000
    assert activity(result, "port") == activity(valid, "port")
    assert result["duration_ps"] == valid["duration_ps"] == 60000
    for key in ("counts", "work_counts"):
        assert result[key] == valid[key]
    for table in ("jobs", "dma"):
        assert result["observations"][table] == valid["observations"][table]
    # Structural admission is part of the witness: only B's mechanism law
    # supplies the rejection. An alternate refusal must fail this regression.
    validate_result(deepcopy(result), job)
    with pytest.raises(CheckFailure, match="^mechanism duration$"):
        check_v2(job.model_dump(mode="json"), result, EXPECTED)
