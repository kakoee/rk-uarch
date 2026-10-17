"""Reconstruct only an unapplied proposal in a new private directory; never install it."""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    repo = package.parents[2]
    manifest = json.loads((package / "combined-postimages.json").read_text())
    patch = (package / "combined.unapplied.patch").read_bytes()
    assert digest(patch) == manifest["patch_sha256"]
    args.output.mkdir(parents=True, exist_ok=False)
    archive = subprocess.check_output(["git", "archive", manifest["base_commit"]], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(args.output, filter="data")
    for row in manifest["activation_inputs"] + manifest["supplemental_future_consumer_inputs"]:
        assert digest((args.output / row["path"]).read_bytes()) == row["sha256"]
    for row in manifest["files"]:
        path = args.output / row["path"]
        actual = digest(path.read_bytes()) if path.exists() else None
        assert actual == row["base_sha256"], row["path"]
    subprocess.run(["git", "apply", "--check", "-"], input=patch, cwd=args.output, check=True)
    subprocess.run(["git", "apply", "-"], input=patch, cwd=args.output, check=True)
    for row in manifest["files"]:
        assert digest((args.output / row["path"]).read_bytes()) == row["postimage_sha256"]
    print(f"Verified {len(manifest['files'])} postimages in {args.output}; proposal only.")


if __name__ == "__main__":
    main()
