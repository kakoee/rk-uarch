"""Python-only cost diagnostic over saved genuine outputs; never launch native code."""

import cProfile
import io
import json
import multiprocessing
import os
import pstats
import resource
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/campaign")
import entrypoint

STATE = None


def no_subprocess(*args, **kwargs):
    raise RuntimeError("diagnostic forbids subprocess/native execution")


def check(index):
    samples, anchors, expected_engine, functions = STATE
    loads, strict, canonical, validate, checker, job_model = functions
    request, output, answer = samples[index % len(samples)]
    raw = strict(request)
    trust = {
        **anchors,
        "trusted_profile_hash": raw["admission"]["profile_hash"],
        "expected_engine": expected_engine,
    }
    timings = {}

    def measured(name, function):
        start = time.perf_counter()
        value = function()
        timings[name] = time.perf_counter() - start
        return value

    # Reproduce the pure validation/serialization work seen in run_fixed_delay,
    # encode_request and parse_response, without constructing a host capability.
    encoded = measured("canonical_input", lambda: canonical(raw).encode())
    first = measured("request_admission", lambda: loads(encoded, **trust))
    encoded = measured("canonical_validated_request", lambda: canonical(first).encode())
    assert encoded == request
    second_raw = strict(request)
    encoded2 = measured("response_request_canonicalization", lambda: canonical(second_raw).encode())
    second = measured("response_request_admission", lambda: loads(encoded2, **trust))
    assert (
        measured("response_checked_canonicalization", lambda: canonical(second).encode()) == request
    )
    job = measured("response_second_admission", lambda: loads(request, **trust))
    result = measured("result_validation", lambda: validate(strict(output), job))
    assert measured("canonical_result", lambda: canonical(result).encode()) == output
    typed = measured("checker_job_reparse", lambda: job_model.model_validate_json(request))
    measured("independent_checker", lambda: checker(result, typed, answer))
    return {
        "index": index,
        "timings": timings,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main():
    global STATE
    common_start = time.perf_counter()
    context = entrypoint.common()
    common_elapsed = time.perf_counter() - common_start
    # No authority() or resolve_host(): all work here is validation of saved evidence.
    subprocess.Popen = no_subprocess
    from uarch_contract.hashing import canonical_json, strict_json_loads
    from uarch_contract.mapped import validate_result

    from rkuarch.engines.native.records import HostRecord
    from rkuarch.workload.mapped import loads_fixed_delay_job

    _, _, _, _, _, _, _, job_model, checker = context
    root = Path("/candidate")
    record = HostRecord.model_validate_json(
        (root / "docs/reviews/U4-K2-first-use-authorization-v1/HostRecord.json").read_bytes()
    )
    answers = json.loads(
        (root / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json").read_bytes()
    )
    samples = []
    for case in ["K01", "K02", "K03-owner", "K04"]:
        row = json.loads((Path("/saved/calls") / f"debug-0-{case}.json").read_bytes())
        assert row["status"] == 0
        streams = {}
        for field in ("request", "stdout", "stderr"):
            data = (Path("/saved") / row[field]).read_bytes()
            assert entrypoint.sha(data) == row[field + "_hash"]
            streams[field] = data
        samples.append((streams["request"], streams["stdout"], answers[case]))
    STATE = (
        samples,
        {"trusted_registry_hash": record.registry_hash},
        record.expected_engine,
        (
            loads_fixed_delay_job,
            strict_json_loads,
            canonical_json,
            validate_result,
            checker,
            job_model,
        ),
    )
    profile = cProfile.Profile()
    first = profile.runcall(check, 0)
    buffer = io.StringIO()
    pstats.Stats(profile, stream=buffer).sort_stats("cumulative").print_stats(35)
    Path("/receipts/profile.txt").write_text(buffer.getvalue())
    batches = []
    available = len(os.sched_getaffinity(0))
    # Small diagnostic, not the interrupted 798-call campaign and not qualification.
    for workers in sorted({1, min(8, available), available}):
        start = time.perf_counter()
        if workers == 1:
            results = [check(i) for i in range(16)]
        else:
            with multiprocessing.get_context("fork").Pool(workers) as pool:
                results = pool.map(check, range(16), chunksize=1)
        assert [r["index"] for r in results] == list(range(16))
        batches.append(
            {
                "workers": workers,
                "checks": 16,
                "elapsed_seconds": time.perf_counter() - start,
                "max_worker_rss_kib": max(r["peak_rss_kib"] for r in results),
                "stage_seconds_sum": {
                    k: sum(r["timings"][k] for r in results) for k in first["timings"]
                },
            }
        )
        Path("/receipts/progress.json").write_text(json.dumps(batches, indent=2) + "\n")
    report = {
        "scope": "Python-only saved-output diagnostic; no public invocation or native execution",
        "affinity_cpus": available,
        "cpu_max": Path("/sys/fs/cgroup/cpu.max").read_text().strip(),
        "memory_max": Path("/sys/fs/cgroup/memory.max").read_text().strip(),
        "common_validation_seconds": common_elapsed,
        "profiled_sample": first,
        "batches": batches,
        "native_calls": 0,
        "host_authority_resolved": False,
    }
    Path("/receipts/diagnostic.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
