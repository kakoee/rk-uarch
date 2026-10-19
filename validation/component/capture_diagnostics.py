"""Proposed offline split-stream capture checks; no policy authority or execution entry.

The fixed wrapper redirects the tracee, never the tracer. A retained command/ledger,
root bootstrap, full raw streams and trace-supported writes must agree. Unsupported
write mechanisms or attribution stay refusals. No successful read-audit claim is made.
"""

from __future__ import annotations

import ast
import json
import re
import runpy
from pathlib import Path
from typing import Any, cast

from uarch_contract.hashing import sha256

from validation.component import capture_monitor as legacy
from validation.component.checks import need

POLICY_FORMAT = "component-capture-diagnostic-policy/1"
CAPS = {
    "canary": {
        "child_stdout": 4096,
        "child_stderr": 4096,
        "tracer_stderr": 65536,
        "bootstrap_stdout": 65536,
    },
    "debug": {
        "child_stdout": 16 * 1024**2,
        "child_stderr": 4 * 1024**2,
        "tracer_stderr": 65536,
        "bootstrap_stdout": 65536,
    },
    "release": {
        "child_stdout": 16 * 1024**2,
        "child_stderr": 4 * 1024**2,
        "tracer_stderr": 65536,
        "bootstrap_stdout": 65536,
    },
}
CANARY_ARGV = [
    "/bin/sh",
    "-c",
    'exec 3</canary/alias; /bin/sh -c "/bin/cat <&3"; '
    "if /bin/cat /canary/absent; then exit 81; fi; /bin/ls -U /canary >/dev/null",
]
CANARY_STDOUT = b"U4-read-canary-v1\n"
CANARY_STDERR = b"/bin/cat: /canary/absent: No such file or directory\n"
QUOTED = r'"(?:\\.|[^"\\])*"'


def wrapped_child(phase: str, argv: list[str]) -> list[str]:
    need(
        phase in CAPS and bool(argv) and all(type(v) is str and "\0" not in v for v in argv),
        "child phase/argv",
    )
    return [
        "/bin/sh",
        "-c",
        f"set -C; exec 1>/receipts/{phase}.child.stdout "
        f'2>/receipts/{phase}.child.stderr; exec "$@"',
        "capture-child",
        *argv,
    ]


def paths(phase: str) -> dict[str, str]:
    need(phase in CAPS, "diagnostic phase")
    return {
        "child_stdout": f"traces/{phase}.child.stdout",
        "child_stderr": f"traces/{phase}.child.stderr",
        "tracer_stderr": "container/stderr",
        "bootstrap_stdout": "container/stdout",
    }


def bounded_file(root: Path, relative: str, cap: int) -> bytes:
    path = root / relative
    need(not root.is_symlink() and path.is_relative_to(root), "stream scope")
    for item in (path, *path.parents):
        if item == root.parent:
            break
        need(not item.is_symlink(), "stream symlink")
    need(
        path.is_file() and path.stat().st_size <= cap,
        "missing or oversized raw stream: " + relative,
    )
    raw = path.read_bytes()
    need(len(raw) <= cap, "raw stream grew beyond cap")
    return raw


def bound_input(plan: dict[str, Any], name: str, cap: int = 1024**2) -> bytes:
    pin = plan["inputs"][name]
    path = Path(pin["path"])
    raw = bounded_file(path.parent, path.name, cap)
    need(sha256(raw) == pin["byte_hash"], "diagnostic input identity: " + name)
    return raw


def verify_policy(plan: dict[str, Any]) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(bound_input(plan, "capture_diagnostic_policy"))
    need(
        set(value) == {"format", "phase_caps", "build_stderr_lines"}
        and value["format"] == POLICY_FORMAT,
        "diagnostic policy schema",
    )
    need(value["phase_caps"] == CAPS, "exact proposed diagnostic caps")
    need(set(value["build_stderr_lines"]) == {"debug", "release"}, "build stderr phase rules")
    for lines in value["build_stderr_lines"].values():
        need(
            type(lines) is list and len(lines) <= 4096 and len(lines) == len(set(lines)),
            "finite diagnostic classification",
        )
        for line in lines:
            need(
                type(line) is str
                and 0 < len(line.encode()) <= 4096
                and line.endswith("\n")
                and "\n" not in line[:-1]
                and "\r" not in line
                and "\0" not in line,
                "complete exact diagnostic line",
            )
            need(
                not any(
                    token in line.lower()
                    for token in ("strace:", "records lost", "truncated", "unfinished")
                ),
                "loss/trace diagnostics cannot be child allowlist entries",
            )
    return value


