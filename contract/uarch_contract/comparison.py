"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from typing import Annotated, Literal, NoReturn

from pydantic import ConfigDict, Field, model_validator

from .assumptions import ModelIdentity
from .common import FrozenModel, JsonFloat
from .evidence import ArtifactPointer
from .exports import ExplicitPrecision
from .prepared import Query


class ProjectionScope(FrozenModel):
    global_kv_heads: Annotated[int, Field(strict=True, ge=1)]
    global_vocab: Annotated[int, Field(strict=True, ge=1)]
    kv_replicated: Annotated[bool, Field(strict=True)]
    padded_vocab: Annotated[int, Field(strict=True, ge=1)]


class ReferenceValue(FrozenModel):
    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"state": {"const": "positive"}}},
                    "then": {"properties": {"value": {"exclusiveMinimum": 0, "type": "number"}}},
                },
                {
                    "if": {"properties": {"state": {"const": "zero"}}},
                    "then": {"properties": {"value": {"const": 0}}},
                },
                {
                    "if": {"properties": {"state": {"const": "null"}}},
                    "then": {"properties": {"value": {"type": "null"}}},
                },
                {
                    "if": {"properties": {"state": {"const": "absent"}}},
                    "then": {"properties": {"value": {"type": "null"}}},
                },
            ]
        }
    )
    state: Literal["positive", "zero", "null", "absent"]
    value: Annotated[JsonFloat, Field(ge=0)] | None

    @model_validator(mode="after")
    def accepted_semantics(self) -> ReferenceValue:
        if (
            (self.state == "positive" and (self.value is None or self.value <= 0))
            or (self.state == "zero" and self.value != 0)
            or (self.state in ("null", "absent") and self.value is not None)
        ):
            raise ValueError("ComparisonPolicyViolation: reference state/value")
        return self


class ProducedValue(FrozenModel):
    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "else": {"properties": {"value": {"type": "null"}}},
                    "if": {"properties": {"state": {"const": "known"}}},
                    "then": {
                        "properties": {
                            "source_hash": {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"},
                            "source_pointer": {"minLength": 1, "type": "string"},
                            "value": {"minimum": 0, "type": "number"},
                        }
                    },
                }
            ]
        }
    )
    conversion: Literal["identity", "ps_to_seconds"]
    source_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    source_pointer: Annotated[str, Field(min_length=1, pattern="\\S")] | None
    state: Literal["known", "unmodelled", "not_produced"]
    value: Annotated[JsonFloat, Field(ge=0)] | None

    @model_validator(mode="after")
    def accepted_semantics(self) -> ProducedValue:
        if (self.state == "known") != (self.value is not None):
            raise ValueError("ComparisonPolicyViolation: produced state/value")
        if self.state == "known" and (self.source_hash is None or self.source_pointer is None):
            raise ValueError("ComparisonPolicyViolation: known value requires source")
        return self


class ComparisonDeviation(FrozenModel):
    deviation_rel: Annotated[JsonFloat, Field(ge=-0.05, le=0.05)]
    id: Annotated[str, Field(min_length=1, pattern="\\S")]
    reason: Annotated[str, Field(min_length=1, pattern="\\S")]


class ComparisonChannel(FrozenModel):
    absolute_adjustment_rel: Annotated[JsonFloat, Field(ge=0)]
    actual: ProducedValue
    channel: Literal[
        "matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes", "duration_s"
    ]
    declared_deviations: Annotated[tuple[ComparisonDeviation, ...], Field(min_length=0)]
    outcome: Literal[
        "passed", "failed", "unassessed", "refused", "execution_failed", "modelled_absence"
    ]
    raw_rel: JsonFloat | None
    reason: Annotated[str, Field(min_length=1, pattern="\\S")]
    reference: ReferenceValue
    residual_rel: JsonFloat | None
    signed_adjustment_rel: JsonFloat
    unit: Literal["op", "byte", "s"]


class ComparisonFixture(FrozenModel):
    bundle_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    candidate_input_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    candidate_output_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    channels: Annotated[tuple[ComparisonChannel, ...], Field(min_length=5)]
    component_binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    execution: Literal["executed", "pre_call_refusal", "execution_failed", "not_run"]
    fixture_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    job_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    outcome: Literal["passed", "failed", "unassessed", "refused", "execution_failed"]
    precision: ExplicitPrecision
    projection_scope: ProjectionScope
    query: Query
    result_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    tp: Annotated[int, Field(strict=True, ge=1)]


