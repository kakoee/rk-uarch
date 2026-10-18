"""Human-only installation of the approved four-file typing correction."""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PACKAGE = "docs/reviews/U4-component-runtime-typing-fix-v1"
APPROVED = "fe38338242bb9615a0efff52a04c6f43bb685c93"
PATCH_SHA = "b2109daaca8ecf67e7c59c3f21c79dae429ae86012d2bcd71769d5d34ddb6717"
DECISION = "U4-component-runtime-typing-correction-v1"
ROOT = Path(__file__).resolve().parents[3]
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "PARAMS", "SHA", "RK"):
    ENV.pop(key, None)
ENV["GIT_NO_REPLACE_OBJECTS"] = "1"


def require(value, message):
    if not value:
        raise ValueError("STOP: " + message)


def git(*args, cwd=ROOT):
    proc = subprocess.run(
        ["git", "--no-replace-objects", *args], cwd=cwd, env=ENV, capture_output=True
    )
    require(proc.returncode == 0, proc.stderr.decode().strip() or "Git guard failed")
    return proc.stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def images(root, rows, which):
    for name, row in rows.items():
        path = root / name
        require(all(not p.is_symlink() for p in [path, *path.parents]), "symlink: " + name)
        require(path.is_file() and sha(path.read_bytes()) == row[which], "image drift: " + name)


def preflight(pin):
    require(re.fullmatch(r"[0-9a-f]{40}", pin), "full helper commit required")
    require(git("rev-parse", "--show-toplevel").decode().strip() == str(ROOT), "wrong root")
    require(git("branch", "--show-current").strip() == b"main", "main required")
    require(
        git("remote", "get-url", "origin").strip() == b"https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    require(not git("diff", "--name-only"), "tracked worktree must be clean")
    require(not git("diff", "--cached", "--name-only"), "index must be empty")
    require(
        all(p.startswith(b"H ") for p in git("ls-files", "-v", "-z").split(b"\0") if p),
        "hidden index flags",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        path = git("rev-parse", "--path-format=absolute", "--git-path", name).decode().strip()
        require(not Path(path).exists(), "unfinished Git operation")
    head = git("rev-parse", "HEAD").decode().strip()
    for commit in (pin, APPROVED):
        git("merge-base", "--is-ancestor", commit, head)
    for name in ("human-install.py", "acceptance.json"):
        path = PACKAGE + "/" + name
        require((ROOT / path).read_bytes() == git("show", pin + ":" + path), "helper drift")
    acceptance = json.loads((ROOT / PACKAGE / "acceptance.json").read_bytes())
    require(
        acceptance["decision"] == DECISION and acceptance["reply_verbatim"] == "yes",
        "approval mismatch",
    )
    for name in ("contract-tests-typing.patch", "protected-test-identities.json"):
        path = PACKAGE + "/" + name
        require((ROOT / path).read_bytes() == git("show", APPROVED + ":" + path), "proposal drift")
    patch = ROOT / PACKAGE / "contract-tests-typing.patch"
    require(sha(patch.read_bytes()) == PATCH_SHA, "patch digest")
    rows = json.loads((ROOT / PACKAGE / "protected-test-identities.json").read_bytes())
    require(len(rows) == 4, "exact four-path scope")
    changed = [
        line.split("\t", 2)[2]
        for line in git("apply", "--numstat", str(patch)).decode().splitlines()
    ]
    require(sorted(changed) == sorted(rows), "patch inventory")
    images(ROOT, rows, "before_sha256")
    git("apply", "--check", str(patch))
    return head, rows, patch


def preview(head, rows, patch):
    with tempfile.TemporaryDirectory(prefix="u4-typing-preview-") as temp:
        root = Path(temp)
        with tarfile.open(fileobj=io.BytesIO(git("archive", head))) as archive:
            archive.extractall(root, filter="data")
        git("apply", str(patch), cwd=root)
        images(root, rows, "after_sha256")
        python = str(ROOT / ".venv/bin/python")
        commands = [
            [
                python,
                "-m",
                "mypy",
                "--cache-dir",
                str(root / ".mypy-production"),
                "src",
                "contract/uarch_contract",
                "scripts",
            ],
            [
                python,
                "-m",
                "mypy",
                "--cache-dir",
                str(root / ".mypy-contract"),
                "--no-explicit-package-bases",
                "contract/tests",
            ],
            [
                python,
                "-m",
                "pytest",
                "-q",
                "-c",
                str(root / "pyproject.toml"),
                "--rootdir",
                str(root),
                *[n for n in rows if n.endswith(".py")],
                "validation/component/test_installation_identity.py",
                "validation/component/test_stage2_selection.py",
            ],
        ]
        for command in commands:
            require(
                subprocess.run(command, cwd=root, env=ENV).returncode == 0,
                "private preview check failed",
            )
        images(root, rows, "after_sha256")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    if args.install:
        require(os.environ.get("UARCH_HUMAN") == "1", "human UARCH_HUMAN=1 required")
    head, rows, patch = preflight(args.helper_commit)
    preview(head, rows, patch)
    require(preflight(args.helper_commit) == (head, rows, patch), "source moved during checks")
    print(
        json.dumps(
            dict(
                decision=DECISION,
                preflight="passed",
                parent=head,
                paths=4,
                patch_sha256=PATCH_SHA,
                installation_executed=False,
            )
        ),
        flush=True,
    )
    if not args.install:
        return
    git("apply", str(patch))
    images(ROOT, rows, "after_sha256")
    require(
        sorted(git("diff", "--name-only").decode().splitlines()) == sorted(rows),
        "installed scope mismatch",
    )
    git("add", "--", *sorted(rows))
    require(
        sorted(git("diff", "--cached", "--name-only").decode().splitlines()) == sorted(rows),
        "staged scope mismatch",
    )
    for name, row in rows.items():
        require(sha(git("show", ":" + name)) == row["after_sha256"], "index drift: " + name)
    git("diff", "--cached", "--check")
    print(
        git(
            "commit", "-m", "test(contract): type issue-edge controls and refresh test bindings"
        ).decode()
    )
    require(git("rev-parse", "HEAD^").decode().strip() == head, "commit parent mismatch")
    images(ROOT, rows, "after_sha256")
    require(
        not git("diff", "--name-only") and not git("diff", "--cached", "--name-only"),
        "tracked state not clean after commit",
    )
    print(
        json.dumps(
            dict(
                decision=DECISION,
                status="human local checkpoint verified",
                commit=git("rev-parse", "HEAD").decode().strip(),
                parent=head,
                paths=4,
                pushed=False,
                native_execution=False,
                authority_changed=False,
            ),
            indent=2,
        )
    )
    print("STOP: return receipt for publication. No native execution or authority change.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
