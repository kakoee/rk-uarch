"""Bounded monitor for one owned offline container. No host process attachment."""

import hashlib
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
TOOL = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/"
LOADER = "/lib64/ld-linux-x86-64.so.2"
TRACER = [
    LOADER,
    "--library-path",
    "/diagnostics/usr/lib/x86_64-linux-gnu:/diagnostics/lib/x86_64-linux-gnu",
    "/diagnostics/usr/bin/strace",
]


def size(root):
    """Measure all owned output bytes, including stdout/stderr and non-trace diagnostics."""
    files = list(root.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("output symlink prevents bounded accounting")
    return sum(p.stat().st_size for p in files if p.is_file())


def limit_reason(elapsed, total, seconds, byte_limit):
    if elapsed >= seconds:
        return "time limit"
    if total >= byte_limit:
        return "output size limit"
    return None


def build_command(root, phase, output, target, child, *, trace):
    name = "u4-b-audit-" + uuid.uuid4().hex
    argv = DOCKER + [
        "run",
        "--name",
        name,
        "--rm",
        "--pull",
        "never",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp",
        "--workdir",
        "/work/native",
    ]
    for src, dest, readonly in [
        (root / "source", "/work", True),
        (root / "cache", "/cargo-home", True),
        (root / "controls", "/controls", True),
        (root / "diagnostics", "/diagnostics", True),
        (root / "canary", "/canary", True),
        (target, "/target", False),
        (output, "/receipts", False),
    ]:
        argv += ["--mount", f"type=bind,src={src},dst={dest}" + (",readonly" if readonly else "")]
    argv += [
        "--entrypoint",
        "/usr/bin/env",
        IMAGE,
        "-i",
        "PATH=" + TOOL + ":/usr/local/cargo/bin:/usr/bin:/bin",
        "CARGO_HOME=/cargo-home",
        "CARGO_TARGET_DIR=/target",
        "RUSTC=" + TOOL + "rustc",
        "RUSTUP_AUTO_INSTALL=0",
        "CARGO_NET_OFFLINE=true",
        "CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse",
        "LC_ALL=C",
        "RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh",
        "RUSTC_WRAPPER=/controls/rustc-wrapper.sh",
        "C2_RUN_TAG=" + phase,
    ]
    if trace:
        argv += TRACER + [
            "-ff",
            "-ttt",
            "-yy",
            "-v",
            "-s",
            "4096",
            "-o",
            "/receipts/" + phase + ".trace",
        ]
    argv += child
    return name, argv


def validate(argv, name):
    assert argv[:3] == DOCKER and name.startswith("u4-b-audit-")
    for flag, value in [
        ("--name", name),
        ("--pull", "never"),
        ("--network", "none"),
        ("--user", "1000:1000"),
        ("--cap-drop", "ALL"),
    ]:
        assert argv[argv.index(flag) + 1] == value
    assert (
        argv.count("--security-opt") == 1
        and argv[argv.index("--security-opt") + 1] == "no-new-privileges"
    )
    assert "--read-only" in argv and IMAGE in argv
    assert not any(
        a in {"--privileged", "--cap-add", "--pid"} or a.startswith("LD_LIBRARY_PATH=")
        for a in argv
    )
    mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
    assert all("docker.sock" not in m for m in mounts)
    assert all(
        m.endswith(",readonly")
        for m in mounts
        if ",dst=/target" not in m and ",dst=/receipts" not in m
    )


def run(root, phase, child, *, trace=False, build=False):
    root = Path(root).resolve()
    assert phase.replace("-", "").isalnum()
    output = root / "receipts" / phase
    output.mkdir()
    target = root / (phase + "-target")
    target.mkdir()
    assert not any(target.iterdir())
    seconds, byte_limit = (600, 512 * 1024**2) if build else (30, 16 * 1024**2)
    name, argv = build_command(root, phase, output, target, child, trace=trace)
    validate(argv, name)
    env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(root / "docker-config")}
    started = time.time_ns()
    tick = time.monotonic()
    reason = None
    cleanup = None
    with (output / "stdout").open("wb") as stdout, (output / "stderr").open("wb") as stderr:
        proc = subprocess.Popen(argv, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            while proc.poll() is None:
                try:
                    reason = limit_reason(
                        time.monotonic() - tick, size(output), seconds, byte_limit
                    )
                except ValueError as error:
                    reason = str(error)
                if reason:
                    break
                time.sleep(0.05)
        except BaseException:
            reason = "monitor interrupted"
            raise
        finally:
            if reason:
                # Kill only the unique container launched above, never unrelated host children.
                kill_argv = DOCKER + ["kill", "--signal", "KILL", name]
                try:
                    killed = subprocess.run(kill_argv, env=env, capture_output=True, timeout=5)
                    cleanup = {
                        "argv": kill_argv,
                        "exit": killed.returncode,
                        "stdout": killed.stdout.decode(errors="replace"),
                        "stderr": killed.stderr.decode(errors="replace"),
                    }
                except subprocess.TimeoutExpired:
                    cleanup = {
                        "argv": kill_argv,
                        "failure": "kill client timeout; coverage incomplete",
                    }
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # This PID is our Docker client, not a host/shared tracee.
                    os.killpg(proc.pid, 9)
                    proc.wait()
    total = size(output)
    elapsed = time.monotonic() - tick
    reason = reason or limit_reason(elapsed, total, seconds, byte_limit)
    files = {
        str(p.relative_to(output)): {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    record = {
        "phase": phase,
        "container_name": name,
        "argv": argv,
        "environment": env,
        "started_ns": started,
        "finished_ns": time.time_ns(),
        "elapsed_seconds": elapsed,
        "limits": {"seconds": seconds, "bytes": byte_limit, "poll_seconds": 0.05},
        "observed_output_bytes": total,
        "exit_code": proc.returncode,
        "stop_reason": reason,
        "cleanup": cleanup,
        "files": files,
        "complete_observation_claim": False,
        "limit_note": (
            "Polling can detect overshoot; any hit/overshoot is retained as incomplete, "
            "never truncated into success."
        ),
    }
    (root / "output" / (phase + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    return record
