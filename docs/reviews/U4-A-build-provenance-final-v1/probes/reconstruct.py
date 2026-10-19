"""Fresh private proposal reconstruction only. Never install or build."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

A = "docs/reviews/U4-A-build-provenance-final-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    repo, work = (Path(v).resolve() for v in sys.argv[1:])
    if not work.is_relative_to(Path("/tmp")):
        raise ValueError("new private /tmp reconstruction root required")
    work.mkdir(exist_ok=False)
    package = repo / A
    record = json.loads((package / "source-transition.json").read_bytes())
    archive = work / "base.tar"
    subprocess.run(
        ["git", "archive", "-o", str(archive), record["base_commit"]], cwd=repo, check=True
    )
    routes = {}
    for name, patches in (
        ("direct", [package / "proposals/complete-successor-from-base.patch"]),
        (
            "prior-then-delta",
            [
                repo
                / "docs/reviews/U4-A-construction-declarations-final-v1/proposals"
                / "complete-activation-unapplied.patch",
                package / "proposals/delta-from-aecc6a2-overlay.patch",
            ],
        ),
    ):
        root = work / name
        root.mkdir()
        with tarfile.open(archive) as stream:
            stream.extractall(root, filter="data")
        for patch in patches:
            subprocess.run(["git", "apply", str(patch)], cwd=root, check=True)
        shutil.copytree(package, root / A)
        for path, binding in record["postimages"].items():
            assert digest(root / path) == binding["after"], (name, path)
        for path, pin in record["prospective_source_files"].items():
            assert digest(root / path) == pin, (name, path)
        assert (
            digest(root / "validation/component/capture_monitor.py")
            == record["optional_capture_monitor_sha256"]
        )
        routes[name] = {
            "postimages": len(record["postimages"]),
            "declared_sources": len(record["prospective_source_files"]),
            "patches": [{"path": str(p.relative_to(repo)), "sha256": digest(p)} for p in patches],
        }
    # Package manifest does not self-reference or contain an unbuilt executable identity.
    manifest_path = package / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_bytes())
        for path, binding in manifest["files"].items():
            file = package / path
            assert digest(file) == binding["sha256"] and file.stat().st_size == binding["bytes"], (
                path
            )
    report = {
        "format": "A-provenance-reconstruction/1",
        "base": record["base_commit"],
        "routes": routes,
        "installation": False,
        "build": False,
        "authority": None,
    }
    (work / "reconstruction.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
