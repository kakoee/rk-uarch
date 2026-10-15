"""Guarded proposal: read-only preflight, or separately authorized human source commit only."""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
BASE = "9b1408437b6dc08d9b77848f5fffe56c0cf1db72"
PINS = {
    "docs/reviews/U4-A-M-package-v1/protected.patch": (
        "d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3"
    ),
    "docs/reviews/U3-B-artifact-dependency-audit-v1/repair.patch": (
        "c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b"
    ),
}


def require(ok, message):
    if not ok:
        raise ValueError("STOP: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    require(result.returncode == 0, result.stderr.decode().strip() or "Git operation failed")
    return result.stdout


def text(root, *args):
    return git(root, *args).decode().strip()


def check_files(root, rows, phase):
    for row in rows:
        relative = Path(row["path"])
        require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and ".git" not in relative.parts,
            "unsafe selection path",
        )
        path = root / relative
        require(
            not any(p.is_symlink() for p in [path, *path.parents] if p != root.parent),
            "symlink in selection path: " + row["path"],
        )
        expected = row[phase + "_sha256"]
        if expected is None:
            require(not path.exists(), "new path already present: " + row["path"])
        else:
            require(
                path.is_file() and sha(path.read_bytes()) == expected,
                phase + " image drift: " + row["path"],
            )


def authorization(record, package_commit, selection_sha, parent):
    require(
        record
        == {
            "format": "uarch-M-policy-install-authorization/1",
            "action": "install-source-only",
            "approved": True,
            "authorizer": "Javid",
            "package_commit": package_commit,
            "selection_sha256": selection_sha,
            "source_parent": parent,
        },
        "authorization does not name this exact source-only selection",
    )


