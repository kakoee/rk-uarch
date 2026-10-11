"""Offline captured-record closure. No engine execution, preparation or evidence promotion."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple

from pydantic import BaseModel
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.comparison import ComparisonArtifact, ReferenceInventory, validate_comparison
from uarch_contract.derivation import Derivation
from uarch_contract.errors import (
    ArtifactHashMismatch,
    ArtifactMissing,
    IncompleteMetricContributors,
)
from uarch_contract.evidence import (
    EvidenceRecord,
    OrderingRecord,
    ReviewRecord,
    SourceRecord,
    VerificationRecord,
)
from uarch_contract.exports import ComponentExport, ExecutionModelInput, ExportBinding
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.hashing import (
    artifact_identity,
    content_hash,
    resolve_artifact,
    sha256,
    strict_json_loads,
    verify_declared_artifact_closure,
    verify_identity,
    verify_review,
)
from uarch_contract.model_card import ModelCard
from uarch_contract.prepared import PreparedBundle
from uarch_contract.registry import FamilyRegistry
from uarch_contract.report_context import (
    DependencySelector,
    MetricDependencies,
    ReportContext,
    validate_metric_dependencies,
    validate_report_context,
)
from uarch_contract.request import CharacterizationRequest
from uarch_contract.table import MOE_OMISSION, Parameter, UarchCostTable, validate_table_bindings

from rkuarch.engines.analytic.core import metric_contributors
from rkuarch.engines.protocol import (
    EngineJob,
    EngineResult,
    validate_engine_job,
    validate_engine_result,
)
from rkuarch.hw.derive import derive_rk_params, resolve_hardware
from rkuarch.hw.export import export_component, project_for_oracle
from rkuarch.workload.prepared import ALGORITHMS, validate_execution_bundle


class VerifiedReportInputs(NamedTuple):
    """Public Python return aggregate of accepted carriers, not a new wire schema.

    Verification here supplies file identity, computation inputs and captured-record joins.
    It grants no evidence eligibility, numeric-display permission or accuracy claim.
    """

    table: UarchCostTable
    bundle: PreparedBundle
    request: CharacterizationRequest
    hardware: HardwareSpec
    derivation: Derivation
    assumptions: AssumptionSet
    model_card: ModelCard
    jobs: tuple[EngineJob, ...]
    results: tuple[EngineResult, ...]
    context: ReportContext
    registry: FamilyRegistry
    dependencies: MetricDependencies
    comparisons: tuple[ComparisonArtifact, ...]
    evidence: tuple[EvidenceRecord, ...]
    sources: tuple[SourceRecord, ...]
    reviews: tuple[ReviewRecord, ...]
    orderings: tuple[OrderingRecord, ...]
    verifications: tuple[VerificationRecord, ...]
    artifacts: Mapping[str, Any]
    terminal_contributors: Mapping[str, tuple[DependencySelector, ...]]


class _Files(Mapping[str, Any]):
    """Lazy, exact hash-name lookup; no globbing, URL resolution or filename heuristics."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.loaded: dict[str, Any] = {}

    def path(self, identity: str) -> Path:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", identity):
            raise ArtifactHashMismatch(f"ArtifactHashMismatch: invalid identity {identity!r}")
        return self.directory / (identity[7:] + ".json")

    def raw(self, identity: str) -> bytes:
        path = self.path(identity)
        try:
            data = path.read_bytes()
        except FileNotFoundError as exc:
            raise ArtifactMissing(f"ArtifactMissing: {identity}") from exc
        if sha256(data) != identity:
            raise ArtifactHashMismatch(f"ArtifactHashMismatch: bytes {identity}")
        self.loaded[identity] = data
        return data

    def __getitem__(self, identity: str) -> Any:
        if identity in self.loaded:
            return self.loaded[identity]
        path = self.path(identity)
        try:
            data = path.read_bytes()
        except FileNotFoundError as exc:
            raise ArtifactMissing(f"ArtifactMissing: {identity}") from exc
        value = strict_json_loads(data)
        if not isinstance(value, dict) or artifact_identity(value) != identity:
            raise ArtifactHashMismatch(f"ArtifactHashMismatch: {identity}")
        self.loaded[identity] = value
        resolve_artifact(identity, self.loaded)
        if value.get("format") == "uarch-prepared/1":
            bundle = validate_execution_bundle(value)
            self.loaded[bundle.intent.hardware_spec_hash] = bundle.hardware_spec.model_dump(
                mode="json"
            )
        if value.get("format") == "uarch-reference-source/1":
            self.raw(value["raw_blob_sha256"])
        return value

    def __contains__(self, identity: object) -> bool:
        if not isinstance(identity, str):
            return False
        self[identity]  # Preserve explicit ArtifactMissing, not silent fallback.
        return True

    def __iter__(self) -> Iterator[str]:
        return iter(self.loaded)

    def __len__(self) -> int:
        return len(self.loaded)


