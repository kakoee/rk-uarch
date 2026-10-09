"""Accepted bounded raw /2 protocol. Pure parsing; never measurement authentication."""

from __future__ import annotations

import base64
import binascii
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from importlib.resources import files
from types import MappingProxyType
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.evidence import EvidenceScopeCase
from uarch_contract.hashing import canonical_json, sha256, strict_json_loads


class ProofRefusal(ValueError):
    """Malformed or contradictory supported proof; no eligibility."""


class ProofUnsupported(ProofRefusal):
    """Well-defined missing input/profile/representation; never a zero or pass."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProofRefusal(reason)


def schema(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(
        files("rkuarch.provenance").joinpath("proof_schemas", name).read_text()
    )
    return value


ORIGINAL = schema("original.json")
SCHEMAS = {
    name: schema(name + ".schema.json")
    for name in ("raw-envelope", "capture-links", "suite-records", "compiler-counts", "fidelity")
}


def shape(value: Any, spec: dict[str, Any]) -> None:
    """Strict interpreter for the exact reviewed schema vocabulary, not a wire type."""
    allowed = {
        "$schema",
        "$id",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "minLength",
        "pattern",
        "minimum",
        "const",
        "enum",
        "anyOf",
    }
    require(set(spec) <= allowed, "MALFORMED_SCHEMA_VOCABULARY")
    if "anyOf" in spec:
        for alt in spec["anyOf"]:
            try:
                shape(value, alt)
                return
            except ProofRefusal:
                pass
        raise ProofRefusal("MALFORMED_MEMBER_SHAPE: anyOf")
    if "const" in spec:
        require(value == spec["const"], "MALFORMED_MEMBER_VERSION")
    if "enum" in spec:
        require(value in spec["enum"], "MALFORMED_MEMBER_ENUM")
    kind = spec.get("type")
    if kind == "object":
        require(isinstance(value, dict), "MALFORMED_OBJECT")
        require(
            set(spec["required"]) <= set(value) <= set(spec["properties"]), "MALFORMED_OBJECT_KEYS"
        )
        for key, item in value.items():
            shape(item, spec["properties"][key])
    elif kind == "array":
        require(
            isinstance(value, list) and len(value) >= spec.get("minItems", 0), "MALFORMED_ARRAY"
        )
        for item in value:
            shape(item, spec["items"])
    elif kind == "string":
        require(
            isinstance(value, str) and len(value) >= spec.get("minLength", 0), "MALFORMED_STRING"
        )
        if "pattern" in spec:
            require(re.search(spec["pattern"], value) is not None, "MALFORMED_STRING_PATTERN")
    elif kind == "integer":
        require(type(value) is int and value >= spec.get("minimum", value), "MALFORMED_INTEGER")
    elif kind == "boolean":
        require(type(value) is bool, "MALFORMED_BOOLEAN")
    elif kind == "null":
        require(value is None, "MALFORMED_NULL")


def json_bytes(raw: bytes) -> Any:
    try:
        value = strict_json_loads(raw)
    except RecursionError as e:
        raise ProofUnsupported("UNSUPPORTED_NESTING") from e
    except (ValueError, UnicodeError) as e:
        raise ProofRefusal("MALFORMED_JSON") from e
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 32:
            raise ProofUnsupported("UNSUPPORTED_NESTING")
        if isinstance(item, (dict, list)):
            stack.extend(
                (v, depth + 1) for v in (item.values() if isinstance(item, dict) else item)
            )
    try:
        require(canonical_json(value).encode() == raw, "MALFORMED_NONCANONICAL_JSON")
    except (ValueError, TypeError) as e:
        raise ProofRefusal("MALFORMED_NONCANONICAL_JSON") from e
    return value


SUPPORT = {
    "suite-plan.json",
    "capture-inventory.json",
    "independent-expected.json",
    "compiler-counts.json",
    "original-expected.txt",
    "original-compiler.txt",
}
REQUIRED = {
    "measurement": {
        "model.json",
        "scope.json",
        "suite.json",
        "prediction.json",
        "observation.json",
        "environment.json",
        "fidelity.json",
        "device.csv",
        "capture-links.json",
    },
    "verification": {
        "model.json",
        "scope.json",
        "verification.json",
        "checks.json",
        "capture-links.json",
    },
    "capture_support": set(),
}
MEMBER_SCHEMAS = {
    **{
        n + ".json": ORIGINAL[n]
        for n in ("suite", "prediction", "observation", "environment", "verification", "checks")
    },
    "capture-links.json": SCHEMAS["capture-links"],
    "fidelity.json": SCHEMAS["fidelity"],
    "suite-plan.json": SCHEMAS["suite-records"]["anyOf"][0],
    "capture-inventory.json": SCHEMAS["suite-records"]["anyOf"][1],
    "independent-expected.json": SCHEMAS["suite-records"]["anyOf"][2],
    "compiler-counts.json": SCHEMAS["compiler-counts"],
}


@dataclass(frozen=True)
class DecodedProof:
    kind: str
    classification: str
    members: Mapping[str, bytes]

    def json(self, name: str) -> Any:
        if name not in self.members:
            raise ProofUnsupported("UNSUPPORTED_MEMBER_ABSENT: " + name)
        return json_bytes(self.members[name])


def decode_proof(raw: bytes) -> DecodedProof:
    if len(raw) > 16 * 1024 * 1024:
        raise ProofUnsupported("UNSUPPORTED_ENVELOPE_SIZE")
    value = json_bytes(raw)
    require(isinstance(value, dict), "MALFORMED_ENVELOPE")
    require(isinstance(value.get("format"), str), "MALFORMED_RAW_FORMAT")
    if value.get("format") != "u2-proof-bundle/2":
        raise ProofUnsupported("UNSUPPORTED_RAW_VERSION")
    require(isinstance(value.get("kind"), str), "MALFORMED_RAW_KIND")
    if value.get("kind") not in REQUIRED:
        raise ProofUnsupported("UNSUPPORTED_RAW_KIND")
    members = value.get("members")
    if isinstance(members, list) and len(members) > 128:
        raise ProofUnsupported("UNSUPPORTED_MEMBER_COUNT")
    shape(value, SCHEMAS["raw-envelope"])
    names = [m["name"] for m in members]
    require(names == sorted(set(names)), "MALFORMED_MEMBER_ORDER_OR_DUPLICATE")
    required = REQUIRED[value["kind"]]
    require(required <= set(names) <= required | SUPPORT, "MALFORMED_MEMBER_SET")
    decoded: dict[str, bytes] = {}
    total = 0
    for member in members:
        encoded = member["base64"]
        if len(encoded) > 4 * ((8 * 1024 * 1024 + 2) // 3):
            raise ProofUnsupported("UNSUPPORTED_DECODED_SIZE")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as e:
            raise ProofRefusal("MALFORMED_BASE64") from e
        total += len(data)
        if total > 8 * 1024 * 1024:
            raise ProofUnsupported("UNSUPPORTED_DECODED_SIZE")
        require(base64.b64encode(data).decode() == encoded, "MALFORMED_BASE64")
        require(sha256(data) == member["sha256"], "MALFORMED_MEMBER_HASH")
        name = member["name"]
        if name.endswith(".json"):
            obj = json_bytes(data)
            try:
                if name == "model.json":
                    ModelIdentity.model_validate(obj)
                elif name == "scope.json":
                    EvidenceScopeCase.model_validate(obj)
                else:
                    member_spec = MEMBER_SCHEMAS[name]
                    known = member_spec.get("properties", {}).get("format", {}).get("const")
                    if (
                        isinstance(obj, dict)
                        and isinstance(obj.get("format"), str)
                        and known
                        and obj["format"] != known
                    ):
                        raise ProofUnsupported("UNSUPPORTED_MEMBER_VERSION")
                    if name == "compiler-counts.json" and isinstance(obj, dict):
                        if (
                            isinstance(obj.get("basis"), str)
                            and obj["basis"] not in member_spec["properties"]["basis"]["enum"]
                        ):
                            raise ProofUnsupported("UNSUPPORTED_COUNT_BASIS")
                    shape(obj, member_spec)
            except ProofUnsupported:
                raise
            except ValueError as e:
                raise ProofRefusal("MALFORMED_MEMBER: " + name) from e
        decoded[name] = data
    return DecodedProof(value["kind"], value["classification"], MappingProxyType(decoded))


def exact_scalar(value: Any, unit: str) -> Fraction:
    if value is None:
        raise ProofUnsupported("UNKNOWN_CAPTURE_VALUE")
    require(
        type(value) in (float, int) and math.isfinite(value) and value >= 0,
        "MALFORMED_CAPTURE_NUMBER",
    )
    if unit not in ("ps", "s", "count", "byte"):
        raise ProofUnsupported("UNSUPPORTED_UNIT")
    number = Fraction.from_float(float(value))
    return number / 10**12 if unit == "ps" else number


def decimal_text(value: Fraction) -> str:
    d, a, b = value.denominator, 0, 0
    while d % 2 == 0:
        d //= 2
        a += 1
    while d % 5 == 0:
        d //= 5
        b += 1
    if d != 1:
        raise ProofUnsupported("UNSUPPORTED_NONTERMINATING_ERROR")
    places = max(a, b)
    scaled = abs(value.numerator) * 2 ** (places - a) * 5 ** (places - b)
    digits = str(scaled).rjust(places + 1, "0")
    if places:
        digits = (digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")
    return ("-" if value < 0 else "") + digits


def decimal_value(text: str) -> Fraction:
    require(
        isinstance(text, str)
        and re.fullmatch(r"-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?", text) is not None
        and text != "-0",
        "MALFORMED_DECIMAL",
    )
    try:
        return Fraction(text)
    except ValueError as e:
        raise ProofUnsupported("UNSUPPORTED_NUMERIC_SIZE") from e


def error_band(
    predictions: list[str], measured: list[str], band: Any
) -> tuple[float, float] | None:
    require(bool(predictions) and len(predictions) == len(measured), "MALFORMED_SAMPLES")
    errors = []
    for p, m in zip(predictions, measured, strict=True):
        pn, mn = decimal_value(p), decimal_value(m)
        require(pn >= 0 and mn > 0, "MISMATCH_TIMING")
        error = (pn - mn) / mn
        decimal_text(error)  # Representation support is required even for null bands.
        errors.append(abs(error))
    if band is None:
        return None
    require(set(band) == {"policy", "low_rel", "high_rel"}, "MALFORMED_BAND")
    if band["policy"] != "max-absolute-relative-error/1":
        raise ProofUnsupported("UNSUPPORTED_BAND_POLICY")
    high = max(errors)
    require(
        decimal_value(band["low_rel"]) == 0 and decimal_value(band["high_rel"]) == high,
        "MISMATCH_BAND",
    )
    if high == 0:
        return None
    return (0.0, outward_high(high))


def outward_high(high: Fraction) -> float:
    require(high > 0, "MALFORMED_BAND_HIGH")
    try:
        rounded = float(high)
    except OverflowError as e:
        raise ProofUnsupported("UNSUPPORTED_BAND_OVERFLOW") from e
    if math.isfinite(rounded) and Fraction(rounded) < high:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded):
        raise ProofUnsupported("UNSUPPORTED_BAND_OVERFLOW")
    return rounded


def check_shared_band(expected: tuple[float, float] | None, offered: Any) -> None:
    """Compare existing shared band's binary64 bytes, including required positive zero."""
    import struct

    from uarch_contract.evidence import EvidenceRecordErrorBand0

    if expected is None or offered is None:
        require(expected is None and offered is None, "MISMATCH_SHARED_BAND")
        return
    band = EvidenceRecordErrorBand0.model_validate(offered)
    require(
        struct.pack(">dd", *expected) == struct.pack(">dd", band.low_rel, band.high_rel),
        "MISMATCH_SHARED_BAND",
    )
