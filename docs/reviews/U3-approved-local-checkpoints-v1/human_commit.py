"""Human-only two separate local commits. --check is repository-read-only; never pushes."""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parents[2]
PROPOSAL = PRIMARY / "docs/reviews/U3-adoption-checkpoint-and-activation-v1"
PROPOSAL_COMMIT = "26e1badc9295f7fa42daf09e69a7b6c9d5856a22"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def text(root, *args):
    return git(root, *args).decode().strip()


def pinned(path, commit):
    relative = path.relative_to(PRIMARY).as_posix()
    require(path.read_bytes() == git(PRIMARY, "show", commit + ":" + relative), relative + " drift")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--helper-commit")
    args = parser.parse_args()
    require(args.check or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    require(args.check or args.helper_commit, "exact published helper commit required")
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "PARAMS",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(key), key + " must be unset")
    if args.helper_commit:
        require(
            len(args.helper_commit) == 40
            and all(c in "0123456789abcdef" for c in args.helper_commit),
            "full helper commit required",
        )
        for name in ("human_commit.py", "acceptance.json", "README.md"):
            pinned(HERE / name, args.helper_commit)
    for name in ("checkpoint-plan.json", "next-decisions.md", "verification.json"):
        pinned(PROPOSAL / name, PROPOSAL_COMMIT)
    plan = json.loads((PROPOSAL / "checkpoint-plan.json").read_bytes())
    approval = json.loads((HERE / "acceptance.json").read_bytes())
    require(
        approval["decisions"]
        == [plan["adoption_checkpoint"]["decision"], plan["activation"]["decision"]]
        and approval["status"] == "both accepted; human commits pending"
        and approval["proposal_commit"] == PROPOSAL_COMMIT
        and approval["checkpoint_plan_sha256"]
        == digest((PROPOSAL / "checkpoint-plan.json").read_bytes()),
        "exact approval of both decisions required",
    )
    freeze = runpy.run_path(
        str(PRIMARY / "docs/reviews/U3-combined-freeze-proposal-v1/preflight.py")
    )
    freeze["check_proposal"]("70adf0988b218aed895fcf5d2d8b039ca2ba0566")
    a, spec = freeze["A"], freeze["SPEC"]
    freeze["safe"](a)
    require((a / ".git").is_dir() and not (a / ".git").is_symlink(), "independent clone required")
    require(text(a, "branch", "--show-current") == "main", "A must stay on main")
    require(
        text(a, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git", "origin"
    )
    for pending in (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "rebase-merge",
        "rebase-apply",
    ):
        path = Path(text(a, "rev-parse", "--path-format=absolute", "--git-path", pending))
        require(not path.exists(), "unfinished Git operation")
    require(
        all(
            not line or line.startswith(b"H ")
            for line in git(a, "ls-files", "-v", "-z").split(b"\0")
        ),
        "hidden index flags",
    )
    hooks = Path(text(a, "rev-parse", "--path-format=absolute", "--git-path", "hooks"))
    require(hooks.resolve() == a / ".git/hooks", "nonstandard hooks path")
    for name, expected in spec["safety_hooks_sha256"].items():
        path = a / name
        freeze["safe"](path)
        require(
            os.access(path, os.X_OK) and digest(path.read_bytes()) == expected,
            "hook drift: " + name,
        )
    first, second = plan["adoption_checkpoint"], plan["activation"]
    parent = first["parent"]
    require(text(a, "rev-parse", "HEAD") == parent, "reviewed parent changed; do not rerun")
    for ancestor in (spec["human_schema_ancestor"], spec["published_peer_ancestor"]):
        git(a, "merge-base", "--is-ancestor", ancestor, "HEAD")
    require(not text(a, "diff", "--cached", "--name-only"), "index must be empty")

    def check_scope(expected):
        modified = set(text(a, "diff", "--name-only").splitlines())
        untracked = set(text(a, "ls-files", "--others", "--exclude-standard").splitlines())
        require(modified | untracked == set(expected), "unexpected worktree scope")
        for name, sha in expected.items():
            freeze["safe"](a / name)
            require(digest((a / name).read_bytes()) == sha, "live bytes changed: " + name)

    check_scope(first["paths"])
    u, v = freeze["load_source"]()
    from tests.u2_refresh import adoption_authority, audit_candidate

    audit = audit_candidate(u.ADOPTED)
    require(audit["adopted"] is False and audit["rows"] == 1008, "strict snapshot audit")
    review_name = "tests/fixtures/u3_rope/received-adoption-review.json"
    adoption_authority(u.ADOPTED, a / review_name, first["paths"][review_name])
    patch = a / second["patch_path"]
    require(digest(patch.read_bytes()) == second["patch_sha256"], "activation patch drift")
    before = (a / second["path"]).read_bytes()
    require(digest(before) == second["before_sha256"], "activation destination drift")
    require(before == git(a, "show", parent + ":" + second["path"]), "activation already changed")
    with tempfile.TemporaryDirectory(prefix="u3-checkpoint-activation-check-") as tmp:
        scratch = Path(tmp)
        target = scratch / second["path"]
        target.parent.mkdir(parents=True)
        target.write_bytes(before)
        subprocess.run(["git", "apply", "--unidiff-zero", str(patch)], cwd=scratch, check=True)
        require(digest(target.read_bytes()) == second["after_sha256"], "activation result differs")
    receipt_dir = a / "tables/U3-rope-generation-v1/receipts"
    freeze["safe"](receipt_dir)
    require(receipt_dir.is_dir(), "original receipt directory required")
    for name in (
        "adoption-local-commit.json",
        "activation-local-commit.json",
        "local-checkpoints.json",
    ):
        require(not (receipt_dir / name).exists(), "checkpoint receipt exists; do not rerun")
    print(
        json.dumps(
            dict(preflight="passed", adoption_paths=7, activation_paths=1, push=False), indent=2
        )
    )
    if args.check:
        print("Read-only preflight complete. No staging, activation, commit or push.")
        return

    def save(name, value):
        with (receipt_dir / name).open("x") as stream:
            stream.write(json.dumps(value, indent=2) + "\n")

    def commit_exact(expected_parent, paths, message, decision):
        require(text(a, "rev-parse", "HEAD") == expected_parent, "parent changed before staging")
        require(not text(a, "diff", "--cached", "--name-only"), "index changed before staging")
        check_scope(paths)
        subprocess.run(["git", "-C", str(a), "add", "--", *sorted(paths)], check=True)
        require(
            set(text(a, "diff", "--cached", "--name-only").splitlines()) == set(paths),
            "staged scope",
        )
        for name, sha in paths.items():
            require(digest(git(a, "show", ":" + name)) == sha, "staged bytes: " + name)
            require(text(a, "ls-files", "--stage", "--", name).startswith("100644 "), "staged mode")
        subprocess.run(["git", "-C", str(a), "diff", "--cached", "--check"], check=True)
        # UARCH_HUMAN was supplied by the invoking human; normal hooks are never bypassed.
        subprocess.run(["git", "-C", str(a), "commit", "-m", message], check=True)
        commit = text(a, "rev-parse", "HEAD")
        require(text(a, "rev-parse", "HEAD^") == expected_parent, "unexpected committed parent")
        require(text(a, "log", "-1", "--format=%B") == message, "commit message differs")
        require(
            set(text(a, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
            == set(paths),
            "committed scope",
        )
        for name, sha in paths.items():
            require(digest(git(a, "show", "HEAD:" + name)) == sha, "committed bytes: " + name)
        require(
            not text(a, "status", "--porcelain", "--untracked-files=all"), "unclean after commit"
        )
        return dict(
            decision=decision,
            parent=expected_parent,
            commit=commit,
            tree=text(a, "rev-parse", "HEAD^{tree}"),
            paths=sorted(paths),
            pushed=False,
        )

    adoption = commit_exact(parent, first["paths"], first["message"], first["decision"])
    save("adoption-local-commit.json", adoption)
    print(json.dumps(adoption, indent=2), flush=True)
    require(
        digest(patch.read_bytes()) == second["patch_sha256"], "patch moved after adoption commit"
    )
    subprocess.run(
        ["git", "-C", str(a), "apply", "--check", "--unidiff-zero", str(patch)], check=True
    )
    subprocess.run(["git", "-C", str(a), "apply", "--unidiff-zero", str(patch)], check=True)
    activated = {second["path"]: second["after_sha256"]}
    check_scope(activated)
    bootstrap = "import sys;sys.path[:0]=" + repr([str(a), str(a / "src"), str(a / "contract")])
    bootstrap += (
        ";import pytest;raise SystemExit(pytest.main(['-q','contract/tests/test_rotary_v2.py',"
        "'contract/tests/test_rotary_v2_runtime_pending.py']))"
    )
    subprocess.run([sys.executable, "-I", "-B", "-c", bootstrap], cwd=a, check=True)
    activation = commit_exact(adoption["commit"], activated, second["message"], second["decision"])
    save("activation-local-commit.json", activation)
    v.check_manifest(u.ADOPTED)
    v.check_generator(u.ADOPTED, current=True)
    receipt = dict(
        status="two separate human local commits verified",
        helper_commit=args.helper_commit,
        adoption=adoption,
        activation=activation,
        strict_currentness=True,
        tracked_and_index_clean=True,
        full_suite_run=False,
        push_performed=False,
    )
    save("local-checkpoints.json", receipt)
    print(json.dumps(receipt, indent=2))
    print("STOP: return both commit receipts. Final integrated checks and push remain separate.")


if __name__ == "__main__":
    main()
