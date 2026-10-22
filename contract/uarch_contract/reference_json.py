"""Existing canonical JSON bytes without copying the entire reference graph.

Only /5 uses this serializer. It changes storage cost, not identity or provenance.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel


def chunks(value: Any, *, exclude: tuple[str, ...] = ()) -> Iterator[str]:
    if isinstance(value, BaseModel):
        keys = sorted(k for k in type(value).model_fields if k not in exclude)
        yield "{"
        for index, key in enumerate(keys):
            if index:
                yield ","
            yield json.dumps(key, ensure_ascii=False)
            yield ":"
            yield from chunks(getattr(value, key))
        yield "}"
    elif isinstance(value, dict):
        yield "{"
        for index, key in enumerate(sorted(k for k in value if k not in exclude)):
            if index:
                yield ","
            yield json.dumps(key, ensure_ascii=False)
            yield ":"
            yield from chunks(value[key])
        yield "}"
    elif isinstance(value, (list, tuple)):
        yield "["
        for index, item in enumerate(value):
            if index:
                yield ","
            yield from chunks(item)
        yield "]"
    elif value is None:
        yield "null"
    elif isinstance(value, bool):
        yield "true" if value else "false"
    elif isinstance(value, int):
        yield str(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite canonical number")
        yield repr(0.0 if value == 0 else value)
    else:
        yield json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def blocks(value: Any, *, exclude: tuple[str, ...] = ()) -> Iterator[bytes]:
    pending = []
    size = 0
    for part in chunks(value, exclude=exclude):
        pending.append(part)
        size += len(part)
        if size >= 65536:
            yield "".join(pending).encode()
            pending.clear()
            size = 0
    if pending:
        yield "".join(pending).encode()


def canonical_json(value: Any) -> str:
    return b"".join(blocks(value)).decode()


def content_hash(value: Any, *, exclude: tuple[str, ...] = ()) -> str:
    digest = hashlib.sha256()
    for block in blocks(value, exclude=exclude):
        digest.update(block)
    return "sha256:" + digest.hexdigest()


def verify_identity(value: Any, field: str) -> str:
    from .errors import ArtifactHashMismatch

    actual = content_hash(value, exclude=(field,))
    got = getattr(value, field) if isinstance(value, BaseModel) else value.get(field)
    if got != actual:
        raise ArtifactHashMismatch(f"ArtifactHashMismatch: /{field}: expected {actual}")
    return actual
