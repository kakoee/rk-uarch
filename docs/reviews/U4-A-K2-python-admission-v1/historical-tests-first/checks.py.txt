"""Frozen Python-only saved-evidence regressions. No native execution permitted."""

import copy
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def outcome(fn):
    try:
        value = fn()
        return {"accepted": True, "value": value}
    except Exception as error:
        cause = error.__cause__
        return {
            "accepted": False,
            "type": type(error).__name__,
            "message": str(error),
            "cause_type": type(cause).__name__ if cause else None,
            "cause": str(cause) if cause else None,
        }


def rule_checks(hardware):
    original = dict(hardware.HARDWARE_UNIT_RULES)

    def reference(path):
        for pattern, allowed in hardware.HARDWARE_UNIT_RULES.items():
            expression = re.escape(pattern).replace(r"\[\]", r"\[\d+\]").replace(r"\*", ".+")
            if re.fullmatch(expression, path):
                return allowed
        raise ValueError(f"{path}: no explicit HardwareSpec unit rule.")

    paths = [None, b"cores[0].clock", "", "unmatched", "a.x", "a."]
    for pattern in original:
        for index in ["0", "01", "١", "-1", ""]:
            for wildcard in ["x", "x.y", "", "\n"]:
                path = pattern.replace("[]", "[" + index + "]").replace("*", wildcard)
                paths += [path, path + ".unknown"]
    n = 0
    schema = hardware.HardwareSpec.model_json_schema()
    try:
        for mapping in [
            original,
            {"a.*": ("first",), "a.x": ("second",)},
            {"a.x": ("second",), "a.*": ("changed",)},
            {f"churn{i}.*": ("u",) for i in range(160)},
            original,
        ]:
            hardware.HARDWARE_UNIT_RULES.clear()
            hardware.HARDWARE_UNIT_RULES.update(mapping)
            for path in paths + [f"churn{i}.x" for i in range(160)]:
                assert outcome(lambda: hardware.hardware_unit_rule(path)) == outcome(
                    lambda: reference(path)
                )
                n += 1
    finally:
        hardware.HARDWARE_UNIT_RULES.clear()
        hardware.HARDWARE_UNIT_RULES.update(original)
    assert hardware.HardwareSpec.model_json_schema() == schema
    pattern = next(iter(original))
    path = pattern.replace("[]", "[0]").replace("*", "x")
    hardware.hardware_unit_rule(path)
    escape = re.escape
    count = 0

    def counted(x):
        nonlocal count
        count += 1
        return escape(x)

    re.escape = counted
    try:
        hardware.hardware_unit_rule(path)
    finally:
        re.escape = escape
    cache = getattr(hardware, "_compiled_hardware_unit_rule", None)
    if cache:
        assert cache.cache_info().currsize <= 128
    return {
        "equivalence_checks": n,
        "schema_hash": sha(json.dumps(schema, sort_keys=True).encode()),
        "warm_escape_calls": count,
        "optimized_expectation_pass": count == 0,
    }


