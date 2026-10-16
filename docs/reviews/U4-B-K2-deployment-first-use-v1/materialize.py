"""Future private copy preparation only. No authority synthesis, root writes or execution."""

import argparse
import json
import shutil
from pathlib import Path

from deployment import HERE, digest, relative, require


def load_inventory(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, "exact frozen runtime inventory required")
    return json.loads(data)


def runtime_copy(source, target, inventory):
    source = Path(source).resolve()
    for name, binding in inventory.items():
        p = source / relative(name)
        dest = target / relative(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if "symlink" in binding:
            require(p.is_symlink() and str(p.readlink()) == binding["symlink"], "symlink changed")
            require(p.resolve().is_relative_to(source), "source symlink escape")
            dest.symlink_to(binding["symlink"])
        else:
            require(not p.is_symlink() and p.is_file(), "regular runtime source")
            data = p.read_bytes()
            require(digest(data) == binding["sha256"], "runtime source changed")
            dest.write_bytes(data)


def prepare(output, inventories):
    output = output.resolve()
    require(
        output.is_relative_to(Path("/tmp")) and not output.exists(), "new private output required"
    )
    output.mkdir()
    layout = json.loads((HERE / "candidate-layout.json").read_bytes())
    for name, binding in layout["files"].items():
        source = Path(binding["source"])
        require(source.is_file() and not source.is_symlink(), "regular candidate source")
        data = source.read_bytes()
        require(digest(data) == binding["byte_hash"], "candidate byte drift")
        target = output / "candidate" / relative(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    runtime = json.loads((HERE / "runtime.json").read_bytes())
    (output / "manifests").mkdir()
    for name, source, target in [
        ("python-files.json", runtime["python_source"], "python"),
        ("site-files.json", runtime["site_source"], "site"),
    ]:
        inv = load_inventory(inventories / name, runtime["inventories"][name])
        runtime_copy(source, output / target, inv)
        shutil.copyfile(inventories / name, output / "manifests" / name)
    (output / "campaign").mkdir()
    names = [
        "entrypoint.py",
        "deployment.py",
        "runtime.json",
        "campaign-plan.json",
        "candidate-layout.json",
    ]
    members = {}
    for name in names:
        data = (HERE / name).read_bytes()
        (output / "campaign" / name).write_bytes(data)
        members[name] = {"sha256": digest(data), "bytes": len(data)}
    manifest = (json.dumps(members, sort_keys=True, indent=2) + "\n").encode()
    require(
        manifest == (HERE / "campaign-files.expected.json").read_bytes(),
        "published helper manifest drift",
    )
    (output / "manifests/campaign-files.json").write_bytes(manifest)
    require(
        all(
            not (output / "candidate" / name).exists()
            for name in layout["reserved_authority_paths"]
        ),
        "authority must remain absent",
    )
    print("Private payload only; root sealing, runtime execution and authority are not performed")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--inventories", type=Path, required=True)
    args = p.parse_args()
    prepare(args.output, args.inventories)
