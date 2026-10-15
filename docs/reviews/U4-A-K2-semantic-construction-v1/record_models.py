"""Proposed build/host metadata schemas only; no trust resolver or workload carrier."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator
from uarch_contract.common import FrozenModel, Hash, NonEmpty
from uarch_contract.mapped import NativeEngineIdentity

GitCommit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]


class FileBinding(FrozenModel):
    path: NonEmpty
    byte_hash: Hash

    @model_validator(mode="after")
    def relative_path(self) -> "FileBinding":
        if self.path.startswith("/") or ".." in self.path.split("/") or "\\" in self.path:
            raise ValueError("Explicit relative path required")
        return self


class CaseBinding(FrozenModel):
    case_id: NonEmpty
    graph_hash: Hash
    point_hash: Hash
    hardware_spec_hash: Hash
    clock_setup_hash: Hash
    seed: Annotated[int, Field(strict=True, ge=0, le=2**64 - 1)]
    execution_outcome: Literal["success", "TimeOverflow"]


class ProfileBinding(FrozenModel):
    profile_hash: Hash
    file: FileBinding
    cases: Annotated[tuple[CaseBinding, ...], Field(min_length=1)]


class BuildTrust(FrozenModel):
    format: Literal["uarch-k2-build-trust/1"]
    purpose: Literal["construction-test-only"]
    semantics_file: FileBinding
    registry_hash: Hash
    registry_file: FileBinding
    profiles: Annotated[tuple[ProfileBinding, ...], Field(min_length=1)]
    corpus_inventory: FileBinding
    # Deliberately no engine, job, binary, receipt or final acceptance reference.


class ToolInputs(FrozenModel):
    format: Literal["uarch-k2-tool-inputs/1"]
    accepted_k1_pins: FileBinding
    compiler_commit: GitCommit
    rust_release: Literal["1.99.0"]
    target: Literal["x86_64-unknown-linux-gnu"]
    image_digest: Hash
    cargo_lock: FileBinding
    full_metadata: FileBinding
    target_metadata: FileBinding
    feature_graph: FileBinding
    licence_inventory: FileBinding
    crate_checksum_inventory: FileBinding
    linker_and_os_inventory: FileBinding
    flags: tuple[NonEmpty, ...]


class SourceInput(FileBinding):
    role: Literal[
        "rust",
        "canonicalization",
        "schema",
        "build-script",
        "generator",
        "python-build-helper",
        "config",
        "trust",
        "tool-input",
    ]


class ModeConfig(FrozenModel):
    mode: Literal["debug", "release"]
    cargo_args: tuple[NonEmpty, ...]
    rustflags: tuple[NonEmpty, ...]


class BuildInputs(FrozenModel):
    format: Literal["uarch-k2-build-inputs/1"]
    source_commit: GitCommit
    source_files: Annotated[tuple[SourceInput, ...], Field(min_length=1)]
    trust_hash: Hash
    trust_file: FileBinding
    tool_inputs_hash: Hash
    tool_inputs_file: FileBinding
    model_source_paths: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]
    model_inputs_hash: Hash
    mode_configs: tuple[ModeConfig, ModeConfig]
    generated_identity_output_paths: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]
    permitted_environment: dict[NonEmpty, str]

    @model_validator(mode="after")
    def acyclic_inputs(self) -> "BuildInputs":
        paths = [f.path for f in self.source_files]
        if paths != sorted(set(paths)):
            raise ValueError("Source paths must be sorted and unique")
        if not set(self.model_source_paths) <= set(paths):
            raise ValueError("Model subset must use recorded source inputs")
        if set(self.generated_identity_output_paths) & set(paths):
            raise ValueError("Generated identity cannot hash itself")
        if tuple(x.mode for x in self.mode_configs) != ("debug", "release"):
            raise ValueError("Exact separate debug/release configurations required")
        return self


class BuildReceipt(FrozenModel):
    format: Literal["uarch-k2-build-receipt/1"]
    build_input_hash: Hash
    engine: NativeEngineIdentity
    mode: Literal["debug", "release"]
    target: Literal["x86_64-unknown-linux-gnu"]
    executable: FileBinding
    image_digest: Hash
    generated_identity_outputs: Annotated[tuple[FileBinding, ...], Field(min_length=1)]
    actual_read_inventory: FileBinding
    actual_environment: FileBinding
    compiler_verbose: FileBinding
    build_log: FileBinding
    binary_origin_check: FileBinding
    software_path_check: FileBinding

    @model_validator(mode="after")
    def engine_join(self) -> "BuildReceipt":
        if self.engine.implementation_hash != self.build_input_hash:
            raise ValueError("Engine/build input mismatch")
        return self


class ApprovedExecutable(FrozenModel):
    mode: Literal["debug", "release"]
    executable: FileBinding
    build_receipt: FileBinding
    target: Literal["x86_64-unknown-linux-gnu"]


class HostRecord(FrozenModel):
    format: Literal["uarch-k2-first-use/1"]
    decision: FileBinding
    independent_review: FileBinding
    semantics: FileBinding
    trust_hash: Hash
    trust_file: FileBinding
    build_input_hash: Hash
    build_input_file: FileBinding
    tool_inputs_hash: Hash
    model_inputs_hash: Hash
    loader_read_inventory: FileBinding
    expected_engine: NativeEngineIdentity
    executables: tuple[ApprovedExecutable, ApprovedExecutable]
    jobs_inventory: FileBinding
    corpus_inventory: FileBinding
    profile_hashes: Annotated[tuple[Hash, ...], Field(min_length=1)]
    registry_hash: Hash

    @model_validator(mode="after")
    def final_joins(self) -> "HostRecord":
        e = self.expected_engine
        if (e.implementation_hash, e.compiler_lock_hash, e.model.implementation_hash) != (
            self.build_input_hash,
            self.tool_inputs_hash,
            self.model_inputs_hash,
        ):
            raise ValueError("Final identity joins required")
        if tuple(x.mode for x in self.executables) != ("debug", "release"):
            raise ValueError("Both actual executable bindings required")
        return self


class HostSelector(FrozenModel):
    format: Literal["uarch-k2-host-selector/1"]
    repository: NonEmpty
    acceptance_commit: GitCommit
    record_path: NonEmpty
    record_byte_hash: Hash
    # Independently installed by human host configuration, never caller input.


ROOTS = (BuildTrust, ToolInputs, BuildInputs, BuildReceipt, HostRecord, HostSelector)


def schemas(output: Path) -> None:
    import json

    output.mkdir(parents=True, exist_ok=True)
    for model in ROOTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (output / (model.__name__ + ".json")).write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n"
        )


if __name__ == "__main__":
    schemas(Path(__file__).with_name("record-schemas"))
