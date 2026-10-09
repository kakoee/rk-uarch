"""Path loader for unchanged vendor sources, confined to the test process.

Absolute rk imports inside vendor source are resolved recursively with per-module
builtins. No sys.path mutation, no rk package registration, no source rewriting.
"""

from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from scripts.vendor_rk import SOURCES


class VendorLoader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.modules: dict[str, ModuleType] = {}

    def load(self, name: str) -> Any:
        if name in self.modules:
            return self.modules[name]
        relative = name.replace(".", "/") + ".py"
        if relative not in SOURCES:
            raise ImportError(f"vendor module outside declared source closure: {name}")
        path = self.root / relative
        module = ModuleType("_uarch_vendor_" + str(id(self)) + "." + name)
        module.__file__ = str(path)
        module.__dict__["__builtins__"] = dict(vars(builtins), __import__=self._import)
        self.modules[name] = module
        # Pydantic resolves postponed annotations through the private module name.
        sys.modules[module.__name__] = module
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        return module

    def _import(
        self, name: str, globals: Any = None, locals: Any = None, fromlist: Any = (), level: int = 0
    ) -> Any:
        if name == "rk" or name.startswith("rk."):
            if not fromlist or level:
                raise ImportError(f"unsupported vendor import form: {name}")
            return self.load(name)
        return builtins.__import__(name, globals, locals, fromlist, level)


# Test-only statement of U0001's naming seam. No production integration in U1.
COUNT_CHANNELS = {
    "matrix_ops": "matrix_ops",
    "vector_ops": "vector_ops",
    "memory_read_bytes": "memory_read",
    "memory_write_bytes": "memory_write",
}


def translate_count_names(counts: dict[str, Any]) -> dict[str, Any]:
    unknown = set(counts) - COUNT_CHANNELS.keys()
    if unknown:
        raise ValueError(f"unknown Row.counts fields: {sorted(unknown)}")
    return {COUNT_CHANNELS[key]: value for key, value in counts.items()}


def check_production_isolation(root: Path) -> None:
    """Conservative source guard, not a proof against arbitrary obfuscated execution.

    Only the fixed schema discovery and byte-pinned local JSON import are allowed.
    Import-linter separately checks the static import graph.
    """
    import ast
    import hashlib

    for directory in (root / "src", root / "contract/uarch_contract"):
        for path in sorted(directory.rglob("*.py")):
            tree = ast.parse(path.read_text())
            violations = []
            schema_generator = path == root / "contract/uarch_contract/generate.py"
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = (
                        [a.name for a in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module or ""]
                    )
                    forbidden = {"rk", "scripts"} | (set() if schema_generator else {"importlib"})
                    fixed_proof_resources = (
                        path == root / "src/rkuarch/provenance/proof_raw.py"
                        and hashlib.sha256(path.read_bytes()).hexdigest()
                        == "9f47439f058417e24fcf2891f996d7b9428a69c4c8825c5e3188936c6d659c15"
                        and isinstance(node, ast.ImportFrom)
                        and node.level == 0
                        and node.module == "importlib.resources"
                        and [(alias.name, alias.asname) for alias in node.names] == [("files", None)]
                    )
                    if (
                        any(name.split(".")[0] in forbidden for name in names)
                        and not fixed_proof_resources
                    ):
                        violations.append(node.lineno)
                if isinstance(node, ast.Call):
                    name = (
                        node.func.id
                        if isinstance(node.func, ast.Name)
                        else node.func.attr
                        if isinstance(node.func, ast.Attribute)
                        else ""
                    )
                    local_schema_call = schema_generator and ast.dump(node) == ast.dump(
                        ast.parse(
                            'importlib.import_module(f"uarch_contract.{name}")', mode="eval"
                        ).body
                    )
                    if (
                        name in {"exec", "eval", "__import__", "import_module", "VendorLoader"}
                        and not local_schema_call
                    ):
                        violations.append(node.lineno)
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if any(
                        value in node.value
                        for value in ("contract/vendor", "rk-sim@", "scripts.vendor_rk")
                    ):
                        violations.append(node.lineno)
            if violations:
                raise ValueError(f"production vendor isolation: {path}:{sorted(set(violations))}")
