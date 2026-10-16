"""Read-only Linux cgroup-v2/affinity budget. Unknown limits stop, never mean unlimited."""

import math
import os
from fractions import Fraction
from pathlib import Path


def select_resources(
    affinity, quotas, memory_available, memory_limits, *, reserve, per_worker, tasks
):
    if not affinity or tasks <= 0 or reserve < 0 or per_worker <= 0:
        raise ValueError("nonempty affinity/tasks and positive memory policy required")
    cpus = min([Fraction(len(affinity))] + [Fraction(q, p) for q, p in quotas])
    if cpus < 1:
        raise ValueError("less than one effective CPU; return bounded resource decision")
    headroom = min([memory_available] + [max(0, limit - used) for limit, used in memory_limits])
    count = min(tasks, math.floor(cpus), (headroom - reserve) // per_worker)
    if count < 1:
        raise ValueError("insufficient measured memory headroom")
    return {
        "affinity": sorted(affinity),
        "effective_cpu_capacity": str(cpus),
        "cpu_quotas": quotas,
        "available_memory_bytes": memory_available,
        "cgroup_memory_limits": memory_limits,
        "memory_headroom_bytes": headroom,
        "parent_and_safety_reserve_bytes": reserve,
        "per_worker_budget_bytes": per_worker,
        "workers": count,
        "task_count": tasks,
    }


def discover(policy, tasks):
    # Cgroup namespace root is /sys/fs/cgroup in the accepted Docker runtime. Walk
    # every visible ancestor of the current unified group; do not silently use v1.
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    entries = [line[3:] for line in lines if line.startswith("0::")]
    if len(entries) != 1:
        raise ValueError("unified cgroup-v2 membership required")
    mount = Path("/sys/fs/cgroup")
    name = entries[0]
    if ".." in Path(name).parts:
        raise ValueError("cgroup namespace must expose current group without parent escape")
    current = mount / name.lstrip("/")
    if not (current / "cpu.max").is_file():
        raise ValueError("current cgroup limits unavailable")
    quotas, memory, observed = [], [], []
    while True:
        raw_cpu = (current / "cpu.max").read_text().strip()
        q, p = raw_cpu.split()
        if int(p) <= 0 or (q != "max" and int(q) <= 0):
            raise ValueError("invalid CPU quota")
        if q != "max":
            quotas.append((int(q), int(p)))
        raw_mem = (current / "memory.max").read_text().strip()
        used = int((current / "memory.current").read_text())
        if raw_mem != "max":
            memory.append((int(raw_mem), used))
        observed.append(
            {
                "path": str(current),
                "cpu.max": raw_cpu,
                "memory.max": raw_mem,
                "memory.current": used,
            }
        )
        if current == mount:
            break
        current = current.parent
    info = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    available = int(info["MemAvailable"].split()[0]) * 1024
    result = select_resources(
        os.sched_getaffinity(0),
        quotas,
        available,
        memory,
        reserve=policy["memory_reserve_bytes"],
        per_worker=policy["per_worker_memory_bytes"],
        tasks=tasks,
    )
    result["observed_cgroups"] = observed
    result["limitations"] = (
        "Visible cgroup ancestors and current MemAvailable; hidden ancestor "
        "limits/competing future allocations cannot be inferred. No resource "
        "settings changed; allocation failure or worker loss stops the run."
    )
    return result
