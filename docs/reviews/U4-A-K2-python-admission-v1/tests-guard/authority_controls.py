"""Frozen compatibility control: malformed nested engine anchor during transport."""

from pathlib import Path

from checks import outcome

from measure import load_runner


def authority_controls(candidate, bound, samples):
    baseline = load_runner(
        "authority_baseline", "/sources/baseline/src/rkuarch/engines/native/runner.py"
    )
    sample = samples[0]
    path = Path("/tmp/authority-request.json")
    path.write_bytes(sample["request"])
    original_engine = bound.record.expected_engine
    rows = []
    for label, value in [
        ("null", None),
        ("dict", original_engine.model_dump(mode="json")),
        ("object", object()),
    ]:
        outcomes = {}
        for name, module in [("baseline", baseline), ("candidate", candidate)]:
            original = module._exchange

            def replay(fd, request, limits, value=value):
                assert request == sample["request"]
                bound.record.__dict__["expected_engine"] = value
                return sample["stdout"], b"", 0

            module._exchange = replay
            try:
                observed = outcome(lambda module=module: module.run_fixed_delay(path, host=bound))
                outcomes[name] = observed
            finally:
                module._exchange = original
                bound.record.__dict__["expected_engine"] = original_engine
        assert outcomes["baseline"]["type"] == "ValueError"
        assert outcomes["baseline"]["message"] == "EngineIdentityMismatch: "
        rows.append(
            {
                "control": label,
                "outcomes": outcomes,
                "equivalent": outcomes["baseline"] == outcomes["candidate"],
            }
        )
    return rows
