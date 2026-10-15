"""Hand arithmetic and proposed structural controls, NEVER native execution evidence."""

import pytest


def raw_edge(freq: int, start: int, cycles: int) -> int:
    # Independent integer inequalities, not a scheduler or a native implementation.
    k = 0 if start == 0 else ((start - 1) * freq) // 10**12 + 1
    return ((k + cycles) * 10**12 + freq - 1) // freq


@pytest.mark.parametrize(
    ("release", "dependency_end", "owner_end", "cycles", "ready", "grant", "end", "aligned"),
    [
        (835, 0, 0, 0, 835, 835, 835, 1667),
        (835, 0, 0, 1, 835, 835, 2500, 1667),
        (835, 500, 0, 1, 835, 835, 2500, 1667),
        (835, 1200, 0, 1, 1200, 1200, 2500, 1667),
        (835, 0, 2000, 1, 835, 2000, 3334, 2500),
        (835, 0, 2000, 0, 835, 2000, 2000, 2500),
        (1000, 1000, 1000, 0, 1000, 1000, 1000, 1667),
        (0, 0, 0, 3, 0, 0, 2500, 0),
        (0, 0, 0, 10**9, 0, 0, 833333333334, 0),
    ],
)
def test_literal_release_and_owned_clock(
    release, dependency_end, owner_end, cycles, ready, grant, end, aligned
):
    assert ready == max(release, dependency_end)
    assert grant == max(ready, owner_end)
    assert raw_edge(1200000000, grant, 0) == aligned
    assert (grant if cycles == 0 else raw_edge(1200000000, grant, cycles)) == end


def test_raw_owned_split_and_discriminating_mutants():
    assert raw_edge(1200000000, 835, 0) == 1667
    assert 835 != raw_edge(1200000000, 835, 0)  # align-zero-job mutant
    assert raw_edge(1200000000, 2000, 1) == 3334
    assert raw_edge(1200000000, 835, 1) == 2500  # nominal-start mutant
    assert 3334 != 2500
    assert 3 * 833 != raw_edge(1200000000, 0, 3)  # rounded-period mutant


def test_zero_probe_overflow_does_not_change_owned_completion():
    maximum = 2**64 - 1
    assert raw_edge(10**9, maximum, 0) > maximum
    # This diagnostic is TimeOverflow/null; a zero-owned job still ends at its grant.
    assert maximum == maximum + 0
    assert raw_edge(10**9, maximum, 1) > maximum


def test_all_zero_and_release_idle_literals():
    assert sum([]) == 0  # required empty critical partition, never a dummy event
    assert 835 + (2500 - 835) == 2500
    assert 2500 - 835 == 1665  # owner busy excludes release idle
    assert 835 + 0 == 835  # released zero job: idle only, owner busy exactly zero
