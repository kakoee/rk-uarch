"""Finite author worksheet for A 43ab3e0; no engine, corpus or execution evidence."""

import json
from fractions import Fraction as Q

PS = 10**12


def ceiling(value: Q) -> int:
    return -(-value.numerator // value.denominator)


def edge(now: int, cycles: int, frequency: int) -> int:
    # Independent search over published edges, not A's proposed inverse formula.
    low, high = 0, max(1, now * frequency // PS + 2)
    while low < high:
        mid = (low + high) // 2
        if ceiling(Q(mid * PS, frequency)) < now:
            low = mid + 1
        else:
            high = mid
    return ceiling(Q((low + cycles) * PS, frequency))


def main() -> None:
    # Constants stipulated by the proposed law; no imports from the runtime or its tests.
    core, noc, dram = 10**9, 10**9, 10**9
    channel_rate = Q(PS * 71, 78 * 8)
    service = Q(256 * PS, 1) / channel_rate
    assert channel_rate == Q(4437500000000, 39)
    assert service == Q(159744, 71)
    assert [edge(t, n, 1200000000) for t, n in [(0, 3), (834, 0), (835, 0),
                                                           (835, 1), (0, 10**9)]] == [
        2500, 834, 1667, 2500, 833333333334,
    ]

    # Seven fixed scalar examples. Tuple: request arrival, DRAM alignment/latency end,
    # channel end, response alignment/arrival, core alignment/final completion.
    examples = [
        ("read-1g", False, core, noc, dram,
         (4000, 4000, 52000, 54250, 55000, 59000, 59000, 60000)),
        ("write-1g", True, core, noc, dram,
         (5000, 5000, 53000, 55250, 56000, 60000, 60000, 60000)),
        ("read-noc1.2", False, core, 1200000000, dram,
         (3334, 4000, 52000, 54250, 55000, 58334, 59000, 60000)),
        ("write-noc1.2", True, core, 1200000000, dram,
         (5000, 5000, 53000, 55250, 55834, 59167, 60000, 60000)),
        ("read-three-domains", False, 800000000, 1200000000, 900000000,
         (3334, 3334, 56667, 58917, 59167, 62500, 62500, 63750)),
        ("write-three-domains", True, 800000000, 1200000000, 900000000,
         (5000, 5556, 58889, 61139, 61667, 65000, 65000, 65000)),
    ]
    rows: dict[str, tuple[int, ...]] = {}
    for name, write, fc, fn, fd, expected in examples:
        outgoing = edge(0, 1, fc) if write else 0
        arrival = edge(outgoing, 4, fn)
        latency = edge(arrival, 48, fd)
        end = ceiling(Q(latency) + service)
        response = edge(end, 4, fn)
        align = edge(response, 0, fc)
        final = align if write else edge(align, 1, fc)
        actual = (arrival, edge(arrival, 0, fd), latency, end,
                  edge(end, 0, fn), response, align, final)
        assert actual == expected, (name, actual, expected)
        rows[name] = actual
    # Second burst read, exact channel carry, no occupied port at response arrival.
    second_end = ceiling(52000 + 2 * service)
    assert (second_end, edge(second_end, 4, noc)) == (56500, 61000)
    assert edge(61000, 1, core) == 62000
    rows["read2-same-burst"] = (54250, second_end, 61000, 62000)

    ends = [ceiling(52000 + j * service) for j in range(1, 6)]
    no_refresh_ends = [52000 + j * 2048 for j in range(1, 6)]
    good = [edge(edge(t, 4, noc), 1, core) for t in ends]
    bad = [edge(edge(t, 4, noc), 1, core) for t in no_refresh_ends]
    assert good == [60000, 62000, 64000, 66000, 69000]
    assert bad == [60000, 62000, 64000, 66000, 68000]
    assert good[:4] == bad[:4]  # Explicitly preserve masking; not mutant kills.
    assert ends[0] == 54250 and no_refresh_ends[0] == 54048
    assert good[4] != bad[4]

    # Separately named arithmetic alternatives, NOT executed implementation mutations.
    fixed_return = ceiling(54250 + Q(4 * PS, 1200000000))
    assert fixed_return == 57584
    assert edge(fixed_return, 1, core) == 59000  # Correct result is 60000.
    assert 54250 + 4000 == 58250 != rows["read-1g"][5]  # Only intermediate differs.
    exact_twelfth = ceiling(52000 + 12 * service)
    rounded_feedback = 52000 + 12 * ceiling(service)
    assert (exact_twelfth, rounded_feedback) == (78999, 79000)
    assert edge(54250, 0, dram) == 55000 != rows["read-1g"][3]
    assert 833 * 10**9 != edge(0, 10**9, 1200000000)
    assert 60000 + 32000 == 92000 != rows["read-1g"][7]  # Erroneous DMA overhead.

    # Specified same-channel placement/idle boundaries, no general scheduling engine.
    assert 60000 + 60000 == 120000  # Two reads with one credit.
    assert edge(edge(52000 + ceiling(service), 4, noc), 1, core) == 60000
    # Third read with two credits can issue at 60000 and complete at 120000.
    assert 60000 + 60000 == 120000 != good[2]
    # Credit release at memory latency completion gives issue 52000, not 60000.
    assert rows["read-1g"][2] != rows["read-1g"][7]
    # Independent channels 6/7 give coincident arrivals; shared core port serializes them.
    assert [edge(59000, n, core) for n in (1, 2)] == [60000, 61000]
    assert edge(62000, 32, noc) == 94000
    # Receiving-mechanism attribution is a partition, not summed resource busy times.
    base_noc = 4000 + 59000 - 54250
    unequal_noc = 3334 + 62500 - 58917
    assert (base_noc, 60000 - base_noc) == (8750, 51250)
    assert (unequal_noc, 63750 - unequal_noc) == (6917, 56833)

    # Sensitivity estimates; chosen widths are NOT observed serialization sizes/RSS.
    volume = {}
    for label, requests in [("e4-33", 33), ("c1-cold", 576), ("max-b", 98304)]:
        minimum, planning = 4 * requests, 32 * requests
        volume[label] = {
            "requests": requests, "minimum_request_records": minimum,
            "planning_request_records": planning,
            "request_bytes_at_256_B_per_record": planning * 256,
            "request_bytes_at_512_B_per_record": planning * 512,
        }
    assert 16 * 4 * 1536 == 98304
    assert 98304 * 256 == 25165824
    assert volume["max-b"]["minimum_request_records"] == 393216
    assert volume["max-b"]["planning_request_records"] == 3145728
    assert volume["c1-cold"]["planning_request_records"] == 18432
    assert 65536 * 256 == 16 * 2**20  # No room for envelope at this average width.
    print(json.dumps({"kind": "author-proposal-arithmetic-only", "timing_rows_ps": rows,
                      "refresh_completion_ps": good, "no_refresh_completion_ps": bad,
                      "volume_estimates": volume}, indent=2, sort_keys=True))
    print("PASS: fixed examples and arithmetic fault distinctions; no native execution")


if __name__ == "__main__":
    main()
