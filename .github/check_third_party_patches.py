"""Verify the exact reviewed K1 register patch chain in an isolated temporary directory."""

import hashlib
import json
import os
import subprocess
import tempfile
from itertools import pairwise
from pathlib import Path

CHAIN = ".github/native-third-party-patches.json"
RECORD = "docs/reviews/U4-B-K1-environment-v1/register-identity.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(root: Path) -> dict[str, str]:
    record: dict[str, str] = json.loads((root / RECORD).read_text())
    manifest = json.loads((root / CHAIN).read_text())
    if (manifest["format"] != "uarch-third-party-patch-chain/1"
            or manifest["base_record"] != RECORD
            or manifest["base_record_sha256"] != sha((root / RECORD).read_bytes())):
        raise ValueError("base patch record identity mismatch")
    steps = [record, *manifest["followups"]]
    if any(step["path"] != record["path"] for step in steps):
        raise ValueError("patch target changed")
    for before, after in pairwise(steps):
        if before["after_sha256"] != after["before_sha256"]:
            raise ValueError("disconnected patch chain")
    patches = sorted((root / "third_party/patches").glob("*.patch"))
    if patches != [root / step["patch"] for step in steps]:
        raise ValueError("unreviewed or missing numbered patch")
    for step in steps:
        if sha((root / step["patch"]).read_bytes()) != step["patch_sha256"]:
            raise ValueError("register patch identity mismatch")
    installed = (root / record["path"]).read_bytes()
    if sha(installed) != steps[-1]["after_sha256"]:
        raise ValueError("installed register postimage mismatch")
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="u4-register-check-") as temp:
        scratch = Path(temp)
        env["GIT_CEILING_DIRECTORIES"] = str(scratch.parent)
        path = scratch / record["path"]
        path.parent.mkdir(parents=True)
        path.write_bytes(installed)
        for reverse, sequence in [(True, list(reversed(steps))), (False, steps)]:
            for step in sequence:
                subprocess.run(
                    ["git", "apply", *(["--reverse"] if reverse else []), "-"],
                    input=(root / step["patch"]).read_bytes(), cwd=scratch,
                    env=env, check=True, capture_output=True,
                )
                wanted = step["before_sha256" if reverse else "after_sha256"]
                if sha(path.read_bytes()) != wanted:
                    raise ValueError("register patch application image mismatch")
    return record


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = check(root)
    print("Verified isolated reverse/forward patch chain:", result["path"])
