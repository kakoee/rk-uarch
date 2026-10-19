"""Proposed ordinary-image EOF adapter. No default-route installation or authority.

The existing session gates the public callable. Private data-core tests may inject
synthetic transports; those are never public execution or runtime-entry evidence.
"""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256, strict_json_loads
from uarch_contract.mapped import MappedEngineResult

from native.tools.component_container_guard import run_container
from validation.component.runtime_campaign import POLICY, helpers

from .component_host import ComponentSession, _PreparedComponent
from .component_records import IMAGE
from .component_runner import _consume, _request
from .host import _require
from .runner import OperationalFailure


def _save(path: Path, value: Any) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(canonical_json(value))
    temporary.replace(path)


def exchange_image(
    prepared: _PreparedComponent,
    raw: bytes,
    evidence_root: Path,
    *,
    timeout_s: float | None = None,
    slot: dict[str, Any] | None = None,
    admitted: dict[str, Any] | None = None,
) -> tuple[bytes, bytes, int, dict[str, Any]]:
    """Private transport core, also used by the unapplied D3 successor.

    Retain bounded observed streams before raising or invoking a result consumer.
    Caller must independently admit raw bytes; this function creates no authority.
    """
    prepared.refresh()
    budget = prepared.payload.budget
    _require(len(raw) <= budget.stdin_bytes, "image stdin bound")
    timeout: float = min(budget.timeout_s, POLICY["per_call_seconds"])
    if timeout_s is not None:
        timeout = min(timeout_s, timeout)
    _require(timeout > 0, "image deadline exhausted")
    root = evidence_root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / "raw_input").write_bytes(raw)
    selected = next(x for x in prepared.payload.executables if x.mode == prepared.mode)
    executable = root / "engine"
    with prepared.executable() as fd, os.fdopen(os.dup(fd), "rb") as source:
        with executable.open("xb") as target:
            shutil.copyfileobj(source, target)
    executable.chmod(0o555)
    _require(sha256(executable.read_bytes()) == selected.executable.byte_hash, "image executable")
    # Same hash-checked resource arithmetic as the reviewed private harness; no override.
    resources = helpers()["discover"](POLICY, 1)
    _require(resources["workers"] >= 1, "image resource budget")
    started = time.monotonic()
    args = [
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "1g",
        "--cpus",
        "1",
        "--ulimit",
        "nofile=256:256",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=bind,src={executable},dst=/engine,readonly",
        "--entrypoint",
        "/usr/bin/env",
        IMAGE,
        "-i",
        "/engine",
        "--protocol",
        "uarch-engine/3",
    ]
    record: dict[str, Any] = {
        "format": "component-eof-attempt/1",
        "transport_kind": "ordinary-eof",
        "slot": slot,
        "admitted": admitted,
        "engine": prepared.payload.engine.model_dump(mode="json"),
        "image": IMAGE,
        "mode": prepared.mode,
        "payload_byte_hash": prepared.payload_file.byte_hash,
        "executable_byte_hash": selected.executable.byte_hash,
        "raw_input": {"path": "raw_input", "byte_hash": sha256(raw), "bytes": len(raw)},
        "runtime_entries": None,
        "entry_evidence": "unobserved in ordinary EOF transport",
        "transport_complete": False,
        "validation_passed": False,
        "status": None,
        "cleanup": None,
        "argv": args,
        "timeout_s": timeout,
        "resources": resources,
        "started_monotonic": started,
        "deadline_monotonic": started + timeout,
        "failure_stage": "transport",
        "guardian_records": "container/",
    }
    _save(root / "attempt.json", record)
    error = None
    try:
        cleanup = run_container(
            root / "container",
            args,
            timeout=timeout,
            cap=budget.stdout_bytes,
            stderr_cap=budget.stderr_bytes,
            stdin_bytes=raw,
        )
        record["cleanup"] = cleanup
        record["status"] = cleanup["exit_code"]
        record["container_id"] = cleanup["container_id"]
        record["process_identity"] = "docker:" + cleanup["container_id"] + ":pid1"
        record["transport_complete"] = cleanup["reason"] == "completed"
    except Exception as failure:
        error = failure
        record["transport_error"] = repr(failure)
    streams = {}
    for name, cap in (("stdout", budget.stdout_bytes), ("stderr", budget.stderr_bytes)):
        path = root / "container" / name
        if not path.exists():
            record[name] = None  # Missing evidence is not an invented empty stream.
            continue
        with path.open("rb") as source:
            data = source.read(cap + 1)
        size = path.stat().st_size
        kept = data[:cap]
        (root / name).write_bytes(kept)
        streams[name] = kept
        record[name] = {
            "path": name,
            "byte_hash": sha256(kept),
            "observed_bytes": size,
            "retained_bytes": len(kept),
            "truncated": size > cap,
        }
        if size > cap:
            record["transport_complete"] = False
    record["ended_monotonic"] = time.monotonic()
    record["deadline_exceeded"] = record["ended_monotonic"] > record["deadline_monotonic"]
    if record["deadline_exceeded"]:
        record["transport_complete"] = False
    _save(root / "attempt.json", record)
    if (
        error
        or not record["transport_complete"]
        or len(streams) != 2
        or type(record["status"]) is not int
    ):
        raise OperationalFailure("image transport incomplete; retained " + str(root)) from error
    return streams["stdout"], streams["stderr"], record["status"], record


