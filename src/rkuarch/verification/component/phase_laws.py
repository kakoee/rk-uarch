"""Independent scalar mechanism checks, not a scheduler or result generator.

Inputs are actual phase observations plus declared work/clock/resource parameters.
These routines never choose ready order, dispatch work, or compute a graph makespan.
"""

from fractions import Fraction
from typing import Any

from rkuarch.verification.component.arithmetic import ceil, edge_after
from rkuarch.verification.component.checks import need


def clocked(grant: int, aligned: int, end: int, hz: int, cycles: int) -> None:
    need(aligned == edge_after(hz, grant, 0), "phase receiving alignment")
    need(end == edge_after(hz, grant, cycles), "phase duration")


def channel(start: Fraction, end: Fraction, transaction: int, bandwidth: Fraction) -> None:
    need(start >= 0 and end - start == transaction * 10**12 / bandwidth, "channel mechanism")


def resident_phases(m: int, k: int, n: int) -> dict[str, int]:
    """Per-tile integer service cycles, without choosing or advancing a start time."""
    return dict(
        overhead=32,
        staging=ceil(Fraction(2 * m * k + 2 * k * n, 1024)),
        wave=510 + m,
        drain=ceil(Fraction(2 * m * n, 1024)),
    )


def tight_chain(activities: list[dict[str, Any]], selected: list[str], duration: int) -> None:
    """Check a selected causal witness, including zero duration links and stable ties.

    Adapter supplies canonical fields from the exact accepted carrier. A predecessor
    represents a causal constraint, never an extra occupied interval for its successor.
    """
    rows = {r["id"]: r for r in activities}
    need(len(rows) == len(activities), "phase identity")
    need(bool(selected) and len(set(selected)) == len(selected), "phase path inventory")
    previous = None
    cursor = 0
    for key in selected:
        need(key in rows, "phase path identity")
        row = rows[key]
        need(row["start"] == cursor <= row["end"], "phase path partition")
        preds = row["predecessors"]
        need(
            all(p in rows and rows[p]["end"] <= row["start"] for p in preds),
            "phase predecessor order",
        )
        tight = sorted(p for p in preds if rows[p]["end"] == row["start"])
        need(previous == (tight[0] if tight else None), "phase tight predecessor")
        cursor, previous = row["end"], key
    need(cursor == duration, "phase path makespan")
