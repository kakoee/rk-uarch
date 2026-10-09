"""Independent accepted literals; these tests precede any U2 producer implementation."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError
from uarch_contract.hashing import content_hash, strict_json_loads, verify_identity
from uarch_contract.prepared import PreparedBundle
from uarch_contract.request import CharacterizationRequest

from rkuarch.engines.protocol import EngineJob, EngineResult

FIXTURES = Path(__file__).parent / "fixtures/u2"


def literal(name):
    return json.loads((FIXTURES / name).read_text())


def test_independent_two_point_bundle_and_counts():
    bundle = PreparedBundle.model_validate(literal("independent-bundle.json"))
    assert len(bundle.points) == 2
    assert bundle.rank.tp == 1
    result = EngineResult.model_validate(literal("engine-result.json"))
    assert result.counts.matrix_ops == 1184
    assert result.counts.vector_ops == 572
    assert result.counts.memory_read_bytes == 1296
    assert result.counts.memory_write_bytes == 288
    assert result.duration_ps == 1892000
    assert sum(op.instances for op in result.per_op) == 31
    EngineJob.model_validate(literal("engine-job.json"))
    CharacterizationRequest.model_validate(literal("request.json"))


@pytest.mark.parametrize(
    "version", ["uarch-contract/0.1", "uarch-contract/0.3", "uarch-contract/1.0"]
)
def test_current_request_refuses_other_versions(version):
    data = literal("request.json")
    data["contract"] = version
    with pytest.raises(ValidationError):
        CharacterizationRequest.model_validate(data)


@pytest.mark.parametrize("bad", [True, "1", 1.5, 0])
def test_rank_integer_is_json_integer(bad):
    data = literal("independent-bundle.json")
    data["rank"]["tp"] = bad
    with pytest.raises(ValidationError):
        PreparedBundle.model_validate(data)


def test_unknown_fields_and_required_null():
    data = literal("engine-result.json")
    data["unknown"] = 0
    with pytest.raises(ValidationError):
        EngineResult.model_validate(data)
    del data["unknown"]
    del data["trace"]
    with pytest.raises(ValidationError):
        EngineResult.model_validate(data)


def test_hash_excludes_only_self_and_retains_nested_identity():
    data = literal("independent-bundle.json")
    assert verify_identity(data, "bundle_hash") == data["bundle_hash"]
    changed = deepcopy(data)
    changed["producer"]["version"] += "-changed"
    assert content_hash(changed, exclude=("bundle_hash",)) != data["bundle_hash"]
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        verify_identity(changed, "bundle_hash")
    changed = deepcopy(data)
    changed["points"][0]["payload_hash"] = "sha256:" + "0" * 64
    assert content_hash(changed, exclude=("bundle_hash",)) != data["bundle_hash"]


def test_duplicate_json_keys_and_nonfinite_refused():
    for text in ['{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}']:
        with pytest.raises(ValueError):
            strict_json_loads(text)


def test_bundle_verifier_checks_structure_beyond_hashes():
    from uarch_contract.prepared import validate_prepared_bundle

    data = literal("independent-bundle.json")
    validate_prepared_bundle(data)
    data["rank"]["rank_index"] = 1
    data["bundle_hash"] = content_hash(data, exclude=("bundle_hash",))
    with pytest.raises(ValueError, match="UnsupportedRankScope"):
        validate_prepared_bundle(data)


def test_engine_arithmetic_verifier_rejects_rehashed_wrong_count():
    from rkuarch.engines.protocol import validate_engine_result

    result = literal("engine-result.json")
    job = literal("engine-job.json")
    validate_engine_result(result, job)
    result["counts"]["matrix_ops"] += 1
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    with pytest.raises(ValueError, match="counts"):
        validate_engine_result(result, job)


@pytest.mark.parametrize("case", literal("negative-cases.json"), ids=lambda c: c["id"])
def test_accepted_prepared_negative_cases(case):
    from uarch_contract.hashing import resolve_pointer
    from uarch_contract.prepared import validate_prepared_bundle

    data = literal(case["base"])
    edit = case["replace"]
    parent, key = edit["path"].rsplit("/", 1)
    target = resolve_pointer(data, parent)
    target[int(key) if isinstance(target, list) else key] = edit["value"]
    if case["rehash_after_mutation"]:
        for point in data["points"]:
            point["payload_hash"] = content_hash(point, exclude=("payload_hash",))
        data["intent_hash"] = content_hash(data["intent"])
        data["bundle_hash"] = content_hash(data, exclude=("bundle_hash",))
    with pytest.raises(ValueError, match=case["expected_error"]):
        validate_prepared_bundle(data)


def test_job_binds_request_and_original_captured_producer():
    from rkuarch.engines.protocol import validate_engine_job

    job = literal("engine-job.json")
    validate_engine_job(job, literal("independent-bundle.json"), literal("request.json"))
    job["producer"]["version"] += "-mutated"
    job["job_hash"] = content_hash(job, exclude=("job_hash",))
    with pytest.raises(ValueError, match="producer"):
        validate_engine_job(job, literal("independent-bundle.json"), literal("request.json"))


def test_complete_job_identity_closure_refuses_deep_source_tampering():
    from uarch_contract.hashing import artifact_identity, verify_declared_artifact_closure

    assumptions = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/reviews/U2-U0003-proposal/fixtures/assumptions.json"
        ).read_text()
    )
    values = [literal("engine-job.json"), literal("independent-bundle.json"), assumptions]
    store = {artifact_identity(value): value for value in values}
    identity = values[0]["job_hash"]
    assert len(verify_declared_artifact_closure(identity, store)) == 3
    assumptions["limitations"].append("Tampered")
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        verify_declared_artifact_closure(identity, store)


def test_nominal_identity_is_not_a_production_engine_selector():
    data = literal("engine-job.json")
    data["engine"]["model"]["name"] = "nominal-rk-compatibility"
    with pytest.raises(ValueError, match="not a production engine"):
        EngineJob.model_validate(data)
