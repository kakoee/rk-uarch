"""Prepare human-only placement commands from published bytes; never invoke root."""

import argparse
import base64
import json
import re
import subprocess
from pathlib import Path

from launch import HERE, NEW_ROOT, OLD_ROOT
from parallel_core import digest, encoded, require

PACKAGE = "docs/reviews/U4-B-K2-parallel-first-use-v1/"
PLACEMENT = "docs/reviews/U4-K2-parallel-placement-v1/placement.json"


def published(repo, commit, name, expected=None):
    require(bool(re.fullmatch("[0-9a-f]{40}", commit)), "full immutable published commit")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main"],
        cwd=repo,
        check=True,
    )
    data = subprocess.check_output(["git", "show", commit + ":" + name], cwd=repo)
    if expected is not None:
        require(digest(data) == expected, "publication byte mismatch")
    return data


def script(files, new_root):
    """Literal fixed paths and embedded verified bytes, never root execution of Python."""
    require(
        all(
            path.is_relative_to(NEW_ROOT)
            and ".." not in path.parts
            and re.fullmatch(r"[A-Za-z0-9_./-]+", str(path))
            for path in files
        ),
        "only fixed new deployment paths",
    )
    lines = ["set -euC", 'test "$(id -u)" = 0']
    if new_root:
        lines += [
            f"test ! -e {NEW_ROOT}",
            f"test ! -L {NEW_ROOT}",
            f"mkdir -m 0555 -- {NEW_ROOT}",
            f"mkdir -m 0555 -- {NEW_ROOT}/helpers {NEW_ROOT}/authority",
        ]
    for path, data in sorted(files.items()):
        payload = base64.b64encode(data).decode("ascii")
        lines += [
            f"test ! -e {path}",
            f"test ! -L {path}",
            f"printf %s '{payload}' | /usr/bin/base64 -d > {path}",
            f"chown root:root -- {path}",
            f"chmod 0444 -- {path}",
            f"printf '%s\\n' '{digest(data).split(':')[1]}  {path}' | /usr/bin/sha256sum -c -",
        ]
    return ("\n".join(lines) + "\n").encode()


def prepare(repo, commit, output, preflight=None, placement_commit=None):
    output = output.resolve()
    require(output.is_relative_to(Path("/tmp")) and not output.exists(), "new private output")
    for p in (NEW_ROOT.parent, *NEW_ROOT.parent.parents):
        st = p.lstat()
        require(
            p.is_dir() and not p.is_symlink() and st.st_uid == 0 and not st.st_mode & 0o022,
            "root-owned real non-writable ancestors",
        )
    # All executed host helper bytes as well as mounted files come from this exact publication.
    for path in HERE.iterdir():
        if path.is_file() and path.suffix in (".py", ".json", ".md", ".txt"):
            published(repo, commit, PACKAGE + path.name, digest(path.read_bytes()))
    manifest_bytes = published(repo, commit, PACKAGE + "helper-manifest.json")
    policy_bytes = published(repo, commit, PACKAGE + "parallel-policy.json")
    policy = json.loads(policy_bytes)
    require(
        digest((OLD_ROOT / "manifests/runtime-release.json").read_bytes())
        == policy["original_runtime_release_hash"],
        "original authority release drift",
    )
    files = {}
    if preflight is None:
        require(not NEW_ROOT.exists() and not NEW_ROOT.is_symlink(), "never overwrite new root")
        for name, binding in json.loads(manifest_bytes).items():
            files[NEW_ROOT / "helpers" / name] = published(
                repo, commit, PACKAGE + name, binding["sha256"]
            )
        files[NEW_ROOT / "authority/helper-manifest.json"] = manifest_bytes
    else:
        require(placement_commit is not None, "actual coordinator placement publication required")
        placement_bytes = published(repo, placement_commit, PLACEMENT)
        placement = json.loads(placement_bytes)
        require(
            placement["status"] == "reconciled-for-human-placement"
            and placement["helper_publication_commit"] == commit
            and placement["helper_manifest_hash"] == digest(manifest_bytes)
            and placement["policy_hash"] == digest(policy_bytes)
            and placement["original_runtime_release_hash"]
            == policy["original_runtime_release_hash"],
            "actual reconciled placement binding required",
        )
        preflight_bytes = preflight.read_bytes()
        receipt = json.loads(preflight_bytes)
        require(
            receipt["status"] == "parallel-import-preflight-passed"
            and receipt["helper_manifest_hash"] == digest(manifest_bytes)
            and receipt["original_runtime_release_hash"] == policy["original_runtime_release_hash"]
            and receipt["native_calls"] == 0
            and receipt["authority_resolved"] is False,
            "actual unchanged-helper authority-free preflight required",
        )
        release = {
            "format": "uarch-k2-parallel-runtime/1",
            "status": "placed-after-coordinator-reconciliation",
            "helper_publication_commit": commit,
            "placement_publication_commit": placement_commit,
            "placement_record_byte_hash": digest(placement_bytes),
            "helper_manifest_hash": digest(manifest_bytes),
            "policy_hash": digest(policy_bytes),
            "original_runtime_release_hash": policy["original_runtime_release_hash"],
            "plan_hash": policy["plan_hash"],
            "preflight_byte_hash": digest(preflight_bytes),
        }
        files[NEW_ROOT / "authority/parallel-preflight.json"] = preflight_bytes
        files[NEW_ROOT / "authority/runtime-release.json"] = encoded(release)
    for path in files:
        require(not path.exists() and not path.is_symlink(), "never overwrite placement")
    output.mkdir()
    (output / "human-stage.sh").write_bytes(script(files, preflight is None))
    (output / "postimages.json").write_bytes(
        encoded({str(p): digest(data) for p, data in files.items()})
    )
    print("Prepared literal human-only script and exact postimages; no root action performed.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--helper-commit", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--preflight", type=Path)
    p.add_argument("--placement-commit")
    a = p.parse_args()
    prepare(a.repo, a.helper_commit, a.output, a.preflight, a.placement_commit)
