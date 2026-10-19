"""Synthetic records and a host-shell mock tracer. No strace/Docker/build/capture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import canonical_json, sha256

from validation.component import capture_diagnostics as diagnostic


def quoted(data: bytes | str) -> str:
    return json.dumps(data.decode("ascii") if isinstance(data, bytes) else data)


def exec_line(argv: list[str]) -> str:
    return f"execve({quoted(argv[0])}, {json.dumps(argv)}, []) = 0"


def write_line(fd: int, target: str, data: bytes) -> str:
    return f"write({fd}<{target}>, {quoted(data)}, {len(data)}) = {len(data)}"


def put(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def fixture(tmp_path: Path, phase: str = "debug") -> tuple[Path, dict[str, Any]]:
    root = tmp_path / phase
    (root / "traces").mkdir(parents=True)
    (root / "container").mkdir()
    policy = {
        "format": diagnostic.POLICY_FORMAT,
        "phase_caps": diagnostic.CAPS,
        "build_stderr_lines": {
            "debug": ["   Compiling synthetic v0.0.0\n"],
            "release": ["   Compiling synthetic v0.0.0\n"],
        },
    }
    calls = ["execve", "openat", "dup2", "write", "read", "close", "clone", "getdents64", "mmap"]
    for name, value in (
        ("capture_diagnostic_policy", policy),
        ("syscall_policy", {"classified_syscalls": calls}),
    ):
        put(root / (name + ".json"), value)
    argv = (
        ["/synthetic/cargo", "rustc", "--synthetic-test-only"]
        if phase != "canary"
        else list(diagnostic.CANARY_ARGV)
    )
    plan = {
        "phase": phase,
        "child_argv": argv,
        "output_bytes": 16 * 1024**2,
        "inputs": {
            name: {
                "path": str(root / (name + ".json")),
                "byte_hash": sha256((root / (name + ".json")).read_bytes()),
            }
            for name in ("capture_diagnostic_policy", "syscall_policy")
        },
    }
    stdout = (
        diagnostic.CANARY_STDOUT
        if phase == "canary"
        else b'{"reason":"build-finished","success":true}\n'
    )
    stderr = diagnostic.CANARY_STDERR if phase == "canary" else b"   Compiling synthetic v0.0.0\n"
    for name, relative in diagnostic.paths(phase).items():
        (root / relative).write_bytes(
            stdout if name == "child_stdout" else stderr if name == "child_stderr" else b""
        )
    out, err = f"/receipts/{phase}.child.stdout", f"/receipts/{phase}.child.stderr"
    rows = [
        exec_line(diagnostic.wrapped_child(phase, argv)),
        f'openat(AT_FDCWD, "{out}", O_WRONLY|O_CREAT|O_EXCL, 0666) = 3<{out}>',
        f"dup2(3<{out}>, 1<pipe:[1001]>) = 1<{out}>",
        f'openat(AT_FDCWD, "{err}", O_WRONLY|O_CREAT|O_EXCL, 0666) = 3<{err}>',
        f"dup2(3<{err}>, 2<pipe:[1002]>) = 2<{err}>",
        exec_line(argv),
        write_line(1, out, stdout),
        write_line(2, err, stderr),
    ]
    logs = {100: rows + ["+++ exited with 0 +++"]}
    if phase == "canary":
        logs[100] = rows[:6] + [
            'openat(AT_FDCWD, "/canary/alias", O_RDONLY) = 3</canary/sentinel>',
            "mmap(NULL, 100, PROT_READ, MAP_PRIVATE, 3</lib/synthetic>, 0) = 0x1000",
            "clone(child_stack=NULL, flags=SIGCHLD) = 101",
            "clone(child_stack=NULL, flags=SIGCHLD) = 102",
            "clone(child_stack=NULL, flags=SIGCHLD) = 103",
            "+++ exited with 0 +++",
        ]
        logs[101] = [
            exec_line(["/bin/cat"]),
            'read(3</canary/sentinel>, "U4-read-canary-v1\\n", 18) = 18',
            write_line(1, out, stdout),
            "close(3</canary/sentinel>) = 0",
            "+++ exited with 0 +++",
        ]
        logs[102] = [
            exec_line(["/bin/cat", "/canary/absent"]),
            'openat(AT_FDCWD, "/canary/absent", O_RDONLY) = -1 ENOENT (No such file or directory)',
            write_line(2, err, stderr),
            "+++ exited with 1 +++",
        ]
        logs[103] = [
            exec_line(["/bin/ls", "-U", "/canary"]),
            "getdents64(3</canary>, [], 32768) = 0",
            "+++ exited with 0 +++",
        ]
    for pid, lines in logs.items():
        (root / f"traces/{phase}.trace.{pid}").write_text(
            "".join(f"1.{index:06d} {line}\n" for index, line in enumerate(lines))
        )
    return root, plan


@pytest.mark.parametrize("phase", ["canary", "debug", "release"])
def test_expected_separate_child_output(tmp_path: Path, phase: str) -> None:
    root, plan = fixture(tmp_path, phase)
    value = diagnostic.inspect_capture(root, plan, 0)
    assert value["diagnostics_accepted"], value
    assert not value["read_audit_complete"] and value["authority"] is None
    assert value["streams"]["tracer_stderr"]["bytes"] == 0
    assert value["bootstrap"]["root"] == 100


@pytest.mark.parametrize(
    "attack",
    [
        "tracer-loss",
        "tracer-unknown",
        "mixed",
        "missing-child",
        "missing-tracer",
        "truncated-stream",
        "truncated-trace",
        "missing-terminal",
        "unfinished",
        "missing-child-trace",
        "unknown-call",
        "false-redirection",
        "unclassified-child",
        "wrong-status",
        "aliased",
        "second-writer",
        "writev",
        "early-output",
    ],
)
def test_malformed_capture_refuses_without_discard(tmp_path: Path, attack: str) -> None:
    root, plan = fixture(tmp_path)
    stderr = root / "traces/debug.child.stderr"
    trace = root / "traces/debug.trace.100"
    raw = trace.read_text()
    if attack in ("tracer-loss", "tracer-unknown"):
        (root / "container/stderr").write_bytes(
            b"strace: records lost\n" if attack == "tracer-loss" else b"unclassified diagnostic\n"
        )
    elif attack == "mixed":
        (root / "container/stderr").write_bytes(stderr.read_bytes())
        stderr.write_bytes(b"")
    elif attack == "missing-child":
        stderr.unlink()
    elif attack == "missing-tracer":
        (root / "container/stderr").unlink()
    elif attack == "truncated-stream":
        stderr.write_bytes(stderr.read_bytes()[:-1])
    elif attack == "truncated-trace":
        trace.write_text(raw.replace('"   Compiling synthetic v0.0.0\\n"', '"   Compiling"...'))
    elif attack == "missing-terminal":
        trace.write_text(raw[: raw.rfind("1.000008")])
    elif attack == "unfinished":
        trace.write_text(
            raw.replace(
                "+++ exited with 0 +++", "read(3, <unfinished ...>\n1.000009 +++ exited with 0 +++"
            )
        )
    elif attack == "missing-child-trace":
        trace.write_text(
            raw.replace(
                "+++ exited with 0 +++",
                "clone(child_stack=NULL, flags=SIGCHLD) = 101\n1.000009 +++ exited with 0 +++",
            )
        )
    elif attack == "unknown-call":
        trace.write_text(
            raw.replace(
                "+++ exited with 0 +++", "unknown_record() = 0\n1.000009 +++ exited with 0 +++"
            )
        )
    elif attack == "false-redirection":
        trace.write_text(raw.replace("O_WRONLY|O_CREAT|O_EXCL", "O_WRONLY|O_CREAT|O_TRUNC"))
    elif attack == "unclassified-child":
        bad = b"unclassified child error!\n"
        trace.write_text(
            raw.replace(
                write_line(2, "/receipts/debug.child.stderr", stderr.read_bytes()),
                write_line(2, "/receipts/debug.child.stderr", bad),
            )
        )
        stderr.write_bytes(bad)
    elif attack == "wrong-status":
        trace.write_text(raw.replace("exited with 0", "exited with 7"))
    elif attack == "aliased":
        stderr.unlink()
        stderr.symlink_to(root / "container/stderr")
    elif attack == "second-writer":
        trace.write_text(
            raw.replace(
                "+++ exited with 0 +++",
                "clone(child_stack=NULL, flags=SIGCHLD) = 101\n1.000009 +++ exited with 0 +++",
            )
        )
        (root / "traces/debug.trace.101").write_text(
            '1.1 write(2</receipts/debug.child.stderr>, "x", 1) = 1\n1.2 +++ exited with 0 +++\n'
        )
        stderr.write_bytes(stderr.read_bytes() + b"x")
    elif attack == "writev":
        trace.write_text(raw.replace("write(2<", "writev(2<"))
    elif attack == "early-output":
        trace.write_text(
            raw.replace("1.000001 ", '1.000000 write(2<pipe:[1002]>, "x", 1) = 1\n1.000001 ', 1)
        )
    snapshot = {
        str(p): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()
    }
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"] and value["errors"], value
    assert not value["read_audit_complete"]
    assert all(Path(name).read_bytes() == raw for name, raw in snapshot.items())


def test_caps_and_policy_identity(tmp_path: Path) -> None:
    root, plan = fixture(tmp_path)
    path = root / "traces/debug.child.stderr"
    path.write_bytes(b"x" * (diagnostic.CAPS["debug"]["child_stderr"] + 1))
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"] and "oversized" in value["errors"][0]
    pin = plan["inputs"]["capture_diagnostic_policy"]
    policy_path = Path(pin["path"])
    policy_path.write_text("{}")
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"] and "identity" in value["errors"][0]


def test_loss_text_cannot_be_reclassified(tmp_path: Path) -> None:
    _, plan = fixture(tmp_path)
    path = Path(plan["inputs"]["capture_diagnostic_policy"]["path"])
    policy = json.loads(path.read_bytes())
    policy["build_stderr_lines"]["debug"].append("strace: records lost\n")
    put(path, policy)
    plan["inputs"]["capture_diagnostic_policy"]["byte_hash"] = sha256(path.read_bytes())
    with pytest.raises(ValueError, match="cannot be child allowlist"):
        diagnostic.verify_policy(plan)


def test_host_shell_mock_keeps_tracer_fd_separate(tmp_path: Path) -> None:
    # Host-only mock tracer; never uses the accepted image or strace. Only the
    # fixed /receipts prefix is relocated for this shell descriptor-semantics test.
    child = [
        sys.executable,
        "-c",
        "import sys; print('child-out'); print('child-err', file=sys.stderr)",
    ]
    argv = diagnostic.wrapped_child("debug", child)
    argv[2] = argv[2].replace("/receipts/", str(tmp_path) + "/")
    tracer = (
        "import subprocess,sys; print('synthetic tracer diagnostic',file=sys.stderr); "
        "sys.exit(subprocess.run(sys.argv[1:]).returncode)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", tracer, *argv], capture_output=True, timeout=5
    )
    assert completed.returncode == 0
    assert completed.stdout == b"" and completed.stderr == b"synthetic tracer diagnostic\n"
    assert (tmp_path / "debug.child.stdout").read_bytes() == b"child-out\n"
    assert (tmp_path / "debug.child.stderr").read_bytes() == b"child-err\n"
    # Fresh-only/noclobber: retry cannot replace retained streams and does not execute child.
    original = (tmp_path / "debug.child.stderr").read_bytes()
    again = subprocess.run(argv, capture_output=True, timeout=5)
    assert again.returncode != 0 and again.stderr
    assert (tmp_path / "debug.child.stderr").read_bytes() == original


def test_unrecorded_but_classified_bytes_refuse(tmp_path: Path) -> None:
    root, plan = fixture(tmp_path)
    stream = root / "traces/debug.child.stderr"
    stream.write_bytes(stream.read_bytes() * 2)
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"]
    assert value["errors"] == ["raw child bytes/write trace join"]


def test_scalar_cargo_record_refuses_as_data(tmp_path: Path) -> None:
    root, plan = fixture(tmp_path)
    path = root / "traces/debug.child.stdout"
    trace = root / "traces/debug.trace.100"
    old, new = path.read_bytes(), b'1\n{"reason":"build-finished","success":true}\n'
    trace.write_text(
        trace.read_text().replace(
            write_line(1, "/receipts/debug.child.stdout", old),
            write_line(1, "/receipts/debug.child.stdout", new),
        )
    )
    path.write_bytes(new)
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"] and value["errors"] == ["Cargo record objects"]


def test_canary_diagnostic_requires_failed_child_writer(tmp_path: Path) -> None:
    root, plan = fixture(tmp_path, "canary")
    child = root / "traces/canary.trace.102"
    parent = root / "traces/canary.trace.100"
    line = write_line(2, "/receipts/canary.child.stderr", diagnostic.CANARY_STDERR)
    child.write_text("\n".join(v for v in child.read_text().splitlines() if line not in v) + "\n")
    parent.write_text(
        parent.read_text().replace(
            "+++ exited with 0 +++", line + "\n1.999999 +++ exited with 0 +++"
        )
    )
    value = diagnostic.inspect_capture(root, plan, 0)
    assert not value["diagnostics_accepted"]
    assert value["errors"] == ["canary diagnostic writer must be failed lookup child"]