class ExpectedPrecisionRefusal(FrozenModel):
    boundary: Annotated[str, Field(min_length=1)]
    check_input_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    component_binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    error_class: Annotated[str, Field(min_length=1)]
    precision: ExplicitPrecision
    refusal_id: Annotated[str, Field(min_length=1)]
    source_entry_index: Annotated[int, Field(strict=True, ge=0)]


class PrecisionCheckInput(FrozenModel):
    callable_source_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    classification: Literal["synthetic_input", "captured_input", "reconstructed_input"]
    component_binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    component_role: Annotated[str, Field(min_length=1)]
    format: Literal["uarch-precision-check-input/1"]
    input_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    limitation: Annotated[str, Field(min_length=1)]
    precision: ExplicitPrecision
    requested_boundary: Annotated[str, Field(min_length=1)]
    upstream_sha: Annotated[str, Field(pattern="^[0-9a-f]{40}$")]


class PrecisionCheckTrace(FrozenModel):
    capture_source: ArtifactPointer | None
    check_input_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    classification: Literal["synthetic_observation", "captured_probe"]
    error_class: Annotated[str, Field(min_length=1)] | None
    execution: Literal["refused", "succeeded", "execution_failed"]
    format: Literal["uarch-precision-check-trace/1"]
    message: Annotated[str, Field(min_length=1)]
    observed_boundary: Annotated[str, Field(min_length=1)] | None
    trace_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]


class PrecisionRefusalObservation(FrozenModel):
    check_input_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None
    error_class: Annotated[str, Field(min_length=1)] | None
    evidence_outcome: Literal["passed", "refused", "execution_failed", "unassessed"]
    execution: Literal["refused", "succeeded", "execution_failed", "not_run"]
    format: Literal["uarch-precision-refusal-observation/1"]
    match_result: Literal[
        "matched",
        "wrong_boundary",
        "wrong_error_class",
        "unexpected_success",
        "unexpected_refusal",
        "execution_failed",
        "not_run",
    ]
    observation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    observed_boundary: Annotated[str, Field(min_length=1)] | None
    reason: Annotated[str, Field(min_length=1)]
    refusal_id: Annotated[str, Field(min_length=1)] | None
    trace_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")] | None


class ReferenceInventoryFixturesItemValues(FrozenModel):
    duration_s: ReferenceValue
    matrix_ops: ReferenceValue
    memory_read_bytes: ReferenceValue
    memory_write_bytes: ReferenceValue
    vector_ops: ReferenceValue


class ReferenceInventoryFixturesItem(FrozenModel):
    component_binding_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    fixture_id: Annotated[str, Field(min_length=1, pattern="\\S")]
    precision: ExplicitPrecision
    projection_scope: ProjectionScope
    query: Query
    tp: Annotated[int, Field(strict=True, ge=1)]
    values: ReferenceInventoryFixturesItemValues


class ReferenceInventory(FrozenModel):
    classification: Literal["adopted_oracle", "synthetic_reference"]
    fixtures: Annotated[tuple[ReferenceInventoryFixturesItem, ...], Field(min_length=1)]
    format: Literal["uarch-reference-inventory/1"]
    inventory_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    oracle_manifest_sha256: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    reference_model: ModelIdentity
    refusal_inventory_source: ArtifactPointer
    refusals: tuple[ExpectedPrecisionRefusal, ...]


class ComparisonArtifact(FrozenModel):
    candidate: ModelIdentity
    classification: Literal["executed_comparison", "synthetic_presentation"]
    comparison_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    evidence_outcome: Literal[
        "complete_pass", "failed", "unassessed", "refused", "execution_failed"
    ]
    fixtures: Annotated[tuple[ComparisonFixture, ...], Field(min_length=1)]
    format: Literal["uarch-comparison/1"]
    gate_outcome: Literal[
        "not_assessed", "compatibility_pass", "compatibility_fail", "discrepancy_record_complete"
    ]
    limitations: Annotated[
        tuple[Annotated[str, Field(min_length=1, pattern="\\S")], ...], Field(min_length=1)
    ]
    precision_refusal_observations: tuple[PrecisionRefusalObservation, ...]
    reference_basis: Literal[
        "physical_vs_nominal_rank_projection", "nominal_aggregate_divided_by_tp"
    ]
    reference_inventory_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    reference_model: ModelIdentity
    track: Literal["physical_discrepancy", "nominal_compatibility"]


# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    ProjectionScope,
    ReferenceValue,
    ProducedValue,
    ComparisonDeviation,
    ComparisonChannel,
    ComparisonFixture,
    ExpectedPrecisionRefusal,
    PrecisionCheckInput,
    PrecisionCheckTrace,
    PrecisionRefusalObservation,
    ReferenceInventory,
    ComparisonArtifact,
)

for _model in (
    ProjectionScope,
    ReferenceValue,
    ProducedValue,
    ComparisonDeviation,
    ComparisonChannel,
    ComparisonFixture,
    ExpectedPrecisionRefusal,
    PrecisionCheckInput,
    PrecisionCheckTrace,
    PrecisionRefusalObservation,
    ReferenceInventoryFixturesItemValues,
    ReferenceInventoryFixturesItem,
    ReferenceInventory,
    ComparisonArtifact,
):
    _model.model_rebuild()


def _refuse(code: str, path: str) -> NoReturn:
    from .errors import ERROR_TYPES

    raise ERROR_TYPES[code](f"{code}: {path}")


def reduce_outcomes(outcomes: tuple[str, ...], *, artifact: bool = False) -> str:
    """Evidence severity only; a satisfied refusal is never a numeric pass."""
    rank = {
        "passed": 0,
        "unassessed": 1,
        "modelled_absence": 1,
        "refused": 2,
        "failed": 3,
        "execution_failed": 4,
    }
    normalized = tuple("unassessed" if x == "modelled_absence" else x for x in outcomes)
    value = max(normalized, key=rank.__getitem__, default="passed")
    return "complete_pass" if artifact and value == "passed" else value


def validate_channel(
    value: object, *, execution: str = "executed", declared_omission: bool = False
) -> tuple[str, bool]:
    """Check supplied arithmetic/outcome; return evidence and nominal obligation.

    Omission authority is supplied by the bound nominal output, never inferred from null.
    This function does not authenticate a ProducedValue source; validate_comparison does.
    """
    import math

    c = ComparisonChannel.model_validate(value)
    r, a = c.reference, c.actual
    if (
        (r.state == "positive" and (r.value is None or r.value <= 0))
        or (r.state == "zero" and r.value != 0)
        or (r.state in ("null", "absent") and r.value is not None)
        or ((a.state == "known") != (a.value is not None))
        or (a.state == "known" and (a.source_hash is None or a.source_pointer is None))
    ):
        _refuse("ComparisonPolicyViolation", "reference/actual state")
    unit = "s" if c.channel == "duration_s" else "op" if c.channel.endswith("ops") else "byte"
    if c.unit != unit:
        _refuse("ComparisonPolicyViolation", "unit")
    ds = c.declared_deviations
    signed = math.fsum(x.deviation_rel for x in ds)
    absolute = math.fsum(abs(x.deviation_rel) for x in ds)
    if (
        len({x.id for x in ds}) != len(ds)
        or absolute > 0.05
        or c.signed_adjustment_rel != signed
        or c.absolute_adjustment_rel != absolute
    ):
        _refuse("ComparisonPolicyViolation", "declared_deviations")
    raw = residual = None
    if execution != "executed":
        outcome = {
            "execution_failed": "execution_failed",
            "not_run": "unassessed",
            "pre_call_refusal": "refused",
        }[execution]
        obligation = False
        if execution in ("not_run", "pre_call_refusal") and a.state != "not_produced":
            _refuse("ComparisonOutcomeMismatch", "unexecuted actual")
    elif r.value is not None and a.value is not None:
        if r.value == 0:
            outcome = "passed" if a.value == 0 else "failed"
        else:
            raw = (a.value - r.value) / r.value
            residual = raw - signed
            limit = 0.001 if c.channel == "duration_s" else 0.005
            outcome = "passed" if abs(residual) <= limit else "failed"
        obligation = outcome == "passed"
    elif r.value is None and a.value is None and declared_omission:
        outcome, obligation = "modelled_absence", True
    else:
        outcome = "unassessed"
        obligation = r.value is None and a.value is not None
    if ds and (raw is None or c.channel == "duration_s" or abs(raw) <= 0.005):
        _refuse("ComparisonPolicyViolation", "adjustment without eligible count denominator")
    if c.raw_rel != raw or c.residual_rel != residual:
        _refuse("ComparisonPolicyViolation", "raw_rel/residual_rel")
    if c.outcome != outcome:
        _refuse("ComparisonOutcomeMismatch", f"{c.channel}/outcome: expected {outcome}")
    return outcome, obligation


