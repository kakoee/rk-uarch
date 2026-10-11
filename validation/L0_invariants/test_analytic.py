"""Bounded U-C0 checks on authenticated, fixed independent prepared work."""

import math

import pytest
from hypothesis import given
from uarch_contract.hashing import canonical_json, verify_identity

from rkuarch.engines.analytic.core import run_analytic
from rkuarch.engines.protocol import validate_engine_result
from validation.analytic_checks import (
    check_attribution,
    check_counts,
    check_determinism,
    check_nulls,
)
from validation.strategies import MODES, bounded, fixed_bundle, hardware_specs, jobs


@pytest.mark.parametrize("mode", MODES)
@bounded
@given(hardware=hardware_specs())
def test_fixed_work_invariants(mode, hardware):
    bundle = fixed_bundle(mode, hardware)
    for job in jobs(bundle):
        before = canonical_json(job)
        result = run_analytic(job)
        check_counts(job, result)
        check_attribution(result)
        check_nulls(result)
        check_determinism(run_analytic, job)
        validate_engine_result(result, job)
        verify_identity(result, "result_hash")
        assert canonical_json(job) == before
        assert result.duration_ps >= result.u_c0_duration_ps
        for field in type(result.counts).model_fields:
            assert getattr(result.counts, field) == math.fsum(
                getattr(op.counts, field) for op in result.per_op
            )


@pytest.mark.parametrize("mode", MODES)
def test_saved_replay_bypasses_producer_and_refuses_stale_identity(mode, tmp_path, monkeypatch):
    import rkuarch.workload.prepare as producer
    from rkuarch.workload.prepared import load_prepared_input

    bundle = fixed_bundle(mode)
    path = tmp_path / "prepared.json"
    path.write_text(canonical_json(bundle))

    def forbidden(*args, **kwargs):
        pytest.fail("saved replay called standalone producer")

    monkeypatch.setattr(producer, "prepare", forbidden)
    assert [canonical_json(run_analytic(j)) for j in jobs(load_prepared_input(path))] == [
        canonical_json(run_analytic(j)) for j in jobs(bundle)
    ]
    raw = bundle.model_dump(mode="json")
    raw["points"][0]["graph"]["groups"][1]["repeat"] += 1
    path.write_text(canonical_json(raw))
    with pytest.raises(ValueError, match="[Hh]ash|[Ii]dentity"):
        load_prepared_input(path)


@pytest.mark.parametrize("mode", MODES)
def test_rehashed_invalid_graph_is_refused_without_repreparation(mode, tmp_path, monkeypatch):
    from uarch_contract.hashing import content_hash

    import rkuarch.workload.prepare as producer
    from rkuarch.workload.prepared import load_prepared_input

    def forbidden(*args, **kwargs):
        pytest.fail("invalid imported graph was silently re-prepared")

    monkeypatch.setattr(producer, "prepare", forbidden)
    raw = fixed_bundle(mode).model_dump(mode="json")
    point = raw["points"][0]
    # Valid positive dimensions, but no longer the supplied model's q projection.
    point["graph"]["groups"][1]["ops"][1]["spec"]["dimensions"]["N"] += 1
    point["payload_hash"] = content_hash(point, exclude=("payload_hash",))
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    path = tmp_path / "invalid-but-rehashed.json"
    path.write_text(canonical_json(raw))
    with pytest.raises(ValueError, match="InvalidPreparedGraph"):
        load_prepared_input(path)
