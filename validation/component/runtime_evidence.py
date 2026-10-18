"""Private receipt consumption and durable replay. No invocation or authority creation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json

from validation.component.checks import need
from validation.component.runtime_checks import CHECKER, consume_case, verify_sources

STREAM_CAP = 64 * 1024**2


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse(raw: bytes) -> Any:
    need(isinstance(raw, bytes) and len(raw) <= STREAM_CAP, "bounded result bytes")
    value = json.loads(raw)
    need(canonical_json(value).encode() == raw, "canonical complete envelope bytes")
    return value


def exact_refusal(raw: bytes, expected: dict[str, Any]) -> None:
    value = parse(raw)
    need(
        isinstance(value, dict) and set(value) == {"code", "message", "pointer"}, "refusal envelope"
    )
    need(value == expected, "exact intended refusal envelope")


def consume_attempt(
    raw: dict[str, Any], row: dict[str, Any], slot: dict[str, Any], acceptance: dict[str, Any]
) -> str:
    admitted = acceptance["inputs"][row["case_id"]]
    need(digest(raw["raw_input"]) == admitted["raw_input_sha256"], "immutable selected raw input")
    witness = raw["witness"]
    need(isinstance(witness, dict), "saved witness object required")
    positive = row["expected_layer"] == "result"
    semantic = raw["stdout"] if positive else raw["stderr"]
    bindings = dict(
        case_id=slot["case_id"],
        mode=slot["mode"],
        raw_input_sha256=admitted["raw_input_sha256"],
        semantic_output_sha256=digest(semantic),
        executable_sha256=acceptance["executables"][slot["mode"]],
        process_identity=raw["process_identity"],
        transport_complete=True,
    )
    need(all(witness.get(k) == v for k, v in bindings.items()), "execution witness bindings")
    need(type(witness.get("runtime_entries")) is int, "numeric runtime-entry witness")
    need(witness["runtime_entries"] == (1 if positive else 0), "runtime-entry witness population")
    need(witness.get("evidence") == acceptance["witness_kind"], "instrumentation witness kind")
    cleanup = raw["cleanup"]
    need(
        isinstance(cleanup, dict)
        and cleanup.get("verified_stopped") is True
        and bool(cleanup.get("container_id"))
        and cleanup.get("process_identity") == raw["process_identity"],
        "actual cleanup receipt",
    )
    if positive:
        need(raw["status"] == 0 and raw["stderr"] == b"", "success transport envelope")
        job, result = json.loads(raw["raw_input"]), parse(semantic)
        # Both published consumption entry points are required. They share check_v3;
        # executing them twice is not two independently derived oracles.
        verify_sources(Path(acceptance["source"]), acceptance["pins"])
        from rkuarch.engines.native.component_runner import validate_component_response

        validate_component_response(
            raw["stdout"],
            raw["stderr"],
            raw["status"],
            job=job,
            observation_contract=acceptance["observation_contract"],
            admitted=admitted,
        )
        consume_case(
            job,
            result,
            row,
            checker_id=CHECKER,
            source=Path(acceptance["source"]),
            pins=acceptance["pins"],
            expected=acceptance["observation_contract"],
            input_sha256=admitted["raw_input_sha256"],
            raw_input=raw["raw_input"],
            admitted=admitted,
        )
        return "success"
    need(raw["status"] == 2 and raw["stdout"] == b"", "refusal transport envelope")
    exact_refusal(semantic, acceptance["negatives"][row["case_id"]]["envelope"])
    code = row["expected_code"]
    need(isinstance(code, str), "expected refusal code string")
    assert isinstance(code, str)
    return code


def read_bound(root: Path, name: str, pin: str) -> bytes:
    path = root / name
    need(
        path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
        "retained evidence path",
    )
    need(path.stat().st_size <= STREAM_CAP, "bounded saved artifact")
    raw = path.read_bytes()
    need(digest(raw) == pin, "retained evidence hash")
    return raw


def replay_admission(
    root: Path, references: list[dict[str, str]], row: dict[str, Any], acceptance: dict[str, Any]
) -> dict[str, Any]:
    """Read six separately saved initial validations and artifacts; never trust a caller dict."""
    need(len(references) == 6, "complete initial group required")
    records = []
    for ref in references:
        record = json.loads(read_bound(root, ref["path"], ref["sha256"]))
        need(
            record["validation_passed"] is True
            and record["phase"] == "initial"
            and record["case_id"] == row["case_id"]
            and record["execution_binding"] == acceptance["execution_binding"],
            "initial receipt binding",
        )
        raw = {
            key: read_bound(root, record[key + "_blob"], record[key + "_sha256"])
            for key in ("raw_input", "stdout", "stderr")
        }
        raw.update(
            {key: record[key] for key in ("process_identity", "witness", "cleanup", "status")}
        )
        consume_attempt(raw, row, record, acceptance)
        records.append(record)
    need(
        {(r["mode"], r["repetition"]) for r in records}
        == {(mode, rep) for mode in ("debug", "release") for rep in range(3)},
        "initial receipt slots",
    )
    need(len({r["process_identity"] for r in records}) == 6, "initial fresh processes")
    need(
        len({(r["raw_input_sha256"], r["stdout_sha256"], r["stderr_sha256"]) for r in records})
        == 1,
        "initial deterministic artifacts",
    )
    first = records[0]
    return dict(
        saved_input_path=str(root / first["raw_input_blob"]),
        raw_input_sha256=first["raw_input_sha256"],
        initial_receipts=references,
        property="durable verified readback; no second independent oracle",
    )
