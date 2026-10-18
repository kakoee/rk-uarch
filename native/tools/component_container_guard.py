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
from pathlib import Path

DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
LABEL = "rk-uarch.private-owner"


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def command(args):
    p = subprocess.run([*DOCKER, *args], capture_output=True, timeout=5)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace"))
    return p.stdout


def guard(directory, read_fd):
    global DOCKER
    config = directory / "docker-config"
    config.mkdir(exist_ok=False)
    DOCKER = [*DOCKER, "--config", str(config)]
    spec = json.loads((directory / "intent.json").read_bytes())
    started = time.monotonic()
    receipt = {
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

    def cancellation():
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
                    *spec["args"],
                ]
            )
            .decode()
            .strip()
        )
        create_acknowledged = True
        receipt["container_id"] = identity
        save(directory / "created.json", {"container_id": identity})
        reason = cancellation()
        with (directory / "stdout").open("wb") as out, (directory / "stderr").open("wb") as err:
            if not reason:
                process = subprocess.Popen(
                    [*DOCKER, "start", "-a", identity],
                    stdout=out,
                    stderr=err,
                    start_new_session=True,
                )
                save(directory / "started.json", {"container_id": identity})
                while process.poll() is None:
                    reason = cancellation()
                    if reason:
                        break
                    if (
                        max((directory / n).stat().st_size for n in ("stdout", "stderr"))
                        > spec["cap"]
                    ):
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


def run_container(directory: Path, args: list[str], *, timeout: float, cap: int = 1024**2):
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    owner = uuid.uuid4().hex
    save(
        directory / "intent.json",
        {
            "owner": owner,
            "name": "u4-private-" + owner,
            "args": args,
            "timeout": timeout,
            "cap": cap,
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
    receipt = json.loads((directory / "cleanup.json").read_bytes())
    if not receipt["stopped"] or not receipt["removed"] or "cleanup_error" in receipt:
        raise RuntimeError("private container cleanup unresolved: " + str(directory))
    return receipt


def cleanup(scope: Path, *, timeout: float = 35):
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
