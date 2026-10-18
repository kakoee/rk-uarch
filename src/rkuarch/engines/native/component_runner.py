"""Installed /3 transport and saved-result consumption; authority is never caller supplied."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256, strict_json_loads
from uarch_contract.mapped import MappedEngineJob, MappedEngineResult, validate_result

from .component_host import ComponentSession, _PreparedComponent, loads_runtime_job
from .component_records import CHECKER, OBSERVATIONS
from .host import _read
from .runner import (
    Limits,
    NativeRefusal,
    OperationalFailure,
    ProtocolViolation,
    _decode_envelope,
    _exchange,
)


def require_route(job: dict[str, Any], result: dict[str, Any]) -> None:
    """Select checker from the admitted job model before consuming any output evidence."""
    model = job.get("engine", {}).get("model", {})
    if (model.get("name"), model.get("version")) != ("native-intervals", "2") or result.get(
        "observations", {}
    ).get("format") != OBSERVATIONS:
        raise ProtocolViolation("component model/observation/checker route mismatch")


def validate_component_response(
    stdout: bytes,
    stderr: bytes,
    returncode: int,
    *,
    job: dict[str, Any],
    observation_contract: dict[str, Any],
) -> MappedEngineResult:
    """Pure replay validator, never authorization or a process-launch path."""
    from validation.component.observations_v3 import check_v3

    checked = loads_runtime_job(
        canonical_json(job),
        trusted_registry_hash=job["registry"]["registry_hash"],
        trusted_profile_hash=job["admission"]["profile_hash"],
        expected_engine=MappedEngineJob.model_validate(job).engine,
    )
    if checked.profile is None or checked.profile.format != "uarch-native-test-profile/2":
        raise ProtocolViolation("component profile/2 required")
    value = _decode_envelope(stdout, stderr, returncode)
    if returncode == 2:
        raise NativeRefusal(value)
    require_route(job, value)
    result = validate_result(value, checked)
    check_v3(job, value, observation_contract)
    if canonical_json(result).encode() != stdout:
        raise ProtocolViolation("component normalized result changed bytes")
    return result


def _request(prepared: _PreparedComponent, saved: Path) -> tuple[bytes, dict[str, Any]]:
    prepared.refresh()
    cap = prepared.payload.budget.stdin_bytes
    with saved.open("rb") as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise OperationalFailure("StdinLimit")
    checked = prepared.job(raw)
    if canonical_json(checked).encode() != raw:
        raise ProtocolViolation("component canonical selected request required")
    return raw, checked.model_dump(mode="json")


def _consume(
    prepared: _PreparedComponent, request: dict[str, Any], stdout: bytes, stderr: bytes, status: int
) -> MappedEngineResult:
    prepared.refresh()
    expected = strict_json_loads(
        _read(prepared.root, prepared.payload.consumers.observation_contract)
    )
    result = validate_component_response(
        stdout, stderr, status, job=request, observation_contract=expected
    )
    from validation.component.runtime_checks import consume_case

    raw = canonical_json(request).encode()
    consume_case(
        request,
        result.model_dump(mode="json"),
        prepared.selection_rows[request["admission"]["case_id"]],
        checker_id=CHECKER,
        source=Path(prepared.payload.consumers.import_root),
        pins=prepared.consumer_pins,
        expected=expected,
        input_sha256=sha256(raw).split(":")[1],
        raw_input=raw,
    )
    prepared.refresh()
    return result


def _run_prepared(
    saved: Path, prepared: _PreparedComponent
) -> tuple[MappedEngineResult, dict[str, Any]]:
    """Private transport core. Tests use synthetic data; public APIs require ComponentSession."""
    request, job = _request(prepared, saved)
    b = prepared.payload.budget
    limits = Limits(b.timeout_s, b.stdin_bytes, b.stdout_bytes, b.stderr_bytes)
    with prepared.executable() as fd:
        stdout, stderr, status = _exchange(fd, request, limits)
    result = _consume(prepared, job, stdout, stderr, status)
    selected = next(x for x in prepared.payload.executables if x.mode == prepared.mode)
    return result, {
        "request_byte_hash": sha256(request),
        "stdout_byte_hash": sha256(stdout),
        "stderr_byte_hash": sha256(stderr),
        "exit_code": status,
        "executable_byte_hash": selected.executable.byte_hash,
        "runtime_payload_byte_hash": prepared.payload_file.byte_hash,
        "independent_checker": CHECKER,
        "limits": vars(limits),
    }


def run_component(
    saved: Path, *, session: ComponentSession
) -> tuple[MappedEngineResult, dict[str, Any]]:
    if not isinstance(session, ComponentSession):
        raise ValueError("independent component authority required")
    prepared = session.claim()
    result = _run_prepared(saved, prepared)
    session.check()
    return result


def replay_component(saved: Path, output: Path, *, session: ComponentSession) -> MappedEngineResult:
    """Saved-result replay still needs current exact authority/inputs and both consumers."""
    if not isinstance(session, ComponentSession):
        raise ValueError("independent component authority required")
    prepared = session.claim()
    _, job = _request(prepared, saved)
    with output.open("rb") as stream:
        raw = stream.read(prepared.payload.budget.stdout_bytes + 1)
    if len(raw) > prepared.payload.budget.stdout_bytes:
        raise OperationalFailure("StdoutLimit")
    result = _consume(prepared, job, raw, b"", 0)
    session.check()
    return result
