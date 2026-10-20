"""Agent arithmetic only; no model execution or human working."""

from fractions import Fraction

import pytest

from rkuarch.verification.component.arithmetic import burst, dma, edge_after, resident, split


def test_resident_literals():
    assert resident(16, 256, 256) == (2097152, 2097152, 139264, 8192, 16384, 702000)
    assert resident(3, 5, 7) == (210, 393216, 100, 42, 84, 547000)
    assert resident(256, 256, 256)[-1] == 1182000
    assert resident(1, 256, 256)[-1] == 673000


def test_exact_e4_and_refresh_discriminator():
    assert dma() == (0, 4000, 52000, 54250, 59000, 60000)
    assert dma(write=True) == (1000, 5000, 53000, 55250, 60000, 60000)
    assert dma(noc=1200000000) == (0, 3334, 52000, 54250, 58334, 60000)
    assert dma(core=800000000, noc=1200000000, dram=900000000) == (
        0,
        3334,
        56667,
        58917,
        62500,
        63750,
    )
    assert dma(core=800000000, noc=1200000000, dram=900000000, write=True) == (
        1250,
        5000,
        58889,
        61139,
        65000,
        65000,
    )
    assert burst(5)[1] == [60000, 62000, 64000, 66000, 69000]
    assert burst(5, refresh=False)[1] == [60000, 62000, 64000, 66000, 68000]
    assert burst(12)[0][-1] == Fraction(5608928, 71)
    # B's remote cold placement: X/W on ch6; compute waits for second commit.
    assert 62000 + 547000 + 60000 == 669000
    # A's ch0/ch1 reads share the local controller; shared port completes at 53ns.
    assert 53000 + 547000 + 56000 == 656000


@pytest.mark.parametrize("m", [1, 3, 16, 64, 255, 256])
@pytest.mark.parametrize("k", [5, 256])
@pytest.mark.parametrize("n", [7, 256])
def test_24_resident_clock_pairs(m, k, n):
    base, fast = resident(m, k, n), resident(m, k, n, core=2_000_000_000)
    assert base[:-1] == fast[:-1]
    assert base[-1] == 2 * fast[-1]


def test_edges_striping_and_valid_clock_premise():
    assert [
        edge_after(1200000000, t, n) for t, n in [(0, 3), (834, 0), (835, 0), (835, 1), (0, 10**9)]
    ] == [2500, 834, 1667, 2500, 833333333334]
    assert split(1536, 513) == [(6, 256, 256), (7, 256, 256), (0, 1, 256)]
    assert split(1791, 2) == [(6, 1, 256), (7, 1, 256)]
    assert edge_after(1200000000, 61000, 0) == 61667
