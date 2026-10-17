"""Verify by default; human-only exact ADR commit and reviewed immutable root placement."""

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = str(HERE.relative_to(ROOT))
MESSAGE = "docs(u4): accept reviewed combined K2 runtime coexistence"


def need(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args, data=None):
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1")
    result = subprocess.run(
        ["/usr/bin/git", "--no-replace-objects", "-C", str(ROOT), *args],
        input=data,
        env=environment,
        capture_output=True,
        check=False,
    )
    need(result.returncode == 0, result.stderr.decode().strip() or "Git check failed")
    return result.stdout


def text(*args):
    return git(*args).decode().strip()


def preflight(helper):
    need(re.fullmatch(r"[0-9a-f]{40}", helper), "full helper commit required")
    need(text("rev-parse", "--show-toplevel") == str(ROOT), "repository differs")
    need(text("branch", "--show-current") == "main", "main required")
    need(text("rev-parse", "HEAD") == helper, "HEAD must equal reviewed helper commit")
    need(
        text("remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "origin differs",
    )
    need(not text("status", "--porcelain", "--untracked-files=no"), "tracked/index dirty")
    need(
        all(row.startswith(b"H ") for row in git("ls-files", "-v", "-z").split(b"\0") if row),
        "hidden index flags",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        target = Path(text("rev-parse", "--path-format=absolute", "--git-path", name))
        need(not target.exists(), "unfinished Git operation")
    names = text("ls-tree", "-r", "--name-only", helper, "--", PACKAGE).splitlines()
    need(
        {
            PACKAGE + "/human-install.py",
            PACKAGE + "/installation.json",
            PACKAGE + "/postimages.json",
        }.issubset(names),
        "published helper package missing",
    )
    for name in names:
        need((ROOT / name).read_bytes() == git("show", helper + ":" + name), "helper drift")
    plan = json.loads((HERE / "installation.json").read_bytes())
    need(
        digest((HERE / "postimages.json").read_bytes()) == plan["postimages_sha256"],
        "postimage inventory drift",
    )
    approval = ROOT / plan["decision_path"]
    need(digest(approval.read_bytes()) == plan["decision_sha256"], "decision drift")
    need(
        approval.read_bytes() == git("show", plan["decision_commit"] + ":" + plan["decision_path"]),
        "published decision differs",
    )
    git("merge-base", "--is-ancestor", plan["decision_commit"], helper)
    decision = json.loads(approval.read_bytes())
    need(
        decision["reply_verbatim"] == "yes"
        and decision["accepted"] is True
        and decision["conditions"] == [],
        "actual accepted decision required",
    )
    for item in plan["patches"]:
        need(digest((ROOT / item["path"]).read_bytes()) == item["before"], "ADR preimage drift")
        raw = (ROOT / item["patch"]).read_bytes()
        need(digest(raw) == item["patch_sha256"], "patch drift")
        need(
            raw == git("show", plan["reviewed_helper"] + ":" + item["patch"]),
            "reviewed patch differs",
        )
        git("apply", "--check", "-", data=raw)
    script = Path(plan["prepared_script"]).read_bytes()
    need(digest(script) == plan["placement_script_sha256"], "placement script drift")
    target = Path(plan["runtime_root"])
    need(not target.exists() and not target.is_symlink(), "new runtime root already exists")
    for parent in target.parents:
        s = parent.lstat()
        need(
            stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022,
            "unsafe runtime parent: " + str(parent),
        )
    hook = Path(text("rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-commit"))
    normal = Path(text("rev-parse", "--absolute-git-dir")) / "hooks/pre-commit"
    need(hook.resolve() == normal.resolve(), "nonstandard hooks path")
    need(hook.is_file() and os.access(hook, os.X_OK), "normal executable hook required")
    need(
        all(x in hook.read_text() for x in ("human_owned.sh", "frozen_predictions.sh")),
        "required hooks missing",
    )
    text("var", "GIT_AUTHOR_IDENT")
    text("var", "GIT_COMMITTER_IDENT")
    return plan, script


def verify_placement(plan):
    root = Path(plan["runtime_root"])
    expected = json.loads((HERE / "postimages.json").read_bytes())
    files = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    need(files == set(expected), "placed membership differs")
    dirs = {"authority"}
    for name in expected:
        dirs.update(str(p) for p in Path(name).parents if str(p) != ".")
    need(
        {str(p.relative_to(root)) for p in root.rglob("*") if p.is_dir()} == dirs,
        "placed directories differ",
    )
    for path in (root, *root.rglob("*")):
        s = path.lstat()
        need(
            s.st_uid == 0 and s.st_gid == 0 and not s.st_mode & 0o222,
            "placed owner/mode differs",
        )
        need(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode), "nonregular placed path")
        need(stat.S_IMODE(s.st_mode) == (0o555 if path.is_dir() else 0o444), "exact mode")
        if path.is_file():
            need(s.st_nlink == 1, "placed file has another link")
            need(
                "sha256:" + digest(path.read_bytes()) == expected[str(path.relative_to(root))],
                "placed content differs",
            )
    need(not any((root / "authority").iterdir()), "authority unexpectedly populated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    need(not args.install or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    plan, script = preflight(args.helper_commit)
    print(json.dumps({"preflight": "passed", "ADR_paths": 2, "payload_files": 40}), flush=True)
    if not args.install:
        print("Read-only verification only; no staging, commit, sudo or execution.")
        return
    need(text("rev-parse", "HEAD") == args.helper_commit, "HEAD moved")
    for item in plan["patches"]:
        git("apply", "-", data=(ROOT / item["patch"]).read_bytes())
        need(digest((ROOT / item["path"]).read_bytes()) == item["after"], "ADR postimage differs")
    paths = sorted(item["path"] for item in plan["patches"])
    need(text("diff", "--name-only").splitlines() == paths, "unexpected changed paths")
    git("add", "--", *paths)
    need(text("diff", "--cached", "--name-only").splitlines() == paths, "staged scope differs")
    for item in plan["patches"]:
        need(digest(git("show", ":" + item["path"])) == item["after"], "staged bytes differ")
    git("diff", "--cached", "--check")
    # Preserve the human's UARCH_HUMAN; this helper never sets it or disables hooks.
    git("commit", "-m", MESSAGE)
    commit = text("rev-parse", "HEAD")
    need(text("rev-parse", "HEAD^") == args.helper_commit, "commit parent differs")
    need(
        text("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines() == paths,
        "committed scope differs",
    )
    need(not text("status", "--porcelain", "--untracked-files=no"), "tracked/index dirty")
    print(json.dumps({"documentation_commit": commit, "paths": paths, "pushed": False}), flush=True)
    # Execute only the already hash-verified bytes held in memory, never a mutable script path.
    subprocess.run(["sudo", "/bin/sh", "-s"], input=script, check=True)
    verify_placement(plan)
    print(
        json.dumps(
            {
                "decision": "U4-K2-reviewed-runtime-and-restart-v2",
                "status": "human ADR commit and exact immutable payload placement verified",
                "documentation_commit": commit,
                "runtime_root": plan["runtime_root"],
                "payload_files": 40,
                "authority_installed": False,
                "runtime_executed": False,
                "pushed": False,
            },
            indent=2,
        ),
        flush=True,
    )
    print("STOP: return receipts. Approval covers coordinator publication and next preflight.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
