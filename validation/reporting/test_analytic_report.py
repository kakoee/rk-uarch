"""Discriminators for the accepted standalone U0006 boundary, before implementation.

Unit fixtures are explicitly illustrations. Qualifying actual runs require committed
suite code and are exercised separately through generate/validate, never forged here.
"""

from copy import deepcopy
from pathlib import Path

import pytest
from hypothesis import strategies as st
from uarch_contract.hashing import canonical_json, content_hash, strict_json_loads

from rkuarch.engines.analytic.core import run_analytic
from validation.mutants.analytic import mutant
from validation.reporting import analytic_report as report
from validation.strategies import fixed_bundle


@pytest.fixture(scope="module")
def sample():
    plan = report.profile("analytic-l0-smoke")
    discovery = report.discover(plan)
    first = report.replay(discovery, implementation=report.git_head())
    second = report.replay(discovery, implementation=report.git_head())
    return first, second


def validate(value):
    return report.validate_report(
        value,
        expected_plan=value["plan"],
        expected_corpus=value["corpus"],
        expected_implementation=value["implementation_git_commit"],
        allow_illustration=True,
    )


def test_populated_controls_both_modes_and_two_replays(sample):
    first, second = sample
    assert canonical_json(first) == canonical_json(second)
    validate(first)
    assert first["execution_kind"] == "illustration"
    assert first["cases"]["discovery"] and first["cases"]["candidate"]
    for mode in ("aggregate", "per_op"):
        active = [
            r
            for r in first["relations"]
            if f":{mode}:" in r["cell_id"] and r["cell_id"].startswith("analytic.")
        ]
        assert len(active) == 7
        assert all(r["status"] == "pass" and r["actual"]["valid_examples"] == 1 for r in active)
    assert first["reduction"]["outcome"] == "not_run"
    assert first["reduction"]["coverage"] == "partial"
    assert all(m["status"] == "killed" for m in first["mutants"])


def test_public_validation_reuses_only_preparation_within_one_call(monkeypatch, sample):
    original = report.jobs
    calls = []

    def observed(bundle):
        calls.append(canonical_json(report.as_json(bundle)))
        return original(bundle)

    monkeypatch.setattr(report, "jobs", observed)
    validate(sample[0])
    first = list(calls)
    assert first and len(first) == len(set(first))
    validate(sample[0])
    assert calls == first + first  # A second public validation prepares afresh.


def test_fixed_replay_has_no_producer(monkeypatch, sample):
    import rkuarch.workload.prepare as producer

    def forbidden(*args, **kwargs):
        pytest.fail("fixed replay called the standalone producer")

    monkeypatch.setattr(producer, "prepare", forbidden)
    discovery = report.discover(report.profile("analytic-l0-smoke"))
    result = report.replay(discovery, implementation=report.git_head())
    validate(result)
    assert result["reduction"] == sample[0]["reduction"]


def test_catalogue_is_complete_frozen_and_model_v1():
    l0 = report.profile("analytic-l0")
    l0m = report.profile("analytic-l0m")
    assert len(l0["cells"]) == 28
    assert len(l0m["cells"]) == 27
    assert {c["relation_id"] for c in l0["cells"]} >= {
        "L0.executed_mac_conservation/1",
        "L0.dma_conservation/1",
        "L0.little_law/1",
        "L0.energy_conservation/1",
        "analytic.saved_replay/1",
    }
    assert {c["relation_id"] for c in l0m["cells"]} >= {
        "L0m.dram_bound_clock/1",
        "L0m.unused_stipulation/1",
        "producer.decode_batch/1",
        "producer.decode_context/1",
        "analytic.mode_order/1",
    }
    for p in (l0, l0m):
        assert p["modes"] == ["aggregate", "per_op"]
        assert all(c["budget"]["required_valid_examples"] == 24 for c in p["cells"])
        assert "captured-v1-graph-excludes-rope/1" in canonical_json(p)
    with pytest.raises(ValueError, match="profile"):
        report.profile("unregistered-subset")


