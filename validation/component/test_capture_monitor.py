"""Mock guardian subprocesses and synthetic traces only; no Docker or tracer runs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import canonical_json, sha256

from validation.component import capture_monitor as monitor


def write(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value))


@pytest.fixture
def plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    files = tmp_path / "inputs"
    files.mkdir()
    mounts = {}
    for name in ("work", "cargo-home", "controls", "diagnostics", "canary"):
        path = files / name
        path.mkdir()
        mounts["/" + name] = str(path)
    generated = files / "work/identity.rs"
    generated.write_text("synthetic identity; not a build")
    tool_inputs = files / "ToolInputs.json"
    write(tool_inputs, {"image_digest": monitor.IMAGE, "synthetic": True})
    monkeypatch.setattr(monitor, "TOOLS_HASH", sha256(tool_inputs.read_bytes()))
    build = files / "BuildInputs.json"
    write(
        build,
        {
            "source_commit": "1" * 40,
            "permitted_environment": {"LC_ALL": "C"},
            "source_files": [{"path": "identity.rs", "byte_hash": sha256(generated.read_bytes())}],
            "generated_identity_output_paths": ["identity.rs"],
            "tool_inputs_file": {
                "path": "ToolInputs.json",
                "byte_hash": sha256(tool_inputs.read_bytes()),
            },
            "mode_configs": [{"mode": "debug", "cargo_args": ["synthetic-not-executed"]}],
        },
    )
    recipe = files / "recipe.json"
    build_value = json.loads(build.read_bytes())
    write(
        recipe,
        {
            "format": "component-capture-recipe/1",
            "source_commit": "1" * 40,
            "build_inputs_byte_hash": sha256(build.read_bytes()),
            "preparation_source": build_value["source_files"][0],
            **{
                k: build_value[k]
                for k in (
                    "mode_configs",
                    "permitted_environment",
                    "generated_identity_output_paths",
                )
            },
        },
    )
    diagnostics = files / "diagnostics.json"
    diagnostic_tool = files / "diagnostics/tool"
    diagnostic_tool.write_bytes(b"synthetic diagnostic bytes; never executed")
    write(
        diagnostics,
        {
            "synthetic": True,
            "image": monitor.IMAGE,
            "extracted_files": {
                "strace/tool": {"sha256": sha256(diagnostic_tool.read_bytes()).split(":")[1]}
            },
            "extracted_symlinks": {},
        },
    )
    monkeypatch.setattr(monitor, "DIAGNOSTICS_HASH", sha256(diagnostics.read_bytes()))
    environment = files / "environment.json"
    write(environment, {"LC_ALL": "C"})
    policy = files / "syscalls.json"
    write(policy, {"classified_syscalls": ["execve", "clone", "read", "write"]})
    return {
        "format": "component-capture-plan/1",
        "image": monitor.IMAGE,
        "source_commit": "1" * 40,
        "phase": "debug",
        "inputs": {
            k: {"path": str(p), "byte_hash": sha256(p.read_bytes())}
            for k, p in {
                "build_inputs": build,
                "construction_recipe": recipe,
                "generated_identity": generated,
                "diagnostics": diagnostics,
                "environment": environment,
                "syscall_policy": policy,
            }.items()
        },
        "environment": {"LC_ALL": "C"},
        "mounts": mounts,
        "tool_inputs": {"path": str(tool_inputs), "byte_hash": sha256(tool_inputs.read_bytes())},
        "child_argv": [monitor.CARGO, "synthetic-not-executed"],
        "seconds": 2,
        "output_bytes": 65536,
        "stream_bytes": 4096,
        "cpus": 1,
        "memory_bytes": 1024**3,
        "pids": 64,
        "nofile": 256,
        "source_files": {str(generated): sha256(generated.read_bytes())},
        "tool_files": {str(diagnostic_tool): sha256(diagnostic_tool.read_bytes())},
    }


def install_guard(monkeypatch: pytest.MonkeyPatch, attack: str | None = None) -> None:
    def mock(
        directory: Path, args: list[str], *, timeout: float, cap: int, stderr_cap: int
    ) -> dict[str, Any]:
        assert "--name" not in args and "--rm" not in args and "--network" in args
        directory.mkdir()
        owner, cid = "a" * 32, "b" * 64
        write(
            directory / "intent.json",
            {
                "owner": owner,
                "name": "u4-private-" + owner,
                "args": args,
                "timeout": timeout,
                "cap": cap,
                "stderr_cap": stderr_cap,
                "stdin": False,
            },
        )
        write(
            directory / "pre-existing.json",
            {"containers": [{"container_id": "f" * 64, "state": "exited"}]},
        )
        write(directory / "created.json", {"owner": owner, "container_id": cid})
        write(
            directory / "started.json", {"container_id": "d" * 64 if attack == "started" else cid}
        )
        if attack == "intent":
            record = json.loads((directory / "intent.json").read_bytes())
            record["args"] = ["forged"]
            write(directory / "intent.json", record)
        (directory / "stdout").write_bytes(b"")
        (directory / "stderr").write_bytes(b"strace: records lost" if attack == "loss" else b"")
        root = directory.parent
        parent = (
            '1.000 execve("/bin/sh", ["sh"], []) = 0\n'
            "1.001 clone(child_stack=NULL, flags=SIGCHLD) = 101\n"
            "1.003 +++ exited with 0 +++\n"
        )
        child = '1.002 read(3</work/input>, "x", 1) = 1\n1.003 +++ exited with 0 +++\n'
        if attack == "nonzero":
            parent = parent.replace("exited with 0", "exited with 7")
        if attack == "unknown":
            child = child.replace("read(", "unclassified_syscall(")
        if attack == "unfinished":
            child = "1.002 read(3, <unfinished ...>\n1.003 +++ exited with 0 +++\n"
        if attack == "tail":
            child = child.split("1.003")[0]
        (root / "traces/debug.trace.100").write_text(parent)
        if attack != "child":
            (root / "traces/debug.trace.101").write_text(child)
        if attack == "bytes":
            (root / "target/large").write_bytes(b"x" * 70000)
        if attack == "symlink":
            (root / "traces/alias").symlink_to(directory / "stdout")
        receipt = {
            "format": "private-container-cleanup/1",
            "owner": owner,
            "name": "u4-private-" + owner,
            "container_id": cid,
            "stopped": True,
            "removed": attack != "cleanup",
            "reason": "completed",
            "exit_code": 7 if attack == "nonzero" else 0,
        }
        write(directory / "cleanup.json", receipt)
        if attack == "hang":
            while not (directory / "cancel").exists():
                time.sleep(0.01)
        return receipt

    from native.tools import component_container_guard

    monkeypatch.setattr(component_container_guard, "run_container", mock)


def test_mock_capture_records_coverage_and_exact_id_cleanup(
    plan: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_guard(monkeypatch)
    value = monitor.run_capture(plan, tmp_path / "capture")
    assert value["record_valid"] and not value["read_audit_complete"]
    assert value["coverage"]["root"] == 100 and value["coverage"]["children"] == [101]
    assert value["started_ns"] < value["ended_ns"] and value["status"] == 0
    assert value["cleanup"]["container_ids"] == ["b" * 64]
    assert "traces/debug.trace.101" in value["files"]


@pytest.mark.parametrize(
    "attack",
    [
        "child",
        "unknown",
        "unfinished",
        "tail",
        "loss",
        "bytes",
        "symlink",
        "cleanup",
        "hang",
        "started",
        "intent",
    ],
)
def test_partial_or_lost_capture_never_becomes_complete(
    plan: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    install_guard(monkeypatch, attack)
    if attack == "hang":
        plan["seconds"] = 0.08
    root = tmp_path / "capture"
    value = monitor.run_capture(plan, root)
    assert not value["record_valid"] and value["reason"] and not value["read_audit_complete"]
    assert value["started_ns"] < value["ended_ns"]
    assert (root / "start.json").exists() and (root / "capture.json").exists()
    assert (root / "traces/debug.trace.100").exists()


def test_missing_or_changed_plan_stops_before_worker(plan: Any, tmp_path: Path) -> None:
    plan["source_commit"] = None
    with pytest.raises(ValueError, match="source commit"):
        monitor.run_capture(plan, tmp_path / "capture")
    assert not (tmp_path / "capture").exists()


@pytest.mark.parametrize(
    "attack", ["source", "environment", "argv", "diagnostic", "tool", "extra-cache"]
)
def test_binding_changes_refuse_before_worker(plan: Any, tmp_path: Path, attack: str) -> None:
    if attack == "source":
        plan["source_files"] = {}
    elif attack == "environment":
        plan["environment"]["RUSTFLAGS"] = "arbitrary"
    elif attack == "argv":
        plan["child_argv"] = plan["child_argv"][1:]
    elif attack == "diagnostic":
        path = Path(plan["inputs"]["diagnostics"]["path"])
        path.write_text("{}")
        plan["inputs"]["diagnostics"]["byte_hash"] = sha256(path.read_bytes())
    elif attack == "tool":
        plan["tool_inputs"]["byte_hash"] = "sha256:" + "f" * 64
    else:
        (Path(plan["mounts"]["/cargo-home"]) / "extra").write_text("unlisted")
    with pytest.raises(ValueError):
        monitor.run_capture(plan, tmp_path / "capture")
    assert not (tmp_path / "capture").exists()


def test_failed_command_is_recorded_without_success(
    plan: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_guard(monkeypatch, "nonzero")
    value = monitor.run_capture(plan, tmp_path / "capture")
    assert value["record_valid"] and not value["command_succeeded"]
    assert value["status"] == 7 and not value["read_audit_complete"]


def test_no_worker_start_retains_terminal_record(
    plan: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refused() -> None:
        raise ValueError("synthetic fork refusal")

    monkeypatch.setattr(monitor, "helpers", lambda: {"safe_fork": refused})
    value = monitor.run_capture(plan, tmp_path / "capture")
    assert not value["record_valid"] and "fork refusal" in value["reason"]
    assert value["status"] is None and value["ended_ns"] > value["started_ns"]


def test_component_build_uses_explicit_recipe_companion(plan: Any) -> None:
    build_path = Path(plan["inputs"]["build_inputs"]["path"])
    build = json.loads(build_path.read_bytes())
    for key in ("mode_configs", "permitted_environment", "generated_identity_output_paths"):
        del build[key]
    write(build_path, build)
    plan["inputs"]["build_inputs"]["byte_hash"] = sha256(build_path.read_bytes())
    recipe_path = Path(plan["inputs"]["construction_recipe"]["path"])
    recipe = json.loads(recipe_path.read_bytes())
    recipe["build_inputs_byte_hash"] = sha256(build_path.read_bytes())
    write(recipe_path, recipe)
    plan["inputs"]["construction_recipe"]["byte_hash"] = sha256(recipe_path.read_bytes())
    monitor.verify_plan(plan)
    recipe["source_commit"] = "2" * 40
    write(recipe_path, recipe)
    plan["inputs"]["construction_recipe"]["byte_hash"] = sha256(recipe_path.read_bytes())
    with pytest.raises(ValueError, match="recipe source/build"):
        monitor.verify_plan(plan)
