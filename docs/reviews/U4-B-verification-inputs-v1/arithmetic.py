"""Independent scalar worksheets, not a scheduler or a native evidence producer."""

from fractions import Fraction

PS_PER_S = 10**12
U64_MAX = 2**64 - 1


def ceil_ratio(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def edge(freq_hz: int, index: int) -> int:
    if freq_hz <= 0 or index < 0:
        raise ValueError("invalid clock/index")
    return ceil_ratio(Fraction(index * PS_PER_S, freq_hz))


def next_edge(freq_hz: int, time_ps: int, cycles: int) -> int:
    """Search the edge sequence, independently of the production inverse formula."""
    if min(time_ps, cycles) < 0 or freq_hz <= 0 or time_ps > U64_MAX:
        raise ValueError("invalid clock/time")
    lo, hi = 0, 1
    while edge(freq_hz, hi) < time_ps:
        hi *= 2
    while lo < hi:
        mid = (lo + hi) // 2
        if edge(freq_hz, mid) < time_ps:
            lo = mid + 1
        else:
            hi = mid
    result = edge(freq_hz, lo + cycles)
    if result > U64_MAX:
        raise OverflowError("time exceeds u64")
    return result


def resident_tile(m: int, k: int, n: int) -> dict[str, int]:
    if not all(1 <= x <= 256 for x in (m, k, n)):
        raise ValueError("outside single-tile premise")
    x_bytes, w_bytes, y_bytes = 2 * m * k, 2 * k * n, 2 * m * n
    stage = ceil_ratio(Fraction(x_bytes + w_bytes, 1024))
    drain = ceil_ratio(Fraction(y_bytes, 1024))
    return {
        "useful_ops": 2 * m * k * n,
        "issued_ops": 2 * m * 256 * 256,
        "read_bytes": x_bytes + w_bytes,
        "write_bytes": y_bytes,
        "accumulator_bytes": 4 * m * n,
        "cycles": 32 + stage + 510 + m + drain,
    }


def fragments(address_bytes: int, payload_bytes: int) -> list[tuple[int, int, int]]:
    """Only the fixed 256-byte/8-channel address partition, no DMA execution."""
    if address_bytes < 0 or payload_bytes <= 0:
        raise ValueError("invalid range")
    out = []
    stop = address_bytes + payload_bytes
    while address_bytes < stop:
        size = min(stop - address_bytes, 256 - address_bytes % 256)
        out.append(((address_bytes // 256) % 8, size, 256))
        address_bytes += size
    return out


def clipped_area(intervals: list[tuple[int, int]], start: int, end: int) -> int:
    if start >= end or any(a > b for a, b in intervals):
        raise ValueError("invalid interval")
    return sum(max(0, min(b, end) - max(a, start)) for a, b in intervals)


def isolated_dma(core_hz: int, noc_hz: int, dram_hz: int, *, write: bool = False):
    """One idle 256-byte/two-hop request only; no traffic or queue input API."""
    port = next_edge(core_hz, 0, 1) if write else 0
    arrival = next_edge(noc_hz, port, 4)
    latency = next_edge(dram_hz, arrival, 48)
    finish = Fraction(latency) + Fraction(159744, 71)
    published = ceil_ratio(finish)
    response = next_edge(noc_hz, published, 4)
    complete = next_edge(core_hz, response, 0 if write else 1)
    return port, arrival, latency, published, response, complete


def simultaneous_channel_finishes(count: int, *, refresh: bool = True):
    """Closed-form FIFO bandwidth sequence for an admitted burst at t=0 only."""
    if not 1 <= count <= 32:
        raise ValueError("burst exceeds this worksheet's premise")
    service = Fraction(159744, 71) if refresh else Fraction(2048)
    return [Fraction(52000) + i * service for i in range(1, count + 1)]