@pytest.mark.parametrize(
    "attack",
    [
        "missing_case",
        "duplicate_case",
        "missing_object",
        "tamper_result",
        "omit_cell",
        "false_count",
        "unknown_field",
        "boolean_count",
        "invent_internal_count",
        "promote_skip",
        "erase_mutant",
    ],
)
def test_report_refuses_tamper_and_incomplete_closure(sample, attack):
    original = sample[0]
    value = deepcopy(original)
    if attack == "missing_case":
        value["cases"]["candidate"].pop()
    elif attack == "duplicate_case":
        value["cases"]["candidate"].append(value["cases"]["candidate"][0])
    elif attack == "missing_object":
        value["objects"].pop()
    elif attack == "tamper_result":
        next(o for o in value["objects"] if o["kind"] == "result")["value"]["duration_ps"] += 1
    elif attack == "omit_cell":
        value["plan"]["cells"].pop()
        value["suite"]["plan_hash"] = content_hash(value["plan"])
    elif attack == "false_count":
        value["relations"][0]["actual"]["engine_evaluations"]["candidate"] += 1
    elif attack == "unknown_field":
        value["review"] = {"accepted": True}
    elif attack == "boolean_count":
        value["relations"][0]["actual"]["valid_examples"] = True
    elif attack == "invent_internal_count":
        value["relations"][0]["actual"]["internal_rejections"] = 0
    elif attack == "promote_skip":
        next(r for r in value["relations"] if r["status"] == "skip")["status"] = "pass"
    elif attack == "erase_mutant":
        value["mutants"].pop()
    with pytest.raises(ValueError):
        report.validate_report(
            value,
            expected_plan=original["plan"],
            expected_corpus=original["corpus"],
            expected_implementation=original["implementation_git_commit"],
            allow_illustration=True,
        )


def test_rehashed_subset_cannot_replace_caller_pin(sample):
    value = deepcopy(sample[0])
    value["corpus"]["entries"].pop()
    value["plan"]["selection"]["corpus_hash"] = content_hash(value["corpus"])
    value["suite"]["plan_hash"] = content_hash(value["plan"])
    with pytest.raises(ValueError, match="[Cc]orpus|[Pp]lan"):
        report.validate_report(
            value,
            expected_plan=sample[0]["plan"],
            expected_corpus=sample[0]["corpus"],
            expected_implementation=value["implementation_git_commit"],
            allow_illustration=True,
        )


def test_changed_implementation_same_version_refused(sample):
    value = deepcopy(sample[0])
    value["engine"]["implementation_hash"] = "sha256:" + "a" * 64
    with pytest.raises(ValueError, match="[Ii]mplementation|[Ii]dentity|[Ee]ngine"):
        validate(value)
    with pytest.raises(ValueError, match="[Ii]mplementation"):
        report.validate_report(
            sample[0],
            expected_plan=sample[0]["plan"],
            expected_corpus=sample[0]["corpus"],
            expected_implementation="0" * 40,
            allow_illustration=True,
        )


def test_skipped_only_illustration_cannot_become_actual_or_pass(monkeypatch):
    path = Path("docs/reviews/U3-U0006-report-example.json")
    value = strict_json_loads(path.read_text())
    # This frozen design illustration records its author's environment, not this runner's.
    # Isolate the illustration boundary; toolchain drift has its own refusal test below.
    recorded_toolchain = deepcopy(value["toolchain"])
    monkeypatch.setattr(report, "toolchain", lambda: deepcopy(recorded_toolchain))
    assert report.validate_report(
        value,
        expected_plan=value["plan"],
        expected_corpus=value["corpus"],
        expected_implementation=value["implementation_git_commit"],
        allow_illustration=True,
    ) == {
        "coverage": "none",
        "outcome": "not_run",
        "purpose_outcomes": {"diagnostics": "not_run"},
    }
    with pytest.raises(ValueError, match="[Ii]llustration"):
        report.validate_report(
            value,
            expected_plan=value["plan"],
            expected_corpus=value["corpus"],
            expected_implementation=value["implementation_git_commit"],
        )
    promoted = deepcopy(value)
    promoted["reduction"]["outcome"] = "passed"
    with pytest.raises(ValueError, match="Illustration differs"):
        validate(promoted)
    value["execution_kind"] = "actual_suite_run"
    with pytest.raises(ValueError, match="[Ii]llustration|[Aa]ctual"):
        validate(value)


@pytest.mark.parametrize(
    "field", ["python_version", "hypothesis_version", "pytest_version", "uv_lock_sha256"]
)
def test_skipped_illustration_toolchain_drift_is_still_refused(monkeypatch, field):
    value = strict_json_loads(Path("docs/reviews/U3-U0006-report-example.json").read_text())
    observed = deepcopy(value["toolchain"])
    monkeypatch.setattr(report, "toolchain", lambda: observed)
    validate(value)  # Matching environment is a valid control for every mismatch.
    observed[field] = "different-from-recorded"
    with pytest.raises(ValueError, match="^Toolchain identity mismatch$"):
        validate(value)


