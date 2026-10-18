"""Additive component records. Valid shapes and construction pins are never authority."""

from typing import Annotated, Literal

from pydantic import Field, model_validator
from uarch_contract.common import FrozenModel, Hash, NonEmpty
from uarch_contract.mapped import NativeEngineIdentity

from .records import FileBinding, GitCommit, ModeConfig, SourceInput

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
CHECKER = "validation.component.observations_v3:check_v3"
OBSERVATIONS = "uarch-native-observations/3"


class ComponentBuildTrust(FrozenModel):
    format: Literal["uarch-component-build-trust/2"]
    purpose: Literal["private-synthetic-tests-only"]
    semantics_file: FileBinding
    registry_hash: Hash
    registry_file: FileBinding
    profiles: Annotated[tuple[FileBinding, ...], Field(min_length=1)]
    selection: FileBinding
    # Selection contains engine-free raw closure/profile promises, not later jobs/receipts.


class ComponentBuildInputs(FrozenModel):
    format: Literal["uarch-component-build-inputs/2"]
    source_commit: GitCommit
    source_files: Annotated[tuple[SourceInput, ...], Field(min_length=1)]
    trust_hash: Hash
    trust_file: FileBinding
    tool_inputs_hash: Hash
    tool_inputs_file: FileBinding
    model_source_paths: Annotated[tuple[NonEmpty, ...], Field(min_length=1)]
    model_inputs_hash: Hash
    mode_configs: tuple[ModeConfig, ModeConfig]
    generated_identity_output_paths: tuple[NonEmpty, ...]
    permitted_environment: dict[NonEmpty, str]

    @model_validator(mode="after")
    def acyclic(self) -> "ComponentBuildInputs":
        paths = [f.path for f in self.source_files]
        if paths != sorted(set(paths)) or not set(self.model_source_paths) <= set(paths):
            raise ValueError("complete sorted unique source/model inventory required")
        if list(self.model_source_paths) != sorted(set(self.model_source_paths)):
            raise ValueError("sorted unique model inventory required")
        if self.generated_identity_output_paths != (
            "native/crates/uarch-engine/generated/identity.rs",
        ) or set(self.generated_identity_output_paths) & set(paths):
            raise ValueError("acyclic explicit generated identity required")
        if tuple(x.mode for x in self.mode_configs) != ("debug", "release"):
            raise ValueError("separate debug/release configurations required")
        return self


class ComponentBuildReceipt(FrozenModel):
    format: Literal["uarch-component-build-receipt/1"]
    build_input_hash: Hash
    engine: NativeEngineIdentity
    mode: Literal["debug", "release"]
    executable: FileBinding
    image_digest: Literal["sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"]
    generated_identity: FileBinding
    build_log: FileBinding
    environment: FileBinding
    loader_observations: FileBinding
    limitations: tuple[NonEmpty, ...]

    @model_validator(mode="after")
    def joined(self) -> "ComponentBuildReceipt":
        require_component_engine(self.engine)
        if self.engine.implementation_hash != self.build_input_hash:
            raise ValueError("component executable/build identity mismatch")
        return self


class ComponentExecutable(FrozenModel):
    mode: Literal["debug", "release"]
    executable: FileBinding
    receipt: FileBinding


class ComponentJobBinding(FrozenModel):
    case_id: NonEmpty
    job_hash: Hash
    profile_hash: Hash
    file: FileBinding


class ComponentConsumers(FrozenModel):
    checker: Literal["validation.component.observations_v3:check_v3"]
    observations: Literal["uarch-native-observations/3"]
    import_root: NonEmpty
    files: Annotated[tuple[FileBinding, ...], Field(min_length=1)]
    observation_contract: FileBinding
    python_executable: FileBinding
    external_files: Annotated[tuple[FileBinding, ...], Field(min_length=1)]


class ComponentBudget(FrozenModel):
    calls: Annotated[int, Field(strict=True, ge=1, le=10000)]
    session_seconds: Annotated[int, Field(strict=True, ge=1, le=86400)]
    timeout_s: Annotated[int, Field(strict=True, ge=1, le=600)]
    stdin_bytes: Annotated[int, Field(strict=True, ge=1, le=64 * 1024 * 1024)]
    stdout_bytes: Annotated[int, Field(strict=True, ge=1, le=64 * 1024 * 1024)]
    stderr_bytes: Annotated[int, Field(strict=True, ge=1, le=1024 * 1024)]


class ComponentPayload(FrozenModel):
    format: Literal["uarch-component-runtime-payload/1"]
    engine: NativeEngineIdentity
    build_inputs: FileBinding
    registry: FileBinding
    profiles: Annotated[tuple[FileBinding, ...], Field(min_length=1)]
    jobs: Annotated[tuple[ComponentJobBinding, ...], Field(min_length=1)]
    executables: tuple[ComponentExecutable, ComponentExecutable]
    consumers: ComponentConsumers
    budget: ComponentBudget

    @model_validator(mode="after")
    def finite(self) -> "ComponentPayload":
        require_component_engine(self.engine)
        if tuple(x.mode for x in self.executables) != ("debug", "release"):
            raise ValueError("both actual component executable modes required")
        for values in ([x.case_id for x in self.jobs], [x.job_hash for x in self.jobs]):
            if len(set(values)) != len(values):
                raise ValueError("unique finite component jobs required")
        paths = [x.path for x in self.consumers.files]
        if paths != sorted(set(paths)):
            raise ValueError("sorted unique consumer/import closure required")
        return self


class ComponentHostRecord(FrozenModel):
    format: Literal["uarch-component-first-use/1"]
    payload: FileBinding
    decision: FileBinding
    independent_review: FileBinding


class ComponentHostSelector(FrozenModel):
    format: Literal["uarch-component-host-selector/1"]
    repository: NonEmpty
    acceptance_commit: GitCommit
    record_path: NonEmpty
    record_byte_hash: Hash


def require_component_engine(engine: NativeEngineIdentity) -> None:
    if (engine.name, engine.version, engine.model.name, engine.model.version) != (
        "native",
        "native-stage/1",
        "native-intervals",
        "2",
    ):
        raise ValueError("component native-intervals/2 identity required")
