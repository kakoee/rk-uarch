"""Literal declaration checks; AST evaluation only, never freeze/build/docker."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from native.tools import component_runtime_candidate as preparation

ROOT = Path(preparation.__file__).resolve().parents[2]


def declarations() -> dict[str, Any]:
    tree = ast.parse((ROOT / "native/tools/component_runtime_candidate.py").read_bytes())
    freeze = next(v for v in tree.body if isinstance(v, ast.FunctionDef) and v.name == "freeze")
    call = next(
        v.value
        for v in freeze.body
        if isinstance(v, ast.Assign)
        and isinstance(v.targets[0], ast.Name)
        and v.targets[0].id == "build"
    )
    assert isinstance(call, ast.Call) and isinstance(call.args[0], ast.Dict)
    values = {
        ast.literal_eval(k): v for k, v in zip(call.args[0].keys, call.args[0].values, strict=True)
    }
    tools = json.loads(
        (ROOT / "docs/reviews/U4-A-K2-construction-v1/candidate-04/ToolInputs.json").read_bytes()
    )
    scope = dict(vars(preparation), tools=SimpleNamespace(**tools))

    def evaluate(key: str) -> Any:
        return eval(compile(ast.Expression(values[key]), "<declarations-only>", "eval"), scope)

    return {
        "modes": evaluate("mode_configs"),
        "shared": evaluate("permitted_environment") if "permitted_environment" in values else None,
    }


@pytest.mark.parametrize("mode", ["debug", "release"])
@pytest.mark.parametrize("field", ["argv", "environment"])
def test_literal_construction_declarations(mode: str, field: str) -> None:
    observed = json.loads(
        (
            ROOT
            / "docs/reviews/U4-B-activation-combined-confirmation-v1/evidence/construction.json"
        ).read_bytes()
    )
    expected = next(v for v in observed["rendered_from_source_ast_only"] if v["mode"] == mode)
    values = declarations()
    selected = next(v for v in values["modes"] if v["mode"] == mode)
    if field == "argv":
        assert [expected["actual_source_argv"][0], *selected["cargo_args"]] == expected[
            "actual_source_argv"
        ]
    else:
        assert (
            selected.get("permitted_environment", values["shared"])
            == expected["actual_source_environment"]
        )
