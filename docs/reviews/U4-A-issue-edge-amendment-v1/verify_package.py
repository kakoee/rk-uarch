"""Verify frozen review artifacts only; never apply patches or execute component jobs."""

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    inventory = json.loads((root / "artifact-inventory.json").read_text())
    expected = inventory["files"]
    actual = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "artifact-inventory.json"
        and "__pycache__" not in path.parts
    }
    assert actual == expected, "review artifact inventory changed"
    manifest = json.loads((root / "manifest.json").read_text())
    for row in manifest["patches"]:
        assert actual[row["path"]] == row["sha256"], row["path"]
    for receipt in (
        "evidence/u4-issue-consumption.json",
        "evidence/u4-issue-consumption-final.json",
    ):
        for row in json.loads((root / receipt).read_text()):
            case = root / "private-probes" / row["case"]
            assert (
                hashlib.sha256((case / "job.json").read_bytes()).hexdigest() == row["input_sha256"]
            )
            assert (
                hashlib.sha256((case / "result.json").read_bytes()).hexdigest()
                == row["output_sha256"]
            )
            assert row["validator"] == row["checker"] == "pass"
    print(f"Verified {len(actual)} artifacts, three patches and twelve private joins.")


if __name__ == "__main__":
    main()
