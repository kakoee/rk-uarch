"""Explicit candidate authoring only; unsigned proposals, never runtime authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedBundle
from uarch_contract.prepared import PreparedOp

from rkuarch.mapping.component import map_component
from rkuarch.workload.component import component_point, prepare_component_bundle
from validation.component.corpus import materialize

ROOT = Path(__file__).resolve().parents[3]


def inputs() -> dict[str, Any]:
    base = MappedBundle.model_validate_json(
        (ROOT / "contract/fixtures/mapped/component.json").read_bytes()
    )
    assert base.scope.kind == "component"
    ops = []
    for name, n in (("a", 255), ("z", 256)):
        raw = base.scope.ops[0].model_dump(mode="json")
        raw.update(id=name, depends_on=[])
        raw["spec"]["dimensions"] = dict(M=256, K=256, N=n)
        ops.append(PreparedOp.model_validate(raw))
    source = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "src/rkuarch/mapping/component.py",
            "src/rkuarch/workload/component.py",
            "contract/uarch_contract/mapped.py",
            "validation/component/corpus.py",
            "docs/reviews/U4-A-component-release-v1/proposal_inputs.py",
        )
    }
    result = {}
    for state in ("cold", "fixture_resident"):
        graph = map_component(ops, base.hardware_spec, initial_state=state, mapping_version="2")
        point = component_point(ops, graph, initial_state=state)
        bundle = prepare_component_bundle(
            ops,
            base.hardware_spec,
            point,
            producer=base.producer,
            assumptions=base.assumptions,
            rank=base.rank,
            admission=base.admission,
            mapping_version="2",
        )
        name = "A2-255-256-" + state
        item = materialize(name, bundle.model_dump(mode="json"), dict(outcome="success"))
        item["bundle"]["producer"] = dict(
            name="A-component-proposal-only", version="2", implementation_hash=content_hash(source)
        )
        item["bundle"]["bundle_hash"] = content_hash(item["bundle"], exclude=("bundle_hash",))
        result[name] = item
    return result


def manifest() -> dict[str, Any]:
    return {
        name: dict(
            bundle_hash=item["bundle"]["bundle_hash"],
            graph_hash=item["bundle"]["points"][0]["task_graph"]["graph_hash"],
            point_hash=item["bundle"]["points"][0]["payload_hash"],
            profile_hash=item["profile"]["profile_hash"],
            status="unsigned-proposal-not-authority",
            engine_identity=None,
            build_identity=None,
            host_identity=None,
            job_hash=None,
            result_hash=None,
            native_status="not_run",
        )
        for name, item in inputs().items()
    }


if __name__ == "__main__":
    print(json.dumps(manifest(), indent=2, sort_keys=True))
