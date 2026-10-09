"""Complete five-channel physical/nominal observations; these are not oracle comparisons."""

import pytest

from contract.tests.test_u2_nominal_candidate import candidate, nominal_input
from tests.unit.test_u2_a_shapes import inputs, prepare, run


def test_independent_physical_nominal_discrepancies_remain_visible():
    i, hw = inputs()
    b = prepare(i, hw)
    actual = run(b)
    base = nominal_input().model_dump(mode="json")
    base.update(model=i.model.model_dump(), query=b.points[0].query.model_dump())
    base["selected_peak"]["value"] = 0.002
    base["bandwidth"]["value"] = 0.001
    base["execution_model"]["compute"]["value"] = 1.0
    nominal = candidate().evaluate_nominal(nominal_input(**base))
    # This synthetic hardware is 2 Gop/s and 1 GB/s, efficiency1.0.
    observed = {
        "matrix_ops": (actual.counts.matrix_ops, nominal.counts.matrix_ops),
        "vector_ops": (actual.counts.vector_ops, nominal.counts.vector_ops),
        "memory_read_bytes": (actual.counts.memory_read_bytes, nominal.counts.memory_read_bytes),
        "memory_write_bytes": (actual.counts.memory_write_bytes, nominal.counts.memory_write_bytes),
        "duration_s": (actual.duration_ps / 1e12, nominal.duration_s),
    }
    assert observed["matrix_ops"] == (1184, 1288)
    assert observed["vector_ops"] == (572, None)
    assert observed["memory_read_bytes"] == (1296, 1016)
    assert observed["memory_write_bytes"] == (288, None)
    assert observed["duration_s"] == pytest.approx((1.892e-6, 1.016e-6))
    # Retain the large discrepancy; never tune work or label absent reference channels passed.
    assert (observed["matrix_ops"][0] - 1288) / 1288 < -0.05
