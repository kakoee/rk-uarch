"""Exact proposal export with existing image: actual native/metadata checks, no installation."""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import runpy
import shutil
import subprocess
import tarfile
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A = Path("/home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/U4-A-K1-stage2-v1")
OLD = "docs/reviews/U4-B-K1-environment-v1"
PYTHON = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seeded_container(original):
    def invoke(work, argv, extra=()):
        return original(
            work, argv, ("--env", "PROPTEST_RNG_SEED=41011", "--env", "PROPTEST_CASES=256", *extra)
        )

    return invoke


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fault-start",
        type=int,
        default=0,
        help="Explicit suffix campaign; earlier receipts remain separate",
    )
    args = parser.parse_args()
    assert 0 <= args.fault_start < 11
    subject = json.loads((HERE / "subject.json").read_text())
    proposal = json.loads((HERE / "inventory.proposed.json").read_text())
    # Fresh, retained scratch for receipt inspection; no source tree is published.
    work = Path(tempfile.mkdtemp(prefix="u4-b-k1-native-stage2-"))
    (HERE / "native-work.json").write_text(
        json.dumps({"work": str(work), "status": "running", "fault_start": args.fault_start}) + "\n"
    )
    source, receipts = work / "source", work / "receipts"
    source.mkdir()
    receipts.mkdir()
    env = os.environ.copy()
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
        env.pop(key, None)
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        GIT_ALTERNATE_OBJECT_DIRECTORIES=str(ROOT / ".git/objects"),
    )
    raw = subprocess.check_output(["git", "archive", subject["base_commit"]], cwd=ROOT, env=env)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(source, filter="data")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=source, env=env)

    git("init", "-q")
    git("read-tree", subject["base_commit"])
    for name, expected in [
        ("proposal.patch", subject["primary_patch_sha256"]),
        ("B-guard-proposal.patch", subject["guard_patch_sha256"]),
    ]:
        assert sha(A / name) == expected
        git("apply", str(A / name))
    for name, expected in subject["postimages"].items():
        assert sha(source / name) == expected
    git("add", "-f", "--", *subject["postimages"])
    assert git("write-tree").decode().strip() == subject["tree"]
    shutil.rmtree(source / ".git")
    c = load(source / OLD / "construct.py", "stage2_construct")
    c.container = seeded_container(c.container)
    (work / "image.id").write_text(subject["image_id"] + "\n")
    inspect = c.run(receipts, "image-inspect", ["docker", "image", "inspect", subject["image_id"]])
    assert inspect == 0
    data = json.loads((receipts / "image-inspect.stdout").read_text())
    assert len(data) == 1 and data[0]["Id"] == subject["image_id"]
    assert data[0]["Os"] == "linux" and data[0]["Architecture"] == "amd64"
    (HERE / "native-availability.json").write_text(
        json.dumps(
            {
                "argv": ["docker", "image", "inspect", subject["image_id"]],
                "exit": 0,
                "Id": data[0]["Id"],
                "Os": data[0]["Os"],
                "Architecture": data[0]["Architecture"],
                "full_inspection_sha256": sha(receipts / "image-inspect.stdout"),
                "installation_pull_or_activation": False,
            },
            indent=2,
        )
        + "\n"
    )
    print("exact image available; verifying private source", flush=True)
    c.verify(work, proposal["replay_test"])
    plan = json.loads((receipts / "test-plan.candidate.json").read_text())
    assert plan["test_names"] == proposal["test_names"]
    verified = json.loads((receipts / "verified.json").read_text())
    assert verified["canonical_payload_sha256"] == proposal["canonical_payload_sha256"]
    print("full native verification passed; running actual metadata linkage", flush=True)
    metadata = receipts / "metadata-full.stdout"
    # Native paths are identical on host/container. No graph rewriting or synthetic nodes.
    for name in ("metadata-full", "metadata-selected"):
        assert json.loads((receipts / (name + ".json")).read_text())["exit"] == 0
    boot = (
        "import sys;from pathlib import Path;r=Path.cwd();"
        "sys.path[:0]=[str(r),str(r/'src'),str(r/'contract')];"
        "import pytest;sys.exit(pytest.main(sys.argv[1:]))"
    )
    argv = [
        PYTHON,
        "-I",
        "-B",
        "-c",
        boot,
        "-c",
        str(source / "pyproject.toml"),
        "--rootdir=" + str(source),
        "-p",
        "no:cacheprovider",
        "--basetemp=" + str(work / "pytest"),
        "-q",
        str(source / "native/test_register_linkage.py"),
        str(source / "tests/unit/test_third_party.py"),
        str(source / "tests/unit/test_third_party_patch_check.py"),
    ]
    done = subprocess.run(
        argv, cwd=source, env={**env, "K1_METADATA": str(metadata)}, capture_output=True, text=True
    )
    (receipts / "python-linkage.log").write_text(done.stdout + done.stderr)
    assert done.returncode == 0, done.stdout + done.stderr
    binding = {
        "source": subject,
        "source_kind": "unapplied exact proposal; not installed commit",
        "source_root": str(source),
        "lock_sha256": sha(source / "native/Cargo.lock"),
        "all_features": True,
        "target": proposal["target"],
        "metadata_full_sha256": sha(metadata),
        "metadata_selected_sha256": sha(receipts / "metadata-selected.stdout"),
        "metadata_commands": [
            json.loads((receipts / (n + ".json")).read_text())
            for n in ("metadata-full", "metadata-selected")
        ],
        "tools": {
            t: (receipts / (t + ".log")).read_text()
            for t in ("rustc", "cargo", "rustfmt", "clippy", "cargo-deny")
        },
        "manual_python_command": argv,
        "K1_METADATA": str(metadata),
        "manual_python_exit": 0,
    }
    (HERE / "native-metadata-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    shutil.copyfile(metadata, HERE / "cargo-metadata.full.json")
    shutil.copyfile(receipts / "metadata-selected.stdout", HERE / "cargo-metadata.linux.json")
    shutil.copyfile(receipts / "python-linkage.log", HERE / "native-python-linkage.log")
    print("manual linkage passed; running real fault and restoration controls", flush=True)
    controls = load(source / OLD / "controls.py", "stage2_controls")
    controls.c.container = seeded_container(controls.c.container)
    # Preserve every historical source byte. Adapt only the old controller's implicit
    # input directory in memory to this explicit, SHA-bound Stage 2 replay fault.
    replay_input = work / "explicit-replay-control"
    replay_input.mkdir()
    shutil.copyfile(HERE / "replay-mutation.proposed.json", replay_input / "replay-mutation.json")
    original_run_path = runpy.run_path

    def paths(path, *args, **kwargs):
        module = original_run_path(path, *args, **kwargs)
        if Path(path).name == "replay_control.py":
            original = module["execute"]
            globals_copy = {**original.__globals__, "PACKAGE": replay_input}
            module["execute"] = types.FunctionType(
                original.__code__, globals_copy, original.__name__, original.__defaults__
            )
        return module

    controls.runpy = types.SimpleNamespace(run_path=paths)
    faults = json.loads((HERE / "faults.proposed.json").read_text())["faults"][args.fault_start :]
    # A records literal substrings; the old B failure function consumes regexes.
    adapted = [{**fault, "diagnostic": re.escape(fault["diagnostic"])} for fault in faults]
    original_failure = controls.failure

    def strict_failure(work, name, argv, diagnostic, extra=()):
        original_failure(work, name, argv, diagnostic, extra)
        if name.startswith("semantic-"):
            index, mode = name.removeprefix("semantic-").split("-")
            fault = faults[int(index)]
            stdout = (receipts / (name + ".stdout")).read_text()
            status = json.loads((receipts / (name + ".json")).read_text())["exit"]
            assert status == 101
            assert "test " + fault["test"] + " ... FAILED" in stdout
            assert "test result: FAILED. 0 passed; 1 failed;" in stdout
            literal = fault["diagnostic"]
            if literal == "owner":
                literal = "foreign owner mutation" if mode == "debug" else "ForeignOwner"
            assert literal in stdout, "wrong semantic diagnostic"

    controls.failure = strict_failure
    controls.execute(work, adapted)
    assert json.loads((receipts / "isolation.json").read_text())[
        "source_bytes_and_mtimes_unchanged"
    ]
    assert json.loads((receipts / "fault-controls.json").read_text())[
        "source_bytes_and_mtimes_restored"
    ]
    for name in (
        "verified.json",
        "isolation.json",
        "fault-controls.json",
        "fault-release-replay-guard.json",
    ):
        shutil.copyfile(receipts / name, HERE / ("native-" + name))
    # Keep small command/exit/diagnostic receipts; full output stays in private work.
    commands = []
    for command in sorted(receipts.glob("*.json")):
        receipt = json.loads(command.read_text())
        if not isinstance(receipt, dict) or "argv" not in receipt:
            continue
        name = command.stem
        commands.append(
            {
                "name": name,
                "command": json.loads(command.read_text()),
                "exit": receipt["exit"],
                "stdout_sha256": sha(receipts / (name + ".stdout")),
                "stderr_sha256": sha(receipts / (name + ".stderr")),
            }
        )
    (HERE / "native-commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    (HERE / "native-work.json").write_text(
        json.dumps(
            {
                "work": str(work),
                "status": "checks complete; proposal only",
                "source_tree": subject["tree"],
                "fault_start": args.fault_start,
                "fault_names": [f["name"] for f in faults],
                "native_qualification": False,
            },
            indent=2,
        )
        + "\n"
    )
    print("native fault/restoration controls complete", flush=True)


if __name__ == "__main__":
    main()
