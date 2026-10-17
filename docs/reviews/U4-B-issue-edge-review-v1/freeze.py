"""Freeze B-owned receipts without publishing raw input archives or authority."""

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path("/tmp/u4-b-issue-edge-01/source")
BUILD = Path("/tmp/u4-b-issue-edge-build-01")
ROOT = HERE.parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


receipts = {
    "reconstruction.json": "/tmp/u4-b-issue-edge-01/reconstruction.json",
    "mapped-runs.json": "/tmp/u4-b-issue-edge-runs-01/runs.json",
    "consumer-controls.json": "/tmp/u4-b-issue-edge-consume-final2/checks.json",
    "checker-fault.json": "/tmp/u4-b-issue-edge-fault-02/checks.json",
    "capacity-fault.json": "/tmp/u4-b-issue-edge-capacity-fault-01/checks.json",
    "inline-readiness-finding.json": "/tmp/u4-b-issue-edge-inline-02/checks.json",
    "inline-readiness-control.json": "/tmp/u4-b-issue-edge-inline-control-01/checks.json",
    "python-checks.json": "/tmp/u4-b-issue-edge-checks-01/checks.json",
    "source-closure.json": "/tmp/u4-b-issue-edge-source-01.json",
}
for name, source in receipts.items():
    shutil.copyfile(source, HERE / name)
build = json.loads((BUILD / "build.json").read_text())
for path, digest in build["private_postimages"].items():
    assert sha(BUILD / "source" / path) == digest
for mode, row in build["commands"].items():
    assert sha(BUILD / (mode + "-target") / row["test_executable"]) == row["test_executable_sha256"]
manifest = json.loads(
    (ROOT / "docs/reviews/U4-A-issue-edge-amendment-v1/manifest.json").read_text()
)
assert all(sha(SOURCE / r["path"]) == r["postimage_sha256"] for r in manifest["files"])
compact = {k: v for k, v in build.items() if k != "cache"}
compact["complete_build_receipt"] = dict(
    path=str(BUILD / "build.json"), sha256=sha(BUILD / "build.json")
)
compact["cache_reverified_files"] = len(build["cache"])
compact["cache_inventory_source"] = "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json"
compact["cache_inventory_sha256"] = sha(ROOT / compact["cache_inventory_source"])
(HERE / "build-bindings.json").write_text(json.dumps(compact, indent=2) + "\n")
# Preserve exact executed source where formatting/import cleanup subsequently changed it.
executed = HERE / "executed-recipes"
executed.mkdir(exist_ok=True)
transitions = []
for p in Path("/tmp/u4-b-issue-edge-executed-recipes").glob("*.py"):
    target = executed / (p.name + ".txt")
    shutil.copyfile(p, target)
    transitions.append(
        dict(
            path=p.name,
            executed_sha256=sha(p),
            published_sha256=sha(HERE / p.name),
            description=(
                "format/import cleanup; consume_final additionally gains "
                "the pending-only overbooking control"
            ),
        )
    )
(HERE / "recipe-transitions.json").write_text(json.dumps(transitions, indent=2) + "\n")
# Bind raw per-case receipts without copying the generated inputs/results into main.
raw = []
for root in map(
    Path,
    [
        "/tmp/u4-b-issue-edge-runs-01",
        "/tmp/u4-b-issue-edge-inline-02",
        "/tmp/u4-b-issue-edge-inline-control-01",
        "/tmp/u4-b-issue-edge-consume-final2",
        "/tmp/u4-b-issue-edge-checks-01",
    ],
):
    raw.extend(
        dict(path=str(p), sha256=sha(p), bytes=p.stat().st_size)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    )
(HERE / "private-receipt-inventory.json").write_text(json.dumps(raw, indent=2) + "\n")
report = dict(
    package_commit="ddd299ca59a27098da9ce4de1359d43f966aab20",
    source_base=manifest["base_commit"],
    patches=manifest["patches"],
    final_postimages_verified=20,
    native_mapped_case_processes=24,
    additional_inline_readiness_processes=4,
    focused_native_tests_per_mode=9,
    focused_native_test_modes=["debug", "release"],
    python_tests_passed=34,
    synthetic_output_attacks=15,
    structural_refusals=13,
    structural_pass_independent_refusal=["duration-law", "late-issue-edge"],
    issue_edge_defense_count=3,
    exact_restoration=True,
    findings=[
        "B-ISSUE-ORDER-01: native first-eligibility order differs from "
        "timestamp-only checker recurrence"
    ],
    corrected_candidate_published=False,
    inherited_only=[
        "A six native guard fault/restoration results",
        "prior full selections and K2 campaign",
        "existing construction read audit gaps",
    ],
    source_installation=False,
    public_execution=False,
    authority_created=False,
    independent_adversarial_acceptance=False,
    trace_capture_or_build=False,
)
(HERE / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
print("B receipt freeze complete; one unresolved ordering finding")
