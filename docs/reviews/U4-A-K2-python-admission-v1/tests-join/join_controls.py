"""Focused public resolver negatives and B's missing-profile case counterexample."""

import contextlib
import importlib.util
import json
import sys
import time
from pathlib import Path

from checks import outcome, sha

from measure import load_runner


def public_negatives(host):
    spec = importlib.util.spec_from_file_location(
        "rkuarch.engines.native.negative_baseline",
        "/sources/baseline/src/rkuarch/engines/native/host.py",
    )
    baseline = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = baseline
    spec.loader.exec_module(baseline)
    root = Path("/candidate")
    selector = json.loads(Path("/etc/rkuarch/k2-host-selector.json").read_bytes())
    record = json.loads((root / selector["record_path"]).read_bytes())
    trust = json.loads((root / record["trust_file"]["path"]).read_bytes())
    inventory = json.loads((root / record["jobs_inventory"]["path"]).read_bytes())
    targets = [
        selector["record_path"],
        "contract/uarch_contract/hardware.py",
        trust["registry_file"]["path"],
        trust["profiles"][0]["file"]["path"],
        record["jobs_inventory"]["path"],
        inventory["jobs"][0]["file"]["path"],
    ]
    rows = []
    fault = Path("/tmp/public-resolution-fault")
    fault.write_bytes(b"{}")
    for target in targets:
        observed = {}
        for label, module in [("baseline", baseline), ("candidate", host)]:
            original = module._open

            @contextlib.contextmanager
            def fault_open(base, relative, original=original, target=target):
                with original(base, relative) as fd:
                    if relative == target:
                        with fault.open("rb") as stream:
                            yield stream.fileno()
                    else:
                        yield fd

            module._open = fault_open
            try:
                observed[label] = outcome(lambda module=module: module.resolve_host(mode="debug"))
            finally:
                module._open = original
        assert observed["baseline"] == observed["candidate"]
        assert observed["candidate"]["type"] == "HostBindingError"
        assert observed["candidate"]["message"] == "bound file digest mismatch: " + target
        rows.append({"target": target, "outcomes": observed})
    return rows


def missing_profile(host, samples, canonical, Job, checker):
    sample = samples[0]
    rows = []
    start = time.perf_counter()
    with host.resolution_session() as select:
        bound = select(mode="debug")
        startup_seconds = time.perf_counter() - start
        for stage, directory in [
            ("before", "startup"),
            ("corrected", "startup-v2"),
            ("reverted", "peer-reverted"),
            ("restored", "peer-restored"),
        ]:
            source = Path("/sources/variants") / directory / "src/rkuarch/engines/native/runner.py"
            module = load_runner("missing_profile_" + stage, source)
            calls = [0]

            def replay(fd, request, limits, calls=calls):
                calls[0] += 1
                assert request == sample["request"]
                return sample["stdout"], b"", 0

            module._exchange = replay
            with module.admitted_case(json.loads(sample["request"]), host=bound) as execute:
                saved = dict(bound.profiles)
                try:
                    bound.profiles.clear()
                    refusal = outcome(execute)
                finally:
                    bound.profiles.update(saved)
                assert calls[0] == 0
            if stage in ("before", "reverted"):
                assert refusal["type"] == "KeyError"
            else:
                assert refusal["type"] == "ValueError"
                assert refusal["message"] == "case host authority changed; fresh admission required"
            started = time.perf_counter()
            with module.admitted_case(json.loads(sample["request"]), host=bound) as execute:
                for _ in range(3):
                    result, receipt = execute()
                    assert canonical(result).encode() == sample["stdout"]
                    assert receipt == sample["receipt"]
                    checker(result, Job.model_validate_json(sample["request"]), sample["answer"])
            assert calls[0] == 3
            rows.append(
                {
                    "stage": stage,
                    "runner_sha256": sha(source.read_bytes()),
                    "refusal": refusal,
                    "transport_calls_on_refusal": 0,
                    "restored_python_replays": 3,
                    "three_replay_seconds": time.perf_counter() - started,
                }
            )
    assert rows[0]["runner_sha256"] == rows[2]["runner_sha256"]
    assert rows[1]["runner_sha256"] == rows[3]["runner_sha256"]
    return {"startup_seconds": startup_seconds, "controls": rows, "new_native_calls": 0}
