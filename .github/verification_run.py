"""Sequential local verification stages with streamed logs and explicit dispositions.

Plans are trusted local commands, never a policy/qualification engine. Expected failures
need an exact exit and diagnostic; restoration stages use ``always: true``. A killed run
has progress/logs but no completed summary. No shell, retries, caching or parallel pools.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import resource
import subprocess
import time
from pathlib import Path
from typing import Any


def run(plan: list[dict[str, Any]], output: Path) -> bool:
    if not isinstance(plan, list) or not plan:
        raise ValueError("empty verification plan")
    for stage in plan:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", stage["name"]):
            raise ValueError("stage name must be a filename-safe identifier")
        if (
            not isinstance(stage["argv"], list)
            or not stage["argv"]
            or not all(isinstance(a, str) for a in stage["argv"])
        ):
            raise ValueError("stage argv must be a nonempty string array")
        if stage.get("expected_exit", 0) not in (0, 1):
            raise ValueError("only success or an assertion failure may be expected; no empty suite")
        if stage.get("expected_exit", 0) != 0 and not stage.get("contains"):
            raise ValueError("expected failure requires a diagnostic identity")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    stages: list[dict[str, Any]] = []
    passed = True
    with (output / "progress.jsonl").open("x", buffering=1) as progress:

        def emit(event: str, **fields: Any) -> None:
            value = {
                "event": event,
                "elapsed_s": time.monotonic() - started,
                "completed": len(stages),
                "planned": len(plan),
                **fields,
            }
            line = json.dumps(value)
            progress.write(line + "\n")
            print(line, flush=True)

        emit(
            "start",
            cwd=str(Path.cwd()),
            platform=platform.platform(),
            cpu_count=os.cpu_count(),
            load=os.getloadavg(),
            plan_sha256=hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
        )
        for index, stage in enumerate(plan, 1):
            name = stage["name"]
            if not passed and not stage.get("always", False):
                stages.append({"name": name, "outcome": "not_run", "reason": "prior failure"})
                emit("not_run", name=name)
                continue
            prefix = f"{index:03}-{name}"
            stdout, stderr = output / (prefix + ".stdout.log"), output / (prefix + ".stderr.log")
            emit(
                "stage_start", name=name, argv=stage["argv"], stdout=str(stdout), stderr=str(stderr)
            )
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            start = time.monotonic()
            error = None
            with stdout.open("xb") as out, stderr.open("xb") as err:
                try:
                    process = subprocess.Popen(stage["argv"], stdout=out, stderr=err)
                    while True:
                        try:
                            code = process.wait(timeout=15)
                            break
                        except subprocess.TimeoutExpired:
                            emit("running", name=name, stage_elapsed_s=time.monotonic() - start)
                except OSError as exc:
                    code, error = None, str(exc)
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            diagnostic = stdout.read_text(errors="replace") + stderr.read_text(errors="replace")
            missing = [s for s in stage.get("contains", []) if s not in diagnostic]
            ok = code == stage.get("expected_exit", 0) and not missing
            result = {
                "name": name,
                "outcome": "passed" if ok else "failed",
                "argv": stage["argv"],
                "returncode": code,
                "expected_exit": stage.get("expected_exit", 0),
                "missing_diagnostics": missing,
                "launch_error": error,
                "elapsed_s": time.monotonic() - start,
                "user_cpu_s": after.ru_utime - before.ru_utime,
                "system_cpu_s": after.ru_stime - before.ru_stime,
                "children_high_water_rss_kib": after.ru_maxrss,
            }
            stages.append(result)
            passed = passed and ok
            emit("stage_finish", **result)
        emit("finish", passed=passed)
    summary = {
        "complete": True,
        "passed": passed,
        "stages": stages,
        "elapsed_s": time.monotonic() - started,
        "memory_note": "Linux child RSS high-water mark across completed stages, not summed RAM",
    }
    temporary = output / "summary.json.tmp"
    temporary.write_text(json.dumps(summary, indent=2) + "\n")
    temporary.rename(output / "summary.json")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(json.loads(args.plan.read_text()), args.output) else 1)


if __name__ == "__main__":
    main()
