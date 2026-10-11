"""Non-quantitative prose cannot bypass numeric report permissions."""

import re
from dataclasses import dataclass
from typing import Literal

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


@dataclass(frozen=True)
class CapturedIdentifier:
    """A field-aware categorical label supplied from a verified captured operator.

    Not a generic prose exemption: arbitrary plot strings still use safe_prose.
    Plot rendering escapes the exact category; it never interprets it as a quantity.
    """

    field: Literal["op_id"]
    value: str
