"""Non-quantitative prose cannot bypass numeric report permissions."""

import re

from uarch_contract.precision import PrecisionFormat

_CATEGORIES = tuple(x.value for x in PrecisionFormat) + (
    "C0",
    "C1",
    "C2",
    "L0",
    "L0m",
    "L1",
    "L2",
    "L3",
    "L4",
)
_PATTERN = re.compile(
    r"\b(?:" + "|".join(map(re.escape, _CATEGORIES)) + r")\b|[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
)


def safe_prose(value: str) -> str:
    """Preserve exact named categories; redact every other unbound numeric token."""
    return _PATTERN.sub(
        lambda match: match[0] if match[0] in _CATEGORIES else "[numeric text withheld]", value
    )
