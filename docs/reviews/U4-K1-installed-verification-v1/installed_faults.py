"""Run reviewed K1 fault adapters on an actual installed commit in a new export."""

import argparse
import io
import json
import os
import re
import runpy
import shutil
import sys
import tarfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "U4-B-K1-stage2-reconciliation-v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "UARCH_HUMAN",
        "K1_METADATA",
        "RUSTFLAGS",
        "RUSTDOCFLAGS",
        "CARGO_BUILD_RUSTFLAGS",
        "UARCH_K1_REPLAY_OUT",
    ):
        os.environ.pop(key, None)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    post = runpy.run_path(str(PACKAGE / "post_install.py"))
    adapter = runpy.run_path(str(PACKAGE / "native_check.py"))
    subject = json.loads((PACKAGE / "subject.json").read_text())
    proposal = json.loads((PACKAGE / "inventory.proposed.json").read_text())
    archive, tree = post["committed_source"](args.repo.resolve(), args.commit, subject)
    work = args.work.resolve()
    assert not work.exists() and not work.is_relative_to(args.repo.resolve())
    assert work.parent == Path("/tmp") and work.name.startswith("u4-b-k1-native-stage2-")
    source, receipts = work / "source", work / "receipts"
    source.mkdir(parents=True)
    receipts.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter="data")
    binding = {
        "kind": "actual installed commit",
        "commit": args.commit,
        "tree": tree,
        "reviewed_proposal_tree": subject["tree"],
        "image_id": subject["image_id"],
    }
    (work / "installed-source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    (work / "image.id").write_text(subject["image_id"] + "\n")
    load = adapter["load"]
    c = load(source / adapter["OLD"] / "construct.py", "installed_construct")
    c.container = adapter["seeded_container"](c.container)
    print("Installed-source baseline verification", flush=True)
    c.verify(work, proposal["replay_test"])
    plan = json.loads((receipts / "test-plan.candidate.json").read_text())
    assert plan["test_names"] == proposal["test_names"]
    assert (
        json.loads((receipts / "verified.json").read_text())["canonical_payload_sha256"]
        == proposal["canonical_payload_sha256"]
    )
    controls = load(source / adapter["OLD"] / "controls.py", "installed_controls")
    controls.c.container = adapter["seeded_container"](controls.c.container)
    replay_input = work / "explicit-replay-control"
    replay_input.mkdir()
    shutil.copyfile(
        PACKAGE / "replay-mutation.proposed.json", replay_input / "replay-mutation.json"
    )
    original_run_path = runpy.run_path

    def paths(path, *positional, **keywords):
        module = original_run_path(path, *positional, **keywords)
        if Path(path).name == "replay_control.py":
            original = module["execute"]
            module["execute"] = types.FunctionType(
                original.__code__,
                {**original.__globals__, "PACKAGE": replay_input},
                original.__name__,
                original.__defaults__,
            )
        return module

    controls.runpy = types.SimpleNamespace(run_path=paths)
    faults = json.loads((PACKAGE / "faults.proposed.json").read_text())["faults"]
    original_failure = controls.failure

    def strict_failure(current, name, argv, diagnostic, extra=()):
        print("Fault: " + name, flush=True)
        original_failure(current, name, argv, diagnostic, extra)
        if name.startswith("semantic-"):
            index, mode = name.removeprefix("semantic-").split("-")
            fault = faults[int(index)]
            stdout = (receipts / (name + ".stdout")).read_text()
            assert json.loads((receipts / (name + ".json")).read_text())["exit"] == 101
            assert "test " + fault["test"] + " ... FAILED" in stdout
            assert "test result: FAILED. 0 passed; 1 failed;" in stdout
            literal = fault["diagnostic"]
            if literal == "owner":
                literal = "foreign owner mutation" if mode == "debug" else "ForeignOwner"
            assert literal in stdout

    controls.failure = strict_failure
    controls.execute(work, [{**f, "diagnostic": re.escape(f["diagnostic"])} for f in faults])
    assert json.loads((receipts / "fault-controls.json").read_text())[
        "source_bytes_and_mtimes_restored"
    ]
    # Reuse the reviewed F5 control code, redirecting ONLY its output/config package.
    f5_output = work / "F5-receipts"
    f5_output.mkdir()
    shutil.copyfile(PACKAGE / "subject.json", f5_output / "subject.json")
    sys.path.insert(0, str(PACKAGE))
    f5 = load(PACKAGE / "linkage_controls.py", "installed_F5")
    original_n = f5.n
    f5.n = types.SimpleNamespace(
        HERE=f5_output,
        sha=original_n.sha,
        load=original_n.load,
        OLD=original_n.OLD,
        PYTHON=original_n.PYTHON,
    )
    sys.argv = [str(PACKAGE / "linkage_controls.py"), "--work", str(work)]
    f5.main()
    (work / "completed.json").write_text(
        json.dumps(
            {
                **binding,
                "semantic_fault_mode_pairs": 22,
                "semantic_restored_positives": 22,
                "F5_faults": 2,
                "F5_positive_controls": 4,
                "inventory_installed": False,
                "qualification": False,
            },
            indent=2,
        )
        + "\n"
    )
    print("Installed-source fault campaign complete; inventory remains a candidate", flush=True)


if __name__ == "__main__":
    main()
