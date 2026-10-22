"""Finite R input laws. No producer imports, timing scheduler or device claims."""

from collections import Counter, defaultdict, deque
from typing import Any

from .mapped import require

WIDTH = {"bf16": 2, "fp32": 4, "int8": 1, "int32": 4}
DOTS = {
    "q_projection",
    "k_projection",
    "v_projection",
    "output_projection",
    "ffn_up",
    "ffn_gate",
    "ffn_down",
}


def validate_hardware(h: Any) -> Any:
    for k, v in h.items():
        if k in {"identity", "design_status"}:
            continue
        require(v["kind"] == "claim" and v["value"] > 0, "UnsupportedHardware", k)
        unit = (
            "count"
            if k.endswith(("_count", "_rows", "_cols", "_outstanding"))
            else "byte"
            if k.endswith("_capacity_bytes")
            else "MAC/s"
            if k.endswith("_mac_per_s")
            else "op/s"
            if k.endswith("_ops_per_s")
            else "byte/s"
            if k.endswith("_bytes_per_s")
            else "ps"
            if k.endswith("_ps")
            else "ratio"
            if k.endswith("_ratio")
            else "MAC-equivalent"
        )
        require(v["unit"] == unit, "UnsupportedHardware", k + " unit")
        if k.endswith(("_count", "_rows", "_cols", "_bytes", "_outstanding")):
            require(
                v["value"].is_integer()
                if isinstance(v["value"], float)
                else isinstance(v["value"], int),
                "UnsupportedHardware",
                k,
            )
    require(
        [h[k]["value"] for k in ("tensorcore_count", "mxu_count", "mxu_rows", "mxu_cols")]
        == [1, 4, 128, 128],
        "UnsupportedHardware",
    )
    for p in ("bf16", "int8"):
        require(
            8 * h[p + "_mxu_mac_per_s"]["value"] <= h[p + "_peak_ops_per_s"]["value"],
            "UnsupportedHardware",
            "MXU share",
        )


def dag(ids: Any, edges: Any) -> Any:
    indegree = {x: 0 for x in ids}
    successors = defaultdict(list)
    require(len(indegree) == len(ids), "InvalidDependency", "duplicate id")
    require(len(set(edges)) == len(edges), "InvalidDependency", "duplicate edge")
    for a, b in edges:
        require(a in indegree and b in indegree and a != b, "InvalidDependency")
        successors[a].append(b)
        indegree[b] += 1
    queue = deque(x for x in ids if not indegree[x])
    order = []
    while queue:
        x = queue.popleft()
        order.append(x)
        for y in successors[x]:
            indegree[y] -= 1
            if indegree[y] == 0:
                queue.append(y)
    require(len(order) == len(ids), "InvalidDependency", "cycle")
    return order, successors