def test_all_calls_and_errors_are_retained():
    seen = []

    def broken(job):
        seen.append(job.job_hash)
        raise RuntimeError("arbitrary host traceback is operational, not stable content")

    discovery = report.discover(report.profile("analytic-l0-smoke"), engine=broken)
    calls = [call for case in discovery.cases for call in case["calls"]]
    assert len(calls) == len(seen) > 0
    assert all(c["state"] == "error" and c["diagnostic_hash"] for c in calls)
    assert all(c["result_hash"] is None for c in calls)
    result = report.replay(discovery, implementation=report.git_head(), engine=broken)
    assert result["reduction"]["outcome"] == "not_run"
    validate(result)
    assert "arbitrary host" not in canonical_json(result)


def test_discovery_failure_survives_passing_replay():
    discovery = report.discover(
        report.profile("analytic-l0-smoke"), engine=mutant("double_attribution")
    )
    assert any(c["status"] == "fail" for c in discovery.cases)
    result = report.replay(discovery, implementation=report.git_head())
    assert any(c["status"] == "pass" for c in result["cases"]["candidate"])
    assert result["reduction"]["outcome"] == "failed"
    validate(result)


def test_mutant_survivor_and_broken_control_are_not_kills():
    discovery = report.discover(report.profile("analytic-l0-smoke"))
    survived = report.replay(
        discovery, implementation=report.git_head(), mutant_factory=lambda name: run_analytic
    )
    assert all(m["status"] == "survived" for m in survived["mutants"])
    assert survived["reduction"]["outcome"] == "failed"
    validate(survived)

    def crash(job):
        raise RuntimeError("not the target assertion")

    crashed = report.replay(
        discovery, implementation=report.git_head(), mutant_factory=lambda name: crash
    )
    assert all(m["status"] == "not_run" for m in crashed["mutants"])
    validate(crashed)
    broken = report.replay(
        discovery, implementation=report.git_head(), engine=mutant("double_attribution")
    )
    assert any(m["status"] == "control_failed" for m in broken["mutants"])
    assert broken["reduction"]["outcome"] == "failed"
    validate(broken)


def test_caller_pinned_invocation_cap_stops_without_fake_counterexample():
    # A test-only plan is not admitted by the registry as an actual production profile.
    plan = report.profile("analytic-l0-smoke")
    for c in plan["cells"]:
        c["budget"]["max_engine_invocations"] = 1
    discovery = report.discover(plan)
    calls = [
        call for case in discovery.cases for call in case["calls"] if call["state"] != "not_run"
    ]
    for cell in plan["cells"]:
        assert (
            sum(
                len([c for c in case["calls"] if c["state"] != "not_run"])
                for case in discovery.cases
                if case["cell_id"] == cell["cell_id"]
            )
            <= 1
        )
    assert calls and discovery.interrupted
    assert not any(case["status"] == "fail" for case in discovery.cases)


def test_underbudget_distinct_cases_and_unavailable_framework_counts(monkeypatch):
    monkeypatch.setattr(
        report, "hardware_specs", lambda **kwargs: st.just(fixed_bundle("aggregate").hardware_spec)
    )
    plan = report.profile("analytic-l0")
    discovery = report.discover(plan)
    result = report.replay(discovery, implementation=report.git_head())
    active = [r for r in result["relations"] if r["cell_id"].startswith("analytic.")]
    assert all(r["actual"]["valid_examples"] == 1 for r in active)
    assert all(r["status"] == "not_run" for r in active)
    assert all(
        r["actual"]["internal_draws"] is None
        and r["actual"]["internal_rejections"] is None
        and r["actual"]["executed_shrink_calls"] is None
        for r in active
    )
    validate(result)


def test_l0m_producer_path_and_all_five_named_mutants(sample, monkeypatch):
    import rkuarch.workload.prepare as producer

    seen = []
    original = producer.prepare

    def spy(*args, **kwargs):
        seen.append(args[0].analytic_mode)
        return original(*args, **kwargs)

    monkeypatch.setattr(producer, "prepare", spy)
    discovery = report.discover(report.profile("analytic-l0m-smoke"))
    seen.clear()
    result = report.replay(discovery, implementation=report.git_head())
    assert sorted(seen) == ["aggregate"] * 4 + ["per_op"] * 4
    assert all(
        r["status"] == "pass"
        for r in result["relations"]
        if r["cell_id"].startswith(("analytic.", "producer."))
    )
    assert {m["mutant_id"] for m in sample[0]["mutants"] + result["mutants"]} == {
        "off_by_one_matrix",
        "double_attribution",
        "zero_unmodelled_diagnostic",
        "nondeterministic_output",
        "wrong_bandwidth_field",
    }
    assert all(m["status"] == "killed" for m in result["mutants"])
    validate(result)