_TYPES: dict[str, type[BaseModel]] = {
    "uarch-assumptions/1": AssumptionSet,
    "uarch-evidence/1": EvidenceRecord,
    "uarch-reference-source/1": SourceRecord,
    "uarch-evidence-review/1": ReviewRecord,
    "uarch-ordering/1": OrderingRecord,
    "uarch-verification/1": VerificationRecord,
    "uarch-family-registry/1": FamilyRegistry,
    "uarch-metric-dependencies/1": MetricDependencies,
    "uarch-report-context/2": ReportContext,
    "uarch-comparison/1": ComparisonArtifact,
    "uarch-reference-inventory/1": ReferenceInventory,
    "uarch-component-truth/1": ComponentExport,
    "uarch-export-binding/1": ExportBinding,
    "uarch-execution-model/1": ExecutionModelInput,
    "uarch-derivation/1": Derivation,
}


def _complete_closure(root: str, files: _Files) -> None:
    closed = set(verify_declared_artifact_closure(root, files))
    checked: set[str] = set()
    while pending := set(files.loaded) - checked:
        for identity in sorted(pending):
            value = files[identity]
            checked.add(identity)
            if not isinstance(value, dict):
                continue
            fmt = value.get("format")
            if "model_id" in value and "verification" in value:
                card = ModelCard.model_validate(value)
                identities = [h for h in card.verification.model_dump().values() if h is not None]
                if card.energy_verification is not None:
                    identities += [
                        h
                        for records in card.energy_verification.model_dump().values()
                        for h in records.values()
                        if h is not None
                    ]
                for child in identities:
                    VerificationRecord.model_validate(files[child])
                    closed.update(verify_declared_artifact_closure(child, files))
            if fmt in _TYPES:
                _TYPES[fmt].model_validate(value)
            if "review_hash" in value and fmt != "uarch-evidence-review/1":
                verify_review(value, files)
            if fmt == "uarch-reference-inventory/1":
                files.raw(value["oracle_manifest_sha256"])
                for fixture in value["fixtures"]:
                    verify_declared_artifact_closure(fixture["component_binding_hash"], files)
            if fmt == "uarch-export-binding/1":
                raw = files.raw(value["projected_descriptor_bytes_sha256"])
                descriptor = strict_json_loads(raw)
                if content_hash(descriptor) != value["projected_descriptor_content_hash"]:
                    raise ArtifactHashMismatch("ArtifactHashMismatch: descriptor content/bytes")
                files.loaded[value["projected_descriptor_content_hash"]] = descriptor
                truth = ComponentExport.model_validate(files[value["primary_export_hash"]])
                execution = ExecutionModelInput.model_validate(files[value["execution_model_hash"]])
                spec = HardwareSpec.model_validate(files[value["hardware_spec_hash"]])
                expected, derivation = export_component(
                    spec, execution, component_id=truth.component_id
                )
                if truth != expected or derivation.derivation_hash != value["derivation_hash"]:
                    raise ValueError("ParamsMismatch: bound export/derivation")
                expected_bytes, expected_binding = project_for_oracle(
                    spec, truth, derivation, execution, upstream_sha=value["upstream_sha"]
                )
                binding = ExportBinding.model_validate(value)
                if (
                    strict_json_loads(expected_bytes) != descriptor
                    or binding.losses != expected_binding.losses
                    or binding.supported_kv_storage != expected_binding.supported_kv_storage
                    or binding.component_id != truth.component_id
                    or binding.design_status != truth.design_status
                ):
                    raise ValueError("ComponentBindingMismatch: projection recipe/losses")
                params = {p.name: p.value for p in truth.params}
                if (
                    set(descriptor["params"]) != set(params)
                    or descriptor["id"] != truth.component_id
                ):
                    raise ValueError("ComponentBindingMismatch: descriptor")
                for name, original in params.items():
                    if descriptor["params"][name]["value"] != original.value:
                        raise ValueError("ParamsMismatch: projected value")
            if fmt == "uarch-upstream-component/1":
                files.raw(value["component_bytes_sha256"])
                files.raw(value["oracle_manifest_sha256"])
            if fmt == "uarch-nominal-input/1":
                verify_identity(value["execution_model"], "execution_model_hash")
                verify_declared_artifact_closure(value["component_binding_hash"], files)
            if fmt == "uarch-nominal-output/1":
                candidate_input = files[value["input_hash"]]
                if value["model_identity"] != candidate_input["model_identity"]:
                    raise ValueError("ModelIdentityMismatch: nominal input/output")
            if value.get("protocol") == "uarch-engine/1":
                if "result_hash" in value:
                    validate_engine_result(value, files[value["job_hash"]])
                else:
                    b = validate_execution_bundle(files[value["bundle_hash"]])
                    request = CharacterizationRequest(
                        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
                    )
                    job = validate_engine_job(value, b, request)
                    if job.hardware != resolve_hardware(
                        b.hardware_spec, job.precision, frequency_ratio=job.point.frequency_ratio
                    ):
                        raise ValueError("EngineJobMismatch: captured comparison hardware")
            if fmt == "uarch-comparison/1":
                validate_comparison(value, files[value["reference_inventory_hash"]], files)
            # Newly reached companions may have their own reviewed/transitive children.
            if identity not in closed:
                closed.update(verify_declared_artifact_closure(identity, files))


