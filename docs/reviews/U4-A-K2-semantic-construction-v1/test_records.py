"""Metadata shape/refusal controls only; dummy hashes never confer authority."""

import importlib.util
import json
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "proposal_record_models", PACKAGE / "record_models.py"
)
assert SPEC is not None and SPEC.loader is not None
MODELS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODELS)
H = "sha256:" + "1" * 64
FILE = dict(path="review/input.json", byte_hash=H)


def minimal_build():
    return dict(
        format="uarch-k2-build-inputs/1",
        source_commit="1" * 40,
        source_files=[dict(path="src/lib.rs", byte_hash=H, role="rust")],
        trust_hash=H,
        trust_file=FILE,
        tool_inputs_hash=H,
        tool_inputs_file=FILE,
        model_source_paths=["src/lib.rs"],
        model_inputs_hash=H,
        mode_configs=[dict(mode=m, cargo_args=[], rustflags=[]) for m in ("debug", "release")],
        generated_identity_output_paths=["generated/identity.rs"],
        permitted_environment={},
    )


def test_no_receipt_or_binary_in_build_inputs():
    raw = minimal_build()
    MODELS.BuildInputs.model_validate(raw)
    for name in ("binary_hash", "final_host_record_hash", "receipt_hash", "engine"):
        with pytest.raises(ValueError):
            MODELS.BuildInputs.model_validate(dict(raw, **{name: H}))
    with pytest.raises(ValueError):
        MODELS.BuildInputs.model_validate(dict(raw, generated_identity_output_paths=["src/lib.rs"]))
    with pytest.raises(ValueError):
        MODELS.BuildInputs.model_validate(dict(raw, mode_configs=[raw["mode_configs"][0]] * 2))


def test_no_engine_in_profile_or_build_trust_schema():
    for model in (MODELS.ProfileBinding, MODELS.BuildTrust):
        props = model.model_json_schema()["properties"]
        assert not {"engine", "job_hash", "binary_hash", "host_record_hash"} & props.keys()
        assert model.model_json_schema()["additionalProperties"] is False


def test_host_record_requires_both_binaries_and_external_selector():
    props = MODELS.HostRecord.model_json_schema()["properties"]
    assert props["executables"]["minItems"] == props["executables"]["maxItems"] == 2
    assert "acceptance_commit" not in props  # commit containing this record is external
    assert "acceptance_commit" in MODELS.HostSelector.model_json_schema()["properties"]
    with pytest.raises(ValueError):
        MODELS.HostRecord.model_validate({})
    with pytest.raises(ValueError):
        MODELS.FileBinding.model_validate(dict(FILE, path="../caller.json"))


def test_metadata_mirrors(tmp_path):
    MODELS.schemas(tmp_path)
    for model in MODELS.ROOTS:
        name = model.__name__ + ".json"
        assert json.loads((tmp_path / name).read_text()) == json.loads(
            (PACKAGE / "record-schemas" / name).read_text()
        )
