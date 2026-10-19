"""Private Docker lifecycle ownership. No K2 or public launch path.

A separate session watches a worker-held pipe. Worker death closes the pipe, but
cannot kill the guardian. Parent cleanup cancels registered intents, then waits for
verified receipts. A management failure is unresolved, never a stopped claim.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time
import uuid
from contextlib import ExitStack
from pathlib import Path
from typing import Any

DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
LABEL = "rk-uarch.private-owner"


def save(path: Path, value: Any) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def command(args: list[str]) -> bytes:
    p = subprocess.run([*DOCKER, *args], capture_output=True, timeout=5)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace"))
    return p.stdout


def guard(directory: Path, read_fd: int) -> None:
    global DOCKER
    config = directory / "docker-config"
    config.mkdir(exist_ok=False)
    DOCKER = [*DOCKER, "--config", str(config)]
    spec = json.loads((directory / "intent.json").read_bytes())
    started = time.monotonic()
    receipt: dict[str, Any] = {
        "format": "private-container-cleanup/1",
        "owner": spec["owner"],
        "name": spec["name"],
        "container_id": None,
        "stopped": False,
        "removed": False,
        "exit_code": None,
        "reason": "unresolved",
    }
    process = None
    create_acknowledged = False

    def cancellation() -> str | None:
        if (directory / "cancel").exists():
            return "cancelled"
        if select.select([read_fd], [], [], 0)[0] and os.read(read_fd, 1) == b"":
            return "worker-exit"
        if time.monotonic() - started >= spec["timeout"]:
            return "deadline"
        return None

    try:
        reason = cancellation()
        if reason:
            receipt.update(reason=reason, stopped=True, removed=True, never_created=True)
            return
        # Read-only pre-run inventory is evidence, never a deletion selector.
        prior = command(["ps", "--all", "--no-trunc", "--format", "{{.ID}} {{.State}}"])
        inventory = []
        for line in prior.decode().splitlines():
            identity, state = line.split(maxsplit=1)
            if len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
                raise RuntimeError("invalid pre-existing container identity")
            inventory.append({"container_id": identity, "state": state})
        save(directory / "pre-existing.json", {"containers": inventory})
        # Complete the bounded create before reconciling cancellation. Killing the
        # CLI alone cannot prove the daemon did not create a container later.
        identity = (
            command(
                [
                    "create",
                    "--pull",
                    "never",
                    "--name",
                    spec["name"],
                    "--label",
                    LABEL + "=" + spec["owner"],
                    *(["--interactive"] if spec.get("stdin") else []),
                    *spec["args"],
                ]
            )
            .decode()
            .strip()
        )
        if len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
            raise RuntimeError("invalid created container identity; manual reconciliation required")
        if identity in {row["container_id"] for row in inventory}:
            raise RuntimeError("create returned pre-existing identity; untouched")
        create_acknowledged = True
        receipt["container_id"] = identity
        save(directory / "created.json", {"container_id": identity, "owner": spec["owner"]})
        owned = json.loads(command(["inspect", identity]))[0]
        if owned["Id"] != identity or owned["Config"]["Labels"].get(LABEL) != spec["owner"]:
            raise RuntimeError("created container ownership mismatch before start")
        reason = cancellation()
        with ExitStack() as files:
            out = files.enter_context((directory / "stdout").open("wb"))
            err = files.enter_context((directory / "stderr").open("wb"))
            source = (
                files.enter_context((directory / "stdin").open("rb"))
                if spec.get("stdin")
                else subprocess.DEVNULL
            )
            if not reason:
                process = subprocess.Popen(
                    [*DOCKER, "start", "-a", *(["-i"] if spec.get("stdin") else []), identity],
                    stdin=source,
                    stdout=out,
                    stderr=err,
                    start_new_session=True,
                )
                save(directory / "started.json", {"container_id": identity})
                while process.poll() is None:
                    reason = cancellation()
                    if reason:
                        break
                    if (directory / "stdout").stat().st_size > spec["cap"] or (
                        directory / "stderr"
                    ).stat().st_size > spec.get("stderr_cap", spec["cap"]):
                        reason = "output-limit"
                        break
                    time.sleep(0.02)
                if not reason:
                    receipt["exit_code"] = process.returncode
                    reason = "completed"
        receipt["reason"] = reason
    except Exception as error:
        receipt["error"] = repr(error)
    finally:
        try:
            if create_acknowledged:
                identity = receipt["container_id"]
                info = json.loads(command(["inspect", identity]))[0]
                if info["Id"] != identity or info["Config"]["Labels"].get(LABEL) != spec["owner"]:
                    raise RuntimeError("container ownership mismatch")
                if info["State"]["Running"]:
                    command(["kill", identity])
                info = json.loads(command(["inspect", identity]))[0]
                receipt["pre_remove_state"] = info["State"]
                # start may race the first inspection: force-remove the exact ID.
                # Successful removal and subsequent absence prove it cannot start later.
                command(["rm", "-f", identity])
                absent = subprocess.run(
                    [*DOCKER, "inspect", identity], capture_output=True, timeout=5
                )
                if absent.returncode == 0 or not any(
                    m in absent.stderr.lower() for m in (b"no such object", b"no such container")
                ):
                    raise RuntimeError("removal not verified")
                receipt["stopped"] = True
                receipt["removed"] = True
            elif not receipt.get("never_created"):
                # A create RPC timeout is not proof of absence. Preserve exact
                # name/token for manual resolution; parent must fail closed.
                receipt["error"] = receipt.get("error", "create acknowledgement absent")
            if process is not None:
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
        except Exception as error:
            receipt["cleanup_error"] = repr(error)
        receipt["elapsed_seconds"] = time.monotonic() - started
        save(directory / "cleanup.json", receipt)
        os.close(read_fd)


def run_container(
    directory: Path,
    args: list[str],
    *,
    timeout: float,
    cap: int = 1024**2,
    stderr_cap: int | None = None,
    stdin_bytes: bytes | None = None,
) -> dict[str, Any]:
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    if stdin_bytes is not None:
        (directory / "stdin").write_bytes(stdin_bytes)
    owner = uuid.uuid4().hex
    save(
        directory / "intent.json",
        {
            "owner": owner,
            "name": "u4-private-" + owner,
            "args": args,
            "timeout": timeout,
            "cap": cap,
            "stderr_cap": cap if stderr_cap is None else stderr_cap,
            "stdin": stdin_bytes is not None,
        },
    )
    read_fd, write_fd = os.pipe()
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                str(Path(__file__).resolve()),
                str(directory),
                str(read_fd),
            ],
            pass_fds=(read_fd,),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.close(read_fd)
        read_fd = -1
        try:
            process.wait(timeout=timeout + 35)
        except BaseException:
            (directory / "cancel").touch()
            raise
    finally:
        os.close(write_fd)
        if read_fd >= 0:
            os.close(read_fd)
    receipt: dict[str, Any] = json.loads((directory / "cleanup.json").read_bytes())
    if not receipt["stopped"] or not receipt["removed"] or "cleanup_error" in receipt:
        raise RuntimeError("private container cleanup unresolved: " + str(directory))
    return receipt


def cleanup(scope: Path, *, timeout: float = 35) -> list[dict[str, Any]]:
    """After workers stop/join: cancel exact intents in this invocation's directory.

    Parent must not accept completion while workers may create further intents.
    Does not sweep Docker or infer stopped from a CLI/worker exit.
    """
    intents = sorted(scope.glob("*/intent.json"))
    for intent in intents:
        (intent.parent / "cancel").touch()
    end = time.monotonic() + timeout
    receipts = []
    for intent in intents:
        path = intent.parent / "cleanup.json"
        while not path.exists() and time.monotonic() < end:
            time.sleep(0.02)
        if not path.exists():
            raise RuntimeError("private cleanup incomplete intent: " + str(intent))
        receipt = json.loads(path.read_bytes())
        owner = json.loads(intent.read_bytes())["owner"]
        if receipt["owner"] != owner or not receipt["stopped"] or not receipt["removed"]:
            raise RuntimeError("private cleanup unresolved: " + str(path))
        receipts.append(receipt)
    return receipts


if __name__ == "__main__":
    guard(Path(sys.argv[1]), int(sys.argv[2]))
