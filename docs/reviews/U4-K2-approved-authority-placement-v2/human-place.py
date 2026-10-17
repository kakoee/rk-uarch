"""Read-only verification by default; human-only placement of five approved authority files."""

import argparse
import hashlib
import json
import os
import re
import runpy
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = str(HERE.relative_to(ROOT))


def need(ok, message):
    if not ok:
        raise ValueError("STOP: " + message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    result = subprocess.run(
        ["/usr/bin/git", "--no-replace-objects", "-C", str(ROOT), *args],
        env=env,
        capture_output=True,
        check=False,
    )
    need(result.returncode == 0, result.stderr.decode().strip() or "Git check refused")
    return result.stdout


def text(*args):
    return git(*args).decode().strip()


def verify_seal(plan, *, placed):
    root = Path(plan["runtime_root"])
    inventory = json.loads((HERE / "payload-postimages.json").read_bytes())
    if placed:
        inventory.update(json.loads((HERE / "authority-postimages.json").read_bytes()))
    dirs = {"authority"}
    for name in inventory:
        dirs.update(str(p) for p in Path(name).parents if str(p) != ".")
    entries = list(root.rglob("*"))
    need(
        {str(p.relative_to(root)) for p in entries if p.is_file()} == set(inventory),
        "exact runtime file membership required",
    )
    need(
        {str(p.relative_to(root)) for p in entries if p.is_dir()} == dirs,
        "exact runtime directory membership required",
    )
    for p in (root, *entries):
        s = p.lstat()
        need(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode), "regular sealed paths only")
        need(s.st_uid == s.st_gid == 0, "root ownership required")
        need(stat.S_IMODE(s.st_mode) == (0o555 if p.is_dir() else 0o444), "exact sealed mode")
        if p.is_file():
            need(s.st_nlink == 1, "single file link required")
            need(
                "sha256:" + digest(p.read_bytes()) == inventory[str(p.relative_to(root))],
                "sealed content drift: " + str(p),
            )
    for p in root.parents:
        s = p.lstat()
        need(
            stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022,
            "unsafe runtime parent",
        )
    if not placed:
        need(not any((root / "authority").iterdir()), "authority must still be empty")


def preflight(helper):
    need(re.fullmatch(r"[0-9a-f]{40}", helper), "full helper commit required")
    need(text("rev-parse", "--show-toplevel") == str(ROOT), "wrong repository")
    need(text("branch", "--show-current") == "main", "main required")
    git("merge-base", "--is-ancestor", helper, "HEAD")
    need(not text("status", "--porcelain", "--untracked-files=no"), "tracked/index dirty")
    need(
        all(row.startswith(b"H ") for row in git("ls-files", "-v", "-z").split(b"\0") if row),
        "hidden index flags",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge"):
        p = Path(text("rev-parse", "--path-format=absolute", "--git-path", name))
        need(not p.exists(), "unfinished Git operation")
    names = text("ls-tree", "-r", "--name-only", helper, "--", PACKAGE).splitlines()
    required = {
        PACKAGE + "/" + n
        for n in (
            "human-place.py",
            "placement.json",
            "human-place.sh",
            "payload-postimages.json",
            "authority-postimages.json",
            "publication-check.json",
        )
    }
    need(required.issubset(names), "helper package missing")
    for name in names:
        need((ROOT / name).read_bytes() == git("show", helper + ":" + name), "helper drift")
    plan = json.loads((HERE / "placement.json").read_bytes())
    for name, expected in plan["package_hashes"].items():
        need(digest((HERE / name).read_bytes()) == expected, "package bytes differ")
    for item in plan["published_inputs"]:
        raw = (ROOT / item["path"]).read_bytes()
        need(digest(raw) == item["sha256"], "published input drift")
        need(raw == git("show", item["commit"] + ":" + item["path"]), "pinned input differs")
        git("merge-base", "--is-ancestor", item["commit"], helper)
    bindings_path = ROOT / plan["bindings_path"]
    need(digest(bindings_path.read_bytes()) == plan["bindings_sha256"], "bindings drift")
    bindings = runpy.run_path(str(bindings_path))
    root = Path(plan["runtime_root"])
    verify_seal(plan, placed=False)
    c, data, publication = bindings["check_payload"](
        root / "project", root / "helpers", root / "record"
    )
    bindings["old_bindings"](bindings["OLD"], c)
    # Check the exact prospective files in ordinary scratch, without resolving a host.
    bindings["check_authority"](HERE / "authority", data, publication)
    script = (HERE / "human-place.sh").read_bytes()
    need(digest(script) == plan["script_sha256"], "root script drift")
    return plan, script, bindings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit", required=True)
    parser.add_argument("--place", action="store_true")
    args = parser.parse_args()
    need(not args.place or os.environ.get("UARCH_HUMAN") == "1", "human invocation required")
    plan, script, bindings = preflight(args.helper_commit)
    print(
        json.dumps(
            {
                "preflight": "passed",
                "authority_files": 5,
                "payload_files_preserved": 40,
                "placement_executed": False,
            }
        ),
        flush=True,
    )
    if not args.place:
        print("Read-only verification only; no sudo, authority resolution or native jobs.")
        return
    # Only these verified in-memory script bytes reach root. Never execute a mutable pathname.
    subprocess.run(["sudo", "/bin/sh", "-s"], input=script, check=True)
    verify_seal(plan, placed=True)
    root = Path(plan["runtime_root"])
    c, data, publication = bindings["check_payload"](
        root / "project", root / "helpers", root / "record"
    )
    bindings["old_bindings"](bindings["OLD"], c)
    binding = bindings["check_authority"](root / "authority", data, publication)
    print(
        json.dumps(
            {
                "decision": "U4-K2-reviewed-runtime-and-restart-v2",
                "status": "human exact authority placement verified",
                "helper_commit": args.helper_commit,
                "runtime_root": str(root),
                "authority_files": 5,
                "original_payload_preserved": True,
                "authority_installed": True,
                "native_calls": 0,
                "binding": binding,
            },
            indent=2,
        ),
        flush=True,
    )
    print("STOP: return receipt. Existing approval covers the fresh 798-call campaign and replay.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
