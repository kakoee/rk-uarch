"""Read-only preflight or exact human placement; never stage, commit, push or build."""

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

RELEASE = "docs/reviews/U4-K2-approved-release-v1"
PROPOSAL = "docs/reviews/U4-K2-joint-candidate-v1"
APPROVED = "4ebec62206edc1a9888c70b74f8093b55440320e"
BASE = "0718955cc0656e5bac4688d4696abbd547cb4186"
PATCH = "775e93b92931ff48b3e5bf9a0de98c7b6d38026f1ff25f9b83db3d56a6f6e7cf"


def require(value, message):
    if not value:
        raise ValueError("STOP: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=env)
    require(result.returncode == 0, result.stderr.decode().strip() or "Git guard failed")
    return result.stdout


def text(root, *args):
    return git(root, *args).decode().strip()


def images(root, rows, phase):
    for row in rows:
        rel = Path(row["path"])
        require(not rel.is_absolute() and not {"..", ".git"} & set(rel.parts), "unsafe path")
        path = root / rel
        current = root
        for part in rel.parts:
            current = current / part
            require(not current.is_symlink(), "symlink in selected path: " + str(rel))
        expected = row[phase + "_sha256"]
        if expected is None:
            require(not path.exists(), "new path already exists: " + str(rel))
        else:
            require(path.is_file() and sha(path.read_bytes()) == expected, phase + ": " + str(rel))


def clean(root):
    require(text(root, "branch", "--show-current") == "main", "main branch required")
    require(not text(root, "status", "--porcelain", "--untracked-files=no"), "tracked/index dirty")
    require(
        all(x.startswith(b"H ") for x in git(root, "ls-files", "-v", "-z").split(b"\0") if x),
        "index flags may hide changes",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        require(
            not Path(
                text(root, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished Git operation",
        )


def preflight(root, package_commit):
    require(re.fullmatch("[0-9a-f]{40}", package_commit), "full package commit required")
    require(text(root, "rev-parse", "--show-toplevel") == str(root), "unexpected repository root")
    require(
        text(root, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    clean(root)
    head = text(root, "rev-parse", "HEAD")
    for ancestor in (BASE, APPROVED, package_commit):
        git(root, "merge-base", "--is-ancestor", ancestor, head)
    require(
        all(
            x.startswith("docs/reviews/")
            for x in text(root, "diff", "--name-only", BASE, head).splitlines()
        ),
        "non-review source advanced; reconcile exact candidate first",
    )
    names = (
        git(root, "ls-tree", "-r", "--name-only", package_commit, "--", RELEASE)
        .decode()
        .splitlines()
    )
    require(
        RELEASE + "/human-install.py" in names and RELEASE + "/acceptance.json" in names,
        "release package missing",
    )
    for name in names:
        require(
            (root / name).is_file()
            and (root / name).read_bytes() == git(root, "show", package_commit + ":" + name),
            "release file differs from pinned commit: " + name,
        )
    for name in ("candidate.json", "combined.proposed.patch", "next-decision.md"):
        rel = PROPOSAL + "/" + name
        require(
            (root / rel).read_bytes() == git(root, "show", APPROVED + ":" + rel),
            "approved proposal drift: " + name,
        )
    acceptance = json.loads((root / RELEASE / "acceptance.json").read_text())
    require(
        acceptance["approval"] == "yes, both" and acceptance["proposal_commit"] == APPROVED,
        "approval binding mismatch",
    )
    accepted = acceptance["decisions"]["U4-K2-semantic-candidate-v1"]
    require(
        accepted["status"] == "approved; guarded human placement pending", "decision not approved"
    )
    raw = (root / PROPOSAL / "candidate.json").read_bytes()
    candidate = json.loads(raw)
    patch = root / PROPOSAL / "combined.proposed.patch"
    require(sha(raw) == accepted["candidate_sha256"], "candidate identity differs")
    require(sha(patch.read_bytes()) == PATCH == accepted["combined_patch_sha256"], "patch differs")
    rows = candidate["paths"]
    require(
        len(rows) == len({x["path"] for x in rows}) == accepted["paths"] == 10, "wrong selection"
    )
    require(
        sorted(x[6:] for x in patch.read_text().splitlines() if x.startswith("+++ b/"))
        == sorted(x["path"] for x in rows),
        "patch selection differs",
    )
    images(root, rows, "before")
    git(root, "apply", "--check", str(patch))
    return head, rows, patch


def preview(root, rows, patch):
    with tempfile.TemporaryDirectory(prefix="u4-k2-human-preview-") as temp:
        dest = Path(temp)
        with tarfile.open(fileobj=io.BytesIO(git(root, "archive", "HEAD"))) as archive:
            archive.extractall(dest, filter="data")
        images(dest, rows, "before")
        result = subprocess.run(["git", "apply", str(patch)], cwd=dest, capture_output=True)
        require(result.returncode == 0, "private patch application failed")
        images(dest, rows, "after")
        env = dict(os.environ)
        for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN", "PARAMS", "SHA", "RK"):
            env.pop(key, None)
        commands = [
            [sys.executable, "-I", "-B", "scripts/vendor_rk.py", "--check"],
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                "import sys;from pathlib import Path;r=Path.cwd();"
                "sys.path[:0]=[str(r),str(r/'src'),str(r/'contract')];"
                "import uarch_contract.mapped as m;"
                "assert Path(m.__file__).resolve().is_relative_to(r);"
                "from uarch_contract.generate_mapped import generate;"
                "assert generate(check=True)==[];"
                "import pytest;raise SystemExit(pytest.main(['-q','-c','pyproject.toml',"
                "'--rootdir='+str(r),'-p','no:cacheprovider','contract/tests/mapped',"
                "'tests/unit/test_u4_a_mapped_loader.py','tests/unit/test_prompt_sync.py']))",
            ],
        ]
        for command in commands:
            checked = subprocess.run(command, cwd=dest, env=env, capture_output=True, text=True)
            print(checked.stdout, end="", flush=True)
            require(checked.returncode == 0, "private candidate checks failed: " + checked.stderr)
        images(dest, rows, "after")


def place(root, rows, patch):
    # Internal placement is also guarded. This program never sets UARCH_HUMAN itself.
    require(os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    images(root, rows, "before")
    git(root, "apply", str(patch))
    images(root, rows, "after")
    expected = sorted(x["path"] for x in rows if x["before_sha256"] is not None)
    require(text(root, "diff", "--name-only").splitlines() == expected, "unexpected tracked delta")
    require(not text(root, "diff", "--cached", "--name-only"), "index changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-commit", required=True)
    parser.add_argument(
        "--install", action="store_true", help="human placement; default is read-only"
    )
    args = parser.parse_args()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        require(not os.environ.get(key), "Git override present: " + key)
    require(not args.install or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    root = Path(__file__).resolve().parents[3]
    head, rows, patch = preflight(root, args.package_commit)
    preview(root, rows, patch)
    print(
        json.dumps(
            dict(
                preflight="passed",
                parent=head,
                paths=10,
                patch_sha256=PATCH,
                installation_executed=False,
            )
        ),
        flush=True,
    )
    if not args.install:
        print("STOP: read-only preflight. No live installation, staging, commit or push.")
        return
    second_head, _, _ = preflight(root, args.package_commit)
    require(second_head == head, "HEAD moved during checks")
    place(root, rows, patch)
    require(text(root, "rev-parse", "HEAD") == head, "HEAD moved during placement")
    print(
        json.dumps(
            dict(
                decision="U4-K2-semantic-candidate-v1",
                status="human placement verified; unstaged and uncommitted",
                package_commit=args.package_commit,
                parent=head,
                paths=[x["path"] for x in rows],
                patch_sha256=PATCH,
                strict_currentness_private_preview=True,
                staged=False,
                committed=False,
                pushed=False,
                dependency_construction_native_execution=False,
            ),
            indent=2,
        ),
        flush=True,
    )
    print(
        "STOP: return placement receipt. Commit, push, K2 construction and "
        "qualification remain separate."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
