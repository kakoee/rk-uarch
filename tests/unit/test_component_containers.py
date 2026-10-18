"""Bounded real Docker probes, synthetic sleep only; opt in to accepted offline image."""

import json
import os
import signal
import subprocess
import sys
import time

import pytest

from native.tools.component_container_guard import cleanup, run_container

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
pytestmark = pytest.mark.skipif(os.environ.get("U4_PRIVATE_DOCKER") != "1", reason="private Docker")
ARGS = [
    "--network",
    "none",
    "--read-only",
    "--cap-drop",
    "ALL",
    "--pids-limit",
    "16",
    "--memory",
    "64m",
    "--entrypoint",
    "/bin/sleep",
    IMAGE,
    "20",
]


def inspect_stopped(receipt):
    assert receipt["stopped"] is True
    assert receipt["removed"] is True
    assert receipt["container_id"]
    p = subprocess.run(["docker", "inspect", receipt["container_id"]], capture_output=True)
    assert p.returncode != 0 and any(
        m in p.stderr.lower() for m in (b"no such object", b"no such container")
    )


def test_deadline_stops_actual_container(tmp_path):
    receipt = run_container(tmp_path / "call", ARGS, timeout=0.6)
    assert receipt["reason"] == "deadline"
    inspect_stopped(receipt)
    assert receipt["pre_remove_state"]["Running"] is False


def test_native_exit_semantics(tmp_path):
    receipt = run_container(tmp_path / "call", [*ARGS[:-1], "0"], timeout=5)
    assert receipt["exit_code"] == 0 and receipt["reason"] == "completed"
    inspect_stopped(receipt)


@pytest.mark.parametrize("phase", ["created", "running"])
def test_worker_death_and_parent_cleanup(tmp_path, phase):
    call = tmp_path / "call"
    module = "from native.tools.component_container_guard import run_container;"
    code = module + f"run_container(__import__('pathlib').Path({str(call)!r}),{ARGS!r},timeout=20)"
    process = subprocess.Popen([sys.executable, "-c", code], start_new_session=True)
    try:
        until = time.monotonic() + 8
        while time.monotonic() < until:
            marker = call / ("created.json" if phase == "created" else "started.json")
            if marker.exists():
                break
            time.sleep(0.01)
        assert marker.exists()
        os.kill(process.pid, signal.SIGKILL)
        process.wait(timeout=3)
        receipt = cleanup(tmp_path, timeout=12)[0]
        assert receipt["reason"] in ("worker-exit", "cancelled")
        inspect_stopped(receipt)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        cleanup(tmp_path, timeout=12)


def test_parent_cancel_and_unrelated_container(tmp_path):
    # An independently created, exact control is removed only by this test's finally.
    control = subprocess.check_output(["docker", "create", *ARGS], text=True).strip()
    (tmp_path / "unrelated-control.id").write_text(control + "\n")
    subprocess.run(["docker", "start", control], check=True, capture_output=True)
    call = tmp_path / "call"
    code = (
        "from native.tools.component_container_guard import run_container;"
        f"run_container(__import__('pathlib').Path({str(call)!r}),{ARGS!r},timeout=20)"
    )
    process = subprocess.Popen([sys.executable, "-c", code])
    try:
        until = time.monotonic() + 8
        while not (call / "started.json").exists() and time.monotonic() < until:
            time.sleep(0.02)
        assert (call / "started.json").exists()
        inspect_stopped(cleanup(tmp_path, timeout=12)[0])
        state = json.loads(subprocess.check_output(["docker", "inspect", control]))[0]["State"]
        assert state["Running"] is True
        process.wait(timeout=3)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        try:
            cleanup(tmp_path, timeout=12)
        finally:
            subprocess.run(["docker", "rm", "-f", control], check=True, capture_output=True)
