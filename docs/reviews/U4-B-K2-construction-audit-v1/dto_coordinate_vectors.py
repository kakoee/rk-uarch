"""Full-DTo integer-coordinate controls; synthetic input trust, no mapped execution."""

import copy
import hashlib
import json
from pathlib import Path

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, spec_hash
from uarch_contract.mapped import NativeEngineIdentity, hardware_projection

from rkuarch.workload.mapped import loads_fixed_delay_job


def seal(v, key):
    v[key] = content_hash(v, exclude=(key,))


def prepare(root, output):
    root, output = Path(root), Path(output)
    assert output.is_relative_to(Path("/tmp")) and not output.exists()
    base = json.loads(
        (root / "native/crates/uarch-engine/testdata/synthetic-kernel-job.json").read_bytes()
    )
    rows = []
    for coordinate in [0, 2**53, 2**53 + 1, 2**64 - 1, 2**64, 2**64 + 1, 2**65 - 1]:
        raw = copy.deepcopy(base)
        spec = raw["workload_closure"]["hardware_spec"]
        spec["cores"]["grid"]["rows"]["value"] = float(2**65)
        spec["memory"]["controllers"][0]["attach"][0] = coordinate
        spec = HardwareSpec.model_validate(spec)
        hw = spec.model_dump(mode="json")
        h = spec_hash(spec)
        bundle = raw["workload_closure"]
        bundle.update(hardware_spec=hw, hardware_spec_hash=h)
        raw.update(hardware=hardware_projection(spec).model_dump(mode="json"), hardware_spec_hash=h)
        for e in raw["profile"]["entries"]:
            e.update(hardware_spec=hw, hardware_spec_hash=h)
        seal(raw["profile"], "profile_hash")
        raw["admission"]["profile_hash"] = raw["profile"]["profile_hash"]
        bundle["admission"] = copy.deepcopy(raw["admission"])
        seal(bundle, "bundle_hash")
        raw["bundle_hash"] = bundle["bundle_hash"]
        raw["registry"]["test_only_specs"] = [
            dict(
                hardware_spec_hash=h,
                rationale=(
                    "B synthetic field-only DTO control; no hardware claim or execution authority."
                ),
            )
        ]
        seal(raw["registry"], "registry_hash")
        seal(raw, "job_hash")
        auth = dict(
            trusted_profile_hash=raw["profile"]["profile_hash"],
            trusted_registry_hash=raw["registry"]["registry_hash"],
            expected_engine=NativeEngineIdentity.model_validate(raw["engine"]),
        )
        text = canonical_json(raw)
        valid = loads_fixed_delay_job(text, **auth)
        assert canonical_json(valid) == text
        rows.append(
            dict(
                id=str(coordinate),
                input=text,
                expected="accept",
                normalized=text,
                trust=dict(
                    registry=auth["trusted_registry_hash"],
                    profile=auth["trusted_profile_hash"],
                    case=raw["admission"]["case_id"],
                    engine=raw["engine"],
                ),
            )
        )
    output.write_text(json.dumps(rows, indent=2) + "\n")
    return dict(
        count=len(rows),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        cases=[r["id"] for r in rows],
        expected="all accepted with exact integer unchanged",
        authority="synthetic admission-only",
    )
