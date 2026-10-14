"""Worksheet tests establish arithmetic only; native faults remain planned."""

import unittest
from fractions import Fraction
from itertools import product

from arithmetic import (
    PS_PER_S,
    U64_MAX,
    ceil_ratio,
    clipped_area,
    edge,
    fragments,
    isolated_dma,
    next_edge,
    resident_tile,
    simultaneous_channel_finishes,
)


class Worksheets(unittest.TestCase):
    def test_edges_and_refusals(self):
        for start, cycles, expected in [
            (0, 3, 2500),
            (834, 0, 834),
            (835, 0, 1667),
            (835, 1, 2500),
            (0, 10**9, 833333333334),
        ]:
            self.assertEqual(next_edge(1200000000, start, cycles), expected)
        for hz, index in product((800000000, 900000000, 1000000000, 1200000000), range(25)):
            time = edge(hz, index)
            self.assertTrue(0 <= time * hz - index * PS_PER_S < hz)
            self.assertEqual(next_edge(hz, time, 0), time)
        for args in [(0, 0, 1), (1, -1, 0), (1, 0, -1)]:
            with self.assertRaises(ValueError):
                next_edge(*args)
        with self.assertRaises(OverflowError):
            next_edge(1000000000, U64_MAX, 1)

    def test_order_and_causality(self):
        events = [(1000, 0, 2, 9), (1000, 1, 0, 2), (1000, 0, 1, 8), (1000, 0, 1, 7)]
        self.assertEqual([x[3] for x in sorted(events)], [7, 8, 9, 2])
        self.assertEqual(max(3000, 5000) + 2000, 7000)
        self.assertEqual(3000 + 5000 + 2000, 10000)
        self.assertEqual(max(3000, 1000) + 0 + 2000, 5000)
        self.assertEqual(max(3000, 1000 + 2000), 3000)  # wrong bypass discriminator

    def test_components(self):
        self.assertEqual(
            resident_tile(16, 256, 256),
            {
                "useful_ops": 2097152,
                "issued_ops": 2097152,
                "read_bytes": 139264,
                "write_bytes": 8192,
                "accumulator_bytes": 16384,
                "cycles": 702,
            },
        )
        self.assertEqual(
            resident_tile(3, 5, 7),
            {
                "useful_ops": 210,
                "issued_ops": 393216,
                "read_bytes": 100,
                "write_bytes": 42,
                "accumulator_bytes": 84,
                "cycles": 547,
            },
        )
        large, tail = resident_tile(256, 256, 256), resident_tile(1, 256, 256)
        self.assertEqual((large["cycles"], tail["cycles"]), (1182, 673))
        self.assertEqual(large["useful_ops"] + tail["useful_ops"], 33685504)
        self.assertEqual(large["read_bytes"] + tail["read_bytes"], 393728)
        self.assertEqual(large["write_bytes"] + tail["write_bytes"], 131584)
        # Twenty-four distinct resident work points; no memory-only reciprocal premise.
        for m, k, n in product((1, 3, 16, 64, 255, 256), (5, 256), (7, 256)):
            cycles = resident_tile(m, k, n)["cycles"]
            self.assertEqual(next_edge(1000000000, 0, cycles), 2 * next_edge(2000000000, 0, cycles))

    def test_fragments_and_windows(self):
        self.assertEqual(fragments(1536, 513), [(6, 256, 256), (7, 256, 256), (0, 1, 256)])
        self.assertEqual(fragments(1791, 2), [(6, 1, 256), (7, 1, 256)])
        self.assertEqual(sum(x[1] for x in fragments(1536, 513)), 513)
        self.assertEqual(sum(x[2] for x in fragments(1536, 513)), 768)
        self.assertEqual(clipped_area([(0, 4000), (2000, 6000)], 0, 8000), 8000)
        self.assertEqual(clipped_area([(0, 4000), (2000, 6000)], 1000, 5000), 6000)
        self.assertEqual(clipped_area([(2000, 6000)], 1000, 5000), 3000)
        self.assertEqual(32 + 128 - 64, 96)

    def test_crossings(self):
        cases = [
            (
                (10**9, 10**9, 10**9),
                (0, 4000, 52000, 54250, 59000, 60000),
                (1000, 5000, 53000, 55250, 60000, 60000),
            ),
            (
                (10**9, 1200000000, 10**9),
                (0, 3334, 52000, 54250, 58334, 60000),
                (1000, 5000, 53000, 55250, 59167, 60000),
            ),
            (
                (800000000, 1200000000, 900000000),
                (0, 3334, 56667, 58917, 62500, 63750),
                (1250, 5000, 58889, 61139, 65000, 65000),
            ),
        ]
        for clocks, read, write in cases:
            self.assertEqual(isolated_dma(*clocks), read)
            self.assertEqual(isolated_dma(*clocks, write=True), write)

    def test_discriminators(self):
        correct = simultaneous_channel_finishes(12)
        self.assertEqual(correct[0], Fraction(3851744, 71))
        self.assertEqual(ceil_ratio(correct[11]), 78999)
        self.assertEqual(52000 + 12 * ceil_ratio(Fraction(159744, 71)), 79000)
        ends = []
        for refresh in (True, False):
            responses = [
                next_edge(10**9, ceil_ratio(f), 4)
                for f in simultaneous_channel_finishes(5, refresh=refresh)
            ]
            ends.append(
                [max(responses[j] + (i - j + 1) * 1000 for j in range(i + 1)) for i in range(5)]
            )
        self.assertEqual(
            ends, [[60000, 62000, 64000, 66000, 69000], [60000, 62000, 64000, 66000, 68000]]
        )
        self.assertEqual(ceil_ratio(simultaneous_channel_finishes(1, refresh=False)[0]), 54048)
        self.assertEqual(next_edge(10**9, 62000, 32), 94000)
        self.assertEqual(Fraction(256 * PS_PER_S, 60000), Fraction(12800000000, 3))


if __name__ == "__main__":
    unittest.main()
