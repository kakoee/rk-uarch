"""Independent B R1 arithmetic/assembly tests; synthetic captures, no upstream execution."""

import json
from collections.abc import Callable
from copy import deepcopy
from typing import Any, Literal, cast

import pytest
from uarch_contract.comparison import (
    ProducedValue,
    ReferenceValue,
    validate_channel,
    validate_comparison,
)
from uarch_contract.hashing import content_hash

from contract.tests.u2_comparison import build_channel
from tests.fixtures.u2_b.b2_support import ROOT, ZERO, proposal_artifacts


def actual(value: float | None = None) -> ProducedValue:
    return ProducedValue(
        state="unmodelled" if value is None else "known",
        value=value,
        source_hash=ZERO if value is not None else None,
        source_pointer="/counts/matrix_ops" if value is not None else None,
        conversion="identity",
    )


@pytest.mark.parametrize(
    "channel,phase,state,expected",
    [
        ("vector_ops", "prefill", "absent", "modelled_absence"),
        ("memory_write_bytes", "decode", "null", "modelled_absence"),
        ("matrix_ops", "decode", "null", "unassessed"),
        ("memory_write_bytes", "prefill", "null", "unassessed"),
    ],
)
def test_R101_R106_only_declared_nominal_omissions(
    channel: str, phase: str, state: Literal["positive", "zero", "null", "absent"], expected: str
) -> None:
    c = build_channel(
        channel,
        ReferenceValue(state=state, value=None),
        actual(),
        track="nominal_compatibility",
        phase=phase,
        nominal_omissions=("declared",),
    )
    assert c.outcome == expected and c.raw_rel is None and c.residual_rel is None
    physical = build_channel(
        channel,
        ReferenceValue(state=state, value=None),
        actual(),
        track="physical_discrepancy",
        phase=phase,
    )
    assert physical.outcome == "unassessed"
    if channel == "matrix_ops":
        with pytest.raises(ValueError, match="ComparisonOutcomeMismatch"):
            validate_channel(dict(c.model_dump(), outcome="modelled_absence"))


@pytest.mark.parametrize(
    "ref,val,outcome",
    [(0, 0, "passed"), (0, 1, "failed"), (200, 201, "passed"), (200, 201.0001, "failed")],
)
def test_R113_R115_zeros_exact_and_count_limit(ref: float, val: float, outcome: str) -> None:
    c = build_channel(
        "matrix_ops",
        ReferenceValue(state="zero" if ref == 0 else "positive", value=ref),
        actual(val),
        track="physical_discrepancy",
        phase="decode",
    )
    assert c.outcome == outcome
    if ref == 0:
        assert c.raw_rel is None and c.residual_rel is None


def test_R114_absolute_spend_and_duration_adjustment_refuse() -> None:
    deviations = [
        dict(id="a", deviation_rel=0.03, reason="synthetic"),
        dict(id="b", deviation_rel=-0.03, reason="synthetic"),
    ]
    with pytest.raises(ValueError, match="ComparisonPolicyViolation"):
        build_channel(
            "matrix_ops",
            ReferenceValue(state="positive", value=100),
            actual(104),
            track="physical_discrepancy",
            phase="decode",
            deviations=deviations,
        )
    with pytest.raises(ValueError, match="ComparisonPolicyViolation"):
        build_channel(
            "duration_s",
            ReferenceValue(state="positive", value=100),
            actual(104),
            track="physical_discrepancy",
            phase="decode",
            deviations=deviations[:1],
        )


@pytest.mark.parametrize(
    "factor,expected", [(1.0, "passed"), (1.0009, "passed"), (1.0011, "failed")]
)
def test_duration_tolerance(factor: float, expected: str) -> None:
    assert (
        build_channel(
            "duration_s",
            ReferenceValue(state="positive", value=1),
            actual(factor),
            track="nominal_compatibility",
            phase="decode",
        ).outcome
        == expected
    )


