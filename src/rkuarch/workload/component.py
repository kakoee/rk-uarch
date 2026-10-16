"""Explicit component assembly, separate from mapping and saved-input replay.

No profile/registry/engine authority is generated here. Callers supply provenance
and admission records. A valid component input is not permission to launch native.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import (
    Admission,
    MappedAssumptions,
    MappedBundle,
    MappedEngineJob,
    MappedPoint,
    NativeEngineIdentity,
    TaskGraph,
    canonical_owners,
    hardware_projection,
    require,
    resolve_frequencies,
    validate_resources,
)
from uarch_contract.prepared import PreparedOp, Producer, RankScope

from rkuarch.workload.mapped import loads_component_job, validate_component_completeness


def component_point(
    ops: Sequence[PreparedOp],
    graph: TaskGraph,
    *,
    initial_state: str = "cold",
) -> MappedPoint:
    """Build the single ratio1 point; its hash can be frozen before profile assembly."""
    require(initial_state in ("cold", "fixture_resident"), "UnsupportedInitialState")
    raw = dict(
        point_id="component",
        identity=dict(kind="component", op_ids=sorted(x.id for x in ops)),
        frequency_ratio=1.0,
        initial_state=initial_state,
        priming_iterations=0,
        task_graph=graph.model_dump(mode="json"),
    )
    return MappedPoint.model_validate(dict(raw, payload_hash=content_hash(raw)))


def prepare_component_bundle(
    ops: Sequence[PreparedOp],
    hardware_spec: HardwareSpec,
    point: MappedPoint,
    *,
    producer: Producer,
    assumptions: MappedAssumptions,
    rank: RankScope,
    admission: Admission,
) -> MappedBundle:
    """Assemble supplied mappings unchanged; validate resources without inventing trust.

    Test profiles bind point bytes before the bundle is assembled. Use the saved-input
    admission API with independent anchors before consuming/exporting this bundle.
    """
    from uarch_contract.hashing import spec_hash

    raw = dict(
        format="uarch-prepared/3",
        producer=producer.model_dump(mode="json"),
        hardware_spec=hardware_spec.model_dump(mode="json"),
        hardware_spec_hash=spec_hash(hardware_spec),
        assumptions_hash=assumptions.assumptions_hash,
        rank=rank.model_dump(mode="json"),
        mapping_scope="task_graph",
        mapping_policy=dict(name="ws-rowsplit", version="1", buffer_depth=2),
        scope=dict(
            kind="component",
            operator_version="prepared-op/1",
            ops=[x.model_dump(mode="json") for x in sorted(ops, key=lambda x: x.id)],
            op_ids=sorted(x.id for x in ops),
            repeat=1,
        ),
        source=None,
        assumptions=assumptions.model_dump(mode="json"),
        admission=admission.model_dump(mode="json"),
        points=[point.model_dump(mode="json")],
    )
    b = MappedBundle.model_validate(dict(raw, bundle_hash=content_hash(raw)))
    assert b.scope.kind == "component"
    require(
        all(set(op.operand_access) == {"X", "W", "Y"} for op in b.scope.ops),
        "InvalidCoverage",
        "operand access",
    )
    validate_resources(b, b.points[0])
    validate_component_completeness(b)
    return b


def prepare_component_job(
    bundle: MappedBundle,
    *,
    point_hash: str,
    registry: object,
    profile: object | None,
    invocation: str,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Construct an input job against independently supplied prospective engine anchors.

    Does not resolve a host, import native execution or copy a K2 build identity. A
    fixed-delay engine is refused by the installed resource-interval job validator.
    """
    points = [p for p in bundle.points if p.payload_hash == point_hash]
    require(len(points) == 1, "MissingCoverage")
    point = points[0]
    raw: dict[str, Any] = dict(
        protocol="uarch-engine/3",
        bundle_hash=bundle.bundle_hash,
        point_hash=point_hash,
        request_hash=None,
        assumptions_hash=bundle.assumptions_hash,
        engine=expected_engine.model_dump(mode="json"),
        mapped_point=point.model_dump(mode="json"),
        workload_closure=bundle.model_dump(mode="json"),
        assumptions=bundle.assumptions.model_dump(mode="json"),
        hardware=hardware_projection(bundle.hardware_spec).model_dump(mode="json"),
        hardware_spec_hash=bundle.hardware_spec_hash,
        rank=bundle.rank.model_dump(mode="json"),
        precision="bf16",
        fidelity_detail=dict(compute=1, noc=0, dram=0, sync="exact", layer_reuse=False),
        frequency_ratio=point.frequency_ratio,
        freq_hz=resolve_frequencies(bundle.hardware_spec, point.frequency_ratio).model_dump(
            mode="json"
        ),
        initial_state=point.initial_state,
        priming_iterations=point.priming_iterations,
        seed=0,
        admission=bundle.admission.model_dump(mode="json"),
        state_model="resource_intervals/1",
        clock_setup=[],
        owner_enumeration="native-owners/1",
        owners=[
            x.model_dump(mode="json")
            for x in canonical_owners(bundle.hardware_spec, point.task_graph)
        ],
        registry=registry,
        profile=profile,
    )
    raw["job_hash"] = content_hash(raw)
    return loads_component_job(
        canonical_json(raw),
        invocation=invocation,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )
