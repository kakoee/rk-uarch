"""Input construction/admission only. Anchors here are synthetic, never human authority."""

import json

import pytest
from uarch_contract.mapped import MappedBundle, admit, validate_resources

from validation.component.corpus import ROOT, build, manifest


@pytest.fixture(scope="module")
def prospective():
    return build()


def test_exact_frozen_corpus():
    assert manifest() == json.loads((ROOT / "validation/component/cases.json").read_bytes())


def test_schema_resource_controls(prospective):
    for item in prospective["items"].values():
        b = MappedBundle.model_validate(item["bundle"])
        outcome = item["expected"]["outcome"]
        if outcome == "success":
            validate_resources(b, b.points[0])
            admit(
                item["bundle"],
                invocation="test",
                checkpoint="B",
                registry=prospective["registry"],
                profile=item["profile"],
                trusted_registry_hash=prospective["registry"]["registry_hash"],
                trusted_profile_hash=item["profile"]["profile_hash"],
            )
        else:
            # Negative profile denies admission before resource validation by installed design.
            # This is resource-validator evidence only, not a public native refusal pass.
            with pytest.raises(ValueError, match=outcome):
                validate_resources(b, b.points[0])
            with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
                admit(
                    item["bundle"],
                    invocation="test",
                    checkpoint="B",
                    registry=prospective["registry"],
                    profile=item["profile"],
                    trusted_registry_hash=prospective["registry"]["registry_hash"],
                    trusted_profile_hash=item["profile"]["profile_hash"],
                )


def test_no_engine_or_authority_in_prospective_manifest():
    for item in manifest()["cases"]:
        assert item["native_status"] == "not_run"
        assert all(
            item[x] is None for x in ("job_hash", "engine_identity", "authority", "build_identity")
        )