def _selector_key(s: DependencySelector) -> tuple[str, str, str]:
    return s.kind, s.artifact_hash, s.json_pointer


def _verify_computation_sources(
    table: UarchCostTable,
    bundle: PreparedBundle,
    jobs: tuple[EngineJob, ...],
    results: tuple[EngineResult, ...],
    deps: MetricDependencies,
    files: _Files,
    terminals: dict[str, tuple[DependencySelector, ...]],
) -> None:
    sources = {(s.artifact_hash, s.recipe.metric_path): s for s in deps.source_recipes}
    for i, (job, result) in enumerate(zip(jobs, results, strict=True)):
        requirements = metric_contributors(job, bundle)
        for pointer, required in requirements.items():
            key = (result.result_hash, pointer)
            if key not in sources:
                raise IncompleteMetricContributors(f"IncompleteMetricContributors: {key}")
            source = sources[key]
            if source.model_identity_hash != content_hash(job.engine.model):
                raise IncompleteMetricContributors("IncompleteMetricContributors: actual model")

            # Expand using the existing verifier so independent purpose/model/scope survive.
            def expand(selectors: tuple[DependencySelector, ...]) -> list[DependencySelector]:
                leaves = []
                for selector in selectors:
                    if selector.kind == "result_field":
                        child = sources[(selector.artifact_hash, selector.json_pointer)]
                        leaves.extend(expand(child.recipe.selectors))
                    else:
                        leaves.append(selector)
                return leaves

            # Full shared validation above already checked cycles, review and each source model.
            present = {_selector_key(s) for s in expand(source.recipe.selectors)}
            if not {_selector_key(s) for s in required} <= present:
                raise IncompleteMetricContributors(f"IncompleteMetricContributors: required {key}")
            output_pointer = (
                pointer.replace("/per_op/", "/op_results/")
                if pointer.startswith("/per_op/")
                else pointer.replace("_ps", "_s")
            )
            expected_granularity = (
                "operator" if pointer.startswith("/per_op/") else "whole_iteration"
            )
            if source.recipe.granularity != expected_granularity:
                raise IncompleteMetricContributors(
                    "IncompleteMetricContributors: source granularity"
                )
            target = f"/rows/{i}" + output_pointer
            generic = "/rows/*" + output_pointer
            recipes = [r for r in deps.recipes if r.metric_path in (target, generic)]
            if len(recipes) != 1:
                raise IncompleteMetricContributors(f"IncompleteMetricContributors: {target}")
            # Render target must select the exact result channel, not an equal-valued substitute.
            if not any(
                s.kind == "result_field" and (s.artifact_hash, s.json_pointer) == key
                for s in recipes[0].selectors
            ):
                raise IncompleteMetricContributors(f"IncompleteMetricContributors: source {target}")
            if not {_selector_key(s) for s in required} <= {
                _selector_key(s) for s in terminals[recipes[0].metric_path]
            }:
                raise IncompleteMetricContributors(
                    f"IncompleteMetricContributors: closure {target}"
                )


