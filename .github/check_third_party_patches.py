"""Verify the exact accepted K1 register patch in an isolated temporary directory."""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

RECORD = "docs/reviews/U4-B-K1-environment-v1/register-identity.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(root: Path) -> dict[str, str]:
    record: dict[str, str] = json.loads((root / RECORD).read_text())
    expected = root / record["patch"]
    patches = sorted((root / "third_party/patches").glob("*.patch"))
    if patches != [expected]:
        raise ValueError("unreviewed or missing numbered patch")
    patch = expected.read_bytes()
    installed = (root / record["path"]).read_bytes()
    if sha(patch) != record["patch_sha256"]:
        raise ValueError("register patch identity mismatch")
    if sha(installed) != record["after_sha256"]:
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
        for flags, wanted in [
            (["--reverse"], record["before_sha256"]),
            ([], record["after_sha256"]),
        ]:
            subprocess.run(
                ["git", "apply", *flags, "-"],
                input=patch,
                cwd=scratch,
                env=env,
                check=True,
                capture_output=True,
            )
            if sha(path.read_bytes()) != wanted:
                raise ValueError("register patch application image mismatch")
    return record


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = check(root)
    print("Verified isolated reverse/forward application:", result["patch"])
