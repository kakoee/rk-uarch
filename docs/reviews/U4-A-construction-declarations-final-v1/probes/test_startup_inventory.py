"""Project path enumeration only; never construct a snapshot or invoke trusted startup."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from native.tools import component_startup_inventory as startup

ROOT = Path(startup.__file__).resolve().parents[2]
HELPERS = (
    "docs/reviews/U4-B-K2-parallel-first-use-v1/parallel_core.py",
    "docs/reviews/U4-B-K2-parallel-first-use-v1/resource_limits.py",
    "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py",
)


def project_rows() -> list[Path]:
    tree = ast.parse((ROOT / "native/tools/component_startup_inventory.py").read_bytes())
    function = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "construct"
    )
    # Only the first project-copy loop, with copy/hash replaced by path collection.
    loop = next(n for n in function.body if isinstance(n, ast.For))
    rows: list[Any] = []
    scope = dict(
        vars(startup),
        source=ROOT,
        project=ROOT,
        rows=rows,
        copy_bound=lambda source, target, expected: source,
        digest=lambda path: "unused",
    )
    exec(compile(ast.Module(body=[loop], type_ignores=[]), "<project-loop-only>", "exec"), scope)
    return rows


def test_startup_project_loop_includes_bound_docs_helpers() -> None:
    paths = {str(p.relative_to(ROOT)) for p in project_rows()}
    assert set(HELPERS) <= paths, sorted(set(HELPERS) - paths)


def test_startup_project_loop_is_complete_unique_import_closure() -> None:
    paths = project_rows()
    expected = {
        p
        for directory in ("src/rkuarch", "contract/uarch_contract", "validation", "native/tools")
        for p in (ROOT / directory).rglob("*.py")
    } | {ROOT / name for name in HELPERS}
    assert len(paths) == len(set(paths))
    assert set(paths) == expected
    assert all(p.is_file() for p in paths)
