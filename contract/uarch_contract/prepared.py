"""Accepted U2 shared carriers; explicit verification checks cross-artifact semantics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import Field

from .common import FrozenModel, JsonFloat
from .hardware import HardwareSpec
from .operators import OpSpec
from .request import RequestIntent


class Producer(FrozenModel):
    implementation_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    name: Annotated[str, Field(min_length=1)]
    version: Annotated[str, Field(min_length=1)]


class RankScope(FrozenModel):
    collectives: Literal["excluded"]
    equivalent_ranks: Annotated[
        tuple[Annotated[int, Field(strict=True, ge=0)], ...], Field(min_length=1)
    ]
    kind: Literal["balanced_tp_representative", "balanced_tp_selected_rank"]
    rank_index: Annotated[int, Field(strict=True, ge=0)]
    tp: Annotated[int, Field(strict=True, ge=1)]


class DecodeQuery(FrozenModel):
    batch: Annotated[int, Field(strict=True, ge=1)]
    phase: Literal["decode"]
    total_context_tokens: Annotated[int, Field(strict=True, ge=1)]


class PrefillQuery(FrozenModel):
    n_prompts: Annotated[int, Field(strict=True, ge=1)]
    phase: Literal["prefill"]
    prompt_tokens: Annotated[int, Field(strict=True, ge=1)]


class Padding(FrozenModel):
    dimension: Annotated[str, Field(min_length=1)]
    logical: Annotated[int, Field(strict=True, ge=1)]
    physical: Annotated[int, Field(strict=True, ge=1)]


class Replication(FrozenModel):
    dimension: Annotated[str, Field(min_length=1)]
    global_extent: Annotated[int, Field(strict=True, ge=1)]
    rank_extent: Annotated[int, Field(strict=True, ge=1)]
    replicas: Annotated[int, Field(strict=True, ge=1)]


class KvAccess(FrozenModel):
    block_size_tokens: Annotated[int, Field(strict=True, ge=1)]
    context_tokens: Annotated[int, Field(strict=True, ge=1)]
    last_page_valid_tokens: Annotated[int, Field(strict=True, ge=1)]
    pages_per_sequence: Annotated[int, Field(strict=True, ge=1)]
    read_policy: Literal["valid_tokens"]
    write_policy: Literal["append_valid_tokens"]


class PreparedOp(FrozenModel):
    depends_on: Annotated[tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=0)]
    embedding_local_tokens: Annotated[int, Field(strict=True, ge=0)] | None
    fusion: Literal["none", "qk_softmax_av"]
    id: Annotated[str, Field(min_length=1)]
    kv_access: KvAccess | None
    operand_access: dict[str, Literal["read", "write", "read_write"]]
    padding: Annotated[tuple[Padding, ...], Field(min_length=0)]
    replication: Annotated[tuple[Replication, ...], Field(min_length=0)]
    spec: OpSpec
    weight_copies: Annotated[int, Field(strict=True, ge=1)]
    work_repeat: Annotated[int, Field(strict=True, ge=1)]


class OpGroup(FrozenModel):
    depends_on: Annotated[tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=0)]
    id: Annotated[str, Field(min_length=1)]
    kind: Literal["head", "decoder", "tail"]
    ops: Annotated[tuple[PreparedOp, ...], Field(min_length=1)]
    repeat: Annotated[int, Field(strict=True, ge=1)]


class PreparedGraph(FrozenModel):
    attention_mask: Literal["full_square", "causal"]
    groups: Annotated[tuple[OpGroup, ...], Field(min_length=1)]
    lm_head_tokens: Annotated[int, Field(strict=True, ge=1)]
    omissions: Annotated[tuple[Annotated[str, Field(min_length=1)], ...], Field(min_length=4)]


class PreparedPoint(FrozenModel):
    embedding_hits: Annotated[
        tuple[Annotated[int, Field(strict=True, ge=0)], ...], Field(min_length=1)
    ]
    frequency_ratio: Annotated[JsonFloat, Field(gt=0)]
    graph: PreparedGraph
    hit_source: Literal["provided_counts", "synthetic_balanced_assignment", "tp1_trivial"]
    initial_state: Literal["steady", "cold"]
    payload_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    query: Query


class PreparedBundle(FrozenModel):
    bundle_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    format: Literal["uarch-prepared/1"]
    hardware_spec: HardwareSpec
    intent: RequestIntent
    intent_hash: Annotated[str, Field(pattern="^sha256:[0-9a-f]{64}$")]
    mapping_scope: Literal["analytic_ops"]
    points: Annotated[tuple[PreparedPoint, ...], Field(min_length=1)]
    producer: Producer
    rank: RankScope


Query = Annotated[DecodeQuery | PrefillQuery, Field(discriminator="phase")]

# Only accepted named roots are emitted; inline helper shapes are nested definitions.
SCHEMA_ROOTS = (
    Producer,
    RankScope,
    Padding,
    Replication,
    KvAccess,
    PreparedOp,
    OpGroup,
    PreparedGraph,
    PreparedPoint,
    PreparedBundle,
)

for _model in (
    Producer,
    RankScope,
    DecodeQuery,
    PrefillQuery,
    Padding,
    Replication,
    KvAccess,
    PreparedOp,
    OpGroup,
    PreparedGraph,
    PreparedPoint,
    PreparedBundle,
):
    _model.model_rebuild()


def validate_prepared_bundle(value: object) -> PreparedBundle:
    """Validate an imported bundle without calling a producer or changing resolved work."""
    from itertools import product

    from .comparison import _refuse
    from .hashing import content_hash, spec_hash, verify_identity
    from .table import DECLARED_OMISSIONS, MOE_OMISSION

    if isinstance(value, dict):
        if value.get("format") != "uarch-prepared/1":
            _refuse("UnsupportedPreparedVersion", "/format")
        if value.get("mapping_scope") != "analytic_ops":
            _refuse("UnsupportedMappingScope", "/mapping_scope")
    b = PreparedBundle.model_validate(value)
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
                validate_prepared_op(op)
                spec = op.spec
                dims = spec.dimensions
                if set(op.operand_access) != set(spec.operands):
                    _refuse("InvalidPreparedGraph", op.id + "/operand_access")
                if (str(spec.operator) == "attention_fused") != (op.fusion == "qk_softmax_av"):
                    _refuse("FusionMismatch", op.id + "/fusion")
                for operand in spec.operands.values():
                    if operand.dtype not in formats:
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


def validate_prepared_op(op: PreparedOp) -> PreparedOp:
    """Enforce the accepted per-operator operand axes, reductions and access modes."""
    from .comparison import _refuse

    name = str(op.spec.operator)
    projections = {
        "q_projection",
        "k_projection",
        "v_projection",
        "output_projection",
        "ffn_up",
        "ffn_gate",
        "ffn_down",
        "lm_head",
    }
    axes: Mapping[str, tuple[str, ...]]
    reductions: tuple[str, ...]
    if name in projections:
        axes, reductions = {"X": ("M", "K"), "W": ("K", "N"), "Y": ("M", "N")}, ("K",)
    elif name == "normalization":
        axes, reductions = {"X": ("M", "D"), "Y": ("M", "D"), "W": ("D",)}, ("D",)
    elif name == "residual_addition":
        axes, reductions = {n: ("M", "D") for n in ("X", "R", "Y")}, ()
    elif name == "activation":
        axes, reductions = {n: ("M", "D") for n in op.spec.operands}, ()
        if set(axes) not in ({"X", "Y"}, {"X", "G", "Y"}):
            _refuse("InvalidPreparedGraph", op.id + "/activation operands")
    elif name == "embedding":
        axes, reductions = {"W": ("V", "D"), "Y": ("M", "D")}, ()
    elif name == "kv_write":
        axes, reductions = {n: ("B", "Hkv", "S", "D") for n in ("K", "V", "K_cache", "V_cache")}, ()
    else:
        q, kv, scores = ("B", "Hq", "S", "D"), ("B", "Hkv", "T", "D"), ("B", "Hq", "S", "T")
        axes, reductions = {
            "attention_fused": ({"Q": q, "K": kv, "V": kv, "O": q}, ("T", "D")),
            "qk_score": ({"Q": q, "K": kv, "scores": scores}, ("D",)),
            "softmax": ({"scores": scores, "probs": scores}, ("T",)),
            "av_application": ({"probs": scores, "V": kv, "O": q}, ("T",)),
        }[name]
    if set(op.spec.operands) != set(axes) or tuple(op.spec.reduction_axes) != reductions:
        _refuse("InvalidPreparedGraph", op.id + "/operands/reduction_axes")
    for key, dimensions in axes.items():
        if tuple(op.spec.operands[key].dimensions) != dimensions:
            _refuse("InvalidPreparedGraph", op.id + "/" + key + "/dimensions")
        writes = {"Y", "O", "K_cache", "V_cache"}
        if name == "qk_score":
            writes.add("scores")
        if name == "softmax":
            writes.add("probs")
        if op.operand_access[key] != ("write" if key in writes else "read"):
            _refuse("InvalidPreparedGraph", op.id + "/" + key + "/access")
    if name in ("attention_fused", "qk_score", "av_application"):
        if op.spec.dimensions["Hq"] % op.spec.dimensions["Hkv"]:
            _refuse("InvalidPreparedGraph", op.id + "/head grouping")
    return op
