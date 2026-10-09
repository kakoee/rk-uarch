"""B-owned test/diagnostic orchestration. Never an oracle or production nominal engine."""

from __future__ import annotations

import math
from contextlib import ExitStack
from typing import Any
from unittest.mock import patch

import yaml
from pydantic import TypeAdapter
from uarch_contract.comparison import (
    ReferenceInventory,
    reduce_outcomes,
    validate_channel,
    validate_comparison,
)
from uarch_contract.hashing import artifact_identity, content_hash, sha256
from uarch_contract.model_shape import ModelSpec
from uarch_contract.prepared import Query
from uarch_contract.sourced import SourcedValue

from contract.tests import nominal_candidate as nominal
from contract.tests.parity import projection_incompatibilities, rank_counts
from scripts import u2_inputs, vendor_rk

DIRECT_SOURCE = "40cd36ed696e378ade013b804554e668795fe45668410e963a8b978adc07ee32"
CHANNELS = ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes", "duration_s")
ZERO = "sha256:" + "0" * 64


def put(store: dict[str, Any], value: dict[str, Any], own: str | None = None) -> dict[str, Any]:
    if own:
        value[own] = content_hash(value, exclude=(own,))
    store[artifact_identity(value)] = value
    return value


def adopted_rows() -> list[dict[str, Any]]:
    import json

    return json.loads((u2_inputs.ADOPTED / "parity/fixtures.json").read_bytes())


