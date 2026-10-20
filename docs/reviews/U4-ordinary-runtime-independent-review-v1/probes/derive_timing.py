"""Hand derivation of the reviewer production job; imports nothing from rkuarch/uarch_contract.

Usage: python3 -I derive_timing.py JOB.json RESULT.json [RESULT2.json ...]
Laws (U0011 E3/E4, stated in the ADR, re-derived here from hardware values in the job):
  * clocked phases align to next_edge of the receiving domain (1 GHz -> 1000 ps grid);
  * DRAM latency = t_cl + t_rcd + t_rp dram cycles, no edge alignment of channel service;
  * channel service = transaction_bytes / (bw/channels * (1 - t_rfc/t_refi)), ceil to ps;
  * zero-hop NoC = zero duration, no alignment; hop delay = hops * router_latency_cycles;
  * ports: ceil(payload / dma bytes_per_cycle) cycles, FIFO by (ready, engine, request id);
  * compute: 32-cycle job overhead, WS staging ceil(K*N*2/operand_bytes_per_cycle),
    fill/steady/drain M + K_phys + N_phys - 2, output ceil(M*N*2/operand_bytes_per_cycle).
"""

import json
import sys
from fractions import Fraction
from math import ceil


def v(node):
    return Fraction(str(node["value"]))


job = json.load(open(sys.argv[1]))
hw = job["workload_closure"]["hardware_spec"]
g = job["mapped_point"]["task_graph"]
jobs = {x["id"]: x for x in g["jobs"]}
routes = {r["id"]: r for r in g["routes"]}
core = hw["cores"]["core_type"]
dram = hw["memory"]["dram"]
t = dram["timing"]
period = {d: int(Fraction(10**12) / v(hw["clock_domains"][d]["freq_hz"])) for d in ("core", "noc", "dram")}


