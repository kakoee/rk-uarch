"""Separate component authority and bounded preparation; private payloads are not selectors."""

from __future__ import annotations

import contextlib
import hashlib
import os
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uarch_contract.hashing import content_hash, sha256, strict_json_loads
from uarch_contract.mapped import (
    MappedEngineJob,
    NativeEngineIdentity,
    NativeTestProfile,
    NativeTestRegistry,
    admit,
    validate_job,
)

from rkuarch.workload.mapped import loads_component_job

from .component_records import (
    ComponentBuildInputs,
    ComponentBuildReceipt,
    ComponentBuildTrust,
    ComponentHostRecord,
    ComponentHostSelector,
    ComponentPayload,
)
from .host import _open, _read, _require
from .records import FileBinding, ToolInputs

_SELECTOR = Path("/etc/rkuarch/component-host-selector.json")
_AUTHORITY = object()
_PROJECT = ("uarch_contract", "rkuarch", "validation")
_EXTERNAL = (
    "pydantic",
    "pydantic_core",
    "annotated_types",
    "typing_extensions",
    "typing_inspection",
    "yaml",
)


def loads_runtime_job(
    data: str | bytes,
    *,
    trusted_registry_hash: str,
    trusted_profile_hash: str,
    expected_engine: NativeEngineIdentity,
) -> MappedEngineJob:
    """Installed B admission, including explicitly profiled transport test controls.

    Component scope uses complete operand/resource admission. Transport fixtures are
    test-only under checkpoint B; no generic production workload is added here.
    Every point is admitted, not just the selected point. This is data validation.
    """
    from .component_records import require_component_engine

    require_component_engine(expected_engine)
    value = strict_json_loads(data)
    anchors = dict(
        trusted_registry_hash=trusted_registry_hash, trusted_profile_hash=trusted_profile_hash
    )
    if value.get("workload_closure", {}).get("scope", {}).get("kind") == "component":
        job = loads_component_job(
            data, invocation="test", expected_engine=expected_engine, **anchors
        )
    else:
        job = validate_job(
            value, invocation="test", checkpoint="B", expected_engine=expected_engine, **anchors
        )
        _require(
            job.workload_closure.scope.kind == "transport_fixture", "component/test scope required"
        )
        admit(
            job.workload_closure,
            invocation="test",
            checkpoint="B",
            registry=job.registry,
            profile=job.profile,
            trusted_registry_hash=trusted_registry_hash,
            trusted_profile_hash=trusted_profile_hash,
        )
    _require(
        job.profile is not None and job.profile.format == "uarch-native-test-profile/2",
        "component profile/2 required",
    )
    return job


@dataclass(frozen=True)
class _PreparedComponent:
    """Private validated data only. Public launch never accepts this object as authority."""

    root: Path
    payload_file: FileBinding
    payload: ComponentPayload
    mode: str
    checks: tuple[tuple[Path, FileBinding], ...]
    immutable: bool

    def refresh(self) -> None:
        for root, binding in self.checks:
            _read(root, binding)
            if self.immutable:
                with _open(root, binding.path) as fd:
                    _require(
                        not os.fstat(fd).st_mode & 0o222, "immutable component payload required"
                    )
        _verify_imports(self.payload)

    def job(self, raw: bytes) -> MappedEngineJob:
        value = strict_json_loads(raw)
        _require(isinstance(value, dict), "component job object required")
        matches = [j for j in self.payload.jobs if j.file.byte_hash == sha256(raw)]
        _require(len(matches) == 1, "job outside exact component raw inventory")
        selected = matches[0]
        registry = NativeTestRegistry.model_validate(
            strict_json_loads(_read(self.root, self.payload.registry))
        )
        job = loads_runtime_job(
            raw,
            trusted_registry_hash=registry.registry_hash,
            trusted_profile_hash=selected.profile_hash,
            expected_engine=self.payload.engine,
        )
        _require(
            job.job_hash == selected.job_hash
            and job.admission.case_id == selected.case_id
            and job.profile is not None
            and job.profile.format == "uarch-native-test-profile/2",
            "component case/profile2 join",
        )
        return job

    @contextlib.contextmanager
    def executable(self) -> Iterator[int]:
        selected = next(x for x in self.payload.executables if x.mode == self.mode)
        with _open(self.root, selected.executable.path) as fd:
            st = os.fstat(fd)
            _require(
                bool(st.st_mode & 0o111) and not st.st_mode & 0o222,
                "component executable must be read-only and executable",
            )
            hasher = hashlib.sha256()
            while block := os.read(fd, 1024 * 1024):
                hasher.update(block)
            _require(
                "sha256:" + hasher.hexdigest() == selected.executable.byte_hash,
                "component executable changed",
            )
            os.lseek(fd, 0, os.SEEK_SET)
            yield fd


