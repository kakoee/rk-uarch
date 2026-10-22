"""Reference policy for the existing component mapper and TaskGraph vocabulary.

Stable four-owner tiling; explicit local transfers and supplied logical HBM spans.
This prepares work and never computes elapsed time.
"""

from __future__ import annotations

from collections import defaultdict
from math import prod
from typing import Any

from uarch_contract.reference import ReferenceBundle, ReferenceSource
from uarch_contract.reference_json import content_hash
from uarch_contract.reference_laws import DOTS, WIDTH, accesses

from rkuarch.workload.reference import sealed


def primitive(
    kind: Any,
    r: Any,
    c: Any,
    *,
    leading: Any = 1,
    repeat: Any = 1,
    source: Any = None,
    dest: Any = None,
) -> dict[str, Any]:
    return dict(
        kind=kind,
        rows=r,
        cols=c,
        leading=leading,
        repeat=repeat,
        source_dtype=source,
        destination_dtype=dest,
    )


def vector_program(operator: Any, r: Any, c: Any) -> Any:
    def cast(source: str, dest: str, rows: int = r, cols: int = c) -> dict[str, Any]:
        return primitive("cast", rows, cols, source=source, dest=dest)

    def ordinary(kind: str, rows: int = r, cols: int = c, repeat: int = 1) -> dict[str, Any]:
        return primitive(kind, rows, cols, repeat=repeat)

    if operator == "normalization":
        return [
            cast("bf16", "fp32"),
            cast("bf16", "fp32", 1, c),
            ordinary("multiply"),
            ordinary("reduction_sum"),
            ordinary("multiply", r, 1),
            ordinary("add", r, 1),
            ordinary("rsqrt", r, 1),
            ordinary("multiply", repeat=2),
            cast("fp32", "bf16"),
        ]
    if operator == "residual_addition":
        return [
            primitive("cast", r, c, repeat=2, source="bf16", dest="fp32"),
            ordinary("add"),
            cast("fp32", "bf16"),
        ]
    if operator == "activation":
        return [
            primitive("cast", r, c, repeat=2, source="bf16", dest="fp32"),
            ordinary("negate"),
            ordinary("exp"),
            ordinary("add"),
            ordinary("reciprocal"),
            ordinary("multiply", repeat=2),
            cast("fp32", "bf16"),
        ]
    if operator == "rotary_embedding":
        # Split halves remain independent vectors: multiply twice and add/subtract once per element.
        return [
            cast("bf16", "fp32"),
            ordinary("multiply", r, c // 2, repeat=4),
            ordinary("add", r, c // 2),
            ordinary("subtract", r, c // 2),
            cast("fp32", "bf16"),
        ]
    if operator == "softmax":
        return [
            ordinary("multiply"),
            ordinary("select"),
            ordinary("reduction_max"),
            ordinary("subtract"),
            ordinary("exp"),
            ordinary("reduction_sum"),
            ordinary("reciprocal", r, 1),
            ordinary("multiply"),
            cast("fp32", "bf16"),
        ]
    if operator == "scalar_add":
        return [ordinary("add")]
    raise ValueError(operator)


class Builder:
    def __init__(
        self,
        source: ReferenceSource,
        assumptions: dict[str, Any],
        *,
        spill_accumulator: bool = False,
    ) -> None:
        self.source = source
        self.spill_accumulator = spill_accumulator
        self.a = assumptions
        self.buffers: dict[str, Any] = {}
        self.jobs: list[dict[str, Any]] = []
        self.edges: set[tuple[str, str]] = set()
        self.coverage: list[dict[str, Any]] = []
        self.offsets: defaultdict[str, int] = defaultdict(int)
        self.serial = 0
        self.op_ends: dict[str, list[str]] = {}
        self.outputs: dict[str, str] = {}
        self.owner_ends: list[list[str]] = [[] for _ in range(4)]
        self.caches: dict[str, str] = {}
        self.decoder_input: str | None = None

    def buffer(
        self,
        name: Any,
        size: Any,
        dtype: Any,
        space: Any = "hbm",
        *,
        operand: Any = None,
        op: Any = None,
        layout: Any = "contiguous",
        accumulator: Any = False,
        persistent: Any = False,
    ) -> Any:
        if name in self.buffers:
            if size > self.buffers[name]["size_bytes"]:
                raise ValueError("fixed scratch slot too small")
            return name
        offset = (self.offsets[space] + 63) // 64 * 64
        self.offsets[space] = offset + size
        self.buffers[name] = dict(
            id=name,
            space=space,
            size_bytes=size,
            alignment_bytes=64,
            core_id=0 if space != "hbm" else None,
            channel_id=None,
            offset_bytes=offset,
            bank=None,
            op_id=op,
            operand=operand,
            slot_index=None,
            initial_residency="preloaded" if space == "hbm" or persistent else "uninitialized",
            producer_id=None,
            final_consumer_ids=[],
            dtype=dtype,
            persistent=persistent,
            layout=layout,
            accumulator=accumulator,
        )
        return name

    def range(self, name: Any, size: Any = None, offset: Any = 0) -> Any:
        return dict(
            buffer_id=name,
            offset_bytes=offset,
            size_bytes=self.buffers[name]["size_bytes"] if size is None else size,
        )

    def task(self, kind: Any, op: Any, depends: Any = (), **fields: Any) -> Any:
        name = f"t{self.serial:08d}"
        self.serial += 1
        self.jobs.append(dict(kind=kind, id=name, op_id=op, **fields))
        self.edges.update((d, name) for d in depends)
        return name

    def dma(
        self,
        op: Any,
        src: Any,
        dst: Any,
        size: Any,
        depends: Any = (),
        *,
        so: Any = 0,
        do: Any = 0,
        spans: Any = None,
    ) -> Any:
        spans = spans or [
            dict(source_offset_bytes=so, destination_offset_bytes=do, payload_bytes=size)
        ]

        def bound(name: Any, end: Any) -> Any:
            lo = min(s[end + "_offset_bytes"] for s in spans)
            hi = max(s[end + "_offset_bytes"] + s["payload_bytes"] for s in spans)
            return self.range(name, hi - lo, lo)

        return self.task(
            "dma",
            op,
            depends,
            dma_engine_id=0,
            direction="read" if self.buffers[src]["space"] == "hbm" else "write",
            source=bound(src, "source"),
            destination=bound(dst, "destination"),
            payload_bytes=size,
            spans=spans,
        )

    def local(self, op: Any, buf: Any, size: Any, depends: Any, purpose: Any = "partial") -> Any:
        return self.task(
            "local_transfer",
            op,
            depends,
            source=self.range(buf, size),
            destination=self.range(buf, size),
            purpose=purpose,
        )

    def vector(
        self, op: Any, member: Any, primitives: Any, inputs: Any, outputs: Any, depends: Any
    ) -> Any:
        return self.task(
            "vector",
            op,
            depends,
            member=member,
            core_id=0,
            primitives=primitives,
            inputs=inputs,
            outputs=outputs,
            scratch_bytes=65536,
        )

    def slots(self) -> Any:
        chunk = self.a["matrix_m_chunk"]
        raw_int8 = all(
            o.spec.operator in DOTS and o.spec.operands["X"].dtype == "int8"
            for o in self.source.ops
        )
        partial_dtype = "int32" if raw_int8 else "fp32"
        operand_dtype = "int8" if raw_int8 else "bf16"
        for owner in range(4):
            self.buffer(
                f"acc{owner}",
                self.a["accumulator_window_bytes"],
                partial_dtype,
                "vmem",
                accumulator=True,
            )
            self.buffer(f"out{owner}", chunk * 128 * 4, partial_dtype, "vmem")
            for slot in range(2):
                self.buffer(f"x{owner}.{slot}", chunk * 128 * 2, operand_dtype, "vmem")
                self.buffer(f"w{owner}.{slot}", 128 * 128 * 2, operand_dtype, "vmem")
        self.buffer("scratch", 65536, "fp32", "vmem")
        for x in ("vx", "vw", "vy"):
            self.buffer(x, 16 * 1024 * 1024, "fp32", "vmem")
        for x in ("stream0", "stream1"):
            self.buffer(x, 65536, "bf16", "vmem")

    def matrix(
        self,
        op: Any,
        m: Any,
        k: Any,
        n: Any,
        precision: Any,
        depends: Any,
        *,
        member: Any = "dot",
        leading: Any = 0,
        final_dtype: Any = None,
        inputs: Any = None,
        output: Any = None,
        causal: Any = False,
    ) -> Any:
        width = WIDTH[precision]
        outdtype = final_dtype or ("int32" if precision == "int8" else "bf16")
        outwidth = WIDTH[outdtype]
        prefix = f"{op}.{member}.{leading}"
        x, w = inputs or (
            self.buffer(
                prefix + ".X", m * k * width, precision, operand="X", op=op, layout="tile-packed"
            ),
            self.buffer(
                prefix + ".W", k * n * width, precision, operand="W", op=op, layout="tile-packed"
            ),
        )
        # Decoder activations are row-major. Pack a supplied X once per operator;
        # every gather and materialization has ordinary HBM/VMEM traffic.
        if self.buffers[x]["layout"] != "tile-packed":
            packed = self.buffer(
                prefix + ".packed_X", m * k * width, precision, op=op, layout="tile-packed"
            )
            pack_ends = list(depends)
            for row in range(0, m, self.a["matrix_m_chunk"]):
                rows = min(self.a["matrix_m_chunk"], m - row)
                for col in range(0, k, 128):
                    cols = min(128, k - col)
                    spans = [
                        dict(
                            source_offset_bytes=((row + r) * k + col) * width,
                            destination_offset_bytes=r * cols * width,
                            payload_bytes=cols * width,
                        )
                        for r in range(rows)
                    ]
                    read = self.dma(op, x, "vx", rows * cols * width, pack_ends, spans=spans)
                    write = self.dma(
                        op,
                        "vx",
                        packed,
                        rows * cols * width,
                        [read],
                        do=(row * k + col * rows) * width,
                    )
                    pack_ends = [write]
            x = packed
            depends = pack_ends
        y = output or self.buffer(prefix + ".Y", m * n * outwidth, outdtype, operand="Y", op=op)
        ends: list[str] = []
        index = 0
        for mi in range(0, m, self.a["matrix_m_chunk"]):
            mr = min(self.a["matrix_m_chunk"], m - mi)
            for ni in range(0, n, 128):
                nr = min(128, n - ni)
                owner = index % 4
                index += 1
                tiledeps = list(dict.fromkeys(list(depends) + self.owner_ends[owner]))
                previous: list[str] = []
                bank = [tiledeps, tiledeps]
                acc = f"acc{owner}"
                out = f"out{owner}"
                part = mr * nr * 4
                for ki in range(0, k, 128):
                    kr = min(128, k - ki)
                    slot = (ki // 128) % 2
                    xb = f"x{owner}.{slot}"
                    wb = f"w{owner}.{slot}"
                    xr = self.dma(
                        op, x, xb, mr * kr * width, bank[slot], so=(mi * k + ki * mr) * width
                    )
                    wr = self.dma(
                        op, w, wb, kr * nr * width, bank[slot], so=(ni * k + ki * nr) * width
                    )
                    partial = [] if not previous else [self.local(op, acc, part, previous)]
                    origin = dict(M=mi, K=ki, N=ni)
                    extent = dict(M=mr, K=kr, N=nr)
                    valid = None
                    if causal:
                        # QK uses the output triangle; AV carries the mask on K positions.
                        valid = (
                            sum(max(0, min(nr, mi + r - ni + 1)) for r in range(mr))
                            if member == "qk"
                            else sum(max(0, min(kr, mi + r - ki + 1)) for r in range(mr))
                        )
                    task = self.task(
                        "compute",
                        op,
                        [xr, wr] + partial + previous,
                        group_id=None,
                        repeat_index=0,
                        core_id=0,
                        engine="matrix",
                        matrix_engine_index=owner,
                        tile_origin=origin,
                        tile_extents=extent,
                        physical_extents=dict(M=mr, K=128, N=128),
                        operand_buffers=dict(X=xb, W=wb, Y=out),
                        operand_dtypes=dict(X=precision, W=precision, Y=outdtype),
                        accumulator_buffer_id=acc,
                        accumulator_dtype="int32" if precision == "int8" else "fp32",
                        dataflow="output_stationary",
                        valid_pairs=valid,
                        member=member,
                        leading_index=leading,
                    )
                    self.coverage.append(
                        dict(
                            job_id=task,
                            op_id=op,
                            group_id=None,
                            repeat_index=0,
                            tile_origin=origin,
                            tile_extents=extent,
                        )
                    )
                    previous = [self.local(op, acc, part, [task])]
                    if self.spill_accumulator and ki + kr < k:
                        spill = self.buffer(
                            prefix + f".spill.{mi}.{ni}",
                            part,
                            "int32" if precision == "int8" else "fp32",
                            op=op,
                        )
                        write_spill = self.dma(op, acc, spill, part, previous)
                        read_spill = self.dma(op, spill, acc, part, [write_spill])
                        previous = [read_spill]
                    bank[slot] = [task]
                read = self.task(
                    "local_transfer",
                    op,
                    previous,
                    source=self.range(acc, part),
                    destination=self.range(out, part),
                    purpose="partial",
                )
                if outdtype == "bf16":
                    final = self.vector(
                        op,
                        "output_cast",
                        [primitive("cast", mr, nr, source="fp32", dest="bf16")],
                        [self.range(out, part)],
                        [self.range(out, mr * nr * outwidth)],
                        [read],
                    )
                else:
                    final = read
                output_spans = (
                    [
                        dict(
                            source_offset_bytes=r * nr * outwidth,
                            destination_offset_bytes=((mi + r) * n + ni) * outwidth,
                            payload_bytes=nr * outwidth,
                        )
                        for r in range(mr)
                    ]
                    if nr != n
                    else None
                )
                store = self.dma(
                    op,
                    out,
                    y,
                    mr * nr * outwidth,
                    [final],
                    do=mi * n * outwidth,
                    spans=output_spans,
                )
                ends.append(store)
                self.owner_ends[owner] = [store]
        return y, ends

    def simple_vector(self, o: Any, depends: Any) -> Any:
        spec = o["spec"]
        d = spec["dimensions"]
        typ = spec["operator"]
        op = o["id"]
        if typ == "rotary_embedding":
            r = d["B"] * d["S"] * d["H"]
            c = d["R"]
        else:
            r, c = d.get("M", 1), d.get("D", 1)
        inputs = []
        read = []
        for idx, (name, value) in enumerate(spec["operands"].items()):
            if name == "Y":
                continue
            size = prod(d[x] for x in value["dimensions"]) * WIDTH[value["dtype"]]
            buf = self.buffer(op + "." + name, size, value["dtype"], operand=name, op=op)
            prior = None
            if typ == "activation" and len(o["depends_on"]) == 2:
                prior = o["depends_on"][1 if name == "X" else 0]
            elif name == "X" and o["depends_on"]:
                prior = o["depends_on"][0]
            elif typ == "residual_addition" and name == "W":
                if len(o["depends_on"]) > 1:
                    prior = o["depends_on"][1]
                elif self.decoder_input is not None:
                    buf = self.decoder_input
            if prior in self.outputs and self.buffers[self.outputs[prior]]["size_bytes"] == size:
                buf = self.outputs[prior]
            if typ == "normalization" and not o["depends_on"] and name == "X":
                self.decoder_input = buf
            local = "vx" if idx == 0 else "vw"
            read.append(self.dma(op, buf, local, size, depends))
            inputs.append(self.range(local, size))
        if typ == "rotary_embedding":
            assert self.source.coefficients is not None
            coef = self.buffer(
                "coefficients",
                self.source.coefficients.position_count * self.source.coefficients.rotary_dim * 4,
                "fp32",
                operand="coefficients",
            )
            size = d["S"] * d["R"] * 4
            read.append(
                self.dma(op, coef, "vw", size, depends, so=self.source.context_before * d["R"] * 4)
            )
            inputs.append(self.range("vw", size))
        size = r * c * (4 if typ == "scalar_add" else 2)
        y = self.buffer(
            op + ".Y", size, "fp32" if typ == "scalar_add" else "bf16", operand="Y", op=op
        )
        v = self.vector(op, typ, vector_program(typ, r, c), inputs, [self.range("vy", size)], read)
        return y, [self.dma(op, "vy", y, size, [v])]

    def memory(self, o: Any, depends: Any) -> Any:
        d = o["spec"]["dimensions"]
        typ = o["spec"]["operator"]
        op = o["id"]
        e = d["E"]
        size = e * 2
        x = self.buffer(op + ".X", 2 if typ == "stream_fill" else size, "bf16", operand="X", op=op)
        y = self.buffer(
            op + ".Y",
            4 if typ == "stream_read_sum" else size,
            "fp32" if typ == "stream_read_sum" else "bf16",
            operand="Y",
            op=op,
        )
        ends: list[str] = []
        slots = [list(depends), list(depends)]
        partials = []
        for i, start in enumerate(range(0, size, 65536)):
            length = min(65536, size - start)
            local = f"stream{i % 2}"
            before = slots[i % 2]
            read = self.dma(
                op,
                x,
                local,
                2 if typ == "stream_fill" else length,
                before,
                so=0 if typ == "stream_fill" else start,
            )
            if typ == "stream_copy":
                last = self.dma(op, local, y, length, [read], do=start)
            else:
                if typ == "stream_fill":
                    program = [primitive("broadcast", 1, length // 2)]
                else:
                    program = [
                        primitive("cast", 1, length // 2, source="bf16", dest="fp32"),
                        primitive("reduction_sum", 1, length // 2),
                    ]
                v = self.vector(
                    op,
                    typ,
                    program,
                    [self.range(local, 2 if typ == "stream_fill" else length)],
                    [self.range(local, length if typ == "stream_fill" else 4)],
                    [read],
                )
                if typ == "stream_fill":
                    last = self.dma(op, local, y, length, [v], do=start)
                else:
                    partial = self.buffer(op + f".partial{i}", 4, "fp32", "vmem")
                    last = self.task(
                        "local_transfer",
                        op,
                        [v],
                        source=self.range(local, 4),
                        destination=self.range(partial, 4),
                        purpose="materialization",
                    )
                    partials.append(partial)
            slots[i % 2] = [last]
            ends.append(last)
        if typ == "stream_read_sum":
            v = self.vector(
                op,
                "chunk_sum",
                [primitive("reduction_sum", 1, len(partials))],
                [self.range(x) for x in partials],
                [self.range("vy", 4)],
                ends,
            )
            ends = [self.dma(op, "vy", y, 4, [v])]
        return y, ends

    def kv(self, o: Any, depends: Any) -> Any:
        op = o["id"]
        d = o["spec"]["dimensions"]
        typ = o["spec"]["operator"]
        b = d.get("B", 1)
        t = d["T"]
        p = d["P"]
        h = d["H"]
        depth = d["D"]
        head_bytes = depth * 2
        token = h * head_bytes
        pages = (t + p - 1) // p
        allocated = b * pages * p * token
        valid = b * t * token
        append = typ == "kv_write"
        count = b * d["S"] * token if append else valid
        self.buffer(
            op + ".indices", pages * 4, "int32", "smem", persistent=True, op=op, operand="indices"
        )
        index_input = self.buffer(op + ".index_input", pages * 4, "int32", operand="indices", op=op)
        index_read = self.dma(op, index_input, "vw", pages * 4, depends)
        lookup = self.task(
            "control",
            op,
            [index_read],
            instructions=pages,
            page_entries=list(self.source.page_indices),
        )
        ends: list[str] = []
        y = None
        for which in ("K", "V"):
            cache = self.buffer(
                op + "." + which, allocated, "bf16", operand=which + "_cache", op=op, layout="paged"
            )
            self.caches[which] = cache
            payload = self.buffer(
                op + "." + which + ".payload",
                count,
                "bf16",
                operand=which if append else which + "_out",
                op=op,
            )
            if append and len(o["depends_on"]) == 2:
                payload = self.outputs[o["depends_on"][0 if which == "K" else 1]]
            before = ends[-1:] or [lookup]
            for batch in range(b):
                first = self.source.context_before if append else 0
                for page in range(first // p, pages):
                    lo = max(first, page * p)
                    hi = min(t, (page + 1) * p)
                    physical = self.source.page_indices[page]
                    # Page payload layout [head, token-in-page, D]. Valid tails exclude padding.
                    for head in range(h):
                        size = (hi - lo) * head_bytes
                        cache_offset = (
                            (batch * pages + physical) * p * h + head * p + lo % p
                        ) * head_bytes
                        # Projections use [batch, S, head, D]; spans preserve each token.
                        if append:
                            spans = [
                                dict(
                                    source_offset_bytes=(
                                        (batch * d["S"] + token_index - first) * h + head
                                    )
                                    * head_bytes,
                                    destination_offset_bytes=(token_index - lo) * head_bytes,
                                    payload_bytes=head_bytes,
                                )
                                for token_index in range(lo, hi)
                            ]
                            r = self.dma(op, payload, "stream0", size, before, spans=spans)
                            end = self.dma(op, "stream0", cache, size, [r], do=cache_offset)
                        else:
                            r = self.dma(op, cache, "stream0", size, before, so=cache_offset)
                            spans = [
                                dict(
                                    source_offset_bytes=(token_index - lo) * head_bytes,
                                    destination_offset_bytes=((batch * t + token_index) * h + head)
                                    * head_bytes,
                                    payload_bytes=head_bytes,
                                )
                                for token_index in range(lo, hi)
                            ]
                            end = self.dma(op, "stream0", payload, size, [r], spans=spans)
                        before = [end]
            ends.extend(before)
            y = payload
        return y, ends

    def attention_inputs(self, op: Any, d: Any, depends: Any) -> Any:
        pages = (d["T"] + d["P"] - 1) // d["P"]
        head_bytes = d["D"] * 2
        page_bytes = d["P"] * d["H"] * head_bytes
        prepared = {}
        ends = list(depends)
        self.buffer(
            op + ".indices", pages * 4, "int32", "smem", persistent=True, op=op, operand="indices"
        )
        index_input = self.buffer(op + ".index_input", pages * 4, "int32", operand="indices", op=op)
        read = self.dma(op, index_input, "vw", pages * 4, ends)
        lookup = self.task(
            "control", op, [read], instructions=pages, page_entries=list(self.source.page_indices)
        )
        ends = [lookup]
        for which in ("K", "V"):
            cache = self.caches.get(which)
            if cache is None:
                cache = self.buffer(
                    op + ".cache." + which,
                    d["B"] * pages * page_bytes,
                    "bf16",
                    operand=which,
                    op=op,
                    layout="paged",
                )
            for batch in range(d["B"]):
                for head in range(d["H"]):
                    packed = self.buffer(
                        f"{op}.packed.{which}.{batch}.{head}",
                        d["T"] * head_bytes,
                        "bf16",
                        operand=which,
                        op=op,
                        layout="tile-packed",
                    )
                    prepared[which, batch, head] = packed
                    for page in range(pages):
                        length = min(d["P"], d["T"] - page * d["P"]) * head_bytes
                        offset = (
                            batch * pages + self.source.page_indices[page]
                        ) * page_bytes + head * d["P"] * head_bytes
                        r = self.dma(op, cache, "stream0", length, ends, so=offset)
                        w = self.dma(
                            op, "stream0", packed, length, [r], do=page * d["P"] * head_bytes
                        )
                        ends = [w]
        return prepared, ends

    def attention(self, o: Any, depends: Any) -> Any:
        op = o["id"]
        d = o["spec"]["dimensions"]
        ends: list[str] = []
        all_outputs = []
        kv, depends = self.attention_inputs(op, d, depends)
        for b in range(d["B"]):
            for head in range(d["Hq"]):
                idx = b * d["Hq"] + head
                q = self.buffer(
                    f"{op}.Q.{idx}",
                    d["S"] * d["D"] * 2,
                    "bf16",
                    operand="Q",
                    op=op,
                    layout="tile-packed",
                )
                if o["depends_on"] and o["depends_on"][0] in self.outputs:
                    original = self.outputs[o["depends_on"][0]]
                    spans = [
                        dict(
                            source_offset_bytes=((b * d["S"] + token) * d["Hq"] + head)
                            * d["D"]
                            * 2,
                            destination_offset_bytes=token * d["D"] * 2,
                            payload_bytes=d["D"] * 2,
                        )
                        for token in range(d["S"])
                    ]
                    read = self.dma(op, original, "vx", d["S"] * d["D"] * 2, depends, spans=spans)
                    write = self.dma(op, "vx", q, d["S"] * d["D"] * 2, [read])
                    depends = [write]
                key_head = head // (d["Hq"] // d["H"])
                qk, qends = self.matrix(
                    op,
                    d["S"],
                    d["D"],
                    d["T"],
                    "bf16",
                    depends,
                    member="qk",
                    leading=idx,
                    final_dtype="fp32",
                    inputs=(q, kv["K", b, key_head]),
                    causal=d["S"] == d["T"],
                )
                r = self.dma(op, qk, "vx", d["S"] * d["T"] * 4, qends)
                prob = self.buffer(f"{op}.prob.{idx}", d["S"] * d["T"] * 2, "bf16", op=op)
                soft = self.vector(
                    op,
                    "softmax",
                    vector_program("softmax", d["S"], d["T"]),
                    [self.range("vx", d["S"] * d["T"] * 4)],
                    [self.range("vy", d["S"] * d["T"] * 2)],
                    [r],
                )
                store = self.dma(op, "vy", prob, d["S"] * d["T"] * 2, [soft])
                val = kv["V", b, key_head]
                y, aends = self.matrix(
                    op,
                    d["S"],
                    d["T"],
                    d["D"],
                    "bf16",
                    [store],
                    member="av",
                    leading=idx,
                    inputs=(prob, val),
                    causal=d["S"] == d["T"],
                )
                ends.extend(aends)
                all_outputs.append(y)
                depends = aends  # Explicit scratch reuse between heads, no free score retention.
        y = self.buffer(
            op + ".O", d["B"] * d["S"] * d["Hq"] * d["D"] * 2, "bf16", operand="O", op=op
        )
        # Output layout join has explicit read/write traffic.
        offset = 0
        joined = []
        for part in all_outputs:
            size = self.buffers[part]["size_bytes"]
            r = self.dma(op, part, "vx", size, ends)
            head_index = offset // size
            batch = head_index // d["Hq"]
            head = head_index % d["Hq"]
            spans = [
                dict(
                    source_offset_bytes=token * d["D"] * 2,
                    destination_offset_bytes=((batch * d["S"] + token) * d["Hq"] + head)
                    * d["D"]
                    * 2,
                    payload_bytes=d["D"] * 2,
                )
                for token in range(d["S"])
            ]
            w = self.dma(op, "vx", y, size, [r], spans=spans)
            joined.append(w)
            ends = [w]
            offset += size
        return y, joined

    def finish(self) -> Any:
        self.slots()
        prior: list[str] = []
        for item in self.source.ops:
            o = item.model_dump(mode="json")
            op = o["id"]
            typ = o["spec"]["operator"]
            d = o["spec"]["dimensions"]
            deps = list(
                dict.fromkeys(prior + [x for p in o["depends_on"] for x in self.op_ends[p]])
            )
            if typ in DOTS:
                inputs = None
                if o["depends_on"]:
                    candidate = self.outputs[o["depends_on"][0]]
                    if self.buffers[candidate]["size_bytes"] == d["M"] * d["K"] * 2:
                        weight = self.buffer(
                            op + ".W",
                            d["K"] * d["N"] * 2,
                            "bf16",
                            operand="W",
                            op=op,
                            layout="tile-packed",
                        )
                        inputs = (candidate, weight)
                y, ends = self.matrix(
                    op,
                    d["M"],
                    d["K"],
                    d["N"],
                    o["spec"]["operands"]["X"]["dtype"],
                    deps,
                    inputs=inputs,
                )
            elif typ.startswith("stream_"):
                y, ends = self.memory(o, deps)
            elif typ in {"kv_write", "paged_gather"}:
                y, ends = self.kv(o, deps)
            elif typ == "attention_fused":
                y, ends = self.attention(o, deps)
            else:
                y, ends = self.simple_vector(o, deps)
            self.outputs[op] = y
            self.op_ends[op] = ends
            prior = ends
        users = defaultdict(list)
        writers = defaultdict(list)
        for j in self.jobs:
            reads, writes = accesses(j)
            for name, _, _ in reads + writes:
                users[name].append(j["id"])
            for name, _, _ in writes:
                writers[name].append(j["id"])
        for name, b in self.buffers.items():
            if writers[name]:
                b["producer_id"] = writers[name][0]
                if not (
                    b["layout"] == "paged" and b["operand"] and b["operand"].endswith("_cache")
                ):
                    b["initial_residency"] = "uninitialized"
            b["final_consumer_ids"] = sorted(set(users[name]))
            if b["persistent"]:
                control = next(
                    j for j in self.jobs if j["kind"] == "control" and j["op_id"] == b["op_id"]
                )
                b["producer_id"] = control["id"]
                b["initial_residency"] = "uninitialized"

        return sealed(
            dict(
                format="uarch-taskgraph/2",
                buffers=sorted(self.buffers.values(), key=lambda x: x["id"]),
                jobs=self.jobs,
                dependencies=[dict(before=x, after=y) for x, y in sorted(self.edges)],
                coverage=self.coverage,
                routes=[],
                arbitration="fifo-ready/1",
            ),
            "graph_hash",
        )


def map_reference(
    source: Any,
    hardware: Any,
    *,
    priming_iterations: Any = 1,
    test_only: Any = False,
    assumptions: Any = None,
    spill_accumulator: bool = False,
) -> ReferenceBundle:
    assumptions = assumptions or sealed(
        dict(
            revision="tpu-v5e-premeasurement/3",
            hbm_budget_bytes=12_000_000_000,
            vmem_budget_bytes=96 * 1024**2,
            smem_budget_bytes=512 * 1024,
            accumulator_window_bytes=512 * 1024,
            transient_scratch_bytes=65536,
            max_request_bytes=8192,
            matrix_m_chunk=1024,
            matrix_kn_slice=128,
            vector_rows=8,
            vector_cols=128,
            reload_policy="payload-every-invocation",
            limitations=[
                "Unvalidated STUB timing",
                "Compiler mapping and device event boundary unobserved",
                "Tile-packed matrix HBM layout; explicit score/probability materialization "
                "and BF16 AV probability conversion",
                "Register/bank/channel/energy behavior unrepresented",
            ],
        ),
        "assumptions_hash",
    )
    graph = Builder(source, assumptions, spill_accumulator=spill_accumulator).finish()
    point = sealed(
        dict(
            point_id="reference",
            task_graph=graph,
            initial_state="steady" if priming_iterations else "cold",
            priming_iterations=priming_iterations,
        ),
        "payload_hash",
    )
    return ReferenceBundle.model_validate(
        sealed(
            dict(
                format="uarch-prepared/5",
                producer=dict(name="rk-uarch", version="0.0.1"),
                hardware_spec=hardware.model_dump(mode="json"),
                hardware_spec_hash=content_hash(hardware),
                assumptions=assumptions,
                assumptions_hash=assumptions["assumptions_hash"],
                rank=dict(
                    collectives="excluded",
                    equivalent_ranks=[0],
                    kind="balanced_tp_representative",
                    rank_index=0,
                    tp=1,
                ),
                mapping_scope="task_graph",
                mapping_policy=dict(name="ws-rowsplit", version="3", buffer_depth=2),
                source=source.model_dump(mode="json"),
                admission=dict(
                    checkpoint="R",
                    invocation="test" if test_only else "production",
                    eligibility="verification_only" if test_only else "reference_suite",
                ),
                points=[point],
            ),
            "bundle_hash",
        )
    )
