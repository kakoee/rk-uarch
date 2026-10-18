"""Independently reconstruct both alternative routes; no live source installation."""

import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "docs/reviews/U4-A-issue-edge-F2-F3-v1"
OLD = ROOT / "docs/reviews/U4-A-issue-edge-stage2-v1"
OUT = Path(sys.argv[1]).resolve()
assert OUT.is_relative_to(Path("/tmp"))
OUT.mkdir(exist_ok=False)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def apply(source, package, patch):
    path = package / patch["path"]
    assert sha(path) == patch["sha256"]
    subprocess.run(["git", "apply", "--check", str(path)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(path)], cwd=source, check=True)


manifest = json.loads((PACKAGE / "manifest.json").read_text())
old = json.loads((OLD / "manifest.json").read_text())
raw = subprocess.check_output(["git", "archive", manifest["base_commit"]], cwd=ROOT)
for name in ("full", "alternative"):
    source = OUT / name
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(source, filter="data")
    for row in manifest["files"]:
        p = source / row["path"]
        assert (sha(p) if p.exists() else None) == row["preimage_sha256"]
    if name == "full":
        for patch in manifest["patches"]:
            apply(source, PACKAGE, patch)
    else:
        for patch in old["patches"]:
            apply(source, OLD, patch)
        for row in old["files"]:
            assert sha(source / row["path"]) == row["postimage_sha256"]
        apply(source, PACKAGE, manifest["alternative_delta"])
    for row in manifest["files"]:
        assert sha(source / row["path"]) == row["postimage_sha256"]
    for row in manifest["verification"]["historical_controls"]:
        assert sha(source / row["path"]) == row["sha256"]
    patches = manifest["patches"] if name == "full" else [manifest["alternative_delta"]]
    for patch in reversed(patches):
        subprocess.run(
            ["git", "apply", "--reverse", "--check", str(PACKAGE / patch["path"])],
            cwd=source,
            check=True,
        )
a = {str(p.relative_to(OUT / "full")): sha(p) for p in (OUT / "full").rglob("*") if p.is_file()}
b = {
    str(p.relative_to(OUT / "alternative")): sha(p)
    for p in (OUT / "alternative").rglob("*")
    if p.is_file()
}
assert a == b
report = dict(
    package_commit="26dc261",
    manifest_sha256=sha(PACKAGE / "manifest.json"),
    base_commit=manifest["base_commit"],
    patches=manifest["patches"],
    alternative_delta=manifest["alternative_delta"],
    files=manifest["files"],
    verified_postimages_per_route=29,
    whole_exports_identical=True,
    export_file_count=len(a),
    export_archive_sha256=hashlib.sha256(raw).hexdigest(),
    historical_controls=manifest["verification"]["historical_controls"],
    recipe_sha256=sha(Path(__file__)),
    private_root=str(OUT),
)
(OUT / "reconstruction.json").write_text(json.dumps(report, indent=2) + "\n")
print("Both routes: 29 exact postimages; complete exports identical:", len(a), "files")
