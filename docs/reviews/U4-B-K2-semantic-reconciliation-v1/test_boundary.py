"""Installed-carrier gap controls; schema positives are never native observations."""

import pytest
from pydantic import ValidationError
from uarch_contract.mapped import EventObservation, QueueObservation


@pytest.mark.parametrize("kind", ["TASK_RELEASE", "DEPENDENCY_READY", "OWNER_GRANT"])
def test_installed_event_vocabulary_refuses_proposed_kinds(kind):
    row = dict(
        event_seq=0,
        observation_ordinal=0,
        t_ps=835,
        phase=0,
        target_id=0,
        kind="TASK_READY",
        job_id="z",
    )
    assert EventObservation.model_validate(row).kind == "TASK_READY"
    with pytest.raises(ValidationError, match="literal_error"):
        EventObservation.model_validate(dict(row, kind=kind))
    assert EventObservation.model_validate(row).kind == "TASK_READY"


def test_installed_queue_requires_physical_domain():
    row = dict(
        queue_id="owner0",
        item_id="z",
        population="waiting",
        enter_ps=835,
        leave_ps=1000,
        owner_id=0,
        clock_domain="core",
    )
    assert QueueObservation.model_validate(row).clock_domain == "core"
    with pytest.raises(ValidationError, match="literal_error"):
        QueueObservation.model_validate(dict(row, clock_domain=None))
    # The positive schema control does NOT license attaching core to a ps-only owner.
    assert QueueObservation.model_validate(row).clock_domain == "core"
