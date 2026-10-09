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


def strict_json_loads(text: str | bytes) -> Any:
    """Parse JSON without duplicate keys or non-finite extension tokens."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"DuplicateJsonKey: {key}")
            result[key] = value
        return result

    def invalid(token: str) -> Any:
        raise ValueError(f"NonFiniteJsonNumber: {token}")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def content_hash(value: Any, *, exclude: tuple[str, ...] = ()) -> str:
    """Hash canonical content, excluding only explicitly named top-level fields."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if exclude:
        value = {key: item for key, item in value.items() if key not in exclude}
    return sha256(canonical_json(value))


def verify_identity(value: Any, field: str) -> str:
    from .errors import ArtifactHashMismatch

    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    actual = content_hash(data, exclude=(field,))
    if data.get(field) != actual:
        raise ArtifactHashMismatch(f"ArtifactHashMismatch: /{field}: expected {actual}")
    return actual


# Explicit envelope discriminators, never a search for hash-shaped field names.
SELF_FIELDS = {
    "uarch-assumptions/1": "assumptions_hash",
    "uarch-prepared/1": "bundle_hash",
    "uarch-derivation/1": "derivation_hash",
    "uarch-execution-model/1": "execution_model_hash",
    "uarch-component-truth/1": "export_hash",
    "uarch-export-binding/1": "binding_hash",
    "uarch-upstream-component/1": "binding_hash",
    "uarch-component-precision/1": "precision_hash",
    "uarch-reference-inventory/1": "inventory_hash",
    "uarch-comparison/1": "comparison_hash",
    "uarch-precision-check-input/1": "input_hash",
    "uarch-precision-check-trace/1": "trace_hash",
    "uarch-precision-refusal-observation/1": "observation_hash",
    "uarch-evidence/1": "evidence_hash",
    "uarch-reference-source/1": "source_hash",
    "uarch-evidence-review/1": "review_hash",
    "uarch-ordering/1": "ordering_hash",
    "uarch-verification/1": "verification_hash",
    "uarch-family-registry/1": "registry_hash",
    "uarch-metric-dependencies/1": "dependencies_hash",
    "uarch-report-context/2": "context_hash",
    "uarch-render/1": "render_hash",
    "uarch-nominal-input/1": "input_hash",
    "uarch-nominal-output/1": "output_hash",
}


def identity_field(value: dict[str, Any]) -> str | None:
    if value.get("protocol") == "uarch-engine/1":
        return "result_hash" if "result_hash" in value else "job_hash"
    if value.get("contract") == "uarch-contract/0.2" and "table_hash" in value:
        return "table_hash"
    return SELF_FIELDS.get(value.get("format", ""))


def artifact_identity(value: dict[str, Any]) -> str:
    field = identity_field(value)
    return content_hash(value, exclude=(field,) if field else ())


def _detach_json(value: Any) -> Any:
    """Own JSON containers without invoking caller-defined __deepcopy__ hooks.

    Preserve tuple/list distinction and scalar values; this is not canonicalization.
    Unsupported payload types still reach the existing identity/type checks.
    """

    def containers(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: containers(child) for key, child in item.items()}
        if isinstance(item, list):
            return [containers(child) for child in item]
        if isinstance(item, tuple):
            return tuple(containers(child) for child in item)
        return item

    # Match the public resolver: only a TOP-LEVEL model is serialized. A model
    # nested in an untyped dictionary must still fail the original identity check.
    return containers(value.model_dump(mode="json") if isinstance(value, BaseModel) else value)


class _ResolutionSession:
    """One synchronous private validation owns each detached, authenticated value.

    The caller mapping may be lazy (A's disk loader). Copy only a requested value,
    BEFORE authenticating it with the public identity algorithm. Internal validators
    read these owned values without mutating them or passing them to caller callbacks.
    Neither this session nor its mutable dictionaries escape a public validation.
    A later public call always creates a new session and reauthenticates current bytes.
    This is not a caller-supplied verified flag, global cache or runtime loader.
    """

    def __init__(self, artifacts: Any) -> None:
        self._artifacts = artifacts
        self._values: dict[str, Any] = {}

    def _read(self, identity: str) -> Any:
        from .errors import ArtifactHashMismatch, ArtifactMissing

        if identity not in self._values:
            if identity not in self._artifacts:
                raise ArtifactMissing(f"ArtifactMissing: {identity}")
            detached = _detach_json(self._artifacts[identity])
            if isinstance(detached, bytes):
                if sha256(detached) != identity:
                    raise ArtifactHashMismatch(f"ArtifactHashMismatch: raw blob {identity}")
            else:
                # Plain private mapping avoids recursion into this session. Admission
                # still performs artifact_identity AND the declared self-field check.
                detached = resolve_artifact(identity, {identity: detached})
            self._values[identity] = detached
        return self._values[identity]

    def _resolve(self, identity: str) -> dict[str, Any]:
        from .errors import ArtifactHashMismatch

        value = self._read(identity)
        if not isinstance(value, dict):
            raise ArtifactHashMismatch(f"ArtifactHashMismatch: {identity}")
        return value


