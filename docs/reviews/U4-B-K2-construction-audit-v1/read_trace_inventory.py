"""Bounded file-access inventory; never a proof of semantic or universal read closure."""

import ast
import collections
import hashlib
import json
import pathlib
import posixpath
import re
import sys

import trace_canary as p

R = pathlib.Path(sys.argv[1]).resolve()
assert R.is_relative_to(pathlib.Path("/tmp"))
phases = sys.argv[2:]
assert phases
quoted = re.compile(r'"(?:\\.|[^"\\])*"')
filecalls = {
    "open",
    "openat",
    "openat2",
    "stat",
    "lstat",
    "newfstatat",
    "statx",
    "access",
    "faccessat",
    "faccessat2",
    "readlink",
    "readlinkat",
    "chdir",
    "execve",
    "execveat",
    "unlink",
    "unlinkat",
    "rename",
    "renameat",
    "renameat2",
    "mkdir",
    "mkdirat",
}
readcalls = {
    "read",
    "pread64",
    "readv",
    "preadv",
    "preadv2",
    "getdents",
    "getdents64",
    "mmap",
    "execve",
    "execveat",
}


def classify(path):
    if path == "/work" or path.startswith("/work/"):
        return "pinned source"
    if path == "/cargo-home" or path.startswith("/cargo-home/"):
        return "pinned cache"
    if path.startswith(("/target/", "/receipts/", "/tmp/")):
        return "generated/output/temporary"
    if path.startswith("/diagnostics/"):
        return "diagnostic input unexpectedly visible to tracee"
    if path.startswith(("/proc/", "/sys/", "/dev/")):
        return "dynamic/kernel/device"
    if path.startswith("/"):
        return "tool/image/OS/configuration"
    return "unresolved relative path"


