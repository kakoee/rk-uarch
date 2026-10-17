"""Reconstruct original reviewed proposal then additive F5 test, only in a fresh /tmp export."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(Path("/tmp")) and not output.exists()
    package = Path(__file__).resolve().parent
    repo = package.parents[2]
    proposal = json.loads((package / "proposal.json").read_text())
    for row in [proposal["prior_manifest"], proposal["prior_reconstruction"]]:
        assert sha(repo / row["path"]) == row["sha256"]
    for row in proposal["ordered_patches"]:
        assert sha(repo / row["path"]) == row["sha256"]
    manifest = json.loads((repo / proposal["prior_manifest"]["path"]).read_text())
    assert manifest["base_commit"] == proposal["preparation_base"]
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(repo / proposal["prior_reconstruction"]["path"]),
            str(output),
        ],
        check=True,
    )
    for row in proposal["changed_files"]:
        assert row["base_sha256"] is None and not (output / row["path"]).exists()
    delta = (repo / proposal["ordered_patches"][1]["path"]).read_bytes()
    subprocess.run(["git", "apply", "--check", "-"], input=delta, cwd=output, check=True)
    subprocess.run(["git", "apply", "-"], input=delta, cwd=output, check=True)
    for row in manifest["files"] + proposal["changed_files"]:
        assert sha(output / row["path"]) == row["postimage_sha256"]
    for row in manifest["activation_inputs"] + proposal["supplemental_future_consumer_inputs"]:
        assert sha(output / row["path"]) == row["sha256"]
    selection = proposal["selection"]
    assert sha(output / selection["path"]) == selection["sha256"]
    assert (
        json.loads((output / selection["path"]).read_text())["selection_hash"]
        == selection["selection_hash"]
    )
    print("Verified original 23 plus one additive test, original 106-case selection and inputs.")
    print("Private preparation only; current main U0011 and all installed source untouched.")


if __name__ == "__main__":
    main()
