"""PRIVATE proposal schema controls; never public execution or authority."""

from typing import Any

import pytest
from uarch_contract import mapped as m


def activity() -> dict[str, Any]:
    return dict(
        activity_id="a",
        job_id="j",
        request_id="r",
        subphase="dma_issue",
        kind="alignment",
        ready_ps=26667,
        start_ps=26667,
        end_ps=27000,
        owner_id=0,
        category="memory",
        receiving_domain="core",
        occupies_resource=False,
        dispatch_ordinal=0,
        completion_ordinal=1,
        predecessors=[],
    )


def test_v3_issue_is_explicit_new_carrier() -> None:
    cls = getattr(m, "ComponentActivityV3", None)
    assert cls is not None, "missing /3 issue carrier"
    assert cls.model_validate(activity()).subphase == "dma_issue"


def test_v2_remains_strict() -> None:
    with pytest.raises(ValueError):
        m.ComponentActivity.model_validate(activity())


def test_v3_pending_queue_is_explicit_new_carrier() -> None:
    cls = getattr(m, "ComponentQueueObservationV3", None)
    assert cls is not None, "missing /3 pending carrier"
    row = dict(
        queue_id="dma_pending:0",
        item_id="r",
        population="pending",
        enter_ps=26667,
        leave_ps=27000,
        owner_id=0,
        clock_domain=None,
        activity_id=None,
    )
    assert cls.model_validate(row).population == "pending"
    with pytest.raises(ValueError):
        m.ComponentQueueObservation.model_validate(row)


def test_v3_reservation_field_required() -> None:
    cls = getattr(m, "DmaObservationV3", None)
    assert cls is not None, "missing /3 reservation carrier"
    assert cls.model_fields["reservation_ps"].is_required()


def test_observation_versions_remain_disjoint() -> None:
    cls = getattr(m, "ComponentObservationsV3", None)
    assert cls is not None, "missing /3 observation carrier"
    assert (
        cls.model_fields["format"].annotation
        != m.ComponentObservations.model_fields["format"].annotation
    )


def test_new_model_version_is_component_only() -> None:
    base: dict[str, Any] = dict(version="2", implementation_hash="sha256:" + "1" * 64)
    assert m.NativeModelIdentity(name="native-intervals", **base).version == "2"
    with pytest.raises(ValueError, match="component model version"):
        m.NativeModelIdentity(name="fixed-delay", **base)


def test_explicit_reservation_opportunity_carrier_required() -> None:
    cls = getattr(m, "DmaReservationOpportunity", None)
    assert cls is not None, "missing actual reservation opportunity carrier"
    row = cls(opportunity_ordinal=0, t_ps=0, event_cursor=0, granted_request_ids=("r01",))
    assert row.event_cursor == 0 and row.granted_request_ids == ("r01",)
    assert "reservation_opportunities" in m.ComponentObservationsV3.model_fields
    assert "reservation_opportunities" not in m.ComponentObservations.model_fields
