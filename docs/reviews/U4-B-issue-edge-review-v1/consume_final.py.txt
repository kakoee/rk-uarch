"""B literal comparisons and synthetic output attacks; no producer imports."""

import argparse
import copy
import hashlib
import importlib
import json
from fractions import Fraction
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, validate_result
from validation.component.observations_v3 import check_v3

from validation.component.consistent_carriers import synchronize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sync_v3(r):
    """Repair joins to supplied forged times, never derive timing laws."""
    queues = r["observations"]["queue_membership"]["records"]
    ledgers = [q for q in queues if q["queue_id"].startswith(("dma_waiting:", "dma_pending:"))]
    r["observations"]["queue_membership"]["records"] = [q for q in queues if q not in ledgers]
    r = synchronize(r)
    r["observations"]["queue_membership"]["records"].extend(ledgers)
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


def attack(r, name):
    r = copy.deepcopy(r)
    o = r["observations"]
    acts = o["activities"]["records"]
    dma = next(x for x in o["dma"]["records"] if x["direction"] != "unicast")
    alignment = next(a for a in acts if a["subphase"] == "dma_issue" and a["kind"] == "alignment")
    service = next(a for a in acts if a["subphase"] == "dma_issue" and a["kind"] == "service")
    pending = next(
        q for q in o["queue_membership"]["records"] if q["queue_id"].startswith("dma_pending:")
    )
    if name == "pending-overbook-only":
        # Reserve the second slot early but retain its later acquired interval.
        # Acquired-only capacity remains legal; only pending+acquired is overbooked.
        dma = [x for x in o["dma"]["records"] if x["direction"] != "unicast"][1]
        req = dma["request_id"]
        a = next(
            x
            for x in acts
            if x["request_id"] == req and x["subphase"] == "dma_issue" and x["kind"] == "alignment"
        )
        barrier = next(x for x in acts if x["subphase"] == "barrier" and x["kind"] == "service")
        assert dma["reservation_ps"] == 86000 and barrier["end_ps"] == 26667
        dma["reservation_ps"] = a["start_ps"] = 26667
        next(
            e for e in o["events"]["records"] if e["observation_ordinal"] == a["completion_ordinal"]
        )["phase"] = 0
        a["predecessors"] = [dict(activity_id=barrier["activity_id"], relation="dependency")]
        next(x for x in o["jobs"]["records"] if x["job_id"] == dma["job_id"])["start_ps"] = 26667
        next(
            x for x in o["allocations"]["records"] if x["buffer_id"] == dma["destination_buffer_id"]
        )["allocate_ps"] = 26667
        for q in o["queue_membership"]["records"]:
            if q["item_id"] == req and q["queue_id"].startswith("dma_waiting:"):
                q["leave_ps"] = 26667
            if q["item_id"] == req and q["queue_id"].startswith("dma_pending:"):
                q["enter_ps"] = 26667
        return sync_v3(r)
    elif name in ("missing-alignment", "missing-zero-alignment"):
        acts.remove(alignment)
    elif name == "early-acquisition":
        dma["credit_acquire_ps"] = dma["reservation_ps"]
    elif name == "missing-pending":
        o["queue_membership"]["records"].remove(pending)
    elif name == "pending-as-inflight":
        pending["population"] = "inflight"
    elif name == "pending-clock":
        pending["clock_domain"] = "core"
    elif name == "pending-wrong-engine":
        pending["queue_id"] = "dma_pending:1"
    elif name == "issue-busy":
        alignment["occupies_resource"] = True
    elif name == "job-start-at-issue":
        next(j for j in o["jobs"]["records"] if j["job_id"] == dma["job_id"])["start_ps"] = dma[
            "issue_ps"
        ]
    elif name == "allocation-at-issue":
        next(
            a for a in o["allocations"]["records"] if a["buffer_id"] == dma["destination_buffer_id"]
        )["allocate_ps"] = dma["issue_ps"]
    elif name == "issue-conversion-nonzero":
        service["end_ps"] += 1000
    elif name == "positive-completion-phase2":
        next(
            e
            for e in o["events"]["records"]
            if e["observation_ordinal"] == alignment["completion_ordinal"]
        )["phase"] = 2
    elif name == "duration-law":
        response = next(
            a for a in acts if a["subphase"] == "response_noc" and a["kind"] == "service"
        )
        port = next(a for a in acts if a["subphase"] == "read_port" and a["kind"] == "alignment")
        assert response["end_ps"] == 59000
        response["end_ps"] = 58500
        port.update(ready_ps=58500, start_ps=58500)
        return sync_v3(r)
    elif name == "late-issue-edge":
        # Delay the issue and entire DMA tail by 10,000 ps (integer cycles in all
        # three domains), retaining reservation, dependency, allocation and traffic.
        # The ONLY intended law violation is the earliest receiving core edge.
        delta = 10000
        for a in acts:
            if a["job_id"] != dma["job_id"]:
                continue
            if a is alignment:
                a["end_ps"] += delta
            else:
                for field in ("ready_ps", "start_ps", "end_ps"):
                    a[field] += delta
        dma["issue_ps"] += delta
        dma["credit_acquire_ps"] += delta
        pending["leave_ps"] += delta
        for resource in o["resource_intervals"]["records"]:
            if (
                resource["job_id"] == dma["job_id"]
                and resource["service_start_ps_ratio"] is not None
            ):
                for field in ("service_start_ps_ratio", "service_end_ps_ratio"):
                    resource[field]["numerator"] += delta * resource[field]["denominator"]
        return sync_v3(r)
    else:
        raise ValueError(name)
    r["result_hash"] = content_hash(r, exclude=("result_hash",))
    return r


