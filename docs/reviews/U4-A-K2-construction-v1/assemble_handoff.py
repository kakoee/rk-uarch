"""Bind actual private observations into owned proposals; never install authority.

Run only after all explicit candidate commands finish. Bulk inputs/outputs stay private.
No byte in this script is an upstream input to the binary it describes.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native.records import BuildInputs, BuildReceipt, BuildTrust, ToolInputs

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
CANDIDATE = PACKAGE / "candidate-04"
SCRATCH = Path("/tmp/u4-k2-candidate-04")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def binding(path):
    return {"path": str(path.relative_to(ROOT)), "byte_hash": sha256(path.read_bytes())}


def inventory(root):
    return {
        str(p.relative_to(root)): {"byte_hash": sha256(p.read_bytes()), "bytes": p.stat().st_size}
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def assemble():
    build = BuildInputs.model_validate_json((CANDIDATE / "BuildInputs.json").read_bytes())
    trust = BuildTrust.model_validate_json((CANDIDATE / "BuildTrust.json").read_bytes())
    tools = ToolInputs.model_validate_json((CANDIDATE / "ToolInputs.json").read_bytes())
    identity = json.loads((SCRATCH / "identity.json").read_bytes())
    assert identity["build_input_hash"] == content_hash(build)
    for source in build.source_files:
        assert sha256((ROOT / source.path).read_bytes()) == source.byte_hash
        assert sha256((SCRATCH / "workspace" / source.path).read_bytes()) == source.byte_hash
    output = CANDIDATE / "observations"
    output.mkdir(exist_ok=True)
    # Commands are compact actual observations; preserve complete streams in private scratch.
    commands = {
        p.stem: json.loads(p.read_bytes()) for p in sorted((SCRATCH / "commands").glob("*.json"))
    }
    for name, command in commands.items():
        for stream in ("stdout", "stderr"):
            path = SCRATCH / "commands" / (name + "." + stream)
            assert sha256(path.read_bytes()) == command[stream + "_byte_hash"]
    for tool in ("image-inspect", "rustc", "cargo", "cargo-deny", "rustfmt", "clippy"):
        shutil.copyfile(SCRATCH / "commands" / (tool + ".stdout"), output / (tool + ".stdout"))
    write(output / "commands.json", commands)
    write(output / "private-command-files.json", inventory(SCRATCH / "commands"))
    write(output / "wrapper-and-link-map-files.json", inventory(SCRATCH / "receipts"))
    write(output / "identity.json", identity)
    pending = json.loads((SCRATCH / "pending-jobs.json").read_bytes())
    # Exact saved input bytes remain private. Paths are explicit relative to candidate scratch.
    jobs = {
        "format": "uarch-k2-jobs-inventory/1",
        "jobs": [{"file": row["file"], "job_hash": row["job_hash"]} for row in pending["jobs"]],
    }
    for row in jobs["jobs"]:
        assert sha256((SCRATCH / row["file"]["path"]).read_bytes()) == row["file"]["byte_hash"]
    write(CANDIDATE / "jobs-inventory.json", jobs)
    write(output / "pending-jobs.json", pending)
    executables = []
    for mode in ("debug", "release"):
        actual = json.loads((SCRATCH / (mode + "-binaries.json")).read_bytes())
        assert (
            sha256(Path(actual["executable_path"]).read_bytes()) == actual["executable_byte_hash"]
        )
        assert actual["engine"] == identity["engine"]
        write(output / (mode + "-binaries.json"), actual)
        for action in ("build", "test", "validate", "peer"):
            assert commands[mode + "-" + action]["exit_code"] == 0
        for action in ("validate", "peer"):
            data = (SCRATCH / "commands" / (mode + "-" + action + ".stdout")).read_text()
            assert "1 passed; 0 failed" in data, "nonempty exact selection"
        for action in ("test", "validate", "peer", "origin"):
            for stream in ("stdout", "stderr"):
                shutil.copyfile(
                    SCRATCH / "commands" / (mode + "-" + action + "." + stream),
                    output / (mode + "-" + action + "." + stream),
                )
        refusals = json.loads((SCRATCH / (mode + "-refusals.json")).read_bytes())
        assert len(refusals["cases"]) == 11 and refusals["successful_public_jobs"] == 0
        write(output / (mode + "-refusals.json"), refusals)
        envs = {}
        for path in sorted((SCRATCH / "receipts" / mode / "build").glob("*.env")):
            envs[path.name] = path.read_bytes().decode().split("\0")
        write(
            output / (mode + "-actual-environment.json"),
            {
                "initial": commands[mode + "-build"]["environment"],
                "compiler_and_linker": envs,
                "limit": "actual wrapper environments, not proof of variable use",
            },
        )
        target = SCRATCH / "targets" / mode / mode
        observed = {}
        for path in sorted(target.rglob("*")):
            if path.is_file() and (
                path.suffix == ".d" or path.name in ("output", "stderr", "root-output")
            ):
                observed[str(path.relative_to(SCRATCH))] = {
                    "byte_hash": sha256(path.read_bytes()),
                    "text": path.read_text(errors="replace"),
                }
        write(
            output / (mode + "-read-evidence.json"),
            {
                "status": "Observed argv/env/dep-info/build outputs; B candidate trace pending",
                "source_files": [x.model_dump(mode="json") for x in build.source_files],
                "generated_identity": identity["generated"],
                "dep_info_and_build_outputs": observed,
                "complete_bounded_read_audit": False,
                "limitations": [
                    "no A tracer execution",
                    "not exhaustive reads or semantic dependence",
                    "inherited C2 B traces do not audit this candidate",
                ],
            },
        )
        build_log = output / (mode + "-build.stderr")
        shutil.copyfile(SCRATCH / "commands" / (mode + "-build.stderr"), build_log)
        sha2_argv = []
        for path in sorted((SCRATCH / "receipts" / mode / "build").glob("*.argv")):
            data = path.read_bytes().decode().split("\0")
            if "--crate-name" in data and data[data.index("--crate-name") + 1] == "sha2":
                assert 'feature="force-soft"' in data
                sha2_argv.append(
                    {"file": str(path), "byte_hash": sha256(path.read_bytes()), "argv": data}
                )
        assert sha2_argv
        write(
            output / (mode + "-software-path.json"),
            {
                "actual_build_log": binding(build_log),
                "actual_sha2_argv": sha2_argv,
                "accepted_feature_graph": tools.feature_graph.model_dump(mode="json"),
                "accepted_lock": tools.cargo_lock.model_dump(mode="json"),
                "selection": "sha2 exact accepted force-soft feature; no new flags",
                "inherited": "C1 unified graph and reconciled C2 software-path evidence",
                "limitation": "No universal no-SIMD claim; hashing SIMD nonblocking",
            },
        )
        receipt = BuildReceipt.model_validate(
            {
                "format": "uarch-k2-build-receipt/1",
                "build_input_hash": content_hash(build),
                "engine": identity["engine"],
                "mode": mode,
                "target": tools.target,
                "executable": {
                    "path": f"targets/{mode}/{mode}/uarch-engine",
                    "byte_hash": actual["executable_byte_hash"],
                },
                "image_digest": tools.image_digest,
                "generated_identity_outputs": [identity["generated"]],
                "actual_read_inventory": binding(output / (mode + "-read-evidence.json")),
                "actual_environment": binding(output / (mode + "-actual-environment.json")),
                "compiler_verbose": binding(output / "rustc.stdout"),
                "build_log": binding(build_log),
                "binary_origin_check": binding(output / (mode + "-origin.stdout")),
                "software_path_check": binding(output / (mode + "-software-path.json")),
            }
        )
        write(CANDIDATE / ("BuildReceipt-" + mode + ".json"), receipt)
        executables.append(
            {
                "mode": mode,
                "executable": receipt.executable.model_dump(mode="json"),
                "build_receipt": binding(CANDIDATE / ("BuildReceipt-" + mode + ".json")),
                "target": tools.target,
            }
        )
    assert commands["debug-clippy"]["exit_code"] == 0
    subject = {
        "build_input_hash": content_hash(build),
        "tool_inputs_hash": content_hash(tools),
        "trust_hash": content_hash(trust),
        "model_inputs_hash": build.model_inputs_hash,
        "executable_byte_hashes": [e["executable"]["byte_hash"] for e in executables],
        "corpus_byte_hash": trust.corpus_inventory.byte_hash,
        "jobs_byte_hash": binding(CANDIDATE / "jobs-inventory.json")["byte_hash"],
    }
    write(CANDIDATE / "first-use-subject.json", subject)
    write(
        CANDIDATE / "HostRecord-proposal.json",
        {
            "status": "proposal only; no qualifying HostRecord exists",
            "proposed_fields": {
                "format": "uarch-k2-first-use/1",
                "semantics": trust.semantics_file.model_dump(mode="json"),
                "trust_hash": content_hash(trust),
                "trust_file": binding(CANDIDATE / "BuildTrust.json"),
                "build_input_hash": content_hash(build),
                "build_input_file": binding(CANDIDATE / "BuildInputs.json"),
                "tool_inputs_hash": content_hash(tools),
                "model_inputs_hash": build.model_inputs_hash,
                "expected_engine": identity["engine"],
                "executables": executables,
                "jobs_inventory": binding(CANDIDATE / "jobs-inventory.json"),
                "corpus_inventory": trust.corpus_inventory.model_dump(mode="json"),
                "profile_hashes": [p.profile_hash for p in trust.profiles],
                "registry_hash": trust.registry_hash,
            },
            "missing_real_bindings": ["decision", "independent_review", "loader_read_inventory"],
            "deployment": "assemble declared paths under one verified root; no layout installed",
            "private_sources": {
                "repository_inputs": str(ROOT),
                "targets_and_vectors": str(SCRATCH),
                "generated_identity": str(SCRATCH / "workspace"),
            },
        },
    )
    write(
        CANDIDATE / "HostSelector-proposal.json",
        {
            "status": "uninstalled; not a HostSelector instance",
            "selector_location": "/etc/rkuarch/k2-host-selector.json",
            "format_when_complete": "uarch-k2-host-selector/1",
            "required_real_fields": [
                "repository",
                "acceptance_commit",
                "record_path",
                "record_byte_hash",
            ],
            "installation_verification": [
                "genuine human commit contains exact completed HostRecord blob",
                "independent root-owned selector byte anchor; no workload-selected path",
                "verify all relocated files and immutable executable/runtime bytes",
                "both executable digests and exact B/human subject accepted",
            ],
            "no_self_cycle": "Receipts and human subject precede HostRecord and selector",
        },
    )
    print(json.dumps(subject, indent=2))


if __name__ == "__main__":
    assemble()
