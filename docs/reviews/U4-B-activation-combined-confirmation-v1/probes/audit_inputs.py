"""Read/AST audit only: render literal declarations, never call build/prepare/docker."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

root, output = (Path(v).resolve() for v in sys.argv[1:])
package = "docs/reviews/U4-A-activation-combined-preparation-v1"
tool = root / "native/tools/component_runtime_candidate.py"
wrapper = root / "native/tools/component_candidate.py"
tree, wrapper_tree = ast.parse(tool.read_bytes()), ast.parse(wrapper.read_bytes())


def function(module: ast.Module, name: str) -> ast.FunctionDef:
    return next(v for v in module.body if isinstance(v, ast.FunctionDef) and v.name == name)


def evaluate(expression: ast.expr, scope: dict[str, Any]) -> Any:
    return eval(compile(ast.Expression(expression), "<read-only-literal-fragment>", "eval"), scope)


freeze = function(tree, "freeze")
validate = next(
    v.value
    for v in freeze.body
    if isinstance(v, ast.Assign)
    and isinstance(v.targets[0], ast.Name)
    and v.targets[0].id == "build"
)
assert isinstance(validate, ast.Call) and isinstance(validate.args[0], ast.Dict)
declarations = {
    ast.literal_eval(k): v
    for k, v in zip(validate.args[0].keys, validate.args[0].values, strict=True)
}
tools = json.loads(
    (root / "docs/reviews/U4-A-K2-construction-v1/candidate-04/ToolInputs.json").read_bytes()
)
modes = evaluate(declarations["mode_configs"], {"tools": SimpleNamespace(**tools)})
permitted = evaluate(declarations["permitted_environment"], {})
constants = {}
for item in wrapper_tree.body:
    if (
        isinstance(item, ast.Assign)
        and isinstance(item.targets[0], ast.Name)
        and item.targets[0].id in ("BIN", "IMAGE")
    ):
        constants[item.targets[0].id] = ast.literal_eval(item.value)
wrapper_return = next(v for v in function(wrapper_tree, "docker").body if isinstance(v, ast.Return))
assert isinstance(wrapper_return.value, ast.BinOp) and isinstance(
    wrapper_return.value.right, ast.List
)
command = next(
    v.value
    for v in function(tree, "build").body
    if isinstance(v, ast.Assign)
    and isinstance(v.targets[0], ast.Name)
    and v.targets[0].id == "command"
)
assert isinstance(command, ast.BinOp) and isinstance(command.right, ast.List)
rendered = []
for config in modes:
    mode = config["mode"]
    suffix = evaluate(wrapper_return.value.right, {**constants, "tag": mode + "-build"})
    env = dict(v.split("=", 1) for v in suffix[suffix.index("-i") + 1 :])
    argv = evaluate(
        command.right,
        {"c": SimpleNamespace(**constants), "config": SimpleNamespace(**config), "mode": mode},
    )
    declared = [constants["BIN"] + "cargo", *config["cargo_args"]]
    assert argv == declared + ["--", "-C", "link-arg=-Wl,-Map=/receipts/" + mode + ".map"]
    assert all(env[k] == v for k, v in permitted.items())
    extras = {k: v for k, v in env.items() if k not in permitted}
    assert set(extras) == {
        "PATH",
        "CARGO_REGISTRIES_CRATES_IO_PROTOCOL",
        "RUSTC",
        "RUSTC_WRAPPER",
        "RUSTFLAGS",
        "C2_RUN_TAG",
    }
    rendered.append(
        {
            "mode": mode,
            "declared_argv": declared,
            "actual_source_argv": argv,
            "declared_environment": permitted,
            "actual_source_environment": env,
            "undeclared_environment": extras,
            "recipe_exact_equality": False,
        }
    )
# Independent literal path inventories, compared against both resulting actual routes.
sources = set()
for directory in ("native", "src/rkuarch", "contract/uarch_contract", "validation"):
    sources.update(
        p
        for p in (root / directory).rglob("*")
        if p.is_file()
        and p.suffix in (".rs", ".toml", ".lock", ".py", ".json")
        and "generated" not in p.parts
    )
sources.update(
    root / p
    for p in (
        "pyproject.toml",
        "uv.lock",
        "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py",
    )
)
sources.update(
    root / "docs/reviews/U4-B-K2-parallel-first-use-v1" / n
    for n in ("parallel_core.py", "resource_limits.py")
)
sources.update(
    root / "docs/reviews/U4-A-K2-construction-v1/inputs" / n
    for n in ("rustc-wrapper.sh", "linker.sh")
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


actual = {str(p.relative_to(root)): sha(p) for p in sorted(sources)}
# Compare with the source manifest from the exact frozen export.
transition = json.loads(
    (output.parent / "source" / package / "source-transition.json").read_bytes()
)
assert actual == transition["activation_prospective_source_files"] and len(actual) == 249
record = {
    "format": "B-final-construction-source-audit/1",
    "preparation_sha256": sha(tool),
    "wrapper_sha256": sha(wrapper),
    "source_entries": len(actual),
    "rendered_from_source_ast_only": rendered,
    "methods_not_called": ["freeze", "prepare", "build", "docker", "command"],
    "real_BuildInputs_or_recipe_generated": False,
    "pending_diagnostic_policy": (
        "all stderr currently refuses; decide exact handling of expected canary/compiler "
        "diagnostics versus tracer loss/unknown diagnostics without discarding raw bytes "
        "or claiming independent loss count"
    ),
}
output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(
    json.dumps(
        {
            "source_entries": len(actual),
            "modes": [v["mode"] for v in rendered],
            "undeclared_environment_keys": sorted(rendered[0]["undeclared_environment"]),
            "construction_ready": False,
        }
    )
)