def enforce_stream_caps(root: Path, plan: dict[str, Any], *, complete: bool = False) -> None:
    for key, relative in paths(plan["phase"]).items():
        path = root / relative
        if complete or path.exists() or path.is_symlink():
            for item in (path, *path.parents):
                if item == root.parent:
                    break
                need(not item.is_symlink(), "stream symlink")
            need(
                path.is_file() and path.stat().st_size <= CAPS[plan["phase"]][key],
                "missing or oversized raw stream: " + relative,
            )


def string(raw: str) -> bytes:
    # strace quoted bytes are C-style escapes. ASCII notation plus octal/hex escapes
    # is supported; any undecodable or abbreviated write is a refusal.
    need(re.fullmatch(QUOTED, raw) is not None and raw.isascii(), "complete quoted trace bytes")
    need(re.search(r"\\(?![0-7x\\\"abfnrtv])", raw) is None, "unknown trace string escape")
    value: str = ast.literal_eval(raw)
    need(type(value) is str, "trace string")
    return value.encode("latin1")


def exec_argv(event: dict[str, Any]) -> list[str] | None:
    if event["call"] != "execve" or event["result"] != "0":
        return None
    match = re.match(rf"^({QUOTED}), (\[(?:{QUOTED}(?:, )?)*\]), ", event["args"])
    need(match is not None, "complete exec argv attribution")
    match = cast(re.Match[str], match)
    argv = [string(v).decode() for v in re.findall(QUOTED, match[2])]
    need(bool(argv) and string(match[1]).decode() == argv[0], "exec pathname/argv join")
    return argv


def root_bootstrap(
    events: list[dict[str, Any]], root_pid: int, plan: dict[str, Any]
) -> dict[str, Any]:
    own = [e for e in events if e["pid"] == root_pid]
    executions = [(e, exec_argv(e)) for e in own if e["call"] == "execve" and e["result"] == "0"]
    need(
        len(executions) >= 2
        and executions[0][1] == wrapped_child(plan["phase"], plan["child_argv"])
        and executions[1][1] == plan["child_argv"],
        "exact wrapper then construction exec",
    )
    before = [
        e for e in own if executions[0][0]["ordinal"] < e["ordinal"] < executions[1][0]["ordinal"]
    ]
    need(
        not any(
            e["call"] in ("clone", "clone3", "fork", "vfork", "write", "writev") for e in before
        ),
        "unattributed pre-redirection activity",
    )
    redirected = {}
    for fd, suffix in ((1, "stdout"), (2, "stderr")):
        target = f"/receipts/{plan['phase']}.child.{suffix}"
        opens = [
            e
            for e in before
            if e["call"] == "openat"
            and e["args"] == f'AT_FDCWD, "{target}", O_WRONLY|O_CREAT|O_EXCL, 0666'
        ]
        need(len(opens) == 1, "exclusive child stream creation")
        opened = re.fullmatch(rf"([0-9]+)<{re.escape(target)}>", opens[0]["result"])
        need(opened is not None, "child stream open result")
        opened = cast(re.Match[str], opened)
        if int(opened[1]) != fd:
            remaps = [
                e
                for e in before
                if e["call"] == "dup2"
                and e["ordinal"] > opens[0]["ordinal"]
                and re.fullmatch(rf"{opened[1]}<{re.escape(target)}>, {fd}(?:<[^>]*>)?", e["args"])
                and e["result"] == f"{fd}<{target}>"
            ]
            need(len(remaps) == 1, "child fd redirection witness")
        redirected[str(fd)] = {"path": target, "open_ordinal": opens[0]["ordinal"]}
    return {
        "root": root_pid,
        "wrapper_exec_ordinal": executions[0][0]["ordinal"],
        "child_exec_ordinal": executions[1][0]["ordinal"],
        "redirected": redirected,
    }


