"""Finite E3/E4 worksheets. No graph execution, production helpers or scheduler."""

from fractions import Fraction

PS = 10**12
SERVICE = Fraction(159744, 71)


def ceil(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def edge_after(hz: int, t: int, cycles: int) -> int:
    """Search independently enumerated rational edges, without the native inverse law."""
    if hz <= 0 or min(t, cycles) < 0:
        raise ValueError("invalid edge premise")
    lo, hi = 0, 1
    while ceil(Fraction(hi * PS, hz)) < t:
        hi *= 2
    while lo < hi:
        mid = (lo + hi) // 2
        if ceil(Fraction(mid * PS, hz)) < t:
            lo = mid + 1
        else:
            hi = mid
    answer = ceil(Fraction((lo + cycles) * PS, hz))
    if answer >= 2**64:
        raise OverflowError("TimeOverflow")
    return answer


def resident(m: int, k: int, n: int, *, core: int = 10**9) -> tuple[int, ...]:
    if not all(1 <= x <= 256 for x in (m, k, n)):
        raise ValueError("single resident WS tile only")
    read, write = 2 * m * k + 2 * k * n, 2 * m * n
    cycles = 32 + ceil(Fraction(read, 1024)) + 510 + m + ceil(Fraction(write, 1024))
    return 2 * m * k * n, 2 * m * 256 * 256, read, write, 4 * m * n, edge_after(core, 0, cycles)


def dma(
    *, core: int = 10**9, noc: int = 10**9, dram: int = 10**9, write: bool = False
) -> tuple[int, ...]:
    """Exactly one idle two-hop request, 256 bytes, fixed E4 baseline bandwidth."""
    port = edge_after(core, 0, 1) if write else 0
    arrival = edge_after(noc, port, 4)
    latency = edge_after(dram, arrival, 48)
    channel = ceil(Fraction(latency) + SERVICE)
    response = edge_after(noc, channel, 4)
    done = edge_after(core, response, 0 if write else 1)
    return port, arrival, latency, channel, response, done


def burst(count: int, *, refresh: bool = True) -> tuple[list[Fraction], list[int]]:
    """Closed form for <=32 simultaneous channel6 reads; never a credit-stalled stream."""
    if not 1 <= count <= 32:
        raise ValueError("simultaneous burst premise")
    service = SERVICE if refresh else Fraction(2048)
    ends = [Fraction(52000) + i * service for i in range(1, count + 1)]
    # Channel service spacing exceeds a one-cycle port, so no port recurrence is needed.
    commits = [edge_after(10**9, edge_after(10**9, ceil(x), 4), 1) for x in ends]
    return ends, commits


def split(address: int, size: int) -> list[tuple[int, int, int]]:
    if address < 0 or size <= 0:
        raise ValueError("invalid transfer")
    end, result = address + size, []
    while address < end:
        payload = min(end - address, 256 - address % 256)
        result.append((address // 256 % 8, payload, 256))
        address += payload
    return result