def runner_checks(runner, host, samples, canonical, Job, checker, *, case_api):
    sample = samples[0]
    request, output, answer = sample["request"], sample["stdout"], sample["answer"]
    raw = json.loads(request)
    path = Path("/tmp/test-request.json")
    path.write_bytes(request)
    rows = {}
    original_exchange = runner._exchange
    original_load = runner.loads_fixed_delay_job
    loads = 0

    def counted(*args, **kwargs):
        nonlocal loads
        loads += 1
        return original_load(*args, **kwargs)

    def replay(fd, data, limits):
        assert os.fstat(fd).st_size > 0
        assert data == request
        if len(data) > limits.stdin_bytes:
            raise runner.OperationalFailure("StdinLimit")
        return output, b"", 0

    runner._exchange = replay
    runner.loads_fixed_delay_job = counted

    def parse(out=output, err=b"", status=0, req=request):
        return runner.parse_response(out, err, status, request_bytes=req, host=host)

    def record(name, fn):
        rows[name] = outcome(fn)
        return rows[name]

    def checked_result(result):
        assert canonical(result).encode() == output
        checker(result, Job.model_validate_json(request), answer)
        return sha(output)

    try:
        loads = 0
        assert runner.encode_request(raw, host=host) == request
        rows["encode_admissions"] = loads
        loads = 0
        checked_result(parse())
        rows["standalone_admissions"] = loads
        loads = 0
        result, receipt = runner.run_fixed_delay(path, host=host)
        checked_result(result)
        assert receipt == sample["receipt"]
        rows["run_admissions"] = loads
        rows["reuse_expectations_pass"] = (
            rows["standalone_admissions"] == rows["run_admissions"] == 1
        )
        record("noncanonical_request", lambda: parse(req=request + b"\n"))
        record("malformed_request", lambda: parse(req=b"{"))
        for name, out, err, status in [
            ("missing", b"", b"", 0),
            ("duplicate_stream", output * 2, b"", 0),
            ("noncanonical_output", output + b"\n", b"", 0),
            ("stderr_on_success", output, b"x", 0),
            ("exit_one", output, b"", 1),
            ("signal", b"", b"", -9),
            ("foreign_status", output, b"", 3),
            ("duplicate_key", b'{"x":0,"x":1}', b"", 0),
            ("foreign_result", samples[1]["stdout"], b"", 0),
            (
                "semantic_refusal",
                b"",
                b'{"code":"TimeOverflow","message":"control","pointer":null}',
                2,
            ),
        ]:
            record(
                name,
                lambda out=out, err=err, status=status: checked_result(parse(out, err, status)),
            )
            assert not rows[name]["accepted"]
        from uarch_contract.hashing import content_hash

        stale = json.loads(output)
        stale["engine"]["implementation_hash"] = "sha256:" + "0" * 64
        stale["result_hash"] = content_hash(stale, exclude=("result_hash",))
        record("rehashed_stale_engine", lambda: parse(canonical(stale).encode()))
        # Exact nested mutation, including model_copy: no instance identity shortcut.
        typed = Job.model_validate_json(request)
        typed.engine.__dict__["implementation_hash"] = "sha256:" + "0" * 64
        for name, value in [
            ("nested_model", typed),
            ("model_copy", typed.model_copy()),
            ("nested_raw", typed.model_dump(mode="json")),
        ]:
            record(name, lambda value=value: runner.encode_request(value, host=host))
            assert not rows[name]["accepted"]
        # Genuine resolved capability faulted only in this private process; restored always.
        faults = [
            ("registry", host.record.__dict__, "registry_hash", "sha256:" + "0" * 64),
            ("profile", host.record.__dict__, "profile_hashes", ()),
            (
                "engine",
                host.record.expected_engine.__dict__,
                "implementation_hash",
                "sha256:" + "0" * 64,
            ),
            ("jobs", host.__dict__, "jobs", frozenset()),
            ("profile_bytes", host.profiles, raw["admission"]["profile_hash"], None),
        ]
        for name, container, key, value in faults:
            before = container[key]
            try:
                container[key] = value
                record("host_" + name, lambda: runner.encode_request(raw, host=host))
                record("standalone_host_" + name, lambda: parse())
                assert not rows["host_" + name]["accepted"]
            finally:
                container[key] = before

            def mutate(fd, data, limits, container=container, key=key, value=value):
                container[key] = value
                return replay(fd, data, limits)

            runner._exchange = mutate
            try:
                record("midcall_" + name, lambda: runner.run_fixed_delay(path, host=host))
                assert not rows["midcall_" + name]["accepted"]
            finally:
                container[key] = before
                runner._exchange = replay
        record(
            "stdin_limit",
            lambda: runner.run_fixed_delay(path, host=host, limits=runner.Limits(stdin_bytes=1)),
        )
        assert not rows["stdin_limit"]["accepted"]

        # Path changed during exchange affects only the next public invocation.
        def rewrite(fd, data, limits):
            path.write_bytes(b"{}")
            return replay(fd, data, limits)

        runner._exchange = rewrite
        checked_result(runner.run_fixed_delay(path, host=host)[0])
        record("changed_path_next_call", lambda: runner.run_fixed_delay(path, host=host))
        assert not rows["changed_path_next_call"]["accepted"]
        path.write_bytes(request)
        runner._exchange = replay
        if case_api:
            if not hasattr(runner, "admitted_case"):
                rows["case_api"] = {"available": False, "expectation_pass": False}
            else:
                case_rows = {}
                loads = 0
                caller = json.loads(request)
                with runner.admitted_case(caller, host=host) as execute:
                    caller.clear()
                    for i in range(3):
                        checked_result(execute()[0])
                    case_rows["three_calls_admissions"] = loads
                    assert loads == 1
                    # Later corrupt result cannot be laundered by a prior success.
                    runner._exchange = lambda *args: (samples[1]["stdout"], b"", 0)
                    case_rows["second_foreign"] = outcome(execute)
                    runner._exchange = lambda *args: (output + b"\n", b"", 0)
                    case_rows["final_corrupt"] = outcome(execute)
                    runner._exchange = replay
                    case_rows["changed_bytes_argument"] = outcome(lambda: execute(request=b"{}"))
                    case_rows["different_host_argument"] = outcome(lambda: execute(host=host))
                    case_rows["different_mode_argument"] = outcome(lambda: execute(mode="release"))
                    for name, container, key, value in faults:
                        before = container[key]
                        try:
                            container[key] = value
                            case_rows["changed_" + name] = outcome(execute)
                        finally:
                            container[key] = before
                    before = host.__dict__["executable"]
                    try:
                        other = next(
                            x.executable for x in host.record.executables if x.executable != before
                        )
                        host.__dict__["executable"] = other
                        case_rows["wrong_mode_binding"] = outcome(execute)
                    finally:
                        host.__dict__["executable"] = before
                    pid = runner.os.getpid
                    try:
                        runner.os.getpid = lambda: -1
                        case_rows["forked_context"] = outcome(execute)
                    finally:
                        runner.os.getpid = pid
                    checked_result(execute()[0])
                    case_rows["limits"] = outcome(
                        lambda: execute(limits=runner.Limits(stdin_bytes=1))
                    )
                case_rows["expired"] = outcome(execute)
                for key, value in case_rows.items():
                    if isinstance(value, dict):
                        assert not value["accepted"], key
                case_rows["available"] = case_rows["expectation_pass"] = True
                rows["case_api"] = case_rows
        checked_result(parse())
        rows["restored"] = True
    finally:
        runner._exchange = original_exchange
        runner.loads_fixed_delay_job = original_load
    return rows
