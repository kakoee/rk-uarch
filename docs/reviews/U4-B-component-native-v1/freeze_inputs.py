"""Freeze B proposals and synthetic private raw jobs; no execution or authority."""

import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash

from validation.component.native_inputs import private_job, prospective_inputs

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    proposal = prospective_inputs()
    members = {"proposal.json": canonical_json(proposal).encode()}
    records = []
    for name, item in proposal["items"].items():
        job = private_job(item, proposal["registry"])
        trust = dict(
            registry=job["registry"]["registry_hash"],
            profile=job["profile"]["profile_hash"],
            case=job["admission"]["case_id"],
            engine=job["engine"],
        )
        members[f"jobs/{name}.json"] = canonical_json(job).encode()
        members[f"trust/{name}.json"] = canonical_json(trust).encode()
        records.append(
            dict(
                case_id=name,
                job_hash=job["job_hash"],
                profile_hash=trust["profile"],
                bundle_hash=job["bundle_hash"],
                mapping_policy=job["workload_closure"]["mapping_policy"],
                expected=item["expected"],
                expected_layer=item["expected_layer"],
                expected_public_code=item["expected_public_code"],
                native_status="not_run",
                synthetic_unit_anchors=True,
                public_execution_authority=None,
            )
        )
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, data in sorted(members.items()):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    compressed = gzip.compress(archive.getvalue(), mtime=0)
    (out / "inputs.tar.gz").write_bytes(compressed)
    manifest = dict(
        format="B-component-native-input-freeze/1",
        status="prospective; private synthetic anchors",
        archive_sha256=hashlib.sha256(compressed).hexdigest(),
        members={name: hashlib.sha256(data).hexdigest() for name, data in sorted(members.items())},
        historical_selection_hash=proposal["historical_selection_hash"],
        historical_selection_sha256=proposal["historical_selection_sha256"],
        registry_hash=proposal["registry"]["registry_hash"],
        sources={
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (
                "validation/component/native_inputs.py",
                "validation/component/native_check.py",
                "validation/component/test_native_inputs.py",
                "validation/component/observations_v2.py",
                "validation/component/transition_checks.py",
                "validation/component/selection.py",
            )
        },
        transitions=proposal["transitions"],
        cases=records,
    )
    manifest["selection_hash"] = content_hash(manifest)
    (out / "input-freeze.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"{len(records)} prospective jobs; {len(compressed)} archive bytes; zero executions")


if __name__ == "__main__":
    main()
