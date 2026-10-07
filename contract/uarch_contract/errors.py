"""User-facing refusals and a language-neutral error envelope (U0001 proposal)."""

from __future__ import annotations

from typing import ClassVar, Literal

from .common import FrozenModel, NonEmpty


class ContractError(ValueError):
    sentence: ClassVar[str] = "The contract input is invalid."

    def __init__(self, sentence: str | None = None) -> None:
        super().__init__(sentence or self.sentence)

    def to_record(self) -> ErrorRecord:
        return ErrorRecord.model_validate({"code": type(self).__name__, "message": str(self)})


class NoTableForComponent(ContractError):
    sentence = "No characterization table exists for this component."


class EnvelopeExceedsGrid(ContractError):
    sentence = "The workload envelope exceeds the table grid; extrapolation is refused."


class SpecHashMismatch(ContractError):
    sentence = "The table hardware spec hash does not match the component spec."


class ParamsMismatch(ContractError):
    sentence = "The component parameters do not match the parameters derived from the spec."


class TpMismatch(ContractError):
    sentence = "The table tp does not match the plan tp; a shard cannot be rescaled."


class ContractMajorMismatch(ContractError):
    sentence = "The contract major versions differ; this table cannot be read."


class ContractMinorMismatch(UserWarning):
    sentence: ClassVar[str] = "The contract minor versions differ; check additive compatibility."

    def __init__(self, sentence: str | None = None) -> None:
        super().__init__(sentence or self.sentence)

    def to_record(self) -> ErrorRecord:
        return ErrorRecord(code="ContractMinorMismatch", message=str(self))


class ResidencyExceedsCapacity(ContractError):
    sentence = "Resident weights exceed the declared memory capacity."


class NonFiniteRow(ContractError):
    sentence = "A table row contains a non-finite or negative quantity."


class MissingFrequencyAxis(ContractError):
    sentence = "DVFS requires a table frequency axis."


class InitialStateMismatch(ContractError):
    sentence = "Back-to-back R1 iterations require a steady table, not a cold table."


class KvLayoutMismatch(ContractError):
    sentence = "The table KV block size does not match the plan block size."


class StipulationOnReference(ContractError):
    sentence = "A reference hardware spec may contain only claims, never stipulations."


class ClaimWithoutSource(ContractError):
    sentence = "A non-stub claim requires a non-empty source."


class SramCapacityExceeded(ContractError):
    sentence = "The mapped operands exceed the available SRAM capacity."


class UnnamedPreset(ContractError):
    sentence = "DRAM timing must cite the named preset file at its pinned commit SHA."


class ShardIndivisible(ContractError):
    sentence = "The model dimension cannot be divided into the requested tp shards."


ErrorCode = Literal[
    "NoTableForComponent",
    "EnvelopeExceedsGrid",
    "SpecHashMismatch",
    "ParamsMismatch",
    "TpMismatch",
    "ContractMajorMismatch",
    "ContractMinorMismatch",
    "ResidencyExceedsCapacity",
    "NonFiniteRow",
    "MissingFrequencyAxis",
    "InitialStateMismatch",
    "KvLayoutMismatch",
    "StipulationOnReference",
    "ClaimWithoutSource",
    "SramCapacityExceeded",
    "UnnamedPreset",
    "ShardIndivisible",
]
ERROR_TYPES: dict[str, type[ContractError] | type[ContractMinorMismatch]] = {
    cls.__name__: cls
    for cls in (
        NoTableForComponent,
        EnvelopeExceedsGrid,
        SpecHashMismatch,
        ParamsMismatch,
        TpMismatch,
        ContractMajorMismatch,
        ContractMinorMismatch,
        ResidencyExceedsCapacity,
        NonFiniteRow,
        MissingFrequencyAxis,
        InitialStateMismatch,
        KvLayoutMismatch,
        StipulationOnReference,
        ClaimWithoutSource,
        SramCapacityExceeded,
        UnnamedPreset,
        ShardIndivisible,
    )
}


class ErrorRecord(FrozenModel):
    code: ErrorCode
    message: NonEmpty

    def to_exception(self) -> ContractError | ContractMinorMismatch:
        return ERROR_TYPES[self.code](self.message)
