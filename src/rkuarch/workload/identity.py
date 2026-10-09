"""Exact legacy ModelId projection from captured identities, without badge inference."""

from pathlib import Path

from uarch_contract.hashing import strict_json_loads
from uarch_contract.model_card import ModelId
from uarch_contract.model_shape import ModelShape, ModelSpec, check_parity
from uarch_contract.prepared import PreparedBundle
from uarch_contract.request import CharacterizationRequest

from rkuarch.engines.protocol import EngineJob, validate_engine_job


def legacy_model_id(job: EngineJob, bundle: PreparedBundle) -> ModelId:
    request = CharacterizationRequest(
        **bundle.intent.model_dump(mode="json"), prepared_input_hash=bundle.bundle_hash
    )
    validate_engine_job(job, bundle, request)
    return ModelId(
        engine=job.engine.name,
        engine_version=job.engine.version,
        fidelity_detail=job.fidelity_detail,
        mapping_policy=bundle.intent.mapping_policy,
    )


def load_model_shape(path: "Path") -> tuple["ModelSpec", "ModelShape"]:
    """Read a caller-selected local sourced sidecar; no network or expected-fixture lookup."""
    value = strict_json_loads(path.read_bytes())
    model = ModelSpec.model_validate(value["model"])
    shape = ModelShape.model_validate(value["shape"])
    check_parity(model, shape)
    return model, shape