def _verify_imports(payload: ComponentPayload) -> None:
    root = Path(payload.consumers.import_root)
    _require(root.is_absolute(), "absolute component import root required")
    project = {str(root / x.path): x.byte_hash for x in payload.consumers.files}
    external = {str(Path("/") / x.path): x.byte_hash for x in payload.consumers.external_files}
    executable = payload.consumers.python_executable
    _require(
        str(Path(sys.executable).resolve()) == str(Path("/") / executable.path),
        "component Python executable origin",
    )
    _read(Path("/"), executable)
    for name, module in tuple(sys.modules.items()):
        top = name.split(".")[0]
        if top not in (*_PROJECT, *_EXTERNAL) and top not in sys.stdlib_module_names:
            continue
        raw = getattr(module, "__file__", None)
        if raw:
            path = str(Path(raw).resolve())
            pins = project if top in _PROJECT else external
            _require(
                path in pins and sha256(Path(path).read_bytes()) == pins[path],
                "component imported source identity: " + name,
            )
        elif top in _PROJECT:
            _require(
                all(Path(x).resolve().is_relative_to(root) for x in module.__path__),
                "component namespace origin: " + name,
            )


def _prepare_payload(
    root: Path, binding: FileBinding, *, mode: str, immutable: bool = False
) -> _PreparedComponent:
    """Synthetic tests may validate data here; this never returns execution authority."""
    _require(mode in ("debug", "release"), "explicit component mode required")
    reads: dict[tuple[Path, str], FileBinding] = {}

    def read(file: FileBinding, base: Path = root) -> bytes:
        data = _read(base, file)
        previous = reads.setdefault((base, file.path), file)
        _require(previous.byte_hash == file.byte_hash, "conflicting component file bindings")
        return data

    def record(cls: Any, file: FileBinding) -> Any:
        return cls.model_validate(strict_json_loads(read(file)))

    payload = record(ComponentPayload, binding)
    build = record(ComponentBuildInputs, payload.build_inputs)
    trust = record(ComponentBuildTrust, build.trust_file)
    tools = record(ToolInputs, build.tool_inputs_file)
    _require(
        content_hash(build) == payload.engine.implementation_hash, "component BuildInputs join"
    )
    _require(content_hash(trust) == build.trust_hash, "component construction trust join")
    _require(
        content_hash(tools) == build.tool_inputs_hash == payload.engine.compiler_lock_hash,
        "component ToolInputs join",
    )
    from .component_records import IMAGE

    _require(tools.image_digest == IMAGE, "accepted component image required")
    _require(all(x.rustflags == tools.flags for x in build.mode_configs), "component build flags")
    _require(
        trust.registry_file == payload.registry and trust.profiles == payload.profiles,
        "component trust registry/profile files",
    )
    for file in build.source_files:
        read(file)
    model = [
        x.model_dump(mode="json") for x in build.source_files if x.path in build.model_source_paths
    ]
    _require(
        content_hash(model) == build.model_inputs_hash == payload.engine.model.implementation_hash,
        "complete component model source identity",
    )
    for name in (
        "accepted_k1_pins",
        "cargo_lock",
        "full_metadata",
        "target_metadata",
        "feature_graph",
        "licence_inventory",
        "crate_checksum_inventory",
        "linker_and_os_inventory",
    ):
        read(getattr(tools, name))
    read(trust.semantics_file)
    selection = strict_json_loads(read(trust.selection))
    _require(
        selection.get("format") == "B-component-prospective-v3-selection/1"
        and selection.get("model") == ["native-intervals", "2"]
        and selection.get("observations") == "uarch-native-observations/3"
        and selection.get("checker") == payload.consumers.checker,
        "component independent selection route",
    )
    promised = {
        row["case_id"]: row for row in selection["rows"] if row["expected_layer"] == "result"
    }
    _require(
        set(promised) == {item.case_id for item in payload.jobs},
        "complete selected positive inventory",
    )
    registry = record(NativeTestRegistry, payload.registry)
    _require(registry.registry_hash == trust.registry_hash, "component registry hash")
    profiles = {}
    expected_cases: set[tuple[str, str]] = set()
    for file in payload.profiles:
        profile = record(NativeTestProfile, file)
        _require(profile.format == "uarch-native-test-profile/2", "component profile/2 required")
        _require(profile.profile_hash not in profiles, "duplicate component profile")
        profiles[profile.profile_hash] = profile
        expected_cases.update((profile.profile_hash, e.case_id) for e in profile.entries)
    seen_cases = set()
    for item in payload.jobs:
        raw = read(item.file)
        job = loads_runtime_job(
            raw,
            trusted_registry_hash=registry.registry_hash,
            trusted_profile_hash=item.profile_hash,
            expected_engine=payload.engine,
        )
        _require(
            job.profile == profiles.get(item.profile_hash)
            and job.job_hash == item.job_hash
            and job.admission.case_id == item.case_id,
            "component selected closure join",
        )
        promise = promised[item.case_id]
        assert job.profile is not None
        _require(
            job.profile.model_dump(mode="json") == promise["profile"]
            and job.bundle_hash == promise["bundle_hash"]
            and job.point_hash == promise["point_hash"]
            and job.mapped_point.task_graph.graph_hash == promise["graph_hash"]
            and job.workload_closure.mapping_policy.model_dump(mode="json") == promise["policy"],
            "component engine-free selection/closure/policy promise",
        )
        seen_cases.add((item.profile_hash, item.case_id))
    _require(seen_cases == expected_cases, "complete component profile/case inventory")
    for executable in payload.executables:
        receipt = record(ComponentBuildReceipt, executable.receipt)
        _require(
            receipt.engine == payload.engine
            and receipt.mode == executable.mode
            and receipt.executable == executable.executable,
            "component receipt/executable join",
        )
        _require(
            receipt.generated_identity.path in build.generated_identity_output_paths,
            "component generated identity path",
        )
        for file in (
            receipt.executable,
            receipt.generated_identity,
            receipt.build_log,
            receipt.environment,
            receipt.loader_observations,
        ):
            read(file)
    source_pins = {x.path: x.byte_hash for x in build.source_files}
    for file in payload.consumers.files:
        _require(
            source_pins.get(file.path) == file.byte_hash,
            "component consumer/build source closure join",
        )
        read(file, Path(payload.consumers.import_root))
    for file in payload.consumers.external_files:
        read(file, Path("/"))
    read(payload.consumers.python_executable, Path("/"))
    read(payload.consumers.observation_contract)
    prepared = _PreparedComponent(
        root,
        binding,
        payload,
        mode,
        tuple((base, file) for (base, _), file in reads.items()),
        immutable,
    )
    prepared.refresh()
    return prepared


