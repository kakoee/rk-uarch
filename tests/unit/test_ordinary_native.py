"""Ordinary /4 contract and installed process boundary acceptance."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash

ROOT = Path(__file__).resolve().parents[2]


def job_data(name="synthetic-runtime-cc0-v3.json"):
    # Explicit development migration only; runtime never repairs/reinterprets /3.
    raw = json.loads((ROOT / "native/crates/uarch-engine/testdata" / name).read_text())
    raw["protocol"] = "uarch-engine/4"
    raw["engine"] = {
        "name": "native",
        "version": "native-stage/2",
        "package_version": "0.0.1",
        "model": {"name": "native-intervals", "version": "2"},
    }
    raw.pop("profile")
    raw.pop("registry")
    raw["admission"] = {"checkpoint": "B", "invocation": "test", "eligibility": "verification_only"}
    b = raw["workload_closure"]
    b["format"] = "uarch-prepared/4"
    b["admission"] = raw["admission"].copy()
    b["producer"].pop("implementation_hash")
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    raw["bundle_hash"] = b["bundle_hash"]
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    return raw


def test_versions_and_no_attestation():
    from uarch_contract.ordinary import OrdinaryJob

    raw = job_data()
    job = OrdinaryJob.model_validate(raw)
    assert job.engine.model.version == "2"
    for key in ("implementation_hash", "compiler_lock_hash", "profile_hash", "registry_hash"):
        assert key not in canonical_json(job)
    for field in ("profile", "registry"):
        bad = deepcopy(raw)
        bad[field] = {}
        bad["job_hash"] = content_hash(bad, exclude=("job_hash",))
        with pytest.raises(ValueError):
            OrdinaryJob.model_validate(bad)


def test_old_formats_are_explicitly_refused():
    from uarch_contract.ordinary import OrdinaryJob

    old = json.loads(
        (ROOT / "native/crates/uarch-engine/testdata/synthetic-runtime-cc0-v3.json").read_text()
    )
    with pytest.raises(ValueError):
        OrdinaryJob.model_validate(old)


@pytest.mark.parametrize(
    "field,value", [("version", "native-stage/1"), ("package_version", "0.0.0")]
)
def test_wrong_software_version(field, value):
    from uarch_contract.ordinary import OrdinaryJob

    raw = job_data()
    raw["engine"][field] = value
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    with pytest.raises(ValueError):
        OrdinaryJob.model_validate(raw)


def test_input_integrity():
    from uarch_contract.ordinary import OrdinaryJob

    raw = job_data()
    raw["seed"] += 1
    with pytest.raises(ValueError, match="[Hh]ash"):
        OrdinaryJob.model_validate(raw)


def production_data():
    from uarch_contract.ordinary import OrdinaryBundle

    from rkuarch.workload.ordinary import prepare_job

    b = json.loads((ROOT / "contract/fixtures/mapped/component.json").read_text())
    b["format"] = "uarch-prepared/4"
    b["producer"].pop("implementation_hash")
    b["admission"] = {
        "checkpoint": "B",
        "invocation": "production",
        "eligibility": "component_only",
    }
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    bundle = OrdinaryBundle.model_validate(b)
    return prepare_job(bundle, point_hash=bundle.points[0].payload_hash).model_dump(mode="json")


def test_production_preparation_and_explicit_fixture_mode():
    from rkuarch.engines.native.ordinary import load_job

    assert load_job(canonical_json(production_data()).encode()).admission.invocation == "production"
    raw = canonical_json(job_data()).encode()
    with pytest.raises(ValueError, match="AdmissionMismatch"):
        load_job(raw)
    assert load_job(raw, test_only=True).admission.eligibility == "verification_only"


def test_ordinary_schema_freshness():
    from uarch_contract.generate_ordinary import generate
    from uarch_contract.ordinary import OrdinaryJob

    assert generate(check=True) == []
    assert (
        json.loads((ROOT / "native/crates/uarch-engine/src/ordinary_carriers.json").read_text())
        == json.loads(json.dumps(OrdinaryJob.model_json_schema()))
    )


def test_production_capability_is_not_a_case_inventory():
    from uarch_contract.ordinary import OrdinaryJob

    raw = production_data()
    raw["seed"] = 901
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    assert OrdinaryJob.model_validate(raw).seed == 901
    raw["engine"]["model"]["version"] = "1"
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    with pytest.raises(ValueError):
        OrdinaryJob.model_validate(raw)


@pytest.mark.parametrize("status", [1, 2, 17, -9])
def test_nonzero_status_cannot_be_success(status):
    from uarch_contract.ordinary import OrdinaryJob

    from rkuarch.engines.native.ordinary import consume

    with pytest.raises((ValueError, RuntimeError)):
        consume(b"{}", b"", status, job=OrdinaryJob.model_validate(production_data()))


def hardware_variant(field, value):
    """Rebind actual input identities; the capability check must be load-bearing."""
    from uarch_contract.hardware import HardwareSpec
    from uarch_contract.hashing import spec_hash
    from uarch_contract.mapped import hardware_projection

    raw = job_data()
    bundle = raw["workload_closure"]
    spec = bundle["hardware_spec"]
    quantity = (spec["cores"]["core_type"]["job_overhead_cycles"]
                if field == "overhead" else spec["sync"]["barrier_latency_cycles"])
    quantity["value"] = value
    hardware = HardwareSpec.model_validate(spec)
    bundle["hardware_spec"] = hardware.model_dump(mode="json")
    bundle["hardware_spec_hash"] = raw["hardware_spec_hash"] = spec_hash(hardware)
    raw["hardware"] = hardware_projection(hardware).model_dump(mode="json")
    bundle["bundle_hash"] = content_hash(bundle, exclude=("bundle_hash",))
    raw["bundle_hash"] = bundle["bundle_hash"]
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    return raw


@pytest.mark.parametrize("field", ["overhead", "barrier"])
@pytest.mark.parametrize("value", [16, 32, 64])
def test_test_only_checker_capability(field, value):
    from rkuarch.engines.native.ordinary import load_job

    saved = canonical_json(hardware_variant(field, value)).encode()
    if value == 32:
        assert load_job(saved, test_only=True).admission.eligibility == "verification_only"
    else:
        with pytest.raises(ValueError, match="UnsupportedHardware"):
            load_job(saved, test_only=True)
