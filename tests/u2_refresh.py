"""B refreshed-artifact consumer. Raw inspection is not adoption; synthetic inputs stay so.

No upstream execution. Uses existing A candidate/capture and shared comparison carriers.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict, cast

from pydantic import JsonValue, TypeAdapter
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.comparison import (
    ComparisonArtifact,
    ComparisonFixture,
    ExpectedPrecisionRefusal,
    PrecisionCheckInput,
    PrecisionCheckTrace,
    PrecisionRefusalObservation,
    ReferenceInventory,
)
from uarch_contract.evidence import ReviewRecord
from uarch_contract.exports import ComponentPrecision
from uarch_contract.hashing import (
    artifact_identity,
    content_hash,
    sha256,
    strict_json_loads,
    verify_identity,
)
from uarch_contract.prepared import PreparedBundle, Query
from uarch_contract.request import CharacterizationRequest

from contract.tests import nominal_candidate
from contract.tests.parity import rank_counts
from contract.tests.u2_comparison import assemble_comparison, precision_observation
from rkuarch.engines.protocol import (
    EngineJob,
    EngineResult,
    validate_engine_job,
    validate_engine_result,
)
from rkuarch.hw.derive import derive_rk_params
from rkuarch.table.build import CapturedWork, TablePackage, computation_sources
from rkuarch.workload.characterize import capacity_summary
from rkuarch.workload.prepared import physical_assumptions, validate_execution_bundle
from scripts import u2_inputs as ui
from scripts import vendor_rk as vr
from tests import u2_comparison as old


# Test orchestration shapes, not alternate shared wire contracts.
class PhysicalAttempt(TypedDict, total=False):
    execution: str
    error: str | None
    bundle_hash: str | None
    assumptions_hash: str | None
    job_hash: str | None
    result_hash: str | None
    failure_hash: str


class PhysicalCapture(TypedDict):
    attempts: dict[str, PhysicalAttempt]
    artifacts: dict[str, object]


ValidatedPhysical = tuple[
    PreparedBundle, AssumptionSet, CharacterizationRequest, EngineJob, EngineResult
]


class ConsumerRun(TypedDict):
    nominal: ComparisonArtifact
    physical: ComparisonArtifact
    inventory: ReferenceInventory
    artifacts: dict[str, object]
    inputs: ui.Inputs
    original_rows: list[dict[str, JsonValue]]
    physical_capture: PhysicalCapture
    validated_physical: dict[str, ValidatedPhysical]
    nominal_errors: list[dict[str, str]]
    physical_errors: list[dict[str, str | None]]
    limitations: list[str]
    synthetic: bool


SYNTHETIC_MARKER = b"Explicit synthetic test premises; not real adoption or oracle output.\n"


def audit_candidate(root: Path) -> dict[str, Any]:
    """Strict byte/source/matrix audit; returns no ReferenceInventory or adoption assertion."""
    vr.check_manifest(root)
    vr.check_snapshot_inputs(root, check_support=True)
    vr.check_generator(root)
    source_hashes = strict_json_loads(
        (ui.ROOT / "tests/fixtures/u2_b/refresh/pinned-source-sha256.json").read_bytes()
    )
    if set(source_hashes) != set(vr.SOURCES):
        raise ValueError("RefusalSourceMismatch: pinned source inventory")
    for name, expected in source_hashes.items():
        if vr.digest((root / name).read_bytes()) != expected:
            raise ValueError("RefusalSourceMismatch: pinned source bytes " + name)
    if not (root / "u2-inputs").is_dir():
        raise ValueError("RefreshedInputsRequired")
    if sha256((root / "rk/engine/f0/compute.py").read_bytes()) != "sha256:" + old.DIRECT_SOURCE:
        raise ValueError("RefusalSourceMismatch: pinned callable source bytes")
    rows = strict_json_loads((root / "parity/fixtures.json").read_bytes())
    if len(rows) != 1008:
        raise ValueError("IncompleteComparisonInventory: exact1008 refreshed matrix")
    inputs = ui.load_inputs(
        root / "u2-inputs", vr.digest((root / "u2-inputs/SHA256SUMS").read_bytes())
    )
    precision_records(
        inputs,
        (root / "parity/refusals.json").read_bytes(),
        (root / "rk/engine/f0/compute.py").read_bytes(),
        {},
        synthetic=(root / "SYNTHETIC-REFERENCE").exists(),
    )
    # The above structural assembly is discarded; raw inspection grants no evidence status.
    return dict(
        adopted=False,
        rows=len(rows),
        manifest_sha256=sha256((root / "MANIFEST.json").read_bytes()),
        input_manifest_sha256=vr.digest((root / "u2-inputs/SHA256SUMS").read_bytes()),
    )


def adoption_authority(root: Path, review_path: Path, trusted_review_sha256: str) -> ReviewRecord:
    """Verify separately supplied human adoption record; hashes do not identify its signer.

    The caller must obtain the review-file digest from the explicit coordinator/human
    adoption handoff. Merely pointing at a valid candidate never calls this authority.
    """
    if root.resolve() != ui.ADOPTED.resolve() or (root / "SYNTHETIC-REFERENCE").exists():
        raise ValueError("AdoptionRequired: canonical adopted path; no synthetic marker")
    raw = review_path.read_bytes()
    if vr.digest(raw) != trusted_review_sha256:
        raise ValueError("AdoptionRequired: trusted review bytes differ")
    review = ReviewRecord.model_validate(strict_json_loads(raw))
    verify_identity(review, "review_hash")
    if (
        review.decision != "accepted"
        or not review.independent
        or review.reviewer != "Javid (@jjaffari)"
        or review.reviewed_subject_hashes != (sha256((root / "MANIFEST.json").read_bytes()),)
    ):
        raise ValueError("AdoptionRequired: explicit human acceptance of exact manifest")
    return review


def consume_adopted(
    *,
    adoption_review: Path,
    review_sha256: str,
    physical_replay: PhysicalCapture | None = None,
) -> ConsumerRun:
    """Only the canonical adopted location plus a separately trusted adoption review."""
    review = adoption_authority(ui.ADOPTED, adoption_review, review_sha256)
    return _consume(ui.ADOPTED, synthetic=False, physical_replay=physical_replay, review=review)


def consume_synthetic(root: Path, *, physical_replay: PhysicalCapture | None = None) -> ConsumerRun:
    if (root / "SYNTHETIC-REFERENCE").read_bytes() != SYNTHETIC_MARKER:
        raise ValueError("SyntheticPremiseRequired")
    return _consume(root, synthetic=True, physical_replay=physical_replay)


def precision_records(
    inputs: ui.Inputs,
    raw: bytes,
    source: bytes,
    store: dict[str, object],
    *,
    synthetic: bool,
) -> tuple[
    dict[str, str], tuple[ExpectedPrecisionRefusal, ...], tuple[PrecisionRefusalObservation, ...]
]:
    """Bind every trace fact to its exact captured event, not merely an existing pointer."""
    if sha256(source) != "sha256:" + old.DIRECT_SOURCE:
        raise ValueError("RefusalSourceMismatch: callable bytes")
    store[sha256(source)] = source
    store[sha256(raw)] = raw
    events = strict_json_loads(raw)
    if not isinstance(events, list):
        raise ValueError("RefusalSourceMismatch: event list")

    def raw_record(data: bytes, kind: str, identity: str) -> dict[str, object]:
        return old.put(
            store,
            dict(
                format="uarch-reference-source/1",
                kind=kind,
                independence_from_candidate=True,
                raw_blob_sha256=sha256(data),
                reference_identity=identity,
                reference_version=vr.PIN,
                limitation=(
                    "Source closure only; no measurement, accuracy evidence or adoption claim."
                ),
            ),
            "source_hash",
        )

    captured_source = raw_record(
        raw,
        "synthetic_fixture" if synthetic else "contract_test",
        "direct-peak captured event bytes",
    )
    callable_source = raw_record(source, "contract_test", "pinned direct-peak callable bytes")
    capture = old.put(
        store,
        dict(
            events=events,
            capture_source=dict(
                artifact_hash=captured_source["source_hash"], json_pointer="/raw_blob_sha256"
            ),
        ),
    )
    # Independent accepted expectation inventory; never derived from observed successes.
    pointer, expected_values, _ = old.precision_plan(inputs, store)
    plan = dict(
        cast(dict[str, JsonValue], store[pointer["artifact_hash"]]),
        capture_source=dict(
            artifact_hash=callable_source["source_hash"], json_pointer="/raw_blob_sha256"
        ),
    )
    old.put(store, plan)
    pointer = dict(pointer, artifact_hash=artifact_identity(plan))
    expected = tuple(ExpectedPrecisionRefusal.model_validate(e) for e in expected_values)
    by_pair = {}
    for e in expected:
        check = PrecisionCheckInput.model_validate(store[e.check_input_hash])
        by_pair[
            (
                "components/" + check.component_role,
                e.precision.compute.value,
                e.precision.kv_cache.value,
            )
        ] = e
    found = {}
    fields = {
        "component_params_file",
        "component_params_sha256",
        "rk_sha",
        "compute",
        "kv_cache",
        "execution",
        "exception",
        "message",
        "boundary",
        "callable_source_sha256",
    }
    for index, event in enumerate(events):
        if not isinstance(event, dict) or set(event) != fields:
            raise ValueError("RefusalSourceMismatch: exact direct event fields")
        key = (event["component_params_file"], event["compute"], event["kv_cache"])
        if key not in by_pair:
            raise ValueError("UnknownExpectedRefusal: extra component/precision event")
        if key in found:
            raise ValueError("DuplicateRefusalObservation")
        e = by_pair[key]
        entry = next(
            v for v in inputs.entries if v.binding.binding_hash == e.component_binding_hash
        )
        if (
            event["rk_sha"] != vr.PIN
            or event["callable_source_sha256"] != old.DIRECT_SOURCE
            or event["component_params_sha256"] != vr.digest(inputs.descriptors[entry.component_id])
        ):
            raise ValueError("RefusalSourceMismatch: captured pin/source/component")
        execution = event["execution"]
        if (
            execution not in ("refused", "succeeded", "execution_failed")
            or not isinstance(event["message"], str)
            or not event["message"]
            or (execution == "succeeded") != (event["exception"] is None)
        ):
            raise ValueError("RefusalSourceMismatch: captured outcome/message")
        trace = old.put(
            store,
            dict(
                format="uarch-precision-check-trace/1",
                check_input_hash=e.check_input_hash,
                classification="synthetic_observation" if synthetic else "captured_probe",
                capture_source=dict(
                    artifact_hash=artifact_identity(capture), json_pointer=f"/events/{index}"
                ),
                execution=execution,
                observed_boundary=event["boundary"],
                error_class=event["exception"],
                message=event["message"],
            ),
            "trace_hash",
        )
        found[key] = PrecisionCheckTrace.model_validate(trace)
    observations = []
    for key, e in by_pair.items():
        check = PrecisionCheckInput.model_validate(store[e.check_input_hash])
        o = precision_observation(
            e,
            check,
            found.get(key),
            reason=(
                "Explicit synthetic trace premise."
                if synthetic
                else "Direct captured event bound to exact snapshot source bytes."
            ),
        )
        store[o.observation_hash] = o.model_dump(mode="json")
        observations.append(o)
    return pointer, expected, tuple(observations)


def _query(row: Mapping[str, JsonValue]) -> Query:
    return TypeAdapter[Query](Query).validate_python(
        {
            k: v
            for k, v in cast(dict[str, JsonValue], row["query"]).items()
            if k not in ("total_prompt_tokens", "sum_of_squared_prompt_tokens")
        }
    )


def _common(row: Mapping[str, JsonValue], entry: ComponentPrecision) -> dict[str, object]:
    model = cast(dict[str, JsonValue], row["model"])
    shape = cast(dict[str, JsonValue], row["model_shape"])
    kv_heads, vocab, tp = (
        cast(int, model["kv_heads"]),
        cast(int, shape["vocab_size"]),
        cast(int, row["tp"]),
    )
    return dict(
        fixture_id=row["id"],
        component_binding_hash=entry.binding.binding_hash,
        query=_query(row).model_dump(mode="json"),
        precision=row["precision"],
        tp=row["tp"],
        projection_scope=dict(
            global_kv_heads=kv_heads,
            global_vocab=vocab,
            kv_replicated=kv_heads < tp,
            padded_vocab=math.ceil(vocab / tp) * tp,
        ),
    )


def capture_physical(
    inputs: ui.Inputs,
    rows: Sequence[Mapping[str, JsonValue]],
) -> PhysicalCapture:
    """Existing A bundles/jobs/results plus attempt index; not a parallel capture contract."""
    artifacts: dict[str, object] = {}
    attempts: dict[str, PhysicalAttempt] = {}
    groups: dict[
        tuple[str, int], tuple[PreparedBundle | None, AssumptionSet | None, str | None]
    ] = {}
    bundle: PreparedBundle | None
    assumptions: AssumptionSet | None
    for row in rows:
        if row["component_params_file"] != "components/npu-l4.yaml":
            continue
        key = (cast(str, row["model_id"]), cast(int, row["tp"]))
        if key not in groups:
            try:
                bundle, assumptions = old.prepare_h1(inputs, model_id=key[0], tp=key[1])
            except Exception as exc:
                groups[key] = (None, None, type(exc).__name__ + ": " + str(exc))
            else:
                groups[key] = (bundle, assumptions, None)
                artifacts[bundle.bundle_hash] = bundle.model_dump(mode="json")
                artifacts[assumptions.assumptions_hash] = assumptions.model_dump(mode="json")
                derivation = derive_rk_params(bundle.hardware_spec)
                artifacts[derivation.derivation_hash] = derivation.model_dump(mode="json")
        bundle, assumptions, error = groups[key]
        if bundle is None:
            failure = old.put(
                artifacts,
                dict(
                    requested={
                        k: row[k]
                        for k in (
                            "model",
                            "model_shape",
                            "model_sources",
                            "precision",
                            "tp",
                            "query",
                            "component_params_sha256",
                        )
                    },
                    execution="execution_failed",
                    error=error,
                    limitation=(
                        "Captured preparation exception; no bundle or engine result was produced."
                    ),
                ),
            )
            attempts[cast(str, row["id"])] = dict(
                execution="execution_failed",
                error=error,
                bundle_hash=None,
                assumptions_hash=None,
                job_hash=None,
                result_hash=None,
                failure_hash=artifact_identity(failure),
            )
            continue
        point = next(p for p in bundle.points if p.query == _query(row))
        assert assumptions is not None
        attempt: PhysicalAttempt = dict(
            bundle_hash=bundle.bundle_hash,
            assumptions_hash=assumptions.assumptions_hash,
            job_hash=None,
            result_hash=None,
            error=None,
        )
        try:
            job, result = old.physical_point(bundle, assumptions, point)
        except Exception as exc:
            attempt.update(
                dict(execution="execution_failed", error=type(exc).__name__ + ": " + str(exc))
            )
        else:
            attempt.update(
                dict(execution="executed", job_hash=job.job_hash, result_hash=result.result_hash)
            )
            artifacts[job.job_hash] = job.model_dump(mode="json")
            artifacts[result.result_hash] = result.model_dump(mode="json")
        attempts[cast(str, row["id"])] = attempt
    return dict(attempts=attempts, artifacts=artifacts)


def verify_physical(
    inputs: ui.Inputs,
    rows: Sequence[Mapping[str, JsonValue]],
    capture: PhysicalCapture,
) -> dict[str, ValidatedPhysical]:
    """Replay validates actual A contracts/joins; never invokes prepare or an engine."""
    selected = [r for r in rows if r["component_params_file"] == "components/npu-l4.yaml"]
    if set(capture["attempts"]) != {r["id"] for r in selected}:
        raise ValueError("IncompleteComparisonInventory: physical attempts")
    store = capture["artifacts"]
    from uarch_contract.assumptions import AssumptionSet

    validated = {}
    bundles = {}
    for row in selected:
        a = capture["attempts"][cast(str, row["id"])]
        if a["bundle_hash"] is None:
            failure = cast(dict[str, JsonValue], store[a["failure_hash"]])
            if (
                artifact_identity(failure) != a["failure_hash"]
                or failure["requested"]
                != {
                    k: row[k]
                    for k in (
                        "model",
                        "model_shape",
                        "model_sources",
                        "precision",
                        "tp",
                        "query",
                        "component_params_sha256",
                    )
                }
                or failure["error"] != a["error"]
                or not a["error"]
                or a["execution"] != "execution_failed"
                or failure["execution"] != "execution_failed"
                or any(a[k] is not None for k in ("job_hash", "result_hash", "assumptions_hash"))
            ):
                raise ValueError("RefusalSourceMismatch: captured preparation failure")
            continue
        if a["bundle_hash"] not in bundles:
            bundles[a["bundle_hash"]] = validate_execution_bundle(store[a["bundle_hash"]])
        bundle = bundles[a["bundle_hash"]]
        assumptions = AssumptionSet.model_validate(store[cast(str, a["assumptions_hash"])])
        verify_identity(assumptions, "assumptions_hash")
        entry = next(e for e in inputs.entries if e.component_id == "compute.asic.npu-l4")
        assert entry.binding.kind == "uarch_projection"
        if (
            bundle.intent.model.model_dump(mode="json") != row["model"]
            or bundle.intent.model_shape.model_dump(mode="json") != row["model_shape"]
            or bundle.intent.precision.model_dump(mode="json") != row["precision"]
            or bundle.intent.tp != row["tp"]
            or bundle.intent.component_id != "npu-l4"
            or bundle.intent.hardware_spec_hash != entry.binding.hardware_spec_hash
            or bundle.intent.assumptions_hash != assumptions.assumptions_hash
            or assumptions != physical_assumptions()
        ):
            raise ValueError("RefusalSourceMismatch: physical model/input/assumptions")
        point = next(p for p in bundle.points if p.query == _query(row))
        request = CharacterizationRequest(
            **bundle.intent.model_dump(mode="json"), prepared_input_hash=bundle.bundle_hash
        )
        if a["execution"] == "executed":
            capacity_summary(bundle, point)
            job = validate_engine_job(store[cast(str, a["job_hash"])], bundle, request)
            result = validate_engine_result(store[cast(str, a["result_hash"])], job)
            if job.point != point or job.assumptions_hash != assumptions.assumptions_hash:
                raise ValueError("RefusalSourceMismatch: physical point/assumptions")
            validated[cast(str, row["id"])] = (bundle, assumptions, request, job, result)
        elif a["execution"] == "execution_failed":
            if a["job_hash"] is not None or a["result_hash"] is not None or not a["error"]:
                raise ValueError("RefusalSourceMismatch: failed attempt fabricated result")
            # Capacity failures are independently reproducible without producer execution.
            try:
                capacity_summary(bundle, point)
            except ValueError as exc:
                if a["error"] != "ValueError: " + str(exc):
                    raise ValueError("RefusalSourceMismatch: capacity failure") from exc
            else:
                raise ValueError("UnsupportedReplay: uncaptured non-capacity engine failure")
        else:
            raise ValueError("UnsupportedReplay: physical execution state")
    return validated


def _consume(
    root: Path,
    *,
    synthetic: bool,
    physical_replay: PhysicalCapture | None = None,
    review: ReviewRecord | None = None,
) -> ConsumerRun:
    audit = audit_candidate(root)
    inputs = ui.load_inputs(root / "u2-inputs", audit["input_manifest_sha256"])
    rows = strict_json_loads((root / "parity/fixtures.json").read_bytes())
    store = dict(inputs.artifacts)
    for e in inputs.entries:
        store[e.binding.binding_hash] = e.binding.model_dump(mode="json")
        raw = inputs.descriptors[e.component_id]
        store[sha256(raw)] = raw
    for path in [root / "MANIFEST.json", root / "u2-inputs/historical-source/MANIFEST.json"]:
        store[sha256(path.read_bytes())] = path.read_bytes()
    if review:
        store[review.review_hash] = review.model_dump(mode="json")
    pointer, expected, observations = precision_records(
        inputs,
        (root / "parity/refusals.json").read_bytes(),
        (root / "rk/engine/f0/compute.py").read_bytes(),
        store,
        synthetic=synthetic,
    )
    metadata = strict_json_loads((root / "GENERATOR.json").read_bytes())
    reference = dict(
        name="nominal-rk-compatibility",
        version=vr.PIN,
        implementation_hash="sha256:" + metadata["oracle_program_sha256"],
    )
    capture = physical_replay if physical_replay is not None else capture_physical(inputs, rows)
    validated = verify_physical(inputs, rows, capture)
    store.update(capture["artifacts"])
    invrows, nominal_rows, physical_rows, errors = [], [], [], []
    for row in rows:
        old.put(store, row)
        entry = next(
            e for e in inputs.entries if "components/" + ui.role(e) == row["component_params_file"]
        )
        common = _common(row, entry)
        ref = dict(rank_counts(row), duration_s=row["duration_s"], vector_ops=None)
        values = {
            n: dict(
                state="absent"
                if n == "vector_ops"
                else "null"
                if ref[n] is None
                else "zero"
                if ref[n] == 0
                else "positive",
                value=ref[n],
            )
            for n in old.CHANNELS
        }
        invrows.append(dict(common, values=values))
        execution, value, output, error = old.nominal_attempt(row, inputs, store)
        if error:
            errors.append(dict(fixture_id=row["id"], reason=error))
        quantities = (
            dict(output.counts.model_dump(mode="json"), duration_s=output.duration_s)
            if output
            else dict.fromkeys(old.CHANNELS)
        )
        nominal_rows.append(
            ComparisonFixture.model_validate(
                dict(
                    common,
                    execution=execution,
                    outcome="unassessed",
                    bundle_hash=None,
                    job_hash=None,
                    result_hash=None,
                    candidate_input_hash=value.input_hash if value else None,
                    candidate_output_hash=output.output_hash if output else None,
                    channels=[
                        old.channel(
                            n,
                            quantities[n],
                            ref[n],
                            output.output_hash if output else None,
                            "/duration_s" if n == "duration_s" else "/counts/" + n,
                            reference_state=values[n]["state"],
                            execution=execution,
                            nominal_omission=bool(output and quantities[n] is None),
                        )
                        for n in old.CHANNELS
                    ],
                )
            )
        )
        a = capture["attempts"].get(
            row["id"], dict(execution="not_run", bundle_hash=None, job_hash=None, result_hash=None)
        )
        result = validated[row["id"]][-1] if row["id"] in validated else None
        quantities = (
            dict(result.counts.model_dump(mode="json"), duration_s=result.duration_ps / 1e12)
            if result
            else dict.fromkeys(old.CHANNELS)
        )
        physical_channels = [
            old.channel(
                n,
                quantities[n],
                ref[n],
                result.result_hash if result else a.get("failure_hash"),
                ("/duration_ps" if n == "duration_s" else "/counts/" + n) if result else "/error",
                reference_state=values[n]["state"],
                execution=a["execution"],
                physical=bool(result),
            )
            for n in old.CHANNELS
        ]
        if a.get("error"):
            for ch in physical_channels:
                ch["reason"] = "Captured execution failure: " + cast(str, a["error"])
        physical_rows.append(
            ComparisonFixture.model_validate(
                dict(
                    common,
                    execution=a["execution"],
                    outcome="unassessed",
                    bundle_hash=a["bundle_hash"],
                    job_hash=a["job_hash"],
                    result_hash=a["result_hash"],
                    candidate_input_hash=None,
                    candidate_output_hash=None,
                    channels=physical_channels,
                )
            )
        )
    inventory_data = old.put(
        store,
        dict(
            format="uarch-reference-inventory/1",
            classification="synthetic_reference" if synthetic else "adopted_oracle",
            fixtures=invrows,
            oracle_manifest_sha256=audit["manifest_sha256"],
            reference_model=reference,
            refusal_inventory_source=pointer,
            refusals=[e.model_dump(mode="json") for e in expected],
        ),
        "inventory_hash",
    )
    inv = ReferenceInventory.model_validate(inventory_data)
    comparisons = {}
    limits = (
        "Explicit synthetic reference premises; not oracle execution or adoption."
        if synthetic
        else (
            "Separately recorded human-adopted reference; "
            "computation compatibility is not model accuracy."
        ),
        (
            "864 retained physical inputs unavailable; attempts remain not_run. "
            "H1 capacity failures retained."
        ),
        "No real L3/L4 or energy eligibility; unknown reference channels remain unassessed.",
    )
    for key, track, model, fixtures in [
        ("nominal", "nominal_compatibility", nominal_candidate.candidate_identity(), nominal_rows),
        ("physical", "physical_discrepancy", physical_assumptions().model, physical_rows),
    ]:
        c = assemble_comparison(
            candidate=model,
            inventory=inv,
            fixtures=tuple(fixtures),
            observations=observations,
            track=track,
            classification="synthetic_presentation" if synthetic else "executed_comparison",
            limitations=limits,
            artifacts=store,
        )
        store[c.comparison_hash] = c.model_dump(mode="json")
        comparisons[key] = c
    return dict(
        nominal=comparisons["nominal"],
        physical=comparisons["physical"],
        inventory=inv,
        artifacts=store,
        inputs=inputs,
        original_rows=rows,
        physical_capture=capture,
        validated_physical=validated,
        nominal_errors=errors,
        physical_errors=[
            dict(fixture_id=k, reason=a["error"])
            for k, a in capture["attempts"].items()
            if a["execution"] != "executed"
        ],
        limitations=list(limits),
        synthetic=synthetic,
    )


def report_package(run: ConsumerRun, *, captured: CapturedWork | None = None) -> TablePackage:
    """Full comparison coverage; a real H1 table supplies the report's hardware context."""
    validated = run["validated_physical"]
    if captured is None:
        bundle = next(
            v[0]
            for v in validated.values()
            if v[0].intent.model.name == "llama-3.1-8b" and v[0].intent.tp == 1
        )
        entries = [v for v in validated.values() if v[0].bundle_hash == bundle.bundle_hash]
        by_point = {v[3].point.payload_hash: v for v in entries}
        ordered = [by_point[p.payload_hash] for p in bundle.points]
        c = CapturedWork(
            bundle,
            ordered[0][1],
            ordered[0][2],
            derive_rk_params(bundle.hardware_spec),
            tuple(v[3] for v in ordered),
            tuple(v[4] for v in ordered),
        )
    else:
        c = captured
    recipes = {}
    for b, assumptions, _, job, result in validated.values():
        for pointer, selectors in computation_sources(job, b).items():
            if pointer not in (
                "/duration_ps",
                *("/counts/" + n for n in old.CHANNELS if n != "duration_s"),
            ):
                continue
            recipes[(result.result_hash, pointer)] = dict(
                artifact_hash=result.result_hash,
                model_identity_hash=content_hash(job.engine.model),
                recipe=dict(
                    metric_path=pointer,
                    purpose="duration" if pointer == "/duration_ps" else "counts",
                    granularity="whole_iteration",
                    applicable_dimensions=[
                        "model_identity",
                        "precision",
                        "initial_state",
                        "frequency_ratio",
                        "kv_block_size_tokens",
                    ],
                    selectors=[s.model_dump(mode="json") for s in selectors]
                    + [
                        dict(
                            kind="model_evidence",
                            artifact_hash=assumptions.assumptions_hash,
                            json_pointer="/model",
                        )
                    ],
                ),
            )
    return old.report_package(c, dict(run, comparison_source_recipes=recipes), run["inputs"])


