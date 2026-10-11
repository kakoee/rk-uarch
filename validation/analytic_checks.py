"""Named relation assertions reused unchanged by controls and injected-fault engines."""

import math

from uarch_contract.hashing import canonical_json

from rkuarch.engines.analytic.core import run_analytic
from validation.strategies import fixed_bundle, jobs, replace_hardware_leaf

# Independent integer answer key for the committed synthetic d4 BF16 graph.
# Decode: existing literal U2 fixture; prefill: T=S=1 instead of decode T=17.
# Not executed-MAC telemetry, and not a full-workload physical accuracy claim.
COUNTS = {
    "decode": (1184, 572, 1296, 288),
    "prefill": (672, 252, 1040, 288),
}
FIELDS = ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes")


def check_counts(job, result):
    assert tuple(getattr(result.counts, f) for f in FIELDS) == COUNTS[job.point.query.phase], (
        "off_by_one_matrix: fixed prepared-work accounting"
    )


def check_attribution(result):
    assert math.isclose(
        math.fsum(result.attribution_ps.model_dump().values()),
        result.duration_ps,
        rel_tol=1e-9,
        abs_tol=0,
    ), "double_attribution: critical-path parts do not sum to duration"


def check_nulls(result):
    assert all(
        v is None
        for v in (
            *result.diagnostics.model_dump().values(),
            *result.busy_time_ps.model_dump().values(),
        )
    ), "zero_unmodelled_diagnostic: unmodelled must be null"
    assert result.trace is None and result.simulator_metrics is None


def check_determinism(engine, job):
    assert canonical_json(engine(job)) == canonical_json(engine(job)), (
        "nondeterministic_output: identical job must produce identical bytes"
    )


def check_bandwidth_response(engine, bundle):
    hardware = bundle.hardware_spec
    faster = replace_hardware_leaf(
        hardware, "memory.dram.bw_bytes_per_s", hardware.memory.dram.bw_bytes_per_s.value * 2
    )
    high = fixed_bundle(bundle.intent.analytic_mode, faster)
    assert bundle.points == high.points
    for first, second in zip(jobs(bundle), jobs(high), strict=True):
        # Establish the domain with the valid control, never from the mutant's
        # claim about which resource binds. Fixed-work integer checks are separate.
        control = run_analytic(second)
        assert all(o.memory_time_ps > o.compute_time_ps for o in control.per_op)
        a, b = engine(first), engine(second)
        assert a.counts == b.counts
        assert math.isclose(b.duration_ps, a.duration_ps / 2, rel_tol=1e-9, abs_tol=0), (
            "wrong_bandwidth_field: memory-bound bandwidth doubling must halve duration"
        )
