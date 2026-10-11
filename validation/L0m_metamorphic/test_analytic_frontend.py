"""Producer-path relations: separate from engine invariants on fixed imported work."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from uarch_contract.request import RequestIntent

from rkuarch.engines.analytic.core import run_analytic
from rkuarch.workload.prepare import prepare
from validation.strategies import MODES, bounded, fixed_bundle, hardware_specs, jobs


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("axis", ("batch", "context"))
@bounded
@given(hardware=hardware_specs(), batch=st.integers(1, 8), context=st.integers(1, 64))
def test_standalone_decode_monotone(mode, axis, hardware, batch, context):
    base = fixed_bundle(mode, hardware)

    def produce(b, t):
        raw = base.intent.model_dump(mode="json")
        raw["grid"]["decode"] = {"batch": [b], "context_per_seq": [t]}
        raw["envelope"]["decode"] = {"batch_max": b, "context_per_seq_max": t}
        return prepare(RequestIntent.model_validate(raw), hardware)

    low = produce(batch, context)
    high = produce(batch * (2 if axis == "batch" else 1), context * (2 if axis == "context" else 1))
    a_job = next(j for j in jobs(low) if j.point.query.phase == "decode")
    b_job = next(j for j in jobs(high) if j.point.query.phase == "decode")
    assert a_job.point_hash != b_job.point_hash
    assert a_job.bundle_hash != b_job.bundle_hash
    a, b = run_analytic(a_job), run_analytic(b_job)
    assert b.duration_ps >= a.duration_ps
    assert b.counts.matrix_ops >= a.counts.matrix_ops
    assert b.counts.memory_read_bytes >= a.counts.memory_read_bytes
