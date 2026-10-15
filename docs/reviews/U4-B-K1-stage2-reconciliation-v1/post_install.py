"""PROPOSAL: collect local evidence after separately authorized source installation.

No source installation, image build/pull, registry operation, CI activation or publication.
Docker execution was unavailable during preparation: the native path is not yet validated.
"""

import argparse
import hashlib
import io
import json
import os
import re
import runpy
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = "docs/reviews/U4-B-K1-environment-v1"
GUARD = "docs/reviews/U4-B-final-reconciliation-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def committed_source(repo, commit, subject):
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit),
        "an actual full installed commit is required; null/base-plus-patch is not one",
    )
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, env=env)

    git("cat-file", "-e", commit + "^{commit}")
    git("merge-base", "--is-ancestor", subject["base_commit"], commit)
    scoped = (
        git(
            "diff",
            "--name-only",
            subject["base_commit"],
            commit,
            "--",
            "native",
            "third_party",
            ".github/check_third_party_patches.py",
            ".github/native-third-party-patches.json",
            "tests/unit/test_third_party_patch_check.py",
        )
        .decode()
        .splitlines()
    )
    require(
        sorted(scoped) == sorted(subject["postimages"]),
        "installed K1 footprint requires new review",
    )
    for name, expected in subject["postimages"].items():
        require(
            hashlib.sha256(git("show", commit + ":" + name)).hexdigest() == expected,
            "installed postimage requires new review: " + name,
        )
    require(
        hashlib.sha256(git("show", commit + ":native/Cargo.lock")).hexdigest()
        == subject["lock_sha256"],
        "installed lock differs",
    )
    # Exports this exact committed object, never uncommitted/live source.
    return git("archive", commit), git("rev-parse", commit + "^{tree}").decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--work", type=Path, required=True, help="new private output directory")
    parser.add_argument("--python", required=True, help="existing host Python with pytest")
    args = parser.parse_args()
    repo, work = args.repo.resolve(), args.work.resolve()
    subject = json.loads((HERE / "subject.json").read_text())
    proposal = json.loads((HERE / "inventory.proposed.json").read_text())
    require(
        not work.exists() and not work.is_relative_to(repo), "new outside-repository work required"
    )
    archive, source_tree = committed_source(repo, args.source_commit, subject)
    # Never set a human flag. Remove ambient import/build overrides for host checks.
    env = os.environ.copy()
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
        env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    work.mkdir()
    source, receipts = work / "source", work / "receipts"
    source.mkdir()
    receipts.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter="data")
    construct = runpy.run_path(str(source / OLD / "construct.py"))
    guard = runpy.run_path(str(source / GUARD / "ci_host_guard.py"))
    construct["installed"](source)
    before = construct["snapshot"](source)
    records = []

    def run(label, command, extra=None):
        require(not (receipts / (label + ".exit")).exists(), "stale receipt: " + label)
        done = subprocess.run(
            command, cwd=source, env={**env, **(extra or {})}, capture_output=True
        )
        (receipts / (label + ".stdout")).write_bytes(done.stdout)
        (receipts / (label + ".stderr")).write_bytes(done.stderr)
        (receipts / (label + ".exit")).write_text(str(done.returncode) + "\n")
        records.append(
            {"label": label, "argv": command, "environment": extra or {}, "exit": done.returncode}
        )
        (receipts / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
        require(done.returncode == 0, label + " failed; retain receipts and stop")
        return done.stdout

    complete = False
    try:
        inspected = json.loads(
            run("image-inspect", ["docker", "image", "inspect", subject["image_id"]])
        )
        require(
            len(inspected) == 1
            and inspected[0]["Id"] == subject["image_id"]
            and inspected[0]["Os"] == "linux"
            and inspected[0]["Architecture"] == "amd64",
            "exact accepted local Linux image unavailable",
        )
        (work / "image.id").write_text(subject["image_id"] + "\n")
        container = construct["container"]
        for stage in ("inspect", "checks"):
            run(
                stage + "-container",
                container(
                    work,
                    [
                        "/bin/bash",
                        str(source / GUARD / "native-container.sh"),
                        str(source),
                        stage,
                        proposal["replay_test"],
                    ],
                    extra=["--env", "PROPTEST_RNG_SEED=41011", "--env", "PROPTEST_CASES=256"],
                ),
            )
        full = json.loads((receipts / "metadata.log").read_text())
        selected = json.loads((receipts / "metadata-target.log").read_text())
        plan = construct["discovery"](
            source,
            full,
            {mode: (receipts / (mode + "-list.log")).read_text() for mode in ("debug", "release")},
            selected,
        )
        require(plan["test_names"] == proposal["test_names"], "reviewed 28-test inventory drift")
        plan.update(
            source_commit=args.source_commit,
            source_tree=source_tree,
            replay_test=proposal["replay_test"],
            replay_output_env="UARCH_K1_REPLAY_OUT",
            image_id=subject["image_id"],
            image_validation_pending=False,
            hosted_ci_pending=True,
            evidence_environment="exact local image; host Python",
            canonical_payload_sha256=proposal["canonical_payload_sha256"],
        )
        guard["validate_results"](source, receipts, plan)
        require(
            digest(receipts / "replay-debug-0.bin") == proposal["canonical_payload_sha256"],
            "equal replays differ from the reviewed Stage 2 payload",
        )
        # Full, unfiltered graph is essential: r-efi's conditional role is in this test.
        # Explicit selection fixes discovery without changing native/ or live CI files.
        boot = (
            "import sys; from pathlib import Path; r=Path.cwd(); "
            "sys.path[:0]=[str(r),str(r/'src'),str(r/'contract')]; "
            "import pytest; sys.exit(pytest.main(sys.argv[1:]))"
        )
        run(
            "python-linkage-and-guards",
            [
                args.python,
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
            ],
            {"K1_METADATA": str(receipts / "metadata.log")},
        )
        binding = {
            "source_commit": args.source_commit,
            "source_tree": source_tree,
            "proposal_tree": subject["tree"],
            "source_root": str(source),
            "image_id": subject["image_id"],
            "lock_sha256": digest(source / "native/Cargo.lock"),
            "all_features": True,
            "target": proposal["target"],
            "metadata_sha256": digest(receipts / "metadata.log"),
            "metadata_target_sha256": digest(receipts / "metadata-target.log"),
            "tool_receipts": {
                tool: digest(receipts / (tool + ".log"))
                for tool in ("rustc", "cargo", "rustfmt", "clippy", "cargo-deny")
            },
            "tool_package_commit": proposal["tool_package_commit"],
            "manual_linkage_exit": 0,
            "fault_campaign_pending": True,
        }
        (receipts / "metadata-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
        (receipts / "inventory.candidate.json").write_text(json.dumps(plan, indent=2) + "\n")
        complete = True
    finally:
        unchanged = before == construct["snapshot"](source)
        (receipts / "completion.json").write_text(
            json.dumps(
                {
                    "checks_completed": complete,
                    "source_bytes_mtimes_unchanged": unchanged,
                    "installation_or_activation": False,
                    "fault_campaign_pending": True,
                    "reviewer_stage3_pending": True,
                },
                indent=2,
            )
            + "\n"
        )
        require(unchanged, "source changed; retain scratch and stop")
    print("Candidate inventory only; retain work/receipts and stop for review. Nothing installed.")


if __name__ == "__main__":
    main()
