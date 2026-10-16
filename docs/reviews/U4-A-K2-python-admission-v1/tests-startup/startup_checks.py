"""Tests frozen before startup-session implementation; genuine authority only."""

import contextlib
import json
import time
from pathlib import Path

from checks import outcome


def fingerprint(binding):
    return {
        "selector": binding.selector.model_dump(mode="json"),
        "record": binding.record.model_dump(mode="json"),
        "executable": binding.executable.model_dump(mode="json"),
        "root": str(binding.root),
        "profiles": {k: v.model_dump(mode="json") for k, v in binding.profiles.items()},
        "jobs": sorted(binding.jobs),
    }


def session_checks(host, runner, samples, expected, *, faults=True):
    if not hasattr(host, "resolution_session"):
        return {"available": False, "expected_session_available": False}
    from rkuarch.workload import mapped

    load = mapped.loads_fixed_delay_job
    admissions = 0

    def counted(*args, **kwargs):
        nonlocal admissions
        admissions += 1
        return load(*args, **kwargs)

    mapped.loads_fixed_delay_job = counted
    rows = {}
    start = time.perf_counter()
    try:
        with host.resolution_session() as select:
            rows["common_validation_seconds"] = time.perf_counter() - start
            rows["common_job_admissions"] = admissions
            assert admissions == 133
            start = time.perf_counter()
            debug = select(mode="debug")
            release = select(mode="release")
            rows["two_mode_materialization_seconds"] = time.perf_counter() - start
            assert admissions == 133
            assert fingerprint(debug) == expected["debug"]
            assert fingerprint(release) == expected["release"]
            assert debug.executable != release.executable
            assert debug.record is not release.record and debug.selector is not release.selector
            assert all(debug.profiles[k] is not release.profiles[k] for k in debug.profiles)
            # Fault returned mutable models; another mode and later selections remain independent.
            debug.record.expected_engine.__dict__["implementation_hash"] = "sha256:" + "0" * 64
            first = next(iter(debug.profiles))
            debug.profiles[first].__dict__["profile_hash"] = "sha256:" + "0" * 64
            assert fingerprint(release) == expected["release"]
            assert fingerprint(select(mode="debug")) == expected["debug"]
            rows["returned_graph_isolation"] = True
            rows["wrong_mode"] = outcome(lambda: select(mode="DEBUG"))
            assert rows["wrong_mode"]["type"] == "HostBindingError"
            assert rows["wrong_mode"]["message"] == "explicit debug/release mode required"
            pid = host.os.getpid
            try:
                host.os.getpid = lambda: -1
                rows["foreign_process"] = outcome(lambda: select(mode="debug"))
                assert (
                    rows["foreign_process"]["message"]
                    == "resolution session expired or belongs to another process"
                )
            finally:
                host.os.getpid = pid
            selector = host._selector_bytes

            def changed_selector():
                return selector() + b"\n"

            host._selector_bytes = changed_selector
            try:
                rows["changed_selector"] = outcome(lambda: select(mode="debug"))
                assert rows["changed_selector"]["type"] == "HostBindingError"
                assert (
                    rows["changed_selector"]["message"]
                    == "selector changed; fresh resolution session required"
                )
            finally:
                host._selector_bytes = selector
            if faults:
                # Negative read-fault injection only. Original confined path open still runs;
                # _read hashes actual private fault-file bytes against the original trusted hash.
                # No modified selector/record ever produces a capability.
                record = release.record
                root = release.root

                def read(binding):
                    return json.loads((root / binding.path).read_bytes())

                trust = read(record.trust_file)
                build = read(record.build_input_file)
                inventory = read(record.jobs_inventory)
                controls = [
                    ("host_record", release.selector.record_path, b"{}"),
                    ("approval", record.decision.path, b"{}"),
                    ("review", record.independent_review.path, b"{}"),
                    ("trust", record.trust_file.path, b"{}"),
                    ("registry", trust["registry_file"]["path"], b"{}"),
                    ("profile", trust["profiles"][0]["file"]["path"], b"{}"),
                    ("source", build["source_files"][0]["path"], b"changed"),
                    ("corpus", record.corpus_inventory.path, b"{}"),
                    ("job", inventory["jobs"][0]["file"]["path"], b"{}"),
                    (
                        "missing_cases",
                        record.jobs_inventory.path,
                        json.dumps({**inventory, "jobs": inventory["jobs"][1:]}).encode(),
                    ),
                    (
                        "extra_cases",
                        record.jobs_inventory.path,
                        json.dumps(
                            {**inventory, "jobs": inventory["jobs"] + inventory["jobs"][:1]}
                        ).encode(),
                    ),
                    (
                        "debug_receipt_as_release",
                        record.executables[1].build_receipt.path,
                        (root / record.executables[0].build_receipt.path).read_bytes(),
                    ),
                    (
                        "release_binary_as_debug",
                        record.executables[0].executable.path,
                        (root / record.executables[1].executable.path).read_bytes(),
                    ),
                    ("release_binary_change", record.executables[1].executable.path, b"changed"),
                ]
                original_open = host._open
                for name, target, data in controls:
                    fault = Path("/tmp/resolution-fault")
                    fault.write_bytes(data)

                    @contextlib.contextmanager
                    def fault_open(base, relative, target=target, fault=fault):
                        with original_open(base, relative) as fd:
                            if relative == target:
                                with fault.open("rb") as stream:
                                    yield stream.fileno()
                            else:
                                yield fd

                    host._open = fault_open
                    try:
                        observed = outcome(lambda: select(mode="debug"))
                        assert observed["type"] == "HostBindingError", (name, observed)
                        assert observed["message"] == "bound file digest mismatch: " + target
                        rows["changed_" + name] = observed
                    finally:
                        host._open = original_open
                assert fingerprint(select(mode="debug")) == expected["debug"]
                rows["all_faults_restored"] = True
            # Prepare genuine per-case state locally without executing native code.
            start = time.perf_counter()
            with runner.admitted_case(json.loads(samples[0]["request"]), host=release):
                pass
            rows["case_constructor_seconds"] = time.perf_counter() - start
            rows["session_job_admissions_after_modes_and_faults"] = admissions
            assert admissions == 133
        rows["expired"] = outcome(lambda: select(mode="debug"))
        assert rows["expired"]["type"] == "HostBindingError"
        assert (
            rows["expired"]["message"] == "resolution session expired or belongs to another process"
        )
        rows["available"] = rows["expected_session_available"] = True
    finally:
        mapped.loads_fixed_delay_job = load
    return rows
