"""Commit the exact approved ten-path adoption locally; --check never stages or commits."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROPOSAL = "60adee9eb57068ec1f43412a1bd307e5c3d61d21"
PLAN = ROOT / "docs/reviews/U4-M-policy-adoption-local-checkpoint-v1/commit-plan.json"
RECEIPT = ROOT / "tables/U4-M-policy-adoption-v1/local-commit.json"


def require(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink: " + str(path))


def git(root, *args, env=None, data=None):
    result = subprocess.run(
        ["git", "-C", str(root), *args], env=env, input=data, capture_output=True
    )
    require(result.returncode == 0, result.stderr.decode().strip() or "Git command refused")
    return result.stdout


def pinned(path, commit):
    safe(path)
    require(
        path.read_bytes() == git(ROOT, "show", commit + ":" + path.relative_to(ROOT).as_posix()),
        "package drift: " + str(path),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--helper-commit", required=True)
    args = parser.parse_args()
    require(
        args.check or os.environ.get("UARCH_HUMAN") == "1", "human commit requires UARCH_HUMAN=1"
    )
    require(
        sys.flags.isolated and sys.dont_write_bytecode and not sys.flags.optimize,
        "use reviewed interpreter with -I -B and no optimization",
    )
    require(sys.prefix == str(ROOT / ".venv"), "wrong interpreter environment")
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "PARAMS",
        "SHA",
        "RK",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(key), "unset " + key)
    pin = args.helper_commit
    require(
        len(pin) == 40 and all(c in "0123456789abcdef" for c in pin), "full helper pin required"
    )
    git(ROOT, "merge-base", "--is-ancestor", PROPOSAL, "HEAD")
    git(ROOT, "merge-base", "--is-ancestor", pin, "HEAD")
    for name in ("human_commit.py", "acceptance.json", "README.md"):
        pinned(HERE / name, pin)
    pinned(PLAN, PROPOSAL)
    plan = json.loads(PLAN.read_bytes())
    approval = json.loads((HERE / "acceptance.json").read_bytes())
    require(
        approval
        == {
            "decision": plan["decision"],
            "status": "approved; human local commit pending",
            "authorizer": "Javid (@jjaffari)",
            "approval": "explicit approval in conversation",
            "proposal_commit": PROPOSAL,
            "commit_plan_sha256": digest(PLAN),
            "expected_tree": plan["expected_tree"],
            "parent": plan["parent"],
            "paths": 10,
            "push_authorized": False,
        },
        "exact approval binding mismatch",
    )
    a = Path(plan["repository"])
    safe(a)
    require(
        git(a, "branch", "--show-current").decode().strip() == plan["branch"] == "main",
        "branch drift",
    )
    require(git(a, "rev-parse", "HEAD").decode().strip() == plan["parent"], "parent drift")
    require(
        git(a, "remote", "get-url", "origin").decode().strip()
        == "https://github.com/kakoee/rk-uarch.git",
        "remote drift",
    )
    require(not git(a, "diff", "--cached", "--name-only").strip(), "index must be empty")
    require(
        all(row.startswith(b"H ") for row in git(a, "ls-files", "-v", "-z").split(b"\0") if row),
        "index flags hide tracked changes",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        path = Path(
            git(a, "rev-parse", "--path-format=absolute", "--git-path", name).decode().strip()
        )
        require(not path.exists(), "unfinished Git operation")
    config = subprocess.run(
        ["git", "-C", str(a), "config", "--get", "core.hooksPath"], capture_output=True
    )
    require(config.returncode == 1 and not config.stdout, "unexpected hooksPath override")
    hook = Path(
        git(a, "rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-commit")
        .decode()
        .strip()
    )
    safe(hook)
    require(hook.is_file() and os.access(hook, os.X_OK), "normal pre-commit hook unavailable")
    require(
        hook.read_bytes() == (ROOT / ".git/hooks/pre-commit").read_bytes(), "normal hook mismatch"
    )
    changed = set(git(a, "diff", "--name-only").decode().splitlines())
    new = set(git(a, "ls-files", "--others", "--exclude-standard").decode().splitlines())
    require(
        changed | new == set(plan["paths"]) and len(plan["paths"]) == 10, "exact ten paths required"
    )
    for name, wanted in plan["paths"].items():
        safe(a / name)
        require(digest(a / name) == wanted, "postimage drift: " + name)
    safe(RECEIPT)
    require(
        RECEIPT.parent.is_dir() and not RECEIPT.exists(),
        "commit receipt exists or placement missing",
    )
    placement = json.loads((RECEIPT.parent / "placement.json").read_bytes())
    require(
        placement["source_commit"] == plan["parent"]
        and placement["candidate_manifest_sha256"] == plan["candidate_manifest_sha256"]
        and placement["changed_paths"] == sorted(plan["paths"]),
        "placement receipt mismatch",
    )
    sys.path[:0] = [str(a), str(a / "src"), str(a / "contract")]
    from scripts import u2_inputs as u
    from scripts import vendor_rk as v
    from tests import u2_refresh

    require(
        u.ROOT == v.ROOT == a and Path(u2_refresh.__file__).resolve().is_relative_to(a),
        "source origin",
    )
    v.check_manifest(u.ADOPTED)
    v.check_snapshot_inputs(u.ADOPTED, check_support=True)
    v.check_generator(u.ADOPTED, current=True)
    review_path = "tests/fixtures/u4_m_policy/received-adoption-review.json"
    u2_refresh.adoption_authority(u.ADOPTED, a / review_path, plan["paths"][review_path])
    with tempfile.TemporaryDirectory(prefix="u4-human-commit-preflight-") as temp:
        temp = Path(temp)
        objects = temp / "objects"
        objects.mkdir()
        old_objects = (
            git(a, "rev-parse", "--path-format=absolute", "--git-path", "objects").decode().strip()
        )
        env = dict(
            os.environ,
            GIT_INDEX_FILE=str(temp / "index"),
            GIT_OBJECT_DIRECTORY=str(objects),
            GIT_ALTERNATE_OBJECT_DIRECTORIES=old_objects,
        )
        git(a, "read-tree", plan["parent"], env=env)
        for name in sorted(plan["paths"]):
            blob = (
                git(a, "hash-object", "-w", "--stdin", env=env, data=(a / name).read_bytes())
                .decode()
                .strip()
            )
            git(a, "update-index", "--add", "--cacheinfo", "100644", blob, name, env=env)
        require(
            git(a, "write-tree", env=env).decode().strip() == plan["expected_tree"],
            "proposed tree mismatch",
        )
    print(
        json.dumps(
            {
                "preflight": "passed",
                "parent": plan["parent"],
                "tree": plan["expected_tree"],
                "paths": 10,
                "staged": False,
                "committed": False,
                "push": False,
            }
        ),
        flush=True,
    )
    if args.check:
        return
    # Human-only local staging/commit; no --no-verify, amended history, or push.
    git(a, "add", "--", *sorted(plan["paths"]))
    require(
        git(a, "diff", "--cached", "--name-only").decode().splitlines() == sorted(plan["paths"]),
        "staged scope",
    )
    require(git(a, "write-tree").decode().strip() == plan["expected_tree"], "staged tree drift")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as message:
        message.write(plan["message"] + "\n")
        message.flush()
        print(git(a, "commit", "--file", message.name).decode(), end="", flush=True)
    commit = git(a, "rev-parse", "HEAD").decode().strip()
    require(git(a, "rev-parse", "HEAD^").decode().strip() == plan["parent"], "commit parent")
    require(
        git(a, "rev-parse", "HEAD^{tree}").decode().strip() == plan["expected_tree"], "commit tree"
    )
    require(
        git(a, "log", "-1", "--format=%B").decode().strip() == plan["message"], "commit message"
    )
    require(
        not git(a, "status", "--porcelain", "--untracked-files=all").strip(),
        "A not clean after commit",
    )
    receipt = {
        "decision": plan["decision"],
        "status": "human local commit verified",
        "commit": commit,
        "parent": plan["parent"],
        "tree": plan["expected_tree"],
        "branch": "main",
        "paths": 10,
        "helper_commit": pin,
        "tracked_and_index_clean": True,
        "push_performed": False,
        "K1_K2_closure": False,
    }
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("STOP: return the commit receipt. Publication, K1 acceptance and K2 remain separate.")


if __name__ == "__main__":
    main()
