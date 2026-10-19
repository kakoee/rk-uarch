"""Offline finite ordinary-build evidence; no launch, reviewer approval or authority.

Expected declarations must be frozen independently by the versioned review consumer.
This module checks retained bytes and joins, not authenticity of their producer, an
exhaustive dynamic read set, startup assurance or simulation correctness.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256

from validation.component.checks import need
from validation.component.ordinary_eof_acceptance import read_bound

EXPECTATION = "component-ordinary-build-expectation/1"
RECEIPT = "component-ordinary-build-receipt/1"
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
INPUT_ROLES = (
    "source_archive",
    "source_files",
    "build_inputs",
    "tool_inputs",
    "tool_files",
    "dependency_lock",
    "cache_manifest",
    "cache_files",
    "generated_inputs",
    "producers",
    "consumers",
)
WARNING_POLICY = "retain-compiler-diagnostics;required-checks-separate"
MAX_INPUT_BYTES = 256 * 1024**2


def _binding(root: Path, value: dict[str, Any], cap: int = MAX_INPUT_BYTES) -> bytes:
    need(set(value) == {"path", "byte_hash"}, "exact input binding")
    need(
        isinstance(value["byte_hash"], str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value["byte_hash"]) is not None,
        "input digest",
    )
    return read_bound(root, value["path"], value["byte_hash"], cap)


def _declaration(root: Path, value: dict[str, Any]) -> None:
    need(
        set(value)
        == {
            "source_commit",
            "source_tree",
            "mode",
            "image_digest",
            "argv",
            "environment",
            "inputs",
            "generated_producers",
            "cargo_artifact",
            "warning_policy",
        },
        "complete ordinary build declaration",
    )
    need(
        all(
            isinstance(value[name], str) and re.fullmatch(r"[0-9a-f]{40}", value[name]) is not None
            for name in ("source_commit", "source_tree")
        ),
        "source commit/tree identity",
    )
    need(
        value["mode"] in ("debug", "release") and value["image_digest"] == IMAGE,
        "mode/image identity",
    )
    argv, environment = value["argv"], value["environment"]
    need(
        isinstance(argv, list)
        and bool(argv)
        and all(isinstance(v, str) and v and "\0" not in v for v in argv),
        "complete build argv",
    )
    need(
        isinstance(environment, dict)
        and bool(environment)
        and all(
            isinstance(k, str)
            and k
            and "=" not in k
            and "\0" not in k
            and isinstance(v, str)
            and "\0" not in v
            for k, v in environment.items()
        ),
        "explicit build environment",
    )
    need(
        value["warning_policy"] == WARNING_POLICY,
        "ordinary warning policy; required checks separate",
    )
    need(
        value["cargo_artifact"] == f"/target/{value['mode']}/uarch-engine",
        "exact Cargo artifact path",
    )
    inputs = value["inputs"]
    need(set(inputs) == set(INPUT_ROLES), "complete provenance roles")
    all_bindings = []
    for role in INPUT_ROLES:
        rows = inputs[role]
        need(isinstance(rows, list) and bool(rows), "nonempty mandatory provenance")
        paths = [row["path"] for row in rows]
        need(paths == sorted(set(paths)), "unique sorted provenance paths")
        for row in rows:
            _binding(root, row)
            all_bindings.append(row)
    producers = inputs["producers"]
    need(
        all(p in inputs["source_files"] + inputs["tool_files"] for p in producers),
        "producer source/tool closure",
    )
    generated = value["generated_producers"]
    need(
        isinstance(generated, list)
        and [row["output"] for row in generated] == inputs["generated_inputs"],
        "complete generated producer joins",
    )
    for row in generated:
        need(
            set(row) == {"output", "producer", "inputs"}
            and row["producer"] in producers
            and bool(row["inputs"]),
            "generated producer binding",
        )
        need(
            all(x in all_bindings and x not in inputs["generated_inputs"] for x in row["inputs"]),
            "acyclic declared generator inputs",
        )


def _cargo(stdout: bytes, expected_artifact: str) -> None:
    need(bool(stdout) and stdout.endswith(b"\n"), "complete Cargo output")
    try:
        rows = [json.loads(line) for line in stdout.splitlines()]
    except (ValueError, UnicodeError) as error:
        raise ValueError("complete Cargo JSON records") from error
    need(all(isinstance(row, dict) for row in rows), "Cargo object records")
    need(
        rows[-1].get("reason") == "build-finished" and rows[-1].get("success") is True,
        "successful Cargo completion",
    )
    need(
        sum(row.get("reason") == "build-finished" for row in rows) == 1,
        "unique terminal Cargo completion",
    )
    selected = []
    for row in rows[:-1]:
        reason = row.get("reason")
        need(
            reason in ("compiler-artifact", "compiler-message", "build-script-executed"),
            "known ordinary Cargo record",
        )
        if reason == "compiler-message":
            need(
                isinstance(row.get("message"), dict)
                and row["message"].get("level") in ("warning", "note", "help", "failure-note"),
                "ordinary compiler diagnostic; errors refuse",
            )
        if reason == "compiler-artifact" and row.get("executable") == expected_artifact:
            selected.append(row)
    need(len(selected) == 1, "unique declared executable artifact")
    row = selected[0]
    need(
        row.get("target", {}).get("name") == "uarch-engine"
        and row["target"].get("kind") == ["bin"]
        and row.get("fresh") is False,
        "fresh production binary artifact",
    )


def consume_build(root: Path, receipt: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Inspect bytes, status and finite joins; never establish runtime authority."""
    need(expected.get("format") == EXPECTATION, "versioned independent build expectation")
    need(
        set(expected)
        == {"format", "declaration", "executable", "timeout_s", "stdout_bytes", "stderr_bytes"},
        "complete independent build expectation",
    )
    need(receipt.get("format") == RECEIPT, "versioned ordinary build receipt")
    need(
        set(receipt)
        == {
            "format",
            "declaration",
            "output_root_id",
            "target_before",
            "started_monotonic",
            "ended_monotonic",
            "deadline_monotonic",
            "exit_code",
            "completed",
            "timed_out",
            "resource_failure",
            "streams",
            "executable",
            "input_observations",
        },
        "complete ordinary build receipt",
    )
    need(receipt["declaration"] == expected["declaration"], "independent declaration equality")
    _declaration(root, expected["declaration"])
    need(
        receipt["input_observations"] == expected["declaration"]["inputs"],
        "observed mandatory inputs",
    )
    need(
        isinstance(receipt["output_root_id"], str)
        and re.fullmatch(r"[0-9a-f]{64}", receipt["output_root_id"]) is not None
        and receipt["target_before"] == [],
        "fresh output identity and empty target observation",
    )
    start, end, deadline = (
        receipt[name] for name in ("started_monotonic", "ended_monotonic", "deadline_monotonic")
    )
    timeout = expected["timeout_s"]
    need(
        all(type(x) in (int, float) and math.isfinite(x) for x in (start, end, deadline, timeout))
        and 0 < timeout <= 600
        and 0 <= start <= end <= deadline
        and deadline == start + timeout,
        "bounded observed build deadline",
    )
    need(
        type(receipt["exit_code"]) is int
        and receipt["exit_code"] == 0
        and receipt["completed"] is True
        and receipt["timed_out"] is False
        and receipt["resource_failure"] is None,
        "successful complete ordinary build status",
    )
    need(set(receipt["streams"]) == {"stdout", "stderr"}, "complete ordinary logs")
    data = {}
    for name in ("stdout", "stderr"):
        cap = expected[name + "_bytes"]
        stream = receipt["streams"][name]
        need(type(cap) is int and 0 < cap <= 64 * 1024**2, "bounded log cap")
        need(
            set(stream) == {"path", "byte_hash", "observed_bytes", "retained_bytes", "truncated"}
            and stream["path"] == name,
            "exact retained log",
        )
        data[name] = read_bound(root, name, stream["byte_hash"], cap)
        need(
            stream["truncated"] is False
            and type(stream["observed_bytes"]) is int
            and type(stream["retained_bytes"]) is int
            and len(data[name]) == stream["observed_bytes"] == stream["retained_bytes"],
            "complete observed log bytes",
        )
    _cargo(data["stdout"], expected["declaration"]["cargo_artifact"])
    need(receipt["executable"] == expected["executable"], "declared executable binding")
    # Separate actual executable check enables an unmasked targeted fault control.
    artifact = expected["executable"]
    path = root / artifact["path"]
    need(
        set(artifact) == {"path", "byte_hash"} and artifact["path"] == "outputs/uarch-engine",
        "retained executable path",
    )
    need(
        path.is_file()
        and not path.is_symlink()
        and not path.parent.is_symlink()
        and not root.is_symlink()
        and 0 < path.stat().st_size <= MAX_INPUT_BYTES,
        "bounded regular executable",
    )
    binary = path.read_bytes()
    need(sha256(binary) == artifact["byte_hash"], "actual executable digest")
    required = {}
    for rows in expected["declaration"]["inputs"].values():
        for item in rows:
            required[item["path"]] = item["byte_hash"]
    for name in ("stdout", "stderr"):
        required[name] = receipt["streams"][name]["byte_hash"]
    required[artifact["path"]] = artifact["byte_hash"]
    return {
        "required_files": [
            {"path": path, "byte_hash": pin} for path, pin in sorted(required.items())
        ],
        "format": "component-ordinary-build-consumption/1",
        "receipt_sha256": sha256(canonical_json(receipt).encode()),
        "declaration_sha256": sha256(canonical_json(expected["declaration"]).encode()),
        "mode": expected["declaration"]["mode"],
        "output_root_id": receipt["output_root_id"],
        "retained_root": str(root.resolve()),
        "executable_sha256": artifact["byte_hash"],
        "clean_build_success": True,
        "binary_reproducibility": "not-assessed",
        "simulation_determinism": "not-assessed",
        "dynamic_read_coverage": "not-assessed",
        "startup_assurance": "not-assessed",
        "required_warning_checks": "separate-review-obligation",
        "authority": None,
    }


def compare_rebuilds(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Compare two consumed same-mode builds; a mismatch is reported, never normalized."""
    need(
        all(
            x.get("format") == "component-ordinary-build-consumption/1"
            and x.get("clean_build_success") is True
            for x in (first, second)
        ),
        "two consumed clean builds",
    )
    need(
        first["mode"] == second["mode"]
        and first["declaration_sha256"] == second["declaration_sha256"],
        "same declared mode and inputs",
    )
    need(
        first["output_root_id"] != second["output_root_id"]
        and first["retained_root"] != second["retained_root"],
        "distinct fresh build output roots",
    )
    return {
        "format": "component-binary-rebuild-comparison/1",
        "mode": first["mode"],
        "receipt_sha256": [first["receipt_sha256"], second["receipt_sha256"]],
        "binary_equal": first["executable_sha256"] == second["executable_sha256"],
        "simulation_determinism": "not-assessed",
        "startup_assurance": "not-assessed",
        "authority": None,
    }
