"""F1 probe: explicit --test-only jobs on single-parameter hardware variants.

Usage: RUNTIME_PYTHON -I hw_sweep.py PRODUCTION_JOB TRANSPORT_FIXTURE_JOB RELEASE_BINARY
For each variant: does the shipping binary admit and run it (and did the parameter change the
native timing)? Does the installed ordinary consumer (validate_result + packaged check_v3) accept
the binary's own output? Rehashing mirrors make_mutants.py; nothing here is a launch policy.
"""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, spec_hash
from uarch_contract.mapped import TaskGraph, canonical_owners, hardware_projection, resolve_frequencies
from uarch_contract.ordinary import OrdinaryJob

from rkuarch.engines.native.ordinary import consume

prod = json.loads(Path(sys.argv[1]).read_text())
fixture = json.loads(Path(sys.argv[2]).read_text())
binary = sys.argv[3]
TEST = {"checkpoint": "B", "invocation": "test", "eligibility": "verification_only"}


def variant(base, path, value):
    raw = deepcopy(base)
    raw["admission"] = dict(TEST)
    b = raw["workload_closure"]
    b["admission"] = dict(TEST)
    node = b["hardware_spec"]
    for key in path[:-1]:
        node = node[key]
    if path[-1] is not None:
        node[path[-1]]["value"] = value
    spec = HardwareSpec.model_validate(b["hardware_spec"])
    b["hardware_spec_hash"] = raw["hardware_spec_hash"] = spec_hash(spec)
    raw["hardware"] = hardware_projection(spec).model_dump(mode="json")
    raw["owners"] = [o.model_dump(mode="json") for o in canonical_owners(
        spec, TaskGraph.model_validate(raw["mapped_point"]["task_graph"]))]
    raw["freq_hz"] = resolve_frequencies(spec, raw["frequency_ratio"]).model_dump(mode="json")
    b["bundle_hash"] = raw["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    return raw


CT = ["cores", "core_type"]
cases = [
    ("baseline (production hw, test invocation)", prod, [None], None),
    ("job_overhead_cycles 32->16", prod, CT + ["job_overhead_cycles"], 16.0),
    ("matrix array rows/cols 256->128", prod, CT + ["matrix_engine", "array", "rows"], 128.0),
    ("operand_bytes_per_cycle 1024->32", prod, CT + ["matrix_engine", "operand_bytes_per_cycle"], 32.0),
    ("dma bytes_per_cycle 256->16", prod, CT + ["dma", "bytes_per_cycle"], 16.0),
    ("noc router_latency_cycles 2->3", prod, ["nocs", 0, "router_latency_cycles"], 3.0),
    ("dram t_cl_cycles 16->20", prod, ["memory", "dram", "timing", "t_cl_cycles"], 20.0),
    ("dram bw 1e12->5e11", prod, ["memory", "dram", "bw_bytes_per_s"], 5e11),
    ("fixture baseline (barrier present)", fixture, [None], None),
    ("fixture sync barrier_latency_cycles 32->16", fixture, ["sync", "barrier_latency_cycles"], 16.0),
]
baseline = {}
rows = []
for label, base, path, value in cases:
    if label.startswith("matrix array"):
        raw = variant(base, CT + ["matrix_engine", "array", "cols"], 128.0)
        raw = variant(raw, path, value)
    else:
        raw = variant(base, path, value)
    payload = canonical_json(raw).encode()
    p = subprocess.run([binary, "--protocol", "uarch-engine/4", "--test-only"], input=payload,
                       capture_output=True, timeout=60)
    row = {"variant": label, "native_status": p.returncode}
    if p.returncode == 2:
        row["native_code"] = json.loads(p.stderr)["code"]
    elif p.returncode == 0:
        out = json.loads(p.stdout)
        row["native_duration_ps"] = out["duration_ps"]
        key = "fixture" if base is fixture else "prod"
        baseline.setdefault(key, out["duration_ps"])
        row["native_timing_changed"] = out["duration_ps"] != baseline[key]
        try:
            consume(p.stdout, b"", 0, job=OrdinaryJob.model_validate(raw))
            row["ordinary_consumer"] = "accepted"
        except Exception as e:  # noqa: BLE001
            row["ordinary_consumer"] = f"{type(e).__name__}: {str(e)[:80]}"
    rows.append(row)
    print(json.dumps(row))