def check_writes(events: list[dict[str, Any]], raw: dict[str, bytes], phase: str) -> dict[str, Any]:
    proof = {}
    for stream in ("child_stdout", "child_stderr"):
        target = f"/receipts/{phase}.{stream.replace('_', '.')}"
        chunks: list[bytes] = []
        writers: set[int] = set()
        for event in events:
            if target not in event["args"] or event["call"] not in (
                "write",
                "writev",
                "pwrite64",
                "pwritev",
                "sendfile",
                "splice",
                "copy_file_range",
                "ftruncate",
                "truncate",
                "mmap",
            ):
                continue
            need(event["call"] == "write", "unsupported child stream write mechanism")
            match = re.fullmatch(
                rf"[0-9]+<{re.escape(target)}>, ({QUOTED}), ([0-9]+)", event["args"]
            )
            need(match is not None, "truncated or undecodable child write")
            match = cast(re.Match[str], match)
            data = string(match[1])
            need(len(data) == int(match[2]), "write request length")
            result = re.fullmatch(r"([0-9]+)", event["result"])
            need(
                result is not None and int(result[1]) <= len(data),
                "partial/failed write accounting",
            )
            result = cast(re.Match[str], result)
            if int(result[1]):
                chunks.append(data[: int(result[1])])
                writers.add(event["pid"])
        need(len(writers) <= 1, "multiple writers require separate ordering proof")
        need(b"".join(chunks) == raw[stream], "raw child bytes/write trace join")
        proof[stream] = {
            "writers": sorted(writers),
            "writes": len(chunks),
            "bytes": len(raw[stream]),
            "byte_hash": sha256(raw[stream]),
        }
    return proof


def child_output(raw: dict[str, bytes], phase: str, policy: dict[str, Any]) -> None:
    if phase == "canary":
        need(
            raw["child_stdout"] == CANARY_STDOUT and raw["child_stderr"] == CANARY_STDERR,
            "exact prospective canary output",
        )
        return
    lines = raw["child_stderr"].decode("utf-8").splitlines(keepends=True)
    need(
        all(line in policy["build_stderr_lines"][phase] for line in lines),
        "unclassified child diagnostic",
    )
    output = raw["child_stdout"]
    need(output.endswith(b"\n"), "complete Cargo output line")
    messages = [json.loads(v) for v in output.splitlines()]
    need(all(type(message) is dict for message in messages), "Cargo record objects")
    need(
        bool(messages) and messages[-1] == {"reason": "build-finished", "success": True},
        "explicit Cargo build-finished record",
    )
    need(sum(m.get("reason") == "build-finished" for m in messages) == 1, "unique Cargo completion")
    for message in messages[:-1]:
        need(
            type(message) is dict
            and message.get("reason") in ("compiler-artifact", "build-script-executed"),
            "unclassified Cargo message",
        )
    # No artifact adoption or semantic correctness follows from classifying Cargo records.


