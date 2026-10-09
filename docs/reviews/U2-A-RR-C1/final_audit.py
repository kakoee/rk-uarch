"""Bounded changed-path audit; no archive copies or whole-worktree source manifest."""
import hashlib
import json
import subprocess
from pathlib import Path

BASE = "7aab97d35ca554b0477ac5719dfa4e5306f8bbab"
OUT = Path("docs/reviews/U2-A-RR-C1")
BUILD = "src/rkuarch/table/build.py"
TEST = "tests/integration/test_u2_a_condition_order.py"


def git(*args):
    return subprocess.check_output(["git", *args])


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


assert git("rev-parse", "HEAD").decode().strip() == BASE
assert git("branch", "--show-current").decode().strip() == "u2/analytic"
assert git("diff", "--name-only", BASE).decode().splitlines() == [BUILD]
assert not git("diff", "--cached", "--name-only")
subprocess.run(["git", "diff", "--check"], check=True)
baseline = git("show", BASE + ":" + BUILD)
assert Path(BUILD).read_bytes() == baseline.replace(
    b"for p, v in sourced_leaves(b.hardware_spec)",
    b"for p, v in sorted(sourced_leaves(b.hardware_spec), key=lambda item: item[0])",
)
assert digest(BUILD) == "c91880cb7ca8977e6ecf491109a8459394af39c6efab82714d34c8cdd895f9e6"
red = json.loads((OUT / "tests-first.json").read_text())
assert digest(TEST) == red["test_sha256"]
checks = json.loads((OUT / "checks.json").read_text())
assert all(c["returncode"] == 0 for c in checks["runs"])
assert all(digest(p) == h for p, h in checks["source_hashes"].items())
actual = json.loads((OUT / "actual-replay.json").read_text())
assert actual["status"] == "passed"
assert digest(OUT / "actual_replay.py") == actual["harness_sha256"]
assert digest(BUILD) == actual["source_sha256"]
assert digest(TEST) == actual["tests_sha256"]
assert digest(actual["received_report"]) == actual["received_report_file_sha256"]
b = Path("/home/jjaff/AI-infra-simulation/rk-uarch-u2-b/docs/reviews/U2-B-real-report-exits-v1/README.md")
assert digest(b) == "1f7bf648a4f5776b95c8773f9c0e41e38ce44ae316ab414b7077c85f8e98de42"
record = dict(baseline=BASE, tracked_changed_paths=[BUILD], index_empty=True,
              exact_proposed_sort_only=True, public_api_changes=[],
              before_sha256=hashlib.sha256(baseline).hexdigest(), after_sha256=digest(BUILD),
              test_sha256=digest(TEST), source_and_test_equal_to_executed_bytes=True,
              B_handoff_sha256=digest(b), received_report_bytes_unchanged=True,
              support_other_83_unchanged=json.loads((OUT / "support-lifecycle.json").read_text())["unchanged_support_count"] == 83,
              existing_archives="No writes; not recursively rehashed or recopied.",
              cross_worktree_edits=False, proposed_message="fix(u2): stabilize table provenance condition ordering for saved replay")
(OUT / "preservation.json").write_text(json.dumps(record, indent=2) + "\n")
paths = {BUILD, TEST, str(OUT / "changed-paths.json")}
paths.update(str(p) for p in OUT.iterdir() if p.is_file())
(OUT / "changed-paths.json").write_text(json.dumps(dict(
    baseline=BASE, scope="Exact new A author delta only; excludes historical untracked archives",
    proposed_commit_paths=sorted(paths), proposed_message=record["proposed_message"],
    staged=False, committed=False), indent=2) + "\n")
print(json.dumps(dict(changed_paths=len(paths), new_evidence_files=len(paths)-2,
                     new_evidence_bytes=sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),
                     source_sha256=digest(BUILD), handoff_sha256=digest(OUT / "README.md"),
                     changed_paths_sha256=digest(OUT / "changed-paths.json")), indent=2))
