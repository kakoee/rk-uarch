"""Synthetic transport and saved cc0-v3 output only; no native/Docker/public execution."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native import component_host, component_image
from rkuarch.engines.native.component_records import IMAGE
from tests.unit import test_component_runtime as fixtures
from validation.component import ordinary_eof_acceptance as consumer
from validation.component.runtime_checks import CHECKER

ROOT = Path(__file__).resolve().parents[2]


def put(path: Any, value: Any) -> None:
    path.write_text(canonical_json(value))


def reference(root: Any) -> Any:
    return {
        "path": str(root / "attempt.json"),
        "byte_hash": sha256((root / "attempt.json").read_bytes()),
        "guardian_files": {
            n: sha256((root / "container" / n).read_bytes()) for n in consumer.GUARD_FILES
        },
    }


@pytest.fixture
def synthetic(
    tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Any:
    root, binding, payload, _ = cast(Any, fixtures.prepared_payload).__wrapped__(tmp_path, request)
    prepared = component_host._prepare_payload(root, binding, mode="debug")
    raw = root / "job.json"
    job = json.loads(raw.read_bytes())
    row = json.loads((root / "selection.json").read_bytes())["rows"][0]
    pins = {}
    for folder in (
        "contract/uarch_contract",
        "validation/component",
        "src/rkuarch/engines/native",
        "native/tools",
    ):
        for path in (ROOT / folder).glob("*.py"):
            if not path.name.startswith("test_"):
                pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("parallel_core.py", "resource_limits.py"):
        path = ROOT / "docs/reviews/U4-B-K2-parallel-first-use-v1" / name
        pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    config = {
        "format": "component-eof-acceptance-inputs/1",
        "source": str(ROOT),
        "pins": pins,
        "checker": CHECKER,
        "inputs": {
            row["case_id"]: {
                "case_id": row["case_id"],
                "job_hash": job["job_hash"],
                "engine": job["engine"],
                "raw_input_sha256": sha256(raw.read_bytes()).removeprefix("sha256:"),
            }
        },
        "image": IMAGE,
        "payload_byte_hash": binding.byte_hash,
        "executables": {v["mode"]: v["executable"]["byte_hash"] for v in payload["executables"]},
        "timeout_s": 5,
        "caps": {"raw_input": 1048576, "stdout": 1048576, "stderr": 1024},
        "executable_cap": 1048576,
        "observation_contract": json.loads(
            (root / "private-component/observation-contract.json").read_bytes()
        ),
        "negatives": {},
    }
    resource = {
        "affinity": [0, 1],
        "effective_cpu_capacity": "2",
        "cpu_quotas": [[200000, 100000]],
        "available_memory_bytes": 4 * 1024**3,
        "cgroup_memory_limits": [[4 * 1024**3, 0]],
        "memory_headroom_bytes": 4 * 1024**3,
        "parent_and_safety_reserve_bytes": 512 * 1024**2,
        "per_worker_budget_bytes": 1024**3,
        "workers": 1,
        "task_count": 1,
    }
    resource.update(
        mount="/sys/fs/cgroup",
        membership="/test",
        mounted_root="/",
        observed_cgroups=[
            {
                "path": "/sys/fs/cgroup/test",
                "cpu.max": "200000 100000",
                "memory.max": str(4 * 1024**3),
                "memory.current": 0,
            },
            {
                "path": "/sys/fs/cgroup",
                "interface": "hierarchy-root-no-bandwidth-or-memory-interface",
            },
        ],
    )
    monkeypatch.setattr(
        component_image, "helpers", lambda: {"discover": lambda *args: deepcopy(resource)}
    )
    sequence = 0

    def guard(
        directory: Any, args: Any, *, timeout: Any, cap: Any, stderr_cap: Any, stdin_bytes: Any
    ) -> Any:
        nonlocal sequence
        sequence += 1
        cid, owner = f"{sequence:064x}", f"{sequence:032x}"
        directory.mkdir()
        (directory / "stdin").write_bytes(stdin_bytes)
        (directory / "stdout").write_bytes((root / "output.json").read_bytes())
        (directory / "stderr").write_bytes(b"")
        put(
            directory / "intent.json",
            {
                "owner": owner,
                "name": "u4-private-" + owner,
                "args": args,
                "timeout": timeout,
                "cap": cap,
                "stderr_cap": stderr_cap,
                "stdin": True,
            },
        )
        put(
            directory / "pre-existing.json",
            {"containers": [{"container_id": "f" * 64, "state": "exited"}]},
        )
        put(directory / "created.json", {"container_id": cid, "owner": owner})
        put(directory / "started.json", {"container_id": cid})
        cleanup = {
            "format": "private-container-cleanup/1",
            "container_id": cid,
            "owner": owner,
            "name": "u4-private-" + owner,
            "stopped": True,
            "removed": True,
            "exit_code": 0,
            "reason": "completed",
            "elapsed_seconds": 0.001,
            "pre_remove_state": {"Running": False},
        }
        put(directory / "cleanup.json", cleanup)
        return cleanup

    monkeypatch.setattr(component_image, "run_container", guard)

    def make(
        name: Any = "attempt", mode: Any = "debug", repetition: Any = 0, replay: Any = None
    ) -> Any:
        dest = tmp_path / name
        component_image._run_prepared_image(
            raw, replace(prepared, mode=mode), dest, repetition=repetition, replay=replay
        )
        return reference(dest)

    return make, row, config, prepared


def accept(ref: Any, row: Any, config: Any) -> Any:
    slot = json.loads(Path(ref["path"]).read_bytes())["slot"]
    return consumer.consume_attempt(ref, row, slot, config)


def reseal(ref: Any, edit: Any) -> Any:
    root = Path(ref["path"]).parent
    value = json.loads((root / "attempt.json").read_bytes())
    edit(value, root)
    put(root / "attempt.json", value)
    return reference(root)


def test_actual_adapter_to_independent_saved_output_consumer(synthetic: Any) -> None:
    make, row, config, _ = synthetic
    ref = make()
    ref = reseal(ref, lambda a, p: a.update(validation_passed=False))
    result = accept(ref, row, config)
    assert result["outcome"] == "success" and result["runtime_entries"] is None
    assert result["authority"] is None  # Adapter's validation boolean supplies no credit.


@pytest.mark.parametrize(
    "attack,match",
    [
        ("anchor", "admitted anchor"),
        ("engine", "execution identities"),
        ("payload", "execution identities"),
        ("status", "complete transport"),
        ("cap", "complete stream lengths"),
        ("deadline", "observed deadline"),
        ("owner", "owner join"),
        ("preexisting", "pre-existing"),
        ("cleanup", "cleanup completion"),
        ("argv", "bounded guardian invocation"),
        ("resources", "resource arithmetic"),
        ("observed_resources", "observations match arithmetic"),
        ("entry", "unobserved entries"),
        ("failed", "retained failure"),
        ("slot", "exact slot"),
    ],
)
def test_resealed_receipt_discriminators(synthetic: Any, attack: str, match: str) -> None:
    make, row, config, _ = synthetic
    ref = make()

    def edit(a: Any, p: Any) -> None:
        if attack == "anchor":
            a["admitted"]["job_hash"] = "sha256:" + "0" * 64
        if attack == "engine":
            a["engine"]["version"] = "wrong"
        if attack == "payload":
            a["payload_byte_hash"] = "sha256:" + "0" * 64
        if attack == "status":
            a["status"] = None
        if attack == "cap":
            a["stdout"]["truncated"] = True
        if attack == "deadline":
            a["ended_monotonic"] = a["deadline_monotonic"] + 1
        if attack == "entry":
            a["runtime_entries"] = 1
        if attack == "failed":
            a["failure_stage"] = "session-finalization"
        if attack == "slot":
            a["slot"]["repetition"] = True
        if attack == "observed_resources":
            a["resources"]["observed_cgroups"][0]["cpu.max"] = "100000 100000"
        if attack == "resources":
            a["resources"]["memory_headroom_bytes"] += 1
        if attack == "owner":
            path = p / "container/created.json"
            value = json.loads(path.read_bytes())
            value["owner"] = "b" * 32
            put(path, value)
        if attack == "preexisting":
            put(
                p / "container/pre-existing.json",
                {"containers": [{"container_id": a["container_id"], "state": "exited"}]},
            )
        if attack == "cleanup":
            a["cleanup"]["removed"] = False
            put(p / "container/cleanup.json", a["cleanup"])
        if attack == "argv":
            a["argv"][a["argv"].index("--network") + 1] = "host"
            path = p / "container/intent.json"
            value = json.loads(path.read_bytes())
            value["args"] = a["argv"]
            put(path, value)

    forged = reseal(ref, edit)
    with pytest.raises(ValueError, match=match):
        accept(forged, row, config)


def test_structural_and_literal_refusals_without_hash_mask(synthetic: Any) -> None:
    make, row, config, _ = synthetic
    ref = make()
    root = Path(ref["path"]).parent
    original = (root / "stdout").read_bytes()

    def forge(a: Any, p: Any) -> None:
        result = json.loads(original)
        item = next(
            x
            for x in result["observations"]["activities"]["records"]
            if x["request_id"] == "r02.00"
            and x["kind"] == "alignment"
            and x["subphase"] == "dma_issue"
        )
        item["predecessors"].append({"activity_id": "activity-00000027", "relation": "credit"})
        result["result_hash"] = content_hash(result, exclude=("result_hash",))
        data = canonical_json(result).encode()
        for name in ("stdout", "container/stdout"):
            (p / name).write_bytes(data)
        a["stdout"].update(
            byte_hash=sha256(data), observed_bytes=len(data), retained_bytes=len(data)
        )

    with pytest.raises(ValueError, match="credit|predecessor"):
        accept(reseal(ref, forge), row, config)
    fresh = make("valid")
    badrow = deepcopy(row)
    badrow["expected"]["duration_ps"] += 1
    with pytest.raises(ValueError, match="literal duration_ps"):
        accept(fresh, badrow, config)
    assert accept(fresh, row, config)["outcome"] == "success"


def test_retained_hash_missing_ledger_and_source_route_controls(synthetic: Any) -> None:
    make, row, config, _ = synthetic
    ref = make()
    root = Path(ref["path"]).parent
    data = (root / "stdout").read_bytes()
    (root / "stdout").write_bytes(b"tamper")
    with pytest.raises(ValueError, match="retained hash"):
        accept(ref, row, config)
    (root / "stdout").write_bytes(data)
    bad = deepcopy(ref)
    del bad["guardian_files"]["created.json"]
    with pytest.raises(ValueError, match="guardian bindings"):
        accept(bad, row, config)
    badconfig = deepcopy(config)
    badconfig["checker"] = "check_v2"
    with pytest.raises(ValueError, match="checker route"):
        accept(ref, row, badconfig)
    badconfig = deepcopy(config)
    del badconfig["pins"]["native/tools/component_container_guard.py"]
    with pytest.raises(ValueError, match="guardian/preparation closure"):
        accept(ref, row, badconfig)
    badconfig = deepcopy(config)
    badconfig["pins"]["validation/component/ordinary_eof_acceptance.py"] = "0" * 64
    with pytest.raises(ValueError, match="source mismatch"):
        accept(ref, row, badconfig)
    assert accept(ref, row, config)["outcome"] == "success"


def test_six_replay_sources_and_twelve_slot_parent_join(
    synthetic: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make, row, config, prepared = synthetic
    initial = [make(f"initial-{m}-{r}", m, r) for m in consumer.MODES for r in range(3)]
    assert len(consumer.admit_replay(initial, row, config)) == 6
    with pytest.raises(ValueError, match="six distinct"):
        consumer.admit_replay([initial[0]] * 6, row, config)
    _, descriptor = component_image.admit_image_replay(
        [(Path(r["path"]), r["byte_hash"]) for r in initial], prepared
    )
    import rkuarch.workload.mapped as producer

    monkeypatch.setattr(
        producer, "export_component_job", lambda *a, **k: pytest.fail("producer invoked")
    )
    replay = []
    for mode in consumer.MODES:
        for repeat in range(3):
            ref = make(f"replay-{mode}-{repeat}", mode, repeat, descriptor)
            ref["initial_receipts"] = initial
            replay.append(ref)
    refs = initial + replay
    parent_path = tmp_path / "parent.json"
    parent_value = {
        "format": "component-eof-parent-cleanup/1",
        "workers_joined": True,
        "outstanding": [],
        "complete": True,
        "attempts": refs,
        "container_ids": [json.loads(Path(r["path"]).read_bytes())["container_id"] for r in refs],
    }
    put(parent_path, parent_value)
    parent = {"path": str(parent_path), "byte_hash": sha256(parent_path.read_bytes())}
    assert consumer.consume_group(refs, parent, row, config)["calls"] == 12
    with pytest.raises(ValueError, match="group slots"):
        consumer.consume_group(refs[:-1], parent, row, config)
    omitted = tmp_path / "unreported-attempt" / "container"
    omitted.mkdir(parents=True)
    put(omitted / "intent.json", {"synthetic": "failed extra attempt must remain incomplete"})
    with pytest.raises(ValueError, match="every retained creation intent"):
        consumer.consume_group(refs, parent, row, config)
    (omitted / "intent.json").unlink()
    parent_value["outstanding"] = ["unknown"]
    put(parent_path, parent_value)
    parent["byte_hash"] = sha256(parent_path.read_bytes())
    with pytest.raises(ValueError, match="parent exact cleanup"):
        consumer.consume_group(refs, parent, row, config)
    original = Path(initial[0]["path"]).parent / "stdout"
    original.write_bytes(b"tamper")
    with pytest.raises(ValueError, match="retained hash"):
        accept(replay[0], row, config)


def test_d3_actual_schema_refusal_and_same_code_discrimination(
    synthetic: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use actual unapplied D3 transport core; synthetic refusal, not Rust guard evidence."""
    import importlib.util
    import sys
    from importlib.machinery import SourceFileLoader
    from types import SimpleNamespace

    make, row, config, prepared = synthetic
    # Capture the full-ledger synthetic guardian, then substitute only its semantic streams.
    guard = cast(Any, component_image).run_container
    envelope = {
        "code": "CapacityExceeded",
        "message": "DMA fragment count exceeds limit",
        "pointer": None,
    }
    received = dict(envelope)

    def negative_guard(directory: Any, args: Any, **kwargs: Any) -> Any:
        cleanup = guard(directory, args, **kwargs)
        (directory / "stdout").write_bytes(b"")
        (directory / "stderr").write_bytes(canonical_json(received).encode())
        cleanup["exit_code"] = 2
        put(directory / "cleanup.json", cleanup)
        return cleanup

    monkeypatch.setattr(component_image, "run_container", negative_guard)
    path = (
        ROOT
        / "docs/reviews/U4-A-component-activation-readiness-v1/proposals"
        / "component_negative-v6.py.txt"
    )
    loader = SourceFileLoader("B_synthetic_D3_proposal", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, loader.name, module)
    loader.exec_module(module)
    admitted = config["inputs"][row["case_id"]]
    source = "native/crates/uarch-engine/src/component_admission.rs"
    source_hash = hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
    provenance = {
        "case_id": row["case_id"],
        "input_sha256": admitted["raw_input_sha256"],
        "job_hash": admitted["job_hash"],
        "engine": admitted["engine"],
        "envelope": envelope,
        "runtime_entries_required": 0,
        "intended_guard": "synthetic exact-envelope wiring only",
        "native_guard_source": {"path": source, "sha256": source_hash},
        "evidence": "SYNTHETIC: no native input invalidity or guard reach claimed",
    }
    provenance_path = tmp_path / "synthetic-negative-provenance.json"
    put(provenance_path, provenance)
    pin = sha256(provenance_path.read_bytes())
    case = module.NegativeCase(
        case_id=row["case_id"],
        raw={"path": "job.json", "byte_hash": "sha256:" + admitted["raw_input_sha256"]},
        profile={
            "path": "profile.json",
            "byte_hash": sha256((tmp_path / "profile.json").read_bytes()),
        },
        expectation_provenance={"path": provenance_path.name, "byte_hash": pin},
        expected_envelope=envelope,
        layer="resource-preflight",
    )
    # Synthetic positive saved input drives a refusal transport mock. Do not claim D3 admission.
    monkeypatch.setattr(module, "_selected_raw", lambda *args: (tmp_path / "job.json").read_bytes())
    negative_row = dict(row, expected_layer="resource-preflight", expected_code=envelope["code"])
    config["negatives"][row["case_id"]] = {
        "admitted": admitted,
        "expected_layer": "resource-preflight",
        "envelope": envelope,
        "intended_guard": provenance["intended_guard"],
        "guard_source": source,
        "guard_source_sha256": source_hash,
        "provenance_path": str(provenance_path),
        "provenance_sha256": pin.removeprefix("sha256:"),
    }
    dest = tmp_path / "negative"
    module._run_negative_image(
        SimpleNamespace(component=prepared, refresh=lambda: None),
        case,
        dest,
        timeout_s=5,
        repetition=0,
    )
    ref = reference(dest)
    assert accept(ref, negative_row, config)["outcome"] == "CapacityExceeded"

    def forge(a: Any, root: Any) -> None:
        data = canonical_json(dict(envelope, message="complete output byte limit")).encode()
        for n in ("stderr", "container/stderr"):
            (root / n).write_bytes(data)
        a["stderr"].update(
            byte_hash=sha256(data), observed_bytes=len(data), retained_bytes=len(data)
        )
        a["validation_passed"] = True

    forged = reseal(ref, forge)
    with pytest.raises(ValueError, match="exact intended refusal envelope"):
        accept(forged, negative_row, config)
    # A narrow call-disconnection discriminator; source-byte fault is repeated privately.
    with monkeypatch.context() as scoped:
        scoped.setattr(consumer, "exact_refusal", lambda *args: None)
        assert accept(forged, negative_row, config)["outcome"] == "CapacityExceeded"
    with pytest.raises(ValueError, match="exact intended refusal envelope"):
        accept(forged, negative_row, config)