def validate_source(s: Any) -> Any:
    require(s["attention_mask"] == "causal", "UnsupportedScope", "R selected causal scope")
    ops = s["ops"]
    for op in ops:
        kind = op["spec"]["operator"]
        axes = (
            {"M", "K", "N"}
            if kind in DOTS
            else {"M", "D"}
            if kind in {"normalization", "residual_addition", "activation", "scalar_add"}
            else {"B", "S", "H", "D", "R"}
            if kind == "rotary_embedding"
            else {"E", "One"}
            if kind in {"stream_read_sum", "stream_fill", "stream_copy"}
            else {"B", "S", "T", "H", "D", "P"}
            if kind == "paged_gather"
            else {"B", "S", "T", "Hq", "H", "D", "P"}
            if kind in {"kv_write", "attention_fused"}
            else set()
        )
        require(
            bool(axes) and set(op["spec"]["dimensions"]) == axes,
            "InvalidCoverage",
            "operator dimensions",
        )
    kinds = {op["spec"]["operator"] for op in ops}
    scalar = s["scalar_inputs"]
    expected = set()
    if "normalization" in kinds:
        expected.add("rmsnorm_epsilon")
        require(scalar.get("rmsnorm_epsilon", 0) > 0, "InvalidCoverage", "RMSNorm epsilon")
    if "attention_fused" in kinds:
        expected.add("attention_scale")
        depth = next(
            op["spec"]["dimensions"]["D"]
            for op in ops
            if op["spec"]["operator"] == "attention_fused"
        )
        require(scalar.get("attention_scale") == depth**-0.5, "InvalidCoverage", "attention scale")
    if any(op["spec"]["operands"].get("X", {}).get("dtype") == "int8" for op in ops):
        expected.update(("raw_int8_min", "raw_int8_max"))
        require(
            scalar.get("raw_int8_min") == -7 and scalar.get("raw_int8_max") == 7,
            "UnsupportedPrecision",
            "raw INT8 bounds",
        )
    require(set(scalar) == expected, "InvalidCoverage", "numerical source inputs")
    validate_operator_inputs(s)
    ids = [o["id"] for o in ops]
    dag(ids, [(d, o["id"]) for o in ops for d in o["depends_on"]])
    require(all(o["work_repeat"] == o["weight_copies"] == 1 for o in ops), "UnsupportedScope")
    for o in ops:
        spec = o["spec"]
        dims = spec["dimensions"]
        operands = spec["operands"]
        typ = spec["operator"]
        limits = dict(
            M=4096,
            K=14336,
            N=14336,
            B=32,
            S=2049,
            T=2049,
            Hq=32,
            H=32,
            D=14336,
            R=128,
            P=32,
            E=134217728,
            One=1,
        )
        require(
            all(k in limits and value <= limits[k] for k, value in dims.items()),
            "UnsupportedShape",
            "bounded reference dimensions",
        )
        require(set(operands) == set(o["operand_access"]), "InvalidCoverage")
        if typ in DOTS:
            require(
                set(dims) == {"M", "K", "N"} and set(operands) == {"X", "W", "Y"}, "InvalidCoverage"
            )
            p = operands["X"]["dtype"]
            require(p in {"bf16", "int8"} and operands["W"]["dtype"] == p, "UnsupportedPrecision")
            require(
                operands["Y"]["dtype"] == ("int32" if p == "int8" else "bf16"),
                "UnsupportedPrecision",
            )
            if p == "int8":
                require(dims["K"] <= 4096, "UnsupportedShape", "raw INT8 range [-7,7]")
        if typ == "rotary_embedding":
            r = o["rotary"]
            c = s["coefficients"]
            require(
                r is not None and c is not None and r["input_op_id"] in o["depends_on"],
                "InvalidCoverage",
            )
            require(
                r["coefficients_hash"]
                == c["coefficients_hash"]
                == s["kv_key_encoding"]["coefficients_hash"],
                "CoefficientHashMismatch",
            )
            require(dims["R"] == c["rotary_dim"] == dims["D"], "InvalidCoverage")
            require(
                r["position_ids"]
                == [list(range(s["context_before"], s["context_after"])) for _ in range(dims["B"])]
                and s["context_after"] - s["context_before"] == dims["S"]
                and s["context_after"] <= c["position_count"],
                "InvalidCoverage",
                "positions",
            )
            producer = next(x for x in ops if x["id"] == r["input_op_id"])
            require(
                producer["spec"]["operator"] == r["target"] + "_projection"
                and producer["spec"]["dimensions"]["N"] == dims["H"] * dims["D"]
                and producer["spec"]["dimensions"]["M"] == dims["B"] * dims["S"],
                "InvalidCoverage",
                "rotary projection join",
            )
        if o["kv_access"]:
            kv = o["kv_access"]
            t = dims["T"]
            p = dims["P"]
            require(
                kv["context_tokens"] == t
                and kv["pages_per_sequence"] == (t + p - 1) // p
                and kv["last_page_valid_tokens"] == (t - 1) % p + 1,
                "InvalidCoverage",
                "KV tail",
            )
        if typ in {"paged_gather", "kv_write", "attention_fused"}:
            count = (dims["T"] + dims["P"] - 1) // dims["P"]
            require(
                sorted(s["page_indices"]) == list(range(count)),
                "InvalidCoverage",
                "page permutation",
            )
    if s["scope"] == "decoder":
        validate_decoder(s)
        require(
            Counter(o["spec"]["operator"] for o in ops)
            == Counter(
                dict(
                    normalization=2,
                    residual_addition=2,
                    q_projection=1,
                    k_projection=1,
                    v_projection=1,
                    rotary_embedding=2,
                    kv_write=1,
                    attention_fused=1,
                    output_projection=1,
                    ffn_up=1,
                    ffn_gate=1,
                    activation=1,
                    ffn_down=1,
                )
            ),
            "MissingCoverage",
            "complete decoder work",
        )
        targets = Counter(o["rotary"]["target"] for o in ops if o["rotary"])
        require(targets == Counter(q=1, k=1), "InvalidCoverage", "Q/K only")


