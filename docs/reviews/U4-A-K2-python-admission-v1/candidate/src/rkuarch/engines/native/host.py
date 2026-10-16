"""Independent first-use authority and acyclic record resolver.

The system selector is deliberately absent until the human first-use decision.
No request, CLI flag, environment variable or adjacent workload file selects it.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import stat
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, content_hash, sha256, strict_json_loads
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
        profile_hash = job.admission.profile_hash
        _require(profile_hash is not None, "profile required")
        assert profile_hash is not None
        _require(job.profile == self.profiles[profile_hash], "profile bytes changed")

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


def _selector_bytes() -> bytes:
    with _open(_SELECTOR.parent, _SELECTOR.name) as fd:
        st = os.fstat(fd)
        _require(
            st.st_uid == 0 and not (st.st_mode & 0o022),
            "selector must be root-owned and not group/world writable",
        )
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read()
    return data


def resolve_host(*, mode: str) -> AcceptedHostBinding:
    """Fresh public resolution; no retained session or global admission cache."""
    _require(mode in ("debug", "release"), "explicit debug/release mode required")
    selector = HostSelector.model_validate(strict_json_loads(_selector_bytes()))
    return _resolve(selector, mode=mode)


def _validated_installation(
    selector: HostSelector,
) -> tuple[Callable[[], None], Callable[[str], AcceptedHostBinding]]:
    """One authority path, retaining only owned bytes and immutable identities.

    The returned closures cannot be constructed from caller-provided admitted data.
    Every original validation below completes before either closure is returned.
    """
    root = Path(selector.repository)
    observed_files: set[tuple[str, str]] = set()

    def read(binding: FileBinding) -> bytes:
        data = _read(root, binding)
        observed_files.add((binding.path, binding.byte_hash))
        return data

    def read_json(binding: FileBinding) -> Any:
        return strict_json_loads(read(binding))

    record = HostRecord.model_validate(
        read_json(FileBinding(path=selector.record_path, byte_hash=selector.record_byte_hash))
    )
    build = BuildInputs.model_validate(read_json(record.build_input_file))
    trust = BuildTrust.model_validate(read_json(record.trust_file))
    tools = ToolInputs.model_validate(read_json(build.tool_inputs_file))
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
        read(file)
    # Decision subjects precede the containing HostRecord; never include its own hash.
    decision = read_json(record.decision)
    review = read_json(record.independent_review)
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
        read(file)
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
        read(file)
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
        parsed = NativeTestProfile.model_validate(read_json(profile.file))
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
    registry = NativeTestRegistry.model_validate(read_json(trust.registry_file))
    _require(registry.registry_hash == trust.registry_hash == record.registry_hash, "registry join")
    _require(tuple(sorted(profiles)) == record.profile_hashes, "host finite profile inventory")
    inventory = read_json(record.jobs_inventory)
    _require(
        set(inventory) == {"format", "jobs"} and inventory["format"] == "uarch-k2-jobs-inventory/1",
        "jobs inventory format",
    )
    corpus = read_json(record.corpus_inventory)
    _require(isinstance(corpus, dict) and isinstance(corpus.get("cases"), list), "corpus cases")
    expected_cases = {
        (p.profile_hash, c.case_id): c.execution_outcome for p in trust.profiles for c in p.cases
    }
    corpus_cases: dict[tuple[str, str], str] = {}
    for case in corpus["cases"]:
        matching = [
            p for p in trust.profiles if p.file.model_dump(mode="json") == case.get("profile")
        ]
        _require(len(matching) == 1, "corpus profile file join")
        key = (matching[0].profile_hash, case["case_id"])
        _require(key not in corpus_cases, "duplicate corpus case")
        corpus_cases[key] = case["execution_outcome"]
    _require(corpus_cases == expected_cases, "exact corpus case/outcome inventory required")
    job_cases: set[tuple[str, str]] = set()
    jobs: set[str] = set()
    from rkuarch.workload.mapped import loads_fixed_delay_job

    for item in inventory["jobs"]:
        _require(set(item) == {"file", "job_hash"}, "job inventory entry fields")
        binding = FileBinding.model_validate(item["file"])
        data = read(binding)
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
        _require(job.admission.case_id is not None, "finite job case required")
        assert job.admission.case_id is not None
        key = (profile_hash, job.admission.case_id)
        _require(key in expected_cases and key not in job_cases, "exact unique job case required")
        job_cases.add(key)
        jobs.add(job.job_hash)
    _require(bool(jobs), "nonempty exact first-use jobs required")
    _require(job_cases == set(expected_cases), "complete first-use job case inventory required")
    for executable in record.executables:
        receipt = BuildReceipt.model_validate(read_json(executable.build_receipt))
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
            read(file)
        # Verify BOTH real binaries independently, even when selecting one mode.
        read(executable.executable)
    # Retain no mutable validated model graph. Each emitted mode binding owns
    # fresh models parsed from these exact, privately captured canonical bytes.
    selector_data = canonical_json(selector).encode()
    record_data = canonical_json(record).encode()
    profile_data = tuple((key, canonical_json(value).encode()) for key, value in profiles.items())
    admitted_jobs = frozenset(jobs)
    verified_files = tuple(sorted(observed_files))
    repository = str(root)

    def recheck() -> None:
        for path, digest in verified_files:
            _read(Path(repository), FileBinding(path=path, byte_hash=digest))

    def materialize(mode: str) -> AcceptedHostBinding:
        own_selector = HostSelector.model_validate(strict_json_loads(selector_data))
        own_record = HostRecord.model_validate(strict_json_loads(record_data))
        own_profiles = {
            key: NativeTestProfile.model_validate(strict_json_loads(data))
            for key, data in profile_data
        }
        selected = next(x for x in own_record.executables if x.mode == mode)
        return AcceptedHostBinding(
            own_selector,
            own_record,
            selected.executable,
            Path(repository),
            own_profiles,
            admitted_jobs,
            _TOKEN,
        )

    return recheck, materialize


def _resolve(selector: HostSelector, *, mode: str) -> AcceptedHostBinding:
    # The standalone API deliberately validates the entire current installation
    # afresh, including every corpus member and BOTH executable/receipt bindings.
    _, materialize = _validated_installation(selector)
    return materialize(mode)


@contextlib.contextmanager
def resolution_session() -> Iterator[Callable[..., AcceptedHostBinding]]:
    """Bounded common startup validation for one campaign/setup parent.

    Select each mode before forking workers; only genuine emitted bindings may be
    inherited. Every selection rehashes every originally read input and compares
    exact selector bytes. Drift refuses; it never refreshes this session's trust.
    Restoring all exact approved bytes allows selection again. Exit/PID change
    invalidates selection. Already emitted bindings have the ordinary public
    capability semantics and belong to the caller's bounded campaign lifetime.
    """
    selector_data = _selector_bytes()
    selector = HostSelector.model_validate(strict_json_loads(selector_data))
    recheck: Callable[[], None] | None
    materialize: Callable[[str], AcceptedHostBinding] | None
    recheck, materialize = _validated_installation(selector)
    del selector
    owner_pid = os.getpid()
    active = True

    def select(*, mode: str) -> AcceptedHostBinding:
        _require(
            active and os.getpid() == owner_pid,
            "resolution session expired or belongs to another process",
        )
        _require(mode in ("debug", "release"), "explicit debug/release mode required")
        _require(
            _selector_bytes() == selector_data,
            "selector changed; fresh resolution session required",
        )
        assert recheck is not None and materialize is not None
        recheck()
        return materialize(mode)

    try:
        yield select
    finally:
        active = False
        selector_data = b""
        recheck = None
        materialize = None