reports = {}
for mode in phases:
    root = R / "receipts" / mode
    logs = {int(f.name.rsplit(".", 1)[1]): f.read_text() for f in root.glob(mode + ".trace.*")}
    events, children, roots = p.parse(logs)
    by_pid = collections.defaultdict(list)
    for e in events:
        by_pid[e["pid"]].append(e)
    cwd = {next(iter(roots)): "/work/native"}
    pending = list(roots)
    paths = {}
    fd_reads = 0
    unresolved = []
    shared_fs = 0
    envexecs = 0
    while pending:
        pid = pending.pop(0)
        here = cwd[pid]
        for e in by_pid[pid]:
            call, args, result = e["call"], e["args"], e["result"]
            loc = {"pid": pid, "ordinal": e["ordinal"], "call": call, "result": result[:120]}
            strings = quoted.findall(args)
            stripped = quoted.sub('""', args)
            fdpaths = re.findall(r"<(/[^>]*)>", stripped + " " + result)
            candidates = []
            if call in filecalls and strings:
                try:
                    query = ast.literal_eval(strings[0])
                except Exception:
                    query = None
                if query:
                    if query.startswith("/"):
                        resolved = query
                    elif call in {
                        "openat",
                        "openat2",
                        "newfstatat",
                        "faccessat",
                        "faccessat2",
                        "readlinkat",
                        "unlinkat",
                        "mkdirat",
                    } and not args.startswith("AT_FDCWD"):
                        resolved = posixpath.join(fdpaths[0], query) if fdpaths else query
                    else:
                        resolved = posixpath.join(here, query)
                    candidates.append((resolved, "path argument"))
                    if call == "chdir" and result == "0":
                        here = posixpath.normpath(resolved)
            if call == "fchdir" and result == "0":
                if fdpaths:
                    here = fdpaths[0]
                else:
                    unresolved.append({**loc, "reason": "fchdir without decoded path"})
            if call in {"clone", "clone3", "fork", "vfork"}:
                child = re.match(r"([1-9][0-9]*)\b", result)
                if child:
                    child = int(child.group(1))
                    cwd[child] = here
                    pending.append(child)
                    if "CLONE_FS" in args:
                        shared_fs += 1
            if call in readcalls:
                if fdpaths:
                    fd_reads += 1
                elif call not in {"execve", "execveat"} and not (
                    "MAP_ANONYMOUS" in args
                    or "<pipe:" in args
                    or "<socket:" in args
                    or "<UNIX" in args
                ):
                    unresolved.append(
                        {
                            **loc,
                            "reason": "read/mmap/directory operation lacks stable decoded path",
                            "args_prefix": args[:160],
                        }
                    )
            if call in {"execve", "execveat"} and result == "0":
                envexecs += 1
            for path in fdpaths:
                candidates.append((path, "fd path decoded by strace -yy"))
            for path, basis in candidates:
                path = posixpath.normpath(path)
                key = path
                d = paths.setdefault(
                    key,
                    {
                        "class": classify(path),
                        "count": 0,
                        "read_or_mapping_count": 0,
                        "failed_lookup_count": 0,
                        "first_observation": loc,
                        "resolution_basis": set(),
                    },
                )
                d["count"] += 1
                d["read_or_mapping_count"] += int(call in readcalls)
                d["failed_lookup_count"] += int(result.startswith("-1"))
                d["resolution_basis"].add(basis)
    assert set(cwd) == set(logs)
    for path, d in paths.items():
        d["resolution_basis"] = sorted(d["resolution_basis"])
        mapped = None
        if path.startswith("/work/"):
            mapped = R / "source" / path[len("/work/") :]
        elif path.startswith("/cargo-home/"):
            mapped = R / "cache" / path[len("/cargo-home/") :]
        if (
            mapped
            and mapped.is_file()
            and mapped.resolve().is_relative_to(
                (R / "source").resolve() if path.startswith("/work/") else (R / "cache").resolve()
            )
        ):
            d["current_file_sha256"] = hashlib.sha256(mapped.read_bytes()).hexdigest()
    counts = collections.Counter(d["class"] for d in paths.values())
    report = {
        "phase": mode,
        "successful_cwd_changes": [
            e for e in events if e["call"] in {"chdir", "fchdir"} and e["result"] == "0"
        ],
        "diagnostic_child_exec_mentions": [
            e for e in events if e["call"] in {"execve", "execveat"} and "/diagnostics" in e["args"]
        ],
        "process_traces": len(logs),
        "root": sorted(roots),
        "all_child_logs_present": len(children) == len(logs) - 1,
        "all_terminal_records_present": True,
        "records_parsed": len(events),
        "exec_successes": envexecs,
        "path_count": len(paths),
        "path_classes": dict(counts),
        "paths": paths,
        "unresolved_fd_records": unresolved,
        "CLONE_FS_count": shared_fs,
        "limitations": [
            (
                "Per-process raw order retained. cwd is inherited at observed clone"
                " and changed on observed chdir; CLONE_FS cross-thread cwd changes "
                "need separate review."
            ),
            (
                "-yy decoded paths bind observed fds; IPC/device/anonymous memory "
                "and unresolved records are not silently source inputs."
            ),
            (
                "Read buffer abbreviation is not file-content coverage; stable "
                "source/cache hashes are from reverified copies, not proof every "
                "byte was read."
            ),
            "Generated/transient file final hashes cannot recover all historical contents.",
            "Environment arrays are recorded at exec; no semantic variable-use proof.",
            (
                "Tracer loader/DSO activity precedes the child tree and is bound by"
                " static closure, not these traces."
            ),
            (
                "Observed access is not semantic dependency; no universal or "
                "complete build-input authority assertion."
            ),
        ],
    }
    (R / "output" / f"{mode}-read-audit-v2.json").write_text(json.dumps(report, indent=2) + "\n")
    reports[mode] = {k: v for k, v in report.items() if k not in ["paths", "unresolved_fd_records"]}
    reports[mode]["unresolved_fd_record_count"] = len(unresolved)
    print(mode, dict(counts), "unresolved", len(unresolved), flush=True)
(R / "output/read-audit-summary-v2.json").write_text(json.dumps(reports, indent=2) + "\n")
