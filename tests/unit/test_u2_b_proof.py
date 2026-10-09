"""Accepted raw /2 semantics; actual A3 captures, explicitly synthetic proof scaffolding."""

import base64
import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.provenance.proof import (
    ProofRefusal,
    ProofUnsupported,
    bind_capture,
    decimal_text,
    decode_proof,
    error_band,
    exact_scalar,
    interpret_measurement,
    interpret_ordering,
)
from rkuarch.table.artifacts import load_verified_report_inputs

ROOT = Path(__file__).resolve().parents[2]


def envelope(members, kind="capture_support", classification="synthetic_fixture"):
    return canonical_json(
        dict(
            format="u2-proof-bundle/2",
            classification=classification,
            kind=kind,
            members=[
                dict(name=n, sha256=sha256(v), base64=base64.b64encode(v).decode())
                for n, v in sorted(members.items())
            ],
        )
    ).encode()


@pytest.fixture(scope="module")
def inputs():
    return load_verified_report_inputs(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json")


def capture_case(v, op=2, quantity="matrix_ops"):
    job, result = v.jobs[0], v.results[0]
    item = result.per_op[op]
    pointer = f"/per_op/{op}/counts/{quantity}"
    ref = dict(
        kind="engine_result",
        value=dict(artifact_hash=result.result_hash, json_pointer=pointer),
        model_identity_hash=content_hash(job.engine.model),
        input_hash=job.job_hash,
        bundle_hash=job.bundle_hash,
        point_hash=job.point_hash,
        group_id=item.group_id,
        operator_id=item.id,
        quantity=quantity,
        source_unit="count",
    )
    case = dict(
        case_id="q-count",
        benchmark_id="historical-q",
        model_identity_hash=ref["model_identity_hash"],
        input_hash=job.job_hash,
        kind="engine_result",
        metric_pointer=pointer,
        group_id=item.group_id,
        operator_id=item.id,
        quantity=quantity,
        source_unit="count",
        purpose="counts",
        granularity="operator",
        required_roles=["verification_observed"],
        independent_expected=None,
    )
    return ref, case


def test_actual_capture_literal_control(inputs):
    ref, case = capture_case(inputs)
    bound = bind_capture(inputs, ref, case)
    assert bound.value == Fraction(64)  # Independent literal for saved tiny Q projection.
    assert bound.model_identity_hash == ref["model_identity_hash"]
    assert bound.purpose == "counts" and bound.granularity == "operator"
    assert bound.scopes[0].mapping_match is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_identity_hash", "sha256:" + "a" * 64),
        ("input_hash", "sha256:" + "a" * 64),
        ("bundle_hash", "sha256:" + "a" * 64),
        ("point_hash", "sha256:" + "a" * 64),
        ("operator_id", "wrong-op"),
        ("group_id", "wrong-group"),
        ("source_unit", "s"),
        ("quantity", "vector_ops"),
    ],
)
def test_capture_identity_mismatch(inputs, field, value):
    ref, case = capture_case(inputs)
    ref[field] = value
    with pytest.raises(ProofRefusal):
        bind_capture(inputs, ref, case)


def test_wrong_op_with_equal_value_is_not_same_capture(inputs):
    ref, case = capture_case(inputs, op=0)  # zero matrix_ops in both operators
    ref["value"]["json_pointer"] = "/per_op/1/counts/matrix_ops"
    with pytest.raises(ProofRefusal):
        bind_capture(inputs, ref, case)


def test_wrong_result_and_missing_closure(inputs):
    ref, case = capture_case(inputs)
    ref["value"]["artifact_hash"] = "sha256:" + "f" * 64
    with pytest.raises(ProofUnsupported, match="CAPTURE"):
        bind_capture(inputs, ref, case)


def test_wrong_purpose(inputs):
    ref, case = capture_case(inputs)
    case["purpose"] = "duration"
    with pytest.raises(ProofRefusal):
        bind_capture(inputs, ref, case)


def test_raw_control():
    raw = envelope({"original-expected.txt": b"64"})
    assert decode_proof(raw).members["original-expected.txt"] == b"64"


@pytest.mark.parametrize(
    "mutation", ["duplicate-key", "hash", "base64", "member", "order", "noncanonical"]
)
def test_malformed_raw(mutation):
    raw = envelope({"original-expected.txt": b"64", "original-compiler.txt": b"8"})
    value = json.loads(raw)
    if mutation == "duplicate-key":
        raw = raw.replace(b'"kind":', b'"kind":"capture_support","kind":')
    elif mutation == "noncanonical":
        raw += b"\n"
    else:
        if mutation == "hash":
            value["members"][0]["sha256"] = "sha256:" + "a" * 64
        if mutation == "base64":
            value["members"][0]["base64"] = "NjQ=\n"
        if mutation == "member":
            value["members"][0]["name"] = "../escape.txt"
        if mutation == "order":
            value["members"].reverse()
        raw = canonical_json(value).encode()
    with pytest.raises(ProofRefusal):
        decode_proof(raw)


