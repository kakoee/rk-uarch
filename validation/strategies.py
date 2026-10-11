"""Synthetic, bounded U2 inputs; never change committed hardware or oracle inputs."""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import settings
from hypothesis import strategies as st
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash, spec_hash
from uarch_contract.prepared import PreparedBundle

from rkuarch.workload.prepared import (
    physical_assumptions,
    prepare_engine_job,
    validate_execution_bundle,
)

MODES = ("aggregate", "per_op")
FIXTURE = Path(__file__).resolve().parents[1] / "contract/tests/fixtures/u2/independent-bundle.json"
bounded = settings(max_examples=24, deadline=None, derandomize=True, database=None)


def replace_hardware_leaf(spec: HardwareSpec, path: str, value: float) -> HardwareSpec:
    raw = spec.model_dump(mode="json")
    leaf = raw
    for part in path.split("."):
        leaf = leaf[part]
    # These are synthetic reference fixtures: unknown claims, never real source evidence.
    assert leaf["kind"] == "claim" and leaf["provenance"] == "stub" and leaf["source"] is None
    leaf["value"] = value
    return HardwareSpec.model_validate(raw)


@st.composite
def hardware_specs(draw, *, memory_bound=False):
    """Vary valid sourced rates, keeping BF16 geometry and capacity fixed.

    The small-bandwidth branch keeps every fixture operator memory-bound even
    after bandwidth doubles; this precondition is also asserted by the checker.
    """
    spec = HardwareSpec.model_validate(json.loads(FIXTURE.read_text())["hardware_spec"])
    values = {
        "clock_domains.core.freq_hz": draw(st.integers(1_000_000, 2_000_000_000)),
        "cores.core_type.matrix_engine.macs_per_cycle.bf16": draw(st.integers(1, 64)),
        "cores.core_type.vector_engine.ops_per_cycle": draw(st.integers(1, 64)),
        "memory.dram.bw_bytes_per_s": draw(
            st.integers(1_000, 10_000) if memory_bound else st.integers(1_000, 10**12)
        ),
    }
    for path, value in values.items():
        spec = replace_hardware_leaf(spec, path, value)
    return spec


def fixed_bundle(mode: str, hardware: HardwareSpec | None = None) -> PreparedBundle:
    """Rebind an independent fixed graph to current assumptions and synthetic hardware.

    Validate full content closure before execution, not just EngineJob's shape.
    Content authentication is not independent human review or physical correctness.
    """
    raw = json.loads(FIXTURE.read_text())
    if hardware is not None:
        raw["hardware_spec"] = hardware.model_dump(mode="json")
    raw["intent"]["hardware_spec_hash"] = spec_hash(
        HardwareSpec.model_validate(raw["hardware_spec"])
    )
    raw["intent"]["analytic_mode"] = mode
    raw["intent"]["assumptions_hash"] = physical_assumptions().assumptions_hash
    raw["intent_hash"] = content_hash(raw["intent"])
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    return validate_execution_bundle(raw)


def jobs(bundle: PreparedBundle):
    return tuple(
        prepare_engine_job(bundle, p.payload_hash, assumptions=physical_assumptions())
        for p in bundle.points
    )
