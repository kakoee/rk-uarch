"""Canonical UTF-8 JSON: sorted keys, repr-round-trip floats, no NaN or infinity.

Hash the validated model for normalized defaults. A table digest excludes only its
own top-level table_hash; it includes hardware_spec_hash, request_hash and every nested card hash.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from .common import CONTRACT_VERSION as CONTRACT_VERSION


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")

    def normalized(item: Any) -> Any:
        if isinstance(item, float) and item == 0:
            return 0.0
        if isinstance(item, dict):
            return {key: normalized(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalized(child) for child in item]
        return item

    return json.dumps(
        normalized(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return "sha256:" + hashlib.sha256(data).hexdigest()


def spec_hash(value: Any) -> str:
    from .hardware import HardwareSpec

    return sha256(canonical_json(HardwareSpec.model_validate(value)))


def request_hash(value: Any) -> str:
    from .request import CharacterizationRequest

    return sha256(canonical_json(CharacterizationRequest.model_validate(value)))


def table_hash(value: Any) -> str:
    from .table import UarchCostTable

    data = UarchCostTable.model_validate(value).model_dump(mode="json")
    del data["table_hash"]
    return sha256(canonical_json(data))
