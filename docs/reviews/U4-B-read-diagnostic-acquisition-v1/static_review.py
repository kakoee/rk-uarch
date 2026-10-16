"""Read saved static-tool output only. No subprocess, network or project imports."""

import argparse
import copy
import hashlib
import json
import pathlib
import re

NAMES = (
    "strace",
    "unwind",
    "unwind-x86_64",
    "unwind-ptrace",
    "unwind-coredump",
    "libc",
    "loader",
    "liblzma",
)


def parse_elf(text):
    assert "Class:                             ELF64" in text
    assert "Machine:                           Advanced Micro Devices X86-64" in text
    assert not re.search(r"\((?:RPATH|RUNPATH)\)", text)
    soname = re.findall(r"\(SONAME\).*\[([^\]]+)\]", text)
    interp = re.findall(r"Requesting program interpreter: ([^\]]+)", text)
    result = {
        "soname": soname[0] if soname else None,
        "interpreter": interp[0] if interp else None,
        "needed": re.findall(r"\(NEEDED\).*\[([^\]]+)\]", text),
        "rpath_runpath": [],
        "version_needs": {},
        "version_definitions": [],
        "exports": [],
        "undefined": [],
    }
    state = None
    provider = None
    rows = 0
    expected_rows = None
    for line in text.splitlines():
        if "Symbol table '.dynsym'" in line:
            expected_rows = int(re.search(r"contains (\d+) entries", line)[1])
        m = re.match(r"\s*\d+:\s+[0-9a-f]+\s+\d+\s+\S+\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(\S+))?", line)
        if m:
            rows += 1
            bind, visibility, index, symbol = m.groups()
            if symbol and bind in {"GLOBAL", "WEAK", "UNIQUE"}:
                if index == "UND":
                    result["undefined"].append({"symbol": symbol, "weak": bind == "WEAK"})
                elif visibility in {"DEFAULT", "PROTECTED"}:
                    result["exports"].append(symbol)
        if line.startswith("Version definition section"):
            state = "definitions"
        if line.startswith("Version needs section"):
            state = "needs"
        if state == "definitions" and "Name:" in line:
            result["version_definitions"].append(re.search(r"Name: (\S+)", line)[1])
        if state == "needs":
            m = re.search(r"File: (\S+)\s+Cnt:", line)
            if m:
                provider = m[1]
                result["version_needs"][provider] = []
            m = re.search(r"Name: (\S+)\s+Flags:", line)
            if m:
                assert provider is not None
                result["version_needs"][provider].append(m[1])
    assert expected_rows is not None and rows == expected_rows, (rows, expected_rows)
    result["dynamic_symbol_rows"] = rows
    return result


def check_closure(objects):
    providers = {x["soname"]: n for n, x in objects.items() if x["soname"]}
    assert len(providers) == len(objects) - 1
    assert objects["strace"]["interpreter"] == "/lib64/ld-linux-x86-64.so.2"
    for n, obj in objects.items():
        for dep in obj["needed"]:
            assert dep in providers, (n, "missing DSO", dep)
        for dep, versions in obj["version_needs"].items():
            assert dep in providers
            defined = objects[providers[dep]]["version_definitions"]
            assert set(versions) <= set(defined), (n, dep, "missing version")
    reachable = {"strace", "loader"}
    pending = list(reachable)
    while pending:
        n = pending.pop()
        for dep in objects[n]["needed"]:
            other = providers[dep]
            if other not in reachable:
                reachable.add(other)
                pending.append(other)
    assert "unwind-coredump" not in reachable
    exports = {}
    for n in sorted(reachable):
        for symbol in objects[n]["exports"]:
            exports.setdefault(symbol.replace("@@", "@"), []).append(n)
            if "@@" in symbol:
                exports.setdefault(symbol.split("@@")[0], []).append(n)
    counts = {}
    bindings = []
    for n, obj in objects.items():
        strong = 0
        weak_unresolved = []
        for row in obj["undefined"]:
            symbol = row["symbol"]
            found = exports.get(symbol, [])
            if not found:
                assert row["weak"], (n, "missing strong symbol", symbol)
                weak_unresolved.append(symbol)
            elif not row["weak"]:
                strong += 1
            bindings.append(
                {"consumer": n, "symbol": symbol, "providers": found, "weak": row["weak"]}
            )
        counts[n] = {"strong_symbols_available": strong, "unresolved_weak_symbols": weak_unresolved}
    return {"tracer_reachable_objects": sorted(reachable), "symbol_availability": counts}, bindings


def fault_controls(objects):
    cases = {}
    missing = copy.deepcopy(objects)
    del missing["liblzma"]
    cases["missing_library"] = missing
    version = copy.deepcopy(objects)
    version["libc"]["version_definitions"].remove("GLIBC_2.34")
    cases["missing_required_version"] = version
    symbol = copy.deepcopy(objects)
    symbol["unwind-x86_64"]["exports"].remove("_Ux86_64_create_addr_space")
    cases["missing_required_strong_symbol"] = symbol
    interp = copy.deepcopy(objects)
    interp["strace"]["interpreter"] = "/unreviewed/loader"
    cases["wrong_interpreter"] = interp
    refused = []
    for name, changed in cases.items():
        try:
            check_closure(changed)
        except AssertionError:
            refused.append(name)
        else:
            raise AssertionError(f"negative control accepted: {name}")
    check_closure(objects)
    return refused


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt_root", type=pathlib.Path)
    parser.add_argument("output_root", type=pathlib.Path)
    args = parser.parse_args()
    objects = {}
    inputs = {}
    for name in NAMES:
        path = args.receipt_root / f"{name}-elf.stdout"
        data = path.read_bytes()
        inputs[path.name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        objects[name] = parse_elf(data.decode())
    summary, bindings = check_closure(objects)
    negatives = fault_controls(objects)
    details = copy.deepcopy(objects)
    for obj in details.values():
        del obj["exports"], obj["undefined"]
    report = {
        "method": (
            "Static readelf output interpretation; symbol availability, "
            "not dynamic loader emulation or execution"
        ),
        "inputs": inputs,
        "objects": details,
        **summary,
        "unused_payload": (
            "unwind-coredump is not DT_NEEDED-reachable from strace; "
            "its strong imports are available in the tracer group, "
            "but standalone loading was not tested"
        ),
        "negative_controls_refused": negatives,
        "restored_positive": True,
        "limits": [
            (
                "No runtime loading, IFUNC resolution, constructors, "
                "optional dlopen paths or ptrace checked"
            ),
            (
                "Weak unresolved symbols retained explicitly; "
                "no claim of semantic dependency or full environment use"
            ),
        ],
    }
    args.output_root.mkdir(exist_ok=True)
    for filename, value in [("static-closure.json", report), ("symbol-bindings.json", bindings)]:
        (args.output_root / filename).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print("Negative controls refused:", ", ".join(negatives))


if __name__ == "__main__":
    main()