def load_verified_report_inputs(
    table_path: Path, *, artifact_dir: Path | None = None
) -> VerifiedReportInputs:
    """Load only local <sha256 hex>.json companions (raw source bytes use that same name).

    Embedded hardware and reconstructed request are indexed by their verified content hashes.
    The returned source recipes retain granularity, purpose, model and dimensions; terminal
    unions never replace them. B owns evidence eligibility and all display permissions.
    """
    table_path = Path(table_path)
    table = UarchCostTable.model_validate(strict_json_loads(table_path.read_bytes()))
    verify_identity(table, "table_hash")
    files = _Files(
        Path(artifact_dir) if artifact_dir is not None else table_path.parent / "artifacts"
    )
    return _load_verified(table, files)


def verify_report_inputs(
    table: UarchCostTable, artifacts: Mapping[str, Any]
) -> VerifiedReportInputs:
    """Same captured-record checks in memory; no filesystem fallback or writes."""

    class MemoryFiles(_Files):
        def __getitem__(self, identity: str) -> Any:
            if identity not in self.loaded:
                raise ArtifactMissing(f"ArtifactMissing: {identity}")
            value = self.loaded[identity]
            return value

        def raw(self, identity: str) -> bytes:
            value = self[identity]
            if not isinstance(value, bytes) or sha256(value) != identity:
                raise ArtifactHashMismatch(f"ArtifactHashMismatch: bytes {identity}")
            return value

    files = MemoryFiles(Path("."))
    for identity, value in artifacts.items():
        files.path(identity)  # Validate every output name, including unused companions.
        if isinstance(value, bytes):
            if sha256(value) != identity:
                raise ArtifactHashMismatch(f"ArtifactHashMismatch: bytes {identity}")
        else:
            resolve_artifact(identity, artifacts)
        files.loaded[identity] = value
    table = UarchCostTable.model_validate(table)
    verify_identity(table, "table_hash")
    return _load_verified(table, files, memory=True)


