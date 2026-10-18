"""Installed /3 transport and saved-result consumption; authority is never caller supplied."""

from __future__ import annotations

from pathlib import Path
from typing import Any, get_args

from uarch_contract.hashing import canonical_json, sha256, strict_json_loads
from uarch_contract.mapped import MappedEngineJob, MappedEngineResult, ProfileEntry, validate_result

from .component_host import ComponentSession, _PreparedComponent, loads_runtime_job
from .component_records import CHECKER, OBSERVATIONS
from .host import _read, _require
from .runner import (
    REFUSAL_CODES,
    Limits,
    NativeRefusal,
    OperationalFailure,
    ProtocolViolation,
    _exchange,
)

# Installed profile outcomes plus independent native structural admission refusals.
# The K2 decoder and its accepted code set remain unchanged.
_COMPONENT_CODES = (
    REFUSAL_CODES
    | frozenset(get_args(ProfileEntry.model_fields["expected_outcome"].annotation))
    | {
        "InvalidBank",
        "InvalidPreparedGraph",
        "UnexpectedClosure",
        "TestOnlyHardware",
    }
) - {"success"}


def _decode_envelope(stdout: bytes, stderr: bytes, returncode: int) -> dict[str, Any]:
    """Exact component framing; operational exits never become semantic refusals."""
    if returncode < 0 or returncode == 1:
        raise OperationalFailure(f"NativeExit:{returncode}")
    if returncode not in (0, 2) or (returncode == 0 and stderr) or (returncode == 2 and stdout):
        raise ProtocolViolation("status/stream mismatch")
    raw = stdout if returncode == 0 else stderr
    try:
        value = strict_json_loads(raw.decode("utf-8"))
        if not isinstance(value, dict) or canonical_json(value).encode() != raw:
            raise ValueError("noncanonical envelope")
        if returncode == 2 and (
            set(value) != {"code", "message", "pointer"}
            or type(value["code"]) is not str
            or value["code"] not in _COMPONENT_CODES
            or type(value["message"]) is not str
            or (value["pointer"] is not None and type(value["pointer"]) is not str)
        ):
            raise ValueError("invalid component refusal fields/code")
    except (ValueError, TypeError, UnicodeError, OverflowError) as error:
        raise ProtocolViolation("invalid complete canonical component envelope") from error
    return value


def require_negative_envelope(
    stdout: bytes, stderr: bytes, status: int, expected: dict[str, Any]
) -> dict[str, Any]:
    """Exact finite expectation from independent inventory; not a native-site proof."""
    _require(status == 2, "exact negative envelope requires status2")
    error = _decode_envelope(stdout, stderr, status)
    _require(error == expected, "exact negative envelope mismatch")
    return error


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
    # This is a consumer-layer check, independent of _request/prepared.job.
    selected = next(
        (item for item in prepared.payload.jobs if item.case_id == request["admission"]["case_id"]),
        None,
    )
    _require(selected is not None, "consumer selected case")
    _require(
        request["engine"] == prepared.payload.engine.model_dump(mode="json"),
        "consumer expected engine",
    )
    raw = canonical_json(request).encode()
    assert selected is not None
    _require(sha256(raw) == selected.file.byte_hash, "consumer selected raw bytes")
    expected = strict_json_loads(
        _read(prepared.root, prepared.payload.consumers.observation_contract)
    )
    result = validate_component_response(
        stdout, stderr, status, job=request, observation_contract=expected
    )
    from validation.component.runtime_checks import consume_case

    consume_case(
        request,
        result.model_dump(mode="json"),
        prepared.selection_rows[request["admission"]["case_id"]],
        checker_id=CHECKER,
        source=Path(prepared.payload.consumers.import_root),
        pins=prepared.consumer_pins,
        expected=expected,
        input_sha256=selected.file.byte_hash.split(":")[1],
        raw_input=raw,
        admitted={
            "case_id": selected.case_id,
            "raw_input_sha256": selected.file.byte_hash.split(":")[1],
            "job_hash": selected.job_hash,
            "engine": prepared.payload.engine.model_dump(mode="json"),
        },
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
