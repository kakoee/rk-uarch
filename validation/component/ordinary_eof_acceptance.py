"""Offline ordinary EOF evidence consumption; no launch, authority or entry witness.

References and acceptance inputs must be frozen independently of presented attempts.
The returned record binds inspected evidence; it does not authenticate its producer.
"""

from __future__ import annotations

import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256

from validation.component.checks import need
from validation.component.runtime_checks import CHECKER, consume_case, verify_sources
from validation.component.runtime_evidence import STREAM_CAP, exact_refusal, parse

GUARD_FILES = ("intent.json", "pre-existing.json", "created.json", "started.json", "cleanup.json")
MODES = ("debug", "release")


def read_bound(root: Path, name: str, pin: str, cap: int = STREAM_CAP) -> bytes:
    relative = Path(name)
    need(not relative.is_absolute() and ".." not in relative.parts, "relative retained path")
    path = root / relative
    need(not root.is_symlink(), "evidence root symlink")
    for part in (path, *path.parents):
        if part == root.parent:
            break
        need(not part.is_symlink(), "retained symlink")
    need(path.is_file() and path.stat().st_size <= cap, "bounded retained file")
    data = path.read_bytes()
    need(len(data) <= cap and sha256(data) == pin, "retained hash")
    return data


def verify_closure(config: dict[str, Any]) -> None:
    source, pins = Path(config["source"]).resolve(), config["pins"]
    verify_sources(source, pins)
    required = {str(p.relative_to(source)) for p in (source / "native/tools").glob("*.py")}
    required.update(
        "docs/reviews/U4-B-K2-parallel-first-use-v1/" + name
        for name in ("parallel_core.py", "resource_limits.py")
    )
    need(required <= pins.keys(), "ordinary guardian/preparation closure")
    # Hashing an unrelated export cannot attest the modules used by this consumer.
    for name, module in tuple(sys.modules.items()):
        if name.startswith(
            ("validation.component.", "rkuarch.engines.native.", "uarch_contract.", "native.tools.")
        ):
            origin = getattr(module, "__file__", None)
            if origin and not Path(origin).name.startswith("test_"):
                path = Path(origin).resolve()
                need(path.is_relative_to(source), "consumer import origin")
                need(str(path.relative_to(source)) in pins, "loaded consumer binding")


