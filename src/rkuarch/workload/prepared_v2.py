"""Strict U0022 admission of explicit v2 graphs, without preparation or migration."""

from __future__ import annotations

from collections import Counter
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from uarch_contract.assumptions import AssumptionSet, ModelIdentity
from uarch_contract.hashing import content_hash, strict_json_loads, verify_identity
from uarch_contract.prepared import DecodeQuery, PreparedOp, validate_prepared_op
from uarch_contract.rotary_v2 import CharacterizationRequestV3, PreparedBundleV2, PreparedOpV2
from uarch_contract.table import MOE_OMISSION

from rkuarch.hw.derive import resolve_hardware, validate_storage


def raw(value: object) -> object:
    # Reparse even frozen carrier instances: model_copy is deliberately unvalidated.
    return value.model_dump(mode="json") if isinstance(value, BaseModel) else value


def validate_op(op: PreparedOpV2) -> None:
    if str(op.spec.operator) != "rotary_embedding":
        if op.rotary is not None:
            raise ValueError("InvalidRotary: nonrotary binding")
        payload = op.model_dump(mode="json", exclude={"rotary"})
        old = PreparedOp.model_validate(payload)
        if set(op.operand_access) != set(op.spec.operands):
            raise ValueError("InvalidPreparedGraph: operand access keys")
        try:
            validate_prepared_op(old)
        except KeyError as exc:
            raise ValueError("InvalidPreparedGraph: missing operand/dimension") from exc
        return
    d = op.spec.dimensions
    if (
        set(d) != {"B", "H", "S", "D", "R", "P"}
        or d["R"] < 2
        or d["R"] % 2
        or d["R"] > d["D"]
        or d["P"] != d["R"] // 2
    ):
        raise ValueError("InvalidRotary: exact dimensions and even rotary extent")
    if (
        op.rotary is None
        or op.spec.reduction_axes
        or op.padding
        or op.fusion != "none"
        or op.kv_access is not None
        or op.embedding_local_tokens is not None
        or op.work_repeat != 1
        or op.weight_copies != 1
    ):
        raise ValueError("InvalidRotary: binding/reductions/padding/multiplicity")
    axes = dict(
        X=("B", "H", "S", "D"), Y=("B", "H", "S", "D"), Cos=("B", "S", "P"), Sin=("B", "S", "P")
    )
    if set(op.spec.operands) != set(axes) or op.operand_access != dict(
        X="read", Y="write", Cos="read", Sin="read"
    ):
        raise ValueError("InvalidRotary: operand/access keys")
    dtype = op.spec.operands["X"].dtype
    if dtype not in ("fp32", "bf16", "fp16"):
        raise ValueError("UnsupportedPrecision: rotary activation")
    for key, operand in op.spec.operands.items():
        if (
            operand.dimensions != axes[key]
            or operand.layout != "contiguous"
            or operand.block_size_tokens is not None
            or operand.dtype != (dtype if key in ("X", "Y") else "fp32")
        ):
            raise ValueError("InvalidRotary: operand axes/layout/precision")


