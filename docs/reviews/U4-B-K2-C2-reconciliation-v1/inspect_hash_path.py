"""Static observations from independently rebuilt, byte-identical binaries."""

import collections
import hashlib
import json
import re
from pathlib import Path

R = Path("/tmp/u4-b-c2-review")
records = {}
for mode in ("debug", "release"):
    asm = (R / f"repeat/receipts/{mode}-objdump.stdout").read_text()
    sections = {}
    names = {}
    current = None
    for line in asm.splitlines():
        m = re.match(r"^([0-9a-f]+) <(.+)>:$", line)
        if m:
            current = int(m[1], 16)
            sections[current] = []
            names[current] = m[2]
        elif current is not None:
            sections[current].append(line)
    slots = {}
    for line in (R / f"repeat/receipts/{mode}-relocations.stdout").read_text().splitlines():
        m = re.match(r"\s*([0-9a-f]+)\s+[0-9a-f]+\s+R_X86_64_RELATIVE\s+([0-9a-f]+)\s*$", line)
        if m:
            slots[int(m[1], 16)] = int(m[2], 16)
    edges = collections.defaultdict(list)
    for address, lines in sections.items():
        for line in lines:
            direct = re.search(r"\b(?:call|jmp)\s+([0-9a-f]+)\s+<", line)
            pointer = re.search(r"#\s*([0-9a-f]+)\s+<", line)
            dest = None
            kind = None
            if direct:
                dest = int(direct[1], 16)
                kind = "direct call/jump"
            elif pointer:
                dest = slots.get(int(pointer[1], 16))
                kind = "relocated pointer call/load"
            if dest in names and dest != address:
                edges[address].append((dest, kind, line.strip()))
    boundary = next(a for a, n in names.items() if n == "c2_sha256_boundary")
    compress = next(a for a, n in names.items() if n == "sha2::sha256::compress256")
    todo = collections.deque([boundary])
    paths = {boundary: []}
    while todo:
        src = todo.popleft()
        for dest, kind, line in edges[src]:
            if dest not in paths:
                paths[dest] = paths[src] + [
                    {"from": names[src], "to": names[dest], "kind": kind, "instruction": line}
                ]
                todo.append(dest)
    assert compress in paths
    selected = []
    for address, name in names.items():
        if name != "c2_sha256_boundary" and not name.startswith("sha2::sha256::"):
            continue
        lines = sections[address]
        simd = [line.strip() for line in lines if re.search(r"%(?:xmm|ymm|zmm|mm)\d", line)]
        if name.startswith("sha2::sha256::"):
            assert not simd
        selected.append(
            {
                "name": name,
                "address": hex(address),
                "simd_register_lines": len(simd),
                "reachable_static": address in paths,
            }
        )
    packing = [
        line.strip()
        for line in sections[boundary]
        if re.search(r"\b(?:punpckhbw|punpcklbw|pshuflw|pshufhw|packuswb)\b", line)
    ]
    if mode == "release":
        assert len(packing) == 14
        assert slots[0x9FB48] == 0x4C9A0 == compress
    records[mode] = {
        "binary_sha256": hashlib.sha256(
            (R / f"repeat/target/{mode}/c2-probe").read_bytes()
        ).hexdigest(),
        "boundary_to_compress": paths[compress],
        "selected_symbols": selected,
        "boundary_packed_transformations": packing,
        "static_reachable_count": len(paths),
        "limitation": (
            "Static direct calls/jumps and relocated pointer references; "
            "loads need actual use inspection. Not exhaustive dynamic tracing "
            "or arbitrary indirect/libc analysis."
        ),
    }
(R / "output/hash-path.json").write_text(json.dumps(records, indent=2) + "\n")
print("Static paths verified; release has 14 packed transformations in the digest boundary.")
