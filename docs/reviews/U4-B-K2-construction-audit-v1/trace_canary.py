"""Canary coverage checks over owned strace -ff logs, preserving per-process order."""

import re


class CoverageError(ValueError):
    pass


def parse(logs):
    if not logs:
        raise CoverageError("no process traces")
    events = []
    children = set()
    for pid, text in logs.items():
        pending = None
        terminal = False
        for ordinal, raw in enumerate(text.splitlines()):
            body = re.sub(r"^\d+\.\d+\s+", "", raw)
            if body.startswith("+++ exited with ") or body.startswith("+++ killed by "):
                terminal = True
                continue
            if body.startswith("--- "):
                continue
            if "<unfinished ...>" in body:
                if pending:
                    raise CoverageError("overlapping unfinished calls")
                pending = body.split("<unfinished ...>")[0]
                continue
            if body.startswith("<... "):
                if pending is None:
                    raise CoverageError("resumed call without beginning")
                body = pending + body.split(" resumed>", 1)[1]
                pending = None
            match = re.fullmatch(r"([a-zA-Z_][a-zA-Z_0-9]*)\((.*)\)\s+=\s+(.*)", body)
            if not match:
                raise CoverageError(f"unparsed record for pid {pid}: {body[:120]}")
            call, args, result = match.groups()
            if call in {
                "execve",
                "execveat",
                "open",
                "openat",
                "openat2",
                "readlink",
                "readlinkat",
                "chdir",
            } and re.search(r'"(?:\\.|[^"\\])*"\.\.\.', args):
                raise CoverageError("truncated path/argv in relevant call")
            events.append(
                {"pid": pid, "ordinal": ordinal, "call": call, "args": args, "result": result}
            )
            if call in {"clone", "clone3", "fork", "vfork"}:
                child = re.match(r"([1-9][0-9]*)\b", result)
                if child:
                    children.add(int(child.group(1)))
        if pending or not terminal:
            raise CoverageError("missing terminal or unfinished call")
    if children - set(logs):
        raise CoverageError("missing child trace")
    roots = set(logs) - children
    if len(roots) != 1:
        raise CoverageError("ambiguous owned process root")
    return events, children, roots


def check(logs, stdout):
    if stdout != b"U4-read-canary-v1\n":
        raise CoverageError("sentinel output absent or changed")
    events, children, roots = parse(logs)

    def exists(call, fragment, result=None):
        return any(
            e["call"] in call
            and fragment in e["args"]
            and (result is None or result in e["result"])
            for e in events
        )

    obligations = {
        "owned_descendants": bool(children),
        "shell_exec": exists({"execve"}, '"/bin/sh"', "0"),
        "cat_exec": exists({"execve"}, '"/bin/cat"', "0"),
        "ls_exec": exists({"execve"}, '"/bin/ls"', "0"),
        "alias_open": exists({"openat", "open"}, '"/canary/alias"'),
        "resolved_sentinel_read": exists({"read", "pread64", "readv"}, "</canary/sentinel>"),
        "sentinel_close": exists({"close"}, "</canary/sentinel>"),
        "missing_file": exists({"openat", "open"}, '"/canary/absent"', "ENOENT"),
        "directory_enumeration": exists({"getdents64", "getdents"}, "</canary>"),
        "image_file_mmap": any(e["call"] == "mmap" and "</" in e["args"] for e in events),
    }
    if not all(obligations.values()):
        raise CoverageError(
            "missing canary evidence: " + str([k for k, v in obligations.items() if not v])
        )
    reads = [
        e
        for e in events
        if e["call"] in {"read", "pread64", "readv"} and "</canary/sentinel>" in e["args"]
    ]
    return {
        "processes": len(logs),
        "children": sorted(children),
        "roots": sorted(roots),
        "events": len(events),
        "obligations": obligations,
        "undeclared_sentinel": {
            "path": "/canary/sentinel",
            "declared_source_or_cache": False,
            "read_events": reads,
        },
        "limitations": [
            "Frozen inventory resolves symlinks; a readlink syscall is not required.",
            "Observed mmap is not proof every mapped byte was consumed.",
            "Exec environment presence does not prove variable use.",
            "This finite canary is not exhaustive build-read or semantic-dependency proof.",
        ],
    }
