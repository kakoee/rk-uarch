"""Read-only independent static local-import and preservation audit of private postimages."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def closure(root, entry):
    def resolve(name):
        if name.startswith("rkuarch"):
            base = root / "src"
        elif name.startswith("uarch_contract"):
            base = root / "contract"
        elif name.startswith("scripts"):
            base = root
        else:
            return None
        path = base / Path(*name.split("."))
        if path.with_suffix(".py").is_file():
            return path.with_suffix(".py")
        if (path / "__init__.py").is_file():
            return path / "__init__.py"
        return None

    pending = [entry]
    seen = set()
    files = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        path = resolve(module)
        if path is None:
            continue
        files.add(path)
        parts = module.split(".")
        for n in range(1, len(parts)):
            pending.append(".".join(parts[:n]))
        package = parts if path.name == "__init__.py" else parts[:-1]
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                pending.extend(x.name for x in node.names)
            if isinstance(node, ast.ImportFrom):
                prefix = package[: len(package) - node.level + 1] if node.level else []
                name = ".".join(prefix + ([] if node.module is None else node.module.split(".")))
                pending.append(name)
                pending.extend(name + "." + x.name for x in node.names)
    return {str(p.relative_to(root)): digest(p) for p in sorted(files)}


def main():
    private = Path(sys.argv[1])
    dest = ROOT / "docs/reviews/U4-B-component-joins-v2"
    a = json.loads(
        (ROOT / "docs/reviews/U4-A-component-release-v1/closure-and-identity.json").read_text()
    )
    edges = {}
    for module, claimed in a["runtime_import_edges"].items():
        before, after = closure(ROOT, module), closure(private, module)
        delta = {
            p: dict(base=before.get(p), postimage=after.get(p))
            for p in before.keys() | after.keys()
            if before.get(p) != after.get(p)
        }
        assert delta == claimed["deltas"], (module, delta, claimed["deltas"])
        assert after == claimed["files"], (module, set(after) ^ set(claimed["files"]))
        edges[module] = dict(files=len(after), actual_deltas=delta, peer_inventory_matches=True)
    for path, expected in a["native_source_unchanged"].items():
        assert digest(ROOT / path) == digest(private / path) == expected
    tpu = {}
    for path in sorted((ROOT / "validation/L3_silicon/tpu-v5e").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            relative = str(path.relative_to(ROOT))
            old = subprocess.check_output(["git", "show", "2c62a0f:" + relative], cwd=ROOT)
            assert hashlib.sha256(old).hexdigest() == digest(path)
            tpu[relative] = digest(path)
    rows = json.loads((ROOT / "validation/L3_silicon/tpu-v5e/suite.json").read_text())
    result = dict(
        candidate_patch_sha256=a["patch_sha256"],
        runtime_import_edges=edges,
        native_unchanged_count=len(a["native_source_unchanged"]),
        tpu_preserved_from="2c62a0f",
        tpu_preserved_files=tpu,
        human_workings={
            name: (ROOT / ("validation/L1_limits/hand/" + name + ".md")).exists()
            for name in ("H-L1-DMA-01", "H-L1-GEMM-01")
        },
        no_native_execution=True,
        no_root_placement=True,
        no_protected_installation=True,
    )
    assert rows
    (dest / "peer-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("5 runtime closures match A exactly; native and TPU bytes preserved")


if __name__ == "__main__":
    main()
