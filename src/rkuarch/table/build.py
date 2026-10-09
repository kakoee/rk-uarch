"""Physical table construction and portable serialization; review/evidence policy is external."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, NamedTuple

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.derivation import Derivation
from uarch_contract.evidence import EvidencePrecision, EvidenceScopeCase
from uarch_contract.hardware import sourced_leaves
from uarch_contract.hashing import (
    artifact_identity,
    canonical_json,
    content_hash,
    execution_hash,
    strict_json_loads,
)
from uarch_contract.model_card import CoefficientFamily, ModelCard
from uarch_contract.prepared import PreparedBundle
from uarch_contract.report_context import (
    DependencySelector,
    MetricRecipe,
    ReportContext,
    SourceMetricRecipe,
)
from uarch_contract.request import CharacterizationRequest
from uarch_contract.table import UarchCostTable

from rkuarch import ENGINE_VERSION
from rkuarch.engines.analytic.core import metric_contributors
from rkuarch.engines.protocol import EngineJob, EngineResult, validate_engine_result
from rkuarch.hw.derive import derive_rk_params
from rkuarch.workload.characterize import capacity_summary
from rkuarch.workload.deviations import unmeasured_errors
from rkuarch.workload.prepared import (
    execute_prepared_point,
    prepare_engine_job,
    validate_execution_bundle,
)

from .artifacts import verify_report_inputs
from .time_units import ps_to_seconds


class CapturedWork(NamedTuple):
    bundle: PreparedBundle
    assumptions: AssumptionSet
    request: CharacterizationRequest
    derivation: Derivation
    jobs: tuple[EngineJob, ...]
    results: tuple[EngineResult, ...]


class TablePackage(NamedTuple):
    table: UarchCostTable
    artifacts: Mapping[str, Any]


def capture(
    bundle: PreparedBundle,
    *,
    assumptions: AssumptionSet,
    workers: int = 1,
    subprocess_engine: bool = False,
) -> CapturedWork:
    """Execute authoritative points in bundle order. Only single-worker execution is supported."""
    if type(workers) is not int or workers != 1:
        raise ValueError("UnsupportedWorkers: analytic capture supports workers=1")
    bundle = validate_execution_bundle(bundle)
    pairs = []
    for point in bundle.points:
        if subprocess_engine:
            job = prepare_engine_job(bundle, point.payload_hash, assumptions=assumptions)
            completed = subprocess.run(
                [sys.executable, "-B", "-m", "rkuarch.engines.analytic"],
                input=canonical_json(job).encode() + b"\n",
                capture_output=True,
                check=False,
            )
            if completed.returncode:
                raise ValueError("EngineError: " + completed.stderr.decode(errors="replace"))
            result = validate_engine_result(strict_json_loads(completed.stdout), job)
            pairs.append((job, result))
        else:
            pairs.append(
                execute_prepared_point(bundle, point.payload_hash, assumptions=assumptions)
            )
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


def computation_sources(
    job: EngineJob, bundle: PreparedBundle
) -> dict[str, tuple[DependencySelector, ...]]:
    """Numeric result source paths including every critical-path attribution component."""
    sources = metric_contributors(job, bundle)
    for name in ("compute", "memory", "noc", "sync", "overhead"):
        sources["/attribution_ps/" + name] = sources["/duration_ps"]
    return sources


def table_recipes(
    captured: CapturedWork, *, generic_rows: bool = False
) -> tuple[tuple[MetricRecipe, ...], tuple[SourceMetricRecipe, ...]]:
    """Capture raw declarations for external review, without manufacturing ReviewRecords.

    Generic row recipes enumerate exact sources for ALL rows; no implicit wildcard source.
    B keeps each source's model/purpose/granularity/dimensions when resolving these unions.
    """
    render: dict[str, MetricRecipe] = {}
    sources = []
    for ri, (job, result) in enumerate(zip(captured.jobs, captured.results, strict=True)):
        for pointer, selectors in computation_sources(job, captured.bundle).items():
            purpose: Literal["counts", "duration"] = (
                "counts" if "/counts/" in pointer or pointer.endswith("/instances") else "duration"
            )
            dims: tuple[str, ...] = (
                "model_identity",
                "precision",
                "initial_state",
                "frequency_ratio",
                "kv_block_size_tokens",
            )
            if pointer.startswith("/per_op/"):
                dims += ("op_class", "array_fill", "intensity_regime")
            source = MetricRecipe(
                metric_path=pointer,
                purpose=purpose,
                granularity="operator" if pointer.startswith("/per_op/") else "whole_iteration",
                applicable_dimensions=dims,
                selectors=selectors
                + (
                    DependencySelector(
                        kind="model_evidence",
                        artifact_hash=job.assumptions_hash,
                        json_pointer="/model",
                    ),
                ),
            )
            sources.append(
                SourceMetricRecipe(
                    artifact_hash=result.result_hash,
                    model_identity_hash=content_hash(job.engine.model),
                    recipe=source,
                )
            )
            target = (
                pointer.replace("/per_op/", "/op_results/")
                if pointer.startswith("/per_op/")
                else pointer.replace("_ps", "_s")
            )
            path = "/rows/" + ("*" if generic_rows else str(ri)) + target
            exact = DependencySelector(
                kind="result_field", artifact_hash=result.result_hash, json_pointer=pointer
            )
            if path in render:
                old = render[path]
                render[path] = old.model_copy(update={"selectors": old.selectors + (exact,)})
            else:
                render[path] = MetricRecipe(
                    metric_path=path,
                    purpose=purpose,
                    granularity=source.granularity,
                    applicable_dimensions=dims,
                    selectors=(exact,),
                )
    return tuple(render.values()), tuple(sources)


def source_scopes(
    captured: CapturedWork, *, family: str
) -> dict[tuple[str, str], tuple[EvidenceScopeCase, ...]]:
    """Captured scope fields, NOT evidence applicability or mapping correspondence proof.

    Whole-iteration sources retain every executed operator scope. Unknown mapping/load
    stays null. Family is supplied from B's reviewed registry, never inferred here.
    """
    scopes = {}
    for job, result in zip(captured.jobs, captured.results, strict=True):
        cases = tuple(
            EvidenceScopeCase(
                family=family,
                hardware_spec_hash=captured.request.hardware_spec_hash,
                prepared_bundle_hash=captured.bundle.bundle_hash,
                model_identity_hash=content_hash(job.engine.model),
                frequency_ratio=job.point.frequency_ratio,
                initial_state=job.initial_state,
                kv_block_size_tokens=captured.request.kv_layout.block_size_tokens,
                mapping_correspondence_hash=None,
                **op.scope.model_dump(mode="json", exclude={"precision_roles"}),
                precision=EvidencePrecision.model_validate(
                    op.scope.precision_roles.model_dump(mode="json")
                ),
            )
            for op in result.per_op
        )
        for pointer in computation_sources(job, captured.bundle):
            scopes[(result.result_hash, pointer)] = (
                (cases[int(pointer.split("/")[2])],) if pointer.startswith("/per_op/") else cases
            )
    return scopes


def consumed_energy_families(captured: CapturedWork) -> tuple[CoefficientFamily, ...]:
    """This analytic model consumes no energy coefficients; static power is unrepresented too."""
    if any("energy" not in result.unrepresented for result in captured.results):
        raise ValueError("UnsupportedEnergyModel: missing captured omission")
    return ()


def captured_artifacts(captured: CapturedWork) -> dict[str, Any]:
    values = (
        captured.bundle,
        captured.assumptions,
        captured.request,
        captured.derivation,
        *captured.jobs,
        *captured.results,
    )
    return {artifact_identity(v.model_dump(mode="json")): v.model_dump(mode="json") for v in values}


def build_table(
    captured: CapturedWork,
    *,
    context: ReportContext,
    model_card: ModelCard,
    artifacts: Mapping[str, Any],
) -> TablePackage:
    """Join externally supplied reviewed context/card with actual captured computations.

    No review, evidence, comparison or badge is invented. Missing external closure refuses.
    """
    c = captured
    b = c.bundle
    req = c.request
    if context.used_energy_families != consumed_energy_families(c):
        raise ValueError("ReportContextMismatch: consumed energy families")
    store = dict(artifacts)
    for key, value in captured_artifacts(c).items():
        if key in store and store[key] != value:
            raise ValueError("ArtifactHashMismatch: captured collision")
        store[key] = value
    store[context.context_hash] = context.model_dump(mode="json")
    store[content_hash(model_card)] = model_card.model_dump(mode="json")
    rows = []
    warnings: list[str] = []
    for job, result in zip(c.jobs, c.results, strict=True):
        point = job.point
        row = dict(
            **point.query.model_dump(mode="json"),
            frequency_ratio=point.frequency_ratio,
            duration_s=ps_to_seconds(result.duration_ps),
            u_c0_duration_s=ps_to_seconds(result.u_c0_duration_ps),
            attribution_s={
                k: ps_to_seconds(v) for k, v in result.attribution_ps.model_dump().items()
            },
            counts=result.counts,
            ext_counts=dict(sram_read_bytes=None, sram_write_bytes=None, noc_flit_hop_count=None),
            peak_resident_bytes=dict(hbm=None, sram=None),
            diagnostics=result.diagnostics,
            analytic_mode=job.mode,
            op_results=result.per_op,
            point_hash=point.payload_hash,
            result_hash=result.result_hash,
            state_model=job.state_model,
        )
        rows.append(row)
        warnings.extend(point.graph.omissions)
        warnings.extend(capacity_summary(b, point).warnings)
        warnings.extend(
            "Unrepresented hardware/model input: " + path for path in result.unrepresented
        )
    value = dict(
        contract="uarch-contract/0.2",
        uarch_version=ENGINE_VERSION,
        hardware_spec_hash=req.hardware_spec_hash,
        request_hash=content_hash(req),
        intent_hash=b.intent_hash,
        execution_hash=execution_hash(
            content_hash(req), tuple(j.job_hash for j in c.jobs), c.jobs[0].engine, ENGINE_VERSION
        ),
        table_hash="sha256:" + "0" * 64,
        tp=req.tp,
        initial_state=req.initial_state,
        kv_layout=req.kv_layout,
        rows=rows,
        interpolation=dict(decode="none", prefill="none", outside_grid="refuse"),
        measured_error=unmeasured_errors(),
        composite_fidelity=req.uarch_fidelity.conservative_composite(),
        fidelity_detail=req.uarch_fidelity,
        provenance=dict(
            params=[dict(name=p.name, value=p.value) for p in c.derivation.parameters],
            model_card=dict(
                model_card.model_dump(mode="json", exclude={"model_id", "verification"}),
                hash=content_hash(model_card),
            ),
            conditional_on=[
                dict(path=p, value=v)
                for p, v in sourced_leaves(b.hardware_spec)
                if v.kind == "stipulation"
            ],
        ),
        warnings=tuple(dict.fromkeys(warnings)),
        preparation=b.producer,
        report_context_version="uarch-report-context/2",
        comparison_state="attempted" if context.comparison_hashes else "not_attempted",
        artifacts=dict(
            comparison_hashes=context.comparison_hashes,
            derivation_hash=c.derivation.derivation_hash,
            hardware_spec_hash=req.hardware_spec_hash,
            model_card_hash=content_hash(model_card),
            prepared_bundle_hash=b.bundle_hash,
            report_context_hash=context.context_hash,
        ),
    )
    table = UarchCostTable.model_validate(value)
    table = table.model_copy(update={"table_hash": content_hash(table, exclude=("table_hash",))})
    verified = verify_report_inputs(table, store)
    return TablePackage(table, MappingProxyType(dict(verified.artifacts)))


def write_table(package: TablePackage, path: Path) -> None:
    """Validate fully before writing deterministic hash-named companions and table bytes.

    Existing differing files refuse; unchanged files are preserved. No adopted artifact paths.
    """
    verify_report_inputs(package.table, package.artifacts)
    path = Path(path)
    directory = path.parent / "artifacts"
    outputs = {
        directory / (h[7:] + ".json"): v
        if isinstance(v, bytes)
        else canonical_json(v).encode() + b"\n"
        for h, v in package.artifacts.items()
        if h != package.table.table_hash
    }
    outputs[path] = canonical_json(package.table).encode() + b"\n"
    for dest, data in outputs.items():
        if dest.exists() and dest.read_bytes() != data:
            raise ValueError(f"OutputConflict: {dest}")
    for dest, data in outputs.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(data)