def base() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    directory = ROOT / "docs/reviews/U2-U0003-proposal/fixtures"
    return (
        json.loads((directory / "comparison-physical.json").read_text()),
        json.loads((directory / "comparison-inventory.json").read_text()),
        cast(Callable[[], dict[str, Any]], proposal_artifacts)(),
    )


def test_R107_R108_attempt_completeness_is_not_accuracy() -> None:
    c, inv, store = base()
    assert validate_comparison(c, inv, store).gate_outcome == "discrepancy_record_complete"
    assert c["evidence_outcome"] == "failed"
    f = c["fixtures"][0]
    f["execution"] = "not_run"
    f["outcome"] = "unassessed"
    f["job_hash"] = f["result_hash"] = None
    for channel in f["channels"]:
        channel.update(
            outcome="unassessed",
            raw_rel=None,
            residual_rel=None,
            declared_deviations=[],
            signed_adjustment_rel=0.0,
            absolute_adjustment_rel=0.0,
        )
        channel["actual"].update(
            state="not_produced", value=None, source_hash=None, source_pointer=None
        )
    c["gate_outcome"] = "not_assessed"
    c["comparison_hash"] = content_hash(c, exclude=("comparison_hash",))
    assert validate_comparison(c, inv, store).gate_outcome == "not_assessed"


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("missing", "RefusalObservationMissing"),
        ("duplicate", "DuplicateRefusalObservation"),
        ("unknown", "UnknownExpectedRefusal"),
        ("source", "RefusalInventoryMismatch"),
    ],
)
def test_R111_invalid_precision_joins_refuse_before_reduction(
    mutation: str, error: str | None
) -> None:
    c, inv, store = base()
    if mutation == "missing":
        c["precision_refusal_observations"].pop()
    if mutation == "duplicate":
        c["precision_refusal_observations"].append(deepcopy(c["precision_refusal_observations"][0]))
    if mutation == "unknown":
        o = c["precision_refusal_observations"][0]
        o["refusal_id"] = "B-unknown"
        o["observation_hash"] = content_hash(o, exclude=("observation_hash",))
    if mutation == "source":
        inv["refusals"][0]["source_entry_index"] = 99
        inv["inventory_hash"] = content_hash(inv, exclude=("inventory_hash",))
        c["reference_inventory_hash"] = inv["inventory_hash"]
        store[inv["inventory_hash"]] = inv
    c["comparison_hash"] = content_hash(c, exclude=("comparison_hash",))
    with pytest.raises(ValueError, match=error):
        validate_comparison(c, inv, store)


@pytest.mark.parametrize(
    "boundary,error,execution,match,evidence",
    [
        ("wrong", "WrongError", "refused", "wrong_boundary", "refused"),
        ("same", "WrongError", "refused", "wrong_error_class", "refused"),
        ("same", "UnsupportedPrecision", "refused", "matched", "refused"),
        ("same", None, "succeeded", "unexpected_success", "passed"),
        (None, "RuntimeError", "execution_failed", "execution_failed", "execution_failed"),
    ],
)
def test_R109_R110_observation_classification_preserves_evidence(
    boundary: str | None, error: str | None, execution: str, match: str, evidence: str
) -> None:
    from uarch_contract.comparison import (
        ExpectedPrecisionRefusal,
        PrecisionCheckInput,
        PrecisionCheckTrace,
    )

    from contract.tests.u2_comparison import precision_observation

    c, inv, store = base()
    expected = ExpectedPrecisionRefusal.model_validate(inv["refusals"][0])
    check = PrecisionCheckInput.model_validate(store[expected.check_input_hash])
    raw = dict(
        format="uarch-precision-check-trace/1",
        check_input_hash=check.input_hash,
        classification="synthetic_observation",
        execution=execution,
        error_class=error,
        observed_boundary=expected.boundary if boundary == "same" else boundary,
        message="B synthetic observation, never executed",
        capture_source=None,
    )
    trace = PrecisionCheckTrace.model_validate(dict(raw, trace_hash=content_hash(raw)))
    result = precision_observation(expected, check, trace, reason="independent synthetic unit case")
    assert (result.match_result, result.evidence_outcome) == (match, evidence)
    if execution == "refused":
        extra = precision_observation(None, check, trace, reason="synthetic unexpected event")
        assert extra.refusal_id is None and extra.match_result == "unexpected_refusal"
    absent = precision_observation(expected, check, None, reason="explicit not run")
    assert absent.trace_hash is None and absent.evidence_outcome == "unassessed"


