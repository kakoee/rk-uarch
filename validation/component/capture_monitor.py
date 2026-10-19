"""Prospective full-ID capture orchestration. No CLI, authority or read-completeness claim.

Tests use subprocess mocks; actual invocation needs separately approved frozen inputs.
The historical name-based monitor and read evidence remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import re
import runpy
import time
from pathlib import Path
from typing import Any

from uarch_contract.hashing import canonical_json, sha256

from native.tools import component_container_guard as guardian
from validation.component.checks import need
from validation.component.ordinary_eof_campaign import cleanup_owned
from validation.component.runtime_campaign import helpers

ROOT = Path(__file__).resolve().parents[2]
PARSER = "docs/reviews/U4-B-K2-construction-audit-v1/trace_canary.py"
PARSER_HASH = "e330c3046534309314915056ad7153ce0478c3c2662997eca97a01c9b00f5fe3"
DIAGNOSTICS_HASH = "sha256:2d9362e720f55d2bc133afb48f5ad6949b765fba8e746cc5dcbca0f3c70a1de6"
TOOLS_HASH = "sha256:db8b8956f0c060416d0d3c6c11f8eccc6b3ece7433b5075cb093e602febcb73d"
CARGO = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/cargo"
METADATA_BYTES = 8 * 1024**2
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
TRACER = [
    "/lib64/ld-linux-x86-64.so.2",
    "--library-path",
    "/diagnostics/usr/lib/x86_64-linux-gnu:/diagnostics/lib/x86_64-linux-gnu",
    "/diagnostics/usr/bin/strace",
    "-ff",
    "-ttt",
    "-yy",
    "-v",
    "-s",
    "4096",
    "-o",
]


def save(path: Path, value: Any) -> None:
    data = canonical_json(value).encode()
    need(len(data) <= METADATA_BYTES, "capture metadata reserve")
    path.write_bytes(data)


def inventory(root: Path) -> tuple[int, dict[str, Any]]:
    need(not root.is_symlink(), "output root symlink")
    rows = {}
    for index, path in enumerate(root.rglob("*")):
        need(index < 16384, "output file-count limit")
        need(not path.is_symlink(), "output symlink")
        if path.is_file():
            rows[str(path.relative_to(root))] = {"bytes": path.stat().st_size}
        else:
            need(path.is_dir(), "unexpected output inode")
    return sum(v["bytes"] for v in rows.values()), rows


def verify_plan(plan: dict[str, Any]) -> None:
    need(
        plan["format"] == "component-capture-plan/1" and plan["image"] == IMAGE,
        "frozen capture format/image",
    )
    need(
        isinstance(plan["source_commit"], str)
        and re.fullmatch("[0-9a-f]{40}", plan["source_commit"]) is not None,
        "exact source commit",
    )
    need(plan["phase"] in ("debug", "release", "canary"), "capture phase")
    need(
        set(plan["inputs"])
        == {
            "build_inputs",
            "generated_identity",
            "diagnostics",
            "environment",
            "syscall_policy",
            "construction_recipe",
        },
        "complete frozen capture inputs",
    )
    for item in plan["inputs"].values():
        path = Path(item["path"])
        need(
            path.is_file()
            and not path.is_symlink()
            and sha256(path.read_bytes()) == item["byte_hash"],
            "capture input binding",
        )
    build = json.loads(Path(plan["inputs"]["build_inputs"]["path"]).read_bytes())
    need(build["source_commit"] == plan["source_commit"], "capture BuildInputs source join")
    recipe = json.loads(Path(plan["inputs"]["construction_recipe"]["path"]).read_bytes())
    need(
        recipe["format"] == "component-capture-recipe/1"
        and recipe["source_commit"] == plan["source_commit"]
        and recipe["build_inputs_byte_hash"] == plan["inputs"]["build_inputs"]["byte_hash"],
        "construction recipe source/build join",
    )
    # Legacy component BuildInputs /1 omits fields carried by runtime BuildInputs /2.
    # Freeze them in an explicit additive companion, never rewrite old BuildInputs.
    for key in ("permitted_environment", "mode_configs", "generated_identity_output_paths"):
        need(key not in build or build[key] == recipe[key], "recipe cannot override BuildInputs")
    need(recipe["preparation_source"] in build["source_files"], "recipe preparation source binding")
    environment = json.loads(Path(plan["inputs"]["environment"]["path"]).read_bytes())
    need(
        environment == plan["environment"] == recipe["permitted_environment"]
        and not any(k in environment for k in ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")),
        "frozen clean environment",
    )
    if plan["phase"] != "canary":
        mode = next(v for v in recipe["mode_configs"] if v["mode"] == plan["phase"])
        need(plan["child_argv"] == [CARGO, *mode["cargo_args"]], "exact construction argv")
    else:
        expected = [
            "/bin/sh",
            "-c",
            'exec 3</canary/alias; /bin/sh -c "/bin/cat <&3"; '
            "if /bin/cat /canary/absent; then exit 81; fi; /bin/ls -U /canary >/dev/null",
        ]
        need(plan["child_argv"] == expected, "exact accepted canary argv")
    need(
        set(plan["mounts"]) == {"/work", "/cargo-home", "/controls", "/diagnostics", "/canary"},
        "exact readonly mounts",
    )
    need(
        all(Path(v).is_dir() and not Path(v).is_symlink() for v in plan["mounts"].values()),
        "existing frozen mount roots",
    )
    work = Path(plan["mounts"]["/work"]).resolve()
    need(
        all(
            not Path(v["path"]).is_absolute() and ".." not in Path(v["path"]).parts
            for v in build["source_files"]
        ),
        "relative source inventory paths",
    )
    expected_sources = {str(work / v["path"]): v["byte_hash"] for v in build["source_files"]}
    need(len(expected_sources) == len(build["source_files"]), "unique source inventory")
    need(plan["source_files"] == expected_sources, "exact BuildInputs source inventory")
    generated = Path(plan["inputs"]["generated_identity"]["path"]).resolve()
    need(
        generated.is_relative_to(work)
        and str(generated.relative_to(work)) in recipe["generated_identity_output_paths"],
        "generated identity path join",
    )
    tools = build["tool_inputs_file"]
    tool_path = Path(plan["tool_inputs"]["path"])
    need(
        plan["tool_inputs"]["byte_hash"] == tools["byte_hash"] == TOOLS_HASH
        and sha256(tool_path.read_bytes()) == TOOLS_HASH,
        "accepted ToolInputs join",
    )
    need(json.loads(tool_path.read_bytes())["image_digest"] == IMAGE, "ToolInputs image")
    need(
        plan["inputs"]["diagnostics"]["byte_hash"] == DIAGNOSTICS_HASH,
        "accepted diagnostics identity",
    )
    diagnostic = json.loads(Path(plan["inputs"]["diagnostics"]["path"]).read_bytes())
    need(diagnostic["image"] == IMAGE, "diagnostics image")
    diagnostic_root = Path(plan["mounts"]["/diagnostics"])
    diagnostic_files = {
        str(diagnostic_root / name.split("/", 1)[1]): "sha256:" + pin["sha256"]
        for name, pin in diagnostic["extracted_files"].items()
        if name.split("/", 1)[0] in ("strace", "libunwind8")
    }
    need(
        all(plan["tool_files"].get(k) == v for k, v in diagnostic_files.items()),
        "diagnostic tool closure",
    )
    links = diagnostic["extracted_symlinks"]
    expected_links = {}
    for name, pin in links.items():
        path = diagnostic_root / name.split("/", 1)[1]
        target = diagnostic_root / pin["resolved_within_private_root"].split("/", 1)[1]
        need(
            path.is_symlink()
            and str(path.readlink()) == pin["target"]
            and path.resolve() == target.resolve(),
            "diagnostic symlink binding",
        )
        expected_links[str(path)] = pin["target"]
    need(
        {str(p) for p in diagnostic_root.rglob("*") if not p.is_dir()}
        == set(diagnostic_files) | set(expected_links),
        "exact diagnostic mount inventory",
    )
    # These inputs freeze closure; they do not establish complete construction reads.
    for mount in ("/cargo-home", "/controls", "/canary"):
        path = Path(plan["mounts"][mount])
        actual = {}
        for item in path.rglob("*"):
            need(not item.is_symlink(), "tool mount symlink needs separately reviewed binding")
            if item.is_file():
                actual[str(item)] = sha256(item.read_bytes())
            else:
                need(item.is_dir(), "tool mount inode")
        need(
            actual == {k: v for k, v in plan["tool_files"].items() if Path(k).is_relative_to(path)},
            "exact tool mount inventory",
        )
    # Explicit resource bounds are reviewed construction inputs, not public-call defaults.
    need(0 < plan["seconds"] <= (30 if plan["phase"] == "canary" else 600), "capture time budget")
    need(
        0 < plan["output_bytes"] <= (16 if plan["phase"] == "canary" else 512) * 1024**2,
        "capture output budget",
    )
    need(0 < plan["stream_bytes"] <= plan["output_bytes"], "capture stream bound")
    need(
        all(
            type(plan[k]) is int and plan[k] > 0 for k in ("cpus", "memory_bytes", "pids", "nofile")
        ),
        "explicit construction resources",
    )
    need(plan["source_files"] and plan["tool_files"], "source and accepted tool closure")
    for name, pin in {**plan["source_files"], **plan["tool_files"]}.items():
        path = Path(name)
        need(path.is_absolute(), "absolute closure path")
        need(not path.is_symlink() and sha256(path.read_bytes()) == pin, "source/tool currentness")


def command(plan: dict[str, Any], root: Path) -> list[str]:
    args = [
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp",
        "--cpus",
        str(plan["cpus"]),
        "--memory",
        str(plan["memory_bytes"]),
        "--pids-limit",
        str(plan["pids"]),
        "--ulimit",
        f"nofile={plan['nofile']}:{plan['nofile']}",
        "--workdir",
        "/work/native",
    ]
    for target, origin in sorted(plan["mounts"].items()):
        args.extend(["--mount", f"type=bind,src={Path(origin).resolve()},dst={target},readonly"])
    for target, name in (("/receipts", "traces"), ("/target", "target")):
        args.extend(["--mount", f"type=bind,src={root / name},dst={target}"])
    result: list[str] = (
        args
        + ["--entrypoint", "/usr/bin/env", IMAGE, "-i"]
        + [k + "=" + v for k, v in sorted(plan["environment"].items())]
        + TRACER
        + ["/receipts/" + plan["phase"] + ".trace"]
        + plan["child_argv"]
    )
    return result


def _worker(root: Path, args: list[str], seconds: float, cap: int) -> None:
    try:
        value = guardian.run_container(
            root / "container", args, timeout=seconds, cap=cap, stderr_cap=cap
        )
        save(root / "worker.json", {"returned": True, "cleanup": value})
    except BaseException as error:
        save(root / "worker.json", {"returned": False, "error": repr(error)})


def analyze(root: Path, plan: dict[str, Any], status: int) -> dict[str, Any]:
    path = ROOT / PARSER
    need(sha256(path.read_bytes()) == "sha256:" + PARSER_HASH, "strict parser identity")
    parser = runpy.run_path(str(path))["parse"]
    traces = {
        int(p.name.rsplit(".", 1)[1]): p.read_text()
        for p in (root / "traces").glob(plan["phase"] + ".trace.*")
    }
    events, children, roots = parser(traces)
    policy = json.loads(Path(plan["inputs"]["syscall_policy"]["path"]).read_bytes())
    unknown = sorted({e["call"] for e in events} - set(policy["classified_syscalls"]))
    need(not unknown, "unclassified syscall records: " + repr(unknown))
    pid = next(iter(roots))
    terminal = re.findall(r"\+\+\+ exited with (\d+) \+\+\+", traces[pid])
    need(len(terminal) == 1 and int(terminal[0]) == status, "root exit/status join")
    stderr = (root / "container/stderr").read_bytes()
    need(not stderr, "tracer/child stderr requires explicit loss and diagnostic reconciliation")
    return {
        "root": pid,
        "children": sorted(children),
        "processes": len(traces),
        "events": len(events),
        "unknown_syscalls": unknown,
        "unmatched_unfinished": False,
        "raw_unfinished_records": sum(t.count("<unfinished ...>") for t in traces.values()),
        "loss_state": "no stderr diagnostic observed; not an independent loss counter",
        "structural_records_complete": True,
        "read_audit_complete": False,
    }


def run_capture(plan: dict[str, Any], root: Path) -> dict[str, Any]:
    """Future approved exercise only. This function supplies no execution authority."""
    verify_plan(plan)
    root = root.resolve()
    root.mkdir(exist_ok=False)
    (root / "traces").mkdir()
    (root / "target").mkdir()
    args = command(plan, root)
    start, wall = time.monotonic(), time.time_ns()
    save(
        root / "start.json",
        {"plan": plan, "argv": args, "started_ns": wall, "started_monotonic": start},
    )
    process = multiprocessing.get_context("fork").Process(
        target=_worker, args=(root, args, plan["seconds"], plan["stream_bytes"])
    )
    reason, coverage, cleanup = None, None, None
    status = None
    total: int | None = None
    started = False
    try:
        helpers()["safe_fork"]()
        process.start()
        started = True
        while process.is_alive():
            total, _ = inventory(root)
            if total >= plan["output_bytes"]:
                reason = "total output limit"
            if time.monotonic() - start >= plan["seconds"]:
                reason = reason or "capture deadline"
            if reason:
                break
            time.sleep(0.01)
    except BaseException as error:
        reason = repr(error)
    finally:
        if reason:
            # Signal only this task's guardian ledger; never a Docker name or shared label.
            if (root / "container/intent.json").exists():
                (root / "container/cancel").touch()
        if started:
            process.join(0.1 if reason else 1)
        if process.is_alive():
            process.terminate()
            process.join(2)
        if process.is_alive():
            process.kill()
            process.join(2)
        joined = not process.is_alive()
        if joined and started:
            process.close()
        try:
            need(joined, "capture worker not joined")
            cleanup = cleanup_owned(root)
            need(cleanup["complete"] and len(cleanup["receipts"]) == 1, "capture full-ID cleanup")
            receipt = cleanup["receipts"][0]["receipt"]
            ledger = root / "container"
            intent = json.loads((ledger / "intent.json").read_bytes())
            need(
                intent["args"] == args
                and intent["timeout"] == plan["seconds"]
                and intent["cap"] == intent["stderr_cap"] == plan["stream_bytes"]
                and intent["stdin"] is False,
                "capture intent/plan join",
            )
            need(
                json.loads((ledger / "started.json").read_bytes())
                == {"container_id": receipt["container_id"]},
                "capture started full-ID join",
            )
            need(
                all(
                    (ledger / stream).stat().st_size <= plan["stream_bytes"]
                    for stream in ("stdout", "stderr")
                ),
                "capture retained stream bounds",
            )
            status = receipt["exit_code"]
            need(
                type(status) is int and receipt["reason"] == "completed",
                "capture process completion",
            )
            total, _ = inventory(root)
            need(
                total < plan["output_bytes"] and time.monotonic() - start < plan["seconds"],
                "capture final limits",
            )
            need(reason is None, "capture monitor interrupted: " + str(reason))
            verify_plan(plan)
            coverage = analyze(root, plan, status)
        except BaseException as error:
            reason = reason or repr(error)
    try:
        total, rows = inventory(root)
        for name in rows:
            digest = hashlib.sha256()
            with (root / name).open("rb") as stream:
                while chunk := stream.read(1024**2):
                    digest.update(chunk)
            rows[name]["byte_hash"] = "sha256:" + digest.hexdigest()
    except Exception as error:
        total, rows = None, {}
        reason = reason or repr(error)
    record = {
        "format": "component-capture-receipt/1",
        "authority": None,
        "started_ns": wall,
        "ended_ns": time.time_ns(),
        "started_monotonic": start,
        "ended_monotonic": time.monotonic(),
        "status": status,
        "reason": reason,
        "cleanup": cleanup,
        "coverage": coverage,
        "output_bytes": total,
        "files": rows,
        "record_valid": reason is None,
        "command_succeeded": reason is None and status == 0,
        "read_audit_complete": False,
        "limits": {"seconds": plan["seconds"], "bytes": plan["output_bytes"]},
        "loss_state": coverage["loss_state"] if coverage else "unknown; retained partial evidence",
        "limitations": [
            "Polling may overshoot; any overshoot refuses acceptance.",
            "This is record integrity, not read reconciliation or A-F3 assurance.",
            "Final monitor record has a separate bounded metadata reserve.",
        ],
    }
    if len(canonical_json(record).encode()) > METADATA_BYTES:
        record.update(
            record_valid=False,
            command_succeeded=False,
            reason="capture metadata reserve exceeded; raw records retained",
            files={},
            cleanup=None,
            coverage=None,
        )
    save(root / "capture.json", record)
    return record
