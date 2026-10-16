"""Private transport helpers only. No successful public MappedEngineJob execution."""

import os
from pathlib import Path

import pytest

from rkuarch.engines.native.runner import (
    Limits,
    OperationalFailure,
    ProtocolViolation,
    _decode_envelope,
    _exchange,
)


def helper(tmp_path: Path, body: str) -> int:
    path = tmp_path / "helper"
    path.write_text("#!/usr/bin/python3\n" + body)
    path.chmod(0o700)
    return os.open(path, os.O_RDONLY)


def test_concurrent_drain_and_stdin(tmp_path: Path) -> None:
    fd = helper(
        tmp_path,
        'import sys\nsys.stderr.buffer.write(b"e"*200000);sys.stderr.flush()\n'
        "b=sys.stdin.buffer.read();sys.stdout.buffer.write(b)\n",
    )
    try:
        stdout, stderr, status = _exchange(fd, b"x" * 200000, Limits(timeout_s=5))
        assert (stdout, stderr, status) == (b"x" * 200000, b"e" * 200000, 0)
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    "body,limits,reason",
    [
        ("import time\ntime.sleep(10)\n", Limits(timeout_s=0.05), "Timeout"),
        (
            'import sys\nsys.stdout.buffer.write(b"x"*10000)\n',
            Limits(stdout_bytes=100),
            "StdoutLimit",
        ),
        (
            'import sys\nsys.stderr.buffer.write(b"x"*10000)\n',
            Limits(stderr_bytes=100),
            "StderrLimit",
        ),
    ],
)
def test_limits_reap(tmp_path: Path, body: str, limits: Limits, reason: str) -> None:
    fd = helper(tmp_path, body)
    try:
        with pytest.raises(OperationalFailure, match=reason):
            _exchange(fd, b"", limits)
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    "stdout,stderr,status",
    [
        (b"{}", b"", 2),
        (b"", b"{}", 0),
        (b"{}\n", b"", 0),
        (b"{} {}", b"", 0),
        (b'{"x":1,"x":2}', b"", 0),
        (b"{}", b"", 17),
        (b"", b'{"code":"Unknown","message":"x","pointer":null}', 2),
        (b"", b'{"code":"InvalidJson","message":"x","pointer":null,"extra":1}', 2),
        (b"", b'{"code":"InvalidJson","message":1,"pointer":null}', 2),
    ],
)
def test_framing_is_not_semantic_refusal(stdout: bytes, stderr: bytes, status: int) -> None:
    with pytest.raises(ProtocolViolation):
        _decode_envelope(stdout, stderr, status)


def test_exact_refusal_envelope() -> None:
    result = _decode_envelope(b"", b'{"code":"InvalidJson","message":"bad JSON","pointer":null}', 2)
    assert result["code"] == "InvalidJson"