@pytest.mark.parametrize("version", ["u2-proof-bundle/1", "u2-proof-bundle/3"])
def test_unsupported_versions(version):
    raw = json.loads(envelope({"original-expected.txt": b"64"}))
    raw["format"] = version
    with pytest.raises(ProofUnsupported):
        decode_proof(canonical_json(raw).encode())


def test_bounds():
    with pytest.raises(ProofUnsupported):
        decode_proof(b" " * (16 * 1024 * 1024 + 1))
    with pytest.raises(ProofUnsupported):
        decode_proof(b"[" * 34 + b"0" + b"]" * 34)
    value = json.loads(envelope({"original-expected.txt": b"64"}))
    value["members"] *= 129
    with pytest.raises(ProofUnsupported):
        decode_proof(canonical_json(value).encode())


def test_exact_numbers_and_outward_bands():
    assert exact_scalar(8000.0, "ps") == Fraction(1, 125000000)
    assert exact_scalar(0.1, "ps") == Fraction(3602879701896397, 36028797018963968000000000000)
    assert exact_scalar(0.125, "s") == Fraction(1, 8)
    assert decimal_text(Fraction(-1, 5)) == "-0.2"
    assert error_band(["0.00000001"], ["0.0000000125"], None) is None
    assert error_band(["1"], ["1"], None) is None
    assert (
        error_band(
            ["0.7"],
            ["1"],
            {"policy": "max-absolute-relative-error/1", "low_rel": "0", "high_rel": "0.3"},
        )[1].hex()
        == "0x1.3333333333334p-2"
    )
    with pytest.raises(ProofUnsupported, match="NONTERMINATING"):
        error_band(["0.000000008"], ["0.000000012"], None)
    with pytest.raises(ProofRefusal):
        error_band(
            ["0.7"],
            ["1"],
            {"policy": "max-absolute-relative-error/1", "low_rel": "0", "high_rel": "0.2"},
        )


def test_real_history_and_aggregate_never_promote():
    with pytest.raises(ProofUnsupported, match="PROJECT_HISTORY"):
        interpret_ordering(b"any")
    # Collector refusal happens only after valid /2 member decoding; full fixture added below.
    assert callable(interpret_measurement)


def test_verification_literal_positive_and_real_mode_unsupported(inputs):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    v, identity = verification_fixture(inputs)
    result = interpret_verification(v, identity, allow_synthetic=True)
    assert result.outcome == "passed" and result.synthetic
    assert result.cases == (("q-count", "passed"),)
    with pytest.raises(ProofUnsupported, match="PARSER"):
        interpret_verification(v, identity)


@pytest.mark.parametrize("outcome,expected", [("failed", "63"), ("not_run", "64")])
def test_verification_failed_not_run_preserved(inputs, outcome, expected):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    v, identity = verification_fixture(inputs, outcome=outcome, expected=expected)
    assert interpret_verification(v, identity, allow_synthetic=True).outcome == outcome


@pytest.mark.parametrize(
    "mutation", ["scalar", "unit", "case-omission", "wrong-op", "source", "purpose"]
)
def test_verification_rehashed_attacks(inputs, mutation):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    def change(d):
        if mutation == "scalar":
            d["checks"]["cases"][0]["observed"] = "65"
        if mutation == "unit":
            d["checks"]["cases"][0]["unit"] = "byte"
        if mutation == "case-omission":
            c = copy.deepcopy(d["plan"]["cases"][0])
            c["case_id"] = "required-second"
            d["plan"]["cases"].append(c)
        if mutation == "wrong-op":
            d["inventory"]["cases"][0]["capture"]["operator_id"] = "other"
        if mutation == "source":
            d["links"]["entries"][0]["independent_reference"]["source_record_hash"] = (
                "sha256:" + "f" * 64
            )
        if mutation == "purpose":
            d["plan"]["cases"][0]["purpose"] = "duration"

    v, identity = verification_fixture(inputs, mutate=change)
    with pytest.raises(ProofRefusal):
        interpret_verification(v, identity, allow_synthetic=True)


