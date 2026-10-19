"""Synthetic command/recipe joins only; no Docker, build or capture worker."""

from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
from typing import Any, cast

import pytest
from uarch_contract.hashing import canonical_json, sha256

from native.tools import component_runtime_candidate as preparation
from rkuarch.engines.native import component_construction
from validation.component import capture_diagnostics as diagnostic
from validation.component import capture_monitor as monitor
from validation.component import test_capture_monitor as fixtures


def put(plan: dict[str, Any], name: str, value: Any) -> None:
    path = Path(plan["inputs"][name]["path"])
    path.write_text(canonical_json(value))
    plan["inputs"][name]["byte_hash"] = sha256(path.read_bytes())


def setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    plan = cast(Any, fixtures.plan).__wrapped__(tmp_path, monkeypatch)
    literals = json.loads(
        (
            preparation.ROOT
            / "docs/reviews/U4-B-activation-combined-confirmation-v1/evidence/construction.json"
        ).read_bytes()
    )["rendered_from_source_ast_only"]
    modes = [
        {
            "mode": v["mode"],
            "cargo_args": v["actual_source_argv"][1:],
            "rustflags": ["-C", "debuginfo=1", "-C", "linker=/controls/linker.sh"],
            "permitted_environment": v["actual_source_environment"],
        }
        for v in literals
    ]
    build = json.loads(Path(plan["inputs"]["build_inputs"]["path"]).read_bytes())
    build.pop("permitted_environment")
    build.update(format="uarch-component-build-inputs/3", mode_configs=modes)
    put(plan, "build_inputs", build)
    recipe = json.loads(Path(plan["inputs"]["construction_recipe"]["path"]).read_bytes())
    recipe.pop("permitted_environment")
    recipe.update(
        format="component-capture-recipe/2",
        mode_configs=modes,
        build_inputs_byte_hash=plan["inputs"]["build_inputs"]["byte_hash"],
    )
    put(plan, "construction_recipe", recipe)
    selected = next(v for v in literals if v["mode"] == mode)
    plan.update(
        format="component-capture-plan/2",
        phase=mode,
        child_argv=selected["actual_source_argv"],
        environment=selected["actual_source_environment"],
    )
    put(plan, "environment", plan["environment"])
    policy_path = tmp_path / "policy.json"
    policy_path.write_bytes(
        (
            preparation.ROOT
            / "docs/reviews/U4-B-capture-diagnostics-v1/diagnostic-policy-proposal.json"
        ).read_bytes()
    )
    plan["inputs"]["capture_diagnostic_policy"] = {
        "path": str(policy_path),
        "byte_hash": sha256(policy_path.read_bytes()),
    }
    return plan, modes


@pytest.mark.parametrize("mode", ["debug", "release"])
def test_independent_literals_survive_split_wrapper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    plan, modes = setup(tmp_path, monkeypatch, mode)
    assert component_construction.invocation(modes, mode) == (
        plan["child_argv"],
        plan["environment"],
    )
    monitor.verify_plan(plan)
    rendered = monitor.command(plan, tmp_path / "unlaunched")
    wrapped = diagnostic.wrapped_child(mode, plan["child_argv"])
    assert rendered[-len(wrapped) :] == wrapped
    assert rendered.count(f"link-arg=-Wl,-Map=/receipts/{mode}.map") == 1
    offset = rendered.index("-i") + 1
    assert dict(v.split("=", 1) for v in rendered[offset : offset + 11]) == plan["environment"]
    assert len(plan["environment"]) == 11
    assert plan["environment"]["C2_RUN_TAG"] == mode + "-build"
    assert not (tmp_path / "unlaunched").exists()
    # The diagnostic wrapper does not replace native argv/environment with policy text.
    assert "capture_diagnostic_policy" not in plan["environment"]


def test_resealed_mode_omission_still_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, modes = setup(tmp_path, monkeypatch, "debug")
    del modes[0]["permitted_environment"]["RUSTC_WRAPPER"]
    build = json.loads(Path(plan["inputs"]["build_inputs"]["path"]).read_bytes())
    build["mode_configs"] = modes
    put(plan, "build_inputs", build)
    recipe = json.loads(Path(plan["inputs"]["construction_recipe"]["path"]).read_bytes())
    recipe.update(
        mode_configs=modes, build_inputs_byte_hash=plan["inputs"]["build_inputs"]["byte_hash"]
    )
    put(plan, "construction_recipe", recipe)
    plan["environment"] = modes[0]["permitted_environment"]
    put(plan, "environment", plan["environment"])
    with pytest.raises(ValueError, match="exact production construction specification"):
        monitor.verify_plan(plan)