def test_import_origin_and_stream_symlink(synthetic: Any, tmp_path: Path) -> None:
    import shutil

    make, row, config, _ = synthetic
    ref = make()
    copied = tmp_path / "other-source"
    for name in config["pins"]:
        path = copied / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    wrong = dict(config, source=str(copied))
    with pytest.raises(ValueError, match="import origin"):
        accept(ref, row, wrong)
    stream = Path(ref["path"]).parent / "stdout"
    original = stream.read_bytes()
    target = tmp_path / "same-bytes"
    target.write_bytes(original)
    stream.unlink()
    stream.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        accept(ref, row, config)
    stream.unlink()
    stream.write_bytes(original)
    assert accept(ref, row, config)["outcome"] == "success"


def test_replay_slot_and_process_population(synthetic: Any) -> None:
    make, row, config, _ = synthetic
    refs = [make(f"initial-{m}-{r}", m, r) for m in consumer.MODES for r in range(3)]
    last = refs[-1]
    receipt = Path(last["path"])
    original = receipt.read_bytes()
    changed = reseal(last, lambda a, root: a["slot"].update(mode="release", repetition=1))
    with pytest.raises(ValueError, match="six initial slots"):
        consumer.admit_replay(refs[:-1] + [changed], row, config)
    receipt.write_bytes(original)
    first_id = json.loads(Path(refs[0]["path"]).read_bytes())["container_id"]

    def same_process(a: Any, root: Any) -> None:
        a["container_id"] = first_id
        a["process_identity"] = "docker:" + first_id + ":pid1"
        a["cleanup"]["container_id"] = first_id
        for name in ("created.json", "started.json", "cleanup.json"):
            path = root / "container" / name
            value = json.loads(path.read_bytes())
            value["container_id"] = first_id
            put(path, value)

    changed = reseal(last, same_process)
    with pytest.raises(ValueError, match="six fresh initial processes"):
        consumer.admit_replay(refs[:-1] + [changed], row, config)
