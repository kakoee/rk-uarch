"""Independent B synthetic records, never a file-loader return or runtime result."""

import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue
from uarch_contract.evidence import EvidenceScopeCase
from uarch_contract.hashing import artifact_identity, content_hash, review_subject_hash, sha256
from uarch_contract.report_context import ReportContext

ROOT = Path(__file__).resolve().parents[3]
ZERO = "sha256:" + "0" * 64
DIMENSIONS = (
    "family",
    "model_identity_hash",
    "precision",
    "mapping_match",
    "initial_state",
    "kv_block_size_tokens",
    "frequency_ratio",
    "prepared_bundle_hash",
)


def put(
    store: dict[str, object], value: dict[str, object], own: str | None = None
) -> dict[str, object]:
    if own:
        value[own] = content_hash(value, exclude=(own,))
    store[artifact_identity(value)] = value
    return value


def review(store: dict[str, object], value: dict[str, object], own: str) -> dict[str, object]:
    r = put(
        store,
        dict(
            format="uarch-evidence-review/1",
            reviewer="B synthetic reviewer",
            independent=True,
            decision="accepted",
            reviewed_subject_hashes=[review_subject_hash(value)],
            rationale="Synthetic unit premise; no human or silicon validation.",
        ),
        "review_hash",
    )
    value["review_hash"] = r["review_hash"]
    return put(store, value, own)


def fixture(
    *,
    rung: str = "L3",
    purpose: str = "counts",
    channel: str = "matrix_ops",
    band: dict[str, float] | None = None,
) -> tuple[ReportContext, EvidenceScopeCase, dict[str, object], dict[str, object]]:
    store: dict[str, object] = {}
    # Reuse the accepted prepared identity as test input, not an independently built workload.
    bundle = json.loads((ROOT / "contract/tests/fixtures/u2/independent-bundle.json").read_text())
    put(store, bundle)
    hardware = bundle["hardware_spec"]
    hh = content_hash(hardware)
    store[hh] = hardware
    model = dict(
        name="physical-resolved",
        version="B-independent-synthetic",
        implementation_hash=content_hash("not executable; test identity only"),
    )
    mh = content_hash(model)
    scope = dict(
        family="B-test-family",
        model_identity_hash=mh,
        hardware_spec_hash=hh,
        prepared_bundle_hash=bundle["bundle_hash"],
        precision=dict(compute="bf16", kv_cache="bf16", operands={}),
        op_class=None,
        array_fill=None,
        intensity_regime=None,
        noc_load_regime=None,
        dram_load_regime=None,
        mapping_match="compiler-chosen",
        mapping_correspondence_hash=None,
        initial_state="steady",
        kv_block_size_tokens=16,
        frequency_ratio=1.0,
    )
    raw = b"B independent SYNTHETIC measurement and ordering premise; not executed.\n"
    store[sha256(raw)] = raw
    source = put(
        store,
        dict(
            format="uarch-reference-source/1",
            kind="synthetic_fixture",
            reference_identity="B-independent",
            reference_version="1",
            raw_blob_sha256=sha256(raw),
            independence_from_candidate=True,
            limitation="synthetic only",
        ),
        "source_hash",
    )
    ordering = put(
        store,
        dict(
            format="uarch-ordering/1",
            prediction_commit="1" * 40,
            result_commit="2" * 40,
            prediction_tree_hash=content_hash("synthetic tree"),
            prediction_is_ancestor=True,
            verification_source_hash=source["source_hash"],
        ),
        "ordering_hash",
    )
    verification = review(
        store,
        dict(
            format="uarch-verification/1",
            rung="L2",
            model_identity_hash=mh,
            purpose=purpose,
            outcome="passed",
            scope=[scope],
            source_hash=source["source_hash"],
        ),
        "verification_hash",
    )
    evidence = review(
        store,
        dict(
            format="uarch-evidence/1",
            evidence_id="B-synthetic-L3",
            classification="synthetic_fixture",
            rung=rung,
            purpose=purpose,
            channel=channel,
            energy_family=None,
            granularity="whole_iteration",
            scope=[scope],
            source_hash=source["source_hash"],
            ordering_hash=ordering["ordering_hash"],
            verification_hashes=[verification["verification_hash"]],
            error_band=band,
        ),
        "evidence_hash",
    )
    registry = review(
        store,
        dict(
            format="uarch-family-registry/1",
            version="B-unit-1",
            entries=[dict(hardware_spec_hash=hh, family=scope["family"])],
        ),
        "registry_hash",
    )
    assumptions = put(
        store,
        dict(
            format="uarch-assumptions/1",
            model=model,
            algorithms={"case": "independent synthetic evidence evaluation"},
            limitations=["No runtime closure or actual execution represented."],
        ),
        "assumptions_hash",
    )
    context = put(
        store,
        dict(
            format="uarch-report-context/2",
            assumptions_hash=assumptions["assumptions_hash"],
            model_identity=model,
            request_hash=ZERO,
            family_registry_hash=registry["registry_hash"],
            metric_dependencies_hash=ZERO,
            evidence_index={evidence["evidence_id"]: evidence["evidence_hash"]},
            comparison_hashes=[],
            used_energy_families=[],
            verification_hashes=[verification["verification_hash"]],
            limitations=["Partial in-memory evaluator inputs, NOT complete runtime closure."],
        ),
        "context_hash",
    )
    return (
        ReportContext.model_validate(context),
        EvidenceScopeCase.model_validate(scope),
        store,
        evidence,
    )