def test_legacy_plan_stays_unwrapped_and_conservative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = cast(Any, fixtures.plan).__wrapped__(tmp_path, monkeypatch)
    monitor.verify_plan(plan)
    rendered = monitor.command(plan, tmp_path / "unlaunched")
    assert "capture-child" not in rendered
    assert rendered[-len(plan["child_argv"]) :] == plan["child_argv"]


@pytest.mark.parametrize("corrupt", [False, True])
def test_monitor_consumes_diagnostic_result_without_real_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corrupt: bool
) -> None:
    from native.tools import component_container_guard
    from validation.component import test_capture_diagnostics as records

    plan, _ = setup(tmp_path, monkeypatch, "debug")
    policy = json.loads(Path(plan["inputs"]["capture_diagnostic_policy"]["path"]).read_bytes())
    policy["build_stderr_lines"]["debug"] = ["   Compiling synthetic v0.0.0\n"]
    put(plan, "capture_diagnostic_policy", policy)
    emitted, old_plan = records.fixture(tmp_path / "emitted")
    put(
        plan,
        "syscall_policy",
        json.loads(Path(old_plan["inputs"]["syscall_policy"]["path"]).read_bytes()),
    )
    trace_path = emitted / "traces/debug.trace.100"
    trace = (
        trace_path.read_text()
        .replace(
            records.exec_line(diagnostic.wrapped_child("debug", old_plan["child_argv"])),
            records.exec_line(diagnostic.wrapped_child("debug", plan["child_argv"])),
        )
        .replace(records.exec_line(old_plan["child_argv"]), records.exec_line(plan["child_argv"]))
    )
    trace_path.write_text(trace)

    def guardian(
        directory: Path, args: list[str], *, timeout: float, cap: int, stderr_cap: int
    ) -> dict[str, Any]:
        directory.mkdir()
        owner, cid = "a" * 32, "b" * 64
        values: dict[str, dict[str, Any]] = {
            "intent.json": {
                "owner": owner,
                "name": "synthetic-" + owner,
                "args": args,
                "timeout": timeout,
                "cap": cap,
                "stderr_cap": stderr_cap,
                "stdin": False,
            },
            "pre-existing.json": {"containers": []},
            "created.json": {"owner": owner, "container_id": cid},
            "started.json": {"container_id": cid},
            "cleanup.json": {
                "owner": owner,
                "container_id": cid,
                "stopped": True,
                "removed": True,
                "reason": "completed",
                "exit_code": 0,
            },
        }
        for name, value in values.items():
            (directory / name).write_text(canonical_json(value))
        for name in ("stdout", "stderr"):
            (directory / name).write_bytes(b"")
        for source in (emitted / "traces").iterdir():
            (directory.parent / "traces" / source.name).write_bytes(source.read_bytes())
        if corrupt:
            path = directory.parent / "traces/debug.child.stderr"
            path.write_bytes(path.read_bytes() * 2)
        return values["cleanup.json"]

    class InlineWorker:
        def __init__(self, *, target: Any, args: Any) -> None:
            self.target, self.args = target, args

        def start(self) -> None:
            self.target(*self.args)

        def is_alive(self) -> bool:
            return False

        def join(self, *_: Any) -> None:
            pass

        def close(self) -> None:
            pass

    class Context:
        Process = InlineWorker

    monkeypatch.setattr(component_container_guard, "run_container", guardian)
    monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context())
    monkeypatch.setattr(monitor, "helpers", lambda: {"safe_fork": lambda: None})
    value = monitor.run_capture(plan, tmp_path / "mock-capture")
    assert value["format"] == "component-capture-receipt/2"
    assert value["record_valid"] is (not corrupt)
    assert value["coverage"]["diagnostics_accepted"] is (not corrupt)
    assert not value["read_audit_complete"]
    if corrupt:
        assert value["coverage"]["errors"] == ["raw child bytes/write trace join"]
        assert "capture diagnostics refused" in value["reason"]