def validate_graph(g: Any) -> Any:
    jobs = {j["id"]: j for j in g["jobs"]}
    buffers = {b["id"]: b for b in g["buffers"]}
    require(
        len(jobs) == len(g["jobs"]) and len(buffers) == len(g["buffers"]),
        "InvalidCoverage",
        "duplicate",
    )
    dag(list(jobs), [(e["before"], e["after"]) for e in g["dependencies"]])
    computes = {k: v for k, v in jobs.items() if v["kind"] == "compute"}
    require(
        set(computes) == {c["job_id"] for c in g["coverage"]}
        and len(computes) == len(g["coverage"]),
        "InvalidCoverage",
    )
    for c in g["coverage"]:
        require(
            all(
                c[k] == computes[c["job_id"]][k]
                for k in ("op_id", "group_id", "repeat_index", "tile_origin", "tile_extents")
            ),
            "InvalidCoverage",
        )
    for j in jobs.values():
        ranges = []
        if j["kind"] in {"dma", "local_transfer"}:
            ranges = [j["source"], j["destination"]]
            if j["kind"] == "local_transfer":
                require(
                    j["source"]["size_bytes"] == j["destination"]["size_bytes"], "InvalidTransfer"
                )
            if j["kind"] == "dma":
                require(
                    sum(x["payload_bytes"] for x in j["spans"]) == j["payload_bytes"],
                    "InvalidTransfer",
                    "span coverage",
                )
                for span in j["spans"]:
                    for end in ("source", "destination"):
                        b = buffers[j[end]["buffer_id"]]
                        require(
                            j[end]["offset_bytes"] <= span[end + "_offset_bytes"]
                            and span[end + "_offset_bytes"] + span["payload_bytes"]
                            <= j[end]["offset_bytes"] + j[end]["size_bytes"]
                            <= b["size_bytes"],
                            "InvalidTransfer",
                            "tail",
                        )
        elif j["kind"] == "vector":
            ranges = j["inputs"] + j["outputs"]
            for p in j["primitives"]:
                pair = (p["source_dtype"], p["destination_dtype"])
                require(
                    pair in {("bf16", "fp32"), ("fp32", "bf16")}
                    if p["kind"] == "cast"
                    else pair == (None, None),
                    "UnsupportedPrecision",
                    "primitive conversion",
                )
        elif j["kind"] == "compute":
            require(
                all(
                    x in buffers
                    for x in list(j["operand_buffers"].values()) + [j["accumulator_buffer_id"]]
                ),
                "InvalidResource",
            )
            require(
                j["physical_extents"] == dict(M=j["tile_extents"]["M"], K=128, N=128),
                "InvalidCoverage",
                "physical tile",
            )
        for r in ranges:
            require(
                r["buffer_id"] in buffers
                and r["offset_bytes"] + r["size_bytes"] <= buffers[r["buffer_id"]]["size_bytes"],
                "InvalidResource",
                "range",
            )
    for b in buffers.values():
        require(
            b["core_id"] in {None, 0} and b["channel_id"] is None and b["bank"] is None,
            "InvalidResource",
        )
        require(
            not b["persistent"] or b["space"] == "smem",
            "InvalidResource",
            "persistent metadata only",
        )
        require(b["producer_id"] is None or b["producer_id"] in jobs, "InvalidResource")
        require(set(b["final_consumer_ids"]) <= jobs.keys(), "InvalidResource")