def preview(root, destination, rows, patch_paths):
    with tarfile.open(fileobj=io.BytesIO(git(root, "archive", "HEAD"))) as archive:
        archive.extractall(destination, filter="data")
    subprocess.run(["git", "init", "-q", str(destination)], check=True)
    check_files(destination, rows, "before")
    patches = [str(root / path) for path in patch_paths]
    git(destination, "apply", "--check", *patches)
    git(destination, "apply", *patches)
    check_files(destination, rows, "after")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-commit", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument(
        "--python", required=True, help="existing reviewed CPython >=3.12 interpreter"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--install", action="store_true")
    parser.add_argument("--authorization-commit")
    parser.add_argument("--authorization-record")
    args = parser.parse_args()
    require(
        not args.install or os.environ.get("UARCH_HUMAN") == "1",
        "installation requires a separately authorized human invocation",
    )
    for commit in [args.package_commit, args.expected_head]:
        require(bool(re.fullmatch("[0-9a-f]{40}", commit)), "full commit identities required")
    require(text(ROOT, "rev-parse", "--show-toplevel") == str(ROOT), "unexpected root")
    require(text(ROOT, "branch", "--show-current") == "main", "use normal main")
    require(
        text(ROOT, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    require(text(ROOT, "rev-parse", "HEAD") == args.expected_head, "HEAD moved")
    require(
        not text(ROOT, "status", "--porcelain", "--untracked-files=all"),
        "clean index/worktree required; preserve unrelated work and stop",
    )
    flagged = [entry for entry in git(ROOT, 'ls-files', '-v', '-z').split(b'\0')
               if entry and not entry.startswith(b'H ')]
    require(not flagged, 'index flags may hide source changes')
    for name in ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"]:
        require(
            not Path(
                text(ROOT, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished Git operation",
        )
    for commit in [BASE, args.package_commit]:
        git(ROOT, "merge-base", "--is-ancestor", commit, "HEAD")
    changed = text(ROOT, "diff", "--name-only", BASE, "HEAD").splitlines()
    require(
        all(path.startswith("docs/reviews/") for path in changed),
        "published non-review source changed since audit; refresh readiness package",
    )
    hook = Path(text(ROOT, "rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-commit"))
    normal = Path(text(ROOT, "rev-parse", "--absolute-git-dir")) / "hooks/pre-commit"
    require(
        hook.resolve() == normal.resolve() and hook.is_file() and os.access(hook, os.X_OK),
        "normal executable pre-commit hook required",
    )
    require(
        all(
            item in hook.read_text()
            for item in ["scripts/hooks/human_owned.sh", "scripts/hooks/frozen_predictions.sh"]
        ),
        "normal ownership and prediction hooks required",
    )
    relative = PACKAGE.relative_to(ROOT).as_posix()
    for name in ["human-install.py", "selection.json", "inventory.json", "inputs.json"]:
        path = relative + "/" + name
        require(
            (ROOT / path).read_bytes() == git(ROOT, "show", args.package_commit + ":" + path),
            "package file differs: " + path,
        )
    inputs = json.loads((PACKAGE / "inputs.json").read_text())
    for path, digest in inputs["unchanged_authority_and_environment"].items():
        require(sha((ROOT / path).read_bytes()) == digest, "authority/environment drift: " + path)
    selection = json.loads((PACKAGE / "selection.json").read_text())
    require(
        selection["base_commit"] == BASE and selection["patches"] == PINS, "selection pins differ"
    )
    rows = selection["files"]
    require(
        len(rows) == len({row["path"] for row in rows}) == 32, "selection must be exactly 32 paths"
    )
    for path, digest in PINS.items():
        require(sha((ROOT / path).read_bytes()) == digest, "accepted patch bytes differ: " + path)
        patch_paths = [
            line[6:] for line in (ROOT / path).read_text().splitlines() if line.startswith("+++ b/")
        ]
        require(
            sorted(patch_paths) == sorted(row["path"] for row in rows if row["patch"] == path),
            "patch/selection path mismatch",
        )
    check_files(ROOT, rows, "before")
    if args.install:
        require(
            args.authorization_commit == args.expected_head, "authorization commit must be HEAD"
        )
        require(
            bool(args.authorization_record)
            and args.authorization_record.startswith("docs/reviews/")
            and ".." not in Path(args.authorization_record).parts,
            "committed authorization required",
        )
        record_path = args.authorization_record
        require(
            text(ROOT, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == record_path,
            "authorization commit must contain only its exact decision record",
        )
        record = json.loads(git(ROOT, "show", "HEAD:" + record_path))
        authorization(
            record,
            args.package_commit,
            sha((PACKAGE / "selection.json").read_bytes()),
            text(ROOT, "rev-parse", "HEAD^"),
        )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN", "SHA", "RK", "PARAMS"}
    }
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    prefix = "import sys;sys.path[:0]=['.','src','contract'];assert sys.version_info >= (3,12);"
    strict = [
        args.python,
        "-B",
        "-c",
        prefix + "from scripts import vendor_rk;vendor_rk.main()",
        "--check",
    ]
    subprocess.run(strict, cwd=ROOT, env=env, check=True)
    with tempfile.TemporaryDirectory(prefix="u4-human-install-check-") as temp:
        dest = Path(temp)
        preview(ROOT, dest, rows, PINS)
        command = [
            args.python,
            "-B",
            "-c",
            prefix
            + "import json;from scripts import u2_support;"
            "print(json.dumps(u2_support.inventory()))",
        ]
        actual = json.loads(subprocess.check_output(command, cwd=dest, env=env))
        require(
            actual == json.loads((PACKAGE / "inventory.json").read_text())["closure"],
            "proposed support closure differs; re-audit before installation",
        )
        refused = subprocess.run(strict, cwd=dest, env=env, capture_output=True, text=True)
        require(
            refused.returncode == 1 and "input support inventory changed" in refused.stderr,
            "combined stale-artifact refusal differs",
        )
    print(
        json.dumps(
            {
                "preflight": "passed",
                "head": args.expected_head,
                "paths": len(rows),
                "support_entries": len(actual),
                "installation_authorized_by_this_preflight": False,
            }
        ),
        flush=True,
    )
    if args.check_only:
        print("STOP: read-only preparation; no installation, staging, commit or publication.")
        return
    require(
        text(ROOT, "rev-parse", "HEAD") == args.expected_head
        and not text(ROOT, "status", "--porcelain", "--untracked-files=all"),
        "source moved",
    )
    check_files(ROOT, rows, "before")
    git(ROOT, "apply", "--index", *[str(ROOT / path) for path in PINS])
    check_files(ROOT, rows, "after")
    wanted = sorted(row["path"] for row in rows)
    require(
        text(ROOT, "diff", "--cached", "--name-only").splitlines() == wanted,
        "unexpected staged paths",
    )
    for row in rows:
        require(
            sha(git(ROOT, "show", ":" + row["path"])) == row["after_sha256"],
            "staged postimage differs",
        )
    git(ROOT, "diff", "--cached", "--check")
    # Inherits the HUMAN's environment and normal hooks. Never sets UARCH_HUMAN itself.
    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "commit",
            "-m",
            "feat(u4): install accepted M carriers and selected input support policy",
        ],
        check=True,
    )
    require(
        text(ROOT, "rev-parse", "HEAD^") == args.expected_head, "unexpected source commit parent"
    )
    require(
        text(ROOT, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        == wanted,
        "unexpected committed paths",
    )
    check_files(ROOT, rows, "after")
    require(
        not text(ROOT, "status", "--porcelain", "--untracked-files=all"),
        "post-commit tree not clean",
    )
    print(
        json.dumps(
            {
                "source_commit": text(ROOT, "rev-parse", "HEAD"),
                "tree": text(ROOT, "rev-parse", "HEAD^{tree}"),
                "parent": args.expected_head,
                "paths": wanted,
                "push_performed": False,
            }
        ),
        flush=True,
    )
    print(
        "STOP: hold source commit locally. Old artifact is stale; "
        "freeze/generation/adoption need separate authority."
    )


if __name__ == "__main__":
    main()
