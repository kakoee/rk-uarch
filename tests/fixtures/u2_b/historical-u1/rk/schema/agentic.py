"""P8b profile data / P8a consumption contract, ADRs 0023 and 0049.

No production defaults: distributions describe declared inputs, not measurements
made by the simulator. YAML I/O belongs above the engine.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from rk.provenance import Calibration, SourcedValue, combine


def _parameter(value: SourcedValue, unit: str, minimum: float) -> None:
    if value.unit != unit or value.value < minimum:
        raise ValueError(f'expected {unit} with value >= {minimum}')
    if value.provenance is not Calibration.STUB and (not value.source or not value.date):
        raise ValueError('non-STUB profile parameters require source and date')


class DurationDistribution(BaseModel):
    """Lognormal in milliseconds: median * exp(sigma * standard_normal)."""

    model_config = ConfigDict(frozen=True, extra='forbid')
    median_ms: SourcedValue
    sigma: SourcedValue

    @model_validator(mode='after')
    def _valid(self) -> DurationDistribution:
        _parameter(self.median_ms, 'ms', 0)
        _parameter(self.sigma, '1', 0)
        return self


class AgenticProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    id: str
    turns_min: SourcedValue
    turns_max: SourcedValue
    tool_cpu: DurationDistribution
    remote_wait: DurationDistribution
    cpu_cores_active: SourcedValue
    context_growth_factor: SourcedValue
    split_provenance: Calibration
    split_source: str | None = None
    second_model_as_tool: bool = False

    @model_validator(mode='after')
    def _valid(self) -> AgenticProfile:
        for turns in (self.turns_min, self.turns_max):
            _parameter(turns, 'count', 1)
            if not turns.value.is_integer():
                raise ValueError('turn counts must be integers')
        if self.turns_max.value < self.turns_min.value:
            raise ValueError('turns_max must be >= turns_min')
        _parameter(self.cpu_cores_active, 'count', 0)
        if self.cpu_cores_active.value == 0:
            raise ValueError('cpu_cores_active must be positive')
        _parameter(self.context_growth_factor, '1', 1)
        if self.split_provenance not in (Calibration.STUB, Calibration.ESTIMATED):
            raise ValueError('profile CPU/remote split is at most estimated')
        if self.split_provenance is Calibration.ESTIMATED and not self.split_source:
            raise ValueError('an estimated split requires split_source; otherwise use STUB')
        return self

    @property
    def sourced_values(self) -> tuple[tuple[str, SourcedValue], ...]:
        return (
            ('turns_min', self.turns_min), ('turns_max', self.turns_max),
            ('tool_cpu.median_ms', self.tool_cpu.median_ms),
            ('tool_cpu.sigma', self.tool_cpu.sigma),
            ('remote_wait.median_ms', self.remote_wait.median_ms),
            ('remote_wait.sigma', self.remote_wait.sigma),
            ('cpu_cores_active', self.cpu_cores_active),
            ('context_growth_factor', self.context_growth_factor),
        )

    @property
    def badge(self) -> Calibration:
        return combine([Calibration.ESTIMATED, self.split_provenance,
                        *(v.provenance for _, v in self.sourced_values)])

    @property
    def contributors(self) -> tuple[str, ...]:
        return (*(f'workload.agentic_profile.{name}' for name, _ in self.sourced_values),
                'workload.agentic_profile.split_provenance', 'model.runtime.r1.agentic')
