"""Verify concrete record/file/hash joins without installing or executing authority."""

import json
from pathlib import Path

from pydantic import ValidationError
from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native.records import (
    BuildInputs,
    BuildReceipt,
    BuildTrust,
    HostRecord,
    HostSelector,
    ToolInputs,
)

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
C = PACKAGE / "candidate-04"
S = Path("/tmp/u4-k2-candidate-04")


def read(name, model):
    data = (C / name).read_bytes()
    value = model.model_validate_json(data)
    assert canonical_json(value).encode() == data
    return value


def file(binding):
    p = ROOT / binding.path
    if not p.is_file():
        p = S / binding.path
    if not p.is_file():
        p = S / "workspace" / binding.path
    assert p.is_file(), p
    assert sha256(p.read_bytes()) == binding.byte_hash, p


def no_authority(value):
    if isinstance(value, dict):
        assert not {"engine", "job_hash", "binary_hash", "executable_byte_hash"} & value.keys()
        for x in value.values():
            no_authority(x)
    elif isinstance(value, list):
        for x in value:
            no_authority(x)


def main():
    build = read("BuildInputs.json", BuildInputs)
    trust = read("BuildTrust.json", BuildTrust)
    tools = read("ToolInputs.json", ToolInputs)
    assert content_hash(trust) == build.trust_hash
    assert content_hash(tools) == build.tool_inputs_hash
    for f in [*build.source_files, build.trust_file, build.tool_inputs_file]:
        file(f)
    for key in (
        "accepted_k1_pins",
        "cargo_lock",
        "full_metadata",
        "target_metadata",
        "feature_graph",
        "licence_inventory",
        "crate_checksum_inventory",
        "linker_and_os_inventory",
    ):
        file(getattr(tools, key))
    for f in [trust.semantics_file, trust.registry_file, trust.corpus_inventory]:
        file(f)
    no_authority(trust.model_dump(mode="json"))
    no_authority(json.loads((ROOT / trust.registry_file.path).read_bytes()))
    for p in trust.profiles:
        file(p.file)
        no_authority(json.loads((ROOT / p.file.path).read_bytes()))
    assert not set(build.generated_identity_output_paths) & {f.path for f in build.source_files}
    assert str((C / "BuildInputs.json").relative_to(ROOT)) not in {
        f.path for f in build.source_files
    }
    bins = []
    for mode in ("debug", "release"):
        receipt = read("BuildReceipt-" + mode + ".json", BuildReceipt)
        assert receipt.mode == mode and receipt.build_input_hash == content_hash(build)
        assert receipt.engine.compiler_lock_hash == content_hash(tools)
        assert receipt.engine.model.implementation_hash == build.model_inputs_hash
        assert receipt.image_digest == tools.image_digest and receipt.target == tools.target
        for f in [
            receipt.executable,
            *receipt.generated_identity_outputs,
            receipt.actual_read_inventory,
            receipt.actual_environment,
            receipt.compiler_verbose,
            receipt.build_log,
            receipt.binary_origin_check,
            receipt.software_path_check,
        ]:
            file(f)
        bins.append(receipt.executable.byte_hash)
    jobs = json.loads((C / "jobs-inventory.json").read_bytes())
    assert len(jobs["jobs"]) == 133 and len({x["job_hash"] for x in jobs["jobs"]}) == 133
    for item in jobs["jobs"]:
        p = S / item["file"]["path"]
        assert sha256(p.read_bytes()) == item["file"]["byte_hash"]
    subject = json.loads((C / "first-use-subject.json").read_bytes())
    assert subject["executable_byte_hashes"] == bins
    assert subject["build_input_hash"] == content_hash(build)
    assert subject["jobs_byte_hash"] == sha256((C / "jobs-inventory.json").read_bytes())
    assert subject["corpus_byte_hash"] == trust.corpus_inventory.byte_hash
    for name, model in [
        ("HostRecord-proposal.json", HostRecord),
        ("HostSelector-proposal.json", HostSelector),
    ]:
        try:
            model.model_validate_json((C / name).read_bytes())
        except ValidationError:
            pass
        else:
            raise AssertionError("Incomplete proposal became qualifying record")
    print("Actual record and 133-job joins pass; incomplete authority proposals refuse")


if __name__ == "__main__":
    main()
