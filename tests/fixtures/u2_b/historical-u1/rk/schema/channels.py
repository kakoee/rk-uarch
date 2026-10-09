"""Additive P7b diagnostics and pure energy input seam. ADR 0041."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rk.provenance import Metric, SourcedValue
from rk.schema.execution import PrecisionFormat

Channel = Literal['matrix_ops', 'vector_ops', 'memory_read', 'memory_write',
                  'network_send', 'network_receive']
Phase = Literal['prefill', 'decode']
Coverage = Literal['modelled', 'partial', 'unmodelled']


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')


class Available(FrozenModel):
    state: Literal['available'] = 'available'
    metric: Metric

    @model_validator(mode='after')
    def valid_metric(self) -> Available:
        if self.metric.value < 0:
            raise ValueError('diagnostic quantities must be nonnegative')
        if self.metric.ci95_low is not None or self.metric.ci95_high is not None:
            raise ValueError('single analytical quantities have no confidence interval')
        if not self.metric.contributors:
            raise ValueError('available diagnostic quantities require contributors')
        return self


class Unavailable(FrozenModel):
    state: Literal['unavailable'] = 'unavailable'
    unit: str
    badge: Literal['stub'] = 'stub'
    reason: Annotated[str, Field(min_length=1)]
    contributors: tuple[str, ...] = ()


AvailableQuantity = Annotated[Available | Unavailable, Field(discriminator='state')]


def require_unit(quantity: AvailableQuantity, unit: str) -> None:
    actual = quantity.metric.unit if isinstance(quantity, Available) else quantity.unit
    if actual != unit:
        raise ValueError(f'quantity requires {unit}, got {actual}')


class ChannelCount(FrozenModel):
    channel: Channel
    phase: Phase
    operator_id: str
    component_id: str
    instance_path: str
    level: str | None = None
    transfer_id: str | None = None
    count: AvailableQuantity
    coverage: Coverage
    omissions: tuple[str, ...] = ()

    @model_validator(mode='after')
    def valid_count(self) -> ChannelCount:
        require_unit(self.count, 'op' if self.channel.endswith('_ops') else 'byte')
        if (self.coverage == 'unmodelled') != isinstance(self.count, Unavailable):
            raise ValueError('unmodelled counts must be unavailable, never numeric zero')
        if self.coverage != 'modelled' and not self.omissions:
            raise ValueError('partial/unmodelled counts require omissions')
        if self.coverage == 'modelled' and self.omissions:
            raise ValueError('modelled count cannot carry omissions')
        if self.channel.startswith('network_') != (self.transfer_id is not None):
            raise ValueError('only network counts require a transfer_id')
        return self


class EnergyCoefficient(FrozenModel):
    component_id: str
    instance_path: str
    channel: Channel
    level: str | None = None
    basis: Literal['MAC', 'FLOP', 'byte_transferred', 'byte_endpoint']
    pj_per_unit: SourcedValue
    transfer_charge: Literal['once', 'endpoint']

    @model_validator(mode='after')
    def valid_basis(self) -> EnergyCoefficient:
        expected = 'pJ/' + self.basis if self.basis in ('MAC', 'FLOP') else 'pJ/byte'
        if self.pj_per_unit.unit != expected or self.pj_per_unit.value < 0:
            raise ValueError(f'coefficient requires nonnegative {expected}')
        if self.channel.endswith('_ops'):
            valid = self.basis in ('MAC', 'FLOP') and self.transfer_charge == 'endpoint'
        elif self.channel.startswith('memory_'):
            valid = self.basis == 'byte_endpoint' and self.transfer_charge == 'endpoint'
        else:
            valid = ((self.basis == 'byte_endpoint' and self.transfer_charge == 'endpoint')
                     or (self.basis == 'byte_transferred' and self.transfer_charge == 'once'
                         and self.channel == 'network_send'))
        if not valid:
            raise ValueError('coefficient basis/charge does not match channel')
        return self


class StaticPower(FrozenModel):
    component_id: str
    instance_path: str
    watts: SourcedValue

    @model_validator(mode='after')
    def valid_watts(self) -> StaticPower:
        if self.watts.unit != 'W' or self.watts.value < 0:
            raise ValueError('static power requires nonnegative W')
        return self


class PowerIdentity(FrozenModel):
    model: Literal['tdp_ceiling', 'utilization_dvfs', 'channel_energy']
    formula_version: str
    coverage: Literal['complete', 'partial', 'unmodelled']
    contributors: tuple[str, ...]


class EnergyDiagnostic(FrozenModel):
    identity: PowerIdentity
    window_id: str
    duration_s: AvailableQuantity
    dynamic_j: AvailableQuantity
    static_j: AvailableQuantity
    it_j: AvailableQuantity
    omissions: tuple[str, ...]

    @model_validator(mode='after')
    def valid_energy(self) -> EnergyDiagnostic:
        require_unit(self.duration_s, 's')
        for value in (self.dynamic_j, self.static_j, self.it_j):
            require_unit(value, 'J')
        if self.identity.coverage != 'complete':
            if not self.omissions or isinstance(self.it_j, Available):
                raise ValueError('incomplete energy requires omissions and unavailable IT total')
        elif self.omissions or any(isinstance(q, Unavailable) for q in
                                  (self.dynamic_j, self.static_j, self.it_j)):
            raise ValueError('complete energy requires all terms and no omissions')
        return self


class PhaseDiagnostic(FrozenModel):
    phase: Phase
    scope: Literal['analytical_representative_rank'] = 'analytical_representative_rank'
    batch_size: Annotated[int, Field(ge=1)]
    context_tokens: Annotated[int, Field(ge=1)]
    tensor_parallel_degree: Annotated[int, Field(ge=1)]
    compute_precision: PrecisionFormat
    kv_precision: PrecisionFormat
    channels: tuple[ChannelCount, ...]
    compute_s: AvailableQuantity
    memory_s: AvailableQuantity
    communication_s: AvailableQuantity
    total_s: AvailableQuantity
    limiting_resource: Literal['compute', 'memory', 'network'] | None
    omissions: tuple[str, ...]

    @model_validator(mode='after')
    def valid_phase(self) -> PhaseDiagnostic:
        for value in (self.compute_s, self.memory_s, self.communication_s, self.total_s):
            require_unit(value, 's')
        if any(row.phase != self.phase for row in self.channels):
            raise ValueError('channel phase differs from diagnostic phase')
        return self


class RuntimeChannelWindow(FrozenModel):
    window_id: str
    scope: Literal['simulated_representative_rank'] = 'simulated_representative_rank'
    channels: tuple[ChannelCount, ...]
    duration_s: AvailableQuantity
    delivered_tokens: AvailableQuantity
    omissions: tuple[str, ...]


class DiagnosticsV1(FrozenModel):
    schema_version: Literal['1'] = '1'
    phases: tuple[PhaseDiagnostic, ...]
    energy: tuple[EnergyDiagnostic, ...]
    omissions: tuple[str, ...]
    runtime_windows: tuple[RuntimeChannelWindow, ...] = ()
