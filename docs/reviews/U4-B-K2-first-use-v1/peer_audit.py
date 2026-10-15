"""Independent conservative loader dependency and explicit read audit; no execution."""

import ast
import hashlib
import json
import sys
from pathlib import Path


def closure(root, entry):
    search = (root, root / "src", root / "contract")
    pending, seen = [], set()

    def resolve(name):
        parts = name.split(".")
        for base in search:
            for n in range(1, len(parts) + 1):
                candidate = base.joinpath(*parts[:n])
                if (candidate / "__init__.py").is_file():
                    pending.append(candidate / "__init__.py")
                if n == len(parts) and candidate.with_suffix(".py").is_file():
                    pending.append(candidate.with_suffix(".py"))

    resolve(entry)
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        assert not path.is_symlink() and path.is_relative_to(root)
        seen.add(path)
        base = next(base for base in reversed(search) if path.is_relative_to(base))
        package = list(path.relative_to(base).parts[:-1])
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolve(alias.name)
            elif isinstance(node, ast.ImportFrom):
                prefix = package[: len(package) - node.level + 1] if node.level else []
                prefix += node.module.split(".") if node.module else []
                name = ".".join(prefix)
                resolve(name)
                for alias in node.names:
                    resolve(name + "." + alias.name)
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(seen)
    }


def audit(root, saved, authority, output):
    opens = []

    def on_open(event, args):
        if event == "open" and isinstance(args[0], str):
            opens.append(str(Path(args[0]).resolve()))

    sys.addaudithook(on_open)
    from uarch_contract.mapped import NativeEngineIdentity

    from rkuarch.workload.mapped import load_fixed_delay_job

    # The test-host file was frozen separately from the mutable saved input.
    host = json.loads(authority.read_bytes())
    host["expected_engine"] = NativeEngineIdentity.model_validate(host["expected_engine"])
    opens.clear()
    job = load_fixed_delay_job(saved, **host)
    load_reads = list(opens)
    assert load_reads == [str(saved.resolve())]
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"rkuarch", "uarch_contract"}:
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(root), (name, path)
            origins[name] = str(path.relative_to(root))
    static = closure(root, "rkuarch.workload.mapped")
    assert set(origins.values()) == set(static)
    from uarch_contract.hashing import content_hash

    from scripts import u2_support, vendor_rk

    selected = u2_support.inventory(root=root)
    adopted = root / "contract/vendor" / ("rk-sim@" + vendor_rk.PIN)
    vendor_rk.check_manifest(adopted, vendor_rk.PIN)
    vendor_rk.check_snapshot_inputs(adopted)
    vendor_rk.check_generator(adopted, current=True)
    assert "src/rkuarch/workload/mapped.py" not in selected
    receipt = dict(
        source_commit="821dc908a3735ef3225f16b56172e802095d77f0",
        loader_commit="f213317ec61622c91e74c9f42e95578e80432588",
        synthetic_host_only=True,
        job_hash=job.job_hash,
        static_local_loader_closure=static,
        runtime_origins=origins,
        load_reads=load_reads,
        implicit_authority_reads=[],
        selected_count=len(selected),
        selected_hash=content_hash(selected),
        strict_currentness="passed",
        lifecycle_required_for_observed_delta=False,
    )
    output.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    audit(*map(Path, sys.argv[1:]))