def channel(
    name: str,
    actual: float | None,
    reference: float | None,
    source: str | None,
    pointer: str,
    *,
    reference_state: str | None = None,
    execution: str = "executed",
    nominal_omission: bool = False,
    physical: bool = False,
    deviations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ds = deviations or []
    signed = math.fsum(d["deviation_rel"] for d in ds)
    absolute = math.fsum(abs(d["deviation_rel"]) for d in ds)
    state = reference_state or (
        "null" if reference is None else "zero" if reference == 0 else "positive"
    )
    raw = residual = None
    produced = (
        "known"
        if actual is not None
        else "unmodelled"
        if execution == "executed"
        else "not_produced"
    )
    if execution != "executed":
        outcome = {
            "pre_call_refusal": "refused",
            "not_run": "unassessed",
            "execution_failed": "execution_failed",
        }[execution]
    elif reference is not None and actual is not None:
        if reference:
            raw = (actual - reference) / reference
            residual = raw - signed
            outcome = (
                "passed"
                if abs(residual) <= (0.001 if name == "duration_s" else 0.005)
                else "failed"
            )
        else:
            outcome = "passed" if actual == 0 else "failed"
    elif reference is None and actual is None and nominal_omission:
        outcome = "modelled_absence"
    else:
        outcome = "unassessed"
    result = dict(
        channel=name,
        unit="s" if name == "duration_s" else "op" if name.endswith("ops") else "byte",
        reference=dict(state=state, value=reference),
        actual=dict(
            state=produced,
            value=actual,
            source_hash=source,
            source_pointer=pointer if source else None,
            conversion="ps_to_seconds" if physical and name == "duration_s" else "identity",
        ),
        raw_rel=raw,
        residual_rel=residual,
        signed_adjustment_rel=signed,
        absolute_adjustment_rel=absolute,
        declared_deviations=ds,
        outcome=outcome,
        reason="No observed accuracy. "
        + (
            "Reference unavailable or deliberately unmodelled; evidence unassessed."
            if state in ("null", "absent")
            else "Accepted comparison policy applied to supplied source values."
        ),
    )
    validate_channel(result, execution=execution, declared_omission=nominal_omission)
    return result


def nominal_attempt(
    row: dict[str, Any], inputs: u2_inputs.Inputs, store: dict[str, Any]
) -> tuple[str, Any, Any, str | None]:
    reasons = projection_incompatibilities(row)
    if reasons:
        return "pre_call_refusal", None, None, "; ".join(reasons)
    entry = next(
        e
        for e in inputs.entries
        if "components/" + u2_inputs.role(e) == row["component_params_file"]
    )
    raw = inputs.descriptors[entry.component_id]
    sidecar = next(m for m in inputs.models if m["id"] == row["model_id"])
    if (
        row["rk_sha"] != vendor_rk.PIN
        or row["component_params_sha256"] != vendor_rk.digest(raw)
        or row["model"] != sidecar["model"]
        or row["model_shape"] != sidecar["shape"]
        or row["model_sources"] != sidecar["sources"]
        or row["precision"] not in inputs.matrix[u2_inputs.role(entry)]
    ):
        raise ValueError("candidate input component/model/precision/source join differs")
    descriptor = yaml.safe_load(raw)
    compute = row["precision"]["compute"]
    unit = "tops" if compute.startswith("int") else "tflops"

    def original(name: str) -> SourcedValue:
        if entry.binding.kind == "upstream_only":
            return SourcedValue.model_validate(
                dict(descriptor["params"][name], kind="claim", rationale=None)
            )
        truth = inputs.artifacts[entry.binding.primary_export_hash]
        return SourcedValue.model_validate(
            next(p["value"] for p in truth["params"] if p["name"] == name)
        )

    model = ModelSpec.model_validate(row["model"])
    query = TypeAdapter(Query).validate_python(
        {
            k: v
            for k, v in row["query"].items()
            if k not in ("total_prompt_tokens", "sum_of_squared_prompt_tokens")
        }
    )
    value = dict(
        format="uarch-nominal-input/1",
        component_binding_hash=entry.binding.binding_hash,
        model=model.model_dump(mode="json"),
        model_identity=nominal.candidate_identity().model_dump(mode="json"),
        precision=row["precision"],
        query=query.model_dump(mode="json"),
        tp=row["tp"],
        selected_peak=original(compute + "_" + unit).model_dump(mode="json"),
        bandwidth=original("hbm_bw").model_dump(mode="json"),
        execution_model=inputs.artifacts[entry.binding.execution_model_hash],
    )
    put(store, value, "input_hash")
    typed = nominal.NominalInput.model_validate(value)

    def denied(*a: Any, **kw: Any) -> Any:
        raise RuntimeError("candidate file access/network/process forbidden")

    try:
        with ExitStack() as stack:
            for name in (
                "builtins.open",
                "io.open",
                "pathlib.Path.read_bytes",
                "pathlib.Path.read_text",
                "socket.socket",
                "subprocess.Popen",
            ):
                stack.enter_context(patch(name, denied))
            output = nominal.evaluate_nominal(typed)
        store[output.output_hash] = output.model_dump(mode="json")
        return "executed", typed, output, None
    except Exception as exc:
        return "execution_failed", typed, None, type(exc).__name__ + ": " + str(exc)


def reference_model() -> dict[str, Any]:
    import json

    metadata = json.loads((u2_inputs.ADOPTED / "GENERATOR.json").read_bytes())
    return dict(
        name="nominal-rk-compatibility",
        version=vendor_rk.PIN,
        implementation_hash="sha256:" + metadata["oracle_program_sha256"],
    )


def precision_plan(
    inputs: u2_inputs.Inputs, store: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    expected = []
    observed = []
    for entry in inputs.entries:
        role = u2_inputs.role(entry)
        for fmt in (
            ("bf16", "fp8")
            if role == "asic_placeholder.yaml"
            else ("fp16", "fp8")
            if role == "npu-l4.yaml"
            else ()
        ):
            rid = role + "/" + fmt + "/" + fmt
            row = dict(
                component=role,
                compute=fmt,
                kv_cache=fmt,
                boundary="Accelerator.peak_op_per_s",
                error="UnsupportedPrecision",
            )
            rows.append(row)
            check = put(
                store,
                dict(
                    format="uarch-precision-check-input/1",
                    component_binding_hash=entry.binding.binding_hash,
                    component_role=role,
                    precision=dict(compute=fmt, kv_cache=fmt),
                    upstream_sha=vendor_rk.PIN,
                    callable_source_sha256="sha256:" + DIRECT_SOURCE,
                    requested_boundary=row["boundary"],
                    classification="reconstructed_input",
                    limitation=(
                        "Approved expectation only; new direct upstream execution awaits "
                        "reviewed human generation."
                    ),
                ),
                "input_hash",
            )
            expected.append(
                dict(
                    refusal_id=rid,
                    component_binding_hash=entry.binding.binding_hash,
                    precision=check["precision"],
                    boundary=row["boundary"],
                    error_class=row["error"],
                    check_input_hash=check["input_hash"],
                    source_entry_index=len(rows) - 1,
                )
            )
            observed.append(
                put(
                    store,
                    dict(
                        format="uarch-precision-refusal-observation/1",
                        refusal_id=rid,
                        check_input_hash=check["input_hash"],
                        trace_hash=None,
                        observed_boundary=None,
                        error_class=None,
                        execution="not_run",
                        match_result="not_run",
                        evidence_outcome="unassessed",
                        reason=(
                            "Pending new direct-peak human-run capture; historical events not "
                            "relabelled."
                        ),
                    ),
                    "observation_hash",
                )
            )
    plan = put(store, dict(expected_direct_refusals=rows))
    return (
        dict(artifact_hash=artifact_identity(plan), json_pointer="/expected_direct_refusals"),
        expected,
        observed,
    )


def run_historical(
    inputs: u2_inputs.Inputs, *, fixture_ids: tuple[str, ...] | None = None
) -> dict[str, Any]:
    """Complete selected historical inventory: nominal executed; physical never invented."""
    vendor_rk.check_manifest(u2_inputs.ADOPTED)
    vendor_rk.check_snapshot_inputs(u2_inputs.ADOPTED)
    if (
        vendor_rk.digest((u2_inputs.ADOPTED / "MANIFEST.json").read_bytes())
        != u2_inputs.ADOPTED_MANIFEST
    ):
        raise ValueError("historical adopted identity changed")
    try:
        vendor_rk.check_generator(u2_inputs.ADOPTED)
    except ValueError as exc:
        fingerprint = str(exc)
    else:
        fingerprint = None
    store = dict(inputs.artifacts)
    for entry in inputs.entries:
        store[entry.binding.binding_hash] = entry.binding.model_dump(mode="json")
    raw = (u2_inputs.ADOPTED / "MANIFEST.json").read_bytes()
    store[sha256(raw)] = raw
    rows = adopted_rows()
    if fixture_ids is not None:
        wanted = set(fixture_ids)
        if len(wanted) != len(fixture_ids) or not wanted <= {r["id"] for r in rows}:
            raise ValueError("unknown/duplicate requested fixture")
        rows = [r for r in rows if r["id"] in wanted]
    if not rows:
        raise ValueError("empty requested inventory")
    refmodel = reference_model()
    pointer, expected, observed = precision_plan(inputs, store)
    invrows = []
    nominal_rows = []
    physical_rows = []
    errors = []
    for row in rows:
        put(store, row)
        entry = next(
            e
            for e in inputs.entries
            if "components/" + u2_inputs.role(e) == row["component_params_file"]
        )
        scope = dict(
            global_kv_heads=row["model"]["kv_heads"],
            global_vocab=row["model_shape"]["vocab_size"],
            kv_replicated=row["model"]["kv_heads"] < row["tp"],
            padded_vocab=math.ceil(row["model_shape"]["vocab_size"] / row["tp"]) * row["tp"],
        )
        query = (
            TypeAdapter(Query)
            .validate_python(
                {
                    k: v
                    for k, v in row["query"].items()
                    if k not in ("total_prompt_tokens", "sum_of_squared_prompt_tokens")
                }
            )
            .model_dump(mode="json")
        )
        ref = dict(rank_counts(row), duration_s=row["duration_s"], vector_ops=None)
        common = dict(
            fixture_id=row["id"],
            component_binding_hash=entry.binding.binding_hash,
            query=query,
            precision=row["precision"],
            tp=row["tp"],
            projection_scope=scope,
        )
        invrows.append(
            dict(
                common,
                values={
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
                    for n in CHANNELS
                },
            )
        )
        execution, value, output, error = nominal_attempt(row, inputs, store)
        if error:
            errors.append(dict(fixture_id=row["id"], reason=error))
        quantities = (
            dict(output.counts.model_dump(mode="json"), duration_s=output.duration_s)
            if output
            else dict.fromkeys(CHANNELS)
        )
        channels = [
            channel(
                n,
                quantities[n],
                ref[n],
                output.output_hash if output else None,
                "/duration_s" if n == "duration_s" else "/counts/" + n,
                reference_state=invrows[-1]["values"][n]["state"],
                execution=execution,
                nominal_omission=bool(output and quantities[n] is None),
            )
            for n in CHANNELS
        ]
        nominal_rows.append(
            dict(
                common,
                channels=channels,
                execution=execution,
                outcome=reduce_outcomes(tuple(c["outcome"] for c in channels)),
                candidate_input_hash=value.input_hash if value else None,
                candidate_output_hash=output.output_hash if output else None,
                bundle_hash=None,
                job_hash=None,
                result_hash=None,
            )
        )
        channels = [
            channel(
                n,
                None,
                ref[n],
                None,
                "",
                reference_state=invrows[-1]["values"][n]["state"],
                execution="not_run",
                physical=True,
            )
            for n in CHANNELS
        ]
        physical_rows.append(
            dict(
                common,
                channels=channels,
                execution="not_run",
                outcome="unassessed",
                candidate_input_hash=None,
                candidate_output_hash=None,
                bundle_hash=None,
                job_hash=None,
                result_hash=None,
            )
        )
    inventory = put(
        store,
        dict(
            format="uarch-reference-inventory/1",
            classification="adopted_oracle",
            fixtures=invrows,
            oracle_manifest_sha256=sha256(raw),
            reference_model=refmodel,
            refusal_inventory_source=pointer,
            refusals=expected,
        ),
        "inventory_hash",
    )
    from rkuarch.workload.prepared import physical_assumptions

    comparisons = {}
    for track, fixtures, model in [
        (
            "nominal_compatibility",
            nominal_rows,
            nominal.candidate_identity().model_dump(mode="json"),
        ),
        (
            "physical_discrepancy",
            physical_rows,
            physical_assumptions().model.model_dump(mode="json"),
        ),
    ]:
        result = put(
            store,
            dict(
                format="uarch-comparison/1",
                classification="executed_comparison",
                candidate=model,
                reference_model=refmodel,
                reference_inventory_hash=inventory["inventory_hash"],
                track=track,
                reference_basis="nominal_aggregate_divided_by_tp"
                if track == "nominal_compatibility"
                else "physical_vs_nominal_rank_projection",
                fixtures=fixtures,
                precision_refusal_observations=observed,
                evidence_outcome=reduce_outcomes(
                    tuple(f["outcome"] for f in fixtures)
                    + tuple(o["evidence_outcome"] for o in observed),
                    artifact=True,
                ),
                gate_outcome="compatibility_fail"
                if track == "nominal_compatibility"
                else "not_assessed",
                limitations=[
                    (
                        "Historical adopted reference diagnostic only; current "
                        "fingerprint incompatible until reviewed refresh."
                    ),
                    "All four new direct checks not run; old refusal records remain historical.",
                    (
                        "Vector absent and decode writes null have unassessed evidence; "
                        "modelled_absence is not numerical agreement."
                    ),
                    (
                        "Physical retained-component execution unavailable: no approved "
                        "full HardwareSpec for retained upstream-only "
                        "components. No H1 substitution."
                    ),
                ],
            ),
            "comparison_hash",
        )
        comparisons[track] = validate_comparison(result, inventory, store)
    return dict(
        nominal=comparisons["nominal_compatibility"],
        physical=comparisons["physical_discrepancy"],
        artifacts=store,
        inventory=ReferenceInventory.model_validate(inventory),
        errors=errors,
        reference_manifest_sha256=u2_inputs.ADOPTED_MANIFEST,
        current_fingerprint_compatible=fingerprint is None,
        fingerprint_diagnostic=fingerprint,
    )


def prepare_h1(inputs: u2_inputs.Inputs, *, model_id: str, tp: int, compact: bool = False):
    """Actual A producer + guarded adapter, using accepted H1 and unchanged nominal sidecar."""
    from uarch_contract.hardware import HardwareSpec
    from uarch_contract.request import RequestIntent

    from rkuarch.workload.prepare import prepare
    from rkuarch.workload.prepared import physical_assumptions

    hardware = HardwareSpec.model_validate(
        yaml.safe_load((u2_inputs.ROOT / "hw/designs/npu-l4.yaml").read_bytes())
    )
    model = next(m for m in inputs.models if m["id"] == model_id)
    assumptions = physical_assumptions()
    grid = dict(
        decode=dict(
            batch=[1] if compact else [1, 8, 32],
            context_per_seq=[128] if compact else [128, 512, 4096, 16384],
        ),
        prefill=dict(
            n=[1] if compact else [1, 4, 16], L=[128] if compact else [128, 512, 2048, 4096]
        ),
        frequency_ratio=[1.0],
    )
    intent = RequestIntent.model_validate(
        dict(
            contract="uarch-contract/0.2",
            rk_schema_snapshot=vendor_rk.PIN,
            component_id=hardware.id,
            hardware_spec_hash=content_hash(hardware),
            model=model["model"],
            model_shape=model["shape"],
            precision=dict(compute="bf16", kv_cache="bf16"),
            tp=tp,
            grid=grid,
            envelope=dict(
                decode=dict(
                    batch_max=max(grid["decode"]["batch"]),
                    context_per_seq_max=max(grid["decode"]["context_per_seq"]),
                ),
                prefill=dict(
                    prompt_tokens_max=max(grid["prefill"]["L"]),
                    prompts_per_iteration_max=max(grid["prefill"]["n"]),
                ),
            ),
            mapping_policy="analytic-ops@1",
            uarch_fidelity=dict(compute=0, noc=0, dram=0, sync="exact", layer_reuse=True),
            initial_state="steady",
            kv_layout=dict(block_size_tokens=16),
            visit_weights=None,
            seed=0,
            accounting="resolved-ops/1",
            analytic_mode="per_op",
            assumptions_hash=assumptions.assumptions_hash,
            preparation_policy="balanced-tp/1",
        )
    )
    bundle = prepare(intent, hardware, synthetic_assignment=tp > 1)
    return bundle, assumptions


def physical_point(bundle, assumptions, point):
    from contract.tests.u2_prepared_adapter import evaluate_captured
    from rkuarch.workload.characterize import capacity_summary

    intent = bundle.intent
    capacity_summary(bundle, point)
    return evaluate_captured(
        bundle,
        model=intent.model,
        model_shape=intent.model_shape,
        query=point.query,
        precision=intent.precision,
        tp=intent.tp,
        component_id=intent.component_id,
        assumptions=assumptions,
    )


def capture_h1(inputs: u2_inputs.Inputs, *, model_id: str, tp: int, compact: bool = False):
    from uarch_contract.request import CharacterizationRequest

    from rkuarch.hw.derive import derive_rk_params
    from rkuarch.table.build import CapturedWork

    bundle, assumptions = prepare_h1(inputs, model_id=model_id, tp=tp, compact=compact)
    pairs = [physical_point(bundle, assumptions, point) for point in bundle.points]
    return CapturedWork(
        bundle,
        assumptions,
        CharacterizationRequest(
            **bundle.intent.model_dump(mode="json"), prepared_input_hash=bundle.bundle_hash
        ),
        derive_rk_params(bundle.hardware_spec),
        tuple(j for j, _ in pairs),
        tuple(r for _, r in pairs),
    )


def run_h1_matrix(inputs: u2_inputs.Inputs) -> dict[str, Any]:
    """All 144 H1 attempts, preserving each failure and earlier successful captures."""
    cases = []
    store = {}
    for model in inputs.models:
        for tp in (1, 8):
            bundle = assumptions = None
            try:
                bundle, assumptions = prepare_h1(inputs, model_id=model["id"], tp=tp)
                store[bundle.bundle_hash] = bundle.model_dump(mode="json")
                store[assumptions.assumptions_hash] = assumptions.model_dump(mode="json")
            except Exception as exc:
                preparation_error = type(exc).__name__ + ": " + str(exc)
            for index, q in enumerate(vendor_rk.QUERIES):
                case = dict(
                    fixture_id=f"{model['id']}/bf16/bf16/tp{tp}/npu-l4.yaml/{index}",
                    query=q,
                    reference="absent: no adopted H1 oracle row",
                    evidence="unassessed",
                    badge="stub",
                )
                if bundle is None:
                    case.update(
                        execution="execution_failed",
                        reason=preparation_error,
                        counts=None,
                        duration_s=None,
                    )
                else:
                    try:
                        point = bundle.points[index]
                        actual_query = point.query.model_dump(mode="json")
                        expected_query = (
                            TypeAdapter(Query)
                            .validate_python(
                                {
                                    k: v
                                    for k, v in q.items()
                                    if k
                                    not in ("total_prompt_tokens", "sum_of_squared_prompt_tokens")
                                }
                            )
                            .model_dump(mode="json")
                        )
                        if actual_query != expected_query:
                            raise ValueError("prepared point/requested query join differs")
                        job, result = physical_point(bundle, assumptions, point)
                        store[job.job_hash] = job.model_dump(mode="json")
                        store[result.result_hash] = result.model_dump(mode="json")
                        case.update(
                            execution="executed",
                            result_hash=result.result_hash,
                            job_hash=job.job_hash,
                            bundle_hash=bundle.bundle_hash,
                            counts=result.counts.model_dump(mode="json"),
                            duration_s=result.duration_ps / 1e12,
                        )
                    except Exception as exc:
                        case.update(
                            execution="execution_failed",
                            reason=type(exc).__name__ + ": " + str(exc),
                            counts=None,
                            duration_s=None,
                        )
                cases.append(case)
    assert len(cases) == 144
    return dict(
        cases=cases,
        artifacts=store,
        reference_coverage="pending refreshed oracle",
        synthetic_assignment=(
            "Explicit balanced embedding assignment for tp>1; computation, not measurement."
        ),
    )


def report_package(captured, run: dict[str, Any], inputs: u2_inputs.Inputs):
    """File-complete demonstration with explicit synthetic review scaffolding.

    Uses real captures/candidates and authentic historical blobs. It creates no accuracy
    evidence and cannot make a physical retained-component run or new oracle row exist.
    """
    from uarch_contract.hashing import review_subject_hash
    from uarch_contract.model_card import ModelCard
    from uarch_contract.report_context import ReportContext

    from rkuarch.table.build import build_table, captured_artifacts, table_recipes
    from rkuarch.workload.identity import legacy_model_id

    store = dict(run["artifacts"])
    store.update(captured_artifacts(captured))
    store[content_hash(captured.bundle.hardware_spec)] = captured.bundle.hardware_spec.model_dump(
        mode="json"
    )
    for entry in inputs.entries:
        raw = inputs.descriptors[entry.component_id]
        store[sha256(raw)] = raw
        descriptor = yaml.safe_load(raw)
        put(store, descriptor)
    render, sources = table_recipes(captured)
    recipes = [r.model_dump(mode="json") for r in render]
    source_recipes = {
        (s.artifact_hash, s.recipe.metric_path): s.model_dump(mode="json") for s in sources
    }
    comparisons = [run["nominal"], run["physical"]]
    original_rows = {
        r["id"]: r for r in (run["original_rows"] if "original_rows" in run else adopted_rows())
    }

    def selector(kind, identity, pointer):
        return dict(kind=kind, artifact_hash=identity, json_pointer=pointer)

    def source(identity, pointer, model, purpose, selectors):
        source_recipes[(identity, pointer)] = dict(
            artifact_hash=identity,
            model_identity_hash=content_hash(model),
            recipe=dict(
                metric_path=pointer,
                purpose=purpose,
                granularity="whole_iteration",
                applicable_dimensions=["model_identity", "precision"],
                selectors=selectors,
            ),
        )

    for ci, c in enumerate(comparisons):
        for fi, f in enumerate(c.fixtures):
            original = original_rows[f.fixture_id]
            original_hash = artifact_identity(original)
            binding = store[f.component_binding_hash]
            entry = next(
                e for e in inputs.entries if e.binding.binding_hash == f.component_binding_hash
            )
            descriptor = yaml.safe_load(inputs.descriptors[entry.component_id])
            dh = content_hash(descriptor)
            for ki, ch in enumerate(f.channels):
                purpose = "duration" if ch.channel == "duration_s" else "counts"
                rp = f"/fixtures/{fi}/values/{ch.channel}/value"
                rs = [
                    selector("prepared_content", original_hash, p)
                    for p in ("/model", "/model_shape", "/query", "/precision", "/tp")
                ]
                rs += [
                    selector("model_assumption", c.reference_inventory_hash, "/reference_model"),
                    selector("model_evidence", c.reference_inventory_hash, "/reference_model"),
                ]
                if purpose == "duration":
                    fmt = f.precision.compute.value
                    if binding["kind"] == "uarch_projection":
                        export_hash = binding["primary_export_hash"]
                        params = store[export_hash]["params"]
                        for name in (fmt + "_tflops", "hbm_bw"):
                            index = next(i for i, p in enumerate(params) if p["name"] == name)
                            rs.append(
                                selector("hardware_leaf", export_hash, f"/params/{index}/value")
                            )
                    else:
                        rs += [
                            selector("hardware_leaf", dh, "/params/" + fmt + "_tflops"),
                            selector("hardware_leaf", dh, "/params/hbm_bw"),
                        ]
                    rs.append(
                        selector("model_assumption", binding["execution_model_hash"], "/compute")
                    )
                source(c.reference_inventory_hash, rp, c.reference_model, purpose, rs)
                leaves = [selector("result_field", c.reference_inventory_hash, rp)]
                if ch.actual.state == "known":
                    if f.result_hash is not None:
                        physical_recipe = run["comparison_source_recipes"][
                            (ch.actual.source_hash, ch.actual.source_pointer)
                        ]
                        source_recipes[(ch.actual.source_hash, ch.actual.source_pointer)] = (
                            physical_recipe
                        )
                        leaves.append(
                            selector(
                                "result_field", ch.actual.source_hash, ch.actual.source_pointer
                            )
                        )
                        continue_actual = False
                    else:
                        continue_actual = True
                    ih = f.candidate_input_hash
                    if continue_actual:
                        assert ih is not None
                        actual = [
                            selector("prepared_content", ih, p)
                            for p in ("/model", "/query", "/precision", "/tp")
                        ]
                        actual += [
                            selector("model_assumption", ih, "/model_identity"),
                            selector("model_evidence", ih, "/model_identity"),
                        ]
                        if purpose == "duration":
                            actual += [
                                selector("hardware_leaf", ih, "/selected_peak"),
                                selector("hardware_leaf", ih, "/bandwidth"),
                                selector("model_assumption", ih, "/execution_model"),
                            ]
                        source(
                            ch.actual.source_hash,
                            ch.actual.source_pointer,
                            c.candidate,
                            purpose,
                            actual,
                        )
                        leaves.append(
                            selector(
                                "result_field", ch.actual.source_hash, ch.actual.source_pointer
                            )
                        )
                leaves.append(
                    selector(
                        "model_assumption",
                        c.comparison_hash,
                        f"/fixtures/{fi}/channels/{ki}/declared_deviations",
                    )
                )
                for name in (
                    "raw_rel",
                    "residual_rel",
                    "signed_adjustment_rel",
                    "absolute_adjustment_rel",
                ):
                    recipes.append(
                        dict(
                            metric_path=f"/comparisons/{ci}/fixtures/{fi}/channels/{ki}/{name}",
                            purpose=purpose,
                            granularity="whole_iteration",
                            applicable_dimensions=["model_identity", "precision"],
                            selectors=leaves,
                        )
                    )

    def reviewed(value, own):
        review = put(
            store,
            dict(
                format="uarch-evidence-review/1",
                reviewer="B synthetic packaging control",
                independent=True,
                decision="accepted",
                rationale=(
                    "Synthetic review scaffolding only; real captured computations "
                    "remain STUB. Not a human evidence approval."
                ),
                reviewed_subject_hashes=[review_subject_hash(value)],
            ),
            "review_hash",
        )
        value["review_hash"] = review["review_hash"]
        return put(store, value, own)

    deps = reviewed(
        dict(
            format="uarch-metric-dependencies/1",
            version="B-pre-freeze-demo/1",
            model_identity_hash=content_hash(captured.assumptions.model),
            recipes=recipes,
            source_recipes=list(source_recipes.values()),
        ),
        "dependencies_hash",
    )
    registry = reviewed(
        dict(
            format="uarch-family-registry/1",
            version="synthetic-H1-report-control/1",
            entries=[
                dict(family="proposed-H1", hardware_spec_hash=captured.request.hardware_spec_hash)
            ],
        ),
        "registry_hash",
    )
    context = put(
        store,
        dict(
            format="uarch-report-context/2",
            request_hash=content_hash(captured.request),
            assumptions_hash=captured.assumptions.assumptions_hash,
            model_identity=captured.assumptions.model.model_dump(mode="json"),
            metric_dependencies_hash=deps["dependencies_hash"],
            family_registry_hash=registry["registry_hash"],
            evidence_index={},
            verification_hashes=[],
            used_energy_families=[],
            comparison_hashes=[c.comparison_hash for c in comparisons],
            limitations=run.get(
                "limitations",
                [
                    (
                        "Synthetic administrative reviews only; no accuracy evidence or "
                        "real positive eligibility."
                    ),
                    (
                        "Historical oracle diagnostic; current fingerprint incompatible. "
                        "All new direct peak observations remain not_run."
                    ),
                    (
                        "H1 physical rows are actual captured computations; retained "
                        "component physical comparisons are not_run without "
                        "approved full hardware inputs."
                    ),
                    (
                        "No adopted H1 reference values. This selected demonstration is "
                        "not the complete refreshed matrix exit."
                    ),
                ],
            ),
        ),
        "context_hash",
    )
    card = ModelCard(
        model_id=legacy_model_id(captured.jobs[0], captured.bundle),
        badge="stub",
        evidence=(),
        verification={},
    )
    if "original_rows" in run:
        # Package only declared comparison/report closure, not unrelated attempts in
        # the orchestration workspace. A still performs every semantic/file check.
        from uarch_contract.hashing import verify_declared_artifact_closure

        keep = set(verify_declared_artifact_closure(context["context_hash"], store))
        keep.update(captured_artifacts(captured))
        keep.update(inputs.artifacts)
        keep.add(content_hash(captured.bundle.hardware_spec))
        keep.update(h for h, v in store.items() if isinstance(v, bytes))
        store = {h: store[h] for h in keep}
    return build_table(
        captured, context=ReportContext.model_validate(context), model_card=card, artifacts=store
    )
