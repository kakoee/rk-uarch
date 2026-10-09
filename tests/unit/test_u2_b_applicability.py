"""B2 semantic tests authored before the B evaluator. No model execution."""

from copy import deepcopy

import pytest
from uarch_contract.evidence import EvidenceScopeCase
from uarch_contract.hashing import content_hash

from rkuarch.provenance.applicability import assess_evidence, match_scope
from rkuarch.provenance.badge import badge_for
from tests.fixtures.u2_b.b2_support import DIMENSIONS, fixture, replace_evidence


def assess(context, scope, store, **kwargs):
    args = dict(
        purpose="counts",
        channel="matrix_ops",
        granularity="whole_iteration",
        dimensions=DIMENSIONS,
        artifacts=store,
        allow_synthetic=True,
    )
    args.update(kwargs)
    return assess_evidence(context, (scope,), **args)


def test_B01_B02_S01_no_band_and_verification_are_distinct():
    context, scope, store, _ = fixture()
    result = assess(context, scope, store)
    assert result.badge == "estimated"
    assert result.error_band is None
    assert result.synthetic
    assert badge_for((), (result,), design_status="proposed").claim_badge is None
    context, scope, store, _ = fixture(rung="L2")
    assert assess(context, scope, store).badge == "stub"


@pytest.mark.parametrize(
    "change", [dict(purpose="duration"), dict(channel="vector_ops"), dict(granularity="operator")]
)
def test_B07_S03_S09_purpose_channel_and_granularity_do_not_transfer(change):
    context, scope, store, _ = fixture()
    assert assess(context, scope, store, **change).badge == "stub"


@pytest.mark.parametrize(
    "field,value",
    [
        ("mapping_match", None),
        ("dram_load_regime", None),
        ("model_identity_hash", "sha256:" + "a" * 64),
        ("initial_state", "cold"),
        ("frequency_ratio", 0.5),
        ("kv_block_size_tokens", 32),
    ],
)
def test_S07_scope_unknown_or_mismatch(field, value):
    context, scope, store, _ = fixture()
    assert assess(context, scope, store).badge == "estimated"
    request = scope.model_copy(update={field: value})
    dimensions = (*DIMENSIONS, "dram_load_regime") if field == "dram_load_regime" else DIMENSIONS
    assert assess(context, request, store, dimensions=dimensions).badge == "stub"


def test_S05_S06_precision_roles_and_format_names_are_exact():
    _, scope, _, _ = fixture()
    for precision in [
        dict(compute="fp8", kv_cache="bf16", operands={}),
        dict(compute="bf16", kv_cache="fp8", operands={}),
        dict(compute="BLOCKFP8", kv_cache="bf16", operands={}),
        dict(compute="bf16", kv_cache="bf16", operands={"a": "fp8"}),
    ]:
        altered = EvidenceScopeCase.model_validate(dict(scope.model_dump(), precision=precision))
        assert match_scope(scope, altered, DIMENSIONS)["precision"] == "MISMATCH"


def test_S08_no_cross_product_of_scope_cases():
    context, scope, store, evidence = fixture()
    first = scope.model_dump(mode="json")
    first["intensity_regime"] = "low"
    second = deepcopy(first)
    second["intensity_regime"] = "high"
    second["precision"]["compute"] = "fp8"
    context, _ = replace_evidence(context, store, evidence, scope=[first, second])
    request = scope.model_copy(update={"intensity_regime": "high"})
    assert (
        assess(context, request, store, dimensions=(*DIMENSIONS, "intensity_regime")).badge
        == "stub"
    )


@pytest.mark.parametrize("mutation", ["ordering", "verification", "review", "source", "synthetic"])
def test_evidence_prerequisites_cannot_be_asserted_away(mutation):
    context, scope, store, evidence = fixture()
    if mutation == "ordering":
        context, _ = replace_evidence(context, store, evidence, ordering_hash=None)
    if mutation == "verification":
        context, _ = replace_evidence(context, store, evidence, verification_hashes=[])
    if mutation == "review":
        review = deepcopy(store[evidence["review_hash"]])
        review["decision"] = "pending"
        review["review_hash"] = content_hash(review, exclude=("review_hash",))
        store[review["review_hash"]] = review
        e = dict(evidence, review_hash=review["review_hash"])
        e["evidence_hash"] = content_hash(e, exclude=("evidence_hash",))
        store[e["evidence_hash"]] = e
        c = context.model_dump()
        c["evidence_index"] = {e["evidence_id"]: e["evidence_hash"]}
        c["context_hash"] = content_hash(c, exclude=("context_hash",))
        context = type(context).model_validate(c)
    if mutation == "source":
        del store[evidence["source_hash"]]
        with pytest.raises(ValueError, match="ArtifactMissing"):
            assess(context, scope, store)
        return
    assert assess(context, scope, store, allow_synthetic=mutation != "synthetic").badge == "stub"


def test_S11_registry_missing_and_tampered_review_refuse():
    context, scope, store, evidence = fixture()
    del store[context.family_registry_hash]
    with pytest.raises(ValueError, match="ArtifactMissing"):
        assess(context, scope, store)
    context, scope, store, evidence = fixture()
    changed = dict(evidence, rung="L4")
    changed["evidence_hash"] = content_hash(changed, exclude=("evidence_hash",))
    store[changed["evidence_hash"]] = changed
    c = context.model_dump()
    c["evidence_index"] = {changed["evidence_id"]: changed["evidence_hash"]}
    c["context_hash"] = content_hash(c, exclude=("context_hash",))
    with pytest.raises(ValueError, match="ReviewSubjectMismatch"):
        assess(type(context).model_validate(c), scope, store)