def outcome(fn):
    try:
        fn()
        return {"outcome": "pass"}
    except Exception as e:
        return {"outcome": "refusal", "type": type(e).__name__, "detail": str(e)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("runs", type=Path)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    expected = json.loads(
        (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
    )["observation_contract"]
    report = dict(
        recipe_sha256=sha(Path(__file__)),
        synthetic_output_attacks=True,
        baselines=[],
        attacks=[],
        source_origins={},
    )
    for mod in [
        "uarch_contract.mapped",
        "uarch_contract.mapped_issue",
        "validation.component.observations_v3",
        "validation.component.issue_checks",
        "validation.component.transition_checks_v3",
    ]:
        file = Path(importlib.import_module(mod).__file__).resolve()
        assert file.is_relative_to(a.source.resolve()), file
        report["source_origins"][mod] = {"path": str(file), "sha256": sha(file)}
    cases = {}
    for path in sorted((a.runs / "jobs").glob("*.json")):
        name = path.stem
        job = json.loads(path.read_text())
        result = json.loads((a.runs / (name + "-debug") / "result.json").read_text())["result"]
        validate_result(result, MappedEngineJob.model_validate(job))
        check_v3(job, result, expected)
        published = json.loads(
            (
                ROOT
                / "docs/reviews/U4-A-issue-edge-amendment-v1/private-probes"
                / name
                / "result.json"
            ).read_text()
        )
        assert result == published, name
        cases[name] = (job, result)
        report["baselines"].append(
            dict(
                case=name,
                validator="pass",
                independent_checker="pass",
                matches_intermediate_full_result=True,
                result_hash=result["result_hash"],
            )
        )
    literals = json.loads(
        (ROOT / "docs/reviews/U4-B-component-native-audit-v1/issue-gap-literals.json").read_text()
    )["rows"]
    for name, literal in zip(("issue-gap", "gap-write"), literals, strict=True):
        j, r = cases[name]
        dma = next(x for x in r["observations"]["dma"]["records"] if x["direction"] != "unicast")
        for field in ("issue_ps", "complete_ps", "payload_bytes", "transaction_bytes"):
            assert dma[field] == literal[field]
        assert dma["reservation_ps"] == literal["dependency_ready_ps"]
        for category, value in literal["proposed_causal_partition_ps"].items():
            assert r["attribution_ps"][category] == value
        for phase, field in [
            ("request_noc", "request_arrival_ps"),
            ("dram_latency", "latency_end_ps"),
            ("channel_service", "channel_end_ps"),
            ("response_noc", "response_end_ps"),
        ]:
            activity = next(
                x
                for x in r["observations"]["activities"]["records"]
                if x["subphase"] == phase and x["kind"] == "service"
            )
            assert activity["end_ps"] == literal[field], (name, phase)
        # Independent declared refresh factor: (3900-350)/3900 = 71/78.
        # 256 bytes at (10^12/8)*(71/78) bytes/s = 159744/71 ps.
        channel = next(
            x
            for x in r["observations"]["resource_intervals"]["records"]
            if x["activity"] == "channel_service"
        )

        def q(key, channel=channel):
            return Fraction(channel[key]["numerator"], channel[key]["denominator"])

        assert q("service_end_ps_ratio") - q("service_start_ps_ratio") == Fraction(256 * 8 * 78, 71)
    for name, wanted in {
        "gap-cap1": ([26667, 86000], [27000, 86000], [86000, 146000]),
        "gap-cap2": ([26667, 26667, 86000], [27000, 27000, 86000], [86000, 89000, 146000]),
        "gap-cap2-pair": ([26667, 26667], [27000, 27000], [86000, 89000]),
        "gap-independent": ([26667, 26667], [27000, 27000], [86000, 89000]),
    }.items():
        rows = [
            x
            for x in cases[name][1]["observations"]["dma"]["records"]
            if x["direction"] != "unicast"
        ]
        assert (
            tuple([x[k] for x in rows] for k in ("reservation_ps", "issue_ps", "complete_ps"))
            == wanted
        )
    o2 = cases["O2"][1]
    assert o2["duration_ps"] == 2735000
    allocation = next(
        x for x in o2["observations"]["allocations"]["records"] if x["buffer_id"] == "bacc"
    )
    assert (allocation["allocate_ps"], allocation["free_ps"]) == (547000, 2188000)
    report["independent_prior_literals"] = (
        "read/write exact phases, rational channel, attribution; cap1/cap2/pair/independent; "
        "O2 exact producer/final-consumer endpoints: pass"
    )
    names = [
        "pending-overbook-only",
        "missing-alignment",
        "missing-zero-alignment",
        "early-acquisition",
        "missing-pending",
        "pending-as-inflight",
        "pending-clock",
        "pending-wrong-engine",
        "issue-busy",
        "job-start-at-issue",
        "allocation-at-issue",
        "issue-conversion-nonzero",
        "positive-completion-phase2",
        "duration-law",
        "late-issue-edge",
    ]
    for name in names:
        case = (
            "gap-cap1"
            if name == "pending-overbook-only"
            else "D01"
            if name in ("missing-zero-alignment", "duration-law")
            else "issue-gap"
        )
        j, r = cases[case]
        forged = attack(r, name)
        (a.output / (name + ".json")).write_text(json.dumps(forged, sort_keys=True) + "\n")
        row = dict(
            name=name,
            case=case,
            forgery_sha256=sha(a.output / (name + ".json")),
            structural=outcome(
                lambda forged=forged, j=j: validate_result(
                    forged, MappedEngineJob.model_validate(j)
                )
            ),
            independent=outcome(lambda j=j, forged=forged: check_v3(j, forged, expected)),
        )
        report["attacks"].append(row)
    (a.output / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    assert all(x["independent"]["outcome"] == "refusal" for x in report["attacks"])
    for x in report["attacks"]:
        if x["name"] in ("duration-law", "late-issue-edge"):
            assert x["structural"]["outcome"] == "pass", x


if __name__ == "__main__":
    main()
