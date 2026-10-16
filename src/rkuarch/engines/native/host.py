"""Independent first-use authority and acyclic record resolver.

The system selector is deliberately absent until the human first-use decision.
No request, CLI flag, environment variable or adjacent workload file selects it.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uarch_contract.hashing import content_hash, sha256, strict_json_loads
from uarch_contract.mapped import MappedEngineJob, NativeTestProfile, NativeTestRegistry

from .records import (
    BuildInputs,
    BuildReceipt,
    BuildTrust,
    FileBinding,
    HostRecord,
    HostSelector,
    ToolInputs,
)

_SELECTOR = Path("/etc/rkuarch/k2-host-selector.json")
_TOKEN = object()


class HostBindingError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HostBindingError(message)


@contextlib.contextmanager
def _open(root: Path, relative: str) -> Iterator[int]:
    parts = relative.split("/")
    _require(
        bool(parts)
        and all(p not in ("", ".", "..") for p in parts)
        and not relative.startswith("/")
        and "\\" not in relative,
        "confined explicit relative path required",
    )
    # Walk each directory using pinned descriptors and O_NOFOLLOW, including root.
    _require(root.is_absolute(), "absolute independent repository root required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in (*root.parts[1:], *parts[:-1]):
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            _require(stat.S_ISREG(os.fstat(leaf).st_mode), "regular file required")
            yield leaf
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def _read(root: Path, binding: FileBinding) -> bytes:
    with _open(root, binding.path) as fd:
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read()
    _require(sha256(data) == binding.byte_hash, "bound file digest mismatch: " + binding.path)
    return data


def _json(root: Path, binding: FileBinding) -> Any:
    return strict_json_loads(_read(root, binding))


@dataclass(frozen=True)
class AcceptedHostBinding:
    """Resolver-produced capability. Construction tests cannot become host approval."""

    selector: HostSelector
    record: HostRecord
    executable: FileBinding
    root: Path
    profiles: dict[str, NativeTestProfile]
    jobs: frozenset[str]
    _token: object

    def __post_init__(self) -> None:
        _require(self._token is _TOKEN, "host binding must come from independent resolver")

    def authority_for(self, raw: Any) -> dict[str, Any]:
        _require(isinstance(raw, dict), "job object required")
        profile = raw.get("admission", {}).get("profile_hash")
        _require(profile in self.record.profile_hashes, "profile outside human host binding")
        return {
            "trusted_registry_hash": self.record.registry_hash,
            "trusted_profile_hash": profile,
            "expected_engine": self.record.expected_engine,
        }

    def require_job(self, job: MappedEngineJob) -> None:
        _require(job.job_hash in self.jobs, "job outside exact human first-use inventory")
        _require(job.profile == self.profiles[job.admission.profile_hash], "profile bytes changed")

    @contextlib.contextmanager
    def open_executable(self) -> Iterator[int]:
        # Revalidate exact byte identity at launch, retaining the same descriptor.
        with _open(self.root, self.executable.path) as fd:
            st = os.fstat(fd)
            _require(
                bool(st.st_mode & 0o111) and not (st.st_mode & 0o222),
                "executable must be immutable/read-only at first use",
            )
            hasher = hashlib.sha256()
            while chunk := os.read(fd, 1024 * 1024):
                hasher.update(chunk)
            _require(
                "sha256:" + hasher.hexdigest() == self.executable.byte_hash,
                "executable digest changed",
            )
            os.lseek(fd, 0, os.SEEK_SET)
            yield fd


def resolve_host(*, mode: str) -> AcceptedHostBinding:
    """Load only the independently installed, root-owned system selector."""
    _require(mode in ("debug", "release"), "explicit debug/release mode required")
    with _open(_SELECTOR.parent, _SELECTOR.name) as fd:
        st = os.fstat(fd)
        _require(
            st.st_uid == 0 and not (st.st_mode & 0o022),
            "selector must be root-owned and not group/world writable",
        )
        with os.fdopen(os.dup(fd), "rb") as stream:
            selector = HostSelector.model_validate(strict_json_loads(stream.read()))
    return _resolve(selector, mode=mode)


def _resolve(selector: HostSelector, *, mode: str) -> AcceptedHostBinding:
    """Private resolver core, also used by explicitly synthetic record tests."""
    root = Path(selector.repository)
    record = HostRecord.model_validate(
        _json(root, FileBinding(path=selector.record_path, byte_hash=selector.record_byte_hash))
    )
    build = BuildInputs.model_validate(_json(root, record.build_input_file))
    trust = BuildTrust.model_validate(_json(root, record.trust_file))
    tools = ToolInputs.model_validate(_json(root, build.tool_inputs_file))
    _require(content_hash(build) == record.build_input_hash, "BuildInputs hash")
    _require(content_hash(trust) == record.trust_hash == build.trust_hash, "BuildTrust hash")
    _require(
        content_hash(tools) == record.tool_inputs_hash == build.tool_inputs_hash, "ToolInputs hash"
    )
    _require(build.trust_file == record.trust_file, "trust file cross-join")
    _require(record.semantics == trust.semantics_file, "semantic file cross-join")
    _require(record.corpus_inventory == trust.corpus_inventory, "corpus file cross-join")
    for file in (
        record.decision,
        record.independent_review,
        record.semantics,
        record.loader_read_inventory,
        record.corpus_inventory,
    ):
        _read(root, file)
    # Decision subjects precede the containing HostRecord; never include its own hash.
    decision = _json(root, record.decision)
    review = _json(root, record.independent_review)
    subject = {
        "build_input_hash": record.build_input_hash,
        "tool_inputs_hash": record.tool_inputs_hash,
        "trust_hash": record.trust_hash,
        "model_inputs_hash": record.model_inputs_hash,
        "executable_byte_hashes": [x.executable.byte_hash for x in record.executables],
        "corpus_byte_hash": record.corpus_inventory.byte_hash,
        "jobs_byte_hash": record.jobs_inventory.byte_hash,
    }
    _require(
        decision
        == {
            "format": "uarch-k2-human-first-use-decision/1",
            "accepted_by": "Javid (@jjaffari)",
            "reply": "yes",
            "subject": subject,
        },
        "exact human first-use decision subjects required",
    )
    _require(
        review.get("format") == "uarch-k2-independent-build-review/1"
        and review.get("subject") == subject
        and review.get("read_audit_complete") is True
        and review.get("selected_support_current") is True,
        "independent final build/read/currentness review required",
    )
    # Every input is checked, including build mode/tool flags and the model subset.
    for file in build.source_files:
        _read(root, file)
    model = [
        x.model_dump(mode="json") for x in build.source_files if x.path in build.model_source_paths
    ]
    _require(
        content_hash(model) == build.model_inputs_hash == record.model_inputs_hash,
        "model subset hash",
    )
    _require(
        list(build.model_source_paths) == sorted(set(build.model_source_paths)),
        "sorted unique model paths",
    )
    for file in (
        tools.accepted_k1_pins,
        tools.cargo_lock,
        tools.full_metadata,
        tools.target_metadata,
        tools.feature_graph,
        tools.licence_inventory,
        tools.crate_checksum_inventory,
        tools.linker_and_os_inventory,
    ):
        _read(root, file)
    _require(
        tuple(x.mode for x in build.mode_configs) == ("debug", "release"),
        "both build modes required",
    )
    for config in build.mode_configs:
        _require(config.rustflags == tools.flags, "mode flags differ from accepted tool inputs")
    profiles = {}
    _require(
        [p.profile_hash for p in trust.profiles]
        == sorted({p.profile_hash for p in trust.profiles}),
        "sorted finite profiles",
    )
    for profile in trust.profiles:
        parsed = NativeTestProfile.model_validate(_json(root, profile.file))
        _require(parsed.profile_hash == profile.profile_hash, "profile file/content mismatch")
        actual = [
            (
                e.case_id,
                e.graph_hash,
                e.point_hash,
                e.hardware_spec_hash,
                e.clock_setup_hash,
                e.seed,
            )
            for e in parsed.entries
        ]
        bound = [
            (
                e.case_id,
                e.graph_hash,
                e.point_hash,
                e.hardware_spec_hash,
                e.clock_setup_hash,
                e.seed,
            )
            for e in profile.cases
        ]
        _require(actual == bound, "finite case closure differs from profile")
        profiles[parsed.profile_hash] = parsed
    registry = NativeTestRegistry.model_validate(_json(root, trust.registry_file))
    _require(registry.registry_hash == trust.registry_hash == record.registry_hash, "registry join")
    _require(tuple(sorted(profiles)) == record.profile_hashes, "host finite profile inventory")
    inventory = _json(root, record.jobs_inventory)
    _require(
        set(inventory) == {"format", "jobs"} and inventory["format"] == "uarch-k2-jobs-inventory/1",
        "jobs inventory format",
    )
    jobs: set[str] = set()
    from rkuarch.workload.mapped import loads_fixed_delay_job

    for item in inventory["jobs"]:
        _require(set(item) == {"file", "job_hash"}, "job inventory entry fields")
        binding = FileBinding.model_validate(item["file"])
        data = _read(root, binding)
        raw = strict_json_loads(data)
        profile_hash = raw["admission"]["profile_hash"]
        _require(profile_hash in profiles, "job profile outside trust")
        job = loads_fixed_delay_job(
            data,
            trusted_registry_hash=record.registry_hash,
            trusted_profile_hash=profile_hash,
            expected_engine=record.expected_engine,
        )
        _require(
            job.job_hash == item["job_hash"]
            and job.job_hash not in jobs
            and job.profile == profiles[profile_hash],
            "job inventory closure",
        )
        jobs.add(job.job_hash)
    _require(bool(jobs), "nonempty exact first-use jobs required")
    for executable in record.executables:
        receipt = BuildReceipt.model_validate(_json(root, executable.build_receipt))
        _require(
            receipt.engine == record.expected_engine
            and receipt.build_input_hash == record.build_input_hash,
            "executable identity join",
        )
        _require(
            receipt.mode == executable.mode and receipt.executable == executable.executable,
            "mode/executable join",
        )
        _require(
            receipt.target == executable.target == tools.target
            and receipt.image_digest == tools.image_digest,
            "target/image join",
        )
        _require(
            tuple(x.path for x in receipt.generated_identity_outputs)
            == build.generated_identity_output_paths,
            "generated identity inventory join",
        )
        for file in (
            *receipt.generated_identity_outputs,
            receipt.actual_read_inventory,
            receipt.actual_environment,
            receipt.compiler_verbose,
            receipt.build_log,
            receipt.binary_origin_check,
            receipt.software_path_check,
        ):
            _read(root, file)
        # Verify BOTH real binaries independently, even when selecting one mode.
        _read(root, executable.executable)
    selected = next(x for x in record.executables if x.mode == mode)
    return AcceptedHostBinding(
        selector, record, selected.executable, root, profiles, frozenset(jobs), _TOKEN
    )