def test_S12_band_is_not_a_confidence_interval():
    context, scope, store, _ = fixture(band={"low_rel": 0.01, "high_rel": 0.03})
    assert assess(context, scope, store).error_band == (0.01, 0.03)


def test_original_B11_unchanged_bins():
    from rkuarch.provenance.applicability import intensity_regime, load_regime

    assert [intensity_regime(x) for x in [0.49, 0.5, 2, 2.01, None]] == [
        "low",
        "middle",
        "middle",
        "high",
        None,
    ]
    assert [load_regime(x) for x in [0.29, 0.30, 0.70, 0.71, None]] == [
        "low",
        "middle",
        "middle",
        "high",
        None,
    ]


def test_original_B10_each_operator_needs_its_own_complete_case():
    context, scope, store, evidence = fixture()
    first = scope.model_copy(update={"op_class": "gemm", "intensity_regime": "low"})
    second = scope.model_copy(update={"op_class": "gemm", "intensity_regime": "high"})
    from tests.fixtures.u2_b.b2_support import put, review

    verification = dict(store[evidence["verification_hashes"][0]], scope=[first.model_dump()])
    review(store, verification, "verification_hash")
    c = context.model_dump()
    c["verification_hashes"] = [verification["verification_hash"]]
    put(store, c, "context_hash")
    context = type(context).model_validate(c)
    context, _ = replace_evidence(
        context,
        store,
        evidence,
        granularity="operator",
        scope=[first.model_dump()],
        verification_hashes=[verification["verification_hash"]],
    )
    assert (
        assess_evidence(
            context,
            (first,),
            purpose="counts",
            channel="matrix_ops",
            granularity="operator",
            dimensions=(*DIMENSIONS, "op_class", "intensity_regime"),
            artifacts=store,
            allow_synthetic=True,
        ).badge
        == "estimated"
    )
    result = assess_evidence(
        context,
        (first, second),
        purpose="counts",
        channel="matrix_ops",
        granularity="operator",
        dimensions=(*DIMENSIONS, "op_class", "intensity_regime"),
        artifacts=store,
        allow_synthetic=True,
    )
    assert result.badge == "stub"
    assert any("intensity_regime" in reason for reason in result.reasons)


def test_accepted_dimension_aliases_and_matched_correspondence():
    _, scope, _, _ = fixture()
    assert all(
        value == "MATCH"
        for value in match_scope(
            scope, scope, ("model_identity", "precision_roles", "kv_layout")
        ).values()
    )
    context, scope, store, evidence = fixture()
    matched = scope.model_copy(update={"mapping_match": "matched"})
    context, _ = replace_evidence(context, store, evidence, scope=[matched.model_dump()])
    assert assess(context, matched, store).badge == "stub"


def test_missing_band_does_not_hide_conflicting_applicable_bands():
    context, scope, store, evidence = fixture(band={"low_rel": 0.01, "high_rel": 0.02})
    from tests.fixtures.u2_b.b2_support import put, review

    different = review(
        store,
        dict(evidence, evidence_id="B-other-band", error_band={"low_rel": 0.02, "high_rel": 0.04}),
        "evidence_hash",
    )
    c = context.model_dump()
    c["evidence_index"][different["evidence_id"]] = different["evidence_hash"]
    put(store, c, "context_hash")
    with pytest.raises(ValueError, match="AmbiguousEvidenceBand"):
        assess(type(context).model_validate(c), scope, store)


def test_S02_original_B1_no_band_fixture_is_not_positive_L3_evidence():
    import json

    from uarch_contract.evidence import EvidenceScopeCase
    from uarch_contract.hashing import artifact_identity
    from uarch_contract.report_context import ReportContext

    from tests.fixtures.u2_b.b2_support import ROOT, ZERO, put

    directory = ROOT / "tests/fixtures/u2_b"
    store = {}
    for p in directory.glob("*.json"):
        value = json.loads(p.read_text())
        if isinstance(value, dict):
            store[artifact_identity(value)] = value
    source = json.loads((directory / "evidence-source.json").read_text())
    store[source["raw_blob_sha256"]] = (directory / "source-literals.json").read_bytes()
    e = json.loads((directory / "evidence-no-band.json").read_text())
    a = json.loads((directory / "actual-assumptions.json").read_text())
    registry = json.loads((directory / "family-registry.json").read_text())
    context = put(
        store,
        dict(
            format="uarch-report-context/2",
            model_identity=a["model"],
            assumptions_hash=a["assumptions_hash"],
            request_hash=ZERO,
            family_registry_hash=registry["registry_hash"],
            metric_dependencies_hash=ZERO,
            evidence_index={e["evidence_id"]: e["evidence_hash"]},
            comparison_hashes=[],
            verification_hashes=[],
            used_energy_families=[],
            limitations=["B1 negative input only"],
        ),
        "context_hash",
    )
    result = assess(
        ReportContext.model_validate(context),
        EvidenceScopeCase.model_validate(e["scope"][0]),
        store,
    )
    assert result.badge == "stub" and result.error_band is None


def test_original_B11_gemm_fill_is_distinct_from_intensity():
    from rkuarch.provenance.applicability import array_fill

    assert array_fill(15, 16, 16, 16) == "underfilled"
    assert array_fill(16, 15, 16, 16) == "underfilled"
    assert array_fill(16, 16, 16, 16) == "full"
    assert array_fill(None, None, 16, 16) is None


def test_unknown_relevant_kv_role_is_not_equal_evidence():
    _, scope, _, _ = fixture()
    precision = scope.precision.model_copy(update={"kv_cache": None})
    unknown = scope.model_copy(update={"precision": precision})
    assert match_scope(unknown, unknown, ("precision_roles",))["precision_roles"] == "UNKNOWN"
