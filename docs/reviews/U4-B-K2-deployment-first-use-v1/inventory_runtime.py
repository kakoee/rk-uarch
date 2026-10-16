"""Recreate private inventories from existing files; never acquire or execute payloads."""

import argparse
import importlib.metadata
import json
from pathlib import Path

from deployment import HERE, digest, require


def inventories(output):
    runtime = json.loads((HERE / "runtime.json").read_bytes())
    root, site = Path(runtime["python_source"]), Path(runtime["site_source"])
    python = {}
    for p in sorted(root.rglob("*")):
        if "__pycache__" in p.parts:
            continue
        if p.is_symlink():
            require(p.resolve().is_relative_to(root), "Python symlink escape")
            python[str(p.relative_to(root))] = {"symlink": str(p.readlink())}
        elif p.is_file():
            python[str(p.relative_to(root))] = {
                "sha256": digest(p.read_bytes()),
                "bytes": p.stat().st_size,
            }
    selected = {}
    found = set()
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name = dist.metadata["Name"].lower().replace("-", "_")
        if name not in runtime["package_versions"]:
            continue
        require(dist.version == runtime["package_versions"][name], "package version drift")
        found.add(name)
        for f in dist.files:
            p = Path(dist.locate_file(f)).absolute()
            require(p.is_relative_to(site), "package path escape")
            if "__pycache__" not in p.parts and p.is_file():
                selected[str(p.relative_to(site))] = {
                    "sha256": digest(p.read_bytes()),
                    "bytes": p.stat().st_size,
                }
    require(found == set(runtime["package_versions"]), "exact existing packages required")
    output.mkdir(exist_ok=False)
    for name, value in [("python-files.json", python), ("site-files.json", selected)]:
        data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        require(digest(data) == runtime["inventories"][name], "frozen inventory drift")
        (output / name).write_bytes(data)
    print("Exact frozen inventories reconstructed; no payload executed")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    require(args.output.resolve().is_relative_to(Path("/tmp")), "private inventory output required")
    inventories(args.output)
