"""Reconstruct the exact unapplied proposal in a fresh disposable directory.

This never installs protected changes into the caller's checkout. Run with Python 3.12+:
    python docs/reviews/U4-ordinary-runtime-implementation-v1/reconstruct.py /tmp/u4-review
"""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    repo = package.parents[2]
    base = (package / "base-commit.txt").read_text().strip()
    destination = args.destination.resolve()
    destination.mkdir(exist_ok=False)
    archive = subprocess.check_output(["git", "archive", base], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(destination, filter="data")
    patch = str(package / "transition.patch")
    subprocess.run(["git", "apply", "--check", patch], cwd=destination, check=True)
    subprocess.run(["git", "apply", patch], cwd=destination, check=True)
    with tempfile.TemporaryDirectory(prefix="u4-ordinary-index-") as scratch:
        environment = dict(
            os.environ, GIT_WORK_TREE=str(destination), GIT_INDEX_FILE=str(Path(scratch) / "index")
        )
        subprocess.run(["git", "read-tree", base], cwd=repo, env=environment, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo, env=environment, check=True)
        tree = subprocess.check_output(
            ["git", "write-tree"], cwd=repo, env=environment, text=True
        ).strip()
    expected = (package / "source-tree.txt").read_text().strip()
    if tree != expected:
        raise SystemExit(f"Reconstruction mismatch: {tree} != {expected}")
    print(f"Reconstructed {tree} at {destination}; protected installation remains a human step.")


if __name__ == "__main__":
    main()
