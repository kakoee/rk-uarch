"""Independent literals and rehashed counterexamples; no oracle/count helper imports."""

from __future__ import annotations

import builtins
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.rotary_v2 import PreparedBundleV2

from rkuarch.engines.analytic.rotary_v2 import counts, engine_identity
from rkuarch.engines.protocol_v2 import EngineResultV2, validate_engine_job, validate_engine_result
from rkuarch.table.capture_v2 import capture, replay
from rkuarch.workload.prepared_v2 import physical_assumptions, validate_execution_bundle

CASES = runpy.run_path(str(Path("contract/tests/rotary_v2_cases.py")))


def active_bundle(mode="per_op"):
    b = CASES["examples"](mode)["bundle"]
    b["intent"]["assumptions_hash"] = physical_assumptions().assumptions_hash
    CASES["rehash"](b)
    return validate_execution_bundle(b)


@pytest.mark.parametrize("case", CASES["RUNTIME_REFUSALS"])
def test_rehashed_admission(case):
    validate_execution_bundle(CASES["examples"]()["bundle"])
    bad = CASES["runtime_counterexample"](case)
    PreparedBundleV2.model_validate(bad)  # syntax alone is not admission
    with pytest.raises(ValueError):
        validate_execution_bundle(bad)


@pytest.mark.parametrize("mode", ["per_op", "aggregate"])
def test_literal_full_counts_and_replay_without_producers(mode, monkeypatch):
    b = active_bundle(mode)
    c = capture(b, assumptions=physical_assumptions())
    assert [tuple(r.counts.model_dump().values()) for r in c.results] == [
        (1184, 632, 1352, 312),
        (672, 312, 1096, 312),
    ]
    assert c.request.prepared_input_hash == b.bundle_hash
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.endswith(("producer_v2", ".prepare")) or "coefficient_producer" in name:
            raise AssertionError("producer import during replay")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    assert replay(b, c.request, c.jobs, c.results, assumptions=c.assumptions) == c
    for result in c.results:
        assert all(v is None for v in result.diagnostics.model_dump().values())
        assert all(v is None for v in result.busy_time_ps.model_dump().values())
        assert result.trace is result.simulator_metrics is None
        assert "precision_conversion" not in result.unrepresented


