"""R mathematical inputs and ordinary /5 assembly; no timing or simulation."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

from uarch_contract.reference import ReferenceBundle, ReferenceJob, ReferenceSource, TpuV5eReference
from uarch_contract.reference_json import content_hash


def sealed(raw: Any, field: Any) -> Any:
    return dict(raw, **{field: content_hash(raw, exclude=(field,))})


def nominal_hardware() -> TpuV5eReference:
    return TpuV5eReference.model_validate(
        json.loads(Path(__file__).with_name("tpu_v5e.json").read_text(encoding="utf-8"))
    )


def operand(dtype: Any, axes: Any, *, page: Any = None) -> Any:
    return dict(
        dtype=dtype,
        dimensions=list(axes),
        layout="paged" if page else "contiguous",
        block_size_tokens=page,
    )


def prepared(
    op_id: Any,
    operator: Any,
    dimensions: Any,
    operands: Any,
    *,
    depends: Any = (),
    rotary: Any = None,
    kv: Any = None,
) -> Any:
    return dict(
        id=op_id,
        depends_on=list(depends),
        embedding_local_tokens=None,
        fusion="qk_softmax_av" if operator == "attention_fused" else "none",
        kv_access=kv,
        operand_access={
            k: ("write" if k in {"Y", "O", "K_out", "V_out", "K_cache", "V_cache"} else "read")
            for k in operands
        },
        padding=[],
        replication=[],
        spec=dict(
            operator=operator,
            dimensions=dimensions,
            operands=operands,
            reduction_axes=["K"] if "K" in dimensions else [],
        ),
        weight_copies=1,
        work_repeat=1,
        rotary=rotary,
    )


def source(
    ops: Any,
    *,
    coefficients: Any = None,
    before: Any = 0,
    after: Any = 1,
    pages: Any = (),
    scope: Any = "individual",
) -> Any:
    scalar_inputs = {}
    for op in ops:
        kind = op["spec"]["operator"]
        if kind == "normalization":
            scalar_inputs["rmsnorm_epsilon"] = 1e-5
        if kind == "attention_fused":
            scalar_inputs["attention_scale"] = op["spec"]["dimensions"]["D"] ** -0.5
        if (
            kind
            in {
                "q_projection",
                "k_projection",
                "v_projection",
                "output_projection",
                "ffn_up",
                "ffn_gate",
                "ffn_down",
            }
            and op["spec"]["operands"]["X"]["dtype"] == "int8"
        ):
            scalar_inputs.update(raw_int8_min=-7.0, raw_int8_max=7.0)
    encoding = (
        None
        if coefficients is None
        else dict(
            kind="rope-precomputed/1",
            rotary_dim=coefficients.rotary_dim,
            pairing="split_halves",
            coefficients_hash=coefficients.coefficients_hash,
            position_policy="zero-origin-contiguous/1",
            cache_key_state="rotated-before-store",
            numeric_policy="fp32-separate-round-rne/1",
        )
    )
    return ReferenceSource.model_validate(
        sealed(
            dict(
                scope=scope,
                scalar_inputs=scalar_inputs,
                ops=ops,
                attention_mask="causal",
                coefficients=None if coefficients is None else coefficients.model_dump(mode="json"),
                kv_key_encoding=encoding,
                page_indices=list(pages),
                context_before=before,
                context_after=after,
            ),
            "source_hash",
        )
    )


def dot(
    op_id: Any,
    m: Any,
    k: Any,
    n: Any,
    precision: Any = "bf16",
    operator: Any = "q_projection",
    depends: Any = (),
) -> Any:
    return prepared(
        op_id,
        operator,
        dict(M=m, K=k, N=n),
        dict(
            X=operand(precision, ("M", "K")),
            W=operand(precision, ("K", "N")),
            Y=operand("int32" if precision == "int8" else "bf16", ("M", "N")),
        ),
        depends=depends,
    )


def matrix_source(m: Any, k: Any, n: Any, precision: Any = "bf16") -> Any:
    return source([dot("dot", m, k, n, precision)])


def suite_source(row: Any, *, coefficients: Any = None, page_indices: Any = None) -> Any:
    """Translate an explicit suite row; no fixture allowlist or compiler observation claim."""
    w = row["work"]
    category = row["benchmark_class"]
    op_id = row["id"]
    if category == "matrix":
        return matrix_source(w["M"], w["K"], w["N"], w["precision"])
    if category == "memory":
        e = w["elements"]
        operator = {"read": "stream_read_sum", "write": "stream_fill", "copy": "stream_copy"}[
            w["action"]
        ]
        operands = dict(
            X=operand("bf16", ("One",) if w["action"] == "write" else ("E",)),
            Y=operand(
                "fp32" if w["action"] == "read" else "bf16",
                ("One",) if w["action"] == "read" else ("E",),
            ),
        )
        return source([prepared(op_id, operator, dict(E=e, One=1), operands)])
    if category in {"launch", "launch_overhead", "launch overhead"}:
        return source(
            [
                prepared(
                    op_id,
                    "scalar_add",
                    dict(M=1, D=1),
                    {x: operand("fp32", ("M", "D")) for x in ("X", "W", "Y")},
                )
            ]
        )
    if category in {"gather", "DRAM gather"}:
        c, p = w["valid_tokens"], w["block_tokens"]
        pages = (c + p - 1) // p
        return source(
            [
                prepared(
                    op_id,
                    "paged_gather",
                    dict(B=1, S=c, T=c, H=w["kv_heads"], D=w["head_dim"], P=p),
                    {
                        k: operand(
                            "bf16", ("B", "T", "H", "D"), page=p if k in {"K", "V"} else None
                        )
                        for k in ("K", "V", "K_out", "V_out")
                    },
                )
            ],
            after=c,
            pages=range(pages - 1, -1, -1) if page_indices is None else page_indices,
        )
    b, s = w["batch"], w["new_tokens"]
    before = w["prior_tokens"]
    t = before + s
    m = b * s
    ops = []

    def add(name: Any, operator: Any, depends: Any = ()) -> Any:
        if operator in {
            "q_projection",
            "k_projection",
            "v_projection",
            "output_projection",
            "ffn_up",
            "ffn_gate",
            "ffn_down",
        }:
            k = 14336 if operator == "ffn_down" else 4096
            n = (
                1024
                if operator in {"k_projection", "v_projection"}
                else 14336
                if operator in {"ffn_up", "ffn_gate"}
                else 4096
            )
            ops.append(dot(name, m, k, n, operator=operator, depends=depends))
            return
        if operator == "rotary_embedding":
            if coefficients is None:
                raise ValueError("Exact coefficient input required")
            target = "q" if name.startswith("q") else "k"
            heads = 32 if target == "q" else 8
            binding = dict(
                target=target,
                coefficients_hash=coefficients.coefficients_hash,
                pairing="split_halves",
                numeric_policy="fp32-separate-round-rne/1",
                position_ids=[list(range(before, t)) for _ in range(b)],
                input_op_id=depends[0],
            )
            ops.append(
                prepared(
                    name,
                    operator,
                    dict(B=b, S=s, H=heads, D=128, R=128),
                    dict(
                        X=operand("bf16", ("B", "S", "H", "D")),
                        Y=operand("bf16", ("B", "S", "H", "D")),
                    ),
                    depends=depends,
                    rotary=binding,
                )
            )
            return
        if operator in {"attention_fused", "kv_write"}:
            dims = dict(B=b, S=s, T=t, Hq=32, H=8, D=128, P=16)
            kv = dict(
                block_size_tokens=16,
                context_tokens=t,
                last_page_valid_tokens=(t - 1) % 16 + 1,
                pages_per_sequence=(t + 15) // 16,
                read_policy="valid_tokens",
                write_policy="append_valid_tokens",
            )
            operands = (
                {
                    x: operand(
                        "bf16",
                        ("B", "S", "Hq", "D") if x in {"Q", "O"} else ("B", "T", "H", "D"),
                        page=16 if x in {"K", "V"} else None,
                    )
                    for x in ("Q", "K", "V", "O")
                }
                if operator == "attention_fused"
                else {
                    k: operand(
                        "bf16",
                        ("B", "S", "H", "D") if k in {"K", "V"} else ("B", "T", "H", "D"),
                        page=16 if k.endswith("_cache") else None,
                    )
                    for k in ("K", "V", "K_cache", "V_cache")
                }
            )
            ops.append(prepared(name, operator, dims, operands, depends=depends, kv=kv))
            return
        d = 14336 if operator == "activation" else 4096
        ops.append(
            prepared(
                name,
                operator,
                dict(M=m, D=d),
                {
                    x: operand(
                        "bf16", ("D",) if x == "W" and operator == "normalization" else ("M", "D")
                    )
                    for x in ("X", "W", "Y")
                },
                depends=depends,
            )
        )

    if category in {"layer", "full_layer", "end-to-end"}:
        sequence = [
            ("norm1", "normalization", ()),
            ("q", "q_projection", ("norm1",)),
            ("k", "k_projection", ("norm1",)),
            ("v", "v_projection", ("norm1",)),
            ("q_rope", "rotary_embedding", ("q",)),
            ("k_rope", "rotary_embedding", ("k",)),
            ("append", "kv_write", ("k_rope", "v")),
            ("attention", "attention_fused", ("q_rope", "append")),
            ("out", "output_projection", ("attention",)),
            ("residual1", "residual_addition", ("out",)),
            ("norm2", "normalization", ("residual1",)),
            ("up", "ffn_up", ("norm2",)),
            ("gate", "ffn_gate", ("norm2",)),
            ("silu", "activation", ("up", "gate")),
            ("down", "ffn_down", ("silu",)),
            ("residual2", "residual_addition", ("down", "residual1")),
        ]
        for name, operator, deps in sequence:
            add(name, operator, deps)
    else:
        operator = w["operator"]
        name = "q" if operator == "q_projection" else "k" if operator == "k_projection" else op_id
        add(name, operator)
        if operator in {"q_projection", "k_projection"}:
            add(name + "_rope", "rotary_embedding", (name,))
    return source(
        ops,
        coefficients=coefficients
        if any(
            x["spec"]["operator"] in {"rotary_embedding", "kv_write", "attention_fused"}
            for x in ops
        )
        else None,
        before=before,
        after=t,
        pages=range((t + 15) // 16),
        scope="decoder" if category in {"layer", "full_layer", "end-to-end"} else "individual",
    )


def prepare_job(bundle: ReferenceBundle) -> ReferenceJob:
    bundle = ReferenceBundle.model_validate(bundle.model_dump(mode="json"))
    return ReferenceJob.model_validate(
        sealed(
            dict(
                protocol="uarch-engine/5",
                bundle_hash=bundle.bundle_hash,
                point_hash=bundle.points[0].payload_hash,
                engine=dict(
                    name="native",
                    version="native-stage/3",
                    package_version=version("rk-uarch"),
                    model=dict(name="native-intervals", version="3"),
                ),
                workload_closure=bundle.model_dump(mode="json"),
                admission=bundle.admission.model_dump(mode="json"),
                seed=0,
            ),
            "job_hash",
        )
    )
