"""Read-only installed K1 evidence audit and proposal guards. Never executes native tools."""

import ast
import hashlib
import json
import re
import runpy
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PUB = ROOT / "docs/reviews/U4-K1-publication-v1"
FAULT = ROOT / "docs/reviews/U4-K1-installed-verification-v1"
STAGE2 = ROOT / "docs/reviews/U4-B-K1-stage2-reconciliation-v1"
SOURCE = "fb7ba4a75d17650d91c2d2532460ccc1c16b5808"
FAULT_SOURCE = "63ca8bec5a4ac1d7dcf87290a5cf080c846de66d"
PAYLOAD = "4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a"
WRAPPED = "tests/unit/test_third_party_patch_check.py"
OLD = runpy.run_path(str(ROOT / "docs/reviews/U4-B-native-ci-v1/ci_guard.py"))
CONSTRUCT = runpy.run_path(str(ROOT / "docs/reviews/U4-B-K1-environment-v1/construct.py"))
HOST = runpy.run_path(str(ROOT / "docs/reviews/U4-B-final-reconciliation-v1/ci_host_guard.py"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_plan(plan, metadata_binding, listings, outputs, payloads):
    require(plan["source_commit"] == metadata_binding["source_commit"] == SOURCE, "wrong source")
    require(
        plan["source_tree"]
        == metadata_binding["source_tree"]
        == git("rev-parse", SOURCE + "^{tree}").decode().strip(),
        "wrong installed tree",
    )
    require(metadata_binding == read(PUB / "metadata-binding.json"), "metadata binding drift")
    HOST["validate_plan"](plan)
    require(
        len(plan["test_names"]) == len(set(plan["test_names"])) == 28, "28 unique tests required"
    )
    for mode in plan["modes"]:
        OLD["check_tests"](listings[mode], outputs[mode], plan["test_names"])
    require(plan["canonical_payload_sha256"] == PAYLOAD, "stale replay binding")
    require(CONSTRUCT["compare_replays"](payloads) == PAYLOAD, "stale replay payload")
    expected = read(PUB / "inventory.candidate.json")
    require(plan == expected, "candidate field drift")


def reference(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}


def proposed_controls():
    return {
        "format": "uarch-k1-controls/1",
        "source_commit": SOURCE,
        "source_tree": read(PUB / "source-merge.json")["source_tree"],
        "inventory_path": ".github/native-k1-tests.json",
        "inventory_sha256": sha((PUB / "inventory.candidate.json").read_bytes()),
        "historical_inventory": {
            "record_commit": SOURCE,
            "path": ".github/native-k1-tests.json",
            "sha256": sha(git("show", SOURCE + ":.github/native-k1-tests.json")),
            "tested_source_commit": "892b9ee00c485718082e8ea9a765578cbd64d684",
            "test_names_per_mode": 19,
        },
        "subject": reference(PUB / "subject.json"),
        "metadata_binding": reference(PUB / "metadata-binding.json"),
        "replay": {
            "test": "tests::canonical_replay_private_bytes",
            "prefix": "UARCH_K1_REPLAY_V1=",
            "output_env": "UARCH_K1_REPLAY_OUT",
            "canonical_payload_sha256": PAYLOAD,
            "mutation": reference(STAGE2 / "replay-mutation.proposed.json"),
        },
        "semantic_faults": {
            **reference(STAGE2 / "faults.proposed.json"),
            "field": "faults",
            "diagnostics": "literal",
        },
        "fault_evidence": {
            "source_commit": FAULT_SOURCE,
            "source_tree": read(FAULT / "fault-installed-source.json")["tree"],
            "binding": reference(FAULT / "fault-installed-source.json"),
            "completion": reference(FAULT / "fault-completion.json"),
            "commands": reference(FAULT / "fault-command-receipts.json"),
            "F5": reference(FAULT / "F5-controls.json"),
            "reuse_basis": (
                "All native/dependency bytes identical; only non-review delta is approved "
                "AST-identical KI-C1 Python test wrapping."
            ),
            "new_fault_run_on_final_source": False,
        },
        "hosted_ci_pending": True,
        "remote_qualification": False,
    }


def validate_controls(controls):
    require(controls == proposed_controls(), "control binding drift")
    for fault in [
        *read(STAGE2 / "faults.proposed.json")["faults"],
        read(STAGE2 / "replay-mutation.proposed.json"),
    ]:
        raw = git("show", SOURCE + ":" + fault["path"])
        require(raw == git("show", FAULT_SOURCE + ":" + fault["path"]), "fault source drift")
        require(
            sha(raw) == fault.get("original_sha256", fault.get("sha256")), "fault preimage drift"
        )
        require(raw.count(fault["before"].encode()) == 1, "fault anchor not unique")


def validate_subject(subject, original):
    require(set(subject["postimages"]) == set(original["postimages"]), "postimage set drift")
    changed = [
        p for p, digest in subject["postimages"].items() if digest != original["postimages"][p]
    ]
    require(changed == [WRAPPED], "not the one approved exception")
    require(
        subject["postimages"][WRAPPED]
        == "26a882fdb9c0930864e47c88dae36c571085c614c64dd425a1cdbcb66f4c8762",
        "wrong formatting hash",
    )
    comparable = json.loads(json.dumps(subject))
    exception = comparable.pop("approved_exception")
    require(
        exception
        == {
            "decision": "U4-K1-KI-C1-formatting-v1",
            "path": WRAPPED,
            "previous_sha256": original["postimages"][WRAPPED],
            "source_commit": SOURCE,
            "original_tree_is_review_reference_only": True,
        },
        "wrong exception",
    )
    comparable["kind"] = original["kind"]
    comparable["postimages"][WRAPPED] = original["postimages"][WRAPPED]
    require(comparable == original, "subject weakened")


def audit():
    subject, original = read(PUB / "subject.json"), read(STAGE2 / "subject.json")
    validate_subject(subject, original)
    deltas = git("diff", "--name-only", FAULT_SOURCE, SOURCE).decode().splitlines()
    require(
        [p for p in deltas if not p.startswith("docs/reviews/")] == [WRAPPED],
        "unreviewed code delta",
    )
    require(
        ast.dump(ast.parse(git("show", SOURCE + ":" + WRAPPED)))
        == ast.dump(ast.parse(git("show", FAULT_SOURCE + ":" + WRAPPED))),
        "Python AST drift",
    )
    for name, digest in subject["postimages"].items():
        require(
            sha(git("show", SOURCE + ":" + name)) == digest, "installed postimage drift: " + name
        )
    require(sha(git("show", SOURCE + ":native/Cargo.lock")) == subject["lock_sha256"], "lock drift")
    plan, binding = read(PUB / "inventory.candidate.json"), read(PUB / "metadata-binding.json")
    raw = Path(read(PUB / "verification.json")["raw_work"])
    receipts, source = raw / "receipts", raw / "source"
    require(source.exists(), "raw source missing; recreate using pinned installed checker")
    image = read(receipts / "image-inspect.stdout")
    require(
        len(image) == 1
        and image[0]["Id"] == subject["image_id"] == plan["image_id"]
        and image[0]["Os"] == "linux"
        and image[0]["Architecture"] == "amd64",
        "actual image identity differs",
    )
    for name, digest in subject["postimages"].items():
        require(sha((source / name).read_bytes()) == digest, "raw source differs: " + name)
    for name in git("ls-tree", "-r", "--name-only", SOURCE, "--", "native").decode().splitlines():
        require(
            (source / name).read_bytes() == git("show", SOURCE + ":" + name),
            "native export source drift: " + name,
        )
    for label, key, published in [
        ("metadata.log", "metadata_sha256", "cargo-metadata.full.json"),
        ("metadata-target.log", "metadata_target_sha256", "cargo-metadata.linux.json"),
    ]:
        require(
            sha((receipts / label).read_bytes())
            == binding[key]
            == sha((PUB / published).read_bytes()),
            "metadata mismatch",
        )
    listings = {m: (receipts / (m + "-list.log")).read_text() for m in plan["modes"]}
    outputs = {m: (receipts / (m + "-tests.log")).read_text() for m in plan["modes"]}
    payloads = {
        f"{m}-{n}": (receipts / f"replay-{m}-{n}.bin").read_bytes()
        for m in plan["modes"]
        for n in range(3)
    }
    validate_plan(plan, binding, listings, outputs, payloads)
    discovered = CONSTRUCT["discovery"](
        source, read(receipts / "metadata.log"), listings, read(receipts / "metadata-target.log")
    )
    require(discovered["test_names"] == plan["test_names"], "metadata discovery differs")
    HOST["validate_results"](source, receipts, plan)
    for tool, digest in binding["tool_receipts"].items():
        require(sha((receipts / (tool + ".log")).read_bytes()) == digest, "tool receipt drift")
    for item in read(PUB / "commands.json"):
        require(item["exit"] == 0, "failed final-source command")
    command = next(
        c for c in read(PUB / "commands.json") if c["label"] == "python-linkage-and-guards"
    )
    require(
        command["environment"]["K1_METADATA"] == str(receipts / "metadata.log"),
        "manual metadata not joined",
    )
    require(
        "13 passed" in (receipts / "python-linkage-and-guards.stdout").read_text(),
        "manual selection incomplete",
    )
    controls = proposed_controls()
    validate_controls(controls)
    fault_work = Path(read(FAULT / "summary.json")["fault_work"])
    fr = fault_work / "receipts"
    require(
        read(fault_work / "installed-source-binding.json")["commit"] == FAULT_SOURCE,
        "wrong fault source",
    )
    for row in read(FAULT / "fault-command-receipts.json"):
        name = row["name"]
        require(read(fr / (name + ".json")) == row["command"], "fault command mismatch")
        for stream in ("stdout", "stderr"):
            require(
                sha((fr / (name + "." + stream)).read_bytes()) == row[stream + "_sha256"],
                "fault log mismatch",
            )
    for name, digest in original["postimages"].items():
        require(
            sha((fault_work / "source" / name).read_bytes())
            == digest
            == sha(git("show", FAULT_SOURCE + ":" + name)),
            "fault export postimage drift",
        )
    diagnostics = {
        "fault-source": (
            r"no targets specified|couldn.t read|could not read|"
            r"no such file|can.t find"
        ),
        "fault-compile": "U4_B_COMPILE_FAULT",
        "fault-runtime": "U4_B_RUNTIME_FAULT",
        "fault-cache": r"offline|no matching package",
        "fault-toolchain": r"not installed|invalid toolchain",
        "fault-license": "Unicode-3.0",
    }
    for name, pattern in diagnostics.items():
        text = (fr / (name + ".stdout")).read_text() + (fr / (name + ".stderr")).read_text()
        require(
            read(fr / (name + ".json"))["exit"] != 0 and re.search(pattern, text, re.IGNORECASE),
            "generic fault reason differs",
        )
    for name in ("fault-empty", "fault-ignored", "fault-filtered"):
        require(read(fr / (name + "-guard.json"))["refused"], "incomplete selection accepted")
    faults = read(STAGE2 / "faults.proposed.json")["faults"]
    for index, fault in enumerate(faults):
        for mode in plan["modes"]:
            name = f"semantic-{index}-{mode}"
            text = (fr / (name + ".stdout")).read_text()
            literal = fault["diagnostic"]
            if literal == "owner":
                literal = "foreign owner mutation" if mode == "debug" else "ForeignOwner"
            require(
                read(fr / (name + ".json"))["exit"] == 101
                and literal in text
                and "test " + fault["test"] + " ... FAILED" in text
                and "test result: FAILED. 0 passed; 1 failed;" in text,
                "wrong semantic refusal",
            )
            require(read(fr / (name + "-restored.json"))["exit"] == 0, "restoration failed")
            OLD["check_tests"](
                fault["test"] + ": test\n",
                (fr / (name + "-restored.stdout")).read_text(),
                [fault["test"]],
            )
    f5 = read(FAULT / "F5-controls.json")
    require(
        f5["work"] == str(fault_work) and f5["K1_METADATA"] == str(fr / "metadata-full.stdout"),
        "F5 source/graph attribution differs",
    )
    require(
        sha((fr / "metadata-full.stdout").read_bytes()) == f5["metadata_sha256"], "F5 graph drift"
    )
    require(len(f5["records"]) == 6 and f5["source_bytes_mtimes_restored"], "F5 completion differs")
    for record in f5["records"]:
        name = record["fault"] + "-" + record["state"] + ".log"
        require(sha((fr / name).read_bytes()) == record["log_sha256"], "F5 receipt drift")
        require(record["exit"] == (1 if record["state"] == "fault" else 0), "F5 failure")
    require(
        read(fr / "fault-controls.json")["source_bytes_and_mtimes_restored"],
        "fault source not restored",
    )
    require(read(fr / "fault-release-replay-guard.json")["refused"], "replay drift accepted")
    require(
        sha((fr / "restored-release-replay.canonical").read_bytes()) == PAYLOAD,
        "replay restoration differs",
    )
    require(
        sha((fr / "fault-release-replay.canonical").read_bytes()) != PAYLOAD, "replay fault absent"
    )
    return {
        "source_commit": SOURCE,
        "fault_evidence_source": FAULT_SOURCE,
        "AST_identical": True,
        "non_review_delta": [WRAPPED],
        "all_twelve_postimages_verified": True,
        "metadata_and_tools_verified": True,
        "actual_names_per_mode": {
            m: dict(Counter(OLD["listed_tests"](listings[m]))) for m in plan["modes"]
        },
        "six_raw_replay_payloads_sha256": PAYLOAD,
        "inherited_final_source_linkage_checks": 13,
        "inherited_semantic_failures_and_restorations": 22,
        "inherited_F5_failures": 2,
        "inherited_F5_positives": 4,
        "raw_paths_present": [str(raw), str(fault_work)],
        "native_execution_this_task": False,
        "manual_linkage_rerun_this_task": False,
        "old_inventory_sha256": sha((ROOT / ".github/native-k1-tests.json").read_bytes()),
        "old_inventory_names": len(read(ROOT / ".github/native-k1-tests.json")["test_names"]),
        "candidate_sha256": sha((PUB / "inventory.candidate.json").read_bytes()),
        "controls": controls,
    }


if __name__ == "__main__":
    result = audit()
    (HERE / "evidence-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "controls.candidate.json").write_text(json.dumps(result["controls"], indent=2) + "\n")
    print(
        "Host audit passed: installed inventory/metadata and inherited 63ca8be "
        "fault receipts; no native execution"
    )
