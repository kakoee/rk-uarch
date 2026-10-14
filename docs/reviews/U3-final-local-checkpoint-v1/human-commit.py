"""Check or human-commit the exact U3 closeout selection; never push or tag."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

BASELINE = "7afba9b16d954fd46684711764cb3718170e53aa"
PACKAGE = "docs/reviews/U3-final-local-checkpoint-v1"
MESSAGE = "docs(u3): record accepted design, policy and closeout evidence"


def stop(message):
    raise SystemExit("STOP: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-sha256", required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    for key in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG_COUNT"):
        if key in os.environ:
            stop("unset " + key)

    def git(*argv, env=None):
        result = subprocess.run(
            ["git", *argv], cwd=root, env=env, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            stop(result.stderr.strip() or result.stdout.strip() or "git failed")
        return result.stdout.strip()

    if git("rev-parse", "--show-toplevel") != str(root):
        stop("unexpected repository root")
    if git("branch", "--show-current") != "main" or git("rev-parse", "HEAD") != BASELINE:
        stop("branch or parent changed; reconcile first")
    if git("diff", "--cached", "--name-only"):
        stop("index must be empty; preserve existing staging")
    manifest_path = root / PACKAGE / "commit-selection.json"
    if manifest_path.is_symlink() or digest(manifest_path) != args.selection_sha256:
        stop("selection identity mismatch")
    selection = json.loads(manifest_path.read_text())
    if selection["parent"] != BASELINE or selection["message"] != MESSAGE:
        stop("unexpected parent/message")
    paths = [item["path"] for item in selection["files"]]
    paths.append(str(manifest_path.relative_to(root)))
    if len(paths) != len(set(paths)) or any(
        not p.startswith("docs/") or ".." in Path(p).parts for p in paths
    ):
        stop("unexpected/duplicate path")
    for item in selection["files"]:
        target = root / item["path"]
        if any(p.is_symlink() for p in (target, *target.parents)):
            stop("symlink: " + item["path"])
        if digest(target) != item["sha256"]:
            stop("bytes changed: " + item["path"])
        mode = "100755" if target.stat().st_mode & 0o111 else "100644"
        if mode != item["mode"]:
            stop("file mode changed: " + item["path"])
    if not set(git("diff", "--name-only").splitlines()) <= set(paths):
        stop("unrelated tracked changes; preserve them")
    hooks = selection["normal_hooks"]
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], cwd=root,
        text=True, capture_output=True, check=False,
    )
    if configured.returncode not in (0, 1) or configured.stdout.strip():
        stop("hook configuration changed; reconcile normal hooks")
    hook = Path(git("rev-parse", "--git-path", "hooks/pre-commit"))
    if not hook.is_absolute():
        hook = root / hook
    if digest(hook) != hooks["pre_commit_sha256"] or not os.access(hook, os.X_OK):
        stop("normal pre-commit hook missing or changed")
    for path, expected in hooks["tracked"].items():
        if digest(root / path) != expected:
            stop("normal hook script changed")
    with tempfile.TemporaryDirectory(prefix="u3-final-commit-") as temp:
        temp = Path(temp)
        pathspec = temp / "paths"
        pathspec.write_bytes(b"\0".join(p.encode() for p in sorted(paths)) + b"\0")
        isolated_env = dict(os.environ, GIT_INDEX_FILE=str(temp / "index"))
        git("read-tree", BASELINE, env=isolated_env)
        add_args = ("add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul")
        git(*add_args, env=isolated_env)
        expected_tree = git("write-tree", env=isolated_env)
        # Preserve immutable patch context and raw diagnostic logs byte-for-byte.
        prose_and_code = [p for p in paths if Path(p).suffix not in {".patch", ".diff", ".log"}]
        git("diff", "--cached", "--check", "--", *prose_and_code, env=isolated_env)
        changed = set(git("diff", "--cached", "--name-only", env=isolated_env).splitlines())
        if changed != set(paths):
            stop("selection differs from actual changed paths")
        print(json.dumps({"preflight": "passed", "parent": BASELINE,
                          "paths": len(paths), "tree": expected_tree,
                          "message": MESSAGE, "real_index_unchanged": True}, indent=2), flush=True)
        if not args.commit:
            print("CHECK ONLY: no real staging, commit, push or tag.")
            return
        if os.environ.get("UARCH_HUMAN") != "1":
            stop("human must invoke with UARCH_HUMAN=1; nothing staged")
        git(*add_args)
        if git("write-tree") != expected_tree:
            stop("staged tree differs; preserve state for reconciliation")
        message = temp / "message"
        message.write_text(MESSAGE + "\n")
        print(git("commit", "--file", str(message)), flush=True)
        commit = git("rev-parse", "HEAD")
        if (
            git("rev-parse", "HEAD^") != BASELINE
            or git("rev-parse", "HEAD^{tree}") != expected_tree
        ):
            stop("commit verification differs")
        if git("diff", "--name-only") or git("diff", "--cached", "--name-only"):
            stop("tracked/index changes remain; preserve state")
        receipt = {"decision": "U3-final-local-checkpoint-v1", "commit": commit,
                   "parent": BASELINE, "tree": expected_tree, "paths": len(paths),
                   "selection_sha256": args.selection_sha256,
                   "tracked_and_index_clean": True, "push_tag_closure_U4": False}
        print(json.dumps(receipt, indent=2))
        print("STOP: return this receipt. Push, published checks, tag and closure remain separate.")


if __name__ == "__main__":
    main()