def _run_prepared_image(
    saved: Path,
    prepared: _PreparedComponent,
    evidence_root: Path,
    *,
    timeout_s: float | None = None,
    repetition: int = 0,
    replay: dict[str, Any] | None = None,
) -> tuple[MappedEngineResult, dict[str, Any]]:
    _require(type(repetition) is int and 0 <= repetition < 3, "exact repetition")
    raw, job = _request(prepared, saved)
    slot = {
        "phase": "initial" if replay is None else "replay",
        "mode": prepared.mode,
        "repetition": repetition,
    }
    admitted = {
        "case_id": job["admission"]["case_id"],
        "raw_input_sha256": sha256(raw).removeprefix("sha256:"),
        "job_hash": job["job_hash"],
        "engine": prepared.payload.engine.model_dump(mode="json"),
    }
    stdout, stderr, status, record = exchange_image(
        prepared, raw, evidence_root, timeout_s=timeout_s, slot=slot, admitted=admitted
    )
    record["replay_descriptor"] = replay
    record["failure_stage"] = "consumer"
    try:
        result = _consume(prepared, job, stdout, stderr, status)
        record["validation_passed"] = True
        record["failure_stage"] = None
    except Exception as error:
        record["validation_error"] = repr(error)
        raise
    finally:
        _save(evidence_root / "attempt.json", record)
    return result, record


def run_component_image(
    saved: Path, *, session: ComponentSession, evidence_root: Path, repetition: int = 0
) -> tuple[MappedEngineResult, dict[str, Any]]:
    _require(isinstance(session, ComponentSession), "independent component authority required")
    prepared = session.claim()
    # Session identity/budget still comes exclusively from the existing authority gate.
    remaining = session._deadline - time.monotonic()
    result = _run_prepared_image(
        saved, prepared, evidence_root, timeout_s=remaining, repetition=repetition
    )
    try:
        session.check()
        _require(time.monotonic() <= session._deadline, "component session deadline exhausted")
    except Exception as error:
        result[1].update(
            validation_passed=False,
            failure_stage="session-finalization",
            finalization_error=repr(error),
        )
        _save(evidence_root / "attempt.json", result[1])
        raise
    return result


def saved_input_from_attempt(
    receipt: Path, expected_receipt_hash: str, prepared: _PreparedComponent
) -> Path:
    """Bound saved-input readback; B owns six-receipt campaign admission above this seam."""
    prepared.refresh()
    _require(receipt.stat().st_size <= 1024**2, "saved input receipt limit")
    raw = receipt.read_bytes()
    _require(sha256(raw) == expected_receipt_hash, "saved input receipt hash")
    value = strict_json_loads(raw)
    selected = next(x for x in prepared.payload.executables if x.mode == prepared.mode)
    _require(
        value["status"] == 0
        and value["engine"] == prepared.payload.engine.model_dump(mode="json")
        and value["image"] == IMAGE
        and value["executable_byte_hash"] == selected.executable.byte_hash
        and value["mode"] == prepared.mode
        and value["runtime_entries"] is None
        and value["format"] == "component-eof-attempt/1"
        and value["validation_passed"] is True
        and value["transport_complete"] is True
        and value["payload_byte_hash"] == prepared.payload_file.byte_hash,
        "saved input validated receipt",
    )
    name: str = value["raw_input"]["path"]
    path = receipt.parent / name
    _require(
        not path.is_symlink() and path.resolve().is_relative_to(receipt.parent.resolve()),
        "saved input path",
    )
    _require(path.stat().st_size <= prepared.payload.budget.stdin_bytes, "saved input limit")
    data = path.read_bytes()
    _require(
        sha256(data) == value["raw_input"]["byte_hash"]
        and len(data) == value["raw_input"]["bytes"],
        "saved input binding",
    )
    _request(prepared, path)
    return path