def edge(ps, domain):
    p = period[domain]
    return -(-ps // p) * p


latency = int((v(t["t_cl_cycles"]) + v(t["t_rcd_cycles"]) + v(t["t_rp_cycles"])) * period["dram"])
derate = (v(t["t_refi_cycles"]) - v(t["t_rfc_cycles"])) / v(t["t_refi_cycles"])
channel_bw = v(dram["bw_bytes_per_s"]) / v(dram["channels"]) * derate  # bytes/s
hop = int(v(hw["nocs"][0]["router_latency_cycles"]) * period["noc"])
cols = int(v(hw["cores"]["grid"]["cols"]))


def hops(route):
    a, z = route["source_core_id"], route["destination_core_id"]
    return abs(a // cols - z // cols) + abs(a % cols - z % cols)


def service_ps(transaction):
    return Fraction(transaction) / channel_bw * 10**12


def port_ps(payload):
    return ceil(Fraction(payload) / v(core["dma"]["bytes_per_cycle"])) * period["core"]


def noc(arrive, route):
    n = hops(route)
    if n == 0:
        return arrive, arrive, 0, 0  # end, start, alignment, service
    start = edge(arrive, "noc")
    return start + n * hop, start, start - arrive, n * hop


attr = {"compute": 0, "memory": 0, "noc": 0, "overhead": 0, "sync": 0}
# Reads a, b issue at 0 (no predecessors), concurrent on distinct channels.
reads = {}
for jid in ("a", "b"):
    f = jobs[jid]["fragments"][0]
    req_end, _, _, _ = noc(0, routes[f["route_id"]])
    dram_end = req_end + latency
    chan_end = ceil(dram_end + service_ps(f["transaction_bytes"]))
    resp_end, _, resp_align, resp_service = noc(chan_end, routes[f["route_id"]])
    reads[jid] = dict(ready_port=resp_end, payload=f["payload_bytes"], chan_end=chan_end,
                      dram_end=dram_end)
# Port FIFO: order by (ready, engine, request id).
port_free = 0
order = sorted(reads, key=lambda j: (reads[j]["ready_port"], jobs[j]["dma_engine_id"], j))
for jid in order:
    r = reads[jid]
    r["port_start"] = max(edge(r["ready_port"], "core"), port_free)
    r["port_end"] = r["port_start"] + port_ps(r["payload"])
    port_free = r["port_end"]
c = jobs["c"]
ready_c = max(reads[j]["port_end"] for j in ("a", "b"))
M, K, N = (c["tile_extents"][x] for x in ("M", "K", "N"))
Kp, Np = c["physical_extents"]["K"], c["physical_extents"]["N"]
obpc = v(core["matrix_engine"]["operand_bytes_per_cycle"])
overhead = int(v(core["job_overhead_cycles"])) * period["core"]
stage = ceil(Fraction(K * N * 2) / obpc) * period["core"]
wave = (M + Kp + Np - 2) * period["core"]
drain = ceil(Fraction(M * N * 2) / obpc) * period["core"]
c_start = edge(ready_c, "core")
c_end = c_start + overhead + stage + wave + drain
d = jobs["d"]
f = d["fragments"][0]
wp_start = edge(c_end, "core")
wp_end = wp_start + port_ps(f["payload_bytes"])
req_end, req_start, req_align, req_service = noc(wp_end, routes[f["route_id"]])
dram_start = edge(req_end, "dram")
dram_end = dram_start + latency
chan_end = ceil(dram_end + service_ps(f["transaction_bytes"]))
resp_end, resp_start, resp_align, resp_service = noc(chan_end, routes[f["route_id"]])
ack = edge(resp_end, "core")
duration = ack
# Critical path: d chain <- c <- b port (resource wait on a's port) <- a port/align <- a read.
first = order[0]
a_align = reads[first]["port_start"] - reads[first]["ready_port"]
attr["memory"] = (reads[first]["dram_end"] - 0) + (reads[first]["chan_end"] - reads[first]["dram_end"]) \
    + a_align + port_ps(reads[first]["payload"]) + port_ps(reads[order[1]]["payload"]) \
    + (wp_end - wp_start) + latency + (chan_end - dram_end)
attr["noc"] = req_align + req_service + resp_align + resp_service
attr["overhead"] = overhead
attr["compute"] = stage + wave + drain
derived = {
    "duration_ps": duration,
    "attribution_ps": attr,
    "milestones": {"a.port_end": reads["a"]["port_end"], "b.port_end": reads["b"]["port_end"],
                   "c.start": c_start, "c.end": c_end, "d.write_port_end": wp_end,
                   "d.dram_latency_end": dram_end, "d.channel_end": chan_end,
                   "d.response_end": resp_end},
    "exact_channel_service_ps": str(service_ps(f["transaction_bytes"])),
}
print(json.dumps(derived, indent=1, sort_keys=True))
assert sum(attr.values()) == duration, (attr, duration)

ok = True
for path in sys.argv[2:]:
    r = json.load(open(path))
    recs = r["observations"]["activities"]["records"]

    def end(job_id, subphase):
        return max(x["end_ps"] for x in recs if x["job_id"] == job_id and x["subphase"] == subphase
                   and x["kind"] == "service")

    observed = {"a.port_end": end("a", "read_port"), "b.port_end": end("b", "read_port"),
                "c.start": min(x["start_ps"] for x in recs if x["job_id"] == "c"),
                "c.end": end("c", "compute_drain"), "d.write_port_end": end("d", "write_port"),
                "d.dram_latency_end": end("d", "dram_latency"),
                "d.channel_end": end("d", "channel_service"), "d.response_end": end("d", "response_noc")}
    match = (r["duration_ps"] == duration and r["attribution_ps"] == attr
             and observed == derived["milestones"])
    ok &= match
    print(path.rsplit("/", 1)[-1], "duration", r["duration_ps"], "attribution", r["attribution_ps"],
          "MATCH" if match else f"MISMATCH observed={observed}")
sys.exit(0 if ok else 1)
