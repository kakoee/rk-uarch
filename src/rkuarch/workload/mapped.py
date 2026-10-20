"""Shared component validation and historical /3 saved-carrier helpers.

Ordinary /4 execution uses validate_component_completeness without host authority or
build receipts. The explicit historical loaders retain /3 carrier validation for existing
fixture and semantic tests; they neither select an executable nor launch a process.
"""

from __future__ import annotations

from pathlib import Path

from uarch_contract.hashing import canonical_json, strict_json_loads
from uarch_contract.mapped import (
    Barrier,
    Compute,
    Dma,
    MappedBundle,
    MappedEngineJob,
    NativeEngineIdentity,
    NocTransfer,
    admit,
    canonical_owners,
    require,
    validate_job,
)
from uarch_contract.ordinary import OrdinaryBundle


def loads_fixed_delay_job(
    data: str | bytes,
    *,
    trusted_registry_hash: str,
    trusted_profile_hash: str,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Authenticate a complete saved job against separately selected host anchors.

    All closure/point/hardware/profile/clock/seed joins use installed validate_job and
    admit. Only K2 test fixed-delay scope is admitted; analytic and component routing
    stays outside this boundary. Synthetic anchors are suitable only for unit tests.
    """
    return validate_job(
        strict_json_loads(data),
        invocation="test",
        checkpoint="K2",
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )


def load_fixed_delay_job(
    path: Path,
    *,
    trusted_registry_hash: str,
    trusted_profile_hash: str,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Read only the explicitly supplied file; relocation does not affect identity."""
    return loads_fixed_delay_job(
        path.read_bytes(),
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )


def export_fixed_delay_job(
    job: MappedEngineJob,
    path: Path,
    *,
    trusted_registry_hash: str,
    trusted_profile_hash: str,
    expected_engine: NativeEngineIdentity,
) -> None:
    """Revalidate and save canonical UTF-8 JSON, refusing to overwrite an existing file.

    Reparse serialized model data so nested mutable dictionaries and model_copy cannot
    bypass Pydantic validation. Validation completes before opening the destination.
    Export is byte-preserving replay of content, never a rehash or authority adoption.
    """
    validated = loads_fixed_delay_job(
        canonical_json(job),
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )
    payload = canonical_json(validated).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)


def loads_component_bundle(
    data: str | bytes,
    *,
    invocation: str,
    registry: object,
    profile: object | None,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
) -> MappedBundle:
    """Admit every saved component point under installed B rules, without producers.

    Registry/profile content and independently selected trust hashes are required
    separately; no local file, environment, self-hash or synthetic anchor is authority.
    """
    value = strict_json_loads(data)
    bundle = MappedBundle.model_validate(value)
    require(bundle.scope.kind == "component", "UnsupportedWorkloadScope")
    assert bundle.scope.kind == "component"
    require(
        all(set(op.operand_access) == {"X", "W", "Y"} for op in bundle.scope.ops),
        "InvalidCoverage",
        "operand access",
    )
    validated = admit(
        bundle,
        invocation=invocation,
        checkpoint="B",
        registry=registry,
        profile=profile,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
    )
    validate_component_completeness(validated)
    return validated


def load_component_bundle(
    path: Path,
    *,
    invocation: str,
    registry: object,
    profile: object | None,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
) -> MappedBundle:
    """Read only the caller-selected saved bundle; relocation preserves identity."""
    return loads_component_bundle(
        path.read_bytes(),
        invocation=invocation,
        registry=registry,
        profile=profile,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
    )


def export_component_bundle(
    bundle: MappedBundle,
    path: Path,
    *,
    invocation: str,
    registry: object,
    profile: object | None,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
) -> None:
    """Revalidate before exclusive creation; never repair a stale mapping or join."""
    validated = loads_component_bundle(
        canonical_json(bundle),
        invocation=invocation,
        registry=registry,
        profile=profile,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
    )
    with path.open("xb") as stream:
        stream.write(canonical_json(validated).encode("utf-8"))


