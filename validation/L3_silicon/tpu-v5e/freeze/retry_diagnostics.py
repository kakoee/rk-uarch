"""One bounded B32 retry with external Linux sampling; no simulator changes.

Launch the existing recovery CLI unchanged. Observable native process RSS/HWM do
not distinguish parsing/admission, simulation or output construction internally.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import recovery


def limits():
    groups = []
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            directory = Path("/sys/fs/cgroup") / line[3:].lstrip("/")
            while True:
                values = {}
                for name in (
                    "memory.max",
                    "memory.high",
                    "memory.current",
                    "memory.swap.max",
                    "memory.swap.current",
                    "memory.events",
                ):
                    try:
                        values[name] = (directory / name).read_text().strip()
                    except OSError:
                        values[name] = None
                groups.append(dict(path=str(directory), **values))
                if directory == Path("/sys/fs/cgroup"):
                    break
                directory = directory.parent
    return dict(
        cgroups=groups,
        rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),
        rlimit_data=list(resource.getrlimit(resource.RLIMIT_DATA)),
        unavailable="null means unavailable; max or RLIM_INFINITY(-1) means unlimited",
    )


def sample(root_pid, executable):
    _, pids = recovery.tree_rss(root_pid)
    processes = []
    for pid in pids:
        try:
            fields = dict(
                line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines()
            )

            def metric(key, values=fields):
                return int(values[key].split()[0]) * 1024 if key in values else None

            try:
                native = os.path.samefile(f"/proc/{pid}/exe", executable)
            except OSError:
                native = None
            processes.append(
                dict(
                    pid=pid,
                    native=native,
                    rss_bytes=metric("VmRSS"),
                    high_water_mark_bytes=metric("VmHWM"),
                    state=fields["State"].strip(),
                )
            )
        except (OSError, KeyError):
            pass
    return dict(
        processes=processes,
        native_processes=[p for p in processes if p["native"]],
        combined_rss_bytes_approx=sum(p["rss_bytes"] or 0 for p in processes),
        caveat="sampled process-tree sum; shared pages may count twice and peaks may be missed",
        memory=recovery.memory(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    for name in ("native_executable", "saved_input", "generator"):
        item = receipt[name]
        if recovery.file_hash(Path(item["path"])) != item["sha256"]:
            raise ValueError(f"{name} identity changed; no retry")
    if args.diagnostics.exists() or (args.work / "layer-b32-s1").exists():
        raise FileExistsError("one attempt only; diagnostic file/attempt directory already exists")
    mem, effective = recovery.memory(), limits()
    if mem["MemAvailable"] < 13.5 * recovery.GIB or mem["swap_used_bytes"] > recovery.GIB:
        raise RuntimeError("additional RAM headroom absent; no retry")
    for group in effective["cgroups"]:
        cap, used = group["memory.max"], group["memory.current"]
        if cap is not None and cap != "max" and used is not None:
            if int(cap) - int(used) < 13.5 * recovery.GIB:
                raise RuntimeError("effective cgroup headroom insufficient; no retry")
    log_args = SimpleNamespace(id="layer-b32-s1", journal=args.diagnostics)
    command = [
        sys.executable,
        receipt["generator"]["path"],
        "run",
        "--id",
        "layer-b32-s1",
        "--source",
        receipt["source_path"],
        "--work",
        str(args.work),
        "--out",
        str(args.out),
        "--environment",
        str(args.environment),
        "--executable",
        receipt["native_executable"]["path"],
        "--journal",
        str(args.journal),
        "--min-available-gib",
        "13.5",
        "--prepared-job",
        receipt["saved_input"]["path"],
        "--prepared-job-sha256",
        receipt["saved_input"]["sha256"],
        "--preparation-generator-sha256",
        receipt["preparation_generator_sha256"],
    ]
    before_lines = len(args.journal.read_text().splitlines()) if args.journal.exists() else 0
    recovery.record(
        log_args,
        "retry_start",
        command=command,
        identities=receipt,
        effective_limits=effective,
        memory=mem,
        boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        internal_native_phases="unmeasured; external sampling cannot distinguish them",
    )
    start = time.monotonic()
    last = None
    interrupted = None
    with args.diagnostics.with_suffix(".log").open("x") as output:
        child = subprocess.Popen(
            command, stdout=output, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            while True:
                last = sample(child.pid, receipt["native_executable"]["path"])
                sizes = {}
                for name in ("job.json", "native.json", "native.stderr"):
                    path = args.work / "layer-b32-s1" / name
                    sizes[name] = path.stat().st_size if path.exists() else None
                recovery.record(
                    log_args,
                    "external_sample",
                    elapsed_s=time.monotonic() - start,
                    file_sizes_bytes=sizes,
                    **last,
                )
                if child.poll() is not None:
                    break
                time.sleep(1)
        except BaseException as error:
            interrupted = repr(error)
            recovery.stop_tree(child.pid)
            child.wait()
        finally:
            stages = [
                json.loads(line) for line in args.journal.read_text().splitlines()[before_lines:]
            ]
            guard = [
                r
                for r in stages
                if r.get("status") == "interrupted" and "resource guard" in r.get("reason", "")
            ]
            status_path = args.work / "layer-b32-s1/native-status.json"
            native_status = (
                json.loads(status_path.read_text())["status"] if status_path.exists() else None
            )
            recovery.record(
                log_args,
                "retry_end",
                elapsed_s=time.monotonic() - start,
                status="complete" if child.returncode == 0 else "failure",
                cli_exit_status=child.returncode,
                native_exit_status=native_status,
                supervisor_stop=bool(guard) or interrupted is not None,
                requested_stop_signal=signal.SIGKILL.value if guard or interrupted else None,
                guard_records=guard,
                interruption=interrupted,
                last_sample=last,
                memory=recovery.memory(),
                effective_limits=limits(),
                confirmed_os_oom_kill=None,
                oom_evidence="not established; a signal alone does not establish an OS OOM kill",
                wall_scope="inclusive launcher time; do not add nested worker/stage timings",
            )
    raise SystemExit(child.returncode if child.returncode else (1 if interrupted else 0))


if __name__ == "__main__":
    main()
