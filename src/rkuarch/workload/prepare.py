"""Standalone balanced TP producer; imported graphs never pass through this module."""

from __future__ import annotations

import hashlib
from itertools import product
from pathlib import Path
from typing import Any, Literal

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash
from uarch_contract.prepared import PreparedBundle
from uarch_contract.request import RequestIntent
from uarch_contract.table import DECLARED_OMISSIONS, MOE_OMISSION

from .prepared import validate_execution_bundle

_IMPLEMENTATION_HASH = "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_ZERO = "sha256:" + "0" * 64


def prepare(
    intent: RequestIntent,
    hardware: HardwareSpec,
    *,
    rank_index: int = 0,
    embedding_hits: tuple[tuple[int, ...], ...] | None = None,
    synthetic_assignment: bool = False,
    attention_mask: Literal["full_square", "causal"] = "full_square",
    lm_head: Literal["all", "last"] = "all",
    fused_attention: bool = True,
) -> PreparedBundle:
    """Prepare one selected rank, conserving explicit per-point embedding assignments.

    Supplied hit vectors follow decode B/context/frequency then prefill n/L/frequency.
    Synthetic balanced assignment gives remainder tokens to the lowest ranks, only on opt-in.
    """
    intent = RequestIntent.model_validate(intent.model_dump(mode="json"))
    if not 0 <= rank_index < intent.tp or lm_head not in ("all", "last"):
        raise ValueError("UnsupportedRankScope: rank/head selection")
    if embedding_hits is not None and synthetic_assignment:
        raise ValueError("Ambiguous embedding assignment")
    m, shape, tp = intent.model, intent.model_shape, intent.tp
    queries: list[dict[str, Any]] = [
        dict(phase="decode", batch=b, total_context_tokens=b * t, frequency_ratio=f)
        for b, t, f in product(
            intent.grid.decode.batch,
            intent.grid.decode.context_per_seq,
            intent.grid.frequency_ratio,
        )
    ]
    queries += [
        dict(phase="prefill", n_prompts=n, prompt_tokens=s, frequency_ratio=f)
        for n, s, f in product(
            intent.grid.prefill.n, intent.grid.prefill.L, intent.grid.frequency_ratio
        )
    ]
    if embedding_hits is not None and len(embedding_hits) != len(queries):
        raise ValueError("embedding assignment coverage")
    points: list[dict[str, Any]] = []
    d, h, ff = m.d_model, m.head_dim, shape.d_ff // tp
    heads, kvh, vocab = m.n_heads // tp, max(1, m.kv_heads // tp), (shape.vocab_size + tp - 1) // tp
    for qi, item in enumerate(queries):
        query = dict(item)
        frequency = query.pop("frequency_ratio")
        decode = query["phase"] == "decode"
        batch = int(query["batch"] if decode else query["n_prompts"])
        seq = 1 if decode else int(query["prompt_tokens"])
        context = int(query["total_context_tokens"]) // batch if decode else seq
        tokens = batch * seq
        if embedding_hits is not None:
            hits, source = embedding_hits[qi], "provided_counts"
        elif tp == 1:
            hits, source = (tokens,), "tp1_trivial"
        elif synthetic_assignment:
            hits = tuple(tokens // tp + (r < tokens % tp) for r in range(tp))
            source = "synthetic_balanced_assignment"
        else:
            raise ValueError("Explicit embedding assignment or synthetic opt-in required")
        if len(hits) != tp or any(type(v) is not int or v < 0 for v in hits) or sum(hits) != tokens:
            raise ValueError("embedding assignment conservation")
        groups: list[dict[str, Any]] = []
        ops: list[dict[str, Any]] = []

        # Local graph-building helpers execute synchronously and never escape this iteration.
        def add(
            name: str,
            dims: dict[str, int],
            axes: dict[str, tuple[str, ...]],
            reduction: tuple[str, ...] = (),
            *,
            id: str | None = None,
            deps: tuple[str, ...] | None = None,
        ) -> str:
            oid = id or name
            operands = {}
            access = {}
            for key, operand_axes in axes.items():
                cache = key in ("K_cache", "V_cache") or (
                    name in ("attention_fused", "qk_score", "av_application") and key in ("K", "V")
                )
                operands[key] = dict(
                    dtype=intent.precision.kv_cache if cache else intent.precision.compute,
                    dimensions=operand_axes,
                    layout="paged" if cache else "contiguous",
                    block_size_tokens=intent.kv_layout.block_size_tokens if cache else None,
                )
                writes = (
                    key in ("Y", "O", "K_cache", "V_cache")
                    or (name == "qk_score" and key == "scores")
                    or (name == "softmax" and key == "probs")
                )
                access[key] = "write" if writes else "read"
            expert = bool(m.n_experts) and name in ("ffn_up", "ffn_gate", "ffn_down", "activation")
            pads = []
            if name in ("embedding", "lm_head") and shape.vocab_size % tp:
                # The selected shard stores a full ceiling-width allocation, including masked slots.
                axis = "V" if name == "embedding" else "N"
                logical = min(vocab, max(1, shape.vocab_size - rank_index * vocab))
                pads = [dict(dimension=axis, logical=logical, physical=vocab)]
            reps = []
            if m.kv_heads < tp:
                axis = "N" if name in ("k_projection", "v_projection") else "Hkv"
                if name in (
                    "k_projection",
                    "v_projection",
                    "kv_write",
                    "attention_fused",
                    "qk_score",
                    "av_application",
                ):
                    reps = [
                        dict(
                            dimension=axis,
                            global_extent=m.kv_heads * (h if axis == "N" else 1),
                            rank_extent=kvh * (h if axis == "N" else 1),
                            replicas=tp // m.kv_heads,
                        )
                    ]
            kv = None
            if name in ("attention_fused", "qk_score", "av_application"):
                block = intent.kv_layout.block_size_tokens
                kv = dict(
                    block_size_tokens=block,
                    context_tokens=context,  # noqa: B023
                    pages_per_sequence=(context + block - 1) // block,  # noqa: B023
                    last_page_valid_tokens=1 + (context - 1) % block,  # noqa: B023
                    read_policy="valid_tokens",
                    write_policy="append_valid_tokens",
                )
            ops.append(  # noqa: B023
                dict(
                    id=oid,
                    depends_on=deps if deps is not None else (() if not ops else (ops[-1]["id"],)),  # noqa: B023
                    embedding_local_tokens=hits[rank_index] if name == "embedding" else None,  # noqa: B023
                    fusion="qk_softmax_av" if name == "attention_fused" else "none",
                    kv_access=kv,
                    operand_access=access,
                    padding=pads,
                    replication=reps,
                    spec=dict(
                        operator=name, dimensions=dims, operands=operands, reduction_axes=reduction
                    ),
                    weight_copies=m.n_experts if expert and name != "activation" else 1,
                    work_repeat=m.experts_per_token if expert else 1,
                )
            )
            return oid

        def projection(name: str, k: int, n: int, rows: int = tokens) -> None:
            add(
                name, dict(M=rows, K=k, N=n), dict(X=("M", "K"), W=("K", "N"), Y=("M", "N")), ("K",)
            )

        def norm(id: str) -> None:
            add(
                "normalization",
                dict(M=tokens, D=d),  # noqa: B023
                dict(X=("M", "D"), Y=("M", "D"), W=("D",)),
                ("D",),
                id=id,
            )

        def finish(kind: str, gid: str, repeat: int = 1) -> None:
            nonlocal ops
            groups.append(  # noqa: B023
                dict(
                    id=gid,
                    kind=kind,
                    repeat=repeat,
                    depends_on=() if not groups else (groups[-1]["id"],),  # noqa: B023
                    ops=ops,
                )
            )
            ops = []

        add("embedding", dict(M=tokens, V=vocab, D=d), dict(W=("V", "D"), Y=("M", "D")))
        finish("head", "head")
        for layer in range(1 if intent.uarch_fidelity.layer_reuse else m.n_layers):
            norm("attention_norm")
            for name, width in [
                ("q_projection", heads * h),
                ("k_projection", kvh * h),
                ("v_projection", kvh * h),
            ]:
                projection(name, d, width)
            add(
                "kv_write",
                dict(B=batch, Hkv=kvh, S=seq, D=h),
                {key: ("B", "Hkv", "S", "D") for key in ("K", "V", "K_cache", "V_cache")},
                deps=("k_projection", "v_projection"),
            )
            dims = dict(B=batch, Hq=heads, Hkv=kvh, S=seq, T=context, D=h)
            q = ("B", "Hq", "S", "D")
            kv = ("B", "Hkv", "T", "D")
            scores = ("B", "Hq", "S", "T")
            if fused_attention:
                add(
                    "attention_fused",
                    dims,
                    dict(Q=q, K=kv, V=kv, O=q),
                    ("T", "D"),
                    deps=("q_projection", "kv_write"),
                )
            else:
                add(
                    "qk_score",
                    dims,
                    dict(Q=q, K=kv, scores=scores),
                    ("D",),
                    deps=("q_projection", "kv_write"),
                )
                add("softmax", dims, dict(scores=scores, probs=scores), ("T",))
                add(
                    "av_application",
                    dims,
                    dict(probs=scores, V=kv, O=q),
                    ("T",),
                    deps=("softmax", "kv_write"),
                )
            projection("output_projection", heads * h, d)
            add(
                "residual_addition",
                dict(M=tokens, D=d),  # noqa: B023
                {key: ("M", "D") for key in ("X", "R", "Y")},
                id="attention_residual",
            )
            norm("ffn_norm")
            projection("ffn_up", d, ff)
            if shape.gated_mlp:
                projection("ffn_gate", d, ff)
            add(
                "activation",
                dict(M=tokens, D=ff),
                {key: ("M", "D") for key in (("X", "G", "Y") if shape.gated_mlp else ("X", "Y"))},
                deps=("ffn_up", "ffn_gate") if shape.gated_mlp else ("ffn_up",),
            )
            projection("ffn_down", ff, d)
            add(
                "residual_addition",
                dict(M=tokens, D=d),  # noqa: B023
                {key: ("M", "D") for key in ("X", "R", "Y")},
                id="ffn_residual",
            )
            finish(
                "decoder",
                f"decoder-{layer}",
                m.n_layers if intent.uarch_fidelity.layer_reuse else 1,
            )
        norm("final_norm")
        head_tokens = batch if lm_head == "last" else tokens
        projection("lm_head", d, vocab, head_tokens)
        finish("tail", "tail")
        point = dict(
            query=query,
            frequency_ratio=frequency,
            initial_state=intent.initial_state,
            embedding_hits=hits,
            hit_source=source,
            payload_hash=_ZERO,
            graph=dict(
                groups=groups,
                lm_head_tokens=head_tokens,
                attention_mask=attention_mask,
                omissions=DECLARED_OMISSIONS + ((MOE_OMISSION,) if m.n_experts else ()),
            ),
        )
        point["payload_hash"] = content_hash(point, exclude=("payload_hash",))
        points.append(point)
    equivalent = tuple(
        r
        for r in range(tp)
        if all(p["embedding_hits"][r] == p["embedding_hits"][rank_index] for p in points)
    )
    bundle = PreparedBundle.model_validate(
        dict(
            format="uarch-prepared/1",
            bundle_hash=_ZERO,
            hardware_spec=hardware,
            intent=intent,
            intent_hash=content_hash(intent),
            mapping_scope="analytic_ops",
            points=points,
            producer=dict(
                name="standalone-balanced-tp", version="1", implementation_hash=_IMPLEMENTATION_HASH
            ),
            rank=dict(
                tp=tp,
                rank_index=rank_index,
                equivalent_ranks=equivalent,
                collectives="excluded",
                kind="balanced_tp_representative"
                if len(equivalent) == tp
                else "balanced_tp_selected_rank",
            ),
        )
    )
    bundle = bundle.model_copy(
        update={"bundle_hash": content_hash(bundle, exclude=("bundle_hash",))}
    )
    return validate_execution_bundle(bundle)
