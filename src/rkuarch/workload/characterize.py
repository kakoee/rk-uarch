"""Known allocation checks, never a claim about total activation peak or accuracy."""

from __future__ import annotations

import math
from typing import NamedTuple

from uarch_contract.hashing import content_hash
from uarch_contract.prepared import PreparedBundle, PreparedPoint

from rkuarch.hw.derive import FORMAT_BYTES


class CapacitySummary(NamedTuple):
    weight_bytes: int
    kv_bytes: int
    total_peak_bytes: None
    warnings: tuple[str, ...]


def capacity_summary(bundle: PreparedBundle, point: PreparedPoint) -> CapacitySummary:
    """Sum unique weights (all experts, replicated router, tied sharing) and paged KV.

    This consumes validated captured extents. Known weights must fit. KV plus weights
    overflowing is a warning; no activation lifetime model exists in this version.
    """
    if point not in bundle.points:
        raise ValueError("PointMismatch: capacity")
    weights = 0
    for group in point.graph.groups:
        for op in group.ops:
            if "W" not in op.spec.operands:
                continue
            if str(op.spec.operator) == "lm_head" and bundle.intent.model_shape.tie_embeddings:
                continue
            operand = op.spec.operands["W"]
            size = math.prod(op.spec.dimensions[a] for a in operand.dimensions)
            weights += (
                math.ceil(size * FORMAT_BYTES[operand.dtype]) * op.weight_copies * group.repeat
            )
    m = bundle.intent.model
    weights += (
        math.ceil(m.d_model * m.n_experts * FORMAT_BYTES[bundle.intent.precision.compute])
        * m.n_layers
    )
    q = point.query
    batch = q.batch if q.phase == "decode" else q.n_prompts
    context = q.total_context_tokens // q.batch if q.phase == "decode" else q.prompt_tokens
    block = bundle.intent.kv_layout.block_size_tokens
    # KV allocation includes physical head width/extents captured by each decoder group.
    kv_bytes = 0
    for group in point.graph.groups:
        if group.kind != "decoder":
            continue
        append = next(o for o in group.ops if str(o.spec.operator) == "kv_write")
        dims = append.spec.dimensions
        for key in ("K_cache", "V_cache"):
            kv_bytes += (
                math.ceil(
                    batch
                    * dims["Hkv"]
                    * dims["D"]
                    * ((context + block - 1) // block)
                    * block
                    * FORMAT_BYTES[append.spec.operands[key].dtype]
                )
                * group.repeat
            )
    capacity = bundle.hardware_spec.memory.dram.capacity_bytes.value
    if weights > capacity:
        raise ValueError(f"WeightCapacityExceeded: {weights} > {capacity}")
    warnings = ["Total activation peak is unmodelled; HBM/SRAM peak remains unknown."]
    if weights + kv_bytes > capacity:
        warnings.append(
            f"KV capacity exceeded: known weights {weights} + paged KV {kv_bytes} > {capacity}."
        )
    return CapacitySummary(weights, kv_bytes, None, tuple(warnings))


def characterize(bundle: PreparedBundle) -> dict[str, object]:
    """Raw physical capture for workload selection, not a rendered or validated report.

    Exact EngineResults preserve each operator's counts, times, op class, intensity and
    array-fill regime. Null mapping/load/peak fields remain explicit. No evidence decision.
    """
    from rkuarch.table.build import capture

    from .prepared import physical_assumptions

    c = capture(bundle, assumptions=physical_assumptions())
    return dict(
        prepared_bundle_hash=bundle.bundle_hash,
        request_hash=content_hash(c.request),
        jobs=[j.model_dump(mode="json") for j in c.jobs],
        results=[r.model_dump(mode="json") for r in c.results],
        capacity=[capacity_summary(bundle, p)._asdict() for p in bundle.points],
    )


def characterize_markdown(captured: dict[str, object]) -> str:
    """Deterministic workload-selection twin of characterize(), without rerunning computation.

    This presents counts and scope for selection; timing remains in raw JSON. It does not interpret
    evidence, assign badges, promote unknowns or implement B's table-report protocol.
    """
    import html
    from typing import Any

    from pydantic import TypeAdapter
    from uarch_contract.hashing import canonical_json, sha256

    from rkuarch.engines.protocol import EngineJob, EngineResult, validate_engine_result

    def cell(value: object) -> str:
        text = "unknown" if value is None else str(value)
        return (
            html.escape(text, quote=False)
            .replace("|", "&#124;")
            .replace("`", "&#96;")
            .replace("\n", "<br>")
        )

    def row(values: tuple[object, ...]) -> str:
        return "| " + " | ".join(cell(value) for value in values) + " |"

    def stub(value: object) -> str:
        return ("unknown" if value is None else str(value)) + " · STUB"

    jobs = TypeAdapter(tuple[EngineJob, ...]).validate_python(captured["jobs"])
    results = TypeAdapter(tuple[EngineResult, ...]).validate_python(captured["results"])
    capacities = TypeAdapter(tuple[dict[str, Any], ...]).validate_python(captured["capacity"])
    lines = [
        "# Workload selection — unvalidated physical predictions",
        "",
        "Raw analytic workload capture for benchmark selection; no evidence or accuracy claim.",
        "Counts, allocation estimates and intensity are STUB, unvalidated selection inputs.",
        "Computed timing estimates remain only in the raw JSON; no timing claim is shown here.",
        "Query and shape coordinates are declared inputs, not measurements.",
        "",
        f"JSON bytes SHA256: {sha256((canonical_json(captured) + chr(10)).encode())}",
        f"Prepared bundle: {cell(captured['prepared_bundle_hash'])}",
        f"Request: {cell(captured['request_hash'])}",
        "",
        "Energy: unverified. Total HBM/SRAM peak: unknown. No measured error experiments.",
        "",
    ]
    for index, (job, result, capacity) in enumerate(zip(jobs, results, capacities, strict=True)):
        validate_engine_result(result, job)
        if (
            job.bundle_hash != captured["prepared_bundle_hash"]
            or job.request_hash != captured["request_hash"]
        ):
            raise ValueError("CharacterizationBindingMismatch: job/bundle/request")
        query = canonical_json(job.point.query)
        lines += [
            f"## Grid point {index}: {job.point.query.phase}",
            "",
            f"Query: {cell(query)}",
            f"Frequency ratio: {job.point.frequency_ratio}; "
            f"state: {job.initial_state}; mode: {job.mode}.",
            f"Rank: {job.rank.rank_index}, tp={job.rank.tp}; "
            f"scope: {job.rank.kind}; collectives: excluded.",
            f"Equivalent ranks: {cell(job.rank.equivalent_ranks)}; "
            f"embedding hits: {cell(job.point.embedding_hits)}; "
            f"hit source: {job.point.hit_source}.",
            f"Attention mask: {job.point.graph.attention_mask}; "
            f"LM-head tokens: {job.point.graph.lm_head_tokens}.",
            f"Hardware spec: {job.hardware.hardware_spec_hash}",
            f"Point: {job.point_hash}",
            f"Job: {job.job_hash}",
            f"Result: {result.result_hash}",
            f"Producer: {cell(job.producer.name)} / {cell(job.producer.version)} / "
            f"{job.producer.implementation_hash}",
            f"Engine: {cell(job.engine.name)} / {cell(job.engine.version)} / "
            f"{job.engine.implementation_hash}",
            f"Model: {cell(job.engine.model.name)} / {cell(job.engine.model.version)} / "
            f"{job.engine.model.implementation_hash}",
            f"Assumptions: {job.assumptions_hash}",
            "",
            row(("Matrix ops", "Vector ops", "Read bytes", "Write bytes")),
            row(("---",) * 4),
            row(tuple(stub(value) for value in result.counts.model_dump().values())),
            "",
            f"Known weight bytes: {cell(stub(capacity['weight_bytes']))}; "
            f"paged KV bytes: {cell(stub(capacity['kv_bytes']))}; "
            f"total peak bytes: {cell(stub(capacity['total_peak_bytes']))}.",
            "",
            "### Per-op computation",
            "",
            row(
                (
                    "Op ID",
                    "Class",
                    "Instances",
                    "Matrix ops",
                    "Vector ops",
                    "Read bytes",
                    "Write bytes",
                    "Intensity ops/byte",
                    "Bound",
                )
            ),
            row(("---",) * 9),
        ]
        specs = {g.id + "/" + op.id: op.spec for g in job.point.graph.groups for op in g.ops}
        for op in result.per_op:
            lines.append(
                row(
                    (
                        op.id,
                        op.scope.op_class,
                        stub(op.instances),
                        *(stub(value) for value in op.counts.model_dump().values()),
                        stub(op.operational_intensity_ops_per_byte),
                        op.bound,
                    )
                )
            )
        lines += [
            "",
            "### Captured Shape and precision scope",
            "",
            row(
                (
                    "Op ID",
                    "Dimensions",
                    "Precision roles",
                    "Array fill",
                    "Intensity regime",
                    "Mapping match",
                    "NoC load",
                    "DRAM load",
                )
            ),
            row(("---",) * 8),
        ]
        for op in result.per_op:
            scope = op.scope
            lines.append(
                row(
                    (
                        op.id,
                        canonical_json(specs[op.id].dimensions),
                        canonical_json(scope.precision_roles),
                        stub(scope.array_fill),
                        scope.intensity_regime,
                        scope.mapping_match,
                        scope.noc_load_regime,
                        scope.dram_load_regime,
                    )
                )
            )
        lines += ["", "### Omissions and unknowns", ""]
        lines.extend(
            "- " + cell(text) + " · STUB (unvalidated capture)"
            for text in (*job.point.graph.omissions, *capacity["warnings"])
        )
        lines.extend("- Unrepresented: " + cell(path) for path in result.unrepresented)
        lines += [
            "- Diagnostics: " + cell(canonical_json(result.diagnostics)),
            "- Busy time: " + cell(canonical_json(result.busy_time_ps)),
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"