def _load_verified(
    table: UarchCostTable, files: _Files, *, memory: bool = False
) -> VerifiedReportInputs:
    files.loaded[table.table_hash] = table.model_dump(mode="json")
    bundle = validate_execution_bundle(files[table.artifacts.prepared_bundle_hash])
    files.loaded[bundle.intent.hardware_spec_hash] = bundle.hardware_spec.model_dump(mode="json")
    request = CharacterizationRequest(
        **bundle.intent.model_dump(mode="json"), prepared_input_hash=bundle.bundle_hash
    )
    # Request is reconstructed per accepted packaging. An explicit companion, if supplied,
    # must still verify; it cannot override captured intent.
    if (table.request_hash in files.loaded) if memory else files.path(table.request_hash).exists():
        if files[table.request_hash] != request.model_dump(mode="json"):
            raise ValueError("TableBindingMismatch: request companion")
    files.loaded[table.request_hash] = request.model_dump(mode="json")
    from rkuarch.provenance.reference_contributors import validate_reference_contributors

    declared_context = ReportContext.model_validate(files[table.artifacts.report_context_hash])
    declared_dependencies = MetricDependencies.model_validate(
        files[declared_context.metric_dependencies_hash]
    )
    declared_comparisons = tuple(
        ComparisonArtifact.model_validate(files[h]) for h in declared_context.comparison_hashes
    )
    validate_reference_contributors(
        declared_dependencies,
        tuple(c.reference_inventory_hash for c in declared_comparisons),
        files,
        read_raw=files.raw,
    )
    _complete_closure(table.table_hash, files)
    table = validate_table_bindings(table, files)
    hardware = bundle.hardware_spec
    derivation = Derivation.model_validate(files[table.artifacts.derivation_hash])
    if derivation != derive_rk_params(hardware) or table.provenance.params != tuple(
        Parameter(name=p.name, value=p.value) for p in derivation.parameters
    ):
        raise ValueError("ParamsMismatch: table/source derivation")
    conditions = {p: v for p, v in sourced_leaves(hardware) if v.kind == "stipulation"}
    actual_conditions = {c.path: c.value for c in table.provenance.conditional_on}
    if (
        len(actual_conditions) != len(table.provenance.conditional_on)
        or actual_conditions != conditions
    ):
        raise ValueError("ConditionMismatch: exact all-spec stipulations")
    card = ModelCard.model_validate(files[table.artifacts.model_card_hash])
    summary = table.provenance.model_card.model_dump(mode="json")
    expected_summary = card.model_dump(mode="json", exclude={"model_id", "verification"})
    if summary != dict(expected_summary, hash=content_hash(card)):
        raise ValueError("ModelCardMismatch: embedded summary")
    assumptions = AssumptionSet.model_validate(files[request.assumptions_hash])
    if assumptions.algorithms != ALGORITHMS:
        raise ValueError("AssumptionMismatch: captured resolved-ops/1 algorithms")
    jobs, results = [], []
    for row in table.rows:
        result = EngineResult.model_validate(files[row.result_hash])
        job = validate_engine_job(files[result.job_hash], bundle, request)
        validate_engine_result(result, job)
        if job.hardware != resolve_hardware(
            hardware, request.precision, frequency_ratio=job.point.frequency_ratio
        ):
            raise ValueError("EngineJobMismatch: sourced hardware projection")
        if (
            job.engine.model != assumptions.model
            or card.model_id.engine != job.engine.name
            or card.model_id.engine_version != job.engine.version
            or card.model_id.fidelity_detail != job.fidelity_detail
            or card.model_id.mapping_policy != request.mapping_policy
        ):
            raise ValueError("ModelCardMismatch: job/request/model identity")
        if row.diagnostics != result.diagnostics or any(
            v is not None for v in row.peak_resident_bytes.values()
        ):
            raise ValueError("TableBindingMismatch: diagnostics/partial peak residency")
        jobs.append(job)
        results.append(result)
    if request.model.n_experts and MOE_OMISSION not in table.warnings:
        raise ValueError("InvalidPreparedGraph: table MOE_OMISSION")
    context = validate_report_context(files[table.artifacts.report_context_hash], files)
    if (
        context.request_hash != table.request_hash
        or context.assumptions_hash != request.assumptions_hash
        or context.model_identity != assumptions.model
        or context.comparison_hashes != table.artifacts.comparison_hashes
    ):
        raise ValueError("ReportContextMismatch: request/assumptions/model/comparisons")
    for identity in card.verification.model_dump().values():
        if identity is not None:
            verify_declared_artifact_closure(identity, files)
            VerificationRecord.model_validate(files[identity])
            if identity not in context.verification_hashes:
                raise ValueError("ModelCardMismatch: verification index")
    if card.energy_verification is not None:
        for family_records in card.energy_verification.model_dump().values():
            for identity in family_records.values():
                if identity is not None:
                    verify_declared_artifact_closure(identity, files)
    if any(e not in context.evidence_index for e in card.evidence):
        raise ValueError("ModelCardMismatch: evidence index")
    for eid, identity in context.evidence_index.items():
        if EvidenceRecord.model_validate(files[identity]).evidence_id != eid:
            raise ValueError("ReportContextMismatch: evidence ID")
    registry = FamilyRegistry.model_validate(files[context.family_registry_hash])
    if sum(e.hardware_spec_hash == table.hardware_spec_hash for e in registry.entries) != 1:
        raise ValueError("AmbiguousFamily: current hardware")
    from rkuarch.provenance.model_card import validate_production_model_card
    from rkuarch.table.build import CapturedWork

    validate_production_model_card(
        card,
        captured=CapturedWork(
            bundle, assumptions, request, derivation, tuple(jobs), tuple(results)
        ),
        context=context,
        artifacts=files,
    )
    dependencies = MetricDependencies.model_validate(files[context.metric_dependencies_hash])
    terminal = validate_metric_dependencies(dependencies, files)
    _verify_computation_sources(
        table, bundle, tuple(jobs), tuple(results), dependencies, files, terminal
    )
    comparisons = tuple(
        ComparisonArtifact.model_validate(files[h]) for h in context.comparison_hashes
    )

    def records(kind: type[Any], fmt: str) -> tuple[Any, ...]:
        return tuple(
            kind.model_validate(v)
            for _, v in sorted(files.loaded.items())
            if isinstance(v, dict) and v.get("format") == fmt
        )

    return VerifiedReportInputs(
        table,
        bundle,
        request,
        hardware,
        derivation,
        assumptions,
        card,
        tuple(jobs),
        tuple(results),
        context,
        registry,
        dependencies,
        comparisons,
        records(EvidenceRecord, "uarch-evidence/1"),
        records(SourceRecord, "uarch-reference-source/1"),
        records(ReviewRecord, "uarch-evidence-review/1"),
        records(OrderingRecord, "uarch-ordering/1"),
        records(VerificationRecord, "uarch-verification/1"),
        MappingProxyType(dict(files.loaded)),
        MappingProxyType(terminal),
    )
