"""Literal O2 transient @2 /2 carrier; SYNTHETIC unit evidence, no native execution."""

from copy import deepcopy
from typing import Any

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedBundle, MappedEngineJob, canonical_owners

from validation.component.consistent_carriers import control, synchronize
from validation.component.corpus import graph, materialize, resident_input
from validation.component.synthetic_carrier import synthetic_job

# Five 3x5x7 bf16 tiles: 32 + 1 + 513 + 1 cycles each at 1 GHz.
ORDER = ("a", "b", "c", "d", "e")
SPANS = {name: (i * 547000, (i + 1) * 547000) for i, name in enumerate(ORDER)}
READY = dict(a=0, b=547000, c=1094000, d=1094000, e=2188000)


def transient_control() -> tuple[Any, Any]:
    bundle = resident_input(3, 5, 7)
    template = deepcopy(bundle)
    g = graph(bundle)
    g.update(jobs=[], buffers=[], coverage=[], dependencies=[])
    bundle["scope"]["ops"] = []
    bundle["scope"]["op_ids"] = []
    bundle["points"][0]["identity"]["op_ids"] = []
    bundle["mapping_policy"]["version"] = "2"
    for i, name in enumerate(ORDER):
        op = deepcopy(template["scope"]["ops"][0])
        op["id"] = f"g{i}"
        bundle["scope"]["ops"].append(op)
        bundle["scope"]["op_ids"].append(op["id"])
        bundle["points"][0]["identity"]["op_ids"].append(op["id"])
        t = deepcopy(graph(template)["jobs"][0])
        t.update(
            id=name,
            op_id=op["id"],
            accumulator_buffer_id=("bacc" if name in "bcd" else name + "acc"),
        )
        t["operand_buffers"] = {k: name + v for k, v in t["operand_buffers"].items()}
        g["jobs"].append(t)
        cover = deepcopy(graph(template)["coverage"][0])
        cover.update(job_id=name, op_id=op["id"])
        g["coverage"].append(cover)
        for buf in deepcopy(graph(template)["buffers"]):
            if buf["space"] == "accumulator" and name in "cd":
                continue
            buf["id"] = name + buf["id"]
            if buf["op_id"] is not None:
                buf["op_id"] = op["id"]
            buf["producer_id"] = name if buf["producer_id"] == "c" else buf["producer_id"]
            buf["final_consumer_ids"] = [name if x == "c" else x for x in buf["final_consumer_ids"]]
            if buf["space"] == "accumulator":
                buf.update(
                    producer_id=name, final_consumer_ids=["c", "d"] if name == "b" else [name]
                )
                buf["offset_bytes"] = {"a": 0, "b": 256, "e": 512}[name]
            else:
                buf["offset_bytes"] += i * 2048
                buf["bank"] = buf["offset_bytes"] // 524288
            g["buffers"].append(buf)
    g["dependencies"] = [
        dict(before=x, after=y)
        for x, y in [("a", "b"), ("b", "c"), ("b", "d"), ("c", "e"), ("d", "e")]
    ]
    item = materialize("SYNTHETIC-O2-TRANSIENT-UNIT", bundle, dict(outcome="success"))
    b = MappedBundle.model_validate(item["bundle"])
    point = b.points[0]
    raw = synthetic_job("C02").model_dump(mode="json")
    raw.update(
        bundle_hash=b.bundle_hash,
        point_hash=point.payload_hash,
        mapped_point=point.model_dump(mode="json"),
        workload_closure=b.model_dump(mode="json"),
        admission=b.admission.model_dump(mode="json"),
        profile=item["profile"],
        owners=[
            o.model_dump(mode="json") for o in canonical_owners(b.hardware_spec, point.task_graph)
        ],
    )
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    job = MappedEngineJob.model_validate(raw)
    _, base = control("C02")
    result = deepcopy(base)
    for key in result["observations"]:
        if key != "format":
            result["observations"][key]["records"] = []
    result["per_op"] = []
    for i, name in enumerate(ORDER):
        piece = deepcopy(base)
        offset = SPANS[name][0]
        obs = piece["observations"]
        for table in (
            "activities",
            "clocks",
            "resource_intervals",
            "queue_membership",
            "events",
            "jobs",
        ):
            for row in obs[table]["records"]:
                if "job_id" in row:
                    row["job_id"] = name
                if "op_id" in row:
                    row["op_id"] = f"g{i}"
                if "activity_id" in row:
                    row["activity_id"] = name + ":" + row["activity_id"]
                if "item_id" in row:
                    row["item_id"] = name
                for key in ("ready_ps", "start_ps", "end_ps", "enter_ps", "leave_ps", "t_ps"):
                    if key in row:
                        row[key] += offset
                for key in (
                    "dispatch_ordinal",
                    "completion_ordinal",
                    "observation_ordinal",
                    "event_seq",
                ):
                    if key in row:
                        row[key] += i * 16
                for pred in row.get("predecessors", []):
                    pred["activity_id"] = name + ":" + pred["activity_id"]
            result["observations"][table]["records"] += obs[table]["records"]
        first = obs["activities"]["records"][0]
        first["ready_ps"] = READY[name]
        if i:
            prior = ORDER[i - 1] + ":compute_drain:service"
            first["predecessors"] = [dict(activity_id=prior, relation="resource")]
            if name != "d":
                first["predecessors"].append(dict(activity_id=prior, relation="dependency"))
        if name == "d":
            waiting = deepcopy(obs["queue_membership"]["records"][0])
            waiting["population"] = "waiting"
            result["observations"]["queue_membership"]["records"].append(waiting)
        obs["jobs"]["records"][0]["ready_ps"] = READY[name]
        per = deepcopy(base["per_op"][0])
        per["op_id"] = f"g{i}"
        result["per_op"].append(per)
    for field in ("counts", "ext_counts", "work_counts", "traffic_counts"):
        for key, value in result[field].items():
            if isinstance(value, (int, float)):
                result[field][key] = value * 5
    owners = {o.resource: o.owner_id for o in job.owners}
    for buf in job.mapped_point.task_graph.buffers:
        acc = buf.space == "accumulator"
        if acc:
            assert buf.producer_id is not None
            begin, end = (547000, 2188000) if buf.id == "bacc" else SPANS[buf.producer_id]
        else:
            begin, end = 0, None
        result["observations"]["allocations"]["records"].append(
            dict(
                buffer_id=buf.id,
                space=buf.space,
                owner_id=owners["matrix:0" if acc else "sram:0"],
                offset_bytes=buf.offset_bytes,
                size_bytes=buf.size_bytes,
                allocate_ps=begin,
                free_ps=end,
                initially_live=buf.initial_residency == "preloaded",
                last_consumer_ids=list(buf.final_consumer_ids),
            )
        )
    result.update(
        job_hash=job.job_hash,
        admission=raw["admission"],
        owners=raw["owners"],
        completed_jobs=list(ORDER),
    )
    result["busy_time_ps"] = [dict(owner_id=o.owner_id, busy_time_ps=0) for o in job.owners]
    result["simulator_metrics"].update(event_count=80, completed_job_count=5)
    for a in result["observations"]["activities"]["records"]:
        a["predecessors"].sort(key=lambda p: (p["activity_id"], p["relation"]))
    return job, synchronize(result)


def transient_attack(field: str, value: int | None) -> tuple[Any, Any]:
    job, result = transient_control()
    row = next(
        a for a in result["observations"]["allocations"]["records"] if a["buffer_id"] == "bacc"
    )
    row[field] = value
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    return job, result