def test_reference_must_have_independent_accepted_review(inputs):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    v, identity = verification_fixture(inputs)
    # Removing the independently reviewed expected record from declared context is not
    # repaired by its raw SourceRecord staying in the artifact map.
    from uarch_contract.report_context import ReportContext
    from uarch_contract.table import UarchCostTable

    from tests.fixtures.u2_b.b2_support import put

    store = dict(v.artifacts)
    c = v.context.model_dump(mode="json")
    c["verification_hashes"] = [identity]
    put(store, c, "context_hash")
    t = v.table.model_dump(mode="json")
    t["artifacts"]["report_context_hash"] = c["context_hash"]
    put(store, t, "table_hash")
    v = v._replace(
        context=ReportContext.model_validate(c),
        table=UarchCostTable.model_validate(t),
        artifacts=store,
    )
    with pytest.raises(ProofUnsupported, match="CLOSURE"):
        interpret_verification(v, identity, allow_synthetic=True)


def test_verification_assembly_passes_actual_in_memory_loader(inputs):
    from rkuarch.provenance.proof import interpret_verification
    from rkuarch.table.artifacts import verify_report_inputs
    from tests.fixtures.u2_b.proof_support import verification_fixture

    v, identity = verification_fixture(inputs)
    verified = verify_report_inputs(v.table, v.artifacts)
    assert interpret_verification(verified, identity, allow_synthetic=True).outcome == "passed"


def test_supported_member_future_version_is_unsupported():
    raw = envelope(
        {"suite-plan.json": canonical_json(dict(format="u2-proof-suite-plan/3")).encode()}
    )
    with pytest.raises(ProofUnsupported, match="VERSION"):
        decode_proof(raw)


def test_total_decoded_bound():
    raw = envelope(
        {
            "original-expected.txt": b"1" * (4 * 1024 * 1024 + 1),
            "original-compiler.txt": b"2" * (4 * 1024 * 1024),
        }
    )
    with pytest.raises(ProofUnsupported, match="SIZE"):
        decode_proof(raw)


def test_band_outward_subnormal_overflow_and_all_zero():
    tiny = "0." + "0" * 323 + "1"
    # Direct outward conversion is independently testable even below minimum binary64.
    from rkuarch.provenance.proof_raw import outward_high

    assert outward_high(Fraction(tiny)).hex() == "0x0.0000000000001p-1022"
    assert outward_high(Fraction("0.2")).hex() == "0x1.999999999999ap-3"
    with pytest.raises(ProofUnsupported):
        outward_high(Fraction(10**400))
    assert (
        error_band(
            ["1"],
            ["1"],
            {"policy": "max-absolute-relative-error/1", "low_rel": "0", "high_rel": "0"},
        )
        is None
    )


def test_source_target_substitution_and_null_mapping(inputs):
    from rkuarch.provenance.proof import check_target_applicability

    ref, case = capture_case(inputs)
    bound = bind_capture(inputs, ref, case)
    statuses = check_target_applicability(bound, bound.scopes, ())
    assert statuses[0]["mapping_match"] == "UNKNOWN"
    wrong = bound.scopes[0].model_copy(update={"model_identity_hash": "sha256:" + "f" * 64})
    for scopes in ((wrong,), (bound.scopes[0], wrong)):
        with pytest.raises(ProofRefusal, match="SOURCE_MODEL"):
            check_target_applicability(bound, scopes, ())
    with pytest.raises(ProofUnsupported):
        check_target_applicability(bound, (), ())


def test_verification_expected_reference_identity_cannot_be_relabelled(inputs):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    def change(d):
        d["checks"]["reference_identity"] = "some-other-independent-source"

    v, identity = verification_fixture(inputs, mutate=change)
    with pytest.raises(ProofRefusal, match="REFERENCE_IDENTITY"):
        interpret_verification(v, identity, allow_synthetic=True)


def test_unreferenced_optional_member_refuses(inputs):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    # Mutant assembled through fixture hook before hashing, not an invalid-byte shortcut.
    v, identity = verification_fixture(inputs, extra_members={"original-compiler.txt": b"128"})
    with pytest.raises(ProofRefusal, match="UNREFERENCED"):
        interpret_verification(v, identity, allow_synthetic=True)


def test_historical_prediction_and_unsupported_aggregate(inputs):
    from rkuarch.provenance.proof import bind_prediction
    from tests.fixtures.u2_b.proof_support import measurement_fixture

    v, source_hash, raw = measurement_fixture(inputs)
    assert bind_prediction(v, source_hash).value == 64
    assert inputs.table.rows[0].counts.matrix_ops != 64  # Target row is a distinct quantity.
    with pytest.raises(ProofUnsupported, match="AGGREGATE_FIDELITY"):
        interpret_measurement(raw)


