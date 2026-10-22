"""Reference dispatch for ordinary installed execution/replay. No producer imports."""

from importlib.metadata import version

from uarch_contract.hashing import strict_json_loads
from uarch_contract.mapped import require
from uarch_contract.reference import ReferenceJob, ReferenceResult
from uarch_contract.reference_json import canonical_json

from rkuarch.verification.component.reference import check_reference

from .transport import NativeRefusal, ProtocolViolation, _decode_envelope


def load_reference_job(raw: bytes, *, test_only: bool = False) -> ReferenceJob:
    job = ReferenceJob.model_validate(strict_json_loads(raw))
    require((job.admission.invocation == "test") == test_only, "AdmissionMismatch")
    require(job.engine.package_version == version("rk-uarch"), "EngineIdentityMismatch")
    if canonical_json(job).encode() != raw:
        raise ProtocolViolation("canonical saved job required")
    return job


def consume_reference(
    stdout: bytes, stderr: bytes, status: int, *, job: ReferenceJob
) -> ReferenceResult:
    from .ordinary import CODES

    job = ReferenceJob.model_validate(job.model_dump(mode="json"))
    value = _decode_envelope(stdout, stderr, status, codes=CODES)
    if status == 2:
        raise NativeRefusal(value)
    result = ReferenceResult.model_validate(value)
    for key in ("job_hash", "bundle_hash", "point_hash", "engine"):
        require(getattr(result, key) == getattr(job, key), "ContentHashMismatch", key)
    check_reference(job.model_dump(mode="json"), value)
    if canonical_json(result).encode() != stdout:
        raise ProtocolViolation("canonical saved result required")
    return result
