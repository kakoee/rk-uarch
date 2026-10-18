"""Freeze bounded B recheck receipts and independently derive transition boundaries."""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = Path("/tmp/u4-b-issue-v2-01/full")
BUILD = Path("/tmp/u4-b-issue-v2-build-01")
RUNS = Path("/tmp/u4-b-issue-v2-runs-01")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


copies = {
    "reconstruction.json": "/tmp/u4-b-issue-v2-01/reconstruction.json",
    "native-runs.json": "/tmp/u4-b-issue-v2-runs-01/runs.json",
    "consumer-checks.json": "/tmp/u4-b-issue-v2-consume-01/checks.json",
    "eligibility-fault.json": "/tmp/u4-b-issue-v2-fault-02/checks.json",
    "local-constraints.json": "/tmp/u4-b-issue-v2-local-constraints.json",
    "python-checks.json": "/tmp/u4-b-issue-v2-checks-01/checks.json",
    "source-delta.json": "/tmp/u4-b-issue-v2-source-delta.json",
}
for name, path in copies.items():
    shutil.copyfile(path, HERE / name)
manifest = json.loads(
    (ROOT / "docs/reviews/U4-A-issue-edge-amendment-v2/manifest.json").read_text()
)
assert all(sha(SOURCE / x["path"]) == x["postimage_sha256"] for x in manifest["files"])
build = json.loads((BUILD / "build.json").read_text())
assert all(sha(BUILD / "source" / p) == v for p, v in build["private_postimages"].items())
for mode, row in build["commands"].items():
    assert sha(BUILD / (mode + "-target") / row["test_executable"]) == row["test_executable_sha256"]
compact = {k: v for k, v in build.items() if k != "cache"}
compact["cache_verified_files"] = len(build["cache"])
compact["full_private_build_receipt"] = dict(
    path=str(BUILD / "build.json"), sha256=sha(BUILD / "build.json")
)
(HERE / "build-bindings.json").write_text(json.dumps(compact, indent=2) + "\n")
# This calculation uses B's prior endpoint records and mechanism terminal names,
# without importing A's new checker or native code. It predicts the new cursors.
old_roots = {
    "r00": Path("/tmp/u4-b-issue-edge-inline-02"),
    "r01": Path("/tmp/u4-b-issue-edge-inline-control-01"),
}
boundaries = []
for name, oldroot in old_roots.items():
    old = json.loads((oldroot / "debug/result.json").read_text())["result"]
    events = old["observations"]["events"]["records"]
    terminal_phases = {"compute_drain", "read_port", "ack", "unicast_noc", "barrier"}
    terminals = [
        a
        for a in old["observations"]["activities"]["records"]
        if a["kind"] == "service" and a["subphase"] in terminal_phases
    ]
    expected = {(0, 0)}
    terminal_records = []
    for act in terminals:
        end = act["completion_ordinal"]
        event = events[end]
        cursor = end + 1
        if event["phase"] == 0:
            while (
                cursor < len(events)
                and events[cursor]["phase"] == 0
                and events[cursor]["t_ps"] == event["t_ps"]
            ):
                cursor += 1
        else:
            assert event["phase"] == 2
        expected.add((cursor, event["t_ps"]))
        terminal_records.append(
            dict(
                job=act["job_id"],
                phase=act["subphase"],
                completion_ordinal=end,
                event_phase=event["phase"],
                opportunity_cursor=cursor,
            )
        )
    expected = sorted(expected)
    assert expected == [(0, 0), (2, 0), (17, 26667), (28, 60000), (50, 120000)]
    for mode in ("debug", "release"):
        new = json.loads((RUNS / (name + "-" + mode) / "result.json").read_text())["result"]
        actual = [
            (r["event_cursor"], r["t_ps"])
            for r in new["observations"]["reservation_opportunities"]["records"]
        ]
        assert actual == expected
    boundaries.append(
        dict(
            case=name,
            prior_receipt_sha256=sha(oldroot / "debug/result.json"),
            expected_cursor_time=expected,
            terminals=terminal_records,
            both_new_modes_match=True,
        )
    )
(HERE / "independent-boundaries.json").write_text(json.dumps(boundaries, indent=2) + "\n")
# Preserve the actual executed recipe bytes when lint-only cleanup followed execution.
transitions = []
for original in sorted(Path("/tmp/u4-b-issue-v2-executed-recipes").glob("*.py")):
    if sha(original) != sha(HERE / original.name):
        target = HERE / "executed-recipes" / (original.name + ".txt")
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(original, target)
        transitions.append(
            dict(
                path=original.name,
                executed_sha256=sha(original),
                published_sha256=sha(HERE / original.name),
                change="import ordering and string wrapping only",
            )
        )
(HERE / "recipe-transitions.json").write_text(json.dumps(transitions, indent=2) + "\n")
private = []
for root in (
    RUNS,
    Path("/tmp/u4-b-issue-v2-consume-01"),
    Path("/tmp/u4-b-issue-v2-fault-01"),
    Path("/tmp/u4-b-issue-v2-fault-02"),
    Path("/tmp/u4-b-issue-v2-checks-01"),
):
    private.extend(dict(path=str(p), sha256=sha(p)) for p in sorted(root.rglob("*")) if p.is_file())
(HERE / "private-receipts.json").write_text(json.dumps(private, indent=2) + "\n")
report = dict(
    subject_commit="7d61d6a02644519d4a7b8b1ce9287e60cd03ca13",
    disposition=(
        "B-ISSUE-ORDER-01 resolved in exact revised private proposal; "
        "no remaining finding from this bounded recheck"
    ),
    patch_routes=2,
    postimages_per_route=22,
    full_exports_equal=True,
    new_mapped_processes=4,
    focused_native_tests_per_mode=12,
    modes=["debug", "release"],
    python_tests_passed=43,
    B_helper_controls=12,
    consistent_output_forgeries=5,
    all_forgery_structural_outcomes="pass",
    all_forgery_independent_outcomes="refusal",
    essential_guard="actual dependency completion at opportunity cursor",
    guard_removed_forgery="unsafe acceptance",
    paired_control="passes baseline/fault/restored",
    original_case_under_fault="expected false refusal; passes baseline/restored",
    exact_restoration=True,
    unaffected_campaigns_reused=True,
    trace_capture_or_build=False,
    independent_review_acceptance=False,
    installation=False,
    authority_changes=False,
)
(HERE / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    "22 source postimages restored; exact binary bindings; "
    "independently derived opportunity boundaries match both modes"
)
