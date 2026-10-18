"""Apply B's immutable correction to exact A 7d61d6a postimages, privately.
Usage: python -I reconstruct_checker.py EXACT_A_EXPORT NEW_PRIVATE_EXPORT
A's earlier published reconstruction recipe supplies EXACT_A_EXPORT. This is not
A's pending combined Stage2 candidate and cannot stand in for final-source evidence.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

old, new = map(lambda x: Path(x).resolve(), sys.argv[1:])
here = Path(__file__).resolve().parent
root = here.parents[2]
assert new.is_relative_to(Path("/tmp")) and not new.exists()
manifest = json.loads((here / "manifest.json").read_text())
a = json.loads((root / "docs/reviews/U4-A-issue-edge-amendment-v2/manifest.json").read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


for row in a["files"]:
    assert sha(old / row["path"]) == row["postimage_sha256"]
shutil.copytree(
    old, new, ignore=shutil.ignore_patterns("__pycache__", ".mypy_cache", ".pytest_cache")
)
for row in manifest["files"]:
    assert sha(new / row["path"]) == row["preimage_sha256"]
for patch in manifest["patches"]:
    p = here / patch["path"]
    assert sha(p) == patch["sha256"]
    subprocess.run(["git", "apply", "--check", str(p)], cwd=new, check=True)
    subprocess.run(["git", "apply", str(p)], cwd=new, check=True)
for row in manifest["files"]:
    assert sha(new / row["path"]) == row["postimage_sha256"]
# The original inline readiness/capacity checker body is unchanged, byte-for-byte.
p = "validation/component/issue_checks.py"
start = "def check_reservation_opportunities("
assert (old / p).read_text().split(start)[1] == (new / p).read_text().split(start)[1]
for patch in reversed(manifest["patches"]):
    subprocess.run(
        ["git", "apply", "--reverse", "--check", str(here / patch["path"])], cwd=new, check=True
    )
print("22 A postimages verified; 3 B transitions; reverse applies; opportunity checker unchanged")