def _validate_rotary_graph(b: PreparedBundleV2) -> None:
    intent, coefficients = b.intent, b.coefficients
    profile = intent.position_encoding
    dtype = intent.precision.compute
    if dtype not in ("fp32", "bf16", "fp16") or intent.precision.kv_cache != dtype:
        raise ValueError("UnsupportedPrecision: same-format rotary activation/KV required")
    if (
        profile.coefficients_hash != coefficients.coefficients_hash
        or profile.rotary_dim != coefficients.rotary_dim
    ):
        raise ValueError("CoefficientMismatch: intent/table")
    m, tp = intent.model, intent.tp
    for point in b.points:
        if point.graph.kv_key_encoding != profile:
            raise ValueError("CacheEncodingMismatch: graph/intent")
        q = point.query
        batch = q.batch if q.phase == "decode" else q.n_prompts
        seq = 1 if q.phase == "decode" else q.prompt_tokens
        context = q.total_context_tokens // batch if q.phase == "decode" else seq
        positions = tuple(
            (context - 1,) if q.phase == "decode" else tuple(range(seq)) for _ in range(batch)
        )
        if coefficients.position_count < context:
            raise ValueError("CoefficientMismatch: context row coverage")
        for group in point.graph.groups:
            ropes = [o for o in group.ops if str(o.spec.operator) == "rotary_embedding"]
            if group.kind != "decoder":
                if ropes:
                    raise ValueError("InvalidRotary: head/tail rotation")
                continue
            if len(ropes) != 2 or {o.id for o in ropes} != {"rope_q", "rope_k"}:
                raise ValueError("InvalidRotary: exactly rope_q and rope_k")
            by_name = {str(o.spec.operator): o for o in group.ops}
            for op in ropes:
                binding = op.rotary
                assert binding is not None  # validate_op runs first
                target = "q" if op.id == "rope_q" else "k"
                name = target + "_projection"
                if name not in by_name:
                    raise ValueError("InvalidRotary: missing projection")
                projection = by_name[name]
                heads = m.n_heads // tp if target == "q" else max(1, m.kv_heads // tp)
                expected = dict(
                    B=batch,
                    H=heads,
                    S=seq,
                    D=m.head_dim,
                    R=profile.rotary_dim,
                    P=profile.rotary_dim // 2,
                )
                if op.spec.dimensions != expected:
                    raise ValueError("InvalidRotary: resolved rank/query dimensions")
                if (
                    binding.target != target
                    or binding.input_op_id != projection.id
                    or op.depends_on != (projection.id,)
                    or binding.position_ids != positions
                    or binding.coefficients_hash != profile.coefficients_hash
                    or binding.pairing != profile.pairing
                    or binding.numeric_policy != profile.numeric_policy
                ):
                    raise ValueError("InvalidRotary: projection/position/profile binding")
                if (
                    projection.spec.dimensions.get("M") != batch * seq
                    or projection.spec.dimensions.get("N") != heads * m.head_dim
                    or projection.spec.operands["Y"].dtype != dtype
                ):
                    raise ValueError("InvalidRotary: projection logical element correspondence")
                expected_reps = []
                if target == "k" and m.kv_heads < tp:
                    expected_reps = [
                        dict(
                            dimension="H",
                            global_extent=m.kv_heads,
                            rank_extent=1,
                            replicas=tp // m.kv_heads,
                        )
                    ]
                if [r.model_dump() for r in op.replication] != expected_reps:
                    raise ValueError("UnsupportedRankScope: rotary replicated KV")
                for key, operand in op.spec.operands.items():
                    # FP32 table storage is fixed by U0022, independent of matrix formats.
                    if key in ("X", "Y") or operand.dtype in b.hardware_spec.formats:
                        validate_storage(b.hardware_spec, operand.dtype)
                    if key in ("X", "Y") and operand.dtype != dtype:
                        raise ValueError("UnsupportedPrecision: rotary role")
            if not {"kv_write", "v_projection"} <= by_name.keys():
                raise ValueError("InvalidRotary: missing cache/V producer")
            kv, v = by_name["kv_write"], by_name["v_projection"]
            if set(kv.depends_on) != {"rope_k", v.id}:
                raise ValueError("InvalidRotary: K/V append edges")
            source = by_name.get("attention_fused", by_name.get("qk_score"))
            if source is None or set(source.depends_on) != {"rope_q", "rope_k", v.id, kv.id}:
                raise ValueError("InvalidRotary: attention rotated/cache sources")
            if "attention_fused" not in by_name:
                if not {"softmax", "av_application"} <= by_name.keys():
                    raise ValueError("InvalidRotary: missing unfused work")
                soft, av = by_name["softmax"], by_name["av_application"]
                if set(soft.depends_on) != {source.id} or set(av.depends_on) != {soft.id, kv.id}:
                    raise ValueError("InvalidRotary: unfused intermediate/cache edges")