class ComponentSession:
    """One independently authorized bounded session. Call budgets are not public permission."""

    def __init__(
        self,
        prepared: _PreparedComponent,
        authority_files: tuple[tuple[Path, FileBinding], ...],
        *,
        token: object,
    ) -> None:
        _require(token is _AUTHORITY, "independent component authority required")
        self._prepared = prepared
        self._authority_files = authority_files
        self._token = token
        self._deadline = time.monotonic() + prepared.payload.budget.session_seconds
        self._remaining = prepared.payload.budget.calls
        self._lock = threading.Lock()

    def check(self) -> None:
        _require(self._token is _AUTHORITY, "independent component authority required")
        for root, file in self._authority_files:
            _read(root, file)
        self._prepared.refresh()

    def claim(self) -> _PreparedComponent:
        _require(self._token is _AUTHORITY, "independent component authority required")
        with self._lock:
            _require(
                time.monotonic() < self._deadline and self._remaining > 0,
                "component session budget exhausted",
            )
            self.check()
            self._remaining -= 1
            return self._prepared


def prepare_component(*, mode: str) -> ComponentSession:
    """Only the fixed independently installed component selector can authorize launch."""
    _require(mode in ("debug", "release"), "explicit component mode required")
    with _open(_SELECTOR.parent, _SELECTOR.name) as fd:
        st = os.fstat(fd)
        _require(
            st.st_uid == 0 and not st.st_mode & 0o022,
            "component selector must be root-owned and protected",
        )
        with os.fdopen(os.dup(fd), "rb") as stream:
            selector_raw = stream.read()
            selector = ComponentHostSelector.model_validate(strict_json_loads(selector_raw))
    root = Path(selector.repository)
    record_file = FileBinding(path=selector.record_path, byte_hash=selector.record_byte_hash)
    record = ComponentHostRecord.model_validate(strict_json_loads(_read(root, record_file)))
    subject = {"runtime_payload_byte_hash": record.payload.byte_hash}
    decision = strict_json_loads(_read(root, record.decision))
    _require(
        decision
        == {
            "format": "uarch-component-human-first-use-decision/1",
            "accepted_by": "Javid (@jjaffari)",
            "reply": "yes",
            "subject": subject,
        },
        "exact component human decision required",
    )
    review = strict_json_loads(_read(root, record.independent_review))
    _require(
        isinstance(review, dict)
        and review.get("format") == "uarch-component-runtime-review/1"
        and review.get("subject") == subject
        and review.get("read_audit_complete") is True
        and review.get("selected_support_current") is True,
        "independent component runtime/read/currentness review required",
    )
    prepared = _prepare_payload(root, record.payload, mode=mode, immutable=True)
    return ComponentSession(
        prepared,
        tuple((root, f) for f in (record_file, record.decision, record.independent_review))
        + ((_SELECTOR.parent, FileBinding(path=_SELECTOR.name, byte_hash=sha256(selector_raw))),),
        token=_AUTHORITY,
    )
