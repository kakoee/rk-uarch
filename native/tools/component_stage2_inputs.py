"""Prospective Stage 2 negative bindings. No execution, authority or historical edits."""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


def transition_negatives(new: Path, old: Path, expected: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for prior in expected["rows"]:
        name = prior["case_id"]
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("finite case filename")
        relative = Path("private-component/jobs") / (name + ".json")
        before_raw, after_raw = (old / relative).read_bytes(), (new / relative).read_bytes()
        before, after = json.loads(before_raw), json.loads(after_raw)
        if (
            hashlib.sha256(before_raw).hexdigest() != prior["input_sha256"]
            or before["job_hash"] != prior["job_hash"]
            or before["engine"] != prior["engine"]
        ):
            raise ValueError("historical independently expected input")
        if {k: v for k, v in before.items() if k not in ("engine", "job_hash")} != {
            k: v for k, v in after.items() if k not in ("engine", "job_hash")
        }:
            raise ValueError("identity-only transition required")
        guard = prior["native_guard_source"]
        if hashlib.sha256((new / guard["path"]).read_bytes()).hexdigest() != guard["sha256"]:
            raise ValueError("changed native guard needs new independent expectations")
        row = deepcopy(prior)
        row.update(
            historical_expectation=deepcopy(prior),
            input_sha256=hashlib.sha256(after_raw).hexdigest(),
            job_hash=after["job_hash"],
            engine=after["engine"],
            transition_scope=(
                "Prospective identity-only input transition; all observations inherited"
            ),
        )
        rows.append(row)
    return {"format": "component-negative-expectations/1", "rows": rows}


def main() -> None:
    new, old, expectations = map(Path, sys.argv[1:])
    if not new.resolve().is_relative_to(Path("/tmp")) or new.resolve() == old.resolve():
        raise ValueError("new private export required")
    output = new / "private-component/negative-expectations.json"
    value = transition_negatives(new, old, json.loads(expectations.read_bytes()))
    with output.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def acceptance_record(
    prepared: Any, summary: dict[str, Any], negatives: dict[str, Any]
) -> dict[str, Any]:
    """Freeze caller-owned expectations before constructing/invoking the adapter.

    Positive identity comes from the prepared payload inventory; negative identity
    comes from the separately reviewed expectation transition, never returned bytes.
    """
    from uarch_contract.hashing import canonical_json, strict_json_loads

    from rkuarch.engines.native.host import _read
    from rkuarch.engines.native.records import FileBinding

    prepared.refresh()
    payload = prepared.payload
    engine = payload.engine.model_dump(mode="json")
    if summary["engine"] != engine:
        raise ValueError("acceptance build engine")
    build = strict_json_loads(_read(prepared.root, payload.build_inputs))
    trust = strict_json_loads(_read(prepared.root, FileBinding.model_validate(build["trust_file"])))
    selection = strict_json_loads(
        _read(prepared.root, FileBinding.model_validate(trust["selection"]))
    )
    inputs = {
        item.case_id: {
            "case_id": item.case_id,
            "raw_input_sha256": item.file.byte_hash.split(":")[1],
            "job_hash": item.job_hash,
            "engine": engine,
        }
        for item in payload.jobs
    }
    expected_negatives = {}
    for row in negatives["rows"]:
        name = row["case_id"]
        if name in inputs or row["engine"] != engine:
            raise ValueError("acceptance negative inventory/engine")
        inputs[name] = {
            "case_id": name,
            "raw_input_sha256": row["input_sha256"],
            "job_hash": row["job_hash"],
            "engine": engine,
        }
        expected_negatives[name] = row
    if set(inputs) != {r["case_id"] for r in selection["rows"]}:
        raise ValueError("acceptance complete selected inventory")
    executables = {}
    for mode in ("debug", "release"):
        record = summary["modes"][mode]
        executable = Path(record["test_executable"])
        actual = hashlib.sha256(executable.read_bytes()).hexdigest()
        if "sha256:" + actual != record["test_executable_byte_hash"]:
            raise ValueError("acceptance actual executable bytes")
        executables[mode] = actual
    return {
        "format": "component-private-acceptance/1",
        "evidence_kind": "private-synthetic-test",
        "selection_sha256": hashlib.sha256(canonical_json(selection).encode()).hexdigest(),
        "execution_binding": prepared.payload_file.byte_hash,
        "inputs": inputs,
        "negatives": expected_negatives,
        "source": payload.consumers.import_root,
        "pins": prepared.consumer_pins,
        "observation_contract": strict_json_loads(
            _read(prepared.root, payload.consumers.observation_contract)
        ),
        "executables": executables,
        "witness_kind": "cfg(test) file-probe; synthetic anchors",
    }


if __name__ == "__main__":
    main()
