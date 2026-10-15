"""Read pinned Git source; create private exports only. Never execute A's builder."""

import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

SUBJECT = "1a52fa82f3aabc3eca5de4fa5597295a0fa04e27"
PATCH = "672ac0ef827a06bdd0ae8b7f5e0cbb3c8f4ab1af7123d7fa96c36ebc1a276b41"
PLAN = "4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(repo, work):
    repo, work = repo.resolve(), work.resolve()
    assert work.is_relative_to(Path("/tmp")) and not work.exists()
    work.mkdir()
    out = work / "receipts"
    out.mkdir()
    data = subprocess.check_output(["git", "archive", SUBJECT], cwd=repo)
    for name in ("baseline", "proposed"):
        root = work / name
        root.mkdir()
        with tarfile.open(fileobj=io.BytesIO(data)) as f:
            f.extractall(root, filter="data")
    root = work / "proposed"
    a = root / "docs/reviews/U4-A-K2-semantic-construction-v1"
    inventory = json.loads((a / "package-inventory.json").read_bytes())
    for name, digest in inventory["files"].items():
        assert sha(a / name) == digest, name
    assert sha(a / "complete.proposed.patch") == PATCH and sha(a / "construction-plan.json") == PLAN
    manifest = json.loads((a / "patch-manifest.json").read_bytes())
    assert len(manifest) == 10
    for row in manifest:
        path = root / row["path"]
        assert (sha(path) if path.exists() else None) == row["before_sha256"]
    subprocess.run(
        ["git", "apply", "--check", str(a / "complete.proposed.patch")], cwd=root, check=True
    )
    subprocess.run(["git", "apply", str(a / "complete.proposed.patch")], cwd=root, check=True)
    for row in manifest:
        assert sha(root / row["path"]) == row["after_sha256"]
    changed = []
    for f in root.rglob("*"):
        if f.is_file():
            old = work / "baseline" / f.relative_to(root)
            if not old.exists() or f.read_bytes() != old.read_bytes():
                changed.append(str(f.relative_to(root)))
    assert sorted(changed) == sorted(x["path"] for x in manifest)
    shutil.copytree(root, work / "guarded")
    delta = Path(__file__).with_name("notification-order.proposed.patch")
    subprocess.run(["git", "apply", str(delta)], cwd=work / "guarded", check=True)
    receipt = dict(
        subject=SUBJECT,
        patch_sha256=PATCH,
        construction_plan_sha256=PLAN,
        package_inventory_files=len(inventory["files"]),
        postimages=manifest,
        exact_changed_paths=sorted(changed),
        archive_sha256=hashlib.sha256(data).hexdigest(),
        source_tree=subprocess.check_output(
            ["git", "rev-parse", SUBJECT + "^{tree}"], cwd=repo, text=True
        ).strip(),
        builder_or_live_scripts_executed=False,
    )
    (out / "patch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Exact source/package/preimages/postimages verified; three private exports prepared.")


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
