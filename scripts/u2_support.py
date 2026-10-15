"""Proposed generation-support policy; review/migration required before installation.

A conservative static import closure plus explicitly reviewed non-import inputs.
Not a sandbox or a proof against arbitrary Python obfuscation. Function-local and
TYPE_CHECKING imports count; package initializers count. No plugin discovery.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

from scripts.u2_import_guard import DIRECTORIES, FILES, check_import_roots

ROOT = Path(__file__).resolve().parents[1]
POLICY = {"format": "uarch-input-support/2", "selection": "generator-imports-and-data/1"}
ENTRYPOINTS = ("scripts/u2_inputs.py", "scripts/vendor_rk.py", "scripts/u2_support.py")
LOCAL_PREFIXES = ("rkuarch", "uarch_contract", "scripts")
EXTERNAL = frozenset(sys.stdlib_module_names) | {"pydantic", "yaml"}
DYNAMIC = {"importlib", "runpy", "pkgutil", "ctypes"}
DATA = (
    "pyproject.toml",
    "uv.lock",
    "hw/designs/npu-l4.yaml",
    "contract/tests/fixtures/u2_b/component-precisions.json",
    "contract/tests/fixtures/u2_b/asic_placeholder-execution.json",
    "contract/tests/fixtures/u2_b/nvidia_h100_sxm-execution.json",
)


def safe(path: Path, root: Path) -> Path:
    if not path.is_relative_to(root):
        raise ValueError("support path outside root")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("support symlink: " + str(path))
    if not path.is_file():
        raise ValueError("support file missing: " + str(path))
    return path


def support_files(*, root: Path = ROOT) -> tuple[Path, ...]:
    check_import_roots(str(root))
    search = (root, root / "src", root / "contract")
    # Script entry execution also places scripts/ on sys.path. Never let an
    # unrelated new local file replace a reviewed external dependency.
    shadow_roots = (*search, root / "scripts")
    queue = [root / name for name in ENTRYPOINTS]
    seen: set[Path] = set()

    def resolve(name: str) -> list[Path]:
        matches = []
        for base in search:
            p = base.joinpath(*name.split("."))
            for candidate in (p.with_suffix(".py"), p / "__init__.py"):
                if candidate.exists() or candidate.is_symlink():
                    matches.append(safe(candidate, root))
        if len(matches) > 1:
            raise ValueError("ambiguous support import: " + name)
        return matches

    def dependency(name: str) -> None:
        top = name.split(".")[0]
        if top in DYNAMIC:
            raise ValueError("unreviewed dynamic dependency: " + name)
        if top in LOCAL_PREFIXES:
            matches = resolve(name)
            if not matches:
                raise ValueError("unresolved support import: " + name)
            queue.extend(matches)
            for n in range(1, len(name.split("."))):
                queue.extend(resolve(".".join(name.split(".")[:n])))
        else:
            if top not in EXTERNAL:
                raise ValueError("unreviewed external dependency: " + name)
            for base in shadow_roots:
                for candidate in (base / (top + ".py"), base / top):
                    if candidate.exists() or candidate.is_symlink():
                        raise ValueError("external import shadow: " + str(candidate))

    while queue:
        path = safe(queue.pop(), root)
        if path in seen:
            continue
        seen.add(path)
        base = next(b for b in reversed(search) if path.is_relative_to(b))
        package = list(path.relative_to(base).parts[:-1])
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call):
                called = node.func.id if isinstance(node.func, ast.Name) else ""
                if called in {"eval", "exec", "__import__"}:
                    raise ValueError("unreviewed dynamic dependency call: " + called)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependency(alias.name)
            if isinstance(node, ast.ImportFrom):
                parts = package[: len(package) - node.level + 1] if node.level else []
                parts += node.module.split(".") if node.module else []
                name = ".".join(parts)
                # from package import module: include module when present, but
                # importing a value does not invent a same-named module.
                if name:
                    dependency(name)
                for alias in node.names:
                    child = name + "." + alias.name
                    if name.split(".")[0] in LOCAL_PREFIXES and resolve(child):
                        dependency(child)
    paths = seen | {safe(root / name, root) for name in DATA}
    paths.update(safe(path, root) for path in (root / "scripts").rglob("*.py"))
    # Bind reserved module files and existing namespace initializers as well as names.
    for relative, names in FILES.items():
        for name in names:
            path = root / relative / name
            if path.exists():
                paths.add(safe(path, root))
    for relative, names in DIRECTORIES.items():
        for name in names:
            path = root / relative / name / "__init__.py"
            if path.exists():
                paths.add(safe(path, root))
    # These are precisely the staging-read families, not broad source inventories.
    for directory, patterns in (
        (root / "contract/tests/fixtures/u2_b/a2-export", ("*.json", "*.yaml", "PIN")),
        (root / "contract/fixtures/model_shapes", ("*.json",)),
    ):
        for pattern in patterns:
            for path in directory.glob(pattern):
                paths.add(safe(path, root))
    from scripts.vendor_rk import HISTORICAL_MANIFEST_SHA256, PIN

    provenance = root / "contract/provenance" / ("rk-sim@" + PIN) / HISTORICAL_MANIFEST_SHA256
    for path in provenance.rglob("*"):
        if path.is_symlink():
            raise ValueError("support symlink: " + str(path))
        if path.is_file():
            paths.add(safe(path, root))
    return tuple(sorted(paths))


def inventory(*, root: Path = ROOT) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in support_files(root=root)
    }


def verify(expected: dict[str, str], *, policy: object = POLICY, root: Path = ROOT) -> None:
    if policy != POLICY:
        raise ValueError("unrecognized input support policy")
    actual = inventory(root=root)
    if set(actual) != set(expected):
        raise ValueError("input support inventory changed")
    for name, digest in expected.items():
        if actual[name] != digest:
            raise ValueError("input support bytes changed: " + name)
