"""Read-only current-clone import/read audit; unit authority is explicitly synthetic."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OPENS: set[str] = set()


def on_audit(event: str, args: tuple[object, ...]) -> None:
    if event == "open" and isinstance(args[0], str):
        path = Path(args[0]).resolve()
        if path.is_relative_to(ROOT) and ".venv" not in path.parts:
            OPENS.add(str(path.relative_to(ROOT)))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_imports(entry: str) -> dict[str, str]:
    """Include local imports in all AST branches and every package initializer."""
    search = (ROOT, ROOT / "src", ROOT / "contract")
    pending = [ROOT / entry]
    seen: set[Path] = set()

    def resolve(name: str) -> None:
        parts = name.split(".")
        for base in search:
            for count in range(1, len(parts) + 1):
                path = base.joinpath(*parts[:count])
                init = path / "__init__.py"
                if init.is_file():
                    pending.append(init)
                if count == len(parts) and path.with_suffix(".py").is_file():
                    pending.append(path.with_suffix(".py"))

    resolve("rkuarch.workload.mapped")
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
            if isinstance(node, ast.ImportFrom):
                parts = package[: len(package) - node.level + 1] if node.level else []
                parts += node.module.split(".") if node.module else []
                name = ".".join(parts)
                resolve(name)
                for alias in node.names:
                    resolve(name + "." + alias.name)
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(seen)}


def main() -> None:
    sys.addaudithook(on_audit)
    from uarch_contract.mapped import NativeEngineIdentity

    from rkuarch.workload.mapped import loads_fixed_delay_job

    fixture = ROOT / "contract/fixtures/mapped/kernel-job.json"
    raw = json.loads(fixture.read_bytes())
    job = loads_fixed_delay_job(
        fixture.read_bytes(),
        trusted_registry_hash=raw["registry"]["registry_hash"],
        trusted_profile_hash=raw["profile"]["profile_hash"],
        expected_engine=NativeEngineIdentity.model_validate(raw["engine"]),
    )
    opens = sorted(OPENS)
    origins = {}
    for name, module in sorted(sys.modules.items()):
        source = getattr(module, "__file__", None)
        if source and name.startswith(("rkuarch", "uarch_contract")):
            path = Path(source).resolve()
            assert path.is_relative_to(ROOT), (name, path)
            origins[name] = str(path.relative_to(ROOT))
    from scripts.u2_support import inventory

    result = {
        "root": str(ROOT),
        "python": sys.version,
        "executable": sys.executable,
        "job_hash": job.job_hash,
        "authority": "synthetic unit control only",
        "runtime_origins": origins,
        "observed_opens_during_import_and_load": opens,
        "static_local_import_closure": static_imports("src/rkuarch/workload/mapped.py"),
        "selected_generation_support": inventory(root=ROOT),
        "data_reads": {str(fixture.relative_to(ROOT)): digest(fixture)},
        "host_authority_reads": [],
        "host_authority_note": "Explicit arguments; no acceptance record installed/read.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
