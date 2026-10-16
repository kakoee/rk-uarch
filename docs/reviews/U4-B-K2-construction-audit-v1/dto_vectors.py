"""Freeze independent full-carrier normalization/refusal vectors, no mapped execution."""

import copy
import hashlib
import json
from pathlib import Path

from uarch_contract.hashing import canonical_json
from uarch_contract.mapped import NativeEngineIdentity

from rkuarch.workload.mapped import loads_fixed_delay_job


def prepare(root, output):
    root, output = Path(root), Path(output)
    assert output.is_relative_to(Path("/tmp")) and not output.exists()
    base = json.loads(
        (root / "native/crates/uarch-engine/testdata/synthetic-kernel-job.json").read_bytes()
    )
    auth = dict(
        trusted_profile_hash=base["profile"]["profile_hash"],
        trusted_registry_hash=base["registry"]["registry_hash"],
        expected_engine=NativeEngineIdentity.model_validate(base["engine"]),
    )
    cases = [("baseline", None, None)]
    for pointer, values in [
        (
            "/workload_closure/hardware_spec/clock_domains/core/scales_with_core",
            [True, 1, 1.0, False, 0, "true"],
        ),
        (
            "/workload_closure/hardware_spec/clock_domains/noc/scales_with_core",
            [False, 0, 0.0, "false", "OFF", " false ", 2],
        ),
        ("/workload_closure/hardware_spec/memory/controllers/0/attach/0", [0, 0.0, True, "0", -1]),
        ("/hardware/leaves/0/path", ["", " ", "\u001c"]),
        ("/seed", [0, 0.0, True, "0", -1, 2**64]),
    ]:
        for i, value in enumerate(values):
            cases.append((pointer + ":" + str(i), pointer, value))
    rows = []
    for name, pointer, value in cases:
        raw = copy.deepcopy(base)
        if pointer:
            parent = raw
            parts = pointer.split("/")[1:]
            for part in parts[:-1]:
                parent = parent[int(part)] if isinstance(parent, list) else parent[part]
            key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
            parent[key] = value
        text = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
        try:
            valid = loads_fixed_delay_job(text, **auth)
        except ValueError as error:
            row = dict(id=name, input=text, expected="refuse", python_error=str(error))
        else:
            row = dict(id=name, input=text, expected="accept", normalized=canonical_json(valid))
        rows.append(row)
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    return dict(
        count=len(rows),
        accepted=sum(r["expected"] == "accept" for r in rows),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        cases=[dict(id=r["id"], expected=r["expected"]) for r in rows],
    )
