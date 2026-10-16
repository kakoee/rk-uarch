"""One-request subprocess boundary. Public launch requires independent host authority."""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256, strict_json_loads
from uarch_contract.mapped import MappedEngineJob, MappedEngineResult, validate_result

from rkuarch.workload.mapped import loads_fixed_delay_job


# Operational resource limits; not simulation performance or qualification budgets.
@dataclass(frozen=True)
class Limits:
    timeout_s: float = 30.0
    stdin_bytes: int = 64 * 1024 * 1024
    stdout_bytes: int = 64 * 1024 * 1024
    stderr_bytes: int = 1024 * 1024

    def __post_init__(self) -> None:
        import math

        if not math.isfinite(self.timeout_s) or self.timeout_s <= 0:
            raise ValueError("positive finite timeout required")
        for n in (self.stdin_bytes, self.stdout_bytes, self.stderr_bytes):
            if type(n) is not int or n <= 0:
                raise ValueError("positive integer byte limits required")


class OperationalFailure(RuntimeError):
    """Spawn/IO/signal/timeout/cap failure, never a semantic refusal."""


class ProtocolViolation(ValueError):
    pass


class NativeRefusal(ValueError):
    def __init__(self, envelope: dict[str, Any]):
        self.envelope = envelope
        super().__init__(f"{envelope['code']}: {envelope['message']}")


REFUSAL_CODES = frozenset(
    {
        "InvalidJson",
        "InvalidCarrier",
        "UnsupportedProtocol",
        "UnsupportedCheckpointScope",
        "UnsupportedScope",
        "UnsupportedFidelity",
        "UnsupportedPrecision",
        "UnsupportedWorkloadScope",
        "UnsupportedInitialState",
        "UnsupportedFrequency",
        "ContentHashMismatch",
        "HardwareMismatch",
        "AdmissionMismatch",
        "InvalidDependency",
        "InvalidResource",
        "MissingCoverage",
        "TestProfileMismatch",
        "TestVariantNotAdmitted",
        "RegistryTrustMismatch",
        "EngineIdentityMismatch",
        "CapacityExceeded",
        "TimeOverflow",
    }
)


def _decode_envelope(stdout: bytes, stderr: bytes, returncode: int) -> dict[str, Any]:
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
            or value["code"] not in REFUSAL_CODES
            or type(value["message"]) is not str
            or (value["pointer"] is not None and type(value["pointer"]) is not str)
        ):
            raise ValueError("invalid refusal fields/code")
    except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise ProtocolViolation("invalid complete canonical envelope") from exc
    return value


def _exchange(executable_fd: int, request: bytes, limits: Limits) -> tuple[bytes, bytes, int]:
    """Linux descriptor execution binds the verified inode; concurrent bounded IO.

    Private transport helper tests use ordinary tiny programs, never mapped jobs.
    The fd comes from host validation in public launch, not the workload or PATH.
    """
    if len(request) > limits.stdin_bytes:
        raise OperationalFailure("StdinLimit")
    with tempfile.TemporaryDirectory(prefix="rkuarch-native-") as cwd:
        try:
            process = subprocess.Popen(
                [f"/proc/self/fd/{executable_fd}", "--protocol", "uarch-engine/3"],
                executable=f"/proc/self/fd/{executable_fd}",
                pass_fds=(executable_fd,),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                shell=False,
                start_new_session=True,
            )
        except OSError as exc:
            raise OperationalFailure("SpawnFailure") from exc
        assert process.stdin and process.stdout and process.stderr
        streams = (process.stdin, process.stdout, process.stderr)
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        caps = {"stdout": limits.stdout_bytes, "stderr": limits.stderr_bytes}
        deadline = time.monotonic() + limits.timeout_s
        sent = 0
        try:
            with selectors.DefaultSelector() as selector:
                for stream in streams:
                    os.set_blocking(stream.fileno(), False)
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                if request:
                    selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
                else:
                    process.stdin.close()
                while selector.get_map():
                    left = deadline - time.monotonic()
                    if left <= 0:
                        raise OperationalFailure("Timeout")
                    for key, _ in selector.select(left):
                        if key.data == "stdin":
                            try:
                                sent += os.write(key.fd, request[sent : sent + 65536])
                            except BrokenPipeError:
                                sent = len(request)
                            if sent == len(request):
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            chunk = os.read(
                                key.fd, min(65536, caps[key.data] - len(buffers[key.data]) + 1)
                            )
                            if not chunk:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            else:
                                buffers[key.data].extend(chunk)
                                if len(buffers[key.data]) > caps[key.data]:
                                    raise OperationalFailure(key.data.capitalize() + "Limit")
                try:
                    status = process.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired as exc:
                    raise OperationalFailure("Timeout") from exc
                return bytes(buffers["stdout"]), bytes(buffers["stderr"]), status
        except OSError as exc:
            raise OperationalFailure("PipeFailure") from exc
        finally:
            # Reap the launched child on every outcome; kill its process group on
            # failure, including descendants retaining a pipe after child exit.
            if process.poll() is None or any(not stream.closed for stream in streams):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            for stream in streams:
                stream.close()


def encode_request(job: object, *, host: Any) -> bytes:
    from .host import AcceptedHostBinding

    if not isinstance(host, AcceptedHostBinding):
        raise ValueError("independent AcceptedHostBinding required")
    raw = job.model_dump(mode="json") if isinstance(job, MappedEngineJob) else job
    # Freshly validate nested mutable containers, using separately supplied trust.
    encoded = canonical_json(raw).encode()
    checked = loads_fixed_delay_job(encoded, **host.authority_for(raw))
    host.require_job(checked)
    return canonical_json(checked).encode()


def parse_response(
    stdout: bytes, stderr: bytes, returncode: int, *, request_bytes: bytes, host: Any
) -> MappedEngineResult:
    request = strict_json_loads(request_bytes)
    if encode_request(request, host=host) != request_bytes:
        raise ProtocolViolation("noncanonical request receipt")
    job = loads_fixed_delay_job(request_bytes, **host.authority_for(request))
    value = _decode_envelope(stdout, stderr, returncode)
    if returncode == 2:
        raise NativeRefusal(value)
    try:
        result = validate_result(value, job)
        if canonical_json(result).encode() != stdout:
            raise ValueError("normalized result changed bytes")
    except (ValueError, TypeError) as exc:
        raise ProtocolViolation("result validation failed") from exc
    return result


def run_fixed_delay(
    saved: Path, *, host: Any, limits: Limits | None = None
) -> tuple[MappedEngineResult, dict[str, Any]]:
    limits = Limits() if limits is None else limits
    with saved.open("rb") as stream:
        raw = stream.read(limits.stdin_bytes + 1)
    if len(raw) > limits.stdin_bytes:
        raise OperationalFailure("StdinLimit")
    request = encode_request(strict_json_loads(raw), host=host)
    with host.open_executable() as executable_fd:
        stdout, stderr, status = _exchange(executable_fd, request, limits)
    result = parse_response(stdout, stderr, status, request_bytes=request, host=host)
    return result, {
        "request_byte_hash": sha256(request),
        "stdout_byte_hash": sha256(stdout),
        "stderr_byte_hash": sha256(stderr),
        "exit_code": status,
        "executable_byte_hash": host.executable.byte_hash,
        "host_record_byte_hash": host.selector.record_byte_hash,
        "limits": vars(limits),
    }
