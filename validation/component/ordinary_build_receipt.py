"""Ordinary build receipt orchestration with an explicitly supplied bounded transport.

No default process/container launcher exists here. The transport must enforce its
own deadline/output/resource bounds and preserve its ownership ledger. A receipt
is observation data, never a human decision or startup/runtime authority.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256

from validation.component.checks import need
from validation.component.ordinary_build_acceptance import RECEIPT, _declaration


def record_attempt(
    root: Path,
    declaration: dict[str, Any],
    limits: dict[str, int],
    transport: Callable[[Path, dict[str, Any]], dict[str, Any]],
    *,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Create a fresh output directory and retain success/failure after transport.

    This is not a standalone hardened transport. Existing guardian cleanup and
    hard cancellation remain the runner's obligation; elapsed checks here do not
    stop a blocked callback or authenticate its reported process status.
    """
    root = root.resolve(strict=True)
    _declaration(root, declaration)
    need(set(limits) == {"timeout_s", "stdout_bytes", "stderr_bytes"}, "exact build limits")
    need(
        type(limits["timeout_s"]) is int and 0 < limits["timeout_s"] <= 600, "bounded build timeout"
    )
    need(
        all(
            type(limits[k]) is int and 0 < limits[k] <= 64 * 1024**2
            for k in ("stdout_bytes", "stderr_bytes")
        ),
        "bounded build output",
    )
    for name in ("stdout", "stderr", "ordinary-build-receipt.json", "transport-failure.json"):
        need(not (root / name).exists(), "fresh build receipt path")
    # Exclusive creation, never an empty-looking reused target supplied by caller.
    (root / "outputs").mkdir(exist_ok=False)
    (root / "target").mkdir(exist_ok=False)
    identifier = uuid.uuid4().hex + uuid.uuid4().hex
    started = clock()
    status: dict[str, Any] = {
        "exit_code": None,
        "completed": False,
        "timed_out": False,
        "resource_failure": None,
        "observed_bytes": {},
        "stream_complete": {},
        "stream_truncated": {},
    }
    try:
        # Copy to prevent transport mutation from rewriting the retained declaration.
        spec = json.loads(
            canonical_json(
                {
                    "argv": declaration["argv"],
                    "environment": declaration["environment"],
                    "limits": limits,
                }
            )
        )
        observed = transport(root, spec)
        need(
            isinstance(observed, dict) and set(observed) == set(status),
            "complete observed transport status",
        )
        status = observed
    except Exception as error:
        failure = {"type": type(error).__name__, "message": str(error)[:4096]}
        (root / "transport-failure.json").write_text(canonical_json(failure))
    ended = clock()
    streams: dict[str, dict[str, Any]] = {}
    for name in ("stdout", "stderr"):
        path = root / name
        if not path.is_file() or path.is_symlink():
            streams[name] = {"missing_or_unsafe": True}
            continue
        size = path.stat().st_size
        if size > limits[name + "_bytes"]:
            streams[name] = {"over_limit": True, "retained_bytes": size}
            continue
        raw = path.read_bytes()
        streams[name] = {
            "path": name,
            "byte_hash": sha256(raw),
            "retained_bytes": len(raw),
            "observed_bytes": status.get("observed_bytes", {}).get(name),
            "truncated": (
                status.get("stream_truncated", {}).get(name)
                if status.get("stream_complete", {}).get(name) is True
                else None
            ),
        }
    artifact = root / "outputs/uarch-engine"
    executable = {"path": "outputs/uarch-engine", "byte_hash": None}
    if (
        artifact.is_file()
        and not artifact.is_symlink()
        and artifact.stat().st_size <= 256 * 1024**2
    ):
        executable["byte_hash"] = sha256(artifact.read_bytes())
    receipt = {
        "format": RECEIPT,
        "declaration": declaration,
        "output_root_id": identifier,
        "target_before": [],
        "started_monotonic": started,
        "ended_monotonic": ended,
        "deadline_monotonic": started + limits["timeout_s"],
        "exit_code": status.get("exit_code"),
        "completed": status.get("completed") is True,
        "timed_out": status.get("timed_out") is True or ended > started + limits["timeout_s"],
        "resource_failure": status.get("resource_failure"),
        "streams": streams,
        "executable": executable,
        "input_observations": declaration["inputs"],
    }
    (root / "ordinary-build-receipt.json").write_text(canonical_json(receipt))
    return receipt