def resolve_artifact(identity: str, artifacts: Any) -> dict[str, Any]:
    """Read a supplied offline mapping and verify content before any selector is followed."""
    from .errors import ArtifactHashMismatch, ArtifactMissing

    if isinstance(artifacts, _ResolutionSession):
        return artifacts._resolve(identity)
    if identity not in artifacts:
        raise ArtifactMissing(f"ArtifactMissing: {identity}")
    value = artifacts[identity]
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if not isinstance(value, dict) or artifact_identity(value) != identity:
        raise ArtifactHashMismatch(f"ArtifactHashMismatch: {identity}")
    field = identity_field(value)
    if field:
        verify_identity(value, field)
    return value


def resolve_pointer(value: Any, pointer: str) -> Any:
    """Strict RFC 6901 pointer; no wildcard, evaluation, implicit hashes or ambient lookup."""
    import re

    if pointer == "":
        return value
    if not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        raise ValueError(f"InvalidArtifactPointer: {pointer}")
    try:
        for part in pointer[1:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    raise KeyError(key)
                value = value[int(key)]
            else:
                value = value[key]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"InvalidArtifactPointer: {pointer}") from exc
    return value


def review_subject_hash(value: Any) -> str:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    field = identity_field(data)
    return content_hash(data, exclude=tuple(x for x in (field, "review_hash") if x))


def verify_review(value: Any, artifacts: Any) -> None:
    from .errors import ReviewSubjectMismatch
    from .evidence import ReviewRecord

    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    review = ReviewRecord.model_validate(resolve_artifact(data["review_hash"], artifacts))
    if review_subject_hash(data) not in review.reviewed_subject_hashes:
        raise ReviewSubjectMismatch("ReviewSubjectMismatch: reviewed_subject_hashes")


def intent_hash(value: Any) -> str:
    from .request import RequestIntent

    return content_hash(RequestIntent.model_validate(value))


def point_hash(value: Any) -> str:
    from .prepared import PreparedPoint

    return content_hash(PreparedPoint.model_validate(value), exclude=("payload_hash",))


def bundle_hash(value: Any) -> str:
    from .prepared import PreparedBundle

    return content_hash(PreparedBundle.model_validate(value), exclude=("bundle_hash",))


def execution_hash(request: str, job_hashes: tuple[str, ...], engine: Any, version: str) -> str:
    return content_hash(
        {
            "request_hash": request,
            "job_hashes": job_hashes,
            "engine": engine.model_dump(mode="json") if isinstance(engine, BaseModel) else engine,
            "uarch_version": version,
        }
    )


def legacy_request_hash(value: Any) -> str:
    from .request import LegacyCharacterizationRequest

    return content_hash(LegacyCharacterizationRequest.model_validate(value))


def legacy_table_hash(value: Any) -> str:
    from .table import LegacyUarchCostTable

    return content_hash(LegacyUarchCostTable.model_validate(value), exclude=("table_hash",))


SELF_FIELDS["uarch-component-truth/1"] = "export_hash"

SELF_FIELDS["uarch-export-binding/1"] = "binding_hash"

SELF_FIELDS["uarch-upstream-component/1"] = "binding_hash"

SELF_FIELDS["uarch-render/1"] = "render_hash"


