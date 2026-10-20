"""Bounded EOF subprocess I/O for ordinary execution."""
from __future__ import annotations

import os
import selectors
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from uarch_contract.hashing import canonical_json, strict_json_loads


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
        "InvalidRoute",
        "InvalidCoverage",
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


def _decode_envelope(stdout: bytes, stderr: bytes, returncode: int, *,
                     codes: frozenset[str] = REFUSAL_CODES) -> dict[str, Any]:
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
            or value["code"] not in codes
            or type(value["message"]) is not str
            or (value["pointer"] is not None and type(value["pointer"]) is not str)
        ):
            raise ValueError("invalid refusal fields/code")
    except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise ProtocolViolation("invalid complete canonical envelope") from exc
    return value


def _exchange(
    executable_fd: int, request: bytes, limits: Limits, *,
    protocol: str = "uarch-engine/4", test_only: bool = False,
) -> tuple[bytes, bytes, int]:
    """Concurrent bounded I/O; execute the selected descriptor and reap its process group."""
    if len(request) > limits.stdin_bytes:
        raise OperationalFailure("StdinLimit")
    with tempfile.TemporaryDirectory(prefix="rkuarch-native-") as cwd:
        try:
            process = subprocess.Popen(
                [f"/proc/self/fd/{executable_fd}", "--protocol", protocol]
                + (["--test-only"] if test_only else []),
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
        read_streams = {"stdout": process.stdout, "stderr": process.stderr}
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
                                process.stdin.close()
                        else:
                            chunk = os.read(
                                key.fd, min(65536, caps[key.data] - len(buffers[key.data]) + 1)
                            )
                            if not chunk:
                                selector.unregister(key.fileobj)
                                read_streams[key.data].close()
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