def test_rehashed_prediction_scalar_refuses(inputs):
    from rkuarch.provenance.proof import bind_prediction
    from tests.fixtures.u2_b.proof_support import measurement_fixture

    v, source_hash, raw = measurement_fixture(inputs, prediction_value="65")
    with pytest.raises(ProofRefusal, match="PREDICTION_SCALAR"):
        bind_prediction(v, source_hash)


def test_saved_A3_scope_model_energy_and_stub_display(inputs):
    from uarch_contract.report_context import RenderSpec

    from rkuarch.provenance.badge import assess_metric
    from rkuarch.report.badged import badged
    from rkuarch.table.build import CapturedWork, consumed_energy_families, source_scopes
    from rkuarch.workload.identity import legacy_model_id

    c = CapturedWork(
        inputs.bundle,
        inputs.assumptions,
        inputs.request,
        inputs.derivation,
        inputs.jobs,
        inputs.results,
    )
    scopes = source_scopes(c, family=inputs.registry.entries[0].family)
    assert len(scopes) == 498 and consumed_energy_families(c) == ()
    assert legacy_model_id(inputs.jobs[0], inputs.bundle) == inputs.model_card.model_id
    assert len(scopes[(inputs.results[0].result_hash, "/duration_ps")]) == len(
        inputs.results[0].per_op
    )
    assert all(
        s.mapping_match is None and s.mapping_correspondence_hash is None
        for ss in scopes.values()
        for s in ss
    )
    a = assess_metric(
        inputs.context,
        "/rows/0/duration_s",
        scopes=scopes,
        channel="duration_s",
        artifacts=inputs.artifacts,
        design_status=inputs.hardware.design_status,
    )
    assert a.badge == "stub" and a.complete
    spec = dict(
        format="uarch-render/1",
        renderer_version="proof-checkpoint",
        table_hash=inputs.table.table_hash,
        report_context_hash=inputs.context.context_hash,
        show_unvalidated_predictions=False,
        allow_synthetic_presentation=True,
        locale="en",
        number_format="roundtrip-display/1",
    )
    spec["render_hash"] = content_hash(spec)
    assert (
        badged(
            inputs.table.rows[0].duration_s,
            "s",
            a,
            RenderSpec.model_validate(spec),
            execution="executed",
        ).number
        is None
    )


def test_independent_nominal_capture_control_and_reverse_source_substitution(inputs):
    from rkuarch.provenance.proof import check_target_applicability
    from tests.fixtures.u2_b.proof_support import nominal_capture_fixture

    v, ref, case = nominal_capture_fixture(inputs)
    bound = bind_capture(v, ref, case)
    assert bound.value == Fraction(3332663724254167, 1125899906842624)  # binary64 2.96 s
    assert bound.scopes == ()  # No invented physical scope for nominal.
    actual_ref, actual_case = capture_case(inputs)
    actual = bind_capture(inputs, actual_ref, actual_case)
    assert bound.model_identity_hash != actual.model_identity_hash
    with pytest.raises(ProofRefusal, match="SOURCE_MODEL"):
        check_target_applicability(bound, actual.scopes, ())


def test_other_actual_result_with_same_model_and_zero_value_refuses(inputs):
    ref, case = capture_case(inputs, op=0)
    assert (
        inputs.results[0].per_op[0].counts.matrix_ops
        == inputs.results[1].per_op[0].counts.matrix_ops
        == 0
    )
    ref["value"]["artifact_hash"] = inputs.results[1].result_hash
    with pytest.raises(ProofRefusal, match="CAPTURE_INPUT"):
        bind_capture(inputs, ref, case)


def test_raw_duplicate_names_and_original_expected_source_hash():
    raw = json.loads(envelope({"original-expected.txt": b"64"}))
    raw["members"] *= 2
    with pytest.raises(ProofRefusal, match="DUPLICATE"):
        decode_proof(canonical_json(raw).encode())


@pytest.mark.parametrize(
    "mutation", ["duplicate-case", "renamed-case", "wrong-expected-pointer", "candidate-derived"]
)
def test_complete_suite_additional_mutants(inputs, mutation):
    from rkuarch.provenance.proof import interpret_verification
    from tests.fixtures.u2_b.proof_support import verification_fixture

    def change(d):
        if mutation == "duplicate-case":
            d["inventory"]["cases"].append(copy.deepcopy(d["inventory"]["cases"][0]))
        if mutation == "renamed-case":
            d["inventory"]["cases"][0]["case_id"] = "other-case"
        if mutation == "wrong-expected-pointer":
            d["links"]["entries"][0]["proof_pointer"] = "/cases/1/observed"
        if mutation == "candidate-derived":
            d["checks"]["candidate_used_for_expected"] = True

    v, identity = verification_fixture(inputs, mutate=change)
    with pytest.raises(ProofRefusal):
        interpret_verification(v, identity, allow_synthetic=True)


