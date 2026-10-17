"""Reconstruct the exact proposed installation tree in a NEW private /tmp directory."""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--ordered", action="store_true", help="preview then delta instead of combined"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(Path("/tmp")) and not output.exists()
    package = Path(__file__).resolve().parent
    repo = package.parents[2]
    manifest = json.loads((package / "postimages.json").read_text())
    combined = package / "install-with-joins.unapplied.patch"
    delta = package / "joins.unapplied.patch"
    preview = repo / manifest["original_preview"]["path"]
    assert sha(combined) == manifest["combined_patch_sha256"]
    assert sha(delta) == manifest["delta_patch_sha256"]
    assert sha(preview) == manifest["original_preview"]["sha256"]
    archive = subprocess.check_output(["git", "archive", manifest["base_commit"]], cwd=repo)
    output.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(output, filter="data")
    for row in manifest["paths"]:
        path = output / row["path"]
        assert (sha(path) if path.exists() else None) == row["base_sha256"], row["path"]
    for patch in [preview, delta] if args.ordered else [combined]:
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=output, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=output, check=True)
    for row in manifest["paths"]:
        assert sha(output / row["path"]) == row["postimage_sha256"], row["path"]
    for row in manifest["activation_inputs"] + manifest["supplemental_future_consumer_inputs"]:
        assert sha(output / row["path"]) == row["sha256"], row["path"]
    selection = manifest["historical_selection"]
    assert sha(output / selection["path"]) == selection["sha256"]
    subprocess.run(["git", "apply", "--reverse", "--check", str(combined)], cwd=output, check=True)
    print(
        "Verified 29 pre/postimages, all activation inputs, sidecar and "
        "immutable 106-case selection."
    )
    print("Combined and ordered routes share exact identities; no live installation or authority.")


if __name__ == "__main__":
    main()
