"""Evidence eligibility over A's shared records; no file loader or ambient ledger."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from uarch_contract.evidence import (
    EvidenceRecord,
    EvidenceScopeCase,
    OrderingRecord,
    ReviewRecord,
    SourceRecord,
    VerificationRecord,
)
from uarch_contract.hashing import (
    resolve_artifact,
    verify_declared_artifact_closure,
    verify_identity,
    verify_review,
)
from uarch_contract.registry import FamilyRegistry
from uarch_contract.report_context import ReportContext


@dataclass(frozen=True)
class EvidenceAssessment:
    """Ephemeral evaluator result, not a serialized evidence or loader contract."""

    badge: str
    model_identity_hash: str
    purpose: str
    granularity: str
    evidence_ids: tuple[str, ...] = ()
    error_band: tuple[float, float] | None = None
    synthetic: bool = False
    reasons: tuple[str, ...] = ()
    dimensions: tuple[str, ...] = ()
    scopes: tuple[EvidenceScopeCase, ...] = ()


def match_scope(
    evidence: EvidenceScopeCase, target: EvidenceScopeCase, dimensions: Sequence[str]
) -> dict[str, str]:
    result = {}
    aliases = {
        "model_identity": "model_identity_hash",
        "precision_roles": "precision",
        "kv_layout": "kv_block_size_tokens",
    }
    for dimension in dimensions:
        field = aliases.get(dimension, dimension)
        if field not in EvidenceScopeCase.model_fields:
            raise ValueError(f"UnsupportedEvidenceDimension: {dimension}")
        left, right = getattr(evidence, field), getattr(target, field)
        if field == "precision" and (left.kv_cache is None or right.kv_cache is None):
            result[dimension] = "UNKNOWN"
            continue
        result[dimension] = (
            "UNKNOWN" if left is None or right is None else "MATCH" if left == right else "MISMATCH"
        )
    return result


def _accepted_review(value: Any, artifacts: Mapping[str, Any]) -> bool:
    verify_review(value, artifacts)
    data = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    r = ReviewRecord.model_validate(resolve_artifact(data["review_hash"], artifacts))
    return r.independent and r.decision == "accepted"


def assess_evidence(
    context: ReportContext,
    scopes: tuple[EvidenceScopeCase, ...],
    *,
    purpose: str,
    channel: str | None,
    granularity: str,
    dimensions: Sequence[str],
    artifacts: Mapping[str, Any],
    allow_synthetic: bool = False,
) -> EvidenceAssessment:
    """Check every requested case, without widening a union or substituting source models.

    B2 accepts synthetic prerequisites only in explicit evaluator test mode. Real L3/L4
    needs a reviewed measurement/order proof interpreter beyond the delivered A1 carriers.
    Such records stay stub here; authenticated assertion bytes alone never promote them.
    This is an in-memory evidence seam, NOT A2's complete runtime artifact loader.
    """
    if len({scope.model_identity_hash for scope in scopes}) != 1:
        raise ValueError("EvidenceScope: require nonempty cases for exactly one source model")
    if len(scopes) > 1:
        parts = tuple(
            assess_evidence(
                context,
                (scope,),
                purpose=purpose,
                channel=channel,
                granularity=granularity,
                dimensions=dimensions,
                artifacts=artifacts,
                allow_synthetic=allow_synthetic,
            )
            for scope in scopes
        )
        rank = {"stub": 0, "estimated": 1, "measured": 2}
        return EvidenceAssessment(
            min((p.badge for p in parts), key=rank.__getitem__),
            scopes[0].model_identity_hash,
            purpose,
            granularity,
            tuple(sorted({e for p in parts for e in p.evidence_ids})),
            None,
            any(p.synthetic for p in parts),
            tuple(sorted({r for p in parts for r in p.reasons})),
            tuple(dimensions),
            scopes,
        )
    verify_identity(context, "context_hash")
    models = {s.model_identity_hash for s in scopes}
    if len(models) != 1:
        raise ValueError("EvidenceScope: require nonempty cases for exactly one source model")
    model = next(iter(models))
    registry = FamilyRegistry.model_validate(
        resolve_artifact(context.family_registry_hash, artifacts)
    )
    registry_ok = _accepted_review(registry, artifacts)
    families = {e.hardware_spec_hash: e.family for e in registry.entries}
    mandatory = {
        "family",
        "model_identity_hash",
        "precision",
        "mapping_match",
        "initial_state",
        "kv_block_size_tokens",
        "frequency_ratio",
    }
    if granularity == "whole_iteration":
        mandatory.add("prepared_bundle_hash")
    if granularity == "operator":
        mandatory.add("op_class")
    if any(scope.mapping_match == "matched" for scope in scopes):
        mandatory.add("mapping_correspondence_hash")
    dims = tuple(sorted(set(dimensions) | mandatory))
    eligible: list[EvidenceRecord] = []
    reasons: set[str] = set()
    for evidence_id, identity in sorted(context.evidence_index.items()):
        e = EvidenceRecord.model_validate(resolve_artifact(identity, artifacts))
        if e.evidence_id != evidence_id:
            raise ValueError("EvidenceIdentityMismatch: evidence_index")
        verify_declared_artifact_closure(identity, artifacts)
        review_ok = _accepted_review(e, artifacts)
        source = SourceRecord.model_validate(resolve_artifact(e.source_hash, artifacts))
        if not review_ok or not registry_ok or not source.independence_from_candidate:
            reasons.add("independent accepted review/source required")
            continue
        if purpose == "energy":
            reasons.add(
                "energy unverified: complete used-family verification not implemented at B2"
            )
            continue
        if e.purpose != purpose or e.granularity != granularity:
            continue
        if e.channel is not None and e.channel != channel:
            continue
        if e.rung not in ("L3", "L4"):
            reasons.add("L0–L2 is verification, not accuracy")
            continue
        synthetic = e.classification == "synthetic_fixture"
        if synthetic:
            if not allow_synthetic or source.kind != "synthetic_fixture":
                reasons.add("synthetic evidence requires explicit evaluator test mode")
                continue
        else:
            # No private raw-measurement schema, guessed Git-proof fields or boolean-only proof.
            reasons.add("real measurement/order protocol verification not delivered at B2")
            continue
        if e.ordering_hash is None:
            reasons.add("prediction ordering unavailable")
            continue
        ordering = OrderingRecord.model_validate(resolve_artifact(e.ordering_hash, artifacts))
        ordering_source = SourceRecord.model_validate(
            resolve_artifact(ordering.verification_source_hash, artifacts)
        )
        if (
            not ordering.prediction_is_ancestor
            or ordering.prediction_commit == ordering.result_commit
            or not ordering_source.independence_from_candidate
            or ordering_source.kind != "synthetic_fixture"
        ):
            reasons.add("invalid synthetic ordering prerequisite")
            continue
        if not e.verification_hashes:
            reasons.add("relevant passed verification unavailable")
            continue
        verifications = []
        for identity in e.verification_hashes:
            v = VerificationRecord.model_validate(resolve_artifact(identity, artifacts))
            accepted = _accepted_review(v, artifacts)
            vs = SourceRecord.model_validate(resolve_artifact(v.source_hash, artifacts))
            if (
                identity in context.verification_hashes
                and accepted
                and v.outcome == "passed"
                and v.purpose == purpose
                and v.model_identity_hash == model
                and vs.independence_from_candidate
            ):
                verifications.append(v)
        covered = True
        for target in scopes:
            if families.get(target.hardware_spec_hash or "") != target.family:
                covered = False
                reasons.add("family is unknown or mismatched")
                continue
            # Hash presence is checked; A2 must supply actual workload/source capture checks.
            if target.prepared_bundle_hash is not None:
                resolve_artifact(target.prepared_bundle_hash, artifacts)
            if target.mapping_match == "matched":
                if target.mapping_correspondence_hash is None:
                    covered = False
                    continue
                resolve_artifact(target.mapping_correspondence_hash, artifacts)
            matching = [
                s
                for s in e.scope
                if all(x == "MATCH" for x in match_scope(s, target, dims).values())
            ]
            if not matching:
                for offered in e.scope:
                    reasons.update(
                        f"{dimension}: {status}"
                        for dimension, status in match_scope(offered, target, dims).items()
                        if status != "MATCH"
                    )
            if not matching or not any(
                all(x == "MATCH" for x in match_scope(s, target, dims).values())
                for v in verifications
                for s in v.scope
            ):
                covered = False
        if covered:
            eligible.append(e)
        else:
            reasons.add("required scope or verification scope uncovered")
    bands = {(e.error_band.low_rel, e.error_band.high_rel) for e in eligible if e.error_band}
    if any(low > high for low, high in bands) or len(bands) > 1:
        raise ValueError("AmbiguousEvidenceBand: no reviewed unique band selection")
    badge = (
        "measured" if any(e.rung == "L4" for e in eligible) else "estimated" if eligible else "stub"
    )
    return EvidenceAssessment(
        badge,
        model,
        purpose,
        granularity,
        tuple(e.evidence_id for e in eligible),
        next(iter(bands)) if bands else None,
        bool(eligible) and all(e.classification == "synthetic_fixture" for e in eligible),
        tuple(sorted(reasons)),
        dims,
        scopes,
    )


def intensity_regime(ratio: float | None) -> str | None:
    if ratio is None:
        return None
    if not math.isfinite(ratio) or ratio < 0:
        raise ValueError("invalid intensity ratio")
    return "low" if ratio < 0.5 else "middle" if ratio <= 2 else "high"


def load_regime(load: float | None) -> str | None:
    if load is None:
        return None
    if not math.isfinite(load) or not 0 <= load <= 1:
        raise ValueError("invalid load ratio")
    return "low" if load < 0.30 else "middle" if load <= 0.70 else "high"


def array_fill(m: int | None, n: int | None, rows: int, cols: int) -> str | None:
    """The accepted U1 GEMM bin; non-GEMM/unknown dimensions stay unknown."""
    if m is None or n is None:
        return None
    if any(type(x) is not int or x <= 0 for x in (m, n, rows, cols)):
        raise ValueError("invalid array dimensions")
    return "underfilled" if m < rows or n < cols else "full"