def test_malformed_csv_rows_and_changed_aggregate_still_unsupported(inputs):
    from tests.fixtures.u2_b.proof_support import measurement_fixture

    _, _, raw = measurement_fixture(inputs)
    value = json.loads(raw)
    members = {m["name"]: base64.b64decode(m["base64"]) for m in value["members"]}
    rows = members["device.csv"].decode().splitlines()
    missing = dict(members)
    missing["device.csv"] = ("\n".join(rows[:-1]) + "\n").encode()
    with pytest.raises(ProofRefusal, match="SAMPLE_INVENTORY"):
        interpret_measurement(envelope(missing, kind="measurement"))
    cols = rows[1].split(",")
    cols[3] = "1025"
    rows[1] = ",".join(cols)
    members["device.csv"] = ("\n".join(rows) + "\n").encode()
    with pytest.raises(ProofUnsupported, match="AGGREGATE_FIDELITY"):
        interpret_measurement(envelope(members, kind="measurement"))


def test_shared_band_bits_must_match_outward_encoding():
    from uarch_contract.evidence import EvidenceRecordErrorBand0

    from rkuarch.provenance.proof_raw import check_shared_band

    expected = (0.0, float.fromhex("0x1.3333333333334p-2"))
    check_shared_band(expected, EvidenceRecordErrorBand0(low_rel=0.0, high_rel=expected[1]))
    with pytest.raises(ProofRefusal, match="BAND"):
        check_shared_band(expected, EvidenceRecordErrorBand0(low_rel=0.0, high_rel=0.3))
    with pytest.raises(ProofRefusal, match="BAND"):
        check_shared_band(None, EvidenceRecordErrorBand0(low_rel=0.0, high_rel=0.3))
    with pytest.raises(ProofRefusal, match="BAND"):
        check_shared_band(expected, EvidenceRecordErrorBand0(low_rel=-0.0, high_rel=expected[1]))
    check_shared_band(None, None)


def test_whole_capture_keeps_all_operator_scopes(inputs):
    ref, case = capture_case(inputs)
    ref["value"]["json_pointer"] = "/counts/matrix_ops"
    ref["group_id"] = ref["operator_id"] = None
    case.update(
        metric_pointer="/counts/matrix_ops",
        group_id=None,
        operator_id=None,
        granularity="whole_iteration",
    )
    bound = bind_capture(inputs, ref, case)
    assert bound.value == 1184 and len(bound.scopes) == 17


def test_nominal_equal_value_cannot_hide_wrong_execution_binding(inputs):
    from tests.fixtures.u2_b.proof_support import nominal_capture_fixture

    v, ref, case = nominal_capture_fixture(inputs, wrong_binding_execution=True)
    with pytest.raises(ProofRefusal, match="NOMINAL_EXECUTION_BINDING"):
        bind_capture(v, ref, case)


def test_prediction_requires_reviewed_evidence_source(inputs):
    from rkuarch.provenance.proof import bind_prediction
    from tests.fixtures.u2_b.proof_support import measurement_fixture

    v, source_hash, _ = measurement_fixture(inputs)
    with pytest.raises(ProofUnsupported, match="PREDICTION_REVIEW"):
        bind_prediction(v._replace(evidence=()), source_hash)


def test_unknown_compiler_basis_is_unsupported_not_malformed():
    compiler = json.loads(
        (ROOT / "tests/fixtures/u2_b/proof-inputs/compiler.json").read_text()
    )
    compiler["basis"] = "unknown-rank-basis"
    with pytest.raises(ProofUnsupported, match="COUNT_BASIS"):
        decode_proof(envelope({"compiler-counts.json": canonical_json(compiler).encode()}))


def test_retained_nominal_uses_existing_upstream_binding_carrier(inputs):
    from tests.fixtures.u2_b.proof_support import nominal_capture_fixture

    v, ref, case = nominal_capture_fixture(inputs, retained=True)
    bound = bind_capture(v, ref, case)
    assert bound.value == Fraction(3332663724254167, 1125899906842624)
    assert bound.model_identity_hash == ref["model_identity_hash"] and not bound.scopes
