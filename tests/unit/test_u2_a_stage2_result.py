"""Independent aggregate algebra and captured-result U-C0 binding regressions."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from uarch_contract.hashing import content_hash

from rkuarch.engines.protocol import validate_engine_result
from tests.unit.test_u2_a_shapes import inputs, prepare, run


@pytest.mark.parametrize("mode", ["per_op", "aggregate"])
@pytest.mark.parametrize("bad", ["zero", "inflated", "wrong_aggregate"])
def test_rehashed_uc0_must_equal_max_of_sums(mode, bad):
    i, hw = inputs(analytic_mode=mode)
    bundle = prepare(i, hw)
    from rkuarch.workload.prepared import execute_prepared_point, physical_assumptions

    job, result = execute_prepared_point(
        bundle, bundle.points[0].payload_hash, assumptions=physical_assumptions()
    )
    assert result.u_c0_duration_ps == 1584000  # Independent hand-worked tiny fixture.
    assert validate_engine_result(result, job) == result
    replacement = {"zero": 0, "inflated": result.duration_ps * 2, "wrong_aggregate": 1500000}[bad]
    forged = result.model_copy(update={"u_c0_duration_ps": replacement})
    forged = forged.model_copy(
        update={"result_hash": content_hash(forged, exclude=("result_hash",))}
    )
    with pytest.raises(ValueError, match="EngineResultMismatch: u_c0_duration_ps"):
        validate_engine_result(forged, job)


@given(
    batch=st.integers(1, 8),
    context=st.integers(1, 64),
    length=st.integers(1, 48),
    frequency=st.sampled_from([0.37, 0.5, 1.0, 1.3]),
    cold=st.booleans(),
)
@settings(max_examples=25, deadline=None, derandomize=True)
def test_per_op_dominates_aggregate_with_attribution_conservation(
    batch, context, length, frequency, cold
):
    i, hw = inputs()
    raw = i.model_dump(mode="json")
    raw["grid"] = dict(
        decode=dict(batch=[batch], context_per_seq=[context]),
        prefill=dict(n=[1], L=[length]),
        frequency_ratio=[frequency],
    )
    raw["envelope"] = dict(
        decode=dict(batch_max=batch, context_per_seq_max=context),
        prefill=dict(prompt_tokens_max=length, prompts_per_iteration_max=1),
    )
    raw["initial_state"] = "cold" if cold else "steady"
    from uarch_contract.request import RequestIntent

    results = {}
    for mode in ("per_op", "aggregate"):
        raw["analytic_mode"] = mode
        b = prepare(RequestIntent.model_validate(raw), hw)
        results[mode] = [run(b, n) for n in range(len(b.points))]
    for per, agg in zip(results["per_op"], results["aggregate"], strict=True):
        # Independent algebra on captured components, not another call to core's reducer.
        expected = max(
            math.fsum(o.compute_time_ps for o in per.per_op),
            math.fsum(o.memory_time_ps for o in per.per_op),
        )
        assert math.isclose(agg.duration_ps, expected, rel_tol=1e-9, abs_tol=1e-3)
        assert math.isclose(per.u_c0_duration_ps, expected, rel_tol=1e-9, abs_tol=1e-3)
        assert per.duration_ps >= agg.duration_ps
        assert per.counts == agg.counts
        for result in (per, agg):
            assert math.isclose(
                math.fsum(result.attribution_ps.model_dump().values()),
                result.duration_ps,
                rel_tol=1e-9,
                abs_tol=1e-3,
            )


def test_subprocess_capture_rejects_rehashed_uc0(monkeypatch):
    import importlib
    from types import SimpleNamespace

    from uarch_contract.hashing import canonical_json, strict_json_loads

    from rkuarch.engines.analytic.core import run_analytic
    from rkuarch.engines.protocol import EngineJob
    from rkuarch.workload.prepared import physical_assumptions

    module = importlib.import_module("rkuarch.table.build")
    i, hw = inputs()
    bundle = prepare(i, hw)

    def forged_transport(*args, **kwargs):
        job = EngineJob.model_validate(strict_json_loads(kwargs["input"]))
        result = run_analytic(job).model_copy(update={"u_c0_duration_ps": 0.0})
        result = result.model_copy(
            update={"result_hash": content_hash(result, exclude=("result_hash",))}
        )
        return SimpleNamespace(returncode=0, stderr=b"", stdout=canonical_json(result).encode())

    monkeypatch.setattr(module.subprocess, "run", forged_transport)
    with pytest.raises(ValueError, match="EngineResultMismatch: u_c0_duration_ps"):
        module.capture(bundle, assumptions=physical_assumptions(), subprocess_engine=True)
