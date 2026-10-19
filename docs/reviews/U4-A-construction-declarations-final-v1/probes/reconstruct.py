"""Reconstruct both unapplied routes in a new private directory; never build or install."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

BASE = "097a69033668a3fc457fb4b6649370a1d4948b16"
A = "docs/reviews/U4-A-construction-declarations-final-v1"
PRIOR = "docs/reviews/U4-A-activation-combined-preparation-v1"
B = "docs/reviews/U4-B-activation-orchestration-v1"
TOOL = "native/tools/component_runtime_candidate.py"
PARSER = "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inventory(root: Path) -> dict[str, str]:
    # Execute only the actual path-enumeration fragment, not freeze(), trust, jobs or identities.
    tree = ast.parse((root / TOOL).read_bytes())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "freeze")
    start = next(
        i
        for i, n in enumerate(function.body)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "paths"
    )
    end = next(
        i
        for i, n in enumerate(function.body)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "inventory"
    )
    fragment = ast.Module(body=function.body[start:end], type_ignores=[])
    scope = {"source": root}
    exec(compile(fragment, str(root / TOOL), "exec"), scope)
    return {str(p.relative_to(root)): digest(p) for p in sorted(set(scope["paths"]))}


def consumer_inventory(root: Path) -> dict[str, str]:
    paths = set()
    for parent in (
        "contract/uarch_contract",
        "validation/component",
        "src/rkuarch/engines/native",
        "native/tools",
    ):
        paths.update(p for p in (root / parent).glob("*.py") if not p.name.startswith("test_"))
    paths.update(
        root / "docs/reviews/U4-B-K2-parallel-first-use-v1" / name
        for name in ("parallel_core.py", "resource_limits.py")
    )
    paths.add(root / PARSER)
    return {str(p.relative_to(root)): digest(p) for p in sorted(paths)}


def main() -> None:
    repo, work = (Path(p).resolve() for p in sys.argv[1:])
    work.mkdir(exist_ok=False)
    package = repo / A
    expected = json.loads((package / "source-transition.json").read_bytes())
    archive = work / "base.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "archive", BASE], cwd=repo, stdout=stream, check=True)
    base = work / "base"
    base.mkdir()
    with tarfile.open(archive) as stream:
        stream.extractall(base, filter="data")
    manifests = {}
    for directory, name in (
        (B, "manifest.json"),
        (PRIOR, "manifest.json"),
        ("docs/reviews/U4-B-component-activation-final-v1", "manifest.json"),
    ):
        record = json.loads((base / directory / name).read_bytes())
        for path, pin in record["files"].items():
            file = base / directory / path
            assert digest(file) == pin["sha256"] and file.stat().st_size == pin["bytes"], path
        manifests[directory] = {
            "sha256": digest(base / directory / name),
            "leaves": len(record["files"]),
        }
    current = source_inventory(base)
    declared = dict(current)
    declared[PARSER] = digest(base / PARSER)
    assert current == expected["current_live_source_files"]
    assert declared == expected["current_declared_source_files"]
    current_pins = json.loads((package / "source-consumer-bindings.json").read_bytes())["files"]
    assert consumer_inventory(base) == current_pins
    routes = {}
    for name, patches in (
        (
            "sequential",
            [
                base / PRIOR / "proposals/activation-full-unapplied.patch",
                package / "proposals/declaration-diagnostics-delta.patch",
            ],
        ),
        ("direct", [package / "proposals/complete-activation-unapplied.patch"]),
    ):
        root = work / name
        shutil.copytree(base, root)
        for patch in patches:
            subprocess.run(["git", "apply", str(patch)], cwd=root, check=True)
        (root / A).mkdir(exist_ok=True)
        shutil.copyfile(
            package / "activation-consumer-bindings.json",
            root / A / "activation-consumer-bindings.json",
        )
        assert source_inventory(root) == expected["prospective_source_files"]
        pins = json.loads((package / "activation-consumer-bindings.json").read_bytes())["files"]
        assert consumer_inventory(root) == pins
        for path, pin in expected["postimages"].items():
            assert digest(root / path) == pin, path
        routes[name] = {"source_entries": len(source_inventory(root)), "consumer_pins": len(pins)}
    for path, pin in expected["actual_B_inputs"].items():
        assert digest(base / path) == pin, path
    b_directory = "docs/reviews/U4-B-capture-diagnostics-v1"
    b_manifest = json.loads((base / b_directory / "manifest.json").read_bytes())
    for path, pin in b_manifest["files"].items():
        assert digest(base / path) == pin, path
    result = {
        "B_final_manifest_sha256": digest(base / b_directory / "manifest.json"),
        "B_final_leaves_verified": len(b_manifest["files"]),
        "format": "A-combined-reconstruction-result/1",
        "base": BASE,
        "historical_manifests": manifests,
        "current_live_enumerated_sources": len(current),
        "current_declared_transition_sources": len(declared),
        "current_consumer_pins": len(current_pins),
        "routes": routes,
        "postimages": expected["postimages"],
        "native_build": False,
        "installation": False,
    }
    (work / "reconstruction.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
