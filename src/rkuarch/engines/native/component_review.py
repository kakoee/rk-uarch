"""Component-only review/2 data admission. Records are never execution authority.

Build provenance, independently supplied startup assurance and optional historical
read evidence remain separate. The installed selector/decision chain stays external.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field
from uarch_contract.common import FrozenModel, Hash
from uarch_contract.hashing import strict_json_loads

from .host import _read, _require
from .records import FileBinding


def _true(value: Any) -> Literal[True]:
    if value is not True:
        raise ValueError("exact true review verdict required")
    return True


Accepted = Annotated[Literal[True], BeforeValidator(_true)]
Evidence = Annotated[tuple[FileBinding, ...], Field(min_length=1)]


class RuntimeSubject(FrozenModel):
    runtime_payload_byte_hash: Hash


class StartupSubject(RuntimeSubject):
    consumer_hash: Hash


class ComponentRuntimeReview(FrozenModel):
    format: Literal["uarch-component-runtime-review/2"]
    subject: RuntimeSubject
    build_provenance: FileBinding
    startup_assurance: FileBinding
    selected_support_current: Accepted
    selected_support_evidence: Evidence
    optional_read_evidence: FileBinding | None


class ComponentStartupAssurance(FrozenModel):
    format: Literal["uarch-component-startup-assurance/1"]
    subject: StartupSubject
    verdict: Literal["accepted"]
    launcher: FileBinding
    manifest: FileBinding
    evidence: Evidence


class NegativeSubject(RuntimeSubject):
    negative_inventory_byte_hash: Hash


class ComponentNegativeReview(FrozenModel):
    format: Literal["uarch-component-negative-review/3"]
    subject: NegativeSubject
    runtime_review: FileBinding
    finite_refusals_current: Accepted
    finite_refusals_evidence: Evidence


@dataclass(frozen=True)
class CheckedRuntimeReview:
    required_files: tuple[FileBinding, ...]
    startup_manifest: FileBinding
    optional_read_evidence: FileBinding | None


def _consume_provenance(
    root: Path, record: dict[str, Any], expected: dict[str, Any]
) -> list[FileBinding]:
    from .component_build_review import consume_provenance

    return consume_provenance(root, record, expected)


def check_runtime_review(
    root: Path,
    value: Any,
    *,
    expected: dict[str, Any],
    launcher: FileBinding,
) -> CheckedRuntimeReview:
    """Validate bound review data; caller expectations come from the prepared payload.

    No startup execution or assurance generation. Public host separately checks
    actual trusted-start state, immutable placement and the genuine decision chain.
    """
    review = ComponentRuntimeReview.model_validate(value)
    _require(
        review.subject.runtime_payload_byte_hash == expected["runtime_payload_byte_hash"],
        "component runtime review subject",
    )
    files: dict[str, FileBinding] = {}

    def read(binding: FileBinding) -> bytes:
        previous = files.setdefault(binding.path, binding)
        _require(previous == binding, "conflicting review file binding")
        return _read(root, binding)

    provenance = strict_json_loads(read(review.build_provenance))
    for binding in _consume_provenance(root, provenance, expected):
        read(binding)
    startup = ComponentStartupAssurance.model_validate(
        strict_json_loads(read(review.startup_assurance))
    )
    _require(
        startup.subject.runtime_payload_byte_hash == expected["runtime_payload_byte_hash"]
        and startup.subject.consumer_hash == expected["consumer_hash"],
        "separate startup assurance subject/consumer join",
    )
    _require(startup.launcher == launcher, "startup assurance launcher join")
    for binding in (
        startup.launcher,
        startup.manifest,
        *startup.evidence,
        *review.selected_support_evidence,
    ):
        read(binding)
    if review.optional_read_evidence is not None:
        # Integrity only. Incomplete/absent optional reads grant nothing and do not
        # defeat otherwise qualifying provenance/startup review.
        read(review.optional_read_evidence)
    return CheckedRuntimeReview(
        tuple(files[path] for path in sorted(files)),
        startup.manifest,
        review.optional_read_evidence,
    )
