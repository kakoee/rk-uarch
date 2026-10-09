"""The sole production row conversion from analytic picoseconds to seconds."""

import math


def ps_to_seconds(value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise ValueError("InvalidDuration: expected finite nonnegative picoseconds")
    return value / 1e12