def validate_bundle(b: Any) -> Any:
    validate_reference_transfers(b)
    validate_math_coverage(b)
    validate_lifetimes(b["points"][0]["task_graph"])
    validate_output_coverage(b["points"][0]["task_graph"])
    require(
        b["rank"]
        == dict(
            collectives="excluded",
            equivalent_ranks=[0],
            kind="balanced_tp_representative",
            rank_index=0,
            tp=1,
        ),
        "UnsupportedRankScope",
    )
    a = b["assumptions"]
    h = b["hardware_spec"]
    g = b["points"][0]["task_graph"]
    for space in ("hbm", "vmem", "smem"):
        budget = a[space + "_budget_bytes"]
        require(budget <= h[space + "_capacity_bytes"]["value"], "CapacityExceeded", space)
        # Allocations use disjoint addresses; mapper reuses actual named scratch slots.
        spans = sorted(
            (x["offset_bytes"], x["offset_bytes"] + x["size_bytes"])
            for x in g["buffers"]
            if x["space"] == space
        )
        require(all(lo >= 0 and hi <= budget for lo, hi in spans), "CapacityExceeded", space)
        require(
            all(x[1] <= y[0] for x, y in zip(spans, spans[1:], strict=False)),
            "LiveBufferAlias",
            space,
        )
    ops = {o["id"]: o for o in b["source"]["ops"]}
    byop = defaultdict(list)
    for j in g["jobs"]:
        require(j["op_id"] in ops, "InvalidCoverage")
        byop[j["op_id"]].append(j)
    require(byop.keys() == ops.keys(), "MissingCoverage")
    for op_id, op in ops.items():
        if op["spec"]["operator"] not in DOTS:
            continue
        dims = op["spec"]["dimensions"]
        tiles = [j for j in byop[op_id] if j["kind"] == "compute"]
        expected = {
            (m, k, n): (
                min(a["matrix_m_chunk"], dims["M"] - m),
                min(128, dims["K"] - k),
                min(128, dims["N"] - n),
            )
            for m in range(0, dims["M"], a["matrix_m_chunk"])
            for n in range(0, dims["N"], 128)
            for k in range(0, dims["K"], 128)
        }
        actual = {
            tuple(j["tile_origin"][x] for x in ("M", "K", "N")): tuple(
                j["tile_extents"][x] for x in ("M", "K", "N")
            )
            for j in tiles
        }
        require(
            len(tiles) == len(actual) and actual == expected, "InvalidCoverage", "dot partition"
        )
        for j in tiles:
            precision = op["spec"]["operands"]["X"]["dtype"]
            require(
                j["accumulator_dtype"] == ("int32" if precision == "int8" else "fp32")
                and j["operand_dtypes"]["X"] == j["operand_dtypes"]["W"] == precision,
                "UnsupportedPrecision",
                "mapped dot precision",
            )
            require(
                4 * j["tile_extents"]["M"] * j["tile_extents"]["N"]
                <= a["accumulator_window_bytes"],
                "CapacityExceeded",
                "accumulator",
            )


def primitive_totals(tasks: Any) -> Any:
    counts: Counter[str] = Counter()
    for j in tasks:
        if j["kind"] != "vector":
            continue
        for p in j["primitives"]:
            r, c = p["rows"], p["cols"]
            times = p["leading"] * p["repeat"]
            count = r * (c - 1 if p["kind"].startswith("reduction_") else c) * times
            counts[p["kind"]] += count
    return counts


