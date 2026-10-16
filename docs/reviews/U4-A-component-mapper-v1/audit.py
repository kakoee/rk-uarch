"""Read-only static/import/data audit; no authority resolution or native invocation."""

from __future__ import annotations

import ast
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "contract")]
ENTRYPOINTS = ("rkuarch.mapping.component", "rkuarch.workload.component", "rkuarch.workload.mapped")
OPENS: set[str] = set()


def audit(event: str, args: tuple[object, ...]) -> None:
    if event == "open" and isinstance(args[0], str):
        path = Path(args[0]).resolve()
        if (
            path.is_relative_to(ROOT)
            and ".venv" not in path.parts
            and "__pycache__" not in path.parts
        ):
            OPENS.add(str(path.relative_to(ROOT)))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def closure(entry: str) -> dict[str, str]:
    search = (ROOT, ROOT / "src", ROOT / "contract")
    pending: list[Path] = []
    seen: set[Path] = set()

    def resolve(name: str) -> None:
        parts = name.split(".")
        for base in search:
            for count in range(1, len(parts) + 1):
                path = base.joinpath(*parts[:count])
                if (path / "__init__.py").is_file():
                    pending.append(path / "__init__.py")
                if count == len(parts) and path.with_suffix(".py").is_file():
                    pending.append(path.with_suffix(".py"))

    resolve(entry)
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        base = next(b for b in reversed(search) if path.is_relative_to(b))
        package = list(path.relative_to(base).parts[:-1])
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolve(alias.name)
            elif isinstance(node, ast.ImportFrom):
                parts = package[: len(package) - node.level + 1] if node.level else []
                parts += node.module.split(".") if node.module else []
                name = ".".join(parts)
                resolve(name)
                for alias in node.names:
                    resolve(name + "." + alias.name)
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(seen)}


def main() -> None:
    sys.addaudithook(audit)
    from uarch_contract.hashing import canonical_json
    from uarch_contract.mapped import MappedBundle

    from rkuarch.mapping.component import map_component
    from rkuarch.workload.component import component_point, prepare_component_bundle
    from rkuarch.workload.mapped import loads_component_bundle

    b = MappedBundle.model_validate_json(
        (ROOT / "contract/fixtures/mapped/component.json").read_bytes()
    )
    reg = json.loads((ROOT / "contract/fixtures/mapped/registry.json").read_bytes())
    assert b.scope.kind == "component"
    g = map_component(b.scope.ops, b.hardware_spec)
    p = component_point(b.scope.ops, g)
    prepared = prepare_component_bundle(
        b.scope.ops,
        b.hardware_spec,
        p,
        producer=b.producer,
        assumptions=b.assumptions,
        rank=b.rank,
        admission=b.admission,
    )
    loaded = loads_component_bundle(
        canonical_json(prepared),
        invocation="production",
        registry=reg,
        profile=None,
        trusted_registry_hash=reg["registry_hash"],
        trusted_profile_hash=None,
    )
    assert loaded == prepared
    opens = sorted(OPENS)
    origins = {}
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if path and name.startswith(("rkuarch", "uarch_contract")):
            origin = Path(path).resolve()
            assert origin.is_relative_to(ROOT), (name, origin)
            origins[name] = str(origin.relative_to(ROOT))
    from scripts.u2_support import inventory

    selected = inventory(root=ROOT)
    deltas = []
    for path, expected in selected.items():
        before = subprocess.check_output(["git", "show", "490d90b:" + path], cwd=ROOT)
        if hashlib.sha256(before).hexdigest() != expected:
            deltas.append(path)
    result = dict(
        platform=platform.platform(),
        python=sys.version,
        executable=sys.executable,
        root=str(ROOT),
        runtime_origins=origins,
        observed_opens=opens,
        static_closures={e: closure(e) for e in ENTRYPOINTS},
        selected_generation_support=selected,
        selected_delta_from_490d90b=deltas,
        authority="synthetic unit fixture anchors only; no actual host authority read",
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        data_inputs=[
            "contract/fixtures/mapped/component.json",
            "contract/fixtures/mapped/registry.json",
        ],
    )
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
