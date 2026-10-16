"""Prepare explicit build records from a published source commit and actual tool metadata.

This writes owned proposal records only. It neither builds nor installs authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, sha256, strict_json_loads

from rkuarch.engines.native.records import BuildInputs, BuildTrust, ToolInputs

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/reviews/U4-A-K2-construction-v1"


def binding(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "byte_hash": sha256(path.read_bytes())}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def freeze(commit: str, out: Path) -> None:
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("explicit full published source commit required")
    tree = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-tree", "-rz", "--full-tree", commit],
        env={"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"},
    )
    blobs = {}
    for row in tree.split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            mode, kind, digest = meta.decode().split()
            if kind == "blob" and mode != "120000":
                blobs[path.decode()] = digest
    paths = set()
    paths.update(
        p
        for p in (ROOT / "native").rglob("*")
        if p.is_file()
        and p.suffix in (".rs", ".toml", ".lock", ".json", ".py")
        and "generated" not in p.parts
        and "target" not in p.parts
    )
    paths.update((ROOT / "contract/uarch_contract").glob("*.py"))
    paths.update((ROOT / "src/rkuarch/engines/native").glob("*.py"))
    paths.update(
        ROOT / p
        for p in [
            "src/rkuarch/__init__.py",
            "src/rkuarch/engines/__init__.py",
            "src/rkuarch/workload/__init__.py",
            "src/rkuarch/workload/mapped.py",
        ]
    )
    peer = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1"
    paths.update(
        peer / name
        for name in (
            "prepare_first_use.py",
            "first_use_checks.py",
            "dto_vectors.py",
            "dto_key_vectors.py",
            "dto_coordinate_vectors.py",
        )
    )
    paths.add(PACKAGE / "inputs/peer-dto-expectations.json")
    source = []
    for path in sorted(paths):
        relative = str(path.relative_to(ROOT))
        data = path.read_bytes()
        git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blobs.get(relative) != git_hash:
            raise ValueError("source differs from explicit published commit: " + relative)
        role = (
            "rust"
            if path.suffix == ".rs"
            else "schema"
            if path.suffix == ".json"
            else "python-build-helper"
            if path.suffix == ".py"
            else "config"
        )
        source.append({**binding(path), "role": role})
    corpus_path = PACKAGE / "corpus/inventory.json"
    corpus = strict_json_loads(corpus_path.read_bytes())
    grouped = {}
    for case in corpus["cases"]:
        profile = strict_json_loads((ROOT / case["profile"]["path"]).read_bytes())
        entry = next(e for e in profile["entries"] if e["case_id"] == case["case_id"])
        group = grouped.setdefault(
            profile["profile_hash"],
            {"profile_hash": profile["profile_hash"], "file": case["profile"], "cases": []},
        )
        group["cases"].append(
            {
                k: entry[k]
                for k in (
                    "case_id",
                    "graph_hash",
                    "point_hash",
                    "hardware_spec_hash",
                    "clock_setup_hash",
                    "seed",
                )
            }
            | {"execution_outcome": case["execution_outcome"]}
        )
    for group in grouped.values():
        group["cases"].sort(key=lambda e: e["case_id"])
    registry = strict_json_loads((ROOT / corpus["registry"]["path"]).read_bytes())
    trust = BuildTrust.model_validate(
        {
            "format": "uarch-k2-build-trust/1",
            "purpose": "construction-test-only",
            "semantics_file": binding(ROOT / "docs/decisions/U0011-the-native-engine-core.md"),
            "registry_hash": registry["registry_hash"],
            "registry_file": corpus["registry"],
            "profiles": [grouped[k] for k in sorted(grouped)],
            "corpus_inventory": binding(corpus_path),
        }
    )
    write(out / "BuildTrust.json", trust)
    c1 = ROOT / "docs/reviews/U4-A-K2-C1-precise-v1"
    flags = ["-C", "debuginfo=1", "-C", "linker=/controls/linker.sh"]
    tools = ToolInputs.model_validate(
        {
            "format": "uarch-k2-tool-inputs/1",
            "accepted_k1_pins": binding(ROOT / "docs/reviews/U4-A-toolchain-v1/pins.json"),
            "compiler_commit": "b940084d7eb6a299eb4bfeb8e34901bc051e7ac4",
            "rust_release": "1.99.0",
            "target": "x86_64-unknown-linux-gnu",
            "image_digest": (
                "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
            ),
            "cargo_lock": binding(ROOT / "native/Cargo.lock"),
            "full_metadata": binding(PACKAGE / "inputs/metadata-full.json"),
            "target_metadata": binding(PACKAGE / "inputs/metadata-linux.json"),
            "feature_graph": binding(c1 / "features.full.json"),
            "licence_inventory": binding(c1 / "licences.json"),
            "crate_checksum_inventory": binding(c1 / "archives.json"),
            "linker_and_os_inventory": binding(PACKAGE / "inputs/tool-and-os-bindings.json"),
            "flags": flags,
        }
    )
    write(out / "ToolInputs.json", tools)
    model_paths = sorted(
        "native/crates/uarch-engine/src/" + name + ".rs"
        for name in ("simulation", "event", "time", "accounting")
    )
    modes = []
    for mode in ("debug", "release"):
        args = [
            "rustc",
            "--offline",
            "--locked",
            "-p",
            "uarch-engine",
            "--bin",
            "uarch-engine",
            "-vv",
            "--message-format=json",
        ]
        if mode == "release":
            args.append("--release")
        args += ["--", "-C", "link-arg=-Wl,-Map=/receipts/" + mode + ".map"]
        modes.append({"mode": mode, "cargo_args": args, "rustflags": flags})
    build = BuildInputs.model_validate(
        {
            "format": "uarch-k2-build-inputs/1",
            "source_commit": commit,
            "source_files": source,
            "trust_hash": content_hash(trust),
            "trust_file": binding(out / "BuildTrust.json"),
            "tool_inputs_hash": content_hash(tools),
            "tool_inputs_file": binding(out / "ToolInputs.json"),
            "model_source_paths": model_paths,
            "model_inputs_hash": content_hash([f for f in source if f["path"] in model_paths]),
            "mode_configs": modes,
            "generated_identity_output_paths": ["native/crates/uarch-engine/generated/identity.rs"],
            "permitted_environment": {
                "PATH": (
                    "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/:"
                    "/usr/local/cargo/bin:/usr/bin:/bin"
                ),
                "CARGO_HOME": "/cargo-home",
                "CARGO_TARGET_DIR": "/target",
                "RUSTC": "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/rustc",
                "RUSTUP_AUTO_INSTALL": "0",
                "CARGO_NET_OFFLINE": "true",
                "CARGO_REGISTRIES_CRATES_IO_PROTOCOL": "sparse",
                "LC_ALL": "C",
                "RUSTFLAGS": " ".join(flags),
                "RUSTC_WRAPPER": "/controls/rustc-wrapper.sh",
                "C2_RUN_TAG": "construction",
            },
        }
    )
    write(out / "BuildInputs.json", build)
    print(
        json.dumps(
            {
                "source_commit": commit,
                "build_input_hash": content_hash(build),
                "source_files": len(source),
                "finite_cases": len(corpus["cases"]),
                "status": "construction proposal; no human first-use",
            },
            indent=2,
        )
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-commit", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    freeze(args.source_commit, args.out.resolve())


if __name__ == "__main__":
    main()