def _validate_structure(value: object) -> PreparedBundleV2:
    """Validate an imported bundle without calling a producer or changing resolved work."""

    from uarch_contract.comparison import _refuse
    from uarch_contract.hashing import content_hash, spec_hash, verify_identity
    from uarch_contract.table import DECLARED_OMISSIONS, MOE_OMISSION

    if isinstance(value, dict):
        if value.get("format") != "uarch-prepared/2":
            _refuse("UnsupportedPreparedVersion", "/format")
        if value.get("mapping_scope") != "analytic_ops":
            _refuse("UnsupportedMappingScope", "/mapping_scope")
    b = PreparedBundleV2.model_validate(raw(value))
    try:
        for point in b.points:
            verify_identity(point, "payload_hash")
        verify_identity(b, "bundle_hash")
        if content_hash(b.intent) != b.intent_hash:
            _refuse("ContentHashMismatch", "/intent_hash")
    except ValueError as exc:
        _refuse("ContentHashMismatch", str(exc))
    intent, rank = b.intent, b.rank
    if spec_hash(b.hardware_spec) != intent.hardware_spec_hash:
        _refuse("SpecHashMismatch", "/intent/hardware_spec_hash")
    formats = b.hardware_spec.formats
    if intent.precision.compute not in formats or intent.precision.kv_cache not in formats:
        _refuse("UnsupportedPrecision", "/intent/precision")
    if intent.precision.compute not in b.hardware_spec.cores.core_type.matrix_engine.macs_per_cycle:
        _refuse("UnsupportedPrecision", "/intent/precision/compute peak")
    if (
        rank.tp != intent.tp
        or rank.rank_index >= rank.tp
        or not rank.equivalent_ranks
        or len(set(rank.equivalent_ranks)) != len(rank.equivalent_ranks)
        or rank.rank_index not in rank.equivalent_ranks
        or any(x >= rank.tp for x in rank.equivalent_ranks)
    ):
        _refuse("UnsupportedRankScope", "/rank")
    if rank.kind == "balanced_tp_representative" and tuple(rank.equivalent_ranks) != tuple(
        range(rank.tp)
    ):
        _refuse("UnsupportedRankScope", "/rank/equivalent_ranks")
    expected = {
        ("decode", batch, batch * context, f, intent.initial_state)
        for batch, context, f in product(
            intent.grid.decode.batch,
            intent.grid.decode.context_per_seq,
            intent.grid.frequency_ratio,
        )
    } | {
        ("prefill", n, length, f, intent.initial_state)
        for n, length, f in product(
            intent.grid.prefill.n, intent.grid.prefill.L, intent.grid.frequency_ratio
        )
    }
    observed: set[tuple[object, ...]] = set()
    for point in b.points:
        q = point.query
        key: tuple[object, ...]
        if isinstance(q, DecodeQuery):
            if q.total_context_tokens % q.batch:
                _refuse("MissingCoverage", "/query/total_context_tokens")
            key = (
                q.phase,
                q.batch,
                q.total_context_tokens,
                point.frequency_ratio,
                point.initial_state,
            )
            tokens, batch, seq, context = q.batch, q.batch, 1, q.total_context_tokens // q.batch
        else:
            key = (
                q.phase,
                q.n_prompts,
                q.prompt_tokens,
                point.frequency_ratio,
                point.initial_state,
            )
            tokens, batch, seq, context = (
                q.n_prompts * q.prompt_tokens,
                q.n_prompts,
                q.prompt_tokens,
                q.prompt_tokens,
            )
        if key in observed:
            _refuse("MissingCoverage", "duplicate point")
        observed.add(key)
        if len(point.embedding_hits) != rank.tp or sum(point.embedding_hits) != tokens:
            _refuse("UnsupportedRankScope", "/embedding_hits conservation")
        if any(
            point.embedding_hits[x] != point.embedding_hits[rank.rank_index]
            for x in rank.equivalent_ranks
        ):
            _refuse("UnsupportedRankScope", "/embedding_hits equivalence")
        if point.hit_source == "tp1_trivial" and rank.tp != 1:
            _refuse("UnsupportedRankScope", "/hit_source")
        g = point.graph
        if not set(DECLARED_OMISSIONS) <= set(g.omissions):
            _refuse("InvalidPreparedGraph", "/graph/omissions")
        if intent.model.n_experts > 1 and MOE_OMISSION not in g.omissions:
            _refuse("InvalidPreparedGraph", "/graph/MoE omission")
        if (
            sum(group.repeat for group in g.groups if group.kind == "decoder")
            != intent.model.n_layers
        ):
            _refuse("InvalidPreparedGraph", "/graph/layer count")
        if g.lm_head_tokens not in ({tokens} if q.phase == "decode" else {tokens, batch}):
            _refuse("InvalidPreparedGraph", "/lm_head_tokens")
        group_ids: set[str] = set()
        for group in g.groups:
            if group.id in group_ids or not set(group.depends_on) <= group_ids:
                _refuse("InvalidDependency", "/groups/" + group.id)
            group_ids.add(group.id)
            if group.kind != "decoder" and group.repeat != 1:
                _refuse("InvalidPreparedGraph", "/group repeat")
            if (
                group.kind == "decoder"
                and not intent.uarch_fidelity.layer_reuse
                and group.repeat != 1
            ):
                _refuse("InvalidPreparedGraph", "/layer_reuse")
            op_ids: set[str] = set()
            for op in group.ops:
                if (
                    op.id in op_ids
                    or not set(op.depends_on) <= op_ids
                    or len(set(op.depends_on)) != len(op.depends_on)
                ):
                    _refuse("InvalidDependency", group.id + "/" + op.id)
                op_ids.add(op.id)
                validate_op(op)
                spec = op.spec
                dims = spec.dimensions
                if set(op.operand_access) != set(spec.operands):
                    _refuse("InvalidPreparedGraph", op.id + "/operand_access")
                if (str(spec.operator) == "attention_fused") != (op.fusion == "qk_softmax_av"):
                    _refuse("FusionMismatch", op.id + "/fusion")
                for operand_key, operand in spec.operands.items():
                    coefficient = str(spec.operator) == "rotary_embedding" and operand_key in (
                        "Cos",
                        "Sin",
                    )
                    if operand.dtype not in formats and not coefficient:
                        _refuse("UnsupportedPrecision", op.id + "/operand dtype")
                    if (
                        operand.layout == "paged"
                        and operand.block_size_tokens != intent.kv_layout.block_size_tokens
                    ):
                        _refuse("KvLayoutMismatch", op.id + "/paged operand")
                for pad in op.padding:
                    if pad.physical < pad.logical or dims.get(pad.dimension) != pad.physical:
                        _refuse("InvalidPreparedGraph", op.id + "/padding")
                for rep in op.replication:
                    if (
                        rep.rank_extent * rank.tp != rep.global_extent * rep.replicas
                        or dims.get(rep.dimension) != rep.rank_extent
                    ):
                        _refuse("UnsupportedRankScope", op.id + "/replication")
                if str(spec.operator) == "embedding":
                    if (
                        op.embedding_local_tokens != point.embedding_hits[rank.rank_index]
                        or dims.get("M") != tokens
                    ):
                        _refuse("UnsupportedRankScope", op.id + "/embedding_local_tokens")
                elif op.embedding_local_tokens is not None:
                    _refuse("InvalidPreparedGraph", op.id + "/embedding_local_tokens")
                if op.kv_access is not None:
                    kv, block = op.kv_access, intent.kv_layout.block_size_tokens
                    if (
                        kv.block_size_tokens != block
                        or kv.context_tokens != context
                        or kv.pages_per_sequence != (context + block - 1) // block
                        or kv.last_page_valid_tokens != 1 + (context - 1) % block
                    ):
                        _refuse("KvLayoutMismatch", op.id + "/kv_access")
                if str(spec.operator) == "attention_fused":
                    if op.kv_access is None or (dims.get("B"), dims.get("S"), dims.get("T")) != (
                        batch,
                        seq,
                        context,
                    ):
                        _refuse("KvLayoutMismatch", op.id + "/attention query")
                    if dims.get("Hq") != intent.model.n_heads // rank.tp or dims.get("Hkv") != max(
                        1, intent.model.kv_heads // rank.tp
                    ):
                        _refuse("UnsupportedRankScope", op.id + "/attention heads")
                expert = intent.model.n_experts > 0 and str(spec.operator) in (
                    "ffn_up",
                    "ffn_gate",
                    "ffn_down",
                    "activation",
                )
                if op.work_repeat != (intent.model.experts_per_token if expert else 1):
                    _refuse("InvalidPreparedGraph", op.id + "/work_repeat")
                if op.weight_copies != (
                    intent.model.n_experts if expert and str(spec.operator) != "activation" else 1
                ):
                    _refuse("InvalidPreparedGraph", op.id + "/weight_copies")
    if observed != expected:
        _refuse("MissingCoverage", "/points exact grid/state/frequency")
    return b


