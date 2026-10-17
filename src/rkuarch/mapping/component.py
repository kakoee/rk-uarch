"""Deterministic ws-rowsplit@1 component placement; no timing or execution.

256-row chunks go to cores 0..3. Each tile gets two disjoint, aligned SRAM
slots; only its first slot is populated. HBM storage is distinct per tile and
operand (including replicated W). Accumulator scratch is shared only for an
identical footprint on the same exclusive matrix owner. Different footprints
reserve disjoint storage under @1. Explicit @2 requires the proposed lifetime contract:
heterogeneous cores use exact-size transient scratch and ordered compute dependencies.
The default @1 bytes and identical-footprint persistent convention are unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.mapped import PRODUCTION_HARDWARE, TaskGraph, canonical_owners, require
from uarch_contract.prepared import PreparedOp, validate_prepared_op

POLICY_NAME = "ws-rowsplit"
POLICY_VERSION = "1"
BUFFER_DEPTH = 2


def _align(value: int) -> int:
    return (value + 255) // 256 * 256


def _ops(ops: Sequence[PreparedOp]) -> tuple[PreparedOp, ...]:
    result = tuple(
        sorted(
            (PreparedOp.model_validate(x.model_dump(mode="json")) for x in ops), key=lambda x: x.id
        )
    )
    require(1 <= len(result) <= 16, "UnsupportedScope", "1..16 component operations")
    ids = {x.id for x in result}
    require(len(ids) == len(result), "InvalidCoverage", "duplicate operator ID")
    for op in result:
        require(op.spec.operator == "q_projection", "UnsupportedOperator", op.id)
        require(
            all(x.dtype == "bf16" for x in op.spec.operands.values()), "UnsupportedPrecision", op.id
        )
        require(set(op.spec.dimensions) == {"M", "K", "N"}, "UnsupportedShape", op.id)
        d = op.spec.dimensions
        require(
            1 <= d["M"] <= 1024 and 1 <= d["K"] <= 256 and 1 <= d["N"] <= 256,
            "UnsupportedShape",
            op.id,
        )
        require(not op.padding, "UnsupportedShape", "imported padding")
        require(
            op.work_repeat == op.weight_copies == 1
            and not op.replication
            and op.fusion == "none"
            and op.kv_access is None
            and op.embedding_local_tokens is None
            and all(x.layout == "contiguous" for x in op.spec.operands.values()),
            "UnsupportedCapability",
            op.id,
        )
        require(set(op.operand_access) == {"X", "W", "Y"}, "InvalidCoverage", "operand access")
        validate_prepared_op(op)
        require(
            set(op.depends_on) <= ids
            and op.id not in op.depends_on
            and len(set(op.depends_on)) == len(op.depends_on),
            "InvalidDependency",
            op.id,
        )
    done: set[str] = set()
    while len(done) < len(result):
        ready = {x.id for x in result if x.id not in done and set(x.depends_on) <= done}
        require(bool(ready), "InvalidDependency", "operator cycle")
        done.update(ready)
    return result


def map_component(
    ops: Sequence[PreparedOp],
    hardware_spec: HardwareSpec,
    *,
    initial_state: str = "cold",
    mapping_version: str = "1",
) -> TaskGraph:
    """Map existing operators. Resident output is explicitly verification-only input.

    This pure function neither constructs a profile nor grants admission. Assembly and
    saved-input admission are separate APIs. Refuse capacity, never retile or spill.
    """
    require(mapping_version in ("1", "2"), "UnsupportedMapping")
    operations = _ops(ops)
    if mapping_version == "2":
        # Stable topological order prevents new serialization edges reversing op dependencies.
        pending = list(operations)
        ordered_ops = []
        done: set[str] = set()
        while pending:
            selected = next(op for op in pending if set(op.depends_on) <= done)
            pending.remove(selected)
            ordered_ops.append(selected)
            done.add(selected.id)
        operations = tuple(ordered_ops)
    spec = HardwareSpec.model_validate(hardware_spec.model_dump(mode="json"))
    require(spec_hash(spec) == PRODUCTION_HARDWARE, "UnsupportedHardware")
    require(initial_state in ("cold", "fixture_resident"), "UnsupportedInitialState")
    resident = initial_state == "fixture_resident"
    raw = spec.model_dump(mode="json")
    core = raw["cores"]["core_type"]
    cols = int(raw["cores"]["grid"]["cols"]["value"])
    ncores = cols * int(raw["cores"]["grid"]["rows"]["value"])
    engines = int(core["dma"]["engines"]["value"])
    sram_bytes = int(core["sram"]["bytes"]["value"])
    bank_bytes = sram_bytes // int(core["sram"]["banks"]["value"])
    acc_bytes = int(core["matrix_engine"]["accumulator_bytes"]["value"])
    buffers: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    routes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()
    sram_ends = [0] * ncores
    acc_ends = [0] * ncores
    acc_ids: dict[tuple[int, int], str] = {}
    hbm_end = 0
    prefixes = {op.id: f"o{i:03}" for i, op in enumerate(sorted(operations, key=lambda x: x.id))}
    footprints: dict[int, set[int]] = {}
    for op in operations:
        for tile_index, start in enumerate(range(0, op.spec.dimensions["M"], 256)):
            size = 4 * min(256, op.spec.dimensions["M"] - start) * op.spec.dimensions["N"]
            footprints.setdefault(tile_index, set()).add(size)
    transient_cores = {c for c, sizes in footprints.items() if len(sizes) > 1}
    last_compute: dict[int, str] = {}
    joined = {name for op in operations for name in op.depends_on}

    def buffer(
        key: str,
        space: str,
        size: int,
        offset: int,
        core_id: int | None,
        operand: str | None,
        op_id: str | None,
        slot: int | None,
        preloaded: bool,
        producer: str | None,
        consumers: list[str],
    ) -> None:
        capacity = (
            sram_bytes
            if space == "sram"
            else acc_bytes
            if space == "accumulator"
            else int(raw["memory"]["dram"]["capacity_bytes"]["value"])
        )
        require(
            offset + size <= capacity,
            "SramCapacityExceeded" if space == "sram" else "CapacityExceeded",
            f"{space} core={core_id} {key}: requested end {offset + size}; available {capacity}",
        )
        buffers.append(
            dict(
                id=key,
                space=space,
                size_bytes=size,
                alignment_bytes=256,
                core_id=core_id,
                channel_id=None,
                offset_bytes=offset,
                bank=offset // bank_bytes if space == "sram" else None,
                op_id=op_id,
                operand=operand,
                slot_index=slot,
                initial_residency="preloaded" if preloaded else "uninitialized",
                producer_id=producer,
                final_consumer_ids=consumers,
            )
        )

    def route(core_id: int, channel: int) -> str:
        attach = raw["memory"]["controllers"][channel // 2]["attach"]
        dest = attach[0] * cols + attach[1]
        key = f"r{core_id:03}-{dest:03}"
        if key not in routes:
            path, current = [core_id], core_id
            while current % cols != dest % cols:
                current += 1 if current % cols < dest % cols else -1
                path.append(current)
            while current // cols != dest // cols:
                current += cols if current < dest else -cols
                path.append(current)
            routes[key] = dict(
                id=key, noc_index=0, source_core_id=core_id, destination_core_id=dest, core_ids=path
            )
        return key

    for op in operations:
        terminal: list[str] = []
        roots: list[str] = []
        d = op.spec.dimensions
        for tile_index, start in enumerate(range(0, d["M"], 256)):
            core_id, m = tile_index, min(256, d["M"] - start)
            require(core_id < ncores, "InvalidResource", "row split core")
            prefix = f"{prefixes[op.id]}.t{tile_index:03}"
            compute_id = prefix + ".2-compute"
            names = ["X", "W", "Y"]
            sizes = [2 * m * d["K"], 2 * d["K"] * d["N"], 2 * m * d["N"]]
            require(
                sizes[0] + sizes[1] <= core["matrix_engine"]["operand_buffer_bytes"]["value"],
                "CapacityExceeded",
                "operand buffer",
            )
            slot_size = sum(_align(x) for x in sizes)
            base = sram_ends[core_id]
            sram_ends[core_id] += 2 * slot_size
            sr_ids: dict[str, str] = {}
            sr_offset = base
            for i, (name, size) in enumerate(zip(names, sizes, strict=True)):
                sr_id = prefix + f".s{i}-{name}"
                sr_ids[name] = sr_id
                dma_id = prefix + (".3-write-Y" if name == "Y" else f".{i}-read-{name}")
                producer = compute_id if name == "Y" else None if resident else dma_id
                consumers = ([dma_id] if not resident else []) if name == "Y" else [compute_id]
                buffer(
                    sr_id,
                    "sram",
                    size,
                    sr_offset,
                    core_id,
                    name,
                    op.id,
                    0,
                    resident and name != "Y",
                    producer,
                    consumers,
                )
                sr_offset += _align(size)
                if resident:
                    continue
                hbm_id = prefix + f".h{i}-{name}"
                buffer(
                    hbm_id,
                    "hbm",
                    size,
                    hbm_end,
                    None,
                    name,
                    op.id,
                    None,
                    name != "Y",
                    dma_id if name == "Y" else None,
                    [] if name == "Y" else [dma_id],
                )
                fragments: list[dict[str, Any]] = []
                cursor = 0
                while cursor < size:
                    address = hbm_end + cursor
                    payload = min(size - cursor, 256 - address % 256)
                    channel = address // 256 % 8
                    fragments.append(
                        dict(
                            request_id=f"{dma_id}.r{len(fragments):06}",
                            source_offset_bytes=cursor,
                            destination_offset_bytes=cursor,
                            payload_bytes=payload,
                            transaction_bytes=256,
                            channel_id=channel,
                            route_id=route(core_id, channel),
                        )
                    )
                    cursor += payload
                hbm_end = _align(hbm_end + size)
                source, dest = (sr_id, hbm_id) if name == "Y" else (hbm_id, sr_id)
                jobs.append(
                    dict(
                        kind="dma",
                        id=dma_id,
                        op_id=op.id,
                        dma_engine_id=core_id * engines + (1 if name == "W" else 0),
                        direction="write" if name == "Y" else "read",
                        source=dict(buffer_id=source, offset_bytes=0, size_bytes=size),
                        destination=dict(buffer_id=dest, offset_bytes=0, size_bytes=size),
                        fragments=fragments,
                    )
                )
                if name == "Y":
                    edges.add((compute_id, dma_id))
                    terminal.append(dma_id)
                else:
                    edges.add((dma_id, compute_id))
                    roots.append(dma_id)
            buffer(
                prefix + ".s3-reserved",
                "sram",
                slot_size,
                base + slot_size,
                core_id,
                None,
                op.id,
                1,
                False,
                None,
                [],
            )
            acc_size = 4 * m * d["N"]
            acc_key = (core_id, acc_size)
            transient = mapping_version == "2" and core_id in transient_cores
            if transient:
                acc_id = prefix + ".acc"
                acc_ids[acc_key] = acc_id
                buffer(
                    acc_id,
                    "accumulator",
                    acc_size,
                    0,
                    core_id,
                    None,
                    None,
                    None,
                    False,
                    compute_id,
                    [compute_id],
                )
                if core_id in last_compute:
                    edges.add((last_compute[core_id], compute_id))
                last_compute[core_id] = compute_id
            elif acc_key not in acc_ids:
                acc_id = f"acc.c{core_id:03}.b{acc_size:06}"
                acc_ids[acc_key] = acc_id
                buffer(
                    acc_id,
                    "accumulator",
                    acc_size,
                    acc_ends[core_id],
                    core_id,
                    None,
                    None,
                    None,
                    False,
                    None,
                    [],
                )
                acc_ends[core_id] += _align(acc_size)
            origin = dict(M=start, K=0, N=0)
            extent = dict(M=m, K=d["K"], N=d["N"])
            jobs.append(
                dict(
                    kind="compute",
                    id=compute_id,
                    op_id=op.id,
                    group_id=None,
                    repeat_index=0,
                    core_id=core_id,
                    engine="matrix",
                    tile_origin=origin,
                    tile_extents=extent,
                    physical_extents=dict(M=m, K=256, N=256),
                    operand_buffers=sr_ids,
                    operand_dtypes=dict(X="bf16", W="bf16", Y="bf16"),
                    accumulator_buffer_id=acc_ids[acc_key],
                    accumulator_dtype="fp32",
                    dataflow="weight_stationary",
                )
            )
            coverage.append(
                dict(
                    job_id=compute_id,
                    op_id=op.id,
                    group_id=None,
                    repeat_index=0,
                    tile_origin=origin,
                    tile_extents=extent,
                )
            )
            if resident:
                terminal.append(compute_id)
                roots.append(compute_id)
        for dependency in op.depends_on:
            edges.update((prefixes[dependency] + ".join", root) for root in roots)
        if op.id in joined:
            join = prefixes[op.id] + ".join"
            jobs.append(
                dict(kind="barrier", id=join, participant_job_ids=sorted(terminal), owner_id=0)
            )
            edges.update((last, join) for last in terminal)
    data: dict[str, Any] = dict(
        format="uarch-taskgraph/1",
        buffers=sorted(buffers, key=lambda x: x["id"]),
        jobs=sorted(jobs, key=lambda x: x["id"]),
        dependencies=[dict(before=a, after=z) for a, z in sorted(edges)],
        coverage=sorted(coverage, key=lambda x: x["job_id"]),
        routes=sorted(routes.values(), key=lambda x: x["id"]),
        arbitration="fifo-ready/1",
    )
    data["graph_hash"] = content_hash(data)
    graph = TaskGraph.model_validate(data)
    owners = {x.resource: x.owner_id for x in canonical_owners(spec, graph)}
    for job in data["jobs"]:
        if job["kind"] == "barrier":
            job["owner_id"] = owners["barrier:" + job["id"]]
    data["graph_hash"] = content_hash(data, exclude=("graph_hash",))
    return TaskGraph.model_validate(data)
