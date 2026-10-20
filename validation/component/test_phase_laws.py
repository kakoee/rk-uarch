"""Synthetic scalar/witness controls only; not native component observations."""

from fractions import Fraction

import pytest

from rkuarch.verification.component.checks import CheckFailure
from rkuarch.verification.component.phase_laws import channel, clocked, resident_phases, tight_chain


def test_resident_mechanism_literals():
    assert resident_phases(3, 5, 7) == dict(overhead=32, staging=1, wave=513, drain=1)
    assert resident_phases(16, 256, 256) == dict(overhead=32, staging=136, wave=526, drain=8)
    assert resident_phases(256, 256, 255) == dict(overhead=32, staging=256, wave=766, drain=128)


def test_unequal_clock_alignment_and_rational_channel():
    clocked(3334, 3334, 56667, 900000000, 48)
    clocked(58917, 59167, 62500, 1200000000, 4)
    clocked(62500, 62500, 63750, 800000000, 1)
    channel(Fraction(56667), Fraction(4183101, 71), 256, Fraction(4437500000000, 39))
    with pytest.raises(CheckFailure, match="alignment"):
        clocked(3334, 4167, 56667, 900000000, 48)
    with pytest.raises(CheckFailure, match="mechanism"):
        channel(Fraction(56667), Fraction(58917), 256, Fraction(4437500000000, 39))


def test_tight_zero_link_and_port_wait_without_busy_invention():
    activities = [
        dict(id="response", start=0, end=59000, predecessors=[]),
        dict(id="first-port", start=59000, end=60000, predecessors=["response"]),
        dict(id="second-port", start=60000, end=61000, predecessors=["response", "first-port"]),
        dict(id="zero-hop", start=61000, end=61000, predecessors=["second-port"]),
    ]
    selected = ["response", "first-port", "second-port", "zero-hop"]
    tight_chain(activities, selected, 61000)
    activities[2]["predecessors"] = ["response"]
    with pytest.raises(CheckFailure, match="tight"):
        tight_chain(activities, selected, 61000)


@pytest.mark.parametrize("domain", ["core", "noc", "dram"])
@pytest.mark.parametrize(
    "population,queue,owner",
    [("service", "channel_service:6", 30), ("inflight", "dma_inflight:0", 12)],
)
def test_ordinary_clock_cannot_bypass_nonclocked_binding(domain, population, queue, owner):
    from rkuarch.verification.component.checks import check_queue_domain

    row = dict(
        queue_id=queue,
        item_id="r",
        population=population,
        enter_ps=0,
        leave_ps=1,
        owner_id=owner,
        clock_domain=None,
    )
    owners = {12: "dma:0:0", 30: "channel:6"}
    requests = {"r": dict(channel_id=6, dma_engine_id=0)}
    check_queue_domain(row, owners, requests, 2, allow_nonclocked=True)
    row["clock_domain"] = domain
    with pytest.raises(CheckFailure, match="ordinary clock"):
        check_queue_domain(row, owners, requests, 2, allow_nonclocked=True)
    row["clock_domain"] = None
    check_queue_domain(row, owners, requests, 2, allow_nonclocked=True)