def expected_primitives(op: Any, source: Any) -> Any:
    spec = op["spec"]
    d = spec["dimensions"]
    typ = spec["operator"]
    r = d.get("M", 1)
    c = d.get("D", 1)
    e = r * c
    if typ in DOTS:
        return Counter(cast=d["M"] * d["N"] if spec["operands"]["X"]["dtype"] == "bf16" else 0)
    if typ == "normalization":
        return Counter(
            cast=2 * e + c, multiply=3 * e + r, reduction_sum=r * (c - 1), add=r, rsqrt=r
        )
    if typ == "residual_addition":
        return Counter(cast=3 * e, add=e)
    if typ == "activation":
        return Counter(cast=3 * e, negate=e, exp=e, add=e, reciprocal=e, multiply=2 * e)
    if typ == "rotary_embedding":
        e = d["B"] * d["S"] * d["H"] * d["R"]
        return Counter(cast=2 * e, multiply=2 * e, add=e // 2, subtract=e // 2)
    if typ == "scalar_add":
        return Counter(add=1)
    if typ == "stream_read_sum":
        return Counter(cast=d["E"], reduction_sum=d["E"] - 1)
    if typ == "stream_fill":
        return Counter(broadcast=d["E"])
    if typ == "attention_fused":
        rows = d["B"] * d["Hq"] * d["S"]
        e = rows * d["T"]
        # QK retains FP32, softmax probability is explicitly rounded for BF16 AV.
        return Counter(
            multiply=2 * e,
            select=e,
            reduction_max=rows * (d["T"] - 1),
            subtract=e,
            exp=e,
            reduction_sum=rows * (d["T"] - 1),
            reciprocal=rows,
            cast=e + rows * d["D"],
        )
    return Counter()


def validate_math_coverage(b: Any) -> Any:
    source = b["source"]
    g = b["points"][0]["task_graph"]
    byop = defaultdict(list)
    for j in g["jobs"]:
        byop[j["op_id"]].append(j)
    for op in source["ops"]:
        tasks = byop[op["id"]]
        actual = primitive_totals(tasks)
        expected = expected_primitives(op, source)
        require(actual == expected, "InvalidCoverage", "typed primitives " + op["id"])
        d = op["spec"]["dimensions"]
        typ = op["spec"]["operator"]
        if typ == "attention_fused":
            tiles = [x for x in tasks if x["kind"] == "compute"]
            seen = set()
            for j in tiles:
                require(
                    j["member"] in {"qk", "av"} and j["leading_index"] < d["B"] * d["Hq"],
                    "InvalidCoverage",
                    "attention member",
                )
                m, k, n = (
                    (d["S"], d["D"], d["T"]) if j["member"] == "qk" else (d["S"], d["T"], d["D"])
                )
                origin = j["tile_origin"]
                ext = j["tile_extents"]
                key = (j["member"], j["leading_index"], *origin.values())
                require(key not in seen, "InvalidCoverage", "duplicate attention tile")
                seen.add(key)
                require(
                    all(
                        origin[x] % step == 0
                        and ext[x] == min(step, limit - origin[x])
                        and origin[x] < limit
                        for x, step, limit in (
                            ("M", b["assumptions"]["matrix_m_chunk"], m),
                            ("K", 128, k),
                            ("N", 128, n),
                        )
                    ),
                    "InvalidCoverage",
                    "attention partition",
                )
                pairs = None
                if d["S"] == d["T"]:
                    axis = "N" if j["member"] == "qk" else "K"
                    pairs = sum(
                        max(0, min(ext[axis], origin["M"] + row - origin[axis] + 1))
                        for row in range(ext["M"])
                    )
                require(j["valid_pairs"] == pairs, "InvalidCoverage", "causal pairs")
            chunks = (d["S"] + b["assumptions"]["matrix_m_chunk"] - 1) // b["assumptions"][
                "matrix_m_chunk"
            ]
            expected_tiles = (
                d["B"] * d["Hq"] * chunks * 2 * ((d["D"] + 127) // 128) * ((d["T"] + 127) // 128)
            )
            require(len(seen) == expected_tiles, "InvalidCoverage", "attention tile coverage")
        elif typ not in DOTS:
            require(
                not any(j["kind"] == "compute" for j in tasks),
                "InvalidCoverage",
                "unexpected matrix work",
            )
        if typ in {"paged_gather", "kv_write"}:
            lookup = [j for j in tasks if j["kind"] == "control"]
            require(
                len(lookup) == 1
                and lookup[0]["page_entries"] == source["page_indices"]
                and lookup[0]["instructions"] == len(source["page_indices"]),
                "InvalidCoverage",
                "page lookup",
            )


def accesses(j: Any) -> Any:
    """Declared byte coverage, preserving holes. Matrix output is the live partial."""
    reads = []
    writes = []

    def r(x: Any) -> Any:
        return (x["buffer_id"], x["offset_bytes"], x["offset_bytes"] + x["size_bytes"])

    if j["kind"] == "dma":
        for span in j["spans"]:
            reads.append(
                (
                    j["source"]["buffer_id"],
                    span["source_offset_bytes"],
                    span["source_offset_bytes"] + span["payload_bytes"],
                )
            )
            writes.append(
                (
                    j["destination"]["buffer_id"],
                    span["destination_offset_bytes"],
                    span["destination_offset_bytes"] + span["payload_bytes"],
                )
            )
    elif j["kind"] == "local_transfer":
        reads = [r(j["source"])]
        writes = [r(j["destination"])]
    elif j["kind"] == "vector":
        reads = list(map(r, j["inputs"]))
        writes = list(map(r, j["outputs"]))
    elif j["kind"] == "compute":
        d = j["tile_extents"]
        width = WIDTH[j["operand_dtypes"]["X"]]
        reads = [
            (j["operand_buffers"]["X"], 0, d["M"] * d["K"] * width),
            (j["operand_buffers"]["W"], 0, d["K"] * d["N"] * width),
        ]
        partial = (j["accumulator_buffer_id"], 0, d["M"] * d["N"] * 4)
        if j["tile_origin"]["K"]:
            reads.append(partial)
        writes = [partial]
    return reads, writes


def validate_lifetimes(g: Any) -> Any:
    from bisect import bisect_left

    jobs = {j["id"]: j for j in g["jobs"]}
    buffers = {b["id"]: b for b in g["buffers"]}
    edges = [(e["before"], e["after"]) for e in g["dependencies"]]
    order, _ = dag(list(jobs), edges)
    rank = {j: i for i, j in enumerate(order)}
    before = defaultdict(list)
    for a, b in edges:
        before[b].append(a)

    # Exact ancestor intervals compress the long sequential reuse chains without
    # retaining a quadratic bit matrix or walking each chain for every byte segment.
    from heapq import merge

    ancestors: dict[str, list[tuple[int, int]]] = {}
    for node in order:
        ancestor_spans: list[tuple[int, int]] = []
        for lo, hi in merge(*(ancestors[p] for p in before[node]), [(rank[node], rank[node])]):
            if ancestor_spans and lo <= ancestor_spans[-1][1] + 1:
                ancestor_spans[-1] = (ancestor_spans[-1][0], max(hi, ancestor_spans[-1][1]))
            else:
                ancestor_spans.append((lo, hi))
        ancestors[node] = ancestor_spans

    def precedes(a: Any, b: Any) -> bool:
        intervals = ancestors[b]
        pos = bisect_left(intervals, (rank[a] + 1,)) - 1
        return pos >= 0 and intervals[pos][0] <= rank[a] <= intervals[pos][1]

    boundaries: defaultdict[str, set[int]] = defaultdict(set)
    uses = {j: accesses(jobs[j]) for j in jobs}
    for read, write in uses.values():
        for name, lo, hi in read + write:
            require(
                name in buffers and 0 <= lo < hi <= buffers[name]["size_bytes"],
                "InvalidResource",
                "access bounds",
            )
            boundaries[name].update((lo, hi))
    points = {b: sorted(xs) for b, xs in boundaries.items()}
    state: dict[str, list[tuple[str | None, set[str]]]] = {
        b: [(None, set()) for _ in range(len(xs) - 1)] for b, xs in points.items()
    }
    for job in order:
        read, write = uses[job]
        for writing, spans in ((False, read), (True, write)):
            for name, lo, hi in spans:
                xs = points[name]
                for i in range(bisect_left(xs, lo), bisect_left(xs, hi)):
                    writer, readers = state[name][i]
                    if writer is not None:
                        require(
                            precedes(writer, job), "InvalidDependency", "buffer producer " + name
                        )
                    elif not writing:
                        require(
                            buffers[name]["initial_residency"] == "preloaded",
                            "InvalidResource",
                            "uninitialized read " + name,
                        )
                    if writing:
                        require(
                            all(precedes(r, job) for r in readers),
                            "LiveBufferAlias",
                            "write before reader " + name,
                        )
                        state[name][i] = (job, set())
                    else:
                        readers.add(job)


def validate_decoder(source: Any) -> Any:
    ops = {o["id"]: o for o in source["ops"]}
    bykind = defaultdict(list)
    for o in ops.values():
        bykind[o["spec"]["operator"]].append(o)

    def names(kind: Any) -> Any:
        return {o["id"] for o in bykind[kind]}

    def require_parents(op: Any, parents: Any) -> Any:
        require(
            set(op["depends_on"]) == parents, "InvalidCoverage", "decoder dependencies " + op["id"]
        )

    norm1 = [o for o in bykind["normalization"] if not o["depends_on"]]
    require(len(norm1) == 1, "InvalidCoverage", "first norm")
    first = norm1[0]["id"]
    norm2 = [o for o in bykind["normalization"] if o["id"] != first]
    require(len(norm2) == 1, "InvalidCoverage", "second norm")
    for kind in ("q_projection", "k_projection", "v_projection"):
        for o in bykind[kind]:
            require_parents(o, {first})
    for kind, parent in (("output_projection", "attention_fused"), ("ffn_down", "activation")):
        for o in bykind[kind]:
            require_parents(o, names(parent))
    for kind in ("ffn_up", "ffn_gate"):
        for o in bykind[kind]:
            require_parents(o, {norm2[0]["id"]})
    for o in bykind["activation"]:
        require_parents(o, names("ffn_up") | names("ffn_gate"))
    rotary = {o["rotary"]["target"]: o["id"] for o in bykind["rotary_embedding"]}
    require(set(rotary) == {"q", "k"}, "InvalidCoverage", "rotary targets")
    for o in bykind["kv_write"]:
        require_parents(o, {rotary["k"]} | names("v_projection"))
    for o in bykind["attention_fused"]:
        require_parents(o, {rotary["q"]} | names("kv_write"))
    residual1 = [
        o for o in bykind["residual_addition"] if set(o["depends_on"]) == names("output_projection")
    ]
    require(len(residual1) == 1, "InvalidCoverage", "first residual")
    require_parents(norm2[0], {residual1[0]["id"]})
    for o in bykind["residual_addition"]:
        if o["id"] != residual1[0]["id"]:
            require_parents(o, names("ffn_down") | {residual1[0]["id"]})


def validate_output_coverage(g: Any) -> Any:
    writes = defaultdict(list)
    for task in g["jobs"]:
        for name, lo, hi in accesses(task)[1]:
            writes[name].append((lo, hi))
    for b in g["buffers"]:
        if b["space"] == "vmem":
            require(
                b["initial_residency"] == "uninitialized",
                "UnsupportedInitialState",
                "VMEM payload reload",
            )
        if b["space"] == "hbm" and b["operand"] in {"Y", "O", "K_out", "V_out"}:
            require(
                b["initial_residency"] == "uninitialized",
                "InvalidResource",
                "output cannot be preloaded",
            )
        if b["space"] == "hbm" and b["initial_residency"] == "uninitialized":
            cursor = 0
            for lo, hi in sorted(writes[b["id"]]):
                require(lo <= cursor, "MissingCoverage", "output hole " + b["id"])
                cursor = max(cursor, hi)
            require(cursor == b["size_bytes"], "MissingCoverage", "output store " + b["id"])


def validate_reference_transfers(b: dict[str, Any]) -> None:
    """Bind page permutation/tails and rotary rows to physical byte spans."""
    g = b["points"][0]["task_graph"]
    buffers = {x["id"]: x for x in g["buffers"]}
    # Each K slice stores one FP32/INT32 partial. Later slices read it back;
    # the final output read supplies the other transfer for the first slice.
    required_partials: Counter[tuple[str, str, int]] = Counter()
    mapped_partials: Counter[tuple[str, str, int]] = Counter()
    for task in g["jobs"]:
        if task["kind"] == "compute":
            d = task["tile_extents"]
            required_partials[
                (task["op_id"], task["accumulator_buffer_id"], 4 * d["M"] * d["N"])
            ] += 2
        elif task["kind"] == "local_transfer" and task["purpose"] == "partial":
            src, dst = task["source"], task["destination"]
            sb, db = buffers[src["buffer_id"]], buffers[dst["buffer_id"]]
            require(
                src["offset_bytes"] == dst["offset_bytes"] == 0
                and src["size_bytes"] == dst["size_bytes"]
                and sb["space"] == db["space"] == "vmem"
                and sb["dtype"] == db["dtype"]
                and sb["dtype"] in {"fp32", "int32"},
                "InvalidTransfer",
                "typed accumulator traffic",
            )
            mapped_partials[(task["op_id"], src["buffer_id"], src["size_bytes"])] += 1
    require(
        mapped_partials == required_partials, "InvalidTransfer", "mandatory accumulator traffic"
    )
    byop: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in g["jobs"]:
        byop[task["op_id"]].append(task)
    for op in b["source"]["ops"]:
        kind = op["spec"]["operator"]
        d = op["spec"]["dimensions"]
        tasks = byop[op["id"]]
        if kind == "rotary_embedding":
            reads = [
                j
                for j in tasks
                if j["kind"] == "dma"
                and buffers[j["source"]["buffer_id"]]["operand"] == "coefficients"
            ]
            require(
                len(reads) == 1
                and reads[0]["payload_bytes"] == d["S"] * d["R"] * 4
                and reads[0]["source"]["offset_bytes"]
                == b["source"]["context_before"] * d["R"] * 4,
                "InvalidTransfer",
                "rotary coefficient row",
            )
        if kind not in {"paged_gather", "kv_write", "attention_fused"}:
            continue
        p, t, heads, depth = d["P"], d["T"], d["H"], d["D"]
        pages = (t + p - 1) // p
        append = kind == "kv_write"
        expected = []
        first = b["source"]["context_before"] if append else 0
        for batch in range(d["B"]):
            order = ((page, head) for page in range(first // p, pages) for head in range(heads))
            if kind == "attention_fused":
                order = ((page, head) for head in range(heads) for page in range(pages))
            for page, head in order:
                lo, hi = max(first, page * p), min(t, (page + 1) * p)
                offset = (
                    (
                        (batch * pages + b["source"]["page_indices"][page]) * p * heads
                        + head * p
                        + lo % p
                    )
                    * depth
                    * 2
                )
                expected.append((offset, (hi - lo) * depth * 2))
        grouped: defaultdict[str, list[tuple[int, int]]] = defaultdict(list)
        for task in tasks:
            if task["kind"] != "dma":
                continue
            end = "destination" if append else "source"
            buffer = buffers[task[end]["buffer_id"]]
            if buffer["layout"] != "paged":
                continue
            spans = task["spans"]
            require(len(spans) == 1, "InvalidTransfer", "page slice")
            grouped[buffer["id"]].append((spans[0][end + "_offset_bytes"], task["payload_bytes"]))
        require(
            len(grouped) == 2 and all(x == expected for x in grouped.values()),
            "InvalidTransfer",
            "page order and valid tail",
        )
        controls = [j for j in tasks if j["kind"] == "control"]
        require(
            len(controls) == 1
            and controls[0]["page_entries"] == b["source"]["page_indices"]
            and controls[0]["instructions"] == pages,
            "InvalidCoverage",
            "page lookup",
        )
        index_reads = [
            j
            for j in tasks
            if j["kind"] == "dma" and buffers[j["source"]["buffer_id"]]["operand"] == "indices"
        ]
        require(
            len(index_reads) == 1 and index_reads[0]["payload_bytes"] == pages * 4,
            "InvalidTransfer",
            "index payload",
        )

        metadata = [x for x in buffers.values() if x["persistent"] and x["op_id"] == op["id"]]
        require(
            len(metadata) == 1
            and metadata[0]["size_bytes"] == pages * 4
            and metadata[0]["producer_id"] == controls[0]["id"]
            and dict(before=index_reads[0]["id"], after=controls[0]["id"]) in g["dependencies"],
            "InvalidCoverage",
            "metadata producer",
        )


def validate_operator_inputs(s: dict[str, Any]) -> None:
    for op in s["ops"]:
        kind = op["spec"]["operator"]
        if kind in DOTS:
            continue
        d = op["spec"]["dimensions"]
        operands = op["spec"]["operands"]
        names = (
            {"X", "W", "Y"}
            if kind in {"normalization", "residual_addition", "activation", "scalar_add"}
            else {"Q", "K", "V", "O"}
            if kind == "attention_fused"
            else {"K", "V", "K_cache", "V_cache"}
            if kind == "kv_write"
            else {"K", "V", "K_out", "V_out"}
            if kind == "paged_gather"
            else {"X", "Y"}
        )
        require(set(operands) == names, "InvalidCoverage", "operator operands")
        for name, operand in operands.items():
            dtype = (
                "fp32"
                if kind == "scalar_add" or (kind == "stream_read_sum" and name == "Y")
                else "bf16"
            )
            require(operand["dtype"] == dtype, "UnsupportedPrecision", "operator operand type")
        if kind in {"attention_fused", "kv_write"}:
            require(
                d["Hq"] % d["H"] == 0
                and d["D"] <= 128
                and d["S"] in {1, d["T"]}
                and s["context_after"] == d["T"]
                and s["context_after"] - s["context_before"] == d["S"],
                "InvalidCoverage",
                "attention/context join",
            )
    if s["scope"] == "decoder":
        att = next(
            o["spec"]["dimensions"] for o in s["ops"] if o["spec"]["operator"] == "attention_fused"
        )
        require(
            (att["Hq"], att["H"], att["D"], att["P"]) == (32, 8, 128, 16),
            "UnsupportedShape",
            "decoder architecture",
        )
        for op in s["ops"]:
            kind = op["spec"]["operator"]
            d = op["spec"]["dimensions"]
            if kind in DOTS:
                require(
                    d
                    == dict(
                        M=att["B"] * att["S"],
                        K=14336 if kind == "ffn_down" else 4096,
                        N=1024
                        if kind in {"k_projection", "v_projection"}
                        else 14336
                        if kind in {"ffn_up", "ffn_gate"}
                        else 4096,
                    ),
                    "InvalidCoverage",
                    "decoder projection shape",
                )
            elif kind in {"normalization", "residual_addition", "activation"}:
                require(
                    d == dict(M=att["B"] * att["S"], D=14336 if kind == "activation" else 4096),
                    "InvalidCoverage",
                    "decoder vector shape",
                )
            elif kind == "kv_write":
                require(d == att, "InvalidCoverage", "decoder cache shape")
