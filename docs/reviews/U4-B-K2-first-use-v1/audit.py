"""Read-only host audit, executed with explicit private-export import roots."""

import ast
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from uarch_contract import mapped
from uarch_contract.hashing import content_hash

from scripts import u2_support, vendor_rk


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, output):
    root = root.resolve()
    actual = u2_support.inventory(root=root)
    adopted = root / "contract/vendor" / ("rk-sim@" + vendor_rk.PIN)
    vendor_rk.check_manifest(adopted, vendor_rk.PIN)
    vendor_rk.check_snapshot_inputs(adopted)
    vendor_rk.check_generator(adopted, current=True)
    local_origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"rkuarch", "uarch_contract", "scripts"}:
            path = getattr(module, "__file__", None)
            if path:
                path = Path(path).resolve()
                assert path.is_relative_to(root), (name, path)
                local_origins[name] = str(path.relative_to(root))
    mapped_path = root / "contract/uarch_contract/mapped.py"
    assert Path(mapped.__file__).resolve() == mapped_path
    assert "contract/uarch_contract/mapped.py" not in actual
    assert "src/rkuarch/engines/native/__init__.py" not in actual
    # Run discrimination in another private copy, never in the source under test.
    with tempfile.TemporaryDirectory(prefix="u4-k2-dependencies-") as directory:
        scratch = Path(directory) / "source"
        shutil.copytree(root, scratch)
        before = u2_support.inventory(root=scratch)
        p = scratch / "contract/uarch_contract/mapped.py"
        p.write_text(p.read_text() + "\n# Unreached mapped-carrier mutation control.\n")
        assert u2_support.inventory(root=scratch) == before
        p = scratch / "contract/uarch_contract/__init__.py"
        p.write_text(p.read_text() + "\nfrom . import mapped\n")
        after = u2_support.inventory(root=scratch)
        assert "contract/uarch_contract/mapped.py" in after
        try:
            u2_support.verify(before, root=scratch)
        except ValueError as error:
            assert str(error) == "input support inventory changed"
            refusal = str(error)
        else:
            raise AssertionError("reached carrier mutation was not refused")
        delta = dict(
            added=sorted(after.keys() - before.keys()),
            removed=sorted(before.keys() - after.keys()),
            changed=sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
        )
    imports = [
        ast.unparse(node)
        for node in ast.walk(ast.parse(mapped_path.read_text()))
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    receipt = dict(
        source_commit="4f3be8fab5fea1a030b72d5047677016f261eb5e",
        support_count=len(actual),
        support_inventory_hash=content_hash(actual),
        strict_currentness="passed",
        origins=local_origins,
        mapped_imports=imports,
        mapped_sha256=digest(mapped_path),
        selected_policy_sha256=digest(root / "scripts/u2_support.py"),
        unrelated_mapped_mutation="unchanged inventory",
        initializer_reachability_control=dict(refusal=refusal, delta=delta),
        native_loader="placeholder at pinned source; actual loader audit pending",
    )
    output.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
