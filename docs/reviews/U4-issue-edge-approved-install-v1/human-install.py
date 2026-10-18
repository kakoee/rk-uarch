"""Exact approved issue-edge placement/checkpoint; clean-export checks, never push or build."""

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

RELEASE = "docs/reviews/U4-issue-edge-approved-install-v1"
PACKAGE = "docs/reviews/U4-issue-edge-install-decision-v1"
APPROVAL_BASE = "13cb0490a09b508900a0857b55045cb3e6827390"
SUBJECT = "0025cef8c871b0193e06d68872faeef4c6c79984"
PATCH_SHA = "5dee8fd749a3fc38f02546c49902077955bc61116e6acaa0968dc97394a0b541"
MANIFEST_SHA = "e7c8241c191f663f3b4b874b6e6e71316d52b95ecbfe02987924378dd0be6c80"
DECISION = "U4-issue-edge-reviewed-install-v1"
MESSAGE = "feat(component): install reviewed issue-edge observation and credit semantics"


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def environment():
    env = dict(os.environ)
    for name in tuple(env):
        if name.startswith("GIT_"):
            del env[name]
    for name in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "PARAMS", "SHA", "RK"):
        env.pop(name, None)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def git(root, *args):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *args],
        env=environment(),
        capture_output=True,
    )
    require(result.returncode == 0, result.stderr.decode().strip() or "Git check failed")
    return result.stdout


def text(root, *args):
    return git(root, *args).decode().strip()


def path_guard(root, name):
    relative = Path(name)
    require(not relative.is_absolute() and bool(relative.parts), "unsafe path")
    require(not {"..", ".git"} & set(relative.parts), "unsafe path")
    current = root
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), "symlink in selected path: " + name)
    return current


def images(root, rows, phase):
    for row in rows:
        path = path_guard(root, row["path"])
        expected = row[phase + "_sha256"]
        if expected is None:
            require(not path.exists(), "new path already exists: " + row["path"])
        else:
            require(
                path.is_file() and sha(path.read_bytes()) == expected,
                phase + " mismatch: " + row["path"],
            )


def human_required():
    require(os.environ.get("UARCH_HUMAN") == "1", "human invocation required")


