"""B-owned record construction, outside A's isolated candidate and physical adapter.

No candidate imports/calls until A2 supplies its reviewed executable signatures.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from uarch_contract.assumptions import ModelIdentity
from uarch_contract.comparison import (
    ComparisonArtifact,
    ComparisonChannel,
    ComparisonFixture,
    ExpectedPrecisionRefusal,
    PrecisionCheckInput,
    PrecisionCheckTrace,
    PrecisionRefusalObservation,
    ProducedValue,
    ReferenceInventory,
    ReferenceValue,
    validate_channel,
)
from uarch_contract.hashing import content_hash, verify_identity


def build_channel(
    channel: str,
    reference: ReferenceValue,
    actual: ProducedValue,
    *,
    track: str,
    phase: str,
    execution: str = "executed",
    nominal_omissions: tuple[str, ...] = (),
    deviations: Sequence[Mapping[str, Any]] = (),
) -> ComparisonChannel:
    """Construct arithmetic from supplied observations, then use A's normative validator.

    Actual sources are authenticated only by final validate_comparison. A nonempty omission
    declaration cannot authorize matrix omission or transfer nominal omissions to physical.
    """
    if track not in ("physical_discrepancy", "nominal_compatibility") or phase not in (
        "decode",
        "prefill",
    ):
        raise ValueError("ComparisonPolicyViolation: track/phase")
    omission = (
        track == "nominal_compatibility"
        and bool(nominal_omissions)
        and actual.state == "unmodelled"
        and (channel == "vector_ops" or channel == "memory_write_bytes" and phase == "decode")
    )
    signed = math.fsum(d["deviation_rel"] for d in deviations)
    absolute = math.fsum(abs(d["deviation_rel"]) for d in deviations)
    raw = residual = None
    if execution != "executed":
        outcome = {
            "execution_failed": "execution_failed",
            "not_run": "unassessed",
            "pre_call_refusal": "refused",
        }[execution]
    elif reference.value is not None and actual.value is not None:
        if reference.value == 0:
            outcome = "passed" if actual.value == 0 else "failed"
        else:
            raw = (actual.value - reference.value) / reference.value
            residual = raw - signed
            outcome = (
                "passed"
                if abs(residual) <= (0.001 if channel == "duration_s" else 0.005)
                else "failed"
            )
    elif reference.value is None and actual.value is None and omission:
        outcome = "modelled_absence"
    else:
        outcome = "unassessed"
    result = ComparisonChannel.model_validate(
        dict(
            channel=channel,
            unit="s" if channel == "duration_s" else "op" if channel.endswith("ops") else "byte",
            reference=reference,
            actual=actual,
            declared_deviations=list(deviations),
            signed_adjustment_rel=signed,
            absolute_adjustment_rel=absolute,
            raw_rel=raw,
            residual_rel=residual,
            outcome=outcome,
            reason="Recorded comparison; absent/null reference is not numerical validation.",
        )
    )
    validate_channel(result, execution=execution, declared_omission=omission)
    return result


def precision_observation(
    expected: ExpectedPrecisionRefusal | None,
    check: PrecisionCheckInput | None,
    trace: PrecisionCheckTrace | None,
    *,
    reason: str,
) -> PrecisionRefusalObservation:
    """Translate an actual supplied trace (or explicit not-run), never execute or fabricate it."""
    if check is not None:
        verify_identity(check, "input_hash")
    if expected is not None and check is not None and expected.check_input_hash != check.input_hash:
        raise ValueError("RefusalSourceMismatch: expected input")
    if trace is None:
        if expected is None:
            raise ValueError("RefusalSourceMismatch: unexpected event requires a trace")
        execution, match, evidence, boundary, error = "not_run", "not_run", "unassessed", None, None
    else:
        verify_identity(trace, "trace_hash")
        if check is None or trace.check_input_hash != check.input_hash:
            raise ValueError("RefusalSourceMismatch: trace input")
        execution, boundary, error = trace.execution, trace.observed_boundary, trace.error_class
        if execution == "succeeded":
            match, evidence = "unexpected_success", "passed"
        elif execution == "execution_failed":
            match, evidence = "execution_failed", "execution_failed"
        else:
            match = (
                "unexpected_refusal"
                if expected is None
                else "wrong_boundary"
                if boundary != expected.boundary
                else "wrong_error_class"
                if error != expected.error_class
                else "matched"
            )
            evidence = "refused"
        if expected is None and execution != "refused":
            raise ValueError("RefusalSourceMismatch: unexpected event must be a refusal")
    data = dict(
        format="uarch-precision-refusal-observation/1",
        refusal_id=expected.refusal_id if expected else None,
        check_input_hash=check.input_hash if check else None,
        trace_hash=trace.trace_hash if trace else None,
        execution=execution,
        observed_boundary=boundary,
        error_class=error,
        match_result=match,
        evidence_outcome=evidence,
        reason=reason,
    )
    return PrecisionRefusalObservation.model_validate(
        dict(data, observation_hash=content_hash(data))
    )


def assemble_comparison(
    *,
    candidate: ModelIdentity,
    inventory: ReferenceInventory | Mapping[str, Any],
    fixtures: tuple[ComparisonFixture, ...],
    observations: tuple[PrecisionRefusalObservation, ...],
    track: str,
    classification: str,
    limitations: tuple[str, ...],
    artifacts: Mapping[str, Any],
) -> ComparisonArtifact:
    """Assemble shared ComparisonArtifact from supplied captures, with final A1 verification.

    No physical/nominal execution is inferred. A2 callers must capture genuine results first.
    """
    from uarch_contract.comparison import (
        reduce_outcomes,
        validate_comparison,
        validate_precision_observations,
    )
    from uarch_contract.hashing import resolve_artifact

    inv = ReferenceInventory.model_validate(inventory)
    passed, recorded = validate_precision_observations(inv, observations, artifacts)
    assembled = []
    for supplied in fixtures:
        f = ComparisonFixture.model_validate(supplied)
        output = (
            resolve_artifact(f.candidate_output_hash, artifacts)
            if f.candidate_output_hash is not None
            else None
        )
        outcomes = []
        fixture_ok = True
        for c in f.channels:
            omission = bool(
                track == "nominal_compatibility"
                and output
                and output.get("omissions")
                and c.actual.state == "unmodelled"
                and (
                    c.channel == "vector_ops"
                    or c.channel == "memory_write_bytes"
                    and f.query.phase == "decode"
                )
            )
            outcome, ok = validate_channel(c, execution=f.execution, declared_omission=omission)
            outcomes.append(outcome)
            fixture_ok &= ok
        if f.execution == "pre_call_refusal":
            fixture_ok = (
                f.projection_scope.kv_replicated
                or f.projection_scope.padded_vocab != f.projection_scope.global_vocab
            )
        if f.execution == "not_run":
            recorded = False
        passed &= fixture_ok
        assembled.append(dict(f.model_dump(mode="json"), outcome=reduce_outcomes(tuple(outcomes))))
    evidence = reduce_outcomes(
        tuple(f["outcome"] for f in assembled) + tuple(o.evidence_outcome for o in observations),
        artifact=True,
    )
    gate = (
        ("compatibility_pass" if passed else "compatibility_fail")
        if track == "nominal_compatibility"
        else "discrepancy_record_complete"
        if recorded
        else "not_assessed"
    )
    data = dict(
        format="uarch-comparison/1",
        candidate=candidate,
        reference_model=inv.reference_model,
        classification=classification,
        track=track,
        reference_inventory_hash=inv.inventory_hash,
        reference_basis="nominal_aggregate_divided_by_tp"
        if track == "nominal_compatibility"
        else "physical_vs_nominal_rank_projection",
        fixtures=assembled,
        precision_refusal_observations=observations,
        evidence_outcome=evidence,
        gate_outcome=gate,
        limitations=limitations,
        comparison_hash="sha256:" + "0" * 64,
    )
    parsed = ComparisonArtifact.model_validate(data)
    parsed = parsed.model_copy(
        update={"comparison_hash": content_hash(parsed, exclude=("comparison_hash",))}
    )
    return validate_comparison(parsed, inv, artifacts)
