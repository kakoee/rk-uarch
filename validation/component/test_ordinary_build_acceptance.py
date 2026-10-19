"""Synthetic finite build provenance. No compiler, Docker, tracing or authority."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import sha256

from validation.component import ordinary_build_acceptance as builds


def bind(root: Path, path: str, data: bytes) -> dict[str, str]:
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)
    return {"path": path, "byte_hash": sha256(data)}


def fixture(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = {
        role: [bind(root, "inputs/" + role, ("synthetic:" + role).encode())]
        for role in builds.INPUT_ROLES
    }
    producer = inputs["source_files"][0]
    inputs["producers"] = [producer]
    generated = inputs["generated_inputs"][0]
    declaration = {
        "source_commit": "a" * 40,
        "source_tree": "b" * 40,
        "mode": "debug",
        "image_digest": builds.IMAGE,
        "argv": ["/synthetic/cargo", "rustc", "--offline", "--locked", "--message-format=json"],
        "environment": {"LC_ALL": "C", "CARGO_NET_OFFLINE": "true"},
        "inputs": inputs,
        "generated_producers": [
            {"output": generated, "producer": producer, "inputs": [inputs["build_inputs"][0]]}
        ],
        "cargo_artifact": "/target/debug/uarch-engine",
        "warning_policy": "retain-compiler-diagnostics;required-checks-separate",
    }
    executable = bind(root, "outputs/uarch-engine", b"synthetic-executable-not-runnable")
    expected = {
        "format": builds.EXPECTATION,
        "declaration": declaration,
        "executable": executable,
        "timeout_s": 600,
        "stdout_bytes": 1024**2,
        "stderr_bytes": 1024**2,
    }
    stdout = (
        b"\n".join(
            json.dumps(x).encode()
            for x in [
                {
                    "reason": "compiler-message",
                    "message": {"level": "warning", "rendered": "synthetic warning"},
                },
                {
                    "reason": "compiler-artifact",
                    "target": {"name": "uarch-engine", "kind": ["bin"]},
                    "executable": declaration["cargo_artifact"],
                    "fresh": False,
                },
                {"reason": "build-finished", "success": True},
            ]
        )
        + b"\n"
    )
    stderr = b"   Compiling synthetic v0.0.0\nwarning: synthetic ordinary output\n"
    streams = {}
    for name, data in (("stdout", stdout), ("stderr", stderr)):
        streams[name] = dict(
            bind(root, name, data),
            observed_bytes=len(data),
            retained_bytes=len(data),
            truncated=False,
        )
    receipt = {
        "format": builds.RECEIPT,
        "declaration": copy.deepcopy(declaration),
        "output_root_id": "c" * 64,
        "target_before": [],
        "started_monotonic": 1.0,
        "ended_monotonic": 2.0,
        "deadline_monotonic": 601.0,
        "exit_code": 0,
        "completed": True,
        "timed_out": False,
        "resource_failure": None,
        "streams": streams,
        "executable": executable,
        "input_observations": copy.deepcopy(inputs),
    }
    return expected, receipt


def test_ordinary_diagnostics_and_absent_trace_are_not_failures(tmp_path: Path) -> None:
    expected, receipt = fixture(tmp_path)
    result = builds.consume_build(tmp_path, receipt, expected)
    assert result["clean_build_success"] and result["authority"] is None
    assert result["dynamic_read_coverage"] == "not-assessed"
    assert result["startup_assurance"] == "not-assessed"
    assert result["simulation_determinism"] == "not-assessed"
    required = {row["path"]: row["byte_hash"] for row in result["required_files"]}
    for rows in expected["declaration"]["inputs"].values():
        assert all(required[row["path"]] == row["byte_hash"] for row in rows)
    assert required["outputs/uarch-engine"] == expected["executable"]["byte_hash"]
    assert required["stdout"] == receipt["streams"]["stdout"]["byte_hash"]
    assert required["stderr"] == receipt["streams"]["stderr"]["byte_hash"]


@pytest.mark.parametrize(
    "attack",
    [
        "source-claim",
        "tool-claim",
        "source-bytes",
        "tool-bytes",
        "generated-bytes",
        "producer",
        "missing-input-role",
        "missing-generated-producer",
        "stale-format",
        "missing-artifact",
        "wrong-executable",
        "wrong-image",
        "wrong-command",
        "extra-environment",
        "nonzero",
        "timeout",
        "incomplete",
        "resource",
        "missing-log",
        "truncated",
        "wrong-length",
        "missing-completion",
        "failed-completion",
        "wrong-cargo-artifact",
        "fresh-artifact",
        "prior-target",
    ],
)
def test_mandatory_failure_refuses(tmp_path: Path, attack: str) -> None:
    expected, receipt = fixture(tmp_path)
    if attack == "source-claim":
        receipt["declaration"]["source_commit"] = "d" * 40
    elif attack == "tool-claim":
        receipt["declaration"]["inputs"]["tool_inputs"][0]["byte_hash"] = "sha256:" + "d" * 64
    elif attack in ("source-bytes", "tool-bytes", "generated-bytes"):
        role = {
            "source-bytes": "source_files",
            "tool-bytes": "tool_files",
            "generated-bytes": "generated_inputs",
        }[attack]
        (tmp_path / expected["declaration"]["inputs"][role][0]["path"]).write_bytes(b"changed")
    elif attack == "producer":
        receipt["declaration"]["generated_producers"][0]["producer"]["path"] = "wrong"
    elif attack == "missing-input-role":
        del expected["declaration"]["inputs"]["tool_files"]
    elif attack == "missing-generated-producer":
        expected["declaration"]["generated_producers"] = []
        receipt["declaration"]["generated_producers"] = []
    elif attack == "stale-format":
        receipt["format"] = "uarch-component-build-receipt/1"
    elif attack == "missing-artifact":
        (tmp_path / receipt["executable"]["path"]).unlink()
    elif attack == "wrong-executable":
        (tmp_path / receipt["executable"]["path"]).write_bytes(b"wrong executable")
    elif attack == "wrong-image":
        receipt["declaration"]["image_digest"] = "sha256:" + "d" * 64
    elif attack == "wrong-command":
        receipt["declaration"]["argv"].append("--release")
    elif attack == "extra-environment":
        receipt["declaration"]["environment"]["RUSTFLAGS"] = "different"
    elif attack == "nonzero":
        receipt["exit_code"] = 1
    elif attack == "timeout":
        receipt["ended_monotonic"] = 602.0
        receipt["timed_out"] = True
    elif attack == "incomplete":
        receipt["completed"] = False
    elif attack == "resource":
        receipt["resource_failure"] = "memory"
    elif attack == "missing-log":
        (tmp_path / "stderr").unlink()
    elif attack == "truncated":
        receipt["streams"]["stderr"]["truncated"] = True
    elif attack == "wrong-length":
        receipt["streams"]["stderr"]["observed_bytes"] += 1
    elif attack == "prior-target":
        receipt["target_before"] = ["prior-cargo-output"]
    else:
        rows = [json.loads(line) for line in (tmp_path / "stdout").read_bytes().splitlines()]
        if attack == "missing-completion":
            rows.pop()
        elif attack == "failed-completion":
            rows[-1]["success"] = False
        elif attack == "wrong-cargo-artifact":
            rows[-2]["executable"] = "/target/other"
        elif attack == "fresh-artifact":
            rows[-2]["fresh"] = True
        data = b"\n".join(json.dumps(row).encode() for row in rows) + b"\n"
        receipt["streams"]["stdout"] = dict(
            bind(tmp_path, "stdout", data),
            observed_bytes=len(data),
            retained_bytes=len(data),
            truncated=False,
        )
    with pytest.raises((ValueError, FileNotFoundError)):
        builds.consume_build(tmp_path, receipt, expected)


def test_rebuild_comparison_is_separate_and_mode_scoped(tmp_path: Path) -> None:
    expected, receipt = fixture(tmp_path / "one")
    a = builds.consume_build(tmp_path / "one", receipt, expected)
    expected, receipt = fixture(tmp_path / "two")
    receipt["output_root_id"] = "d" * 64
    b = builds.consume_build(tmp_path / "two", receipt, expected)
    assert builds.compare_rebuilds(a, b)["binary_equal"]
    with pytest.raises(ValueError, match="distinct fresh"):
        builds.compare_rebuilds(a, a)
    changed = copy.deepcopy(b)
    changed["executable_sha256"] = "sha256:" + "e" * 64
    assert not builds.compare_rebuilds(a, changed)["binary_equal"]
    changed = copy.deepcopy(b)
    changed["mode"] = "release"
    with pytest.raises(ValueError, match="same declared mode"):
        builds.compare_rebuilds(a, changed)
