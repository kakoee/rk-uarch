"""Verify published evidence joins without rerunning native calls or changing expectations."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from uarch_contract.hashing import content_hash

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(name):
    return json.loads((HERE / name).read_text())


history = read("source-audit.json")["preparation_freeze"]
for name, digest in history["files"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
runs = read("native-runs.json")
final = next(r for r in runs if r["label"] == "integrated")
rows = final["observations"]
assert len(rows) == 276 and final["metadata"]["all_selected_calls_completed"]
assert not final["metadata"]["passed"]
assert len(final["metadata"]["failures"]) == 6
assert {r["case"] for r in rows if "failure" in r} == {"D13-barrier"}
assert Counter((r["expected_layer"], r["rust_outcome"]) for r in rows) == {
    ("result", "success"): 198,
    ("result", "refusal"): 6,
    ("resource-preflight", "refusal"): 48,
    ("profile", "refusal"): 24,
}
for case in {r["case"] for r in rows}:
    same = [r for r in rows if r["case"] == case]
    assert len(same) == 6 and len({r["output_sha256"] for r in same}) == 1
for r in rows:
    assert r["exit_code"] == 0
    if r["rust_outcome"] == "success":
        assert r["independent_check"] == "pass"
assert all(
    r["fresh_processes"] == 6 and r["complete_bytes_equal"] for r in read("supplement-replays.json")
)
for case in ("D01", "B-native-O2"):
    old = next(r for r in runs[0]["observations"] if r["case"] == case)
    new = next(r for r in rows if r["case"] == case)
    assert old["output_sha256"] == new["output_sha256"]
fault = read("collision-fault.json")
assert fault["exact_restoration"] and fault["all_source_postimages_restored"]
assert [r["receipt"]["exit_code"] for r in fault["observations"]] == [101, 0]
forgeries = read("forgeries.json")
assert len(forgeries["records"]) == 26
assert all(r["exact_restoration"] for r in forgeries["restorations"])
missing = next(r for r in forgeries["records"] if r["stage"] == "causes-removed")
assert missing["full_literal_consumer"] == "accepted"
assert all(
    r["independent_v2"] != "accepted"
    for r in forgeries["records"]
    if r["stage"] == "baseline" or r["stage"].endswith("-restored")
)
selection = read("first-use-selection.json")
assert selection["selection_hash"] == content_hash(selection, exclude=("selection_hash",))
assert len(selection["rows"]) == 111
assert "D13-barrier" not in {r["case"] for r in selection["rows"]}
owner = next(r for r in selection["rows"] if r["case"] == "B-native-D13-canonical-owner")
actual = read("supplemental-runs.json")[1]["receipt"]["observations"][0]
assert owner["private_synthetic_job_hash"] == actual["job_hash"]
assert selection["public_binary"] is None and selection["human_authority"] is None
assert not read("read-audit.json")["final_read_closure_accepted"]
print("276 outcomes bound; six D13 failures preserved; restoration and selection joins pass")

final_selection = read("first-use-selection-final.json")
assert final_selection["rows"] == selection["rows"]
assert final_selection["selection_hash"] == content_hash(
    final_selection, exclude=("selection_hash",)
)
assert final_selection["source_candidate"] == "64837bea3724919facbc27be1c7f5644a6354cfa"
projection = read("projection-controls.json")
assert len(projection["observations"]) == 12
for name in ("distinct", "collision"):
    group = [r for r in projection["observations"] if r["case"] == name]
    assert len(group) == 6 and len({r["output_sha256"] for r in group}) == 1
assert len(read("final-delta-runs.json")["observations"]) == 6
assert read("final-delta-runs.json")["passed"]
assert len(read("final-supplement.json")["observations"]) == 4
assert read("runtime-libraries.json")["library_bytes_match_published_A"]
assert read("final-reconciliation.json")["explicit_native_probe_calls_total"] == 324
assert not read("read-audit-final.json")["read_closure_accepted"]
assert read("A-candidate-bindings.json")["source_commit"] == final_selection["source_candidate"]
print("Final-source projection, candidate binaries/runtime and unchanged selection rows joined")