def test_B_record_assembly_uses_shared_reductions_and_preserves_discrepancy_failure() -> None:
    from uarch_contract.comparison import ComparisonArtifact

    from contract.tests.u2_comparison import assemble_comparison

    c, inv, store = base()
    supplied = ComparisonArtifact.model_validate(c)
    result = assemble_comparison(
        candidate=supplied.candidate,
        inventory=inv,
        fixtures=supplied.fixtures,
        observations=supplied.precision_refusal_observations,
        track=supplied.track,
        classification=supplied.classification,
        limitations=supplied.limitations,
        artifacts=store,
    )
    assert result.evidence_outcome == "failed"
    assert result.gate_outcome == "discrepancy_record_complete"
    assert result.comparison_hash == supplied.comparison_hash


@pytest.mark.parametrize(
    "channel,phase", [("matrix_ops", "decode"), ("memory_write_bytes", "prefill")]
)
def test_missing_required_outputs_against_known_reference_fail_obligation(
    channel: str, phase: str
) -> None:
    c = build_channel(
        channel,
        ReferenceValue(state="positive", value=100),
        actual(),
        track="nominal_compatibility",
        phase=phase,
        nominal_omissions=("declared",),
    )
    assert validate_channel(c) == ("unassessed", False)


def test_R112_unexpected_event_and_duplicate_auxiliary_trace() -> None:
    from uarch_contract.comparison import (
        ExpectedPrecisionRefusal,
        PrecisionCheckInput,
        PrecisionCheckTrace,
        PrecisionRefusalObservation,
        ReferenceInventory,
        validate_precision_observations,
    )

    from contract.tests.u2_comparison import precision_observation

    c, inv, store = base()
    expected = ExpectedPrecisionRefusal.model_validate(inv["refusals"][0])
    check = PrecisionCheckInput.model_validate(store[expected.check_input_hash])
    observations = tuple(
        PrecisionRefusalObservation.model_validate(o) for o in c["precision_refusal_observations"]
    )
    trace_hash = observations[0].trace_hash
    assert trace_hash is not None
    trace = PrecisionCheckTrace.model_validate(store[trace_hash])
    inventory = ReferenceInventory.model_validate(inv)
    assert validate_precision_observations(inventory, observations, store) == (True, True)
    extra = precision_observation(None, check, trace, reason="B synthetic additional refusal")
    assert validate_precision_observations(inventory, observations + (extra,), store) == (
        False,
        True,
    )
    with pytest.raises(ValueError, match="DuplicateRefusalObservation"):
        validate_precision_observations(inventory, observations + (extra, extra), store)


def test_R115_duration_exact_boundary_and_R114_unknown_adjustment() -> None:
    result = build_channel(
        "duration_s",
        ReferenceValue(state="positive", value=1000),
        actual(1001),
        track="physical_discrepancy",
        phase="decode",
    )
    assert result.raw_rel == 0.001 and result.outcome == "passed"
    with pytest.raises(ValueError, match="ComparisonPolicyViolation"):
        build_channel(
            "matrix_ops",
            ReferenceValue(state="absent", value=None),
            actual(),
            track="nominal_compatibility",
            phase="decode",
            deviations=[dict(id="a", reason="synthetic invalid adjustment", deviation_rel=0.01)],
        )
