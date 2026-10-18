"""B independent mechanism arithmetic and literal opportunity/cause expectations.
Stdlib only. No validator, engine, or reviewer oracle imports. Synthetic private cases.
Usage: python -I literal.py RUNS OUTPUT
"""

import hashlib
import json
import sys
from fractions import Fraction as Q
from math import ceil
from pathlib import Path

runs, out = map(Path, sys.argv[1:])


def edge(t, hz, cycles=0):
    # ceil(k*period) >= t iff k*period > t-1 for integer t > 0.
    k = 0 if t == 0 else ((t - 1) * hz) // 10**12 + 1
    return ceil(Q((k + cycles) * 10**12, hz))


reports = []
for name in ("cc0-v3", "cc-v3", "sr-v3"):
    j = json.loads((runs / name / "job.json").read_text())
    r = json.loads((runs / name / "debug/result.json").read_text())["result"]
    obs = r["observations"]
    h = j["workload_closure"]["hardware_spec"]
    freq = j["freq_hz"]
    hw = h["memory"]["dram"]
    tim = hw["timing"]

    def val(x):
        return int(x["value"])

    latency = sum(val(tim[k]) for k in ("t_cl_cycles", "t_rcd_cycles", "t_rp_cycles"))
    service = Q(
        256 * 10**12 * val(hw["channels"]) * val(tim["t_refi_cycles"]),
        val(hw["bw_bytes_per_s"]) * (val(tim["t_refi_cycles"]) - val(tim["t_rfc_cycles"])),
    )
    assert service == Q(159744, 71)
    barrier = edge(0, freq["noc"], 32)
    assert barrier == 26667
    initial = 0 if name == "cc0-v3" else barrier
    tasks = {t["id"]: t for t in j["mapped_point"]["task_graph"]["jobs"] if t["kind"] == "dma"}
    # First read and write use separate channels. Reads after their releases use ch6 FIFO.
    first_read = "r01" if name == "sr-v3" else "r00"
    first_write = "r00" if name == "sr-v3" else "r01"
    stages = {}
    channels = {}
    ends = {}
    for tid in (first_write, first_read, "r02") + (() if name == "sr-v3" else ("r03",)):
        task = tasks[tid]
        f = task["fragments"][0]
        req = f["request_id"]
        reservation = initial if tid in (first_read, first_write) else ends[first_read]
        issue = edge(reservation, freq["core"])
        t = issue
        spans = {}
        if task["direction"] == "write":
            spans["write_port"] = (t, edge(t, freq["core"], 1))
            t = spans["write_port"][1]
        start = edge(t, freq["noc"])
        t = edge(start, freq["noc"], 4)
        spans["request_noc"] = (start, t)
        start = edge(t, freq["dram"])
        t = edge(start, freq["dram"], latency)
        spans["dram_latency"] = (start, t)
        # Preserve rational tail across back-to-back service on ch6, round only endpoints.
        start = max(Q(t), channels.get(f["channel_id"], Q(0)))
        tail = start + service
        channels[f["channel_id"]] = tail
        spans["channel_service"] = (ceil(start), ceil(tail))
        t = ceil(tail)
        start = edge(t, freq["noc"])
        t = edge(start, freq["noc"], 4)
        spans["response_noc"] = (start, t)
        start = edge(t, freq["core"])
        if task["direction"] == "write":
            spans["ack"] = (start, start)
            t = start
        else:
            # The later reads' port windows are naturally disjoint (120000/121000 etc).
            t = edge(start, freq["core"], 1)
            spans["read_port"] = (start, t)
        ends[tid] = t
        actual = {
            a["subphase"]: (a["start_ps"], a["end_ps"])
            for a in obs["activities"]["records"]
            if a["request_id"] == req and a["kind"] == "service" and a["subphase"] != "dma_issue"
        }
        assert actual == spans, (name, tid, actual, spans)
        stages[tid] = {"reservation": reservation, "issue": issue, "phases": spans, "complete": t}
    assert ends[first_read] == ends[first_write] == (60000 if initial == 0 else 86000)
    T = ends[first_read]
    # Event inventory independently counts two endpoints per explicit phase/alignment.
    # Phase0 drains read terminal 50 and write alignment terminal51 before opportunity52.
    # Write ACK is an inline service: endpoints54/55 in cc, 52/53 in sr (no free engine0).
    wanted = [(0, 0, []), (2, 0, []), (6, 26667, [first_write + ".00", first_read + ".00"])]
    wanted[2] = (6, 26667, sorted(wanted[2][2]))
    if initial == 0:
        wanted = [(0, 0, ["r00.00", "r01.00"]), (2, 0, []), (32, 26667, [])]
    wanted += (
        [(52, T, []), (54, T, ["r02.00"]), (76, ends["r02"], [])]
        if name == "sr-v3"
        else [
            (52, T, ["r02.00"]),
            (56, T, ["r03.00"]),
            (94, ends["r02"], []),
            (98, ends["r03"], []),
        ]
    )
    actual = [
        (o["event_cursor"], o["t_ps"], o["granted_request_ids"])
        for o in obs["reservation_opportunities"]["records"]
    ]
    assert actual == wanted, (name, actual, wanted)
    acts = {a["activity_id"]: a for a in obs["activities"]["records"]}
    causes = {}
    for tid in tasks:
        a = next(
            a
            for a in acts.values()
            if a["job_id"] == tid and a["subphase"] == "dma_issue" and a["kind"] == "alignment"
        )
        got = sorted(
            (acts[p["activity_id"]]["job_id"], acts[p["activity_id"]]["subphase"])
            for p in a["predecessors"]
            if p["relation"] == "credit"
        )
        wanted_causes = []
        if tid == "r02":
            wanted_causes = (
                [(first_write, "ack")] if name == "sr-v3" else [(first_read, "read_port")]
            )
        if tid == "r03":
            wanted_causes = [(first_read, "read_port"), (first_write, "ack")]
        assert got == sorted(wanted_causes), (name, tid, got, wanted_causes)
        causes[tid] = got
    reports.append(
        dict(
            case=name,
            job_sha256=hashlib.sha256((runs / name / "job.json").read_bytes()).hexdigest(),
            channel_step_ps=str(service),
            stages=stages,
            opportunities=actual,
            causes=causes,
        )
    )
out.write_text(json.dumps(reports, indent=2) + "\n")
print("Three independently derived timelines, opportunity inventories and a1 cause sets agree")
