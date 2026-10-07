"""Which fidelity level ran, per axis — and which levels this prototype implements.

Validation lives here rather than in `rk/engine/registry.py` for two reasons: it must
run before the engine is reached, and `schema` may not import `engine` (rk/README.md
layering). P3 adds the registry that maps a level to a model function and asserts the
two agree.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, model_validator

from rk.provenance import (
    ComputeFidelity,
    MemoryFidelity,
    NetworkFidelity,
    RuntimeFidelity,
)

__all__ = ["IMPLEMENTED", "FidelityMap", "FidelityOverride", "effective_fidelity"]


# build-spec §2.3.2: the prototype implements the left-most level of each axis, plus R1.
# STUB is always allowed — declaring "no model here" is a first-class answer.
IMPLEMENTED: Final[dict[str, frozenset[str]]] = {
    "compute": frozenset({ComputeFidelity.C0, ComputeFidelity.STUB}),
    "memory": frozenset({MemoryFidelity.M0, MemoryFidelity.STUB}),
    "network": frozenset({NetworkFidelity.N0, NetworkFidelity.STUB}),
    "runtime": frozenset({RuntimeFidelity.R0, RuntimeFidelity.R1, RuntimeFidelity.STUB}),
}


def _check(axis: str, level: str) -> None:
    allowed = IMPLEMENTED[axis]
    if level not in allowed:
        listed = ", ".join(sorted(allowed))
        raise ValueError(
            f"fidelity: {axis} axis level {level!r} is not implemented in this prototype "
            f"(implemented: {listed}). Silent degradation to a cruder model is forbidden "
            f"— build-spec §2.4."
        )


class FidelityMap(BaseModel):
    """The C/M/N/R level a run asks for. Anything unimplemented fails loudly, by axis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    compute: ComputeFidelity
    memory: MemoryFidelity
    network: NetworkFidelity
    runtime: RuntimeFidelity

    @model_validator(mode="after")
    def _levels_are_implemented(self) -> FidelityMap:
        _check("compute", self.compute)
        _check("memory", self.memory)
        _check("network", self.network)
        _check("runtime", self.runtime)
        return self


class FidelityOverride(BaseModel):
    """One component instance's answer to "how much may you claim about me?".

    Every axis is optional: an unset axis falls through to `SystemConfig.fidelity`, which
    is the run's default rather than its only answer (ADR 0011 §1). The engine has always
    dispatched per component and `RunResult.fidelity_map` has always reported per
    component; before this, only the *input* was system-wide, so the Fidelity Map panel
    would have rendered a constant as a per-component fact.

    The same `IMPLEMENTED` gate applies here as to `FidelityMap` — one rule, called twice,
    never reimplemented. In practice that leaves two live choices per axis today: the
    implemented level, or STUB. STUB is not a degenerate option; it is a user saying
    "claim nothing about this part", which is the honest answer for a component whose
    numbers we could not source.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    compute: ComputeFidelity | None = None
    memory: MemoryFidelity | None = None
    network: NetworkFidelity | None = None
    runtime: RuntimeFidelity | None = None

    @model_validator(mode="after")
    def _levels_are_implemented(self) -> FidelityOverride:
        for axis in ("compute", "memory", "network", "runtime"):
            level = getattr(self, axis)
            if level is not None:
                _check(axis, level)
        return self

    @model_validator(mode="after")
    def _overrides_something(self) -> FidelityOverride:
        """An all-unset override is the F5 shape: accepted, doing nothing, announcing nothing.

        It is indistinguishable in effect from no override at all, so it can only mislead
        a reader of the config into thinking a component was deliberately pinned. Omit the
        field instead — that says the same thing and says it honestly.
        """
        if all(
            getattr(self, axis) is None
            for axis in ("compute", "memory", "network", "runtime")
        ):
            raise ValueError(
                "fidelity override sets no axis. An override that overrides nothing is "
                "the same as no override, so it states an intent the run does not carry "
                "— omit the field."
            )
        return self


def effective_fidelity(
    default: FidelityMap, override: FidelityOverride | None
) -> FidelityMap:
    """The levels a component actually runs at: its override where set, the default elsewhere.

    One function, so "effective" means the same thing to the registry, the dispatch, the
    fidelity map and the API. Two implementations of this would be two answers to the
    question the whole change exists to make askable per component.
    """
    if override is None:
        return default
    return FidelityMap(
        compute=override.compute if override.compute is not None else default.compute,
        memory=override.memory if override.memory is not None else default.memory,
        network=override.network if override.network is not None else default.network,
        runtime=override.runtime if override.runtime is not None else default.runtime,
    )
