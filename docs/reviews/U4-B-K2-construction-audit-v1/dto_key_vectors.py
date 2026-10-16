"""Independent follow-up for public HardwareSpec float-key normalization."""

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
    original = base["workload_closure"]["hardware_spec"]["energy"]["voltage_ratio"]
    assert list(original) == ["1.0"]
    rows = []
    for key in [
        "1.0",
        "1",
        "1e0",
        " 1.0 ",
        "\t1.0\n",
        "1_0e-1",
        "+1.0",
        "0",
        "-1",
        "nan",
        "inf",
        "1e999",
        "1.0x",
    ]:
        raw = copy.deepcopy(base)
        raw["workload_closure"]["hardware_spec"]["energy"]["voltage_ratio"] = {
            key: copy.deepcopy(original["1.0"])
        }
        text = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
        try:
            valid = loads_fixed_delay_job(text, **auth)
        except ValueError as error:
            row = dict(id=repr(key), input=text, expected="refuse", python_error=str(error))
        else:
            row = dict(
                id=repr(key), input=text, expected="accept", normalized=canonical_json(valid)
            )
        rows.append(row)
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    return dict(
        count=len(rows),
        accepted=sum(r["expected"] == "accept" for r in rows),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        cases=[dict(id=r["id"], expected=r["expected"]) for r in rows],
    )
