"""Install only the reviewed U3 documentation; never stage, commit or push."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

EXPECTED_PATCH = "2b0bc1934020e1d0da2d21ab3514d26c1595a780d3d539b300f79a05286d9416"
PACKAGE = "docs/reviews/U3-closeout-documents-v1"


def stop(message):
    raise SystemExit("STOP: " + message)


def git(root, *args):
    result = subprocess.run(
        ["git", *args], cwd=root, check=False, text=True, capture_output=True,
    )
    if result.returncode:
        stop(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("--check", "--apply", "--verify"))
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--patch-sha256", required=True)
    # A positional beginning with -- needs an explicit separator; accept the documented form.
    import sys
    args_list = sys.argv[1:]
    if args_list and args_list[0] in ("--check", "--apply", "--verify"):
        mode = args_list.pop(0)
        args_list.extend(["--", mode])
    args = parser.parse_args(args_list)
    root = Path(__file__).resolve().parents[3]
    if git(root, "rev-parse", "--show-toplevel") != str(root):
        stop("unexpected repository root")
    if git(root, "branch", "--show-current") != "main":
        stop("expected main")
    if git(root, "rev-parse", "HEAD") != args.expected_head:
        stop("HEAD changed; reconcile before installation")
    if args.patch_sha256 != EXPECTED_PATCH:
        stop("supplied patch digest differs from reviewed package")
    package = root / PACKAGE
    review = json.loads((package / "review.json").read_text())
    patch = package / "closeout.patch"
    if digest(patch) != EXPECTED_PATCH or review["patch_sha256"] != EXPECTED_PATCH:
        stop("patch identity mismatch")
    git(root, "merge-base", "--is-ancestor", review["baseline_commit"], "HEAD")
    allowed = {
        "docs/build-spec.md", "docs/execution-plan.md",
        "docs/prompts/U-P6-L0-invariants-and-L0m-metamorphic.md",
        "docs/decisions/U0002-the-vendored-snapshot-and-parity-discipline.md",
        "docs/decisions/U0011-the-native-engine-core.md",
    }
    if {item["path"] for item in review["paths"]} != allowed:
        stop("unexpected target selection")
    numstat = git(root, "apply", "--numstat", str(patch))
    actual = {row.split("\t", 2)[2] for row in numstat.splitlines()}
    if actual != allowed:
        stop("patch target selection differs")
    for item in review["paths"]:
        target = root / item["path"]
        if any(p.is_symlink() for p in (target, *target.parents)):
            stop("symlink target")
        expected = item["after_sha256"] if args.mode == "--verify" else item["before_sha256"]
        if digest(target) != expected or (expected is None and target.exists()):
            stop("target bytes differ: " + item["path"])
    if args.mode == "--verify":
        print("Verified exact five installed documentation files; no action performed.")
        return
    if git(root, "diff", "--name-only") or git(root, "diff", "--cached", "--name-only"):
        stop("tracked worktree/index changes need reconciliation; preserve them")
    git(root, "apply", "--check", str(patch))
    print("Preflight passed: exact five-file documentation amendment; no runtime/support edits.")
    if args.mode == "--check":
        print("CHECK ONLY: no installation, staging, commit or push.")
        return
    if os.environ.get("UARCH_HUMAN") != "1":
        stop("human must invoke with UARCH_HUMAN=1; nothing installed")
    git(root, "apply", str(patch))
    for item in review["paths"]:
        if digest(root / item["path"]) != item["after_sha256"]:
            stop("postimage mismatch; preserve state for reconciliation")
    print("Installed exact documentation only, unstaged and uncommitted.")
    print("STOP: return receipt. Commit, push, U3 closure and U4 release remain separate.")


if __name__ == "__main__":
    main()
