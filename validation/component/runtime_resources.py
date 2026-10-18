"""Read visible unified-cgroup limits without assuming root has non-root controls.

Component-private orchestration only. The historical K2 helper stays byte-exact.
Its budget arithmetic is supplied by the caller after checking its frozen hash.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _path(raw: str) -> Path:
    decoded = re.sub(r"\\(040|011|012|134)", lambda m: chr(int(m[1], 8)), raw)
    value = Path(decoded)
    require(
        value.is_absolute() and ".." not in value.parts, "absolute unescaped cgroup path required"
    )
    return value


def inspect_cgroups(membership: str, mountinfo: str) -> dict[str, Any]:
    entries = [line[3:] for line in membership.splitlines() if line.startswith("0::")]
    require(len(entries) == 1, "one unified cgroup-v2 membership required")
    name = Path(entries[0])
    require(name.is_absolute() and ".." not in name.parts, "absolute cgroup membership required")
    mounts = []
    for line in mountinfo.splitlines():
        before, separator, after = line.partition(" - ")
        if separator and after.split()[0] == "cgroup2":
            fields = before.split()
            require(len(fields) >= 6, "complete cgroup mountinfo required")
            mounts.append((_path(fields[3]), _path(fields[4])))
    require(len(mounts) == 1, "one unambiguous cgroup-v2 mount required")
    mounted_root, mount = mounts[0]
    require(mounted_root == Path("/"), "hidden mount ancestors require a reviewed environment")
    require(
        {"cpu", "memory"} <= set((mount / "cgroup.controllers").read_text().split()),
        "CPU and memory controllers must be exposed",
    )
    current = mount / name.relative_to("/")
    require(current.resolve().is_relative_to(mount.resolve()), "cgroup path must stay inside mount")
    quotas: list[tuple[int, int]] = []
    memory: list[tuple[int, int]] = []
    observed: list[dict[str, Any]] = []
    while True:
        values: dict[str, str | None] = {}
        for field in ("cpu.max", "memory.max", "memory.current"):
            try:
                values[field] = (current / field).read_text().strip()
            except FileNotFoundError:
                values[field] = None
        # Linux's actual hierarchy root has no non-root interface, including cgroup.type.
        # A namespace/mount root WITH controls must still contribute all its limits.
        if all(v is None for v in values.values()) and current == mount:
            try:
                (current / "cgroup.type").read_text()
            except FileNotFoundError:
                observed.append(
                    {
                        "path": str(current),
                        "interface": "hierarchy-root-no-bandwidth-or-memory-interface",
                    }
                )
                break
            raise ValueError("missing controls at namespace root")
        require(
            all(v is not None for v in values.values()),
            "incomplete non-root or partial-root limits",
        )
        raw_cpu, raw_mem, raw_used = (
            values["cpu.max"],
            values["memory.max"],
            values["memory.current"],
        )
        assert raw_cpu is not None and raw_mem is not None and raw_used is not None
        q, p = raw_cpu.split()
        require(int(p) > 0 and (q == "max" or int(q) > 0), "invalid CPU quota")
        used = int(raw_used)
        require(
            used >= 0 and (raw_mem == "max" or int(raw_mem) >= 0), "invalid memory limit/current"
        )
        if q != "max":
            quotas.append((int(q), int(p)))
        if raw_mem != "max":
            memory.append((int(raw_mem), used))
        observed.append({"path": str(current), **values, "memory.current": used})
        if current == mount:
            break
        current = current.parent
    return dict(
        membership=str(name),
        mount=str(mount),
        mounted_root=str(mounted_root),
        quotas=quotas,
        memory=memory,
        observed_cgroups=observed,
    )


def discover(
    policy: dict[str, Any], tasks: int, *, select_resources: Callable[..., dict[str, Any]]
) -> dict[str, Any]:
    membership = Path("/proc/self/cgroup").read_text()
    mountinfo = Path("/proc/self/mountinfo").read_text()
    limits = inspect_cgroups(membership, mountinfo)
    info = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    amount, unit = info["MemAvailable"].split()
    require(unit == "kB" and int(amount) >= 0, "measured MemAvailable in kB required")
    affinity = os.sched_getaffinity(0)
    result = select_resources(
        affinity,
        limits["quotas"],
        int(amount) * 1024,
        limits["memory"],
        reserve=policy["memory_reserve_bytes"],
        per_worker=policy["per_worker_memory_bytes"],
        tasks=tasks,
    )
    require(
        Path("/proc/self/cgroup").read_text() == membership
        and Path("/proc/self/mountinfo").read_text() == mountinfo
        and os.sched_getaffinity(0) == affinity,
        "resource membership changed during discovery",
    )
    result.update({k: v for k, v in limits.items() if k not in ("quotas", "memory")})
    result["limitations"] = (
        "Visible cgroup limits, affinity and current MemAvailable only; "
        "namespace-hidden ancestors and competing future allocations are not inferred. "
        "No resource setting changed. Worker/container loss still stops the run. "
        "Docker per-call limits remain separately enforced; this is no host reservation."
    )
    return result