def _resources(value: dict[str, Any]) -> None:
    affinity = value["affinity"]
    need(bool(affinity) and len(set(affinity)) == len(affinity), "resource affinity")
    need(all(type(v) is int and v >= 0 for v in affinity), "resource affinity values")
    quotas, memory = value["cpu_quotas"], value["cgroup_memory_limits"]
    need(
        all(type(q) is int and type(p) is int and q > 0 and p > 0 for q, p in quotas), "CPU quotas"
    )
    need(
        all(type(m) is int and type(u) is int and m >= 0 and u >= 0 for m, u in memory),
        "memory limits",
    )
    observed = value["observed_cgroups"]
    mount, member = Path(value["mount"]), Path(value["membership"])
    need(
        mount.is_absolute()
        and member.is_absolute()
        and ".." not in mount.parts
        and ".." not in member.parts
        and value["mounted_root"] == "/",
        "visible resource hierarchy",
    )
    current = mount / member.relative_to("/")
    paths = []
    while True:
        paths.append(str(current))
        if current == mount:
            break
        current = current.parent
    need([item["path"] for item in observed] == paths, "complete observed resource ancestors")
    recorded_quotas, recorded_memory = [], []
    for item in observed:
        if "interface" in item:
            need(
                item
                == {
                    "path": str(mount),
                    "interface": "hierarchy-root-no-bandwidth-or-memory-interface",
                },
                "resource root interface",
            )
            continue
        q, period = item["cpu.max"].split()
        need(int(period) > 0 and (q == "max" or int(q) > 0), "recorded CPU limit")
        if q != "max":
            recorded_quotas.append([int(q), int(period)])
        used, limit = item["memory.current"], item["memory.max"]
        need(
            type(used) is int and used >= 0 and (limit == "max" or int(limit) >= 0),
            "recorded memory limit",
        )
        if limit != "max":
            recorded_memory.append([int(limit), used])
    need(
        quotas == recorded_quotas and memory == recorded_memory,
        "resource observations match arithmetic",
    )
    available = value["available_memory_bytes"]
    need(type(available) is int and available >= 0, "available memory")
    cpu = min([Fraction(len(affinity))] + [Fraction(q, p) for q, p in quotas])
    headroom = min([available] + [max(0, m - u) for m, u in memory])
    workers = min(1, math.floor(cpu), (headroom - 512 * 1024**2) // 1024**3)
    need(
        workers == 1
        and value["workers"] == workers
        and value["task_count"] == 1
        and value["effective_cpu_capacity"] == str(cpu)
        and value["memory_headroom_bytes"] == headroom
        and value["parent_and_safety_reserve_bytes"] == 512 * 1024**2
        and value["per_worker_budget_bytes"] == 1024**3,
        "default resource arithmetic",
    )


def consume_attempt(
    reference: dict[str, Any], row: dict[str, Any], slot: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """Reconsume a frozen receipt, its streams and separately pinned guardian ledger."""
    need(config["format"] == "component-eof-acceptance-inputs/1", "ordinary acceptance format")
    need(config["checker"] == CHECKER, "matching checker route")
    verify_closure(config)
    receipt = Path(reference["path"])
    root = receipt.parent
    attempt = json.loads(read_bound(root, receipt.name, reference["byte_hash"], 1024**2))
    admitted = config["inputs"][row["case_id"]]
    need(admitted["case_id"] == row["case_id"], "selected case")
    positive = row["expected_layer"] == "result"
    # D3 v6's wire subset omits job_hash; the independently frozen full anchor
    # still binds raw job_hash below. Never infer a missing anchor from output.
    wire_admitted = admitted if positive else {k: v for k, v in admitted.items() if k != "job_hash"}
    need(attempt["admitted"] == wire_admitted, "independent admitted anchor")
    need(
        attempt["format"] == "component-eof-attempt/1"
        and attempt["transport_kind"] == "ordinary-eof"
        and attempt["runtime_entries"] is None,
        "ordinary format and unobserved entries",
    )
    need(
        slot["phase"] in ("initial", "replay")
        and slot["mode"] in MODES
        and type(slot["repetition"]) is int
        and 0 <= slot["repetition"] < 3
        and attempt["slot"] == slot
        and attempt["mode"] == slot["mode"],
        "exact slot",
    )
    need(
        attempt["engine"] == admitted["engine"]
        and attempt["image"] == config["image"]
        and attempt["payload_byte_hash"] == config["payload_byte_hash"]
        and attempt["executable_byte_hash"] == config["executables"][slot["mode"]],
        "frozen execution identities",
    )
    need(
        attempt["transport_complete"] is True and type(attempt["status"]) is int,
        "complete transport",
    )
    need(
        attempt.get("failure_stage") is None
        and not attempt.get("transport_error")
        and not attempt.get("validation_error")
        and not attempt.get("finalization_error"),
        "retained failure",
    )
    start, end, deadline, timeout = (
        attempt[k]
        for k in ("started_monotonic", "ended_monotonic", "deadline_monotonic", "timeout_s")
    )
    need(
        all(type(v) in (int, float) and math.isfinite(v) for v in (start, end, deadline, timeout)),
        "finite deadline",
    )
    need(
        0 < timeout <= min(30, config["timeout_s"])
        and 0 <= start <= end <= deadline
        and deadline == start + timeout
        and attempt["deadline_exceeded"] is False,
        "observed deadline",
    )
    _resources(attempt["resources"])
    blobs = {}
    for name in ("raw_input", "stdout", "stderr"):
        binding = attempt[name]
        need(isinstance(binding, dict) and binding["path"] == name, "retained stream binding")
        data = read_bound(root, name, binding["byte_hash"], config["caps"][name])
        if name == "raw_input":
            need(
                len(data) == binding["bytes"]
                and sha256(data).removeprefix("sha256:") == admitted["raw_input_sha256"],
                "frozen raw input",
            )
        else:
            need(
                binding["truncated"] is False
                and len(data) == binding["observed_bytes"] == binding["retained_bytes"],
                "complete stream lengths",
            )
        blobs[name] = data
    job = json.loads(blobs["raw_input"])
    need(
        job["job_hash"] == admitted["job_hash"]
        and job["engine"] == admitted["engine"]
        and job["admission"]["case_id"] == admitted["case_id"],
        "raw anchor joins",
    )
    need(attempt["guardian_records"] == "container/", "guardian directory")
    need(set(reference["guardian_files"]) == set(GUARD_FILES), "complete guardian bindings")
    guards = {
        name: json.loads(
            read_bound(root, "container/" + name, reference["guardian_files"][name], 1024**2)
        )
        for name in GUARD_FILES
    }
    intent, prior, created, started, cleanup = (guards[n] for n in GUARD_FILES)
    identity, owner = created["container_id"], created["owner"]
    need(
        isinstance(identity, str) and re.fullmatch("[0-9a-f]{64}", identity) is not None,
        "full container ID",
    )
    need(isinstance(owner, str) and re.fullmatch("[0-9a-f]{32}", owner) is not None, "owner token")
    need(
        intent["owner"] == owner == cleanup["owner"]
        and intent["name"] == cleanup["name"] == "u4-private-" + owner,
        "guardian owner join",
    )
    need(
        started["container_id"] == cleanup["container_id"] == attempt["container_id"] == identity
        and attempt["process_identity"] == "docker:" + identity + ":pid1",
        "guardian process join",
    )
    ids = [v["container_id"] for v in prior["containers"]]
    need(
        all(re.fullmatch("[0-9a-f]{64}", x) for x in ids)
        and len(set(ids)) == len(ids)
        and identity not in ids,
        "preserve pre-existing containers",
    )
    need(
        cleanup["format"] == "private-container-cleanup/1"
        and cleanup["stopped"] is True
        and cleanup["removed"] is True
        and cleanup["reason"] == "completed"
        and type(cleanup["exit_code"]) is int
        and cleanup["exit_code"] == attempt["status"]
        and not any(k in cleanup for k in ("error", "cleanup_error", "never_created")),
        "guardian cleanup completion",
    )
    need(attempt["cleanup"] == cleanup, "embedded cleanup agrees with retained ledger")
    args = [
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "1g",
        "--cpus",
        "1",
        "--ulimit",
        "nofile=256:256",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=bind,src={root.resolve() / 'engine'},dst=/engine,readonly",
        "--entrypoint",
        "/usr/bin/env",
        config["image"],
        "-i",
        "/engine",
        "--protocol",
        "uarch-engine/3",
    ]
    need(
        intent["args"] == attempt["argv"] == args
        and intent["stdin"] is True
        and intent["timeout"] == timeout
        and intent["cap"] == config["caps"]["stdout"]
        and intent["stderr_cap"] == config["caps"]["stderr"],
        "exact bounded guardian invocation",
    )
    read_bound(root, "engine", attempt["executable_byte_hash"], config["executable_cap"])
    for name in blobs:
        saved = "stdin" if name == "raw_input" else name
        need(
            read_bound(root, "container/" + saved, sha256(blobs[name]), config["caps"][name])
            == blobs[name],
            "guardian stream equality",
        )
    positive = row["expected_layer"] == "result"
    if positive:
        need(attempt["status"] == 0 and blobs["stderr"] == b"", "success transport envelope")
        result = parse(blobs["stdout"])
        consume_case(
            job,
            result,
            row,
            checker_id=config["checker"],
            source=Path(config["source"]),
            pins=config["pins"],
            expected=config["observation_contract"],
            input_sha256=admitted["raw_input_sha256"],
            raw_input=blobs["raw_input"],
            admitted=admitted,
        )
        outcome = "success"
    else:
        need(
            slot["phase"] == "initial" and attempt["status"] == 2 and blobs["stdout"] == b"",
            "refusal transport envelope",
        )
        negative = config["negatives"][row["case_id"]]
        need(
            negative["admitted"] == admitted
            and negative["expected_layer"] == row["expected_layer"]
            and negative["envelope"]["code"] == row["expected_code"]
            and bool(negative["intended_guard"]),
            "independent refusal provenance",
        )
        read_bound(
            Path(config["source"]),
            negative["guard_source"],
            "sha256:" + negative["guard_source_sha256"],
        )
        provenance_path = Path(negative["provenance_path"])
        provenance = json.loads(
            read_bound(
                provenance_path.parent,
                provenance_path.name,
                "sha256:" + negative["provenance_sha256"],
            )
        )
        need(
            provenance["case_id"] == admitted["case_id"]
            and provenance["input_sha256"] == admitted["raw_input_sha256"]
            and provenance["job_hash"] == admitted["job_hash"]
            and provenance["engine"] == admitted["engine"]
            and provenance["envelope"] == negative["envelope"]
            and provenance["runtime_entries_required"] == 0
            and provenance["intended_guard"] == negative["intended_guard"]
            and provenance["native_guard_source"]
            == {"path": negative["guard_source"], "sha256": negative["guard_source_sha256"]}
            and attempt["expected_envelope"] == negative["envelope"]
            and attempt["expectation_provenance"]["byte_hash"]
            == "sha256:" + negative["provenance_sha256"],
            "frozen negative provenance",
        )
        exact_refusal(blobs["stderr"], negative["envelope"])
        outcome = row["expected_code"]
    if slot["phase"] == "initial":
        need(attempt.get("replay_descriptor") is None, "initial has no replay descriptor")
    else:
        descriptor = attempt["replay_descriptor"]
        refs = reference["initial_receipts"]
        need(
            descriptor
            == {
                "phase": "replay",
                "initial_receipts": [
                    {"path": str(Path(r["path"]).resolve()), "byte_hash": r["byte_hash"]}
                    for r in refs
                ],
                "raw_input_byte_hash": sha256(blobs["raw_input"]),
            },
            "exact replay descriptor",
        )
        initial = admit_replay(refs, row, config)
        need(
            attempt["process_identity"] not in {v["process_identity"] for v in initial}
            and all(v["streams"] == {n: sha256(b) for n, b in blobs.items()} for v in initial),
            "replay fresh process and byte equality",
        )
    return {
        "format": "component-eof-acceptance/1",
        "authority": None,
        "runtime_entries": None,
        "reference": reference,
        "acceptance_inputs_byte_hash": sha256(canonical_json(config).encode()),
        "selected_definition_byte_hash": sha256(canonical_json(row).encode()),
        "slot": slot,
        "outcome": outcome,
        "container_id": identity,
        "process_identity": attempt["process_identity"],
        "streams": {n: sha256(b) for n, b in blobs.items()},
        "consumer_source_pins": config["pins"],
        "claim": "offline evidence consistency, not producer attestation or public execution",
    }


def admit_replay(
    references: list[dict[str, Any]], row: dict[str, Any], config: dict[str, Any]
) -> list[dict[str, Any]]:
    need(
        row["expected_layer"] == "result"
        and len(references) == 6
        and len({str(Path(r["path"]).resolve()) for r in references}) == 6,
        "six distinct positive initial references",
    )
    records = []
    for ref in references:
        path = Path(ref["path"])
        slot = json.loads(read_bound(path.parent, path.name, ref["byte_hash"], 1024**2))["slot"]
        need(slot["phase"] == "initial", "replay source must be initial")
        records.append(consume_attempt(ref, row, slot, config))
    need(
        {(v["slot"]["mode"], v["slot"]["repetition"]) for v in records}
        == {(m, r) for m in MODES for r in range(3)},
        "six initial slots",
    )
    need(len({v["process_identity"] for v in records}) == 6, "six fresh initial processes")
    need(
        len({json.dumps(v["streams"], sort_keys=True) for v in records}) == 1,
        "six initial byte equality",
    )
    return records


def consume_group(
    references: list[dict[str, Any]],
    parent: dict[str, str],
    row: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Offline group completion only; parent orchestration and budgets are not executed."""
    records = []
    for ref in references:
        path = Path(ref["path"])
        slot = json.loads(read_bound(path.parent, path.name, ref["byte_hash"], 1024**2))["slot"]
        records.append(consume_attempt(ref, row, slot, config))
    phases = ("initial", "replay") if row["expected_layer"] == "result" else ("initial",)
    wanted = {(p, m, r) for p in phases for m in MODES for r in range(3)}
    need(
        len(records) == len(wanted)
        and {(v["slot"]["phase"], v["slot"]["mode"], v["slot"]["repetition"]) for v in records}
        == wanted,
        "exact group slots",
    )
    need(len({v["process_identity"] for v in records}) == len(records), "fresh group processes")
    need(
        len({json.dumps(v["streams"], sort_keys=True) for v in records}) == 1, "group byte equality"
    )
    initials = {
        r["reference"]["path"]: r["reference"]["byte_hash"]
        for r in records
        if r["slot"]["phase"] == "initial"
    }
    for record in records:
        if record["slot"]["phase"] == "replay":
            need(
                {r["path"]: r["byte_hash"] for r in record["reference"]["initial_receipts"]}
                == initials,
                "group replay uses this initial group",
            )
    path = Path(parent["path"])
    scope = path.parent.resolve()
    expected_intents = {
        Path(ref["path"]).parent.resolve() / "container/intent.json" for ref in references
    }
    need(all(p.is_relative_to(scope) for p in expected_intents), "parent task scope")
    need(
        not path.parent.is_symlink() and all(not p.is_symlink() for p in scope.rglob("*")),
        "parent scope symlink",
    )
    need(
        {p.resolve() for p in scope.rglob("intent.json")} == expected_intents,
        "parent covers every retained creation intent",
    )
    final = json.loads(read_bound(path.parent, path.name, parent["byte_hash"], 1024**2))
    need(
        final["format"] == "component-eof-parent-cleanup/1"
        and final["workers_joined"] is True
        and final["outstanding"] == []
        and final["complete"] is True
        and final["attempts"] == references
        and sorted(final["container_ids"]) == sorted(v["container_id"] for v in records),
        "parent exact cleanup completion",
    )
    return {
        "format": "component-eof-group-consumption/1",
        "complete": True,
        "authority": None,
        "calls": len(records),
        "parent": parent,
        "records": records,
        "scope": "offline group consistency; campaign budgets and public execution not established",
    }
