"""Unobservable U-P6 relations must be visible skips, never vacuous passes."""

import pytest

from validation.strategies import MODES

UNOBSERVABLE = {
    "executed_mac_conservation": "U2 reports shape-derived matrix_ops, not executed MAC telemetry",
    "dma_conservation": "No DMA traffic/compute-consumption boundary observations in U-C0",
    "window_utilisation": "No resource busy windows; analytic busy_time_ps is null",
    "little_law": "No queues, occupancy, arrivals or residence times in U-C0",
    "causality": "EngineResult.trace is None; dependency validation is not timed causality",
    "sram_placement": "No placement or per-event SRAM occupancy in analytic_ops",
    "energy_conservation": "No energy observation in EngineResult; energy remains unverified",
    "noc_sram_bandwidth": "NoC and SRAM bandwidth are unrepresented by U-C0",
    "core_permutation": "No core IDs or mapping placement in analytic_ops",
    "idle_core": "No mapped idle-core set; all spec cores contribute to resolved peak",
    "unused_stipulation": "Deferred: generated reference fixtures contain only stub claims",
    "latency_monotonicity": "Router/DRAM/job/barrier latency is unrepresented by U-C0",
    "dma_outstanding": "DMA max_outstanding is unrepresented by U-C0",
    "cold_steady": "stateless_roofline models neither cold startup nor steady-state history",
}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("relation", UNOBSERVABLE)
def test_unobservable_or_deferred_relation(mode, relation):
    pytest.skip(f"analytic/{mode}: {relation}: {UNOBSERVABLE[relation]}")


def test_per_op_exact_clock_precondition():
    pytest.skip("analytic/per_op: memory-only embedding violates whole-query compute-bound premise")
