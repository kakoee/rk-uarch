"""Pure construction-data rendering; no real BuildInputs, build, capture or Docker call."""

from __future__ import annotations

import ast
import hashlib
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from native.tools import component_candidate as wrapper
from native.tools import component_runtime_candidate as preparation
from rkuarch.engines.native.component_records import ComponentBuildInputsV3

root = preparation.ROOT
package = root / "docs/reviews/U4-A-construction-declarations-final-v1/probes"
inputs = runpy.run_path(str(package / "test_declarations.py"))["declarations"]()
synthetic = runpy.run_path(str(package / "test_repair.py"))["synthetic_build"](inputs["modes"])
value = ComponentBuildInputsV3.model_validate(synthetic)
raw = json.dumps(synthetic, sort_keys=True).encode()
recipe = preparation.construction_recipe(raw)
tree = ast.parse(Path(preparation.__file__).read_bytes())
build = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build")
assignment = next(
    n.value
    for n in build.body
    if isinstance(n, ast.Assign)
    and isinstance(n.targets[0], ast.Name)
    and n.targets[0].id == "command"
)
rows = []
for mode in ("debug", "release"):
    argv, environment = preparation.production_invocation(value, mode)
    observed = []

    def substitute(*args: Any, recorded: list[Any] = observed, **kwargs: Any) -> list[str]:
        recorded.append({"mode": args[1], "tag": args[2], "environment": kwargs["environment"]})
        return ["synthetic-container-prefix"]

    rendered = eval(
        compile(ast.Expression(assignment), "<builder-expression-only>", "eval"),
        {
            "c": SimpleNamespace(docker=substitute),
            "out": Path("/synthetic-not-used"),
            "mode": mode,
            "argv": argv,
            "environment": environment,
        },
    )
    selected = next(row for row in recipe["mode_configs"] if row["mode"] == mode)
    assert rendered[1:] == argv
    assert selected["permitted_environment"] == environment
    assert (
        dict(
            item.split("=", 1)
            for item in wrapper.container_environment(mode + "-build", environment)
        )
        == environment
    )
    rows.append(
        {
            "mode": mode,
            "declaration": selected,
            "actual_builder_assignment": rendered,
            "exact_environment_passed_to_prefix": observed,
            "recipe_join_equal": True,
        }
    )
paths = [
    "native/tools/component_runtime_candidate.py",
    "native/tools/component_candidate.py",
    "src/rkuarch/engines/native/component_construction.py",
    "src/rkuarch/engines/native/component_records.py",
    "src/rkuarch/engines/native/component_host.py",
    "validation/component/capture_monitor.py",
]
result = {
    "format": "A-construction-source-rendering/1",
    "synthetic": True,
    "postimages": {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths},
    "modes": rows,
    "build_or_capture_executed": False,
    "real_BuildInputs_or_recipe_generated": False,
    "methods_not_called": ["freeze", "prepare", "build", "docker", "command", "run_capture"],
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print("Rendered debug/release declarations, builder expression and recipe; no execution.")
