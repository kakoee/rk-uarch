# ruff: noqa: E402
# Imports follow explicit private runtime paths.
"""Private shared-session/case join using genuine authority and saved outputs only."""

import contextlib
import importlib.util
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

from parallel_core import Store, digest, require, run_workers
from resource_limits import discover

sys.path[:0] = ["/campaign", "/join"]
import diagnostic
import entrypoint as base
import parallel_case_reuse as grouped
import reuse_join as reuse

SELECT = None


def child_selection(task):
    try:
        SELECT(mode="debug")
    except ValueError as error:
        require(
            str(error) == "resolution session expired or belongs to another process", "PID guard"
        )
        return {"case": task, "selection_refused": True}
    raise AssertionError("parent selector callable accepted in child")


def main():
    global SELECT
    started = time.monotonic()
    out = Store("/receipts", 64 * 1024**2)
    baseline_context = base.common()
    baseline_modules = {
        n: m for n, m in sys.modules.copy().items() if n.startswith(("rkuarch", "uarch_contract"))
    }
    original_path = sys.path.copy()
    proposal = json.loads(Path("/join/proposal-files.json").read_bytes())
    for name, expected in proposal.items():
        require(
            digest((Path("/proposal") / name).read_bytes()) == expected, "private proposal drift"
        )
    for name in baseline_modules:
        del sys.modules[name]
    sys.path[:0] = ["/proposal/src", "/proposal/contract"]
    from uarch_contract.hashing import canonical_json, content_hash
    from uarch_contract.mapped import MappedEngineJob

    from rkuarch.engines.native import host, runner
    from rkuarch.workload import mapped

    spec = importlib.util.spec_from_file_location(
        "B_candidate_checker",
        "/candidate/docs/reviews/U4-B-K2-construction-audit-v1/first_use_checks.py",
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    context = (
        *baseline_context[:3],
        host,
        runner,
        canonical_json,
        content_hash,
        MappedEngineJob,
        checker.check_real_result,
    )
    subprocess.Popen = reuse.forbidden
    runner._exchange = reuse.forbidden

    def audit(event, args):
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            reuse.forbidden()

    sys.addaudithook(audit)
    cases = diagnostic.CASES
    samples, source_rows = {}, {}
    for case in cases:
        path = Path("/saved/calls") / ("debug-0-" + case + ".json")
        row = json.loads(path.read_bytes())
        require(
            row["case_id"] == case
            and row["mode"] == "debug"
            and row["repetition"] == 0
            and row["status"] == 0,
            "actual saved debug0 sample",
        )
        values = {
            field: (Path("/saved") / row[field]).read_bytes()
            for field in ("request", "stdout", "stderr")
        }
        require(
            all(digest(data) == row[field + "_hash"] for field, data in values.items()),
            "saved stream drift",
        )
        samples[case] = values
        source_rows[case] = digest(path.read_bytes())
    answers = base.read_json(
        base.ROOT / "docs/reviews/U4-A-K2-construction-v1/corpus/expectations.json"
    )
    policy = json.loads(Path("/join/parallel-policy.json").read_bytes())
    resources = discover(policy, len(cases))
    report = {
        "scope": "private Python saved-output shared startup/case diagnostic",
        "native_calls": 0,
        "qualifying_results": 0,
        "saved_row_hashes": source_rows,
        "source_files": proposal,
        "resources": resources,
        "preflight_import_seconds": time.monotonic() - started,
    }

    def save():
        # Progress snapshots use distinct names; never overwrite prior receipts.
        out.json(
            "progress-" + str(len(list(Path("/receipts").glob("progress-*.json")))) + ".json",
            report,
        )

    counts = {"job_admissions": 0, "read_calls": 0, "read_seconds": 0.0}
    load, read = mapped.loads_fixed_delay_job, host._read

    def counted_load(*args, **kwargs):
        counts["job_admissions"] += 1
        return load(*args, **kwargs)

    def counted_read(*args, **kwargs):
        tick = time.monotonic()
        try:
            return read(*args, **kwargs)
        finally:
            counts["read_calls"] += 1
            counts["read_seconds"] += time.monotonic() - tick

    mapped.loads_fixed_delay_job, host._read = counted_load, counted_read
    session = host.resolution_session

    @contextlib.contextmanager
    def measured_session():
        global SELECT
        tick = time.monotonic()
        with session() as select:
            SELECT = select
            report["common_validation"] = {"seconds": time.monotonic() - tick, **counts}
            require(counts["job_admissions"] == 133, "exact once full corpus admission")
            modes = []

            def measured_select(*, mode):
                before = dict(counts)
                tick = time.monotonic()
                binding = select(mode=mode)
                modes.append(
                    {
                        "mode": mode,
                        "seconds": time.monotonic() - tick,
                        "read_calls": counts["read_calls"] - before["read_calls"],
                        "new_job_admissions": counts["job_admissions"] - before["job_admissions"],
                    }
                )
                return binding

            report["mode_selections"] = modes
            yield measured_select

    host.resolution_session = measured_session
    save()
    setup_start = time.monotonic()
    with grouped.resolve_campaign_hosts(base, context[1], host) as hosts:
        grouped.STATE = base, context, hosts, {}, answers, out
        report["genuine_resolution_seconds"] = time.monotonic() - setup_start
        require(
            counts["job_admissions"] == 133 and len(report["mode_selections"]) == 2,
            "one corpus validation and separate mode selections",
        )
        require(hosts["debug"].executable != hosts["release"].executable, "mode ELFs distinct")
        require(hosts["debug"].record is not hosts["release"].record, "separate returned graph")
        require(
            all(
                hosts["debug"].profiles[k] is not hosts["release"].profiles[k]
                for k in hosts["debug"].profiles
            ),
            "separate profile graphs",
        )
        mapped.loads_fixed_delay_job, host._read = load, read
        diagnostic.STATE = (
            context,
            hosts,
            {k: (v["request"], v["stdout"], v["stderr"], 0) for k, v in samples.items()},
            answers,
        )
        if "--controls-only" not in sys.argv:
            batches = []
            for workers in sorted({1, resources["workers"]}):
                tick = time.monotonic()
                rows = run_workers(
                    cases,
                    diagnostic.check,
                    workers=workers,
                    task_timeout=180,
                    total_timeout=600,
                    executable_paths=tuple(str(h.root / h.executable.path) for h in hosts.values()),
                )
                batches.append(
                    {
                        "workers": workers,
                        "checks": len(rows),
                        "elapsed_seconds": time.monotonic() - tick,
                        "peak_worker_rss_kib": max(r["peak_rss_kib"] for r in rows),
                        "results": rows,
                    }
                )
            require(len(batches) == 2, "actual parallel comparison unavailable")
            fields = ["case", "request_hash", "stdout_hash", "stderr_hash", "status"]
            require(
                [{k: r[k] for k in fields} for r in batches[0]["results"]]
                == [{k: r[k] for k in fields} for r in batches[1]["results"]],
                "serial/parallel byte mismatch",
            )
            report["same_eight_saved_checks"] = batches
            save()
            report["foreign_process_selection"] = run_workers(
                ["foreign-select"], child_selection, workers=1, task_timeout=15, total_timeout=30
            )
            reuse.RUNNER, reuse.HOSTS, reuse.CONTEXT = runner, hosts, context
            reuse.SAMPLES, reuse.ANSWERS = samples, answers
            report["six_operation_groups"] = run_workers(
                ["K01", "K02"],
                reuse.group,
                workers=2,
                task_timeout=180,
                total_timeout=300,
                executable_paths=tuple(str(h.root / h.executable.path) for h in hosts.values()),
            )
            try:
                run_workers(
                    ["K01:final-fault"], reuse.group, workers=1, task_timeout=180, total_timeout=240
                )
            except ValueError as error:
                require("worker failure" in str(error), "expected grouped semantic refusal")
                failed = Path("/receipts/groups/K01:final-fault")
                require(len(list((failed / "calls").glob("*.json"))) == 5, "five checked calls")
                require(len(list((failed / "transport").glob("*.json"))) == 6, "six raw responses")
                report["final_group_fault"] = {"checked": 5, "transport": 6, "completed": False}
            else:
                raise AssertionError("corrupt sixth response accepted")
        else:
            report["unchanged_evidence_reused"] = (
                "evidence/startup-d0.json: same eight timing batches, child PID "
                "and sixth-response fault; "
                "both whole groups repeated on corrected runner"
            )
            reuse.RUNNER, reuse.HOSTS, reuse.CONTEXT = runner, hosts, context
            reuse.SAMPLES, reuse.ANSWERS = samples, answers
            report["six_operation_groups"] = run_workers(
                ["K01", "K02"],
                reuse.group,
                workers=2,
                task_timeout=180,
                total_timeout=300,
                executable_paths=tuple(str(h.root / h.executable.path) for h in hosts.values()),
            )
        from session_boundary_controls import check_bound_reads

        report["bound_read_controls"] = check_bound_reads(host, SELECT, hosts)
        # The existing independent case controls retain their expected refusal type.
        # A wrong exception is recorded as an unresolved control, never a pass.
        try:
            report["case_controls"] = reuse.controls()
            report["case_controls_passed"] = True
        except KeyError as error:
            require(
                str(error) in (repr(k) for k in hosts["debug"].profiles),
                "unexpected control KeyError",
            )
            report["case_controls_passed"] = False
            report["case_control_failure"] = {
                "expected": "ValueError authority drift",
                "actual": repr(error),
                "transport": "not reached for mutation",
            }
        runner._exchange = reuse.exchange
        reuse.FAULT_AT = None
        with runner.admitted_case(
            json.loads(samples["K01"]["request"]), host=hosts["debug"]
        ) as execute:
            execute()
        report["case_control_restored_positive"] = True
        # Returned graph mutation cannot change release or a later selection.
        release_hash = digest(canonical_json(hosts["release"].record).encode())
        profiles = hosts["debug"].profiles.copy()
        hosts["debug"].profiles.clear()
        require(
            digest(canonical_json(hosts["release"].record).encode()) == release_hash,
            "mode graph alias",
        )
        restored_binding = SELECT(mode="debug")
        require(restored_binding.profiles == profiles, "session retained caller mutation")
        hosts["debug"].profiles.update(profiles)
        report["emitted_binding_isolation"] = True
        selector = host._selector_bytes
        host._selector_bytes = lambda: selector() + b"\n"
        try:
            try:
                SELECT(mode="debug")
            except host.HostBindingError as error:
                require(
                    str(error) == "selector changed; fresh resolution session required",
                    "selector refusal",
                )
            else:
                raise AssertionError("changed selector accepted")
        finally:
            host._selector_bytes = selector
        require(
            SELECT(mode="release").executable == hosts["release"].executable, "restored selector"
        )
        report["selector_drift_and_restoration"] = True
        save()
    require(grouped.STATE is None, "parent state released before session closes")
    report["parent_state_released"] = True
    host.resolution_session = session
    try:
        SELECT(mode="debug")
    except host.HostBindingError as error:
        require(
            str(error) == "resolution session expired or belongs to another process",
            "expired selector",
        )
    else:
        raise AssertionError("expired session accepted")
    report["expired_session_refused"] = True
    report["peak_parent_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["origins"] = {
        n: m.__file__
        for n, m in sys.modules.copy().items()
        if n.startswith(("rkuarch", "uarch_contract")) and getattr(m, "__file__", None)
    }
    require(
        all(Path(f).is_relative_to("/proposal") for f in report["origins"].values()),
        "private proposal origins required",
    )
    for name in list(sys.modules):
        if name.startswith(("rkuarch", "uarch_contract")):
            del sys.modules[name]
    sys.modules.update(baseline_modules)
    sys.path[:] = original_path
    base.common()
    report["total_seconds"] = time.monotonic() - started
    report["status"] = (
        "private join passed"
        if report["case_controls_passed"]
        else "startup/scheduling joined; case refusal-type correction pending"
    )
    out.json("startup-join.json", report)


if __name__ == "__main__":
    main()
