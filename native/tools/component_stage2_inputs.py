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


if __name__ == "__main__":
    main()