def validate_precision_observations(
    inventory: ReferenceInventory,
    observations: tuple[PrecisionRefusalObservation, ...],
    artifacts: object,
) -> tuple[bool, bool]:
    """Authenticate the complete refusal join in the accepted R1 primary-error order.

    Returns (all nominal obligations satisfied, every required attempt recorded).
    No callable execution, source fetching or inferred expectation takes place here.
    """
    from .hashing import resolve_artifact, resolve_pointer, verify_identity

    expected = inventory.refusals
    ids = [x.refusal_id for x in expected]
    indices = [x.source_entry_index for x in expected]
    if len(set(ids)) != len(ids) or len(set(indices)) != len(indices):
        _refuse("DuplicateExpectedRefusal", "refusals")
    pointer = inventory.refusal_inventory_source
    source = resolve_pointer(
        resolve_artifact(pointer.artifact_hash, artifacts), pointer.json_pointer
    )
    if not isinstance(source, list) or set(indices) != set(range(len(source))):
        _refuse("RefusalInventoryMismatch", "refusal_inventory_source")
    observed_ids = [x.refusal_id for x in observations if x.refusal_id is not None]
    extra_traces = [x.trace_hash for x in observations if x.refusal_id is None]
    if len(set(observed_ids)) != len(observed_ids) or len(set(extra_traces)) != len(extra_traces):
        _refuse("DuplicateRefusalObservation", "precision_refusal_observations")
    if set(observed_ids) - set(ids):
        _refuse("UnknownExpectedRefusal", "refusal_id")
    if set(ids) - set(observed_ids):
        _refuse("RefusalObservationMissing", "refusal_id")
    by_id = {x.refusal_id: x for x in expected}
    # Check every expectation even if the matching observed check never ran.
    for expectation in expected:
        check = PrecisionCheckInput.model_validate(
            resolve_artifact(expectation.check_input_hash, artifacts)
        )
        row = source[expectation.source_entry_index]
        if (
            check.component_binding_hash != expectation.component_binding_hash
            or check.precision != expectation.precision
            or check.requested_boundary != expectation.boundary
            or row.get("component") != check.component_role
            or row.get("compute") != expectation.precision.compute
            or row.get("kv_cache") != expectation.precision.kv_cache
            or row.get("boundary") != expectation.boundary
            or row.get("error") != expectation.error_class
        ):
            _refuse("RefusalSourceMismatch", expectation.refusal_id)
        binding = resolve_artifact(check.component_binding_hash, artifacts)
        if binding.get("upstream_sha") != check.upstream_sha:
            _refuse("RefusalSourceMismatch", expectation.refusal_id + "/upstream_sha")
    passed = recorded = True
    for o in observations:
        verify_identity(o, "observation_hash")
        e: ExpectedPrecisionRefusal | None = by_id.get(o.refusal_id) if o.refusal_id else None
        if e and o.check_input_hash not in (e.check_input_hash, None):
            _refuse("RefusalSourceMismatch", "check_input_hash")
        if o.execution == "not_run":
            if any(x is not None for x in (o.trace_hash, o.observed_boundary, o.error_class)):
                _refuse("RefusalSourceMismatch", "not_run trace")
            match, evidence = "not_run", "unassessed"
            recorded = False
        else:
            if o.check_input_hash is None or o.trace_hash is None:
                _refuse("RefusalSourceMismatch", "missing input/trace")
            check = PrecisionCheckInput.model_validate(
                resolve_artifact(o.check_input_hash, artifacts)
            )
            trace = PrecisionCheckTrace.model_validate(resolve_artifact(o.trace_hash, artifacts))
            if (
                trace.check_input_hash != o.check_input_hash
                or trace.execution != o.execution
                or trace.observed_boundary != o.observed_boundary
                or trace.error_class != o.error_class
            ):
                _refuse("RefusalSourceMismatch", "trace facts")
            if trace.capture_source is not None:
                resolve_pointer(
                    resolve_artifact(trace.capture_source.artifact_hash, artifacts),
                    trace.capture_source.json_pointer,
                )
            if o.execution == "succeeded":
                if o.error_class is not None or o.observed_boundary is None:
                    _refuse("RefusalSourceMismatch", "succeeded trace")
                match, evidence = "unexpected_success", "passed"
            elif o.execution == "execution_failed":
                if o.error_class is None:
                    _refuse("RefusalSourceMismatch", "execution_failed error_class")
                match, evidence = "execution_failed", "execution_failed"
            else:
                if o.error_class is None or o.observed_boundary is None:
                    _refuse("RefusalSourceMismatch", "refused trace")
                match = (
                    "unexpected_refusal"
                    if e is None
                    else "wrong_boundary"
                    if o.observed_boundary != e.boundary
                    else "wrong_error_class"
                    if o.error_class != e.error_class
                    else "matched"
                )
                evidence = "refused"
        if e is None and (o.execution != "refused" or match != "unexpected_refusal"):
            _refuse("RefusalSourceMismatch", "null refusal_id")
        if (o.match_result, o.evidence_outcome) != (match, evidence):
            _refuse("ComparisonOutcomeMismatch", "observation match/evidence")
        passed &= match == "matched"
    return passed, recorded