def verify_declared_artifact_closure(identity: str, artifacts: Any) -> tuple[str, ...]:
    """Verify explicit companion identities, including raw blobs, without ambient lookup.

    This is identity closure only. Domain validators and B's eligibility checks remain
    required. Implementation/source fingerprints and review subject-body digests are not
    artifact lookup instructions. Embedded hardware/points are checked in place.
    """
    from .errors import ArtifactHashMismatch

    session = _ResolutionSession(artifacts)
    fields = {
        "uarch-component-truth/1": ("derivation_hash", "execution_model_hash"),
        "uarch-export-binding/1": (
            "primary_export_hash",
            "execution_model_hash",
            "derivation_hash",
        ),
        "uarch-upstream-component/1": ("execution_model_hash",),
        "uarch-comparison/1": ("reference_inventory_hash",),
        "uarch-evidence/1": ("source_hash", "review_hash", "ordering_hash"),
        "uarch-reference-source/1": ("raw_blob_sha256",),
        "uarch-ordering/1": ("verification_source_hash",),
        "uarch-verification/1": ("source_hash", "review_hash"),
        "uarch-family-registry/1": ("review_hash",),
        "uarch-metric-dependencies/1": ("review_hash",),
        "uarch-report-context/2": (
            "assumptions_hash",
            "family_registry_hash",
            "metric_dependencies_hash",
        ),
        "uarch-render/1": ("table_hash", "report_context_hash"),
        "uarch-precision-check-trace/1": ("check_input_hash",),
        "uarch-precision-check-input/1": ("component_binding_hash",),
        "uarch-precision-refusal-observation/1": ("check_input_hash", "trace_hash"),
    }
    visited: set[str] = set()

    def visit(key: str) -> None:
        if key in visited:
            return
        raw = session._read(key)
        if isinstance(raw, bytes):
            visited.add(key)
            return
        value = session._resolve(key)
        visited.add(key)
        children = [
            value[name]
            for name in fields.get(value.get("format", ""), ())
            if value.get(name) is not None
        ]
        for name in ("comparison_hashes", "verification_hashes", "evidence_hashes"):
            children.extend(value.get(name, ()))
        children.extend(value.get("evidence_index", {}).values())
        if value.get("format") == "uarch-prepared/1":
            for point in value["points"]:
                verify_identity(point, "payload_hash")
            if (
                content_hash(value["intent"]) != value["intent_hash"]
                or spec_hash(value["hardware_spec"]) != value["intent"]["hardware_spec_hash"]
            ):
                raise ArtifactHashMismatch("ArtifactHashMismatch: bundle embedded identity")
            children.append(value["intent"]["assumptions_hash"])
        if value.get("protocol") == "uarch-engine/1":
            if "result_hash" in value:
                children.append(value["job_hash"])
            else:
                verify_identity(value["point"], "payload_hash")
                children.extend((value["bundle_hash"], value["assumptions_hash"]))
        if value.get("contract") == "uarch-contract/0.2":
            if "table_hash" in value:
                children.extend(
                    v
                    for k, v in value["artifacts"].items()
                    if k != "hardware_spec_hash" and isinstance(v, str)
                )
                children.extend(value["artifacts"]["comparison_hashes"])
                children.extend(row["result_hash"] for row in value["rows"])
            else:
                children.extend((value["prepared_input_hash"], value["assumptions_hash"]))
        if value.get("format") == "uarch-comparison/1":
            for observation in value["precision_refusal_observations"]:
                verify_identity(observation, "observation_hash")
                children.extend(
                    observation[k]
                    for k in ("check_input_hash", "trace_hash")
                    if observation[k] is not None
                )
            for fixture in value["fixtures"]:
                children.extend(
                    fixture[k]
                    for k in (
                        "bundle_hash",
                        "job_hash",
                        "result_hash",
                        "candidate_input_hash",
                        "candidate_output_hash",
                        "component_binding_hash",
                    )
                    if fixture[k] is not None
                )
                children.extend(
                    c["actual"]["source_hash"]
                    for c in fixture["channels"]
                    if c["actual"]["source_hash"] is not None
                )
        if value.get("format") == "uarch-reference-inventory/1":
            children.append(value["refusal_inventory_source"]["artifact_hash"])
            children.extend(e["check_input_hash"] for e in value["refusals"])
        if value.get("format") == "uarch-component-precision/1":
            binding = value["binding"]
            verify_identity(binding, "binding_hash")
            children.append(binding["execution_model_hash"])
            if binding["kind"] == "uarch_projection":
                children.extend((binding["primary_export_hash"], binding["derivation_hash"]))
        if value.get("format") == "uarch-metric-dependencies/1":
            for recipe in [*value["recipes"], *(s["recipe"] for s in value["source_recipes"])]:
                for selector in recipe["selectors"]:
                    child = resolve_artifact(selector["artifact_hash"], session)
                    resolve_pointer(child, selector["json_pointer"])
                    children.append(selector["artifact_hash"])
        capture = value.get("capture_source")
        if capture is not None:
            resolve_pointer(
                resolve_artifact(capture["artifact_hash"], session), capture["json_pointer"]
            )
            children.append(capture["artifact_hash"])
        for child in children:
            visit(child)

    visit(identity)
    return tuple(sorted(visited))
