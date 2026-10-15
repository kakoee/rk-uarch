"""Read-only K1 Stage 2 proposal audit; native evidence is inherited, never fabricated."""

import hashlib
import io
import json
import os
import re
import runpy
import subprocess
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = Path("/home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/U4-A-K1-stage2-v1")
COORD = ROOT / "docs/reviews/U4-AD-M1-and-K1-reconciliation-v1"
BASE = "9b1408437b6dc08d9b77848f5fffe56c0cf1db72"
TREE = "6d5263e13e43a5dfb44d8addf93cc47cc814a0ac"
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
REPLAY = "4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a"
PYTHON = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
ENV = os.environ.copy()
for key in (
    "PYTHONPATH",
    "MYPYPATH",
    "VIRTUAL_ENV",
    "UARCH_HUMAN",
    "K1_METADATA",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
):
    ENV.pop(key, None)
ENV["PYTHONDONTWRITEBYTECODE"] = "1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (sha(p.read_bytes()), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def main():
    original = snapshot(A)
    identity = json.loads((COORD / "identity.json").read_text())
    package = json.loads((A / "package.json").read_text())
    assert identity["k1_base"] == package["base_commit"] == BASE
    assert identity["k1_review_tree"] == TREE
    assert sha((A / "README.md").read_bytes()) == identity["k1_response_sha256"]
    for file, key in [
        ("proposal.patch", "k1_primary_patch"),
        ("B-guard-proposal.patch", "k1_guard_patch"),
    ]:
        assert sha((A / file).read_bytes()) == identity[key]
    assert package["proposal_patch_sha256"] == identity["k1_primary_patch"]
    assert package["B_guard_proposal_sha256"] == identity["k1_guard_patch"]
    result = {
        "starting_B_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "base_commit": BASE,
        "proposal_tree": TREE,
        "native_execution": "unavailable; inherited A evidence only",
        "checks": [],
    }
    with tempfile.TemporaryDirectory(prefix="u4-b-k1-stage2-") as temporary:
        work = Path(temporary)
        source = work / "source"
        source.mkdir()
        raw = subprocess.check_output(["git", "archive", BASE], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(source, filter="data")
        env = dict(ENV, GIT_ALTERNATE_OBJECT_DIRECTORIES=str(ROOT / ".git/objects"))

        def git(*args, cwd=source, check=True, data=None):
            return subprocess.run(
                ["git", *args], cwd=cwd, env=env, input=data, capture_output=True, check=check
            )

        git("init", "-q")
        git("read-tree", BASE)
        for patch in ("proposal.patch", "B-guard-proposal.patch"):
            git("apply", str(A / patch))
        for item in package["postimages"]:
            assert sha((source / item["path"]).read_bytes()) == item["sha256"]
        git("add", "-f", "--", *identity["k1_changed_paths"])
        assert git("write-tree").stdout.decode().strip() == TREE
        assert sorted(
            git("diff", "--cached", "--name-only", BASE).stdout.decode().splitlines()
        ) == (sorted(identity["k1_changed_paths"]))
        before = snapshot(source)
        postimages = {
            name: sha((source / name).read_bytes()) for name in identity["k1_changed_paths"]
        }
        historical = "docs/reviews/U4-B-K1-environment-v1/register-identity.json"
        assert (source / historical).read_bytes() == (ROOT / historical).read_bytes()
        assert (source / "third_party/patches/0001-u4-k1-register.patch").read_bytes() == (
            ROOT / "third_party/patches/0001-u4-k1-register.patch"
        ).read_bytes()
        checker = runpy.run_path(str(source / ".github/check_third_party_patches.py"))
        checker["check"](source)
        result["chain_controls"] = []
        record = json.loads((source / historical).read_text())
        chain = json.loads((source / checker["CHAIN"]).read_text())
        steps = [record, *chain["followups"]]
        for fault in (
            "missing-first",
            "missing-second",
            "extra",
            "reordered",
            "tampered-first",
            "tampered-second",
            "disconnected",
        ):
            trial = work / fault
            for name in [
                historical,
                checker["CHAIN"],
                record["path"],
                *[s["patch"] for s in steps],
            ]:
                dest = trial / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((source / name).read_bytes())
            if fault.startswith("missing"):
                (trial / steps[int(fault.endswith("second"))]["patch"]).unlink()
            elif fault == "extra":
                (trial / "third_party/patches/0003-unreviewed.patch").write_text("extra")
            elif fault == "reordered":
                first, second = [trial / s["patch"] for s in steps]
                left, right = first.read_bytes(), second.read_bytes()
                first.write_bytes(right)
                second.write_bytes(left)
            elif fault.startswith("tampered"):
                p = trial / steps[int(fault.endswith("second"))]["patch"]
                p.write_bytes(p.read_bytes() + b"\n# tamper\n")
            else:
                p = trial / checker["CHAIN"]
                altered = json.loads(p.read_text())
                altered["followups"][0]["before_sha256"] = "0" * 64
                p.write_text(json.dumps(altered))
            try:
                checker["check"](trial)
            except ValueError as exc:
                result["chain_controls"].append({"fault": fault, "refused": str(exc)})
            else:
                raise AssertionError(fault + " was accepted")
        # Exercise application order as well as numbered patch byte ordering.
        target = work / "chain-order" / record["path"]
        target.parent.mkdir(parents=True)
        installed = (source / record["path"]).read_bytes()
        target.write_bytes(installed)
        order_root = work / "chain-order"
        git("init", "-q", cwd=order_root)
        assert (
            git(
                "apply",
                "--reverse",
                "-",
                cwd=order_root,
                check=False,
                data=(source / steps[0]["patch"]).read_bytes(),
            ).returncode
            != 0
        )
        transitions = []
        for reverse, sequence in ((True, list(reversed(steps))), (False, steps)):
            if not reverse:
                assert (
                    git(
                        "apply",
                        "-",
                        cwd=order_root,
                        check=False,
                        data=(source / steps[1]["patch"]).read_bytes(),
                    ).returncode
                    != 0
                )
            for step in sequence:
                git(
                    "apply",
                    *(["--reverse"] if reverse else []),
                    "-",
                    cwd=order_root,
                    data=(source / step["patch"]).read_bytes(),
                )
                expected = step["before_sha256" if reverse else "after_sha256"]
                assert sha(target.read_bytes()) == expected
                transitions.append({"reverse": reverse, "patch": step["patch"], "sha256": expected})
        assert target.read_bytes() == installed
        result["reverse_forward"] = transitions
        result["wrong_reverse_and_forward_order_refused"] = True
        guard = runpy.run_path(str(source / "docs/reviews/U4-B-native-ci-v1/ci_guard.py"))
        plan = json.loads((A / "B-test-inventory-proposed.json").read_text())
        assert plan["source_commit"] is None
        names = plan["test_names"]
        assert len(names) == len(set(names)) == 28
        for mode in ("debug", "release"):
            listing = (A / f"results/list-{mode}.log").read_text()
            output = (A / f"results/full-{mode}.log").read_text()
            guard["check_tests"](listing, output, names)
            assert "0 filtered out" in output
            assert guard["listed_tests"](listing) == Counter({n: 1 for n in names})
            for fault, changed in [
                (
                    "old19",
                    json.loads((ROOT / ".github/native-k1-tests.json").read_text())["test_names"],
                ),
                ("missing", names[:-1]),
                ("duplicate", names + names[:1]),
                ("extra", names + ["not_a_test"]),
            ]:
                try:
                    guard["check_tests"](listing, output, changed)
                except ValueError:
                    result["checks"].append(mode + " inventory refuses " + fault)
                else:
                    raise AssertionError(fault)
        payloads = []
        for mode in ("debug", "release"):
            for number in range(3):
                log = (A / f"results/replay-{mode}-{number}.log").read_text()
                guard["check_tests"](plan["replay_test"] + ": test\n", log, [plan["replay_test"]])
                matches = re.findall(r"^UARCH_K1_REPLAY_V1=(.*)$", log, re.MULTILINE)
                assert len(matches) == 1
                payloads.append(matches[0].encode())
        assert len(set(payloads)) == 1 and sha(payloads[0]) == REPLAY
        faults = json.loads((A / "fault-anchors.json").read_text())["faults"]
        receipts = json.loads((A / "fault-results.json").read_text())
        assert len(faults) == 11 and len(receipts) == 66
        for fault in faults:
            raw = (source / fault["path"]).read_bytes()
            assert sha(raw) == fault["original_sha256"] and raw.count(fault["before"].encode()) == 1
            assert names.count(fault["test"]) == 1
            for mode in ("debug", "release"):
                for state in ("baseline", "fault", "restored"):
                    entries = [
                        r
                        for r in receipts
                        if (r["fault"], r["mode"], r["state"]) == (fault["name"], mode, state)
                    ]
                    assert len(entries) == 1
                    entry = entries[0]
                    assert entry["exit"] == (101 if state == "fault" else 0)
                    log = (A / "results" / entry["log"]).read_text()
                    assert fault["test"] in log
                    if state == "fault":
                        assert fault["diagnostic"].lower() in log.lower()
                    else:
                        guard["check_tests"](fault["test"] + ": test\n", log, [fault["test"]])
        replay_fault = json.loads(
            (ROOT / "docs/reviews/U4-B-K1-environment-v1/replay-mutation.json").read_text()
        )
        replay_fault["sha256"] = sha((source / replay_fault["path"]).read_bytes())
        assert (source / replay_fault["path"]).read_text().count(replay_fault["before"]) == 1
        (HERE / "replay-mutation.proposed.json").write_text(
            json.dumps(replay_fault, indent=2) + "\n"
        )
        argv = [
            PYTHON,
            "-B",
            "-m",
            "pytest",
            "-c",
            str(source / "pyproject.toml"),
            "--rootdir=" + str(source),
            "-p",
            "no:cacheprovider",
            "--basetemp=" + str(work / "pytest"),
            "-q",
            str(source / "tests/unit/test_third_party.py"),
            str(source / "tests/unit/test_third_party_patch_check.py"),
            str(source / "native/test_register_linkage.py")
            + "::test_native_readme_describes_delivered_boundary",
        ]
        done = subprocess.run(argv, cwd=source, env=ENV, capture_output=True, text=True)
        (HERE / "python-checks.log").write_text(done.stdout + done.stderr)
        assert done.returncode == 0, done.stdout + done.stderr
        assert snapshot(source) == before
        result.update(
            python_command=argv,
            python_exit=done.returncode,
            source_isolation_files=len(before),
            source_bytes_mtimes_unchanged=True,
            inherited_names_per_mode=28,
            inherited_replay_runs=6,
            inherited_replay_sha256=REPLAY,
            inherited_fault_runs=66,
            original_first_record_sha256=sha((source / historical).read_bytes()),
            original_first_patch_sha256=sha((source / steps[0]["patch"]).read_bytes()),
        )
        subject = {
            "kind": "unapplied proposal; not an installed source commit",
            "base_commit": BASE,
            "tree": TREE,
            "primary_patch_sha256": identity["k1_primary_patch"],
            "guard_patch_sha256": identity["k1_guard_patch"],
            "postimages": postimages,
            "lock_sha256": sha((source / "native/Cargo.lock").read_bytes()),
            "tool_package_commit": plan["tool_package_commit"],
            "image_id": IMAGE,
        }
        (HERE / "subject.json").write_text(json.dumps(subject, indent=2) + "\n")
        # Explicitly a proposal identity rather than copying null into an installed-source record.
        plan.pop("source_commit")
        plan.update(
            format="uarch-k1-stage2-proposal/1",
            source=subject,
            test_multiplicity={n: 1 for n in names},
            replay_prefix="UARCH_K1_REPLAY_V1=",
            canonical_payload_sha256=REPLAY,
            native_results="inherited A receipts; not rerun",
            image_validation_pending=True,
        )
        (HERE / "inventory.proposed.json").write_text(json.dumps(plan, indent=2) + "\n")
    assert snapshot(A) == original
    result["A_package_files_unchanged"] = len(original)
    result["scratch_removed"] = True
    (HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
