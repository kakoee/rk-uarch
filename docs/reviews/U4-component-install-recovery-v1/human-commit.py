"""Verify already placed component bytes in a clean export; human-only local checkpoint."""

import argparse
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PACKAGE = "docs/reviews/U4-component-install-recovery-v1"
ORIGINAL = "docs/reviews/U4-component-approved-install-v2/human-install.py"
ORIGINAL_PIN = "3a615fe5baf52df7dd5fa3e0f908a3e3b61ee8b8"
STOPPED_HEAD = "2a4c9e261bb7536024b7902f7169fe987cccac25"
PROPOSAL = "docs/reviews/U4-B-component-install-joins-v1"
MANIFEST_SHA = "e8cef2bcbfc04a29c27c0e22a8f4156665a399df11f372841e1a99877e8defb9"
DECISION = "U4-component-semantic-install-v2"


def require(value, message):
    if not value:
        raise ValueError("STOP: " + message)


def raw_git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *args], env=env, capture_output=True
    )
    require(result.returncode == 0, result.stderr.decode().strip() or "Git guard failed")
    return result.stdout


def load_original(root):
    path = root / ORIGINAL
    require(not path.is_symlink(), "original helper symlink")
    require(
        path.read_bytes() == raw_git(root, "show", ORIGINAL_PIN + ":" + ORIGINAL),
        "original helper differs from approved publication",
    )
    spec = importlib.util.spec_from_file_location("approved_component_helper", path)
    require(spec is not None and spec.loader is not None, "helper cannot load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight(root, pin, h):
    require(re.fullmatch("[0-9a-f]{40}", pin), "full recovery helper commit required")
    require(h.text(root, "rev-parse", "--show-toplevel") == str(root), "wrong repository")
    require(h.text(root, "branch", "--show-current") == "main", "main branch required")
    require(
        h.text(root, "remote", "get-url", "origin") == "https://github.com/kakoee/rk-uarch.git",
        "unexpected origin",
    )
    require(not h.text(root, "diff", "--cached", "--name-only"), "index must remain empty")
    require(
        all(x.startswith(b"H ") for x in h.git(root, "ls-files", "-v", "-z").split(b"\0") if x),
        "index flags may hide changes",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        require(
            not Path(
                h.text(root, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished Git operation",
        )
    head = h.text(root, "rev-parse", "HEAD")
    for ancestor in (STOPPED_HEAD, ORIGINAL_PIN, pin):
        h.git(root, "merge-base", "--is-ancestor", ancestor, head)
    require(
        all(
            n.startswith("docs/reviews/")
            for n in h.text(root, "diff", "--name-only", STOPPED_HEAD, head).splitlines()
        ),
        "source history advanced; reconcile before recovery",
    )
    names = h.text(root, "ls-tree", "-r", "--name-only", pin, "--", PACKAGE).splitlines()
    require(
        PACKAGE + "/human-commit.py" in names and PACKAGE + "/README.md" in names,
        "pinned recovery package missing",
    )
    for name in names:
        path = h.path_guard(root, name)
        require(
            path.is_file() and path.read_bytes() == h.git(root, "show", pin + ":" + name),
            "recovery package differs: " + name,
        )
    approval_path = "docs/reviews/U4-component-approved-install-v2/acceptance.json"
    approval = h.path_guard(root, approval_path).read_bytes()
    require(approval == h.git(root, "show", ORIGINAL_PIN + ":" + approval_path), "approval drift")
    record = json.loads(approval)
    require(
        record["decision"] == DECISION and record["reply_verbatim"] == "yes",
        "existing approval mismatch",
    )
    raw = h.path_guard(root, PROPOSAL + "/postimages.json").read_bytes()
    require(h.sha(raw) == MANIFEST_SHA, "approved manifest changed")
    manifest = json.loads(raw)
    rows = manifest["paths"]
    require(len(rows) == len({r["path"] for r in rows}) == 29, "wrong approved selection")
    h.images(root, rows, "postimage")
    expected = sorted(r["path"] for r in rows if r["base_sha256"] is not None)
    require(
        h.text(root, "diff", "--name-only").splitlines() == expected,
        "tracked delta differs from exact interrupted placement",
    )
    for row in rows:
        # All commit preimages still match; newly placed paths must remain untracked.
        result = subprocess.run(
            ["git", "--no-replace-objects", "show", "HEAD:" + row["path"]],
            cwd=root,
            env=h.environment(),
            capture_output=True,
        )
        if row["base_sha256"] is None:
            require(result.returncode != 0, "new selected path already committed")
        else:
            require(
                result.returncode == 0 and h.sha(result.stdout) == row["base_sha256"],
                "commit preimage drift: " + row["path"],
            )
    for row in manifest["activation_inputs"] + manifest["supplemental_future_consumer_inputs"]:
        require(
            h.sha(h.path_guard(root, row["path"]).read_bytes()) == row["sha256"],
            "activation input drift: " + row["path"],
        )
    return head, rows


def verify_installed_export(root, head, rows, h):
    # This is the prospective commit tree, not a claim about the dirty worktree's namespaces.
    # Copy verified actual installed bytes, including all 20 new files; never reapply a patch.
    with tempfile.TemporaryDirectory(prefix="u4-component-installed-export-") as name:
        dest = Path(name)
        with tarfile.open(fileobj=io.BytesIO(h.git(root, "archive", head))) as archive:
            archive.extractall(dest, filter="data")
        for row in rows:
            raw = h.path_guard(root, row["path"]).read_bytes()
            require(h.sha(raw) == row["postimage_sha256"], "installed bytes moved")
            path = h.path_guard(dest, row["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        h.images(dest, rows, "postimage")
        h.checks(dest, identity=True)
        h.images(dest, rows, "postimage")
    h.images(root, rows, "postimage")


def checkpoint(root, pin, head, rows, h):
    h.human_required()
    require(preflight(root, pin, h) == (head, rows), "state changed during verification")
    selected = sorted(row["path"] for row in rows)
    h.git(root, "add", "--", *selected)
    require(
        h.text(root, "diff", "--cached", "--name-only").splitlines() == selected,
        "staged selection differs",
    )
    for row in rows:
        require(
            h.sha(h.git(root, "show", ":" + row["path"])) == row["postimage_sha256"],
            "index bytes differ",
        )
    h.git(root, "diff", "--cached", "--check")
    h.human_required()
    require(h.text(root, "rev-parse", "HEAD") == head, "HEAD moved before commit")
    print(h.git(root, "commit", "-m", h.MESSAGE).decode(), end="", flush=True)
    commit = h.text(root, "rev-parse", "HEAD")
    require(h.text(root, "rev-parse", "HEAD^") == head, "unexpected commit parent")
    require(
        h.text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        == selected,
        "committed paths differ",
    )
    for row in rows:
        require(
            h.sha(h.git(root, "show", commit + ":" + row["path"])) == row["postimage_sha256"],
            "committed postimage mismatch",
        )
    h.images(root, rows, "postimage")
    require(
        not h.text(root, "status", "--porcelain", "--untracked-files=no"), "tracked/index dirty"
    )
    return commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--commit", action="store_true", help="human-only checkpoint, no placement")
    args = parser.parse_args()
    require(not args.commit or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    root = Path(__file__).resolve().parents[3]
    require(root == Path("/home/jjaff/AI-infra-simulation/rk-uarch"), "wrong coordinator checkout")
    h = load_original(root)
    head, rows = preflight(root, args.helper_commit, h)
    verify_installed_export(root, head, rows, h)
    require(preflight(root, args.helper_commit, h) == (head, rows), "state moved during checks")
    print(
        json.dumps(
            dict(
                decision=DECISION,
                recovery="U4-component-install-recovery-v1",
                preflight="passed",
                parent=head,
                postimages=29,
                index_empty=True,
                verification="clean export of exact installed bytes",
                staged=False,
                committed=False,
                pushed=False,
            )
        ),
        flush=True,
    )
    if not args.commit:
        print("STOP: read-only recovery preflight; installed worktree and index preserved.")
        return
    commit = checkpoint(root, args.helper_commit, head, rows, h)
    print(
        json.dumps(
            dict(
                decision=DECISION,
                recovery="U4-component-install-recovery-v1",
                status="human local checkpoint verified",
                parent=head,
                commit=commit,
                tree=h.text(root, "rev-parse", "HEAD^{tree}"),
                paths=29,
                helper_commit=args.helper_commit,
                strict_currentness="passed on clean export of exact committed source",
                tracked_and_index_clean=True,
                source_reinstalled=False,
                guard_changed=False,
                tables_modified=False,
                pushed=False,
                native_execution=False,
                authority_changed=False,
            ),
            indent=2,
        ),
        flush=True,
    )
    print(
        "STOP: return receipt for coordinator verification/publication. Native release is separate."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
