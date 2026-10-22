"""Ordinary preparation from existing mapped points. No host authority or file discovery."""

from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import version
from typing import Any

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import (
    MappedAssumptions,
    MappedPoint,
    canonical_owners,
    hardware_projection,
    require,
    resolve_frequencies,
    validate_resources,
)
from uarch_contract.ordinary import (
    OrdinaryAdmission,
    OrdinaryBundle,
    OrdinaryJob,
    SoftwareIdentity,
    SoftwareProducer,
)
from uarch_contract.prepared import PreparedOp, RankScope
from uarch_contract.reference import ReferenceBundle, ReferenceJob

from rkuarch.workload.mapped import validate_component_completeness


def software_identity() -> SoftwareIdentity:
    return SoftwareIdentity.model_validate(
        {
            "name": "native",
            "version": "native-stage/2",
            "package_version": version("rk-uarch"),
            "model": {"name": "native-intervals", "version": "2"},
        }
    )


def prepare_job(
    bundle: OrdinaryBundle | ReferenceBundle,
    *,
    point_hash: str,
) -> OrdinaryJob | ReferenceJob:
    """Assemble a selected prepared point unchanged, with installed software versions."""
    if isinstance(bundle, ReferenceBundle):
        from .reference import prepare_job as prepare_reference_job

        require(bundle.points[0].payload_hash == point_hash, "MissingCoverage")
        return prepare_reference_job(bundle)
    bundle = OrdinaryBundle.model_validate(bundle.model_dump(mode="json"))
    validate_component_completeness(bundle)
    points = [p for p in bundle.points if p.payload_hash == point_hash]
    require(len(points) == 1, "MissingCoverage")
    point = points[0]
    raw: dict[str, Any] = dict(
        protocol="uarch-engine/4",
        bundle_hash=bundle.bundle_hash,
        point_hash=point_hash,
        request_hash=None,
        assumptions_hash=bundle.assumptions_hash,
        engine=software_identity().model_dump(mode="json"),
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
    )
    raw["job_hash"] = content_hash(raw)
    return OrdinaryJob.model_validate(raw)


def prepare_bundle(
    ops: Sequence[PreparedOp],
    hardware_spec: HardwareSpec,
    point: MappedPoint,
    *,
    producer: SoftwareProducer,
    assumptions: MappedAssumptions,
    rank: RankScope,
    admission: OrdinaryAdmission,
    mapping_version: str = "1",
) -> OrdinaryBundle:
    """Assemble an existing mapping with basic producer metadata; never remap."""
    from uarch_contract.hashing import spec_hash

    raw = dict(
        format="uarch-prepared/4",
        producer=producer.model_dump(mode="json"),
        hardware_spec=hardware_spec.model_dump(mode="json"),
        hardware_spec_hash=spec_hash(hardware_spec),
        assumptions_hash=assumptions.assumptions_hash,
        rank=rank.model_dump(mode="json"),
        mapping_scope="task_graph",
        mapping_policy=dict(name="ws-rowsplit", version=mapping_version, buffer_depth=2),
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
    b = OrdinaryBundle.model_validate(dict(raw, bundle_hash=content_hash(raw)))
    assert b.scope.kind == "component"
    require(
        all(set(op.operand_access) == {"X", "W", "Y"} for op in b.scope.ops),
        "InvalidCoverage",
        "operand access",
    )
    validate_resources(b, b.points[0])
    validate_component_completeness(b)
    return b
