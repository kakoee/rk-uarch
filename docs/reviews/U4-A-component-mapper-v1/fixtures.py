"""Author input fixtures only. Synthetic test profiles are NOT human host authority."""

from __future__ import annotations

import json
from pathlib import Path

from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import Admission, MappedBundle
from uarch_contract.prepared import PreparedOp, Producer

from rkuarch.mapping.component import map_component
from rkuarch.workload.component import component_point, prepare_component_bundle
from rkuarch.workload.mapped import export_component_bundle

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "fixtures"


def main() -> None:
    # Explicit source closure from the separately executed audit, no implicit host lookup.
    audit = json.loads((OUT.parent / "dependency-audit.json").read_bytes())
    closure = {}
    for paths in audit["static_closures"].values():
        closure.update(paths)
    producer = Producer(
        name="rkuarch-component-inputs", version="1", implementation_hash=content_hash(closure)
    )
    baseline = MappedBundle.model_validate_json(
        (ROOT / "contract/fixtures/mapped/component.json").read_bytes()
    )
    assert baseline.scope.kind == "component"
    registry = json.loads((ROOT / "contract/fixtures/mapped/registry.json").read_bytes())
    manifest = dict(
        authority="synthetic author input fixtures; no host/native authority",
        producer=producer.model_dump(mode="json"),
        cases={},
    )
    OUT.mkdir(exist_ok=True)
    for name, m, k, n, state in [
        ("A-C01-resident", 16, 256, 256, "fixture_resident"),
        ("A-C02-resident", 3, 5, 7, "fixture_resident"),
        ("A-C03-resident", 257, 256, 256, "fixture_resident"),
        ("A-C02-cold", 3, 5, 7, "cold"),
    ]:
        raw = baseline.scope.ops[0].model_dump(mode="json")
        raw["spec"]["dimensions"] = dict(M=m, K=k, N=n)
        ops = (PreparedOp.model_validate(raw),)
        graph = map_component(ops, baseline.hardware_spec, initial_state=state)
        point = component_point(ops, graph, initial_state=state)
        profile = None
        admission = baseline.admission
        if state == "fixture_resident":
            profile = json.loads(
                (ROOT / "contract/fixtures/mapped/resident-profile.json").read_bytes()
            )
            profile["owner"] = "SYNTHETIC-UNIT-ONLY; not an accepted human profile"
            profile["entries"][0].update(
                case_id=name,
                graph_hash=graph.graph_hash,
                point_hash=point.payload_hash,
                allowed_job_kinds=["compute"],
            )
            profile["profile_hash"] = content_hash(profile, exclude=("profile_hash",))
            admission = Admission(
                checkpoint="B",
                invocation="test",
                profile_hash=profile["profile_hash"],
                case_id=name,
                eligibility="verification_only",
            )
            with (OUT / (name + ".profile.json")).open("x") as stream:
                stream.write(canonical_json(profile))
        bundle = prepare_component_bundle(
            ops,
            baseline.hardware_spec,
            point,
            producer=producer,
            assumptions=baseline.assumptions,
            rank=baseline.rank,
            admission=admission,
        )
        export_component_bundle(
            bundle,
            OUT / (name + ".json"),
            invocation=admission.invocation,
            registry=registry,
            profile=profile,
            trusted_registry_hash=registry["registry_hash"],
            trusted_profile_hash=admission.profile_hash,
        )
        manifest["cases"][name] = dict(
            bundle_hash=bundle.bundle_hash,
            point_hash=point.payload_hash,
            graph_hash=graph.graph_hash,
            profile_hash=admission.profile_hash,
            expected_native_outcome="not_run",
        )
    with (OUT / "manifest.json").open("x") as stream:
        stream.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
