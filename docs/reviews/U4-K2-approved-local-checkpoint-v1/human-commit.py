"""Verify exact installed source; stage/commit only on an approved human invocation."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RELEASE = "docs/reviews/U4-K2-approved-local-checkpoint-v1"
PLAN = "docs/reviews/U4-K2-semantic-local-checkpoint-v1/commit-plan.json"
PROPOSAL = "1e48088209b2c3bd8bb5b2c58422cd7473ebc37e"
PLACEMENT = "535b8346d6209e11a50daaa06f8bcf08d8a0d254"
COMMON = "docs/reviews/U4-K2-approved-release-v1/human-install.py"
COMMON_HASH = "70d259c322e0ad8d85e653b48260711163a55501089773212678a740b181cbd1"
MESSAGE = "feat(contract): complete K2 clock and causal observation semantics"


def require(ok, message):
    if not ok:
        raise ValueError("STOP: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    p = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )
    require(p.returncode == 0, p.stderr.decode().strip() or "Git guard failed")
    return p.stdout


def text(root, *args):
    return git(root, *args).decode().strip()


def inspect(root, helper_commit):
    require(re.fullmatch("[0-9a-f]{40}", helper_commit), "full helper commit required")
    require(text(root, "rev-parse", "--show-toplevel") == str(root), "unexpected repository")
    require(text(root, "branch", "--show-current") == "main", "main required")
    require(
        text(root, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    require(not text(root, "diff", "--cached", "--name-only"), "real index must be empty")
    require(
        all(x.startswith(b"H ") for x in git(root, "ls-files", "-v", "-z").split(b"\0") if x),
        "hidden index flags",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        require(
            not Path(
                text(root, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished Git operation",
        )
    head = text(root, "rev-parse", "HEAD")
    for commit in (PLACEMENT, PROPOSAL, helper_commit):
        git(root, "merge-base", "--is-ancestor", commit, head)
    require(
        all(
            x.startswith("docs/reviews/")
            for x in text(root, "diff", "--name-only", PLACEMENT, head).splitlines()
        ),
        "source history moved; reconcile before commit",
    )
    names = text(root, "ls-tree", "-r", "--name-only", helper_commit, "--", RELEASE).splitlines()
    require(
        RELEASE + "/human-commit.py" in names and RELEASE + "/acceptance.json" in names,
        "helper package missing",
    )
    for name in names:
        require(
            (root / name).is_file()
            and (root / name).read_bytes() == git(root, "show", helper_commit + ":" + name),
            "helper package drift: " + name,
        )
    raw = (root / PLAN).read_bytes()
    require(raw == git(root, "show", PROPOSAL + ":" + PLAN), "approved plan drift")
    acceptance = json.loads((root / RELEASE / "acceptance.json").read_text())
    require(
        acceptance["decision"] == "U4-K2-semantic-local-checkpoint-v1"
        and acceptance["status"] == "approved; human local commit pending"
        and acceptance["proposal_commit"] == PROPOSAL
        and acceptance["commit_plan_sha256"] == sha(raw),
        "approval identity mismatch",
    )
    plan = json.loads(raw)
    rows = plan["paths"]
    require(
        len(rows) == len({x["path"] for x in rows}) == acceptance["paths"] == 10,
        "selection differs",
    )
    require(plan["message"] == acceptance["message"] == MESSAGE, "message differs")
    require(
        not acceptance["push_authorized"] and not plan["push_authorized"], "push boundary differs"
    )
    common = root / COMMON
    require(
        sha(common.read_bytes()) == COMMON_HASH
        and common.read_bytes() == git(root, "show", PLACEMENT + ":" + COMMON),
        "shared guard drift",
    )
    spec = importlib.util.spec_from_file_location("approved_placement_guards", common)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.images(root, rows, "after")
    changed = text(root, "diff", "--name-only").splitlines()
    require(
        changed == sorted(x["path"] for x in rows if x["before_sha256"] is not None),
        "unexpected tracked changes",
    )
    git(root, "diff", "--check")
    hook = Path(text(root, "rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-commit"))
    normal = Path(text(root, "rev-parse", "--absolute-git-dir")) / "hooks/pre-commit"
    require(
        hook.resolve() == normal.resolve() and hook.is_file() and os.access(hook, os.X_OK),
        "normal executable pre-commit hook required",
    )
    require(
        all(
            s in hook.read_text()
            for s in ("scripts/hooks/human_owned.sh", "scripts/hooks/frozen_predictions.sh")
        ),
        "required hooks missing",
    )
    return head, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--commit", action="store_true", help="human commit; default only verifies")
    args = parser.parse_args()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        require(not os.environ.get(key), "Git override present: " + key)
    require(not args.commit or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    root = Path(__file__).resolve().parents[3]
    head, rows = inspect(root, args.helper_commit)
    print(
        json.dumps(
            dict(
                preflight="passed",
                parent=head,
                paths=10,
                message=MESSAGE,
                staged=False,
                committed=False,
                push=False,
            )
        ),
        flush=True,
    )
    if not args.commit:
        print("STOP: read-only checkpoint verification; real index unchanged.")
        return
    require(text(root, "rev-parse", "HEAD") == head, "HEAD moved")
    wanted = sorted(x["path"] for x in rows)
    git(root, "add", "--", *wanted)
    require(
        text(root, "diff", "--cached", "--name-only").splitlines() == wanted, "staged scope differs"
    )
    for row in rows:
        require(
            sha(git(root, "show", ":" + row["path"])) == row["after_sha256"], "staged bytes differ"
        )
    git(root, "diff", "--cached", "--check")
    # Uses normal hooks and the human's environment. Never sets UARCH_HUMAN.
    subprocess.run(["git", "-C", str(root), "commit", "-m", MESSAGE], check=True)
    require(text(root, "rev-parse", "HEAD^") == head, "unexpected commit parent")
    require(
        text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        == wanted,
        "committed scope differs",
    )
    for row in rows:
        require(
            sha(git(root, "show", "HEAD:" + row["path"])) == row["after_sha256"],
            "committed bytes differ",
        )
    require(
        not text(root, "status", "--porcelain", "--untracked-files=no"), "tracked/index not clean"
    )
    print(
        json.dumps(
            dict(
                decision="U4-K2-semantic-local-checkpoint-v1",
                status="human local commit verified",
                helper_commit=args.helper_commit,
                parent=head,
                commit=text(root, "rev-parse", "HEAD"),
                tree=text(root, "rev-parse", "HEAD^{tree}"),
                paths=wanted,
                tracked_and_index_clean=True,
                push_performed=False,
                native_execution_C2_K2_qualification=False,
            ),
            indent=2,
        ),
        flush=True,
    )
    print(
        "STOP: return this receipt. Push, C2, native execution and qualification remain separate."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
