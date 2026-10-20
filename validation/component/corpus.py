"""Prospective B input authoring, independent of A's mapper and timing implementation.

Profiles below are unsigned proposals. They are never launch authority. Public engine,
build, host and final job hashes remain null until a genuine component release exists.
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.mapped import NativeTestProfile, NativeTestRegistry

from rkuarch.verification.component.arithmetic import burst, ceil, dma, resident, split

ROOT = Path(__file__).resolve().parents[2]
REVISION = "B-component-corpus/1"


def read(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / path).read_bytes()))


def seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    value[field] = content_hash(value, exclude=(field,))
    return value


def base(kind: str) -> dict[str, Any]:
    return read("contract/fixtures/mapped/" + kind + ".json")


def graph(bundle: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], bundle["points"][0]["task_graph"])


def variant(b: dict[str, Any], name: str, changes: dict[str, int]) -> None:
    spec = b["hardware_spec"]
    spec["id"] = "u4-b-" + name.lower()
    for path, value in changes.items():
        leaf = spec
        for key in path.split("."):
            leaf = leaf[key]
        leaf.update(
            value=float(value),
            rationale="Verification-only "
            + name
            + ": isolate declared component premise; not a physical hardware claim.",
        )
    b["hardware_spec_hash"] = spec_hash(HardwareSpec.model_validate(spec))


def resident_input(m: int, k: int, n: int) -> dict[str, Any]:
    b = base("resident")
    b["scope"]["ops"][0]["spec"]["dimensions"] = dict(M=m, K=k, N=n)
    g = graph(b)
    c = g["jobs"][0]
    c["tile_extents"] = dict(M=m, K=k, N=n)
    c["physical_extents"]["M"] = m
    g["coverage"][0]["tile_extents"] = dict(c["tile_extents"])
    x, w, y = 2 * m * k, 2 * k * n, 2 * m * n

    def align(z: int) -> int:
        return (z + 255) // 256 * 256

    start_y = align(x) + align(w)
    size = start_y + align(y)
    for buf in g["buffers"]:
        offset, amount = {
            "sx": (0, x),
            "sw": (align(x), w),
            "sy": (start_y, y),
            "slot1": (size, size),
            "acc": (0, 4 * m * n),
        }[buf["id"]]
        buf.update(offset_bytes=offset, size_bytes=amount)
    return b


def two_tiles(same_core: bool = False) -> dict[str, Any]:
    a, tail = resident_input(256, 256, 256), resident_input(1, 256, 256)
    a["scope"]["ops"][0]["spec"]["dimensions"]["M"] = 257
    g, t = graph(a), graph(tail)
    c = t["jobs"][0]
    c.update(id="z", core_id=0 if same_core else 1)
    c["tile_origin"]["M"] = 256
    c["accumulator_buffer_id"] = "zacc"
    c["operand_buffers"] = {k: "z" + v for k, v in c["operand_buffers"].items()}
    for buf in t["buffers"]:
        buf["id"] = "z" + buf["id"]
        buf["core_id"] = c["core_id"]
        if buf["producer_id"] == "c":
            buf["producer_id"] = "z"
        buf["final_consumer_ids"] = ["z" if x == "c" else x for x in buf["final_consumer_ids"]]
        if same_core:
            # Preserve old C04 premise: separate live slots and exact accumulator footprints.
            # Installed exact-size/lifetime semantics refuse this, rather than invent reuse.
            buf["offset_bytes"] += 786432 if buf["space"] == "sram" else 262144
            if buf["space"] == "sram":
                buf["bank"] = buf["offset_bytes"] // 524288
    t["coverage"][0].update(job_id="z", tile_origin=dict(c["tile_origin"]))
    g["buffers"] += t["buffers"]
    g["jobs"] += t["jobs"]
    g["coverage"] += t["coverage"]
    return a


def buffer(
    name: str,
    space: str,
    offset: int,
    size: int,
    producer: str | None,
    consumers: list[str],
    preloaded: bool,
) -> dict[str, Any]:
    return dict(
        id=name,
        space=space,
        size_bytes=size,
        alignment_bytes=256,
        core_id=0 if space == "sram" else None,
        channel_id=None,
        offset_bytes=offset,
        bank=offset // 524288 if space == "sram" else None,
        op_id=None,
        operand=None,
        slot_index=None,
        initial_residency="preloaded" if preloaded else "uninitialized",
        producer_id=producer,
        final_consumer_ids=consumers,
    )


def transport(
    count: int = 1, *, write: bool = False, addresses: list[int] | None = None, size: int = 256
) -> dict[str, Any]:
    b = base("transport")
    b["points"][0]["initial_state"] = "fixture_resident" if write else "cold"
    g = graph(b)
    g.update(buffers=[], jobs=[], dependencies=[], routes=[], coverage=[])
    routes = {}
    for i in range(count):
        name = f"r{i:02}"
        address = addresses[i] if addresses else 1536 + 2048 * i
        offset = address % 256
        hb, sr = name + "h", name + "s"
        g["buffers"] += [
            buffer(
                hb,
                "hbm",
                address - offset,
                size + offset,
                name if write else None,
                [] if write else [name],
                not write,
            ),
            buffer(
                sr, "sram", 1024 * i, size, None if write else name, [name] if write else [], write
            ),
        ]
        src: dict[str, Any] = dict(
            buffer_id=sr if write else hb, offset_bytes=0 if write else offset, size_bytes=size
        )
        dst: dict[str, Any] = dict(
            buffer_id=hb if write else sr, offset_bytes=offset if write else 0, size_bytes=size
        )
        fragments = []
        cursor = 0
        for index, (channel, payload, transaction) in enumerate(split(address, size)):
            dest = channel // 2
            path = {0: [0], 1: [0, 1], 2: [0, 2], 3: [0, 1, 3]}[dest]
            route = f"p{dest}"
            routes[route] = dict(
                id=route, noc_index=0, source_core_id=0, destination_core_id=dest, core_ids=path
            )
            fragments.append(
                dict(
                    request_id=f"{name}.{index:02}",
                    source_offset_bytes=src["offset_bytes"] + cursor,
                    destination_offset_bytes=dst["offset_bytes"] + cursor,
                    payload_bytes=payload,
                    transaction_bytes=transaction,
                    channel_id=channel,
                    route_id=route,
                )
            )
            cursor += payload
        g["jobs"].append(
            dict(
                kind="dma",
                id=name,
                op_id=None,
                dma_engine_id=0,
                direction="write" if write else "read",
                source=src,
                destination=dst,
                fragments=fragments,
            )
        )
    g["routes"] = list(routes.values())
    return b


def cases() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def add(name: str, b: dict[str, Any], **expect: Any) -> None:
        out.append((name, b, dict(outcome="success", **expect)))

    for name, shape in [("C01", (16, 256, 256)), ("C02", (3, 5, 7))]:
        u, i, r, w, acc, duration = resident(*shape)
        add(
            name,
            resident_input(*shape),
            duration_ps=duration,
            useful_ops=u,
            issued_ops=i,
            sram_read_bytes=r,
            sram_write_bytes=w,
            accumulator_bytes=acc,
            hbm_payload_bytes=0,
            useful_floor_ps=ceil(Fraction(u * 1000, 131072)),
        )
    add(
        "C03",
        two_tiles(),
        duration_ps=1182000,
        useful_ops=33685504,
        issued_ops=33685504,
        tile_durations_ps=[1182000, 673000],
    )
    out.append(
        (
            "C04-carrier",
            two_tiles(True),
            dict(
                outcome="CapacityExceeded",
                arithmetic_only_duration_ps=1855000,
                blocker=(
                    "different exact accumulator footprints cannot share full-capacity allocation"
                ),
            ),
        )
    )
    for name, capacity in [("C06-small", 131072), ("C06-fit", 262144)]:
        b = resident_input(256, 256, 256)
        variant(b, name, {"cores.core_type.matrix_engine.accumulator_bytes": capacity})
        out.append(
            (
                name,
                b,
                dict(
                    outcome="CapacityExceeded" if capacity == 131072 else "success",
                    required_accumulator_bytes=262144,
                ),
            )
        )
    # Preserve B remote placement independently of the installed A cold input.
    for name, is_remote in [("C05-B", True), ("C05-A-carrier", False)]:
        b = base("component")
        if is_remote:
            g = graph(b)
            for buf in g["buffers"]:
                if buf["id"] in ("hx", "hw", "hy"):
                    buf["offset_bytes"] = {"hx": 1536, "hw": 3584, "hy": 5632}[buf["id"]]
            for job in g["jobs"]:
                if job["kind"] == "dma":
                    job["fragments"][0].update(channel_id=6, route_id="p3")
            g["routes"] = [
                dict(
                    id="p3",
                    noc_index=0,
                    source_core_id=0,
                    destination_core_id=3,
                    core_ids=[0, 1, 3],
                )
            ]
        add(
            name,
            b,
            duration_ps=669000 if is_remote else 656000,
            useful_ops=210,
            issued_ops=393216,
            read_payload_bytes=100,
            write_payload_bytes=42,
            read_transaction_bytes=512,
            write_transaction_bytes=256,
        )
    b = resident_input(3, 5, 7)
    second = resident_input(3, 5, 7)
    g, t = graph(b), graph(second)
    op = copy.deepcopy(b["scope"]["ops"][0])
    op["id"] = "g1"
    b["scope"]["ops"].append(op)
    b["scope"]["op_ids"].append("g1")
    b["points"][0]["identity"]["op_ids"].append("g1")
    for buf in t["buffers"]:
        if buf["id"] == "acc":
            continue
        buf["id"] = "z" + buf["id"]
        buf["offset_bytes"] += 1536
        buf["op_id"] = "g1"
        buf["producer_id"] = "z" if buf["producer_id"] == "c" else buf["producer_id"]
        buf["final_consumer_ids"] = ["z" if x == "c" else x for x in buf["final_consumer_ids"]]
        g["buffers"].append(buf)
    c = t["jobs"][0]
    c.update(id="z", op_id="g1")
    c["operand_buffers"] = {k: "z" + v for k, v in c["operand_buffers"].items()}
    g["jobs"].append(c)
    cov = t["coverage"][0]
    cov.update(job_id="z", op_id="g1")
    g["coverage"].append(cov)
    add(
        "C04-control",
        b,
        duration_ps=1094000,
        useful_ops=420,
        issued_ops=786432,
        premise="two equal-footprint independent jobs share matrix0 and accumulator; FIFO",
    )
    for space, capacity in [("sram", 16777216), ("hbm", 32000000000)]:
        for extra in (0, 1):
            b = transport()
            graph(b)["buffers"].append(
                buffer("zz-boundary", space, capacity - 256, 256 + extra, None, [], False)
            )
            out.append(
                (
                    f"C07-{space}-{extra}",
                    b,
                    dict(
                        outcome=("SramCapacityExceeded" if space == "sram" else "CapacityExceeded")
                        if extra
                        else "success",
                        capacity_bytes=capacity,
                    ),
                )
            )
    b = resident_input(3, 5, 7)
    remote = transport()
    g, t = graph(b), graph(remote)
    next(x for x in t["buffers"] if x["space"] == "sram")["offset_bytes"] = 2048
    g["buffers"] += t["buffers"]
    g["jobs"] += t["jobs"]
    g["routes"] += t["routes"]
    add(
        "C09-overlap",
        b,
        duration_ps=547000,
        useful_ops=210,
        issued_ops=393216,
        job_times_ps={"c": [0, 547000], "r00": [0, 60000]},
        forbidden_serial_duration_ps=607000,
        premise="independent DMA into disjoint allocation while matrix0 computes resident tile",
    )
    for m in (1, 3, 16, 64, 255, 256):
        for k in (5, 256):
            for n in (7, 256):
                for ratio in (1, 2):
                    b = resident_input(m, k, n)
                    b["points"][0]["frequency_ratio"] = float(ratio)
                    u, i, r, w, acc, duration = resident(m, k, n, core=ratio * 10**9)
                    add(
                        f"C08-{m}-{k}-{n}-r{ratio}",
                        b,
                        duration_ps=duration,
                        useful_ops=u,
                        issued_ops=i,
                        sram_read_bytes=r,
                        sram_write_bytes=w,
                        premise="resident compute only; no DMA; core scales once",
                    )
    add(
        "D01",
        transport(),
        crossings_ps=list(dma()),
        duration_ps=60000,
        attribution_ps=dict(compute=0, overhead=0, sync=0, noc=8750, memory=51250),
    )
    # Old corrected D02/D14 bytes are inputs, preserved without rewrites.
    corrected = "docs/reviews/U4-B-final-reconciliation-v1/fixtures/"
    add(
        "D02",
        read(corrected + "D02.bundle.json"),
        crossings_ps=list(dma(write=True)),
        duration_ps=60000,
    )
    for count, name in [(5, "D03"), (12, "D04")]:
        ends, commits = burst(count)
        add(
            name,
            transport(count),
            channel_end_ps=[ceil(x) for x in ends],
            channel_end_ratios=[[x.numerator, x.denominator] for x in ends],
            complete_ps=commits,
            duration_ps=commits[-1],
        )
    for name, count, cap, issues, completes in [
        ("D05-one", 2, 1, [0, 60000], [60000, 120000]),
        ("D05-two", 2, 2, [0, 0], [60000, 62000]),
        ("D06-two", 3, 2, [0, 0, 60000], [60000, 62000, 120000]),
        ("D06-full", 3, 32, [0, 0, 0], [60000, 62000, 64000]),
    ]:
        b = transport(count)
        if cap != 32:
            variant(b, name, {"cores.core_type.dma.max_outstanding": cap})
        add(name, b, issue_ps=issues, complete_ps=completes, duration_ps=completes[-1])
    add("D07", transport(33), issue_ps=[0] * 32 + [60000], final_inflight=0, max_inflight=32)
    add(
        "D08",
        transport(2, addresses=[1536, 1792]),
        complete_ps=[60000, 61000],
        duration_ps=61000,
        response_ps=[59000, 59000],
    )
    for name, core, noc, dram in [
        ("D09", 10**9, 1200000000, 10**9),
        ("D10", 800000000, 1200000000, 900000000),
    ]:
        for write in (False, True):
            b = transport(write=write)
            variant(
                b,
                name,
                {
                    "clock_domains.core.freq_hz": core,
                    "clock_domains.noc.freq_hz": noc,
                    "clock_domains.dram.freq_hz": dram,
                },
            )
            crossing = dma(core=core, noc=noc, dram=dram, write=write)
            add(
                name + ("-write" if write else "-read"),
                b,
                crossings_ps=list(crossing),
                duration_ps=crossing[-1],
            )
    for name, address, size in [("D11", 1536, 513), ("D12", 1791, 2)]:
        add(
            name,
            transport(addresses=[address], size=size),
            fragments=[list(x) for x in split(address, size)],
            payload_bytes=size,
            transaction_bytes=len(split(address, size)) * 256,
        )
    b = read(corrected + "D14.bundle.json")
    b["hardware_spec"] = base("resident")["hardware_spec"]
    b["hardware_spec_hash"] = base("resident")["hardware_spec_hash"]
    g = graph(b)
    g["jobs"] = [x for x in g["jobs"] if x["kind"] == "noc_transfer"]
    g["buffers"] = [x for x in g["buffers"] if x["id"] in ("ss", "sd")]
    next(x for x in g["buffers"] if x["id"] == "sd")["core_id"] = 3
    g["routes"] = [
        dict(id="r0", noc_index=0, source_core_id=0, destination_core_id=3, core_ids=[0, 1, 3])
    ]
    g["dependencies"] = []
    add("D13-hop", b, duration_ps=4000, unicast_payload_bytes=256)
    b = transport(2)
    g = graph(b)
    g["jobs"].append(dict(kind="barrier", id="z", participant_job_ids=["r00", "r01"], owner_id=44))
    # 4 matrix +4 vector +4 SRAM +8 DMA +4 ports +8 channels +4 routers +8 links =44.
    g["dependencies"] = [dict(before=x, after="z") for x in ("r00", "r01")]
    add("D13-barrier", b, duration_ps=94000, barrier_ready_ps=62000)
    add(
        "D14",
        read(corrected + "D14.bundle.json"),
        duration_ps=61000,
        complete_ps=[60000, 61000, 61000],
        wrong_alignment_ps=61667,
    )
    b = transport()
    variant(b, "D15", {"cores.core_type.dma.bytes_per_cycle": 512})
    add("D15", b, duration_ps=60000)
    return out


def materialize(name: str, b: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    b = copy.deepcopy(b)
    p, g = b["points"][0], graph(b)
    for field, key in [("buffers", "id"), ("jobs", "id"), ("routes", "id"), ("coverage", "job_id")]:
        g[field].sort(key=lambda x: x[key])
    g["dependencies"].sort(key=lambda x: (x["before"], x["after"]))
    seal(g, "graph_hash")
    p["point_id"] = name
    if p["identity"]["kind"] == "fixture":
        p["identity"]["fixture_id"] = name
    seal(p, "payload_hash")
    raw = b["hardware_spec"]
    ratio = p["frequency_ratio"]
    frequencies = {
        k: int(v["freq_hz"]["value"] * (ratio if v["scales_with_core"] else 1))
        for k, v in raw["clock_domains"].items()
    }
    profile = seal(
        dict(
            format="uarch-native-test-profile/1",
            semantics_revision="U0011-stage2/1",
            owner="Lane B agent proposal; unsigned; not first-use authority",
            entries=[
                dict(
                    case_id=name,
                    checkpoint="B",
                    scope=b["scope"]["kind"],
                    initial_state=p["initial_state"],
                    priming_iterations=0,
                    hardware_spec_hash=b["hardware_spec_hash"],
                    hardware_spec=raw,
                    frequency_ratio=ratio,
                    freq_hz=frequencies,
                    graph_hash=g["graph_hash"],
                    point_hash=p["payload_hash"],
                    allowed_job_kinds=sorted({x["kind"] for x in g["jobs"]}),
                    expected_outcome=expected["outcome"],
                    seed=0,
                    case_selection_revision=REVISION,
                    clock_setup_hash=content_hash([]),
                )
            ],
        ),
        "profile_hash",
    )
    NativeTestProfile.model_validate(profile)
    # Reconstruct historical input bytes with their recorded producer metadata.
    # This identifies the archived author, not this fixture helper's current source.
    historical = ROOT / "native/crates/uarch-engine/testdata/synthetic-component-jobs.json"
    b["producer"] = json.loads(historical.read_bytes())["C02"]["workload_closure"]["producer"]
    b["admission"] = dict(
        checkpoint="B",
        invocation="test",
        eligibility="verification_only",
        case_id=name,
        profile_hash=profile["profile_hash"],
    )
    seal(b, "bundle_hash")
    return dict(bundle=b, profile=profile, expected=expected)


def build() -> dict[str, Any]:
    items = {name: materialize(name, b, e) for name, b, e in cases()}
    baseline = base("resident")["hardware_spec_hash"]
    specs = sorted({x["bundle"]["hardware_spec_hash"] for x in items.values()} - {baseline})
    registry = seal(
        dict(
            format="uarch-native-test-registry/1",
            semantics_revision="U0011-stage2/1",
            test_only_specs=[
                dict(
                    hardware_spec_hash=x,
                    rationale="B finite verification-only proposal; no production admission",
                )
                for x in specs
            ],
        ),
        "registry_hash",
    )
    NativeTestRegistry.model_validate(registry)
    return dict(items=items, registry=registry)


def manifest() -> dict[str, Any]:
    corpus = build()
    cells = []
    for name, item in corpus["items"].items():
        b, p = item["bundle"], item["bundle"]["points"][0]
        cells.append(
            dict(
                case_id=name,
                hardware_spec_hash=b["hardware_spec_hash"],
                bundle_hash=b["bundle_hash"],
                graph_hash=p["task_graph"]["graph_hash"],
                point_hash=p["payload_hash"],
                profile_hash=item["profile"]["profile_hash"],
                expected=item["expected"],
                expected_hash=content_hash(item["expected"]),
                job_hash=None,
                engine_identity=None,
                build_identity=None,
                authority=None,
                native_status="not_run",
            )
        )
    return dict(
        revision=REVISION,
        registry_hash=corpus["registry"]["registry_hash"],
        status="unsigned prospective inputs; not a native receipt",
        cases=cells,
    )


if __name__ == "__main__":
    print(json.dumps(manifest(), indent=2, sort_keys=True))
