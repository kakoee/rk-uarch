"""F2 probe: single active checker implementation, and which default tests can reach it.

Usage: python3 -I checker_reach.py TREE COLLECT_ONLY_LISTING [TARGET_MODULE_PREFIX]
(default target rkuarch.verification.component; e.g. validation.component.observations_v3 for v1)
* Lists every top-level definition of the shipped checker functions anywhere outside
  docs/reviews (a duplicate implementation would show up here).
* Builds a static import graph (all Import/ImportFrom nodes, including function-level and
  relative imports) over src/, contract/, validation/, tests/, native/, scripts/ and reports
  which collected test files transitively reach rkuarch.verification.component.*.
Static reachability over-approximates use; it bounds the selection run under drift.
"""

import ast
import json
import sys
from pathlib import Path

tree, listing = Path(sys.argv[1]), Path(sys.argv[2])
ROOTS = {"src": "", "contract": "", ".": ""}
CHECKER = "rkuarch.verification.component"
TARGET = sys.argv[3] if len(sys.argv) > 3 else CHECKER
shipped = tree / "src/rkuarch/verification/component"
names = set()
for f in shipped.glob("*.py"):
    for node in ast.parse(f.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)

modules: dict[str, Path] = {}
for base, prefix in (("src", ""), ("contract", ""), (".", "")):
    root = tree / base
    for f in root.rglob("*.py"):
        rel = f.relative_to(root)
        if rel.parts[0] in ("docs", ".venv", "third_party") or "vendor" in rel.parts:
            continue
        if base == "." and rel.parts[0] in ("src",):
            continue
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            modules.setdefault(".".join(parts), f)

duplicates = {}
for mod, f in modules.items():
    if mod.startswith(CHECKER):
        continue
    for node in ast.parse(f.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            duplicates.setdefault(node.name, []).append(mod)


def imports(mod: str, f: Path) -> set[str]:
    out = set()
    pkg = mod.split(".") if f.name == "__init__.py" else mod.split(".")[:-1]
    for node in ast.walk(ast.parse(f.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = pkg[: len(pkg) - node.level + 1] if node.level else []
            head = ".".join(base + ([node.module] if node.module else []))
            out.add(head)
            out |= {f"{head}.{a.name}" for a in node.names}
    resolved = set()
    for name in out:
        while name and name not in modules:
            name = name.rpartition(".")[0]
        if name:
            resolved.add(name)
    return resolved


graph = {m: imports(m, f) for m, f in modules.items()}
reach_cache: dict[str, bool] = {}


def reaches(m: str, seen: frozenset = frozenset()) -> bool:
    if m.startswith(TARGET):
        return True
    if m in reach_cache:
        return reach_cache[m]
    if m in seen:
        return False
    r = any(reaches(n, seen | {m}) for n in graph.get(m, ()))
    reach_cache[m] = r
    return r


collected = sorted({line.split("::")[0] for line in listing.read_text().splitlines() if "::" in line})
reaching = []
for path in collected:
    mod = ".".join(Path(path).with_suffix("").parts)
    if mod in modules and reaches(mod):
        reaching.append(path)
print(json.dumps({
    "shipped_checker_definitions": len(names),
    "duplicate_definitions_outside_shipped": duplicates,
    "validation_component_checker_files_present": sorted(
        p.name for p in (tree / "validation/component").glob("*.py")
        if p.name in {f.name for f in shipped.glob("*.py")}),
    "collected_test_files": len(collected),
    "target": TARGET,
    "test_files_reaching_shipped_checker": reaching,
}, indent=1))