def inspect_capture(root: Path, plan: dict[str, Any], status: Any) -> dict[str, Any]:
    report: dict[str, Any] = {
        "format": "component-capture-diagnostics/1",
        "diagnostics_accepted": False,
        "authority": None,
        "read_audit_complete": False,
        "streams": {},
        "statuses": {},
        "traces": {},
        "observed_guardian_status": status,
        "errors": [],
        "loss_state": "unknown; raw evidence retained",
    }
    try:
        phase = plan["phase"]
        policy = verify_policy(plan)
        need(
            type(plan["output_bytes"]) is int
            and 0 < plan["output_bytes"] <= (16 if phase == "canary" else 512) * 1024**2,
            "capture total bound",
        )
        if phase == "canary":
            need(plan["child_argv"] == CANARY_ARGV, "exact canary command")
        enforce_stream_caps(root, plan, complete=True)
        raw, identities = {}, set()
        for key, relative in paths(phase).items():
            path = root / relative
            st = path.stat()
            need(
                st.st_nlink == 1 and (st.st_dev, st.st_ino) not in identities,
                "aliased diagnostic streams",
            )
            identities.add((st.st_dev, st.st_ino))
            raw[key] = bounded_file(root, relative, CAPS[phase][key])
            report["streams"][key] = {
                "path": relative,
                "bytes": len(raw[key]),
                "byte_hash": sha256(raw[key]),
            }
        need(
            raw["tracer_stderr"] == raw["bootstrap_stdout"] == b"",
            "tracer/bootstrap diagnostics or mixed output",
        )
        parser_path = legacy.ROOT / legacy.PARSER
        need(
            sha256(parser_path.read_bytes()) == "sha256:" + legacy.PARSER_HASH,
            "strict parser identity",
        )
        parser_module = runpy.run_path(str(parser_path))
        parser = parser_module["parse"]
        logs = {}
        total = sum(len(value) for value in raw.values())
        for path in sorted((root / "traces").glob(phase + ".trace.*")):
            total += path.stat().st_size
            need(total <= plan["output_bytes"], "trace total byte cap")
            trace_raw = bounded_file(root, str(path.relative_to(root)), plan["output_bytes"])
            pid = int(path.name.rsplit(".", 1)[1])
            need(pid not in logs, "unique PID trace file")
            report["traces"][str(pid)] = {
                "path": str(path.relative_to(root)),
                "bytes": len(trace_raw),
                "byte_hash": sha256(trace_raw),
            }
            logs[pid] = trace_raw.decode("utf-8")
        report["accounted_stream_and_trace_bytes"] = total
        need(sum(len(t.splitlines()) for t in logs.values()) <= 200000, "trace record bound")
        events, children, roots = parser(logs)
        allowed = json.loads(bound_input(plan, "syscall_policy"))["classified_syscalls"]
        need(not ({e["call"] for e in events} - set(allowed)), "unknown syscall record")
        root_pid = next(iter(roots))
        for pid, log in logs.items():
            lines = log.splitlines()
            terminal = [v for v in lines if "+++" in v]
            match = re.fullmatch(r"[0-9]+\.[0-9]+ \+\+\+ exited with ([0-9]+) \+\+\+", lines[-1])
            need(len(terminal) == 1 and match is not None, "missing/ambiguous terminal status")
            match = cast(re.Match[str], match)
            report["statuses"][str(pid)] = int(match[1])
        need(
            type(status) is int and status == report["statuses"][str(root_pid)] == 0,
            "root/guardian success join",
        )
        execs = {
            pid: [v for e in events if e["pid"] == pid and (v := exec_argv(e)) is not None]
            for pid in logs
        }
        expected_failed = {
            pid
            for pid, rows in execs.items()
            if phase == "canary" and rows and rows[-1] == ["/bin/cat", "/canary/absent"]
        }
        need(
            len(expected_failed) == (1 if phase == "canary" else 0),
            "phase-specific failed lookup process",
        )
        need(
            all(
                code == (1 if int(pid) in expected_failed else 0)
                for pid, code in report["statuses"].items()
            ),
            "child terminal status classification",
        )
        report["bootstrap"] = root_bootstrap(events, root_pid, plan)
        report["write_accounting"] = check_writes(events, raw, phase)
        child_output(raw, phase, policy)
        if phase == "canary":
            need(
                set(report["write_accounting"]["child_stderr"]["writers"]) == expected_failed,
                "canary diagnostic writer must be failed lookup child",
            )
            stdout_writers = report["write_accounting"]["child_stdout"]["writers"]
            need(
                len(stdout_writers) == 1 and execs[stdout_writers[0]][-1] == ["/bin/cat"],
                "canary stdout writer",
            )
            report["canary"] = parser_module["check"](logs, raw["child_stdout"])
        report.update(
            diagnostics_accepted=True,
            root=root_pid,
            children=sorted(children),
            events=len(events),
            loss_state=(
                "empty tracer channel and complete classified records; "
                "not an independent loss counter"
            ),
        )
    except (ValueError, KeyError, TypeError, OSError, SyntaxError, UnicodeError) as error:
        report["errors"].append(str(error))
    return report