def preflight(root, helper_commit):
    require(re.fullmatch("[0-9a-f]{40}", helper_commit), "full helper commit required")
    require(text(root, "rev-parse", "--show-toplevel") == str(root), "wrong repository root")
    require(text(root, "branch", "--show-current") == "main", "main branch required")
    require(
        text(root, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    require(
        not text(root, "status", "--porcelain", "--untracked-files=no"),
        "tracked files/index must be clean; preserve unrelated work",
    )
    require(
        all(x.startswith(b"H ") for x in git(root, "ls-files", "-v", "-z").split(b"\0") if x),
        "index flags may conceal changes",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        require(
            not Path(
                text(root, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished Git operation",
        )
    head = text(root, "rev-parse", "HEAD")
    for ancestor in (SUBJECT, APPROVAL_BASE, helper_commit):
        git(root, "merge-base", "--is-ancestor", ancestor, head)
    changed = text(root, "diff", "--name-only", APPROVAL_BASE, head).splitlines()
    require(
        all(n.startswith("docs/reviews/") for n in changed),
        "source advanced since approval; coordinator reconciliation required",
    )
    names = text(root, "ls-tree", "-r", "--name-only", helper_commit, "--", RELEASE).splitlines()
    require(
        RELEASE + "/human-install.py" in names and RELEASE + "/acceptance.json" in names,
        "pinned helper package missing",
    )
    for name in names:
        path = path_guard(root, name)
        require(
            path.is_file() and path.read_bytes() == git(root, "show", helper_commit + ":" + name),
            "helper package differs: " + name,
        )
    approved = json.loads((root / RELEASE / "acceptance.json").read_text())
    require(
        approved["decision"] == DECISION
        and approved["reply_verbatim"] == "yes"
        and approved["proposal_commit"] == APPROVAL_BASE
        and approved["patch_sha256"] == PATCH_SHA,
        "approval binding mismatch",
    )
    decision_path = path_guard(root, PACKAGE + "/next-decision.md")
    require(
        decision_path.read_bytes()
        == git(root, "show", APPROVAL_BASE + ":" + PACKAGE + "/next-decision.md"),
        "approved decision text differs",
    )
    manifest_path = path_guard(root, PACKAGE + "/reviewed-manifest.json")
    patch_path = path_guard(root, PACKAGE + "/install.patch")
    raw = manifest_path.read_bytes()
    patch = patch_path.read_bytes()
    require(sha(raw) == MANIFEST_SHA and sha(patch) == PATCH_SHA, "approved payload mismatch")
    manifest = json.loads(raw)
    rows = manifest["files"]
    require(len(rows) == len({r["path"] for r in rows}) == 29, "wrong path selection")
    require(
        sorted(line[6:] for line in patch.decode().splitlines() if line.startswith("+++ b/"))
        == sorted(row["path"] for row in rows),
        "patch paths differ",
    )
    for row in (
        manifest["prospective_dependencies"] + manifest["verification"]["historical_controls"]
    ):
        require(
            sha(path_guard(root, row["path"]).read_bytes()) == row["sha256"],
            "immutable input changed: " + row["path"],
        )
    images(root, rows, "preimage")
    tracked = set(text(root, "ls-tree", "-r", "--name-only", head).splitlines())
    for row in rows:
        if row["preimage_sha256"] is None:
            require(row["path"] not in tracked, "new selected path already committed")
        else:
            require(
                sha(git(root, "show", head + ":" + row["path"])) == row["preimage_sha256"],
                "committed preimage mismatch",
            )
    git(root, "apply", "--check", str(patch_path))
    return head, rows, patch


def checks(root, identity=False):
    # No editable project imports: prepend the checked tree and assert every project origin.
    code = (
        "import sys,runpy; from pathlib import Path; p=Path.cwd();"
        "sys.path[:]=[x for x in sys.path if 'site-packages' in x or 'python3.12' in x];"
        "sys.path[:0]=[str(p),str(p/'src'),str(p/'contract')];"
        "sys.argv=['scripts/vendor_rk.py','--check'];"
        "runpy.run_path('scripts/vendor_rk.py',run_name='__main__');"
        "sys.argv=['generate_mapped','--check'];"
        "runpy.run_module('uarch_contract.generate_mapped',run_name='__main__');"
    )
    if identity:
        code += (
            "import pytest; rc=pytest.main(['-q','-c',str(p/'pyproject.toml'),"
            "'--rootdir',str(p),'-p','no:cacheprovider',"
            "'validation/component/test_stage2_selection.py']);"
        )
    else:
        code += "rc=0;"
    code += (
        "assert all(not getattr(m,'__file__',None) or Path(m.__file__).resolve().is_relative_to(p) "
        "for n,m in sys.modules.items() if n.split('.')[0] in "
        "('scripts','rkuarch','uarch_contract','validation'));sys.exit(rc)"
    )
    env = environment()
    env.pop("UARCH_HUMAN", None)
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code], cwd=root, env=env)
    require(result.returncode == 0, "read-only currentness/schema/identity check failed")


def preview(root, rows, patch):
    with tempfile.TemporaryDirectory(prefix="u4-issue-human-preview-") as name:
        target = Path(name)
        with tarfile.open(fileobj=io.BytesIO(git(root, "archive", "HEAD"))) as archive:
            archive.extractall(target, filter="data")
        images(target, rows, "preimage")
        result = subprocess.run(
            ["git", "apply", "-"], cwd=target, input=patch, capture_output=True, env=environment()
        )
        require(result.returncode == 0, "private patch failed")
        images(target, rows, "postimage")
        checks(target, identity=True)
        images(target, rows, "postimage")


def install(root, helper_commit, parent, rows, patch):
    human_required()
    new_parent, new_rows, new_patch = preflight(root, helper_commit)
    require((new_parent, new_rows, new_patch) == (parent, rows, patch), "preflight moved")
    result = subprocess.run(
        ["git", "apply", "-"], cwd=root, input=patch, capture_output=True, env=environment()
    )
    require(result.returncode == 0, "placement failed; inspect worktree, do not overwrite")
    images(root, rows, "postimage")
    expected_tracked = sorted(row["path"] for row in rows if row["preimage_sha256"] is not None)
    require(
        text(root, "diff", "--name-only").splitlines() == expected_tracked,
        "unrelated tracked change after placement",
    )
    require(not text(root, "diff", "--cached", "--name-only"), "index changed during placement")
    # All currentness/schema/identity checks already ran on exact prospective source.
    # Never import the live checkout: ignored tables are not part of its commit tree.
    images(root, rows, "postimage")
    human_required()
    require(text(root, "rev-parse", "HEAD") == parent, "HEAD moved")
    git(root, "add", "--", *(row["path"] for row in rows))
    selected = sorted(row["path"] for row in rows)
    require(
        text(root, "diff", "--cached", "--name-only").splitlines() == selected,
        "staged selection differs",
    )
    for row in rows:
        require(
            sha(git(root, "show", ":" + row["path"])) == row["postimage_sha256"],
            "staged bytes differ: " + row["path"],
        )
    git(root, "diff", "--cached", "--check")
    # Normal Git configuration and hooks; no override or bypass.
    print(git(root, "commit", "-m", MESSAGE).decode(), end="", flush=True)
    commit = text(root, "rev-parse", "HEAD")
    require(text(root, "rev-parse", "HEAD^") == parent, "unexpected parent")
    require(
        text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        == selected,
        "committed path selection differs",
    )
    for row in rows:
        require(
            sha(git(root, "show", commit + ":" + row["path"])) == row["postimage_sha256"],
            "committed bytes differ: " + row["path"],
        )
    images(root, rows, "postimage")
    require(not text(root, "status", "--porcelain", "--untracked-files=no"), "tracked/index dirty")
    return commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--install", action="store_true", help="human place/check/local commit")
    args = parser.parse_args()
    if args.install:
        human_required()
    root = Path(__file__).resolve().parents[3]
    require(root == Path("/home/jjaff/AI-infra-simulation/rk-uarch"), "wrong coordinator checkout")
    parent, rows, patch = preflight(root, args.helper_commit)
    preview(root, rows, patch)
    print(
        json.dumps(
            dict(
                decision=DECISION,
                preflight="passed",
                parent=parent,
                paths=29,
                patch_sha256=PATCH_SHA,
                installation_executed=False,
            )
        ),
        flush=True,
    )
    if not args.install:
        print("STOP: read-only preflight; no live placement, staging, commit or push.")
        return
    commit = install(root, args.helper_commit, parent, rows, patch)
    print(
        json.dumps(
            dict(
                decision=DECISION,
                status="human installation and local checkpoint verified",
                helper_commit=args.helper_commit,
                parent=parent,
                commit=commit,
                tree=text(root, "rev-parse", "HEAD^{tree}"),
                paths=29,
                patch_sha256=PATCH_SHA,
                tracked_and_index_clean=True,
                strict_currentness="passed on clean export of exact source",
                pushed=False,
                native_execution=False,
                authority_changed=False,
            ),
            indent=2,
        ),
        flush=True,
    )
    print(
        "STOP: return receipt for coordinator verification/publication. "
        "Native release remains separate."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
