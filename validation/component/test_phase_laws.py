"""Synthetic scalar/witness controls only; not native component observations."""

from fractions import Fraction

import pytest

from validation.component.checks import CheckFailure
from validation.component.phase_laws import channel, clocked, resident_phases, tight_chain


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
