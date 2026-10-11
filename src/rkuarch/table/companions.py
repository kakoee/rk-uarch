"""Authenticate saved analytic captures and draft declarations for external review.

No execution, review issuance, family assignment or evidence eligibility lives here.
See companions.md for the explicit external-review stop and public command sequence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.hashing import (
    artifact_identity,
    content_hash,
    resolve_artifact,
    review_subject_hash,
    sha256,
    strict_json_loads,
    verify_identity,
)
from uarch_contract.model_card import ModelCard, Verification
from uarch_contract.prepared import PreparedBundle
from uarch_contract.report_context import MetricDependencies
from uarch_contract.request import CharacterizationRequest

from rkuarch.engines.analytic.core import engine_identity
from rkuarch.engines.protocol import (
    EngineJob,
    EngineResult,
    validate_engine_job,
    validate_engine_result,
)
from rkuarch.hw.derive import derive_rk_params, resolve_hardware
from rkuarch.workload.identity import legacy_model_id
from rkuarch.workload.prepared import ALGORITHMS, validate_execution_bundle

from .build import CapturedWork, captured_artifacts, table_recipes

# An unresolved pointer in the existing carrier, never a ReviewRecord or accepted authority.
UNREVIEWED = "sha256:" + "0" * 64


def read_artifact_directory(directory: Path, *, raw_blobs: bool = False) -> dict[str, Any]:
    """Read every exact hash-named member, including unused artifacts; no remote fallback.

    Assembly permits original raw source blobs under their byte hashes. Capture admits
    JSON objects only. Extra directories and alias names refuse instead of being ignored.
    """
    store: dict[str, Any] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}\.json", path.name):
            raise ValueError(f"CaptureArtifactName: {path}")
        identity = "sha256:" + path.stem
        data = path.read_bytes()
        try:
            if raw_blobs and sha256(data) == identity:
                store[identity] = data
            else:
                value = strict_json_loads(data)
                resolve_artifact(identity, {identity: value})
                store[identity] = value
        except (ValueError, TypeError) as exc:
            raise ValueError(f"CaptureArtifactInvalid: {path}: {exc}") from exc
    return store


def _validate_captured(c: CapturedWork) -> None:
    b = validate_execution_bundle(c.bundle)
    verify_identity(c.assumptions, "assumptions_hash")
    expected_engine = engine_identity()
    if (
        c.assumptions.assumptions_hash != b.intent.assumptions_hash
        or c.assumptions.model != expected_engine.model
        or c.assumptions.algorithms != ALGORITHMS
    ):
        raise ValueError("CaptureAssumptionMismatch: assumptions/model/algorithms")
    request = CharacterizationRequest(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    if c.request != request:
        raise ValueError("CaptureRequestMismatch: request/prepared")
    if c.derivation != derive_rk_params(b.hardware_spec):
        raise ValueError("CaptureDerivationMismatch: derivation/hardware")
    if len(c.jobs) != len(b.points) or len(c.results) != len(b.points):
        raise ValueError("CaptureCoverageMismatch: one job/result per prepared point")
    for point, job, result in zip(b.points, c.jobs, c.results, strict=True):
        validate_engine_job(job, b, request)
        if job.point != point or job.engine != expected_engine:
            raise ValueError("CaptureJobMismatch: point order/current engine identity")
        if job.hardware != resolve_hardware(
            b.hardware_spec, job.precision, frequency_ratio=point.frequency_ratio
        ):
            raise ValueError("CaptureHardwareMismatch: sourced hardware projection")
        validate_engine_result(result, job)


def load_captured_work(
    directory: Path, prepared: PreparedBundle, assumptions: AssumptionSet
) -> CapturedWork:
    """Authenticate the complete capture/ output; never regenerate absent or stale work.

    Membership is exactly bundle, assumptions, request, derivation and one job/result
    per point. Hash filenames do not supply ordering: the prepared point order does.
    Captured arithmetic/identity validation is not fresh engine execution or measurement.
    """
    b = validate_execution_bundle(prepared)
    request = CharacterizationRequest(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    derivation = derive_rk_params(b.hardware_spec)
    store = read_artifact_directory(Path(directory))
    jobs = [
        EngineJob.model_validate(v)
        for v in store.values()
        if "job_hash" in v and "result_hash" not in v
    ]
    results = [EngineResult.model_validate(v) for v in store.values() if "result_hash" in v]
    if len(jobs) != len(b.points) or len(results) != len(b.points):
        raise ValueError(f"CaptureCoverageMismatch: {directory}: job/result count")
    ordered_jobs, ordered_results = [], []
    for point in b.points:
        matches = [j for j in jobs if j.point_hash == point.payload_hash]
        if len(matches) != 1:
            raise ValueError(f"CaptureCoverageMismatch: {directory}: point {point.payload_hash}")
        job = matches[0]
        matches_r = [r for r in results if r.job_hash == job.job_hash]
        if len(matches_r) != 1:
            raise ValueError(f"CaptureCoverageMismatch: {directory}: job {job.job_hash}")
        ordered_jobs.append(job)
        ordered_results.append(matches_r[0])
    c = CapturedWork(
        b, assumptions, request, derivation, tuple(ordered_jobs), tuple(ordered_results)
    )
    try:
        _validate_captured(c)
        expected = captured_artifacts(c)
        if set(store) != set(expected):
            raise ValueError(
                f"CaptureMembershipMismatch: missing={sorted(set(expected) - set(store))}; "
                f"extra={sorted(set(store) - set(expected))}"
            )
        for identity, value in expected.items():
            if store[identity] != value:
                raise ValueError(f"CaptureArtifactMismatch: {identity}")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{directory}: {exc}") from exc
    return c


def draft_companions(captured: CapturedWork) -> tuple[ModelCard, MetricDependencies, str]:
    """Return a deterministic STUB card, UNREVIEWED declarations and exact review subject."""
    _validate_captured(captured)
    card = ModelCard(
        model_id=legacy_model_id(captured.jobs[0], captured.bundle),
        badge="stub",
        evidence=(),
        verification=Verification(),
        validated_error_band=None,
        energy_verification=None,
    )
    recipes, sources = table_recipes(captured)
    deps = MetricDependencies(
        format="uarch-metric-dependencies/1",
        version="intrinsic-table/1",
        dependencies_hash=UNREVIEWED,
        review_hash=UNREVIEWED,
        model_identity_hash=content_hash(captured.assumptions.model),
        recipes=recipes,
        source_recipes=sources,
    )
    deps = deps.model_copy(
        update={"dependencies_hash": content_hash(deps, exclude=("dependencies_hash",))}
    )
    return card, deps, review_subject_hash(deps)


def add_artifact(store: dict[str, Any], value: Any) -> str:
    """Index an explicit input without silently replacing an unequal existing artifact."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    identity = artifact_identity(value)
    resolve_artifact(identity, {identity: value})
    if identity in store and store[identity] != value:
        raise ValueError(f"ArtifactHashMismatch: unequal duplicate {identity}")
    store[identity] = value
    return identity


def write_outputs(outputs: dict[Path, bytes]) -> None:
    """Preflight the whole output set, preserving existing identical files and refusing aliases."""
    normalized = [p.resolve() for p in outputs]
    if len(normalized) != len(set(normalized)):
        raise ValueError("OutputConflict: aliased destinations")
    for path, data in outputs.items():
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError(f"OutputConflict: symlink {path}")
        if any(parent.exists() and not parent.is_dir() for parent in path.parents):
            raise ValueError(f"OutputConflict: non-directory parent {path}")
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise ValueError(f"OutputConflict: {path}")
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)
