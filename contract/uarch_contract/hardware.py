"""Rev-2 hardware vocabulary. Numeric leaves carry evidence, including counts.

Cycles here describe hardware: cores use core, NoC/sync/shared SRAM use noc,
DRAM timing uses dram. Requests and result rows never carry cycle quantities.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, ConfigDict, Field, field_validator, model_validator

from .common import FrozenModel, JsonPositiveFloat, NonEmpty, PositiveFloat, Sha
from .common import JsonNonNegativeInt as NonNegativeInt
from .errors import StipulationOnReference, UnnamedPreset
from .precision import PrecisionFormat
from .sourced import SourcedValue


def nonnegative(value: SourcedValue) -> SourcedValue:
    if value.value < 0:
        raise ValueError("Hardware quantities must be nonnegative.")
    return value


def positive(value: SourcedValue) -> SourcedValue:
    if value.value <= 0:
        raise ValueError("Hardware capacities, rates and counts must be positive.")
    return value


def integral(value: SourcedValue) -> SourcedValue:
    if not value.value.is_integer():
        raise ValueError("Hardware counts require an integral value.")
    return value


Quantity = Annotated[SourcedValue, AfterValidator(nonnegative)]
PositiveQuantity = Annotated[Quantity, AfterValidator(positive)]
Count = Annotated[PositiveQuantity, AfterValidator(integral)]
Coordinate = tuple[NonNegativeInt, NonNegativeInt]


class ClockDomain(FrozenModel):
    freq_hz: PositiveQuantity
    scales_with_core: bool


class CoreClockDomain(ClockDomain):
    scales_with_core: Literal[True] = True


class ClockDomains(FrozenModel):
    core: CoreClockDomain
    noc: ClockDomain
    dram: ClockDomain


class HardwareGrid(FrozenModel):
    rows: Count
    cols: Count


class MatrixEngine(FrozenModel):
    array: HardwareGrid
    dataflows: Annotated[
        tuple[Literal["weight_stationary", "output_stationary"], ...], Field(min_length=1)
    ]
    macs_per_cycle: dict[PrecisionFormat, PositiveQuantity]
    accumulator_bytes: PositiveQuantity
    operand_buffer_bytes: PositiveQuantity
    operand_bytes_per_cycle: PositiveQuantity


class VectorEngine(FrozenModel):
    ops_per_cycle: PositiveQuantity


class Sram(FrozenModel):
    bytes: PositiveQuantity
    banks: Count
    bytes_per_cycle_per_bank: PositiveQuantity


class Dma(FrozenModel):
    engines: Count
    bytes_per_cycle: PositiveQuantity
    max_outstanding: Count
    request_bytes: PositiveQuantity


class CoreType(FrozenModel):
    matrix_engine: MatrixEngine
    vector_engine: VectorEngine
    sram: Sram
    dma: Dma
    job_overhead_cycles: Quantity


class Cores(FrozenModel):
    grid: HardwareGrid
    core_type: CoreType


class Sync(FrozenModel):
    mechanism: Literal["noc_semaphore", "hardware_barrier"]
    barrier_latency_cycles: Quantity


class SharedSram(Sram):
    latency_cycles: Quantity
    attach: Annotated[tuple[Coordinate, ...], Field(min_length=1)]


class Noc(FrozenModel):
    topology: Literal["mesh", "torus"]
    direction: Literal["positive", "negative", "bidirectional"]
    link_bytes_per_cycle: PositiveQuantity
    router_latency_cycles: Quantity
    virtual_channels: Count
    buffer_flits: Count


class Interleave(FrozenModel):
    granularity_bytes: PositiveQuantity
    scheme: Literal["channel_hash", "round_robin"]


class Controller(FrozenModel):
    attach: Coordinate
    scheduler: Literal["fr_fcfs", "fcfs"]
    page_policy: Literal["open", "closed"]
    read_queue_depth: Count
    write_queue_depth: Count
    noc_credits: Count


class DramOrganization(FrozenModel):
    ranks: Count
    bank_groups: Count
    banks_per_group: Count
    row_bytes: PositiveQuantity


class TimingPreset(FrozenModel):
    file: NonEmpty
    sha: Sha

    @model_validator(mode="before")
    @classmethod
    def pinned(cls, data: Any) -> Any:
        if isinstance(data, dict) and not re.fullmatch("[0-9a-f]{40}", str(data.get("sha", ""))):
            raise UnnamedPreset("memory.dram.timing_preset requires a pinned 40-hex sha.")
        return data


class DramTiming(FrozenModel):
    t_rcd_cycles: Quantity
    t_rp_cycles: Quantity
    t_cl_cycles: Quantity
    t_rfc_cycles: Quantity
    t_refi_cycles: PositiveQuantity


class Dram(FrozenModel):
    """Explicit timing origin; source strings are citations, never mode selectors."""

    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"timing_source": {"const": "direct"}}},
                    "then": {"properties": {"timing_preset": {"type": "null"}}},
                },
                {
                    "if": {"properties": {"timing_source": {"const": "preset"}}},
                    "then": {
                        "required": ["timing_preset"],
                        "properties": {"timing_preset": {"type": "object"}},
                    },
                },
            ]
        }
    )
    standard: NonEmpty
    channels: Count
    bw_bytes_per_s: PositiveQuantity
    capacity_bytes: PositiveQuantity
    organization: DramOrganization
    timing_source: Literal["direct", "preset"]
    timing_preset: TimingPreset | None = None
    timing: DramTiming

    @model_validator(mode="after")
    def named_preset(self) -> Dram:
        if self.timing_source == "direct":
            if self.timing_preset is not None:
                raise ValueError("direct timing requires memory.dram.timing_preset=None.")
            return self
        if self.timing_preset is None:
            raise UnnamedPreset(
                "preset timing requires memory.dram.timing_preset with file and sha."
            )
        expected = f"{self.timing_preset.file}@{self.timing_preset.sha}"
        for name in type(self.timing).model_fields:
            value = getattr(self.timing, name)
            # Stubs and proposed-design stipulations retain their own provenance rules.
            if value.kind == "claim" and value.provenance != "stub" and value.source != expected:
                raise UnnamedPreset(
                    f"memory.dram.timing.{name} cites {value.source!r}; "
                    f"memory.dram.timing_preset names {expected!r}."
                )
        return self


class Memory(FrozenModel):
    interleave: Interleave
    controllers: Annotated[tuple[Controller, ...], Field(min_length=1)]
    dram: Dram


class NumericFormat(FrozenModel):
    bytes: JsonPositiveFloat
    accumulate_bytes: PositiveQuantity
    block_scale_bytes: Quantity


class Energy(FrozenModel):
    pj_per_mac: dict[PrecisionFormat, Quantity]
    pj_per_byte: dict[Literal["sram", "noc_hop", "dram"], Quantity]
    voltage_ratio: dict[PositiveFloat, PositiveQuantity]

    @field_validator("voltage_ratio", mode="before")
    @classmethod
    def unique_voltage_keys(cls, value: Any) -> Any:
        if isinstance(value, dict):
            normalized = [float(key) for key in value]
            if len(set(normalized)) != len(normalized):
                raise ValueError("duplicate normalized voltage_ratio keys are forbidden.")
        return value


def sourced_leaves(value: Any, path: str = "") -> Iterator[tuple[str, SourcedValue]]:
    if isinstance(value, SourcedValue):
        yield path, value
    elif isinstance(value, FrozenModel):
        for key in type(value).model_fields:
            yield from sourced_leaves(getattr(value, key), f"{path}.{key}" if path else key)
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from sourced_leaves(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from sourced_leaves(child, f"{path}[{index}]")


# Explicit paths, not suffix inference. [] is an array index; * is one mapping key.
# Raw coordinates are dimensionless indices; formats.*.bytes is an implicit byte width.
# Those scalar fields have no SourcedValue.unit to validate.
HARDWARE_UNIT_RULES: dict[str, tuple[str, ...]] = {
    "clock_domains.core.freq_hz": ("Hz",),
    "clock_domains.noc.freq_hz": ("Hz",),
    "clock_domains.dram.freq_hz": ("Hz",),
    "cores.grid.rows": ("count",),
    "cores.grid.cols": ("count",),
    "cores.core_type.matrix_engine.array.rows": ("count",),
    "cores.core_type.matrix_engine.array.cols": ("count",),
    "cores.core_type.matrix_engine.macs_per_cycle.*": ("MAC/cycle",),
    "cores.core_type.matrix_engine.accumulator_bytes": ("byte", "B"),
    "cores.core_type.matrix_engine.operand_buffer_bytes": ("byte", "B"),
    "cores.core_type.matrix_engine.operand_bytes_per_cycle": ("byte/cycle",),
    "cores.core_type.vector_engine.ops_per_cycle": ("op/cycle",),
    "cores.core_type.sram.bytes": ("byte", "B"),
    "cores.core_type.sram.banks": ("count",),
    "cores.core_type.sram.bytes_per_cycle_per_bank": ("byte/cycle",),
    "cores.core_type.dma.engines": ("count",),
    "cores.core_type.dma.bytes_per_cycle": ("byte/cycle",),
    "cores.core_type.dma.max_outstanding": ("count",),
    "cores.core_type.dma.request_bytes": ("byte", "B"),
    "cores.core_type.job_overhead_cycles": ("cycle",),
    "sync.barrier_latency_cycles": ("cycle",),
    "shared_sram.bytes": ("byte", "B"),
    "shared_sram.banks": ("count",),
    "shared_sram.bytes_per_cycle_per_bank": ("byte/cycle",),
    "shared_sram.latency_cycles": ("cycle",),
    "nocs[].link_bytes_per_cycle": ("byte/cycle",),
    "nocs[].router_latency_cycles": ("cycle",),
    "nocs[].virtual_channels": ("count",),
    "nocs[].buffer_flits": ("count",),
    "memory.interleave.granularity_bytes": ("byte", "B"),
    "memory.controllers[].read_queue_depth": ("count",),
    "memory.controllers[].write_queue_depth": ("count",),
    "memory.controllers[].noc_credits": ("count",),
    "memory.dram.channels": ("count",),
    "memory.dram.bw_bytes_per_s": ("byte/s",),
    "memory.dram.capacity_bytes": ("byte", "B"),
    "memory.dram.organization.ranks": ("count",),
    "memory.dram.organization.bank_groups": ("count",),
    "memory.dram.organization.banks_per_group": ("count",),
    "memory.dram.organization.row_bytes": ("byte", "B"),
    "memory.dram.timing.t_rcd_cycles": ("cycle",),
    "memory.dram.timing.t_rp_cycles": ("cycle",),
    "memory.dram.timing.t_cl_cycles": ("cycle",),
    "memory.dram.timing.t_rfc_cycles": ("cycle",),
    "memory.dram.timing.t_refi_cycles": ("cycle",),
    "formats.*.accumulate_bytes": ("byte", "B"),
    "formats.*.block_scale_bytes": ("byte", "B"),
    "energy.pj_per_mac.*": ("pJ/MAC",),
    "energy.pj_per_byte.sram": ("pJ/byte",),
    "energy.pj_per_byte.noc_hop": ("pJ/byte",),
    "energy.pj_per_byte.dram": ("pJ/byte",),
    "energy.voltage_ratio.*": ("ratio",),
    "static_power_w": ("W",),
    "tdp_w": ("W",),
}


def hardware_unit_rule(path: str) -> tuple[str, ...]:
    for pattern, allowed in HARDWARE_UNIT_RULES.items():
        expression = re.escape(pattern).replace(r"\[\]", r"\[\d+\]").replace(r"\*", ".+")
        if re.fullmatch(expression, path):
            return allowed
    raise ValueError(f"{path}: no explicit HardwareSpec unit rule.")


def hardware_schema(schema: dict[str, Any]) -> None:
    schema["description"] = (
        "Hardware inputs. Unit/path consistency is semantic validation; "
        "x-hardware-unit-rules lists exact allowed labels, without conversion. "
        "Coordinates are count indices; formats.*.bytes is an implicit byte width; "
        "energy.voltage_ratio keys are dimensionless frequency ratios. "
        "byte and B are equivalent labels preserved verbatim."
    )
    schema["x-hardware-unit-rules"] = HARDWARE_UNIT_RULES


class HardwareSpec(FrozenModel):
    model_config = ConfigDict(json_schema_extra=hardware_schema)
    id: NonEmpty
    design_status: Literal["proposed", "reference"]
    clock_domains: ClockDomains
    cores: Cores
    sync: Sync
    shared_sram: SharedSram | None = None
    nocs: Annotated[tuple[Noc, ...], Field(min_length=1)]
    memory: Memory
    formats: dict[PrecisionFormat, NumericFormat]
    energy: Energy
    static_power_w: Quantity
    tdp_w: PositiveQuantity

    @model_validator(mode="after")
    def coherent(self) -> HardwareSpec:
        for path, value in sourced_leaves(self):
            allowed = hardware_unit_rule(path)
            if value.unit not in allowed:
                raise ValueError(
                    f"{path}: supplied unit {value.unit!r}; allowed units {allowed!r}."
                )
        if self.design_status == "reference":
            for path, value in sourced_leaves(self):
                if value.kind == "stipulation":
                    raise StipulationOnReference(f"{path}: a reference permits only claims.")
        if "sram" not in self.energy.pj_per_byte:
            raise ValueError("cores.core_type.sram.bytes requires energy.pj_per_byte.sram.")
        if not self.formats or not self.cores.core_type.matrix_engine.macs_per_cycle:
            raise ValueError("formats and matrix_engine.macs_per_cycle must be non-empty.")
        coordinates = [c.attach for c in self.memory.controllers]
        if self.shared_sram:
            coordinates.extend(self.shared_sram.attach)
        for r, c in coordinates:
            if r >= self.cores.grid.rows.value or c >= self.cores.grid.cols.value:
                raise ValueError(f"attach coordinate {(r, c)} lies outside cores.grid.")
        return self
