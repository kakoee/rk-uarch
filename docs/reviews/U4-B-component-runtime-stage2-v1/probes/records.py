"""Additive preparation records, derived from frozen inputs and attributed saved evidence."""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from validation.component.runtime_literals import INPUTS, METADATA, OUTPUTS

source = Path(sys.argv[1])
out = Path(sys.argv[2])
base = Path("/tmp/u4-a-runtime-build-cc899d2/source/private-component")
old = Path("/tmp/u4-a-runtime-build-c67d558")
selection = json.loads((base / "selection.json").read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(n, v):
    (out / n).write_text(json.dumps(v, sort_keys=True, indent=2) + "\n")


site = "native/crates/uarch-engine/src/component_admission.rs"
assert sha(source / site) == sha(old / "source" / site)
negative = []
for row in selection["rows"]:
    if row["expected_layer"] == "result":
        continue
    case = row["case_id"]
    jpath = base / "jobs" / (case + ".json")
    j = json.loads(jpath.read_bytes())
    ep = old / "outputs/debug/selected" / (case + ".json")
    origin = "A c67d558 cfg(test) debug execution, inherited; no new B native execution"
    newer = Path("/tmp/u4-a-runtime-build-cc899d2/outputs/debug/focused") / (case + ".json")
    if newer.exists():
        ep = newer
        origin = "A cc899d2 cfg(test) debug focused execution, inherited; no new B native execution"
    envelope = json.loads(ep.read_bytes())
    g = j["mapped_point"]["task_graph"]
    h = j["workload_closure"]["hardware_spec"]
    buffers = {b["id"]: b for b in g["buffers"]}
    jobs = {t["id"]: t for t in g["jobs"]}
    parents = {k: set() for k in jobs}
    for e in g["dependencies"]:
        parents[e["after"]].add(e["before"])
    for _ in jobs:
        for k in jobs:
            parents[k].update(set().union(*(parents[x] for x in list(parents[k]))))
    code, message = envelope["code"], envelope["message"]
    if row["expected_layer"] == "profile":
        entry = next(e for e in j["profile"]["entries"] if e["case_id"] == case)
        assert entry["expected_outcome"] != "success"
        derivation = dict(
            guard="profile positive admission",
            entry_outcome=entry["expected_outcome"],
            not_a_capacity_test=True,
        )
    elif code in ("CapacityExceeded", "SramCapacityExceeded"):
        b = buffers[message]
        core = h["cores"]["core_type"]
        capacity = (
            h["memory"]["dram"]["capacity_bytes"]
            if b["space"] == "hbm"
            else core["sram"]["bytes"]
            if b["space"] == "sram"
            else core["matrix_engine"]["accumulator_bytes"]
        )["value"]
        end = b["offset_bytes"] + b["size_bytes"]
        assert end > capacity
        derivation = dict(
            guard="allocation extent exceeds capacity",
            buffer=message,
            space=b["space"],
            offset_bytes=b["offset_bytes"],
            size_bytes=b["size_bytes"],
            end_bytes=end,
            capacity_bytes=capacity,
            excess_bytes=end - capacity,
        )
    elif message == "accumulator producer must use this buffer":
        b = next(
            b
            for b in buffers.values()
            if b["space"] == "accumulator"
            and b["producer_id"] is not None
            and jobs[b["producer_id"]].get("accumulator_buffer_id") != b["id"]
        )
        derivation = dict(
            guard="declared producer does not use accumulator",
            buffer=b["id"],
            producer=b["producer_id"],
            producer_accumulator=jobs[b["producer_id"]].get("accumulator_buffer_id"),
        )
    elif message == "accumulator owner":
        b = next(
            b
            for b in buffers.values()
            if b["space"] == "accumulator"
            and b["producer_id"]
            and jobs[b["producer_id"]]["core_id"] != b["core_id"]
        )
        derivation = dict(
            guard="producer/buffer owner mismatch",
            buffer=b["id"],
            buffer_core=b["core_id"],
            producer_core=jobs[b["producer_id"]]["core_id"],
        )
    elif message == "accumulator use before production":
        uses = [
            dict(
                user=t["id"],
                producer=buffers[t["accumulator_buffer_id"]]["producer_id"],
                ancestors=sorted(parents[t["id"]]),
            )
            for t in jobs.values()
            if t["kind"] == "compute"
            and buffers[t["accumulator_buffer_id"]]["producer_id"] not in (None, t["id"])
            and buffers[t["accumulator_buffer_id"]]["producer_id"] not in parents[t["id"]]
        ]
        assert uses
        derivation = dict(guard="producer is not an ancestor of use", uses=uses)
    elif message.startswith("final consumers "):
        b = buffers[message.split()[-1]]
        uses = {t["id"] for t in jobs.values() if t.get("accumulator_buffer_id") == b["id"]}
        terminal = sorted(x for x in uses if not any(x in parents[y] for y in uses))
        assert terminal != b["final_consumer_ids"]
        derivation = dict(
            guard="complete terminal user set mismatch",
            buffer=b["id"],
            required_terminal=terminal,
            declared=b["final_consumer_ids"],
        )
    else:
        assert code == "LiveBufferAlias"
        x, y = [buffers[k] for k in message.split("/")]
        overlap = max(x["offset_bytes"], y["offset_bytes"]) < min(
            x["offset_bytes"] + x["size_bytes"], y["offset_bytes"] + y["size_bytes"]
        )

        def before(a, b, parents=parents):
            return (
                bool(a["final_consumer_ids"])
                and b["producer_id"]
                and all(u in parents[b["producer_id"]] for u in a["final_consumer_ids"])
            )

        assert overlap and not before(x, y) and not before(y, x)
        derivation = dict(
            guard="overlapping storage without complete final-consumer ordering",
            buffers=[x["id"], y["id"]],
            overlap=True,
        )
    if newer.exists():
        receipts = Path("/tmp/u4-b-runtime-joined-audit-01/evidence/final/native-probes")
        witness_path = next(
            p
            for p in receipts.glob("*/receipt.json")
            if json.loads(p.read_bytes())["raw_input_byte_hash"] == "sha256:" + sha(jpath)
            and json.loads(p.read_bytes())["semantic_status"] == 2
        )
        witness = json.loads(witness_path.read_bytes())
        assert witness["runtime_entries"] == 0
        assert witness["semantic_output_byte_hash"] == "sha256:" + sha(ep)
        entry_evidence = dict(
            path=str(witness_path),
            sha256=sha(witness_path),
            runtime_entries=0,
            observed_input_sha256=sha(jpath),
            semantic_status=2,
            attribution=origin,
        )
    else:
        entry_path = ep.with_suffix(".runtime-entries")
        status_path = ep.with_suffix(".status")
        assert int(entry_path.read_text()) == 0 and int(status_path.read_text()) == 2
        observed_job = old / "source/private-component/jobs" / (case + ".json")
        observed = json.loads(observed_job.read_bytes())
        assert {k: v for k, v in observed.items() if k not in {"engine", "job_hash"}} == {
            k: v for k, v in j.items() if k not in {"engine", "job_hash"}
        }
        entry_evidence = dict(
            path=str(entry_path),
            sha256=sha(entry_path),
            runtime_entries=0,
            observed_input_sha256=sha(observed_job),
            semantic_status=2,
            status_path=str(status_path),
            status_sha256=sha(status_path),
            attribution=origin,
            transition=(
                "Prospective input differs only in engine/job_hash; "
                "observed input remains old identity"
            ),
        )
    negative.append(
        dict(
            case_id=case,
            input_sha256=sha(jpath),
            job_hash=j["job_hash"],
            engine=j["engine"],
            envelope=envelope,
            intended_guard=derivation,
            native_guard_source=dict(path=site, sha256=sha(source / site)),
            observed=dict(path=str(ep), sha256=sha(ep), attribution=origin),
            pointer_status="observed null; not a guard discriminator",
            runtime_entries_required=0,
            entry_evidence=entry_evidence,
            scope=(
                "Unsigned prospective expectation; not authority. "
                "Historical pending/not_run unchanged."
            ),
        )
    )
write(
    "negative-expectations-v1.json", dict(format="component-negative-expectations/1", rows=negative)
)
coverage = []
for r in selection["rows"]:
    if r["expected_layer"] == "result":
        assert set(r["expected"]) <= INPUTS | OUTPUTS | METADATA
        keys = {
            k: (
                "descriptive metadata, not checked as output"
                if k in METADATA
                else "input premise plus observed allocation"
                if k in INPUTS
                else "independent output literal"
            )
            for k in r["expected"]
        }
    else:
        keys = {
            k: (
                (
                    "Exact intended refusal; numeric input conditions independently "
                    "derived in negative-expectations-v1"
                )
                if k in {"outcome", "required_accumulator_bytes", "capacity_bytes"}
                else "historical metadata/arithmetic only; not a native duration claim"
            )
            for k in r["expected"]
        }
    coverage.append(
        dict(case_id=r["case_id"], expected=r["expected"], keys=keys, layer=r["expected_layer"])
    )
write(
    "expectation-coverage-v1.json",
    dict(
        format="component-expectation-coverage/1",
        selection_sha256=sha(base / "selection.json"),
        closed_positive_keys=sorted(INPUTS | OUTPUTS | METADATA),
        rows=coverage,
        unrepresentable_numeric_output_obligations=[],
    ),
)
pairs = [
    [f"v3:B-native-resource-{n}", f"v3:B2-resource-{n}"]
    for n in ("C04-carrier", "C06-small", "C07-hbm-1", "C07-sram-1")
]
removed = {p[1] for p in pairs}
write(
    "schedule-proposal-v1.json",
    dict(
        format="component-schedule-proposal/1",
        approved=False,
        executed=False,
        historical=dict(definitions=124, calls=1368, initial_calls=744, replay_calls=624),
        duplicate_capacity_pairs=pairs,
        negative_classes=dict(
            capacity_definitions=8,
            dependency_lifetime_owner_definitions=8,
            profile_definitions=4,
            distinct_capacity_conditions=4,
            distinct_dependency_lifetime_owner_guards=5,
            distinct_profile_guards=1,
        ),
        proposed=dict(
            cases=[r["case_id"] for r in selection["rows"] if r["case_id"] not in removed],
            definitions=120,
            calls=1344,
            positive_calls=1248,
            negative_calls=96,
            reason=(
                "Drop only four duplicate capacity placements. Retain both modes, "
                "three fresh processes, all 104 positive saved-input replays, "
                "every distinct negative mechanism and four profile cases."
            ),
        ),
        decisions=[
            (
                "Coordinator/human schedule gate decision before revised execution; "
                "no silent replacement of 124/1368"
            ),
            (
                "Durable replay verifies storage readback and producer independence; "
                "no additional independent reasoning"
            ),
        ],
        source_selection_sha256=sha(base / "selection.json"),
    ),
)
print(
    json.dumps(
        dict(
            negative_cases=len(negative),
            coverage_cases=len(coverage),
            guard_counts=Counter(n["intended_guard"]["guard"] for n in negative),
        )
    )
)
