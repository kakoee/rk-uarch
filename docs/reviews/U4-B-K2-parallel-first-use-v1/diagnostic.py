"""Bounded saved-output validation only; no native calls or replacement authority."""

import json
import resource
import subprocess
import sys
import time
from pathlib import Path

from parallel_core import Store, digest, require, run_workers
from resource_limits import discover

sys.path.insert(0, "/campaign")
import entrypoint as base

STATE = None
CASES = ["K01", "K02", "K03-owner", "K04", "K05-chain", "K05", "K06-00", "K06-01"]


def forbid(*args, **kwargs):
    raise RuntimeError("diagnostic prohibits native/subprocess execution")


def check(case):
    context, hosts, samples, answers = STATE
    _, _, _, _, runner, canonical, _, job_model, checker = context
    from uarch_contract.hashing import strict_json_loads

    request, output, error, status = samples[case]
    start = time.monotonic()
    encoded = runner.encode_request(strict_json_loads(request), host=hosts["debug"])
    require(encoded == request, "real saved canonical request mismatch")
    result = runner.parse_response(
        output, error, status, request_bytes=request, host=hosts["debug"]
    )
    checker(result, job_model.model_validate_json(request), answers[case])
    require(canonical(result).encode() == output, "real saved canonical result mismatch")
    return {
        "case": case,
        "request_hash": digest(request),
        "stdout_hash": digest(output),
        "stderr_hash": digest(error),
        "status": status,
        "elapsed_seconds": time.monotonic() - start,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    global STATE
    start = time.monotonic()
    context = base.common()
    policy = json.loads(Path("/parallel/parallel-policy.json").read_bytes())
    store = Store("/receipts", 32 * 1024**2)
    store.json(
        "diagnostic-start.json",
        {"case_ids": CASES, "native_calls": 0, "status": "starting genuine production resolution"},
    )
    hosts = base.authority(context[1], context[3])
    resolver_seconds = time.monotonic() - start
    subprocess.Popen = forbid
    context[4]._exchange = forbid
    samples = {}
    source_rows = {}
    for case in CASES:
        row_file = Path("/saved/calls") / ("debug-0-" + case + ".json")
        row = json.loads(row_file.read_bytes())
        require(
            row["case_id"] == case
            and row["mode"] == "debug"
            and row["repetition"] == 0
            and row["status"] == 0,
            "actual completed saved sample required",
        )
        streams = []
        for field in ["request", "stdout", "stderr"]:
            data = (Path("/saved") / row[field]).read_bytes()
            require(digest(data) == row[field + "_hash"], "saved sample byte drift")
            streams.append(data)
        samples[case] = (*streams, row["status"])
        source_rows[case] = digest(row_file.read_bytes())
    answers = base.read_json(
        base.ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json"
    )
    STATE = context, hosts, samples, answers
    resources = discover(policy, len(CASES))
    batches = []
    for workers in sorted({1, resources["workers"]}):
        started = time.monotonic()
        results = run_workers(
            CASES,
            check,
            workers=workers,
            task_timeout=180,
            total_timeout=600,
            executable_paths=tuple(str(base.ROOT / h.executable.path) for h in hosts.values()),
        )
        elapsed = time.monotonic() - started
        require([r["case"] for r in results] == CASES, "diagnostic ordered membership")
        record = {
            "workers": workers,
            "checks": len(CASES),
            "elapsed_seconds": elapsed,
            "peak_worker_rss_kib": max(r["peak_rss_kib"] for r in results),
            "results": results,
        }
        store.json(f"diagnostic-{workers}.json", record)
        batches.append(record)
    require(len(batches) == 2, "parallel comparison unavailable; do not claim speedup")
    fields = ["case", "request_hash", "stdout_hash", "stderr_hash", "status"]
    require(
        [{k: r[k] for k in fields} for r in batches[0]["results"]]
        == [{k: r[k] for k in fields} for r in batches[1]["results"]],
        "serial/parallel byte mismatch",
    )
    base.common()
    store.json(
        "diagnostic.json",
        {
            "scope": (
                "actual saved-output Python validation; no native/public call, "
                "not campaign qualification"
            ),
            "original_subject": context[1]["subject"],
            "case_ids": CASES,
            "saved_row_hashes": source_rows,
            "actual_production_host_resolution": True,
            "setup_and_resolver_seconds": resolver_seconds,
            "resource_selection": resources,
            "batches": batches,
            "observed_serial_over_parallel_ratio": batches[0]["elapsed_seconds"]
            / batches[1]["elapsed_seconds"],
            "native_calls": 0,
            "new_qualifying_results": 0,
            "limitations": (
                "One local comparison; excludes native work and resolver startup "
                "from timed batches; memory maximum and full-campaign throughput "
                "are not established."
            ),
        },
    )


if __name__ == "__main__":
    main()
