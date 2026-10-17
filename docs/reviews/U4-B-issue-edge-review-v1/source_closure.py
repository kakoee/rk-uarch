"""Exact final proposal postimages and unchanged selected-support closure."""

import hashlib
import json
import subprocess
from pathlib import Path

from uarch_contract.hashing import content_hash

from scripts.u2_support import inventory

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path("/tmp/u4-b-issue-edge-01/source")
OUT = Path("/tmp/u4-b-issue-edge-source-01.json")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=ROOT)


manifest = json.loads(
    (ROOT / "docs/reviews/U4-A-issue-edge-amendment-v1/manifest.json").read_text()
)
for row in manifest["files"]:
    assert sha((SOURCE / row["path"]).read_bytes()) == row["postimage_sha256"], row["path"]
selected = inventory(root=SOURCE)
assert len(selected) == 56
assert all(
    sha(git("show", "3949b104d0eaae95a7452f976c2afa048fa82ff1:" + p)) == v
    for p, v in selected.items()
)
assert (
    content_hash(selected)
    == "sha256:676b12509606b7a519d9597dc406f8fe66d141af4c86425a5baf3a2e3825358a"
)
# Preserve original installed stream through the exact new append-only transition.
old = git(
    "show",
    "e259d2d8f2f0389e14bdb92a3a2cc5ec056ab1ea:docs/decisions/U0011-the-native-engine-core.md",
)
new = (SOURCE / "docs/decisions/U0011-the-native-engine-core.md").read_bytes()
assert new[: len(old)] == old and len(old) == 48294 and len(new) == 57768
for prefix in ("src/rkuarch/engines/native", "docs/reviews/U4-K2-campaign-throughput-v1"):
    assert not git("diff", "3949b104d0eaae95a7452f976c2afa048fa82ff1", "HEAD", "--", prefix)
report = dict(
    package_commit="ddd299ca59a27098da9ce4de1359d43f966aab20",
    manifest_sha256=sha(
        (ROOT / "docs/reviews/U4-A-issue-edge-amendment-v1/manifest.json").read_bytes()
    ),
    exact_postimages=manifest["files"],
    selected_support=selected,
    selected_support_hash=content_hash(selected),
    selected_support_changed=[],
    U0002_generation_required=False,
    protected_installation_permission=False,
    K2_runner_campaign_unchanged=True,
    old_ADR_bytes=len(old),
    new_ADR_bytes=len(new),
    appendix_sha256=sha(new[len(old) :]),
    support_source_origin=__import__("scripts.u2_support", fromlist=["x"]).__file__,
)
OUT.write_text(json.dumps(report, indent=2) + "\n")
print("20 final postimages; 56 unchanged selected support files; exact 9474-byte ADR appendix")
