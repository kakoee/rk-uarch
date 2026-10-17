"""Read-only final source/support audit; no generation, authority resolution or execution."""

import ast
import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
PRIVATE = Path(sys.argv[1]).resolve()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(path, name):
    source = path.read_text()
    node = next(
        n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    return ast.get_source_segment(source, node)


# Reuse the unchanged conservative import walker, with explicit roots on both sides.
prior = ROOT / "docs/reviews/U4-B-component-joins-v2/audit_peer.py"
closure = runpy.run_path(str(prior))["closure"]
old_a = json.loads(
    (ROOT / "docs/reviews/U4-A-component-release-v1/closure-and-identity.json").read_text()
)
edges = {}
for module in old_a["runtime_import_edges"]:
    before, after = closure(ROOT, module), closure(PRIVATE, module)
    delta = {
        p: dict(base=before.get(p), postimage=after.get(p))
        for p in sorted(before.keys() | after.keys())
        if before.get(p) != after.get(p)
    }
    edges[module] = dict(files=after, actual_deltas=delta)
# Inventory selects source/data from its explicit root; it does not import the candidate.
sys.path.insert(0, str(ROOT))
from scripts.u2_support import inventory  # noqa: E402

before, after = inventory(root=ROOT), inventory(root=PRIVATE)
support_delta = {
    p: dict(base=before.get(p), postimage=after.get(p))
    for p in sorted(before.keys() | after.keys())
    if before.get(p) != after.get(p)
}
native = old_a["native_source_unchanged"]
for path, digest in native.items():
    assert sha(ROOT / path) == sha(PRIVATE / path) == digest
mapped = "contract/uarch_contract/mapped.py"
assert function(ROOT / mapped, "validate_fixed_delay_observations") == function(
    PRIVATE / mapped, "validate_fixed_delay_observations"
)
assert function(ROOT / mapped, "canonical_owners") == function(PRIVATE / mapped, "canonical_owners")
coordinator = json.loads((ROOT / "docs/reviews/U4-component-stage2-v1/checks.json").read_text())
k2 = coordinator["k2_dependency"]
assert sha(ROOT / mapped) == sha(Path(k2["sealed_path"])) == k2["old_sha256"]
root_artifacts = {}
for path, record in k2["read_only_record_hashes"].items():
    file = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1") / path
    root_artifacts[str(file)] = dict(actual_sha256=sha(file), coordinator_sha256=record["sha256"])
    assert sha(file) == record["sha256"]
tpu = {}
for path in sorted((ROOT / "validation/L3_silicon/tpu-v5e").rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts:
        relative = str(path.relative_to(ROOT))
        historical = subprocess.check_output(["git", "show", "2c62a0f:" + relative], cwd=ROOT)
        assert hashlib.sha256(historical).hexdigest() == sha(path) == sha(PRIVATE / relative)
        tpu[relative] = sha(path)
result = dict(
    scope="author preparation only",
    reused_import_walker_sha256=sha(prior),
    source_commit=subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip(),
    selected_support=dict(
        before=before,
        after=after,
        count=len(after),
        actual_deltas=support_delta,
        human_U0002_generation_required=bool(support_delta),
    ),
    runtime_import_edges=edges,
    native_unchanged=native,
    fixed_delay_helper_unchanged=True,
    canonical_owners_unchanged=True,
    old_K2_sealed_mapped_sha256=k2["old_sha256"],
    old_K2_artifacts=root_artifacts,
    tpu_preserved_from="2c62a0f",
    tpu_files=tpu,
    human_workings={
        name: (ROOT / ("validation/L1_limits/hand/" + name + ".md")).exists()
        for name in ("H-L1-DMA-01", "H-L1-GEMM-01")
    },
    protected_installation_authorized=False,
    native_execution="not_run",
)
(PACKAGE / "final-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(
    json.dumps(
        dict(
            selected_support=len(after),
            actual_support_deltas=support_delta,
            runtime_closures=len(edges),
            native_files=len(native),
            tpu_files=len(tpu),
        )
    )
)
