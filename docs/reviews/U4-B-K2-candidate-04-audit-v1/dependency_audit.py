# ruff: noqa: E401, E402, E731, I001, F401, E501
# Exact executed orchestration; preserve import order and origin-observation imports.
from pathlib import Path
import sys, json, hashlib, ast, subprocess

S = Path("/tmp/u4-b-candidate04-audit/reference")
R = S.parent
sys.path[:0] = [str(S), str(S / "src"), str(S / "contract")]
from scripts import u2_support, vendor_rk
from uarch_contract.hashing import content_hash

selected = u2_support.inventory(root=S)
artifact = S / "contract/vendor" / ("rk-sim@" + vendor_rk.PIN)
print("artifact", artifact)
vendor_rk.check_manifest(artifact)
vendor_rk.check_generator(artifact, current=True)
search = (S, S / "src", S / "contract")


def resolve(name):
    out = []
    for base in search:
        p = base.joinpath(*name.split("."))
        for c in (p.with_suffix(".py"), p / "__init__.py"):
            if c.is_file():
                out.append(c)
    assert len(out) <= 1, (name, out)
    return out


queue = [
    S / "src/rkuarch/engines/native/runner.py",
    S / "src/rkuarch/engines/native/host.py",
    S / "native/tools/export_carriers.py",
]
seen = set()
edges = []
external = set()


def dependency(path, name):
    if name.split(".")[0] in ("rkuarch", "uarch_contract", "scripts"):
        found = resolve(name)
        assert found, (path, name)
        for n in range(1, len(name.split("."))):
            found += resolve(".".join(name.split(".")[:n]))
        queue.extend(found)
        edges.extend((str(path.relative_to(S)), str(x.relative_to(S))) for x in found)
    else:
        external.add(name)


while queue:
    p = queue.pop()
    if p in seen:
        continue
    seen.add(p)
    base = next(b for b in reversed(search) if p.is_relative_to(b))
    package = list(p.relative_to(base).parts[:-1])
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n, ast.Import):
            for a in n.names:
                dependency(p, a.name)
        if isinstance(n, ast.ImportFrom):
            parts = package[: len(package) - n.level + 1] if n.level else []
            parts += n.module.split(".") if n.module else []
            name = ".".join(parts)
            if name:
                dependency(p, name)
            for a in n.names:
                child = name + "." + a.name
                if name.split(".")[0] in ("rkuarch", "uarch_contract", "scripts") and resolve(
                    child
                ):
                    dependency(p, child)
receipt = dict(
    source="24fa36803081e5077d5977baa91441a2c8534ec8",
    strict_currentness="passed",
    selected_count=len(selected),
    selected_hash=content_hash(selected),
    selected_files=selected,
    consumer_closure={
        str(p.relative_to(S)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(seen)
    },
    consumer_edges=sorted(set(edges)),
    external_imports=sorted(external),
    origins={m.__name__: m.__file__ for m in [u2_support, vendor_rk]},
    dynamic_reads={
        "host": "explicit independently installed selector; bound files via descriptor walks, both binaries at resolve and selected fd at launch",
        "runner": "explicit saved job; bounded process pipes; private temporary cwd",
        "schema_export": "installed schema + own __file__; writes owned carriers.json only outside --check",
    },
    claim="conservative static local import closure and inspected explicit reads, not complete external-library/environment semantics",
)
(R / "output/dependency-audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(len(selected), len(seen), receipt["selected_hash"])