def _validate_actual_source(
    channel: ComparisonChannel, fixture: ComparisonFixture, track: str, artifacts: object
) -> None:
    """Bind a known ProducedValue to its output contract, not merely an equal number."""
    from .hashing import resolve_artifact, resolve_pointer

    actual = channel.actual
    if actual.state != "known":
        return
    physical = track == "physical_discrepancy"
    expected_source = fixture.result_hash if physical else fixture.candidate_output_hash
    if fixture.execution == "executed" and actual.source_hash != expected_source:
        _refuse("RefusalSourceMismatch", "actual candidate output source")
    if channel.channel == "duration_s":
        pointer, conversion = (
            ("/duration_ps", "ps_to_seconds") if physical else ("/duration_s", "identity")
        )
    else:
        pointer, conversion = "/counts/" + channel.channel, "identity"
    if (actual.source_pointer, actual.conversion) != (pointer, conversion):
        _refuse("RefusalSourceMismatch", channel.channel + "/source_pointer/conversion")
    assert actual.source_hash is not None
    original = resolve_pointer(resolve_artifact(actual.source_hash, artifacts), pointer)
    if conversion == "ps_to_seconds":
        original /= 1e12
    if isinstance(original, bool) or original != actual.value:
        _refuse("RefusalSourceMismatch", "actual source value")