def replace_evidence(
    context: ReportContext,
    store: dict[str, object],
    evidence: dict[str, object],
    **changes: object,
) -> tuple[ReportContext, dict[str, object]]:
    evidence = dict(evidence, **changes)
    evidence = review(store, evidence, "evidence_hash")
    context_data = context.model_dump(mode="json")
    context_data["evidence_index"] = {evidence["evidence_id"]: evidence["evidence_hash"]}
    put(store, context_data, "context_hash")
    return ReportContext.model_validate(context_data), evidence


def metric_fixture() -> tuple[
    ReportContext,
    dict[tuple[str, str, str], tuple[EvidenceScopeCase, ...]],
    dict[str, object],
    dict[str, object],
]:
    """Independent literal DAG with both source models, not a runtime comparison artifact."""
    context, scope, store, actual_evidence = fixture()
    context_data = context.model_dump(mode="json")
    actual_assumptions = cast(dict[str, object], store[context_data["assumptions_hash"]])
    reference_model = dict(
        name="nominal-rk-compatibility",
        version="B-independent-reference",
        implementation_hash=content_hash("synthetic reference label"),
    )
    rh = content_hash(reference_model)
    reference = put(
        store,
        dict(
            format="uarch-assumptions/1",
            model=reference_model,
            algorithms={"case": "independent stipulated reference literal"},
            limitations=["Not an oracle input or executed model."],
        ),
        "assumptions_hash",
    )
    rs = scope.model_copy(update={"model_identity_hash": rh})
    verification = dict(
        cast(dict[str, object], store[cast(list[str], actual_evidence["verification_hashes"])[0]]),
        model_identity_hash=rh,
        scope=[rs.model_dump(mode="json")],
    )
    verification = review(store, verification, "verification_hash")
    evidence = dict(
        actual_evidence,
        evidence_id="B-reference-count",
        scope=[rs.model_dump(mode="json")],
        verification_hashes=[verification["verification_hash"]],
    )
    evidence = review(store, evidence, "evidence_hash")
    context_data["evidence_index"][evidence["evidence_id"]] = evidence["evidence_hash"]
    context_data["verification_hashes"].append(verification["verification_hash"])
    raw = put(
        store,
        dict(
            classification="synthetic_fixture",
            matrix_ops=12.0,
            reference_matrix_ops=8.0,
            duration_ps=250.0,
            reference_duration_s=2.5e-10,
        ),
    )
    raw_hash = artifact_identity(raw)
    sources = []
    for model, assumptions, fields in [
        (
            scope.model_identity_hash,
            actual_assumptions,
            [("matrix_ops", "counts"), ("duration_ps", "duration")],
        ),
        (rh, reference, [("reference_matrix_ops", "counts"), ("reference_duration_s", "duration")]),
    ]:
        for field, purpose in fields:
            selectors = [
                dict(kind="prepared_content", artifact_hash=raw_hash, json_pointer="/" + field),
                dict(
                    kind="model_assumption",
                    artifact_hash=assumptions["assumptions_hash"],
                    json_pointer="/algorithms",
                ),
                dict(
                    kind="model_evidence",
                    artifact_hash=assumptions["assumptions_hash"],
                    json_pointer="/model",
                ),
            ]
            if field == "duration_ps":
                for pointer in [
                    "/cores/grid/rows",
                    "/cores/grid/cols",
                    "/clock_domains/core/freq_hz",
                    "/cores/core_type/vector_engine/ops_per_cycle",
                    "/memory/dram/bw_bytes_per_s",
                    "/cores/core_type/matrix_engine/macs_per_cycle/bf16",
                ]:
                    selectors.append(
                        dict(
                            kind="hardware_leaf",
                            artifact_hash=scope.hardware_spec_hash,
                            json_pointer=pointer,
                        )
                    )
            sources.append(
                dict(
                    artifact_hash=raw_hash,
                    model_identity_hash=model,
                    recipe=dict(
                        metric_path="/" + field,
                        purpose=purpose,
                        granularity="whole_iteration",
                        applicable_dimensions=list(DIMENSIONS),
                        selectors=selectors,
                    ),
                )
            )
    recipes = []
    for name, purpose, metric_fields in [
        ("count", "counts", ["matrix_ops", "reference_matrix_ops"]),
        ("timing", "duration", ["duration_ps", "reference_duration_s"]),
    ]:
        recipes.append(
            dict(
                metric_path="/" + name,
                purpose=purpose,
                granularity="whole_iteration",
                applicable_dimensions=list(DIMENSIONS),
                selectors=[
                    dict(kind="result_field", artifact_hash=raw_hash, json_pointer="/" + f)
                    for f in metric_fields
                ],
            )
        )
    deps = review(
        store,
        dict(
            format="uarch-metric-dependencies/1",
            version="B2-independent",
            model_identity_hash=scope.model_identity_hash,
            recipes=recipes,
            source_recipes=sources,
        ),
        "dependencies_hash",
    )
    context_data["metric_dependencies_hash"] = deps["dependencies_hash"]
    put(store, context_data, "context_hash")
    scopes: dict[tuple[str, str, str], tuple[EvidenceScopeCase, ...]] = {
        (s.model_identity_hash, p, "whole_iteration"): (s,)
        for s in (scope, rs)
        for p in ("counts", "duration")
    }
    return ReportContext.model_validate(context_data), scopes, store, deps


def proposal_artifacts() -> dict[str, dict[str, JsonValue]]:
    """Read-only accepted A test support for independent C1/C2 regression mutations."""
    directory = ROOT / "docs/reviews/U2-U0003-proposal"
    store: dict[str, dict[str, JsonValue]] = {}
    for path in [*directory.glob("*.json"), *(directory / "fixtures").glob("*.json")]:
        value = json.loads(path.read_text())
        if isinstance(value, dict):
            store[artifact_identity(value)] = value
    return store
