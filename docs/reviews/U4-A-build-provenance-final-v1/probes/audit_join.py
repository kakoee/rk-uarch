"""Read-only source/import/consumer enumeration; no startup construction or build."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from native.tools import component_runtime_candidate as prep
from native.tools.component_startup_inventory import project_files
from validation.component.runtime_checks import verify_sources

A = "docs/reviews/U4-A-build-provenance-final-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inventory(root: Path) -> dict[str, str]:
    # Evaluate ONLY the actual freeze path enumeration. No freeze/generation call.
    tree = ast.parse((root / "native/tools/component_runtime_candidate.py").read_bytes())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "freeze")
    start = next(
        i
        for i, n in enumerate(function.body)
        if isinstance(n, ast.AnnAssign)
        and isinstance(n.target, ast.Name)
        and n.target.id == "paths"
    )
    end = next(
        i
        for i, n in enumerate(function.body)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "inventory"
    )
    scope: dict[str, Any] = {"source": root, "Path": Path}
    exec(
        compile(ast.Module(body=function.body[start:end], type_ignores=[]), "<paths-only>", "exec"),
        scope,
    )
    return {str(p.relative_to(root)): digest(p) for p in sorted(set(scope["paths"]))}


def main() -> None:
    root, output, observation = (Path(v).resolve() for v in sys.argv[1:])
    expected = json.loads((root / A / "source-transition.json").read_bytes())
    assert source_inventory(root) == expected["prospective_source_files"]
    result = prep.imports(root, observation_root=observation)
    assert result["independent_binding"]["path"] == A + "/activation-consumer-bindings.json"
    imports = {v["path"]: v["byte_hash"][7:] for v in result["files"]}
    startup_paths = {str(p.relative_to(root)): digest(p) for p in project_files(root)}
    assert imports == startup_paths
    inherited = json.loads(
        (
            root
            / "docs/reviews/U4-A-construction-declarations-final-v1"
            / "inherited-external-inventory.json"
        ).read_bytes()
    )
    assert result["external_files"] == inherited["external_files"]
    assert result["python_executable"] == inherited["python_executable"]
    pins = json.loads((root / A / "activation-consumer-bindings.json").read_bytes())["files"]
    assert all(imports.get(name) == pin for name, pin in pins.items())
    verify_sources(root, pins)
    refusals = {}
    for name in (
        "native/tools/component_ordinary_build.py",
        "src/rkuarch/engines/native/component_build_review.py",
        "src/rkuarch/engines/native/component_review.py",
        "validation/component/ordinary_build_acceptance.py",
        "validation/component/ordinary_build_receipt.py",
    ):
        bad = dict(pins)
        del bad[name]
        try:
            verify_sources(root, bad)
        except ValueError as error:
            assert "complete matching consumer/structural closure" in str(error)
            refusals[name] = str(error)
        else:
            raise AssertionError("missing required module accepted: " + name)
    name = "native/tools/component_runtime_candidate.py"
    bad = dict(pins)
    bad[name] = "24271b51ffe564b01455059ca49e1831fe3576c99764b0f276755f1e97a61d58"
    try:
        verify_sources(root, bad)
    except ValueError as error:
        assert "consumer source mismatch: " + name in str(error)
        refusals["stale-preparation"] = str(error)
    else:
        raise AssertionError("old preparation accepted")
    origins = {}
    for name, module in sorted(sys.modules.copy().items()):
        if name.split(".")[0] in ("native", "rkuarch", "uarch_contract", "validation"):
            raw = getattr(module, "__file__", None)
            if raw:
                path = Path(raw).resolve()
                assert path.is_relative_to(root), (name, path)
                origins[name] = {"path": str(path.relative_to(root)), "sha256": digest(path)}
            else:
                assert all(Path(v).resolve().is_relative_to(root) for v in module.__path__)
    report = {
        "format": "A-provenance-final-join-check/1",
        "source_inventory": source_inventory(root),
        "project_import_inventory": imports,
        "startup_project_path_inventory": startup_paths,
        "source_count": len(expected["prospective_source_files"]),
        "consumer_count": len(pins),
        "import_count": len(imports),
        "external_count": len(result["external_files"]),
        "python_executable": result["python_executable"],
        "independent_binding": result["independent_binding"],
        "missing_and_stale_refusals": refusals,
        "origin_checks": origins,
        "startup_assurance": "not assessed; A-F3 deferred",
        "build_or_startup_execution": False,
        "method": "read/hash imports; pure path enumeration only, no construct/startup/probe",
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k.endswith("count") or k in ("build_or_startup_execution", "startup_assurance")
            }
        )
    )


if __name__ == "__main__":
    main()