def loads_component_job(
    data: str | bytes,
    *,
    invocation: str,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Replay input only. Public component result replay waits for stage B execution."""
    value = strict_json_loads(data)
    # Validate structural operand access before the installed job validator descends
    # into its embedded resource admission (which indexes those keys).
    if isinstance(value, dict) and isinstance(value.get("workload_closure"), dict):
        closure = MappedBundle.model_validate(value["workload_closure"])
        if closure.scope.kind == "component":
            require(
                all(set(op.operand_access) == {"X", "W", "Y"} for op in closure.scope.ops),
                "InvalidCoverage",
                "operand access",
            )
    job = validate_job(
        value,
        invocation=invocation,
        checkpoint="B",
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )
    require(job.workload_closure.scope.kind == "component", "UnsupportedWorkloadScope")
    # Installed validate_job selects one point. Saved closure admission must additionally
    # reject invalid unselected resources, so the imported bundle remains wholly valid.
    loads_component_bundle(
        canonical_json(job.workload_closure),
        invocation=invocation,
        registry=job.registry,
        profile=job.profile,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
    )
    return job


def load_component_job(
    path: Path,
    *,
    invocation: str,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Load a saved job without any preparation or native execution dependencies."""
    return loads_component_job(
        path.read_bytes(),
        invocation=invocation,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )


def export_component_job(
    job: MappedEngineJob,
    path: Path,
    *,
    invocation: str,
    trusted_registry_hash: str,
    trusted_profile_hash: str | None,
    expected_engine: NativeEngineIdentity,
) -> None:
    """Export canonical bytes only after all current joins and anchors pass."""
    validated = loads_component_job(
        canonical_json(job),
        invocation=invocation,
        trusted_registry_hash=trusted_registry_hash,
        trusted_profile_hash=trusted_profile_hash,
        expected_engine=expected_engine,
    )
    with path.open("xb") as stream:
        stream.write(canonical_json(validated).encode("utf-8"))


def validate_component_completeness(bundle: MappedBundle | OrdinaryBundle) -> None:
    """Consumer guards after installed admission; no new carrier or relaxed law.

    The installed resource validator checks range bounds but does not prove a
    producer populated the *whole* operand, that cold Y is written, or the
    barrier's owner join. Keep these checks outside protected source until its
    exact additive repair is reviewed; native B must implement the same guards.
    """
    for point in bundle.points:
        graph = point.task_graph
        buffers = {b.id: b for b in graph.buffers}
        jobs = {j.id: j for j in graph.jobs}
        owners = {o.resource: o.owner_id for o in canonical_owners(bundle.hardware_spec, graph)}
        for job in graph.jobs:
            if isinstance(job, Barrier):
                require(
                    job.owner_id == owners["barrier:" + job.id],
                    "InvalidResource",
                    "barrier owner " + job.id,
                )
            if not isinstance(job, Compute):
                continue
            for name in ("X", "W"):
                buf = buffers[job.operand_buffers[name]]
                if buf.initial_residency == "preloaded":
                    continue
                producer = jobs.get(buf.producer_id or "")
                require(
                    isinstance(producer, (Dma, NocTransfer)),
                    "InvalidTransfer",
                    "complete operand " + buf.id,
                )
                assert isinstance(producer, (Dma, NocTransfer))
                require(
                    producer.destination.buffer_id == buf.id
                    and producer.destination.offset_bytes == 0
                    and producer.destination.size_bytes == buf.size_bytes,
                    "InvalidTransfer",
                    "complete operand " + buf.id,
                )
            if point.initial_state == "cold":
                buf = buffers[job.operand_buffers["Y"]]
                writes = sorted(
                    (j.source.offset_bytes, j.source.size_bytes)
                    for j in graph.jobs
                    if isinstance(j, Dma)
                    and j.direction == "write"
                    and j.source.buffer_id == buf.id
                )
                cursor = 0
                for offset, size in writes:
                    require(offset == cursor, "InvalidTransfer", "complete output " + buf.id)
                    cursor += size
                require(cursor == buf.size_bytes, "InvalidTransfer", "complete output " + buf.id)
