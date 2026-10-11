"""Content identity of the explicit execution roots and their local Python imports.

Includes conditional/function imports and package initializers. It does not substitute
for U0002's support/lock binding, or identify installed third-party package bytes.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

from uarch_contract.hashing import content_hash, sha256

_ROOT = Path(__file__).resolve().parents[4]
_ROOTS = (
    "rkuarch.engines.analytic.rotary_v2",
    "rkuarch.engines.analytic.dispatch",
    "rkuarch.engines.protocol_v2",
    "rkuarch.workload.prepared_v2",
    "uarch_contract.rotary_v2",
)


def execution_dependencies() -> dict[str, str]:
    """Discover deterministic local import closure; hash fresh bytes on every call."""
    pending = list(_ROOTS)
    seen: set[str] = set()
    files: dict[str, str] = {}
    while pending:
        module = pending.pop()
        if module in seen or module.split(".")[0] not in ("rkuarch", "uarch_contract"):
            continue
        seen.add(module)
        base = _ROOT / ("src" if module.startswith("rkuarch") else "contract")
        path = base.joinpath(*module.split("."))
        source = path / "__init__.py" if path.is_dir() else path.with_suffix(".py")
        if not source.is_file():
            # `from module import member` also visits members that are not modules.
            continue
        payload = source.read_bytes()
        files[source.relative_to(_ROOT).as_posix()] = sha256(payload)
        parts = module.split(".")
        pending.extend(".".join(parts[:i]) for i in range(1, len(parts)))
        package = module if source.name == "__init__.py" else module.rpartition(".")[0]
        for node in ast.walk(ast.parse(payload)):
            if isinstance(node, ast.Import):
                pending.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                name = "." * node.level + (node.module or "")
                resolved = importlib.util.resolve_name(name, package) if node.level else name
                pending.append(resolved)
                pending.extend(resolved + "." + alias.name for alias in node.names)
    # Missing execution roots must not silently disappear from the identity.
    for module in _ROOTS:
        relative = "src/" if module.startswith("rkuarch") else "contract/"
        relative += module.replace(".", "/") + ".py"
        if relative not in files:
            raise ValueError("MissingExecutionDependency: " + relative)
    return dict(sorted(files.items()))


def _source_hash() -> str:
    return content_hash(
        dict(format="analytic-rope-implementation/1", files=execution_dependencies())
    )


_IMPORTED_HASH = _source_hash()


def implementation_hash() -> str:
    # Never label already imported code with subsequently edited source bytes.
    # A fresh process under changed code gets a different identity; old jobs refuse.
    current = _source_hash()
    if current != _IMPORTED_HASH:
        raise ValueError("ImplementationChanged: local execution source changed; restart required")
    return current
