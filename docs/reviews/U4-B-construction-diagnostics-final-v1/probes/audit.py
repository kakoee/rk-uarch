"""Read-only exact final proposal audit; no build/capture/startup invocation."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    repo, work = [Path(value).resolve() for value in sys.argv[1:]]
    package = repo / "docs/reviews/U4-A-construction-declarations-final-v1"
    manifest = json.loads((package / "manifest.json").read_bytes())
    assert (
        digest(package / "manifest.json")
        == "193d6621a1c1ad508048efffa990ac9ab08c8244c52c7200ff74700f5e9e4b23"
    )
    for path, pin in manifest["files"].items():
        file = package / path
        assert digest(file) == pin["sha256"] and file.stat().st_size == pin["bytes"]
    transition = json.loads((package / "source-transition.json").read_bytes())
    root = work / "direct"
    for path, pin in transition["prospective_source_files"].items():
        assert digest(root / path) == digest(work / "sequential" / path) == pin
    for path, pin in manifest["postimages"].items():
        assert digest(root / path) == pin
    b = repo / "docs/reviews/U4-B-capture-diagnostics-v1"
    old = (b / "proposals/capture-monitor-postimage.py.txt").read_text()
    new = (root / "validation/component/capture_monitor.py").read_text()

    def nonimports(raw: str) -> str:
        tree = ast.parse(raw)
        tree.body = [
            node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        return ast.dump(tree)

    assert nonimports(old) == nonimports(new)

    def imports(raw: str) -> list[str]:
        return sorted(
            ast.dump(node)
            for node in ast.parse(raw).body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )

    assert imports(old) == imports(new)
    b_manifest = json.loads((b / "manifest.json").read_bytes())
    for path, pin in b_manifest["files"].items():
        assert digest(root / path) == pin
    source = (root / "native/tools/component_runtime_candidate.py").read_text()
    binding_path = (
        "docs/reviews/U4-A-construction-declarations-final-v1/activation-consumer-bindings.json"
    )
    binding = json.loads((root / binding_path).read_bytes())
    assert (
        digest(root / binding_path)
        == "bcd940c0bdebe0f0f9edf48e8bef987eba6204c3f6f989a3d21d779a0b6fffda"
    )
    assert "U4-A-construction-declarations-final-v1" in source
    assert digest(root / binding_path) not in source
    assert binding["files"]["native/tools/component_runtime_candidate.py"] == digest(
        root / "native/tools/component_runtime_candidate.py"
    )
    base = work / "base"
    startup = "native/tools/component_startup_inventory.py"

    def functions(path: Path) -> dict[str, ast.FunctionDef]:
        return {
            node.name: node
            for node in ast.parse(path.read_bytes()).body
            if isinstance(node, ast.FunctionDef)
        }

    before, after = functions(base / startup), functions(root / startup)
    for name in ("copy_bound", "construct"):
        old_return, new_return = before[name].returns, after[name].returns
        assert old_return is not None and new_return is not None
        assert ast.dump(old_return) == ast.dump(new_return) == "Name(id='dict', ctx=Load())"
    assert ast.dump(before["copy_bound"]) == ast.dump(after["copy_bound"])
    launcher = "native/tools/component_trusted_start.py"
    assert digest(base / launcher) == digest(root / launcher)
    old_class = ast.parse((base / "src/rkuarch/engines/native/component_records.py").read_bytes())
    new_class = ast.parse((root / "src/rkuarch/engines/native/component_records.py").read_bytes())

    def v2(tree: ast.Module) -> str:
        return ast.dump(
            next(
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "ComponentBuildInputs"
            )
        )

    assert v2(old_class) == v2(new_class)
    result = {
        "source": "aecc6a27e1533eee43e884380ed095cfc1edfd20",
        "handoff": "e550a8801525c722792d375f78f623aebb72caeb",
        "manifest": digest(package / "manifest.json"),
        "A_leaves": len(manifest["files"]),
        "both_routes_source_entries": len(transition["prospective_source_files"]),
        "postimages": manifest["postimages"],
        "consumer_pins": len(binding["files"]),
        "binding_sha256": digest(root / binding_path),
        "B_leaves_unchanged": len(b_manifest["files"]),
        "monitor_nonimport_ast_and_import_set_unchanged": True,
        "historical_v2_class_ast_unchanged": True,
        "binding_dependency_acyclic": True,
        "typing": (
            "two unchanged bare-dict return annotations; no runtime guard or policy bypass inferred"
        ),
        "unchanged_launcher": digest(root / launcher),
        "new_build_capture_startup_or_authority": False,
    }
    (work / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