def admit_image_replay(
    references: list[tuple[Path, str]], prepared: _PreparedComponent
) -> tuple[Path, dict[str, Any]]:
    """Reopen and independently consume six bound initial receipts. No producer calls.

    Hashes are the campaign's frozen initial references, not acceptance/authority.
    This helper does not run the historical campaign or replace B's group gate.
    """
    _require(
        len(references) == 6 and len({p.resolve() for p, _ in references}) == 6,
        "six distinct initial receipt references required",
    )
    slots, processes, inputs, outputs = set(), set(), set(), set()
    retained = []
    saved = None
    for receipt, pin in references:
        _require(receipt.stat().st_size <= 1024**2, "saved input receipt limit")
        raw_receipt = receipt.read_bytes()
        _require(sha256(raw_receipt) == pin, "saved input receipt hash")
        value = strict_json_loads(raw_receipt)
        slot = value["slot"]
        _require(
            slot["phase"] == "initial" and slot["mode"] == value["mode"],
            "initial replay source required",
        )
        mode = slot["mode"]
        _require(mode in ("debug", "release"), "saved initial mode")
        current = replace(prepared, mode=mode)
        saved = saved_input_from_attempt(receipt, pin, current)
        data, job = _request(current, saved)
        streams = []
        for name in ("stdout", "stderr"):
            binding = value[name]
            path = receipt.parent / name
            _require(not path.is_symlink() and binding["path"] == name, "saved output path")
            cap = (
                current.payload.budget.stdout_bytes
                if name == "stdout"
                else current.payload.budget.stderr_bytes
            )
            _require(path.stat().st_size <= cap, "saved output cap")
            raw = path.read_bytes()
            _require(
                not binding["truncated"]
                and sha256(raw) == binding["byte_hash"]
                and len(raw) == binding["retained_bytes"] == binding["observed_bytes"],
                "saved output binding",
            )
            streams.append(raw)
        _consume(current, job, streams[0], streams[1], value["status"])
        expected = {
            "case_id": job["admission"]["case_id"],
            "raw_input_sha256": sha256(data).removeprefix("sha256:"),
            "job_hash": job["job_hash"],
            "engine": job["engine"],
        }
        _require(value["admitted"] == expected, "saved initial admitted anchor")
        cleanup = value["cleanup"]
        _require(
            cleanup["stopped"] is True
            and cleanup["removed"] is True
            and cleanup["container_id"] == value["container_id"],
            "saved cleanup",
        )
        slots.add((mode, slot["repetition"]))
        processes.add(value["process_identity"])
        inputs.add(data)
        outputs.add(tuple(streams))
        retained.append({"path": str(receipt.resolve()), "byte_hash": pin})
    _require(
        slots == {(m, r) for m in ("debug", "release") for r in range(3)}
        and len(processes) == 6
        and len(inputs) == len(outputs) == 1,
        "six initial slots/processes and byte equality",
    )
    assert saved is not None
    return saved, {
        "phase": "replay",
        "initial_receipts": retained,
        "raw_input_byte_hash": sha256(next(iter(inputs))),
    }


def replay_component_image(
    initial_receipts: list[tuple[Path, str]],
    *,
    session: ComponentSession,
    evidence_root: Path,
    repetition: int,
) -> tuple[MappedEngineResult, dict[str, Any]]:
    _require(isinstance(session, ComponentSession), "independent component authority required")
    prepared = session.claim()
    saved, descriptor = admit_image_replay(initial_receipts, prepared)
    result = _run_prepared_image(
        saved,
        prepared,
        evidence_root,
        timeout_s=session._deadline - time.monotonic(),
        repetition=repetition,
        replay=descriptor,
    )
    try:
        session.check()
        _require(time.monotonic() <= session._deadline, "component session deadline exhausted")
    except Exception as error:
        result[1].update(
            validation_passed=False,
            failure_stage="session-finalization",
            finalization_error=repr(error),
        )
        _save(evidence_root / "attempt.json", result[1])
        raise
    return result