def validate_comparison(value: object, inventory: object, artifacts: object) -> ComparisonArtifact:
    """Verify an already captured comparison; never construct or execute a candidate.

    The caller supplies all companions by content hash. This verifies record consistency,
    not the truth of claimed external execution or the provenance eligibility of evidence.
    """
    from .hashing import resolve_artifact, verify_identity

    c = ComparisonArtifact.model_validate(value)
    inv = ReferenceInventory.model_validate(inventory)
    verify_identity(c, "comparison_hash")
    verify_identity(inv, "inventory_hash")
    for o in c.precision_refusal_observations:
        verify_identity(o, "observation_hash")
    if c.reference_inventory_hash != inv.inventory_hash or c.reference_model != inv.reference_model:
        _refuse("RefusalSourceMismatch", "reference_inventory_hash/reference_model")
    obligations, recorded = validate_precision_observations(
        inv, c.precision_refusal_observations, artifacts
    )
    references = {f.fixture_id: f for f in inv.fixtures}
    if (
        len(references) != len(inv.fixtures)
        or len({f.fixture_id for f in c.fixtures}) != len(c.fixtures)
        or {f.fixture_id for f in c.fixtures} != references.keys()
    ):
        _refuse("IncompleteComparisonInventory", "fixtures")
    if c.reference_basis != (
        "physical_vs_nominal_rank_projection"
        if c.track == "physical_discrepancy"
        else "nominal_aggregate_divided_by_tp"
    ):
        _refuse("ComparisonPolicyViolation", "reference_basis")
    for f in c.fixtures:
        r = references[f.fixture_id]
        for field in ("component_binding_hash", "precision", "projection_scope", "query", "tp"):
            if getattr(f, field) != getattr(r, field):
                _refuse("IncompleteComparisonInventory", f.fixture_id + "/" + field)
        if len(f.channels) != 5 or {x.channel for x in f.channels} != set(
            type(r.values).model_fields
        ):
            _refuse("IncompleteComparisonInventory", f.fixture_id + "/channels")
        nominal_output = None
        if c.track == "nominal_compatibility":
            if any(x is not None for x in (f.bundle_hash, f.job_hash, f.result_hash)):
                _refuse("ComparisonPolicyViolation", "nominal physical identities")
            if f.execution == "executed":
                if f.candidate_input_hash is None or f.candidate_output_hash is None:
                    _refuse("IncompleteComparisonInventory", "nominal input/output")
                candidate_input = resolve_artifact(f.candidate_input_hash, artifacts)
                nominal_output = resolve_artifact(f.candidate_output_hash, artifacts)
                if (
                    candidate_input.get("format") != "uarch-nominal-input/1"
                    or nominal_output.get("format") != "uarch-nominal-output/1"
                    or candidate_input.get("query") != f.query.model_dump(mode="json")
                    or candidate_input.get("precision") != f.precision.model_dump(mode="json")
                    or candidate_input.get("tp") != f.tp
                    or candidate_input.get("component_binding_hash") != f.component_binding_hash
                    or nominal_output.get("model_identity") != c.candidate.model_dump(mode="json")
                ):
                    _refuse("RefusalSourceMismatch", "nominal query/precision/component/model")
                if nominal_output.get("input_hash") != f.candidate_input_hash:
                    _refuse("RefusalSourceMismatch", "nominal output input_hash")
                if candidate_input.get("model_identity") != c.candidate.model_dump(mode="json"):
                    _refuse("RefusalSourceMismatch", "nominal model")
        else:
            if f.candidate_input_hash is not None or f.candidate_output_hash is not None:
                _refuse("ComparisonPolicyViolation", "physical nominal identities")
            if f.execution == "executed":
                if any(x is None for x in (f.bundle_hash, f.job_hash, f.result_hash)):
                    _refuse("IncompleteComparisonInventory", "physical input/output")
                assert (
                    f.result_hash is not None
                    and f.job_hash is not None
                    and f.bundle_hash is not None
                )
                result = resolve_artifact(f.result_hash, artifacts)
                job = resolve_artifact(f.job_hash, artifacts)
                resolve_artifact(f.bundle_hash, artifacts)
                if result.get("job_hash") != f.job_hash or job.get("bundle_hash") != f.bundle_hash:
                    _refuse("RefusalSourceMismatch", "physical job/result")
                if (
                    job["point"]["query"] != f.query.model_dump(mode="json")
                    or job["rank"]["tp"] != f.tp
                    or job["precision"] != f.precision.model_dump(mode="json")
                    or job["engine"] != result["engine"]
                ):
                    _refuse("RefusalSourceMismatch", "physical query/precision/rank/engine")
                if result["engine"]["model"] != c.candidate.model_dump(mode="json"):
                    _refuse("RefusalSourceMismatch", "physical model")
        evidence = []
        fixture_ok = True
        for channel in f.channels:
            if channel.reference != getattr(r.values, channel.channel):
                _refuse("RefusalSourceMismatch", "reference channel")
            actual = channel.actual
            _validate_actual_source(channel, f, c.track, artifacts)
            omission = bool(
                nominal_output
                and nominal_output.get("omissions")
                and actual.state == "unmodelled"
                and (
                    channel.channel == "vector_ops"
                    or channel.channel == "memory_write_bytes"
                    and f.query.phase == "decode"
                )
            )
            outcome, ok = validate_channel(
                channel, execution=f.execution, declared_omission=omission
            )
            evidence.append(outcome)
            fixture_ok &= ok
        if f.execution == "pre_call_refusal":
            scope = f.projection_scope
            fixture_ok = scope.kv_replicated or scope.padded_vocab != scope.global_vocab
            if (
                f.result_hash is not None
                or f.job_hash is not None
                or f.candidate_output_hash is not None
            ):
                _refuse("ComparisonPolicyViolation", "pre_call_refusal fabricated result")
        if f.execution == "not_run":
            recorded = False
        if f.outcome != reduce_outcomes(tuple(evidence)):
            _refuse("ComparisonOutcomeMismatch", f.fixture_id + "/outcome")
        obligations &= fixture_ok
    evidence_outcome = reduce_outcomes(
        tuple(f.outcome for f in c.fixtures)
        + tuple(o.evidence_outcome for o in c.precision_refusal_observations),
        artifact=True,
    )
    gate = (
        ("compatibility_pass" if obligations else "compatibility_fail")
        if c.track == "nominal_compatibility"
        else ("discrepancy_record_complete" if recorded else "not_assessed")
    )
    if (c.evidence_outcome, c.gate_outcome) != (evidence_outcome, gate):
        _refuse("ComparisonOutcomeMismatch", "artifact evidence/gate")
    return c
