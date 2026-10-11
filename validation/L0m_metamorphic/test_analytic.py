"""Hardware transformations hold prepared work fixed; frontend checks are separate."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from uarch_contract.hashing import canonical_json

from rkuarch.engines.analytic.core import run_analytic
from validation.analytic_checks import check_bandwidth_response
from validation.strategies import (
    MODES,
    bounded,
    fixed_bundle,
    hardware_specs,
    jobs,
    replace_hardware_leaf,
)


@pytest.mark.parametrize("mode", MODES)
@bounded
@given(hardware=hardware_specs())
def test_dram_bandwidth_monotone(mode, hardware):
    faster = replace_hardware_leaf(
        hardware, "memory.dram.bw_bytes_per_s", hardware.memory.dram.bw_bytes_per_s.value * 2
    )
    low, high = fixed_bundle(mode, hardware), fixed_bundle(mode, faster)
    assert low.bundle_hash != high.bundle_hash
    assert low.points == high.points  # no hidden re-preparation
    for first, second in zip(jobs(low), jobs(high), strict=True):
        a, b = run_analytic(first), run_analytic(second)
        assert a.counts == b.counts
        assert b.duration_ps <= a.duration_ps


@pytest.mark.parametrize("mode", MODES)
@bounded
@given(hardware=hardware_specs(memory_bound=True))
def test_memory_bound_bandwidth_response(mode, hardware):
    check_bandwidth_response(run_analytic, fixed_bundle(mode, hardware))


@bounded
@given(hardware=hardware_specs(), factor=st.integers(2, 4))
def test_aggregate_compute_bound_clock_scaling(hardware, factor):
    # Aggregate must remain compute-bound after scaling; individual embedding ops
    # are memory-only, so this exact relation is not asserted for per_op mode.
    hardware = replace_hardware_leaf(hardware, "memory.dram.bw_bytes_per_s", 1e18)
    faster = replace_hardware_leaf(
        hardware, "clock_domains.core.freq_hz", hardware.clock_domains.core.freq_hz.value * factor
    )
    low, high = fixed_bundle("aggregate", hardware), fixed_bundle("aggregate", faster)
    assert low.points == high.points
    for first, second in zip(jobs(low), jobs(high), strict=True):
        a, b = run_analytic(first), run_analytic(second)
        assert sum(o.compute_time_ps for o in b.per_op) > sum(
            o.memory_time_ps for o in b.per_op
        )
        assert b.duration_ps == pytest.approx(a.duration_ps / factor, rel=1e-9, abs=0)
        assert a.counts == b.counts


@bounded
@given(hardware=hardware_specs())
def test_modes_preserve_work_and_per_op_is_no_faster(hardware):
    for first, second in zip(
        jobs(fixed_bundle("aggregate", hardware)),
        jobs(fixed_bundle("per_op", hardware)),
        strict=True,
    ):
        a, b = run_analytic(first), run_analytic(second)
        assert a.counts == b.counts
        assert canonical_json(a.model_dump(mode="json")["per_op"]) == canonical_json(
            b.model_dump(mode="json")["per_op"]
        )
        assert b.duration_ps >= a.duration_ps