def validate_execution_bundle(value: object) -> PreparedBundleV2:
    """Validate global logical extents and the supplied physical graph without remapping."""
    b = _validate_structure(value)
    _validate_rotary_graph(b)
    intent = b.intent
    if intent.mapping_policy != "analytic-ops@2":
        raise ValueError("UnsupportedMappingScope: analytic execution requires analytic-ops@2")
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
                    rotary_embedding=2,
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
                if name == "rotary_embedding":
                    continue  # Fully checked by _validate_rotary_graph, not remapped.
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
                    required = {by_name[n].id for n in ("kv_write",)}
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
                    or not {"rope_q", by_name["kv_write"].id} <= set(score.depends_on)
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
    from .capacity_v2 import capacity_summary

    for point in b.points:
        capacity_summary(b, point)
    return b


if TYPE_CHECKING:
    from rkuarch.engines.protocol_v2 import EngineJobV2, EngineResultV2

ALGORITHMS = {
    "rotary": "rope-3e-plus-explicit-casts/1",
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
    from rkuarch.engines.analytic.rotary_v2 import engine_identity

    result = AssumptionSet(
        format="uarch-assumptions/1",
        assumptions_hash="sha256:" + "0" * 64,
        model=ModelIdentity.model_validate(engine_identity().model.model_dump()),
        algorithms=ALGORITHMS,
        limitations=(
            "Abstract vector operation rate is unvalidated for transcendental algorithms.",
            "No independent full-workload physical timing validation.",
            "RoPE scalar casts are abstract vector ops, not measured instructions.",
            "Supplied FP32 coefficient reads are charged per node/token/layer, without retention.",
            "Precomputed coefficients have no named-model equivalence claim.",
            "RoPE supports same-format FP32/BF16/FP16 activations and KV only.",
            "Coefficient allocation is known; total peak residency remains unknown.",
        ),
    )
    return result.model_copy(
        update={"assumptions_hash": content_hash(result, exclude=("assumptions_hash",))}
    )


def validate_assumptions(bundle: PreparedBundleV2, assumptions: AssumptionSet) -> None:
    actual = AssumptionSet.model_validate(raw(assumptions))
    verify_identity(actual, "assumptions_hash")
    if (
        actual != physical_assumptions()
        or actual.assumptions_hash != bundle.intent.assumptions_hash
    ):
        raise ValueError("AssumptionMismatch: active v2 algorithms/model/limitations")


def load_prepared_input(path: Path) -> PreparedBundleV2:
    return validate_execution_bundle(strict_json_loads(Path(path).read_bytes()))


def prepare_engine_job(
    bundle: PreparedBundleV2, point_hash: str, *, assumptions: AssumptionSet
) -> EngineJobV2:
    """The shared table/adapter analytic boundary, bypassing all producer entry points."""
    from rkuarch.engines.analytic.rotary_v2 import engine_identity
    from rkuarch.engines.protocol_v2 import EngineJobV2, validate_engine_job

    b = validate_execution_bundle(bundle)
    validate_assumptions(b, assumptions)
    matches = [p for p in b.points if p.payload_hash == point_hash]
    if len(matches) != 1:
        raise ValueError("MissingCoverage: exact prepared point")
    point = matches[0]
    request = CharacterizationRequestV3(
        **b.intent.model_dump(mode="json"), prepared_input_hash=b.bundle_hash
    )
    job = EngineJobV2(
        coefficients=b.coefficients,
        protocol="uarch-engine/2",
        job_hash="sha256:" + "0" * 64,
        request_hash=content_hash(request),
        bundle_hash=b.bundle_hash,
        point_hash=point.payload_hash,
        producer=b.producer,
        engine=engine_identity(),
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
    validate_engine_job(job, b, request, assumptions=assumptions)
    return job


def execute_prepared_point(
    bundle: PreparedBundleV2, point_hash: str, *, assumptions: AssumptionSet
) -> tuple[EngineJobV2, EngineResultV2]:
    """Execute the validated captured job in process, without a producer import."""
    from rkuarch.engines.analytic.rotary_v2 import run_analytic

    job = prepare_engine_job(bundle, point_hash, assumptions=assumptions)
    return job, run_analytic(job, bundle=bundle, assumptions=assumptions)
