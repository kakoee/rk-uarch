"""Saved fixed-delay inputs using the installed M carriers and host-owned authority.

The embedding host supplies reviewed anchors separately from caller content. There is
no authority discovery, producer, executable lookup or subprocess here. Successful
validation is not a public K2 release or an enduring launch capability: a future writer
must revalidate current bytes and verify its executable against accepted build receipts.
"""

from __future__ import annotations

from pathlib import Path

from uarch_contract.hashing import canonical_json, strict_json_loads
from uarch_contract.mapped import MappedEngineJob, NativeEngineIdentity, validate_job


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
