"""Additional frozen case-lifetime/authority controls; explicit refusal meanings."""

import json
import os
import subprocess
from pathlib import Path

from checks import outcome


def controls(runner, bound, release, samples, canonical, Job, checker):
    sample = samples[0]
    request, output = sample["request"], sample["stdout"]
    rows = {}
    original = runner._exchange

    def replay(fd, data, limits):
        assert data == request
        assert os.fstat(fd).st_size > 0
        return output, b"", 0

    runner._exchange = replay

    def verify(call):
        result, receipt = call()
        assert canonical(result).encode() == output
        assert receipt == sample["receipt"]
        checker(result, Job.model_validate_json(request), sample["answer"])

    def refuse(name, call, kind, message):
        observed = outcome(call)
        assert observed["accepted"] is False, name
        assert observed["type"] == kind, (name, observed)
        assert observed["message"] == message, (name, observed)
        rows[name] = observed

    try:
        raw = json.loads(request)
        with runner.admitted_case(raw, host=bound) as execute:
            raw["engine"]["version"] = "mutated-caller-after-admission"
            verify(execute)
            runner._exchange = lambda *args: (samples[1]["stdout"], b"", 0)
            refuse("second_foreign", execute, "ProtocolViolation", "result validation failed")
            assert rows["second_foreign"]["cause"] == "ResultBindingMismatch: "
            runner._exchange = replay
            verify(execute)
            runner._exchange = lambda *args: (output + b"\n", b"", 0)
            refuse(
                "final_corrupt", execute, "ProtocolViolation", "invalid complete canonical envelope"
            )
            assert rows["final_corrupt"]["cause"] == "noncanonical envelope"
            runner._exchange = replay
            faults = [
                ("registry", bound.record.__dict__, "registry_hash", "sha256:" + "0" * 64),
                ("profile", bound.record.__dict__, "profile_hashes", ()),
                (
                    "engine",
                    bound.record.expected_engine.__dict__,
                    "implementation_hash",
                    "sha256:" + "0" * 64,
                ),
                ("jobs", bound.__dict__, "jobs", frozenset()),
                (
                    "profile_bytes",
                    bound.profiles,
                    json.loads(request)["admission"]["profile_hash"],
                    None,
                ),
                ("mode", bound.__dict__, "executable", release.executable),
                ("root", bound.__dict__, "root", Path("/wrong-root")),
                ("selector", bound.selector.__dict__, "record_byte_hash", "sha256:" + "0" * 64),
            ]
            for name, container, key, value in faults:
                before = container[key]
                kind = "HostBindingError" if name in ("jobs", "profile_bytes") else "ValueError"
                message = (
                    "job outside exact human first-use inventory"
                    if name == "jobs"
                    else "profile bytes changed"
                    if name == "profile_bytes"
                    else "case host authority changed; fresh admission required"
                )
                try:
                    container[key] = value
                    refuse("before_" + name, execute, kind, message)
                finally:
                    container[key] = before

                def fault(fd, data, limits, container=container, key=key, value=value):
                    container[key] = value
                    return replay(fd, data, limits)

                runner._exchange = fault
                try:
                    refuse("during_" + name, execute, kind, message)
                finally:
                    container[key] = before
                    runner._exchange = replay
            refuse(
                "limits",
                lambda: execute(limits=runner.Limits(stdin_bytes=1)),
                "OperationalFailure",
                "StdinLimit",
            )

            # Reentrant invocation cannot share an in-flight context.
            def reentrant(fd, data, limits):
                refuse(
                    "reentrant",
                    execute,
                    "ValueError",
                    "case context requires sequential executions",
                )
                return replay(fd, data, limits)

            runner._exchange = reentrant
            verify(execute)
            runner._exchange = replay
            # New supplied bytes must go through admission; this nested mutation refuses.
            observed = outcome(lambda: runner.encode_request(raw, host=bound))
            from measure import load_runner

            baseline = load_runner(
                "literal_control", "/sources/baseline/src/rkuarch/engines/native/runner.py"
            )
            expected = outcome(lambda: baseline.encode_request(raw, host=bound))
            assert observed == expected
            assert observed["type"] == "ValidationError"
            assert "engine.version" in observed["message"]
            assert "type=literal_error" in observed["message"]
            rows["new_mutated_input"] = observed
            for field, value in [
                ("request", samples[1]["request"]),
                ("host", release),
                ("mode", "release"),
            ]:
                refuse(
                    "argument_" + field,
                    lambda field=field, value=value: execute(**{field: value}),
                    "TypeError",
                    "admitted_case.<locals>.execute() got an unexpected keyword argument '"
                    + field
                    + "'",
                )
            pid = runner.os.getpid
            try:
                runner.os.getpid = lambda: -1
                refuse(
                    "fork_guard",
                    execute,
                    "ValueError",
                    "case context expired or belongs to another process",
                )
            finally:
                runner.os.getpid = pid
            verify(execute)
        refuse(
            "expired", execute, "ValueError", "case context expired or belongs to another process"
        )
        # Independently resolved release context admits, but no missing release output is invented.
        with runner.admitted_case(json.loads(request), host=release):
            rows["release_context_constructed_without_execution"] = True
        refuse(
            "native_guard",
            lambda: subprocess.Popen(["/bin/true"]),
            "RuntimeError",
            "Python diagnostic prohibits process execution",
        )
        rows["restored"] = True
    finally:
        runner._exchange = original
    return rows
