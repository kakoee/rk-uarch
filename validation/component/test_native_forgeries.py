"""Unit-test the new attack constructor on SYNTHETIC anchors, never native results."""

import pytest
from uarch_contract.mapped import validate_result

from rkuarch.verification.component.checks import CheckFailure
from validation.component.consistent_carriers import EXPECTED, control
from validation.component.native_forgeries import forge
from validation.component.observations_v2 import check_v2
from validation.component.transient_carrier import transient_control


@pytest.mark.parametrize(
    "attack,structural,independent",
    [
        ("duration-law", True, "mechanism duration"),
        ("missing-occupancy", False, "required occupancy"),
        ("false-latency-occupancy", False, "required occupancy"),
        ("channel-clock", False, "nonclocked exact binding"),
        ("dma-clock", False, "nonclocked exact binding"),
        ("ordinary-clock", False, "ordinary queue exact binding"),
        ("channel-population", False, "channel population lifecycle"),
        ("o2-early-allocation", True, "accumulator lifetime mechanism"),
        ("o2-late-free", True, "accumulator lifetime mechanism"),
        ("o2-persistent", True, "accumulator lifetime mechanism"),
        ("o2-first-consumer", True, "allocation access lifetime"),
        ("missing-cause", True, "complete eligible causes"),
    ],
)
def test_synthetic_attack_constructor(attack, structural, independent):
    job, valid = (
        transient_control()
        if attack.startswith("o2-") or attack == "missing-cause"
        else control("D01")
    )
    validate_result(valid, job)
    check_v2(job.model_dump(mode="json"), valid, EXPECTED)
    bad = forge(valid, attack)
    assert bad != valid
    assert bad["counts"] == valid["counts"]
    assert bad["traffic_counts"] == valid["traffic_counts"]
    assert bad["duration_ps"] == valid["duration_ps"]
    if structural:
        validate_result(bad, job)
    else:
        with pytest.raises(ValueError, match="^IncompleteObservations"):
            validate_result(bad, job)
    with pytest.raises(CheckFailure, match="^" + independent + "$"):
        check_v2(job.model_dump(mode="json"), bad, EXPECTED)