@pytest.mark.parametrize(
    "dtype,r,b,s,repeat,q,k,read,write",
    [
        ("bf16", 4, 1, 1, 1, 40, 20, 56, 24),
        ("fp16", 4, 1, 1, 1, 40, 20, 56, 24),
        ("fp32", 4, 1, 1, 1, 24, 12, 80, 48),
        ("bf16", 2, 1, 1, 1, 20, 10, 40, 24),
        ("bf16", 4, 2, 3, 1, 240, 120, 336, 144),
        ("bf16", 4, 1, 1, 2, 80, 40, 112, 48),
    ],
)
def test_independent_rotary_count_literals(dtype, r, b, s, repeat, q, k, read, write):
    template = CASES["examples"]()["bundle"]["points"][0]["graph"]["groups"][1]["ops"]
    answers = []
    for target, heads in [("q", 2), ("k", 1)]:
        op = deepcopy(next(o for o in template if o["id"] == "rope_" + target))
        op["spec"]["dimensions"] = dict(B=b, H=heads, S=s, D=4, R=r, P=r // 2)
        for key in ("X", "Y"):
            op["spec"]["operands"][key]["dtype"] = dtype
        from uarch_contract.rotary_v2 import PreparedOpV2

        answers.append(counts(PreparedOpV2.model_validate(op), repeat, causal=False))
    assert [a["vector_ops"] for a in answers] == [q, k]
    assert sum(a["matrix_ops"] for a in answers) == 0
    assert sum(a["memory_read_bytes"] for a in answers) == read
    assert sum(a["memory_write_bytes"] for a in answers) == write


@pytest.mark.parametrize(
    "field",
    [
        "hardware",
        "rank",
        "coefficients",
        "request_hash",
        "assumptions_hash",
        "engine",
        "point",
        "bundle_hash",
        "point_hash",
        "producer",
        "precision",
        "fidelity_detail",
        "mode",
        "seed",
        "initial_state",
    ],
)
def test_rehashed_job_refuses_broken_join(field):
    c = capture(active_bundle(), assumptions=physical_assumptions())
    j = c.jobs[0].model_dump(mode="json")
    if field == "hardware":
        j[field]["matrix_peak_ops_per_s"] *= 2
    elif field == "rank":
        j[field]["rank_index"] = 1
    elif field == "coefficients":
        j[field]["cos_bits"][0][0] = "00000000"
        CASES["seal"](j[field], "coefficients_hash")
    elif field == "engine":
        j[field]["implementation_hash"] = "sha256:" + "1" * 64
    elif field == "producer":
        j[field]["version"] = "different"
    elif field == "precision":
        j[field] = dict(compute="fp32", kv_cache="fp32")
    elif field == "fidelity_detail":
        j[field]["compute"] = 1
    elif field == "mode":
        j[field] = "aggregate"
    elif field == "seed":
        j[field] += 1
    elif field == "initial_state":
        j[field] = "cold"
    elif field == "point":
        j[field]["graph"]["groups"][1]["repeat"] = 3
        CASES["seal"](j[field], "payload_hash")
        j["point_hash"] = j[field]["payload_hash"]
    else:
        j[field] = "sha256:" + "1" * 64
    CASES["seal"](j, "job_hash")
    validate_engine_job(c.jobs[0], c.bundle, c.request, assumptions=c.assumptions)
    with pytest.raises(ValueError):
        validate_engine_job(j, c.bundle, c.request, assumptions=c.assumptions)


@pytest.mark.parametrize("kind", ["counts", "missing", "duplicated", "scope", "timing", "null"])
def test_rehashed_result_cannot_invent_work(kind):
    c = capture(active_bundle(), assumptions=physical_assumptions())
    r = c.results[0].model_dump(mode="json")
    if kind == "counts":
        r["per_op"][0]["counts"]["vector_ops"] += 1
        r["counts"]["vector_ops"] += 1
    elif kind == "missing":
        r["per_op"].pop()
    elif kind == "duplicated":
        r["per_op"].append(deepcopy(r["per_op"][0]))
    elif kind == "scope":
        r["per_op"][0]["scope"]["op_class"] = "rotary_embedding"
    elif kind == "null":
        r["busy_time_ps"]["compute"] = 0.0
    else:
        r["duration_ps"] *= 2
    r = EngineResultV2.model_validate(r).model_dump(mode="json")
    CASES["seal"](r, "result_hash")
    validate_engine_result(c.results[0], c.jobs[0], c.bundle, c.request, assumptions=c.assumptions)
    with pytest.raises(ValueError):
        validate_engine_result(r, c.jobs[0], c.bundle, c.request, assumptions=c.assumptions)


def test_assumptions_and_version_refusal():
    c = capture(active_bundle(), assumptions=physical_assumptions())
    from rkuarch.engines.protocol import EngineJob
    from rkuarch.workload.prepared import physical_assumptions as v1_assumptions

    with pytest.raises(ValueError):
        EngineJob.model_validate(c.jobs[0].model_dump(mode="json"))
    with pytest.raises(ValueError):
        capture(c.bundle, assumptions=v1_assumptions())
    assert engine_identity().version == "resolved-ops/2"
    assert content_hash(c.request) == c.jobs[0].request_hash


@pytest.mark.parametrize("field", ["prepared_input_hash", "seed", "position_encoding"])
def test_request_intent_join_with_rehashed_job(field):
    c = capture(active_bundle(), assumptions=physical_assumptions())
    r = c.request.model_dump(mode="json")
    if field == "seed":
        r[field] += 1
    elif field == "position_encoding":
        r[field]["pairing"] = "split_halves"
    else:
        r[field] = "sha256:" + "1" * 64
    j = c.jobs[0].model_dump(mode="json")
    j["request_hash"] = content_hash(r)
    if field == "seed":
        j["seed"] = r["seed"]
    CASES["seal"](j, "job_hash")
    validate_engine_job(c.jobs[0], c.bundle, c.request, assumptions=c.assumptions)
    with pytest.raises(ValueError, match="reconstructed request"):
        validate_engine_job(j, c.bundle, r, assumptions=c.assumptions)


@pytest.mark.parametrize("case", ["v1", "missing_rotary", "changed_model", "changed_limitations"])
def test_active_assumptions_not_just_hash_correspondence(case):
    from uarch_contract.assumptions import AssumptionSet

    capture(active_bundle(), assumptions=physical_assumptions())
    b = active_bundle().model_dump(mode="json")
    a = physical_assumptions().model_dump(mode="json")
    if case == "v1":
        from rkuarch.workload.prepared import physical_assumptions as v1_assumptions

        a = v1_assumptions().model_dump(mode="json")
    elif case == "missing_rotary":
        a["algorithms"].pop("rotary")
    elif case == "changed_model":
        a["model"]["implementation_hash"] = "sha256:" + "1" * 64
    else:
        a["limitations"] = ["false completeness claim"]
    CASES["seal"](a, "assumptions_hash")
    b["intent"]["assumptions_hash"] = a["assumptions_hash"]
    CASES["rehash"](b)
    validate_execution_bundle(b)  # graph-valid; all input hashes now agree
    with pytest.raises(ValueError, match="AssumptionMismatch"):
        capture(b, assumptions=AssumptionSet.model_validate(a))
