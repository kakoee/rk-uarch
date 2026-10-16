"""Pure acyclic identity generation from explicit checked BuildInputs, never live HEAD.

Run before Cargo in the disposable export. No downloads, builds, workload execution,
or authority installation. Source inventory excludes generated output and receipts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, sha256, strict_json_loads
from uarch_contract.mapped import NativeEngineIdentity, NativeTestProfile, NativeTestRegistry

from rkuarch.engines.native.records import BuildInputs, BuildTrust, ToolInputs


def generate(root: Path, input_path: Path, output: Path) -> dict:
    build = BuildInputs.model_validate(strict_json_loads(input_path.read_bytes()))

    def read(binding):
        path = root / binding.path
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("symlink in build inputs")
        data = path.read_bytes()
        if sha256(data) != binding.byte_hash:
            raise ValueError("input changed: " + binding.path)
        return data

    for file in build.source_files:
        read(file)
    trust = BuildTrust.model_validate(strict_json_loads(read(build.trust_file)))
    tools = ToolInputs.model_validate(strict_json_loads(read(build.tool_inputs_file)))
    assert content_hash(trust) == build.trust_hash
    assert content_hash(tools) == build.tool_inputs_hash
    assert tuple(x.mode for x in build.mode_configs) == ("debug", "release")
    assert all(x.rustflags == tools.flags for x in build.mode_configs)
    assert list(build.model_source_paths) == sorted(set(build.model_source_paths))
    model = [x for x in build.source_files if x.path in build.model_source_paths]
    assert content_hash([x.model_dump(mode="json") for x in model]) == build.model_inputs_hash
    for file in (trust.semantics_file, trust.registry_file, trust.corpus_inventory):
        read(file)
    registry = NativeTestRegistry.model_validate(strict_json_loads(read(trust.registry_file)))
    assert registry.registry_hash == trust.registry_hash
    for p in trust.profiles:
        profile = NativeTestProfile.model_validate(strict_json_loads(read(p.file)))
        assert profile.profile_hash == p.profile_hash
        actual = [
            (
                e.case_id,
                e.graph_hash,
                e.point_hash,
                e.hardware_spec_hash,
                e.clock_setup_hash,
                e.seed,
            )
            for e in profile.entries
        ]
        expected = [
            (
                e.case_id,
                e.graph_hash,
                e.point_hash,
                e.hardware_spec_hash,
                e.clock_setup_hash,
                e.seed,
            )
            for e in p.cases
        ]
        assert actual == expected
    for name in (
        "accepted_k1_pins",
        "cargo_lock",
        "full_metadata",
        "target_metadata",
        "feature_graph",
        "licence_inventory",
        "crate_checksum_inventory",
        "linker_and_os_inventory",
    ):
        read(getattr(tools, name))
    engine = NativeEngineIdentity.model_validate(
        {
            "name": "native",
            "version": "native-stage/1",
            "implementation_hash": content_hash(build),
            "compiler_lock_hash": content_hash(tools),
            "model": {
                "name": "fixed-delay",
                "version": "1",
                "implementation_hash": build.model_inputs_hash,
            },
        }
    )

    def literal(value):
        text = canonical_json(value)
        hashes = "#"
        while '"' + hashes in text:
            hashes += "#"
        return "r" + hashes + '"' + text + '"' + hashes

    data = (
        "// Generated from explicit checked acyclic inputs; not host authority.\n"
        + "pub(crate) const ENGINE_JSON: &str = "
        + literal(engine)
        + ";\n"
        + "pub(crate) const TRUST_JSON: &str = "
        + literal(trust)
        + ";\n"
    ).encode()
    assert build.generated_identity_output_paths == (
        "native/crates/uarch-engine/generated/identity.rs",
    )
    target = output / build.generated_identity_output_paths[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {
        "engine": engine.model_dump(mode="json"),
        "build_input_hash": content_hash(build),
        "generated": {"path": build.generated_identity_output_paths[0], "byte_hash": sha256(data)},
        "source_commit": build.source_commit,
        "authority": "construction only; human first-use absent",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(generate(args.root.resolve(), args.inputs, args.output), indent=2))


if __name__ == "__main__":
    main()