def save_comparisons(run: ConsumerRun, destination: Path) -> None:
    """Preserve raw closure and actual captures before potentially costly report validation."""
    destination.mkdir(parents=True, exist_ok=False)
    closure = destination / "comparison-artifacts"
    closure.mkdir()
    for identity, value in sorted(run["artifacts"].items()):
        (closure / (identity[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else vr.canonical(value)
        )
    for name, value in (
        ("nominal", run["nominal"]),
        ("physical", run["physical"]),
        ("inventory", run["inventory"]),
    ):
        (destination / (name + ".json")).write_bytes(vr.canonical(value.model_dump(mode="json")))
    (destination / "physical-capture.json").write_bytes(vr.canonical(run["physical_capture"]))
    (destination / "observations.json").write_bytes(
        vr.canonical(
            dict(
                synthetic=run["synthetic"],
                nominal_gate=run["nominal"].gate_outcome,
                physical_gate=run["physical"].gate_outcome,
                nominal_errors=run["nominal_errors"],
                physical_errors=run["physical_errors"],
                limitations=run["limitations"],
            )
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="strict raw audit, never adoption")
    inspect.add_argument("root", type=Path)
    for mode in ("synthetic", "adopted"):
        consume = commands.add_parser(mode)
        if mode == "synthetic":
            consume.add_argument("root", type=Path)
        else:
            consume.add_argument("--adoption-review", type=Path, required=True)
            consume.add_argument("--review-sha256", required=True)
        consume.add_argument("--output", type=Path, required=True)
        consume.add_argument("--physical-replay", type=Path)
        consume.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.command == "inspect":
        print(json.dumps(audit_candidate(args.root), sort_keys=True))
        return
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("OutputConflict: absent consumer destination required")
    replay = strict_json_loads(args.physical_replay.read_bytes()) if args.physical_replay else None
    if args.command == "synthetic":
        run = consume_synthetic(args.root, physical_replay=replay)
    else:
        run = consume_adopted(
            adoption_review=args.adoption_review,
            review_sha256=args.review_sha256,
            physical_replay=replay,
        )
    save_comparisons(run, args.output)
    if args.report:
        from rkuarch.report.complete import write_report
        from rkuarch.table.build import write_table

        package = report_package(run)
        path = args.output / "table.json"
        write_table(package, path)
        write_report(path, allow_synthetic_presentation=run["synthetic"])
    print(
        json.dumps(
            dict(
                nominal_gate=run["nominal"].gate_outcome,
                physical_gate=run["physical"].gate_outcome,
                synthetic=run["synthetic"],
            )
        )
    )
    # A positive nominal gate never hides unresolved physical inputs or becomes B-F16.
    if run["nominal"].gate_outcome != "compatibility_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
