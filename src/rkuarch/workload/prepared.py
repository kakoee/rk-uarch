"""Strict captured-work validation and execution; never imports a preparation producer."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from uarch_contract.assumptions import AssumptionSet
from uarch_contract.hashing import content_hash, strict_json_loads, verify_identity
from uarch_contract.prepared import PreparedBundle, validate_prepared_bundle
from uarch_contract.request import CharacterizationRequest
from uarch_contract.table import MOE_OMISSION

from rkuarch.engines.analytic import core
from rkuarch.engines.protocol import EngineJob, EngineResult, validate_engine_job
from rkuarch.hw.derive import resolve_hardware, validate_storage

ALGORITHMS = {
    "activation": "silu-5md-plus-gate/1",
    "compute_overlap": "serialize-matrix-vector/1",
    "embedding": "supplied-conserved-hit-vector/1",
    "kv": "valid-tokens-context-includes-append/1",
    "normalization": "rms-6md/1",
    "residency": "partial-weight-kv-checks-total-peak-unknown/1",
    "softmax": "scalar-5pairs/1",
    "traffic": "once-per-operand-no-retention/1",
    "vector_rate": "cores-times-ops-per-cycle-times-resolved-core-hz/1",
}


def physical_assumptions() -> AssumptionSet:
    result = AssumptionSet(
        format="uarch-assumptions/1",
        assumptions_hash="sha256:" + "0" * 64,
        model=core.engine_identity().model,
        algorithms=ALGORITHMS,
        limitations=(
            "Abstract vector operation rate is unvalidated for transcendental algorithms.",
            "No independent full-workload physical timing validation.",
        ),
    )
    return result.model_copy(
        update={"assumptions_hash": content_hash(result, exclude=("assumptions_hash",))}
    )


def validate_execution_bundle(value: object) -> PreparedBundle:
    """Validate global logical extents and the supplied physical graph without remapping."""
    b = validate_prepared_bundle(value)
    intent = b.intent
    if intent.mapping_policy != "analytic-ops@1":
        raise ValueError("UnsupportedMappingScope: analytic execution requires analytic-ops@1")
    detail = intent.uarch_fidelity
    if (b.hardware_spec.shared_sram is not None) != (detail.shared_sram is not None):
        raise ValueError("UnsupportedFidelity: shared SRAM presence/detail")
    if (
        detail.compute != 0
        or detail.noc != 0
        or detail.dram != 0
        or detail.shared_sram not in (None, "unrepresented")
        or detail.sync != "exact"
    ):
        raise ValueError("UnsupportedFidelity: analytic execution scope")
    model, shape, tp = intent.model, intent.model_shape, intent.tp
    d, h = model.d_model, model.head_dim
    q_width, kv_width, ff = d // tp, max(1, model.kv_heads // tp) * h, shape.d_ff // tp
    vocab = (shape.vocab_size + tp - 1) // tp
    if shape.vocab_size <= b.rank.rank_index * vocab:
        raise ValueError(
            "UnsupportedRankScope: empty logical vocabulary shard cannot be represented "
            "by accepted positive Padding.logical; no fabricated logical slot"
        )
    equivalent = tuple(
        r
        for r in range(tp)
        if all(p.embedding_hits[r] == p.embedding_hits[b.rank.rank_index] for p in b.points)
    )
    if b.rank.equivalent_ranks != equivalent:
        raise ValueError("UnsupportedRankScope: exact equivalent ranks across every point")
    for point in b.points:
        resolve_hardware(b.hardware_spec, intent.precision, frequency_ratio=point.frequency_ratio)
        query = point.query
        if query.phase == "decode":
            tokens, batch, seq, context = (
                query.batch,
                query.batch,
                1,
                query.total_context_tokens // query.batch,
            )
        else:
            tokens = query.n_prompts * query.prompt_tokens
            batch, seq, context = query.n_prompts, query.prompt_tokens, query.prompt_tokens
        if model.n_experts and MOE_OMISSION not in point.graph.omissions:
            raise ValueError("InvalidPreparedGraph: MOE_OMISSION")
        group_kinds = Counter(g.kind for g in point.graph.groups)
        if group_kinds["head"] != 1 or group_kinds["tail"] != 1:
            raise ValueError("InvalidPreparedGraph: exact head/tail coverage")
        ancestors: dict[str, set[str]] = {}
        for group in point.graph.groups:
            ancestors[group.id] = set(group.depends_on)
            for parent in group.depends_on:
                ancestors[group.id].update(ancestors[parent])
            previous = {g.id for g in point.graph.groups[: len(ancestors) - 1]}
            if group.kind != "head" and not previous <= ancestors[group.id]:
                raise ValueError("InvalidPreparedGraph: group completion dependency")
            if (group.kind == "head") != (len(ancestors) == 1):
                raise ValueError("InvalidPreparedGraph: head order")
            if group.kind == "tail" and len(ancestors) != len(point.graph.groups):
                raise ValueError("InvalidPreparedGraph: tail order")
            names = Counter(str(op.spec.operator) for op in group.ops)
            if group.kind == "head":
                expected = Counter(embedding=1)
            elif group.kind == "tail":
                expected = Counter(normalization=1, lm_head=1)
            else:
                expected = Counter(
                    normalization=2,
                    residual_addition=2,
                    q_projection=1,
                    k_projection=1,
                    v_projection=1,
                    output_projection=1,
                    ffn_up=1,
                    ffn_down=1,
                    activation=1,
                    kv_write=1,
                )
                if shape.gated_mlp:
                    expected["ffn_gate"] = 1
                if names["attention_fused"]:
                    expected["attention_fused"] = 1
                else:
                    expected.update(qk_score=1, softmax=1, av_application=1)
            if names != expected:
                raise ValueError(f"InvalidPreparedGraph: {group.id}/operator coverage")
            by_name = {str(op.spec.operator): op for op in group.ops}
            for op in group.ops:
                name = str(op.spec.operator)
                dims = op.spec.dimensions
                if name in ("q_projection", "k_projection", "v_projection", "ffn_up", "ffn_gate"):
                    n = {
                        "q_projection": q_width,
                        "k_projection": kv_width,
                        "v_projection": kv_width,
                        "ffn_up": ff,
                        "ffn_gate": ff,
                    }[name]
                    logical = dict(M=tokens, K=d, N=n)
                elif name in ("output_projection", "ffn_down"):
                    logical = dict(M=tokens, K=q_width if name == "output_projection" else ff, N=d)
                elif name == "lm_head":
                    logical = dict(M=point.graph.lm_head_tokens, K=d, N=vocab)
                elif name == "embedding":
                    logical = dict(M=tokens, V=vocab, D=d)
                elif name in ("normalization", "residual_addition", "activation"):
                    logical = dict(M=tokens, D=ff if name == "activation" else d)
                elif name == "kv_write":
                    logical = dict(B=batch, Hkv=max(1, model.kv_heads // tp), S=seq, D=h)
                else:
                    logical = dict(
                        B=batch,
                        Hq=model.n_heads // tp,
                        Hkv=max(1, model.kv_heads // tp),
                        S=seq,
                        T=context,
                        D=h,
                    )
                pads = {p.dimension: p for p in op.padding}
                if set(pads) - logical.keys():
                    raise ValueError("InvalidPreparedGraph: unknown padding dimension")
                for axis, pad in pads.items():
                    expected_logical = logical[axis]
                    if name in ("embedding", "lm_head") and axis in ("V", "N"):
                        expected_logical = min(
                            vocab, max(1, shape.vocab_size - b.rank.rank_index * vocab)
                        )
                    if pad.logical != expected_logical or pad.physical != dims.get(axis):
                        raise ValueError(
                            "InvalidPreparedGraph: padding logical/physical correspondence"
                        )
                if name in ("embedding", "lm_head") and shape.vocab_size % tp:
                    if ("V" if name == "embedding" else "N") not in pads:
                        raise ValueError("InvalidPreparedGraph: missing vocabulary padding")
                expected_reps = []
                if model.kv_heads < tp and name in (
                    "k_projection",
                    "v_projection",
                    "kv_write",
                    "attention_fused",
                    "qk_score",
                    "av_application",
                ):
                    axis = "N" if name in ("k_projection", "v_projection") else "Hkv"
                    scale = h if axis == "N" else 1
                    expected_reps = [
                        dict(
                            dimension=axis,
                            global_extent=model.kv_heads * scale,
                            rank_extent=scale,
                            replicas=tp // model.kv_heads,
                        )
                    ]
                if [r.model_dump() for r in op.replication] != expected_reps:
                    raise ValueError("UnsupportedRankScope: exact KV replication declarations")
                if len(pads) != len(op.padding):
                    raise ValueError("InvalidPreparedGraph: duplicate padding")
                for axis, extent in dims.items():
                    if axis not in logical:
                        raise ValueError(f"InvalidPreparedGraph: {op.id}/unknown dimension {axis}")
                    if extent != logical[axis] and not (
                        axis in pads
                        and pads[axis].logical == logical[axis]
                        and pads[axis].physical == extent
                    ):
                        raise ValueError(f"InvalidPreparedGraph: {op.id}/dimensions/{axis}")
                if name == "activation" and ("G" in op.spec.operands) != shape.gated_mlp:
                    raise ValueError("InvalidPreparedGraph: activation gating")
                for key, operand in op.spec.operands.items():
                    validate_storage(b.hardware_spec, operand.dtype)
                    is_kv = (
                        name in ("attention_fused", "qk_score", "av_application")
                        and key in ("K", "V")
                    ) or key in ("K_cache", "V_cache")
                    target = intent.precision.kv_cache if is_kv else intent.precision.compute
                    paged = is_kv
                    if (operand.layout == "paged") != paged:
                        raise ValueError(f"KvLayoutMismatch: {op.id}/{key} layout")
                    if operand.dtype != target:
                        raise ValueError(f"UnsupportedPrecision: {op.id}/{key} role")
                if (
                    name in ("attention_fused", "qk_score", "av_application")
                    and op.kv_access is None
                ):
                    raise ValueError("KvLayoutMismatch: missing KV access")
                if name == "attention_fused":
                    required = {by_name[n].id for n in ("q_projection", "kv_write")}
                    if not required <= set(op.depends_on):
                        raise ValueError(
                            "InvalidPreparedGraph: attention must depend on Q/KV append"
                        )
            if group.kind == "decoder":
                widths = [
                    by_name["ffn_up"].spec.dimensions["N"],
                    by_name["activation"].spec.dimensions["D"],
                    by_name["ffn_down"].spec.dimensions["K"],
                ]
                if shape.gated_mlp:
                    widths.append(by_name["ffn_gate"].spec.dimensions["N"])
                if len(set(widths)) != 1:
                    raise ValueError("InvalidPreparedGraph: FFN physical correspondence")
                attention = by_name["attention_fused" if names["attention_fused"] else "qk_score"]
                ad = attention.spec.dimensions
                expected_widths = {
                    "q_projection": ad["Hq"] * ad["D"],
                    "k_projection": ad["Hkv"] * ad["D"],
                    "v_projection": ad["Hkv"] * ad["D"],
                }
                if any(by_name[n].spec.dimensions["N"] != w for n, w in expected_widths.items()):
                    raise ValueError("InvalidPreparedGraph: Q/K/V physical correspondence")
                if by_name["output_projection"].spec.dimensions["K"] != ad["Hq"] * ad["D"]:
                    raise ValueError(
                        "InvalidPreparedGraph: attention/output physical correspondence"
                    )
                append = by_name["kv_write"].spec.dimensions
                if any(append[a] != ad[a] for a in ("B", "Hkv", "S", "D")):
                    raise ValueError("InvalidPreparedGraph: KV append physical correspondence")
            if group.kind == "decoder" and not names["attention_fused"]:
                score, soft, av = (by_name[n] for n in ("qk_score", "softmax", "av_application"))
                if (
                    score.id not in soft.depends_on
                    or soft.id not in av.depends_on
                    or not {by_name["q_projection"].id, by_name["kv_write"].id}
                    <= set(score.depends_on)
                    or by_name["kv_write"].id not in av.depends_on
                ):
                    raise ValueError("InvalidPreparedGraph: unfused attention correspondence")
                if (
                    score.spec.operands["scores"] != soft.spec.operands["scores"]
                    or soft.spec.operands["probs"] != av.spec.operands["probs"]
                ):
                    raise ValueError("InvalidPreparedGraph: unfused intermediate correspondence")
                for key in ("B", "Hq", "S", "T"):
                    if len({o.spec.dimensions[key] for o in (score, soft, av)}) != 1:
                        raise ValueError("InvalidPreparedGraph: unfused score dimensions")
    from .characterize import capacity_summary

    for point in b.points:
        capacity_summary(b, point)
    return b


def load_prepared_input(path: Path) -> PreparedBundle:
    return validate_execution_bundle(strict_json_loads(Path(path).read_bytes()))


def prepare_engine_job(
    bundle: PreparedBundle, point_hash: str, *, assumptions: AssumptionSet
) -> EngineJob:
    """The shared table/adapter analytic boundary, bypassing all producer entry points."""
    b = validate_execution_bundle(bundle)
    verify_identity(assumptions, "assumptions_hash")
    if (
        assumptions.assumptions_hash != b.intent.assumptions_hash
        or assumptions.model != core.engine_identity().model
        or assumptions.algorithms != ALGORITHMS
    ):
        raise ValueError("AssumptionMismatch: resolved-ops/1 algorithms/model")
    matches = [p for p in b.points if p.payload_hash == point_hash]
    if len(matches) != 1:
        raise ValueError("MissingCoverage: exact prepared point")
    point = matches[0]
    request = CharacterizationRequest(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    job = EngineJob(
        protocol="uarch-engine/1",
        job_hash="sha256:" + "0" * 64,
        request_hash=content_hash(request),
        bundle_hash=b.bundle_hash,
        point_hash=point.payload_hash,
        producer=b.producer,
        engine=core.engine_identity(),
        point=point,
        rank=b.rank,
        hardware=resolve_hardware(
            b.hardware_spec, b.intent.precision, frequency_ratio=point.frequency_ratio
        ),
        precision=b.intent.precision,
        fidelity_detail=b.intent.uarch_fidelity,
        mode=b.intent.analytic_mode,
        accounting=b.intent.accounting,
        initial_state=point.initial_state,
        state_model="stateless_roofline",
        seed=b.intent.seed,
        assumptions_hash=assumptions.assumptions_hash,
    )
    job = job.model_copy(update={"job_hash": content_hash(job, exclude=("job_hash",))})
    validate_engine_job(job, b, request)
    return job


def execute_prepared_point(
    bundle: PreparedBundle, point_hash: str, *, assumptions: AssumptionSet
) -> tuple[EngineJob, EngineResult]:
    """Execute the validated captured job in process, without a producer import."""
    job = prepare_engine_job(bundle, point_hash, assumptions=assumptions)
    return job, core.run_analytic(job)
