"""Content hashing for run inputs: sha256 over canonical JSON.

A run is citable only if the same configuration always produces the same id, so the
canonical form pins every degree of freedom JSON leaves open: key order, separator
whitespace, and non-ASCII escaping.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from rk.schema.versions import input_v1_hash_payload

__all__ = ["canonical_json", "content_hash"]


def canonical_json(model: BaseModel) -> bytes:
    """Serialize a model to the one byte-string that stands for its content.

    `mode="json"` so enums become their string values and nothing exotic survives;
    `sort_keys` so declaration order and dict insertion order cannot change the hash.
    """
    payload: Any = input_v1_hash_payload(model)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def content_hash(model: BaseModel) -> str:
    """`sha256:<hex>` over the canonical JSON. Prefixed so the algorithm is visible."""
    return "sha256:" + hashlib.sha256(canonical_json(model)).hexdigest()
