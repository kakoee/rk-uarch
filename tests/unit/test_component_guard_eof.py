"""Synthetic Docker protocol controls; no daemon or containers are used."""

import json
import os
import subprocess
from types import SimpleNamespace

import pytest

from native.tools import component_container_guard as guard


@pytest.mark.parametrize("overflow", [False, True])
def test_eof_inventory_and_exact_owned_cleanup(tmp_path, monkeypatch, overflow):
    existing, created = "a" * 64, "b" * 64
    calls = []
    payload = b"one finite input\n"
    (tmp_path / "stdin").write_bytes(payload)
    guard.save(
        tmp_path / "intent.json",
        dict(
            owner="synthetic",
            name="synthetic",
            args=[],
            timeout=5,
            cap=1024,
            stderr_cap=3,
            stdin=True,
        ),
    )
    monkeypatch.setattr(guard, "DOCKER", list(guard.DOCKER))

    def command(args):
        calls.append(args)
        if args[0] == "ps":
            return (existing + " running\n").encode()
        if args[0] == "create":
            assert "--interactive" in args
            assert (tmp_path / "pre-existing.json").exists()
            return created.encode()
        assert args[-1] == created
        if args[0] == "inspect":
            return json.dumps(
                [
                    dict(
                        Id=created,
                        Config={"Labels": {guard.LABEL: "synthetic"}},
                        State={"Running": overflow},
                    )
                ]
            ).encode()
        assert args[0] in ("kill", "rm")
        return b""

    def start(args, **kwargs):
        assert args[-4:] == ["start", "-a", "-i", created]
        assert kwargs["stdin"].read() == payload
        assert kwargs["stdin"].read() == b""  # Actual file EOF, no fixed-delay protocol.
        kwargs["stdout"].write(b"ok")
        kwargs["stdout"].flush()
        if overflow:
            kwargs["stderr"].write(b"four")
            kwargs["stderr"].flush()
        return SimpleNamespace(
            poll=lambda: None if overflow else 0, returncode=0, wait=lambda **kw: 0
        )

    monkeypatch.setattr(guard, "command", command)
    monkeypatch.setattr(guard.subprocess, "Popen", start)
    monkeypatch.setattr(
        guard.subprocess,
        "run",
        lambda args, **kw: subprocess.CompletedProcess(args, 1, b"", b"No such object"),
    )
    read_fd, write_fd = os.pipe()
    try:
        guard.guard(tmp_path, read_fd)
    finally:
        os.close(write_fd)
    receipt = json.loads((tmp_path / "cleanup.json").read_bytes())
    assert receipt["reason"] == ("output-limit" if overflow else "completed")
    assert receipt["exit_code"] == (None if overflow else 0)
    assert receipt["stopped"] is True and receipt["removed"] is True
    assert json.loads((tmp_path / "created.json").read_bytes()) == {
        "container_id": created,
        "owner": "synthetic",
    }
    assert json.loads((tmp_path / "pre-existing.json").read_bytes())["containers"] == [
        {"container_id": existing, "state": "running"}
    ]
    assert all(existing not in call for call in calls)
    assert ["rm", "-f", created] in calls