def test_strict_json_and_cli_require_external_expectations(tmp_path):
    path = tmp_path / "report.json"
    path.write_text('{"format":"a","format":"b"}')
    with pytest.raises(ValueError, match="Duplicate"):
        report.read_json(path)
    with pytest.raises(SystemExit):
        report.main(["validate", "--report", str(path)])


def test_actual_generation_requires_clean_committed_suite(tmp_path, monkeypatch):
    monkeypatch.setattr(
        report,
        "require_committed",
        lambda: (_ for _ in ()).throw(ValueError("Uncommitted implementation")),
    )
    with pytest.raises(ValueError, match="Uncommitted"):
        report.generate("analytic-l0-smoke", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_executed_shrinking_and_reproduction_calls_are_all_retained(monkeypatch):
    from validation.strategies import replace_hardware_leaf

    hardware = fixed_bundle("aggregate").hardware_spec
    monkeypatch.setattr(
        report,
        "hardware_specs",
        lambda **kwargs: st.integers(1_000_000, 1_000_030).map(
            lambda hz: replace_hardware_leaf(hardware, "clock_domains.core.freq_hz", hz)
        ),
    )
    plan = report.profile("analytic-l0")
    plan["cells"] = [
        next(
            c
            for c in plan["cells"]
            if c["cell_id"].startswith("analytic.attribution_sum/1:aggregate:")
        )
    ]
    seen = []
    fault = mutant("double_attribution")

    def conditional(job):
        value = fault(job) if job.hardware.core_freq_hz > 1_000_002 else run_analytic(job)
        seen.append((job.job_hash, value.result_hash))
        return value

    discovery = report.discover(plan, engine=conditional)
    recorded = [
        (call["job_hash"], call["result_hash"])
        for case in discovery.cases
        for call in case["calls"]
        if call["state"] == "completed"
    ]
    assert recorded == seen and len(seen) > 2
    failed_at = next(i for i, c in enumerate(discovery.cases) if c["status"] == "fail")
    assert len(discovery.cases) > failed_at + 1
    assert all(c["stage"] == "discovery" for c in discovery.cases)
    assert discovery.observed[plan["cells"][0]["cell_id"]] == len(discovery.cases)


def test_complete_plan_rejects_boolean_budget_even_with_rehashed_pins(sample):
    value = deepcopy(sample[0])
    value["plan"]["cells"][0]["budget"]["required_valid_examples"] = True
    value["discovery_plan"]["cells"][0]["budget"]["required_valid_examples"] = True
    value["suite"]["plan_hash"] = content_hash(value["plan"])
    with pytest.raises(ValueError, match="[Pp]rofile|[Bb]udget"):
        validate(value)


def test_missing_call_cannot_be_relabelled_an_interruption(sample):
    value = deepcopy(sample[0])
    case = value["cases"]["candidate"][0]
    case["calls"].pop()
    case["results"].pop()
    case.update(status="not_run", reason="ENGINE_ERROR")
    value["execution"].update(state="interrupted", stop_reason="INCOMPLETE_EXECUTION")
    observed = {r["cell_id"]: r["actual"]["observed_body_entries"] for r in value["relations"]}
    value["relations"] = report.relations_from(value["plan"], value["cases"], observed)
    value["reduction"] = report.reduce_report(
        value["plan"], value["relations"], value["mutants"], value["execution"]
    )
    with pytest.raises(ValueError, match="[Mm]issing|[Ii]ncomplete"):
        validate(value)


def test_recording_sink_precedes_call_and_assertion():
    events = []
    recorder = report.Recorder(sink=lambda kind, data: events.append((kind, deepcopy(data))))
    cell = report.profile("analytic-l0-smoke")["cells"][0]

    def spy(job):
        assert events[-1][0] == "call_started"
        assert any(kind == "object" and data["hash"] == job.job_hash for kind, data in events)
        return run_analytic(job)

    case = report.exercise(recorder, cell, [fixed_bundle("aggregate")], "discovery", spy)
    assert case["status"] == "pass"
    assert events[-1][0] == "case_finished"
    assert sum(kind == "call_finished" for kind, _ in events) == 2


def test_registered_domain_and_transformation_are_checked(sample):
    objects = report.Objects(sample[0]["objects"])
    cell = report.profile("analytic-l0-smoke")["cells"][0]
    bundle = fixed_bundle("per_op")
    with pytest.raises(ValueError, match="[Dd]omain|[Mm]ode"):
        report.validate_inputs(cell, [bundle])
    cell = report.profile("analytic-l0m-smoke")["cells"][0]
    bundle = fixed_bundle("aggregate")
    with pytest.raises(ValueError, match="[Tt]ransformation"):
        report.validate_inputs(cell, [bundle, bundle])
    assert objects.values  # populated source object closure, not synthetic empty evidence


def test_memory_response_retains_control_premises(monkeypatch):
    discovery = report.discover(report.profile("analytic-l0m-smoke"))
    result = report.replay(discovery, implementation=report.git_head())
    cases = {c["case_id"]: c for c in result["cases"]["mutant"]}
    for m in result["mutants"]:
        for control_id, fault_id in zip(m["control_case_ids"], m["mutant_case_ids"], strict=True):
            assert cases[control_id]["premise_results"][0]["observation_pointers"]
            assert cases[fault_id]["premise_results"] == cases[control_id]["premise_results"]
    validate(result)


def test_producer_counterexample_before_engine_is_retained(monkeypatch):
    import rkuarch.workload.prepare as producer

    discovery = report.discover(report.profile("analytic-l0m-smoke"))
    original = producer.prepare

    def wrong_seed(intent, hardware):
        return original(intent.model_copy(update={"seed": intent.seed + 1}), hardware)

    monkeypatch.setattr(producer, "prepare", wrong_seed)
    result = report.replay(discovery, implementation=report.git_head())
    failed = [c for c in result["cases"]["candidate"] if c["cell_id"].startswith("producer.")]
    assert len(failed) == 4 and all(c["status"] == "fail" and not c["calls"] for c in failed)
    assert all(c["failure_fingerprint"]["observed"]["producer_outputs"] for c in failed)
    assert result["reduction"]["outcome"] == "failed"
    validate(result)


def test_malformed_result_is_retained_as_error_not_mutant_kill():
    def stale(job):
        value = run_analytic(job).model_dump(mode="json")
        value["result_hash"] = "sha256:" + "0" * 64
        return value

    discovery = report.discover(report.profile("analytic-l0-smoke"), engine=stale)
    result = report.replay(discovery, implementation=report.git_head())
    calls = [call for case in result["cases"]["discovery"] for call in case["calls"]]
    assert calls and all(c["state"] == "error" and c["diagnostic_hash"] for c in calls)
    assert result["reduction"]["outcome"] == "not_run"
    validate(result)


def test_unrelated_artifacts_are_refused(sample):
    value = deepcopy(sample[0])
    objects = report.Objects(value["objects"])
    objects.add("diagnostic", {"unrelated": "not report evidence"})
    value["objects"] = objects.export()
    with pytest.raises(ValueError, match="[Uu]nreferenced"):
        validate(value)


def test_reused_mutable_result_preserves_every_returned_value():
    from uarch_contract.hashing import verify_identity

    shared = {}

    def reusing(job):
        shared.clear()
        shared.update(run_analytic(job).model_dump(mode="json"))
        return shared

    recorder = report.Recorder()
    cell = report.profile("analytic-l0-smoke")["cells"][0]
    case = report.exercise(recorder, cell, [fixed_bundle("aggregate")], "discovery", reusing)
    assert case["status"] == "pass"
    assert len(case["results"]) == 2 and case["results"][0] != case["results"][1]
    for identity in case["results"]:
        assert verify_identity(recorder.objects.get(identity), "result_hash") == identity


def test_git_binding_ignores_prose_but_refuses_changed_code_same_version(tmp_path, monkeypatch):
    import subprocess

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    source = tmp_path / "src"
    source.mkdir()
    code = source / "engine.py"
    code.write_text('VERSION = "1"\nVALUE = 1\n')
    prose = source / "README.md"
    prose.write_text("Original explanation\n")
    git("add", ".")
    git(
        "-c",
        "user.name=Report binding fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "test fixture",
    )
    commit = git("rev-parse", "HEAD")
    monkeypatch.setattr(report, "ROOT", tmp_path)
    prose.write_text("Clarified explanation; implementation unchanged\n")
    report.check_implementation(commit)
    code.write_text('VERSION = "1"\nVALUE = 2\n')
    with pytest.raises(ValueError, match="Implementation bytes changed"):
        report.check_implementation(commit)


@pytest.mark.parametrize(
    "output",
    [
        {},
        {"duration_ps": float("nan")},
        {"duration_ps": float("inf")},
        {"duration_ps": -float("inf")},
        object(),
        {"nested": [object(), float("nan")]},
    ],
    ids=["json-control", "nan", "positive-infinity", "negative-infinity", "object", "nested"],
)
def test_invalid_return_full_retention_and_public_validation(output):
    import base64

    events = []

    def sink(kind, value):
        events.append((kind, deepcopy(value)))

    def invalid(job):
        return output

    discovery = report.discover(report.profile("analytic-l0-smoke"), engine=invalid, sink=sink)
    expected_corpus = report.corpus_from(discovery.cases)
    expected_plan = report.frozen_plan(discovery)
    implementation = report.git_head()
    result = report.replay(
        discovery,
        implementation=implementation,
        engine=invalid,
        mutant_factory=lambda name: invalid,
        sink=sink,
    )
    assert (
        report.validate_report(
            result,
            expected_plan=expected_plan,
            expected_corpus=expected_corpus,
            expected_implementation=implementation,
            allow_illustration=True,
        )["outcome"]
        == "not_run"
    )
    calls = [call for cases in result["cases"].values() for case in cases for call in case["calls"]]
    assert calls and all(c["state"] == "error" and c["diagnostic_hash"] for c in calls)
    assert all(c["result_hash"] is None for c in calls)
    assert sum(k == "call_started" for k, _ in events) == len(calls)
    assert sum(k == "call_finished" for k, _ in events) == len(calls)
    assert all(c["status"] == "not_run" for cases in result["cases"].values() for c in cases)
    assert all(r["actual"]["valid_examples"] == 0 for r in result["relations"])
    assert all(m["status"] == "not_run" for m in result["mutants"])
    objects = report.Objects(result["objects"])
    diagnostics = [
        strict_json_loads(base64.b64decode(objects.get(c["diagnostic_hash"]))) for c in calls
    ]
    assert all(d["code"] == "INVALID_ENGINE_OUTPUT" for d in diagnostics)
    if output == {}:
        assert all(d == {"code": "INVALID_ENGINE_OUTPUT", "output": {}} for d in diagnostics)
    else:
        assert all(
            d["output_representation"]["format"] == "invalid-engine-output/1" for d in diagnostics
        )
        assert "0x" not in canonical_json(diagnostics)
    # A healthy replay cannot hide the discovery errors or admit their examples.
    recovered = report.replay(discovery, implementation=implementation)
    assert (
        report.validate_report(
            recovered,
            expected_plan=expected_plan,
            expected_corpus=expected_corpus,
            expected_implementation=implementation,
            allow_illustration=True,
        )["outcome"]
        == "not_run"
    )


def test_invalid_output_diagnostic_is_deterministic_and_explicit():
    import base64

    class Opaque:
        def __repr__(self):
            raise AssertionError("Never format an opaque return with repr")

    class BrokenSerializer(Opaque):
        def model_dump(self, **kwargs):
            raise RuntimeError("serializer failed at host-specific address")

    def capture(value):
        recorder = report.Recorder()
        cell = report.profile("analytic-l0-smoke")["cells"][0]
        case = report.exercise(
            recorder, cell, [fixed_bundle("aggregate")], "discovery", lambda job: value
        )
        assert case["status"] == "not_run" and case["reason"] == "ENGINE_ERROR"
        call = case["calls"][0]
        diagnostic = base64.b64decode(recorder.objects.get(call["diagnostic_hash"]))
        return strict_json_loads(diagnostic)

    cycle = []
    cycle.append(cycle)
    for output in [cycle, BrokenSerializer()]:
        first = capture(output)
        assert canonical_json(first) == canonical_json(capture(output))
        assert first["code"] == "INVALID_ENGINE_OUTPUT"
        assert first["output_representation"]["format"] == "invalid-engine-output/1"
    assert capture(Opaque()) == capture(Opaque())
    projection = capture({"ok": [7, "text"], "bad": float("nan")})["output_representation"]
    assert projection["value"]["type"] == "builtins.dict"
    entries = projection["value"]["items"]
    assert any(
        k["value"] == "bad"
        and v == {"type": "builtins.float", "encoding": "nonfinite", "value": "nan"}
        for k, v in entries
    )
    assert any(k["value"] == "ok" and v["items"][0]["value"] == 7 for k, v in entries)
    assert capture({}) == {"code": "INVALID_ENGINE_OUTPUT", "output": {}}
