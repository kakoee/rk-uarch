"""Complete synthetic carrier examples, not a producer, oracle, or executable job.

Reuse the accepted U2 literal by reference; author explicit new profile/nodes/edges.
No production preparation, counting, engine, or transcendental functions are imported.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from uarch_contract.hashing import content_hash, sha256

FIXTURES = Path(__file__).parent / "fixtures/u2"


def literal(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / name).read_text()))


def seal(value: dict[str, Any], key: str) -> None:
    value[key] = content_hash(value, exclude=(key,))


def examples(mode: str = "per_op", pairing: str = "adjacent") -> dict[str, Any]:
    """Author full two-point, tp1, BF16, synthetic-d4 contract closure for tests."""
    producer = dict(
        name="synthetic-contract-example",
        version="1",
        implementation_hash=sha256(Path(__file__).read_bytes()),
    )
    # Synthetic supplied bits, no named model equivalence and no sin/cos generation.
    coefficients = dict(
        format="uarch-rotary-coefficients/1",
        position_count=17,
        rotary_dim=2,
        dtype="fp32",
        cos_bits=[["3f800000"] for _ in range(17)],
        sin_bits=[["00000000"] for _ in range(17)],
        producer=producer,
    )
    seal(coefficients, "coefficients_hash")
    encoding = dict(
        kind="rope-precomputed/1",
        rotary_dim=2,
        pairing=pairing,
        coefficients_hash=coefficients["coefficients_hash"],
        position_policy="zero-origin-contiguous/1",
        cache_key_state="rotated-before-store",
        numeric_policy="fp32-separate-round-rne/1",
    )
    # This identity labels a test-only stand-in, never an installed v2 implementation.
    assumptions = dict(
        format="uarch-assumptions/1",
        model=dict(
            name="physical-resolved",
            version="2",
            implementation_hash=sha256(b"test-only-v2-engine-not-implemented"),
        ),
        algorithms={
            "activation": "silu-5md-plus-gate/1",
            "compute_overlap": "serialize-matrix-vector/1",
            "embedding": "supplied-conserved-hit-vector/1",
            "kv": "valid-tokens-context-includes-append/1",
            "normalization": "rms-6md/1",
            "residency": "partial-weight-kv-checks-total-peak-unknown/1",
            "softmax": "scalar-5pairs/1",
            "traffic": "once-per-operand-no-retention/1",
            "vector_rate": "cores-times-ops-per-cycle-times-resolved-core-hz/1",
            "rotary": "rope-3e-plus-explicit-casts/1",
        },
        limitations=[
            "Test-only identity, no v2 engine exists for this example.",
            "Abstract vector operation rate is unvalidated for transcendental algorithms.",
            "No independent full-workload physical timing validation.",
            "RoPE scalar casts are abstract vector ops, not measured instructions.",
            "Supplied FP32 coefficient reads are charged per node/token/layer, without retention.",
            "Precomputed coefficients have no named-model equivalence claim.",
            "RoPE supports same-format FP32/BF16/FP16 activations and KV only.",
            "Coefficient allocation is known; total peak residency remains unknown.",
        ],
    )
    seal(assumptions, "assumptions_hash")
    bundle = literal("independent-bundle.json")
    bundle.update(format="uarch-prepared/2", coefficients=coefficients, producer=producer)
    bundle["intent"].update(
        contract="uarch-contract/0.3",
        accounting="resolved-ops/2",
        mapping_policy="analytic-ops@2",
        analytic_mode=mode,
        position_encoding=encoding,
        assumptions_hash=assumptions["assumptions_hash"],
    )
    for point in bundle["points"]:
        position = 16 if point["query"]["phase"] == "decode" else 0
        point["graph"]["kv_key_encoding"] = deepcopy(encoding)
        for group in point["graph"]["groups"]:
            ops = []
            for op in group["ops"]:
                op["rotary"] = None
                if op["id"] == "kv":
                    op["depends_on"] = ["rope_k", "v"]
                if op["id"] == "attn":
                    op["depends_on"] = ["rope_q", "rope_k", "v", "kv"]
                ops.append(op)
                if group["kind"] == "decoder" and op["id"] in ("q", "k"):
                    target = op["id"]
                    operands = {
                        name: dict(
                            dtype="bf16" if name in ("X", "Y") else "fp32",
                            dimensions=["B", "H", "S", "D"]
                            if name in ("X", "Y")
                            else ["B", "S", "P"],
                            layout="contiguous",
                            block_size_tokens=None,
                        )
                        for name in ("X", "Cos", "Sin", "Y")
                    }
                    ops.append(
                        dict(
                            depends_on=[target],
                            embedding_local_tokens=None,
                            fusion="none",
                            id="rope_" + target,
                            kv_access=None,
                            operand_access=dict(X="read", Cos="read", Sin="read", Y="write"),
                            padding=[],
                            replication=[],
                            weight_copies=1,
                            work_repeat=1,
                            spec=dict(
                                operator="rotary_embedding",
                                dimensions=dict(
                                    B=1,
                                    H=2 if target == "q" else 1,
                                    S=1,
                                    D=2,
                                    R=2,
                                    P=1,
                                ),
                                operands=operands,
                                reduction_axes=[],
                            ),
                            rotary=dict(
                                target=target,
                                coefficients_hash=coefficients["coefficients_hash"],
                                pairing=pairing,
                                numeric_policy=encoding["numeric_policy"],
                                position_ids=[[position]],
                                input_op_id=target,
                            ),
                        )
                    )
            group["ops"] = ops
        seal(point, "payload_hash")
    bundle["intent_hash"] = content_hash(bundle["intent"])
    seal(bundle, "bundle_hash")
    request = dict(bundle["intent"], prepared_input_hash=bundle["bundle_hash"])
    return dict(bundle=bundle, request=request, assumptions=assumptions)


def rehash(bundle: dict[str, Any]) -> None:
    """Refresh only enclosing identities, never repair deliberately broken joins."""
    for point in bundle["points"]:
        seal(point, "payload_hash")
    bundle["intent_hash"] = content_hash(bundle["intent"])
    seal(bundle, "bundle_hash")


RUNTIME_REFUSALS = (
    "missing-q",
    "doubled-k",
    "rope-in-tail",
    "rotate-v",
    "q-bypass",
    "k-bypass",
    "wrong-projection",
    "cached-token-rotation",
    "odd-R",
    "Hkv-as-Hq",
    "extra-repeat",
    "rotary-padding",
    "different-cache-profile",
    "wrong-position",
    "different-binding-hash",
    "different-pairing",
    "intent-coefficient-mismatch",
    "missing-grid-point",
    "wrong-rank",
    "mixed-kv",
    "fp8",
    "wrong-hardware-hash",
    "wrong-intent-hash",
    "wrong-point-hash",
    "missing-nonrotary-op",
    "layer-repeat",
    "wrong-omissions",
    "short-context-table",
)


def runtime_counterexample(case: str) -> dict[str, Any]:
    """Schema-valid counterexamples for the future full graph/closure validator."""
    b: dict[str, Any] = deepcopy(examples()["bundle"])
    p = b["points"][0]
    groups = p["graph"]["groups"]
    decoder = groups[1]
    ops = decoder["ops"]
    q = next(o for o in ops if o["id"] == "rope_q")
    k = next(o for o in ops if o["id"] == "rope_k")
    by_id = {o["id"]: o for o in ops}
    if case == "missing-q":
        ops.remove(q)
    elif case == "doubled-k":
        ops.append(deepcopy(k))
    elif case == "rope-in-tail":
        ops.remove(q)
        groups[2]["ops"].append(q)
    elif case == "rotate-v":
        k["depends_on"] = ["v"]
        k["rotary"]["input_op_id"] = "v"
    elif case == "q-bypass":
        by_id["attn"]["depends_on"] = ["q", "rope_k", "v", "kv"]
    elif case == "k-bypass":
        by_id["kv"]["depends_on"] = ["k", "v"]
    elif case == "wrong-projection":
        q["depends_on"] = ["k"]
        q["rotary"]["input_op_id"] = "k"
    elif case == "cached-token-rotation":
        k["spec"]["dimensions"]["S"] = 17
        k["rotary"]["position_ids"] = [list(range(17))]
    elif case == "odd-R":
        q["spec"]["dimensions"]["R"] = 3
    elif case == "Hkv-as-Hq":
        k["spec"]["dimensions"]["H"] = 2
    elif case == "extra-repeat":
        k["work_repeat"] = 2
    elif case == "rotary-padding":
        q["padding"] = [dict(dimension="H", logical=1, physical=2)]
    elif case == "different-cache-profile":
        p["graph"]["kv_key_encoding"]["pairing"] = "split_halves"
    elif case == "wrong-position":
        q["rotary"]["position_ids"] = [[15]]
    elif case == "different-binding-hash":
        q["rotary"]["coefficients_hash"] = sha256(b"different supplied table")
    elif case == "different-pairing":
        q["rotary"]["pairing"] = "split_halves"
    elif case == "intent-coefficient-mismatch":
        b["intent"]["position_encoding"]["rotary_dim"] = 4
    elif case == "missing-grid-point":
        b["points"].pop()
    elif case == "wrong-rank":
        b["rank"]["rank_index"] = 1
    elif case == "mixed-kv":
        b["intent"]["precision"]["kv_cache"] = "fp16"
    elif case == "fp8":
        b["intent"]["precision"] = dict(compute="fp8", kv_cache="fp8")
    elif case == "wrong-hardware-hash":
        b["intent"]["hardware_spec_hash"] = sha256(b"wrong hardware")
    elif case == "missing-nonrotary-op":
        ops.remove(by_id["norm1"])
    elif case == "layer-repeat":
        decoder["repeat"] = 3
    elif case == "wrong-omissions":
        p["graph"]["omissions"] = ["a", "b", "c", "d"]
    elif case == "short-context-table":
        c = b["coefficients"]
        c["position_count"] = 16
        c["cos_bits"].pop()
        c["sin_bits"].pop()
        seal(c, "coefficients_hash")
        h = c["coefficients_hash"]
        b["intent"]["position_encoding"]["coefficients_hash"] = h
        for point in b["points"]:
            point["graph"]["kv_key_encoding"]["coefficients_hash"] = h
            for group in point["graph"]["groups"]:
                for op in group["ops"]:
                    if op["rotary"] is not None:
                        op["rotary"]["coefficients_hash"] = h
    elif case not in ("wrong-intent-hash", "wrong-point-hash"):
        raise ValueError(case)
    rehash(b)
    if case == "wrong-intent-hash":
        b["intent_hash"] = sha256(b"wrong intent")
        seal(b, "bundle_hash")
    if case == "wrong-point-hash":
        p["payload_hash"] = sha256(b"wrong point")
        seal(b, "bundle_hash")
    return b
