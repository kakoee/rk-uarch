"""Semantic expectations authored before U2 production code; no producer/oracle calls."""

import json
from pathlib import Path

import pytest
from uarch_contract.comparison import validate_channel, validate_comparison
from uarch_contract.hashing import artifact_identity
from uarch_contract.report_context import validate_metric_dependencies

PROPOSAL = Path(__file__).resolve().parents[2] / "docs/reviews/U2-U0003-proposal/fixtures"


def read(name):
    return json.loads((PROPOSAL / name).read_text())


def artifacts():
    result = {}
    for path in (*PROPOSAL.glob("*.json"), *PROPOSAL.parent.glob("*.json")):
        value = json.loads(path.read_text())
        if isinstance(value, dict):
            result[artifact_identity(value)] = value
    return result


@pytest.mark.parametrize(
    "case", read("r1-semantic-cases.json")["cases"], ids=lambda c: c["case_id"]
)
def test_r1_observed_correspondence_and_reductions(case):
    store = artifacts()
    for trace in case["additional_synthetic_traces"]:
        store[artifact_identity(trace)] = trace
    expected = case["expected"]
    if expected["validation_refusal"]:
        with pytest.raises(ValueError, match=expected["validation_refusal"]):
            validate_comparison(case["comparison"], case["inventory"], store)
    else:
        value = validate_comparison(case["comparison"], case["inventory"], store)
        assert value.evidence_outcome == expected["artifact_evidence"]
        assert value.gate_outcome == expected["physical_gate"]


@pytest.mark.parametrize("case", read("r1-channels.json")["cases"], ids=lambda c: c["case_id"])
def test_r1_zero_null_absent(case):
    verdict, obligation = validate_channel(
        case["channel"], declared_omission=case["case_id"] == "nominal-omission"
    )
    assert verdict == case["expected"]["outcome"]
    assert obligation == (case["expected"]["gate_obligation"] != "failed")


def test_r2_timing_inherits_original_stub_and_separate_models():
    leaves = validate_metric_dependencies(read("metric-dependencies.json"), artifacts())
    counts = leaves["/comparisons/0/fixtures/0/channels/0/raw_rel"]
    timing = leaves["/comparisons/0/fixtures/0/channels/4/raw_rel"]
    assert not any(s.kind == "hardware_leaf" for s in counts)
    assert any(s.json_pointer == "/memory/dram/bw_bytes_per_s" for s in timing)
    assert len({s.artifact_hash for s in timing if s.kind == "model_evidence"}) == 2
    assert "/comparisons/0/fixtures/0/channels/4/actual/value" not in leaves


@pytest.mark.parametrize("case", read("r2-semantic-cases.json")["cases"], ids=lambda c: c["id"])
def test_r2_discriminating_negative_closures(case):
    from uarch_contract.hashing import content_hash, resolve_pointer, review_subject_hash

    value = read(case["base"])
    store = artifacts()
    for edit in case["edits"]:
        parent, token = edit["path"].rsplit("/", 1)
        target = resolve_pointer(value, parent)
        if isinstance(target, list):
            if edit["op"] == "remove":
                target.pop(int(token))
            elif token == "-":
                target.append(edit["value"])
            else:
                target[int(token)] = edit["value"]
        else:
            target[token] = edit["value"]
    if case["review_action"] == "rebind_synthetic":
        review = dict(store[value["review_hash"]])
        review["reviewed_subject_hashes"] = [review_subject_hash(value)]
        review["review_hash"] = content_hash(review, exclude=("review_hash",))
        value["review_hash"] = review["review_hash"]
        store[review["review_hash"]] = review
    value["dependencies_hash"] = content_hash(value, exclude=("dependencies_hash",))
    with pytest.raises(ValueError, match=case["expected_refusal"]):
        validate_metric_dependencies(value, store)


def test_evidence_severity_and_precision_gate_are_independent():
    from uarch_contract.comparison import (
        ComparisonArtifact,
        ReferenceInventory,
        reduce_outcomes,
        validate_precision_observations,
    )

    assert reduce_outcomes(("passed",), artifact=True) == "complete_pass"
    assert reduce_outcomes(("modelled_absence", "passed")) == "unassessed"
    assert reduce_outcomes(("refused", "unassessed")) == "refused"
    assert reduce_outcomes(("failed", "refused")) == "failed"
    assert reduce_outcomes(("execution_failed", "failed")) == "execution_failed"
    for case in read("r1-semantic-cases.json")["cases"]:
        if case["expected"]["validation_refusal"]:
            continue
        store = artifacts()
        for trace in case["additional_synthetic_traces"]:
            store[artifact_identity(trace)] = trace
        comparison = ComparisonArtifact.model_validate(case["comparison"])
        passed, recorded = validate_precision_observations(
            ReferenceInventory.model_validate(case["inventory"]),
            comparison.precision_refusal_observations,
            store,
        )
        assert passed == (
            case["expected"]["nominal_gate_on_isolated_otherwise_passing_inventory"]
            == "compatibility_pass"
        )
        assert recorded == (case["expected"]["physical_gate"] == "discrepancy_record_complete")


def test_arithmetic_failure_is_data_but_adjustment_policy_refuses():
    from copy import deepcopy

    channel = read("comparison-physical.json")["fixtures"][0]["channels"][0]
    assert validate_channel(channel) == ("failed", False)
    forged = deepcopy(channel)
    forged["outcome"] = "passed"
    with pytest.raises(ValueError, match="ComparisonOutcomeMismatch"):
        validate_channel(forged)
    forged = deepcopy(channel)
    forged["declared_deviations"] = [
        {"id": str(i), "deviation_rel": 0.046, "reason": "cannot remove discrepancy"}
        for i in range(4)
    ]
    forged["signed_adjustment_rel"] = forged["absolute_adjustment_rel"] = 0.184
    with pytest.raises(ValueError, match="ComparisonPolicyViolation"):
        validate_channel(forged)


def test_table_row_and_transitive_binding_refuse_rehashed_conversion_error():
    from uarch_contract.hashing import content_hash
    from uarch_contract.table import validate_table_bindings

    table = read("table.json")
    validate_table_bindings(table, artifacts())
    table["rows"][0]["duration_s"] *= 1000
    for key in table["rows"][0]["attribution_s"]:
        table["rows"][0]["attribution_s"][key] *= 1000
    table["table_hash"] = content_hash(table, exclude=("table_hash",))
    with pytest.raises(ValueError, match="captured result/conversion"):
        validate_table_bindings(table, artifacts())


def test_report_context_joins_exact_channel_index_to_metric_purpose():
    from uarch_contract.hashing import content_hash, review_subject_hash
    from uarch_contract.report_context import validate_report_context

    context = read("r2-semantic-context.json")
    store = artifacts()
    validate_report_context(context, store)
    deps = read("metric-dependencies.json")
    recipe = next(
        r
        for r in deps["recipes"]
        if r["metric_path"] == "/comparisons/0/fixtures/0/channels/4/raw_rel"
    )
    recipe["purpose"] = "counts"
    review = dict(store[deps["review_hash"]])
    review["reviewed_subject_hashes"] = [review_subject_hash(deps)]
    review["review_hash"] = content_hash(review, exclude=("review_hash",))
    deps["review_hash"] = review["review_hash"]
    deps["dependencies_hash"] = content_hash(deps, exclude=("dependencies_hash",))
    store[review["review_hash"]], store[deps["dependencies_hash"]] = review, deps
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    context["context_hash"] = content_hash(context, exclude=("context_hash",))
    with pytest.raises(ValueError, match="MetricPurposeMismatch"):
        validate_report_context(context, store)


# A1-C1/C2 correction regressions. These mutate captured synthetic literals only;
# no producer, nominal callable, oracle or renderer supplies any expectation.
def correction_rebind(context, deps, store):
    from copy import deepcopy

    from uarch_contract.hashing import content_hash, review_subject_hash

    review = deepcopy(store[deps["review_hash"]])
    review["reviewed_subject_hashes"] = [review_subject_hash(deps)]
    review["review_hash"] = content_hash(review, exclude=("review_hash",))
    deps["review_hash"] = review["review_hash"]
    deps["dependencies_hash"] = content_hash(deps, exclude=("dependencies_hash",))
    store[review["review_hash"]] = review
    store[deps["dependencies_hash"]] = deps
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    context["context_hash"] = content_hash(context, exclude=("context_hash",))


@pytest.mark.parametrize("boundary", ["context", "dependencies"])
@pytest.mark.parametrize(
    "mutation",
    [
        "missing_reference",
        "different_reference_channel",
        "equal_reference_fixture",
        "equal_substitute_inventory",
        "missing_actual",
        "missing_adjustment",
        "wrong_adjustment_pointer",
    ],
)
def test_c1_ratio_requires_exact_sources_after_fresh_review(boundary, mutation):
    from copy import deepcopy

    from uarch_contract.hashing import content_hash
    from uarch_contract.report_context import validate_report_context

    context, deps, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    validate_report_context(context, store)
    # Equal duration literals in different reference fixtures intentionally discriminate identity.
    duration = mutation in (
        "missing_reference",
        "equal_reference_fixture",
        "equal_substitute_inventory",
    )
    index = 4 if duration else 0
    path = f"/comparisons/0/fixtures/0/channels/{index}/raw_rel"
    recipe = next(r for r in deps["recipes"] if r["metric_path"] == path)
    actual, reference, adjustment = recipe["selectors"]
    if mutation in ("missing_adjustment", "wrong_adjustment_pointer"):
        comparison = read("comparison-physical.json")
        old_hash = comparison["comparison_hash"]
        channel = comparison["fixtures"][0]["channels"][0]
        channel["declared_deviations"] = [
            {
                "id": "synthetic-count-adjustment",
                "deviation_rel": 0.01,
                "reason": "Independent source-binding test only.",
            }
        ]
        channel["signed_adjustment_rel"] = channel["absolute_adjustment_rel"] = 0.01
        channel["residual_rel"] = 0.184 - 0.01
        comparison["comparison_hash"] = content_hash(comparison, exclude=("comparison_hash",))
        store[comparison["comparison_hash"]] = comparison
        context["comparison_hashes"][0] = comparison["comparison_hash"]
        for r in deps["recipes"]:
            for selector in r["selectors"]:
                if selector["artifact_hash"] == old_hash:
                    selector["artifact_hash"] = comparison["comparison_hash"]
        correction_rebind(context, deps, store)
        validate_report_context(context, store)  # Nonempty declarations are a valid control.
    if mutation == "missing_reference":
        recipe["selectors"].remove(reference)
    elif mutation == "different_reference_channel":
        reference["json_pointer"] = "/fixtures/0/values/memory_read_bytes/value"
    elif mutation == "equal_reference_fixture":
        inv = read("comparison-inventory.json")
        assert (
            inv["fixtures"][0]["values"]["duration_s"] == inv["fixtures"][1]["values"]["duration_s"]
        )
        reference["json_pointer"] = "/fixtures/1/values/duration_s/value"
    elif mutation == "equal_substitute_inventory":
        inv = read("comparison-inventory.json")
        old_hash = inv["inventory_hash"]
        inv["oracle_manifest_sha256"] = "sha256:" + "9" * 64
        inv["inventory_hash"] = content_hash(inv, exclude=("inventory_hash",))
        store[inv["inventory_hash"]] = inv
        source = deepcopy(
            next(
                s
                for s in deps["source_recipes"]
                if s["artifact_hash"] == old_hash
                and s["recipe"]["metric_path"] == reference["json_pointer"]
            )
        )
        source["artifact_hash"] = inv["inventory_hash"]
        deps["source_recipes"].append(source)
        reference["artifact_hash"] = inv["inventory_hash"]
    elif mutation == "missing_actual":
        recipe["selectors"].remove(actual)
    elif mutation == "missing_adjustment":
        recipe["selectors"].remove(adjustment)
    else:
        adjustment["json_pointer"] = "/fixtures/0/channels/1/declared_deviations"
    correction_rebind(context, deps, store)
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        if boundary == "context":
            validate_report_context(context, store)
        else:
            validate_metric_dependencies(deps, store)


def correction_refresh_comparison(comparison, store):
    """Independent arithmetic for these adjustment-free synthetic known-value cases."""
    from uarch_contract.hashing import content_hash, resolve_pointer

    for fixture in comparison["fixtures"]:
        if fixture["execution"] != "executed":
            continue
        for channel in fixture["channels"]:
            actual = channel["actual"]
            if actual["state"] != "known":
                continue
            value = resolve_pointer(store[actual["source_hash"]], actual["source_pointer"])
            actual["value"] = value / 1e12 if actual["conversion"] == "ps_to_seconds" else value
            reference = channel["reference"]["value"]
            if reference is None:
                channel["outcome"], channel["raw_rel"], channel["residual_rel"] = (
                    "unassessed",
                    None,
                    None,
                )
            elif reference == 0:
                channel["outcome"] = "passed" if actual["value"] == 0 else "failed"
                channel["raw_rel"] = channel["residual_rel"] = None
            else:
                raw = (actual["value"] - reference) / reference
                channel["raw_rel"] = channel["residual_rel"] = raw
                channel["outcome"] = (
                    "passed"
                    if abs(raw) <= (0.001 if channel["channel"] == "duration_s" else 0.005)
                    else "failed"
                )
    comparison["comparison_hash"] = content_hash(comparison, exclude=("comparison_hash",))


def correction_comparison(track):
    from copy import deepcopy

    from uarch_contract.hashing import content_hash

    c, inv, store = read("comparison-physical.json"), read("comparison-inventory.json"), artifacts()
    if track == "nominal_compatibility":
        # Use accepted hand-authored nominal literals, not a generated candidate result.
        source_input = read("nominal-decode-input.json")
        output = read("nominal-decode-output.expected.json")
        c["track"], c["reference_basis"] = track, "nominal_aggregate_divided_by_tp"
        c["candidate"] = deepcopy(output["model_identity"])
        c["gate_outcome"] = "compatibility_fail"
        c["fixtures"], inv["fixtures"] = c["fixtures"][:1], inv["fixtures"][:1]
        fixture = c["fixtures"][0]
        for key in ("query", "precision", "tp", "component_binding_hash"):
            fixture[key] = inv["fixtures"][0][key] = deepcopy(source_input[key])
        fixture["bundle_hash"] = fixture["job_hash"] = fixture["result_hash"] = None
        fixture["candidate_input_hash"], fixture["candidate_output_hash"] = (
            source_input["input_hash"],
            output["output_hash"],
        )
        for channel in fixture["channels"]:
            actual = channel["actual"]
            if channel["channel"] in ("vector_ops", "memory_write_bytes"):
                actual.update(
                    state="unmodelled",
                    value=None,
                    source_hash=None,
                    source_pointer=None,
                    conversion="identity",
                )
                channel["outcome"] = "modelled_absence"
            else:
                actual["source_hash"] = output["output_hash"]
                actual["conversion"] = "identity"
                actual["source_pointer"] = (
                    "/duration_s"
                    if channel["channel"] == "duration_s"
                    else "/counts/" + channel["channel"]
                )
        inv["inventory_hash"] = content_hash(inv, exclude=("inventory_hash",))
        c["reference_inventory_hash"] = inv["inventory_hash"]
        correction_refresh_comparison(c, store)
    validate_comparison(c, inv, store)
    return c, inv, store


@pytest.mark.parametrize("track", ["physical_discrepancy", "nominal_compatibility"])
@pytest.mark.parametrize("equal", [False, True])
def test_c2_wrong_count_field_refuses_even_when_values_equal(track, equal):
    from copy import deepcopy

    from uarch_contract.hashing import content_hash

    c, inv, store = correction_comparison(track)
    channel = c["fixtures"][0]["channels"][0]
    assert channel["channel"] == "matrix_ops"
    old_hash = channel["actual"]["source_hash"]
    output = deepcopy(store[old_hash])
    wrong_field = "vector_ops" if track == "physical_discrepancy" else "memory_read_bytes"
    if equal:
        # Independently chosen equal-value capture isolates semantic pointer identity.
        output["counts"][wrong_field] = output["counts"]["matrix_ops"]
        field = "result_hash" if track == "physical_discrepancy" else "output_hash"
        output[field] = content_hash(output, exclude=(field,))
        store[output[field]] = output
        for fixture in c["fixtures"]:
            if fixture["execution"] != "executed":
                continue
            fixture[
                "result_hash" if track == "physical_discrepancy" else "candidate_output_hash"
            ] = output[field]
            for other in fixture["channels"]:
                if other["actual"]["source_hash"] == old_hash:
                    other["actual"]["source_hash"] = output[field]
        correction_refresh_comparison(c, store)
        validate_comparison(c, inv, store)  # Correct pointers still pass with equality.
    channel["actual"]["source_pointer"] = "/counts/" + wrong_field
    correction_refresh_comparison(c, store)
    assert channel["outcome"] == "failed"  # This was never a pass-laundering test.
    with pytest.raises(ValueError, match="RefusalSourceMismatch"):
        validate_comparison(c, inv, store)


@pytest.mark.parametrize(
    "track,index,pointer,conversion",
    [
        ("physical_discrepancy", 0, "/attribution_ps/compute", "identity"),
        ("physical_discrepancy", 4, "/u_c0_duration_ps", "ps_to_seconds"),
        ("physical_discrepancy", 4, "/duration_ps", "identity"),
        ("physical_discrepancy", 4, "/counts/matrix_ops", "ps_to_seconds"),
        ("nominal_compatibility", 4, "/duration_s", "ps_to_seconds"),
        ("nominal_compatibility", 4, "/counts/matrix_ops", "identity"),
        ("physical_discrepancy", 0, "/counts/matrix_ops", "ps_to_seconds"),
        ("nominal_compatibility", 0, "/counts/matrix_ops", "ps_to_seconds"),
    ],
)
def test_c2_unrelated_fields_and_duration_conversions(track, index, pointer, conversion):
    c, inv, store = correction_comparison(track)
    channel = c["fixtures"][0]["channels"][index]
    channel["actual"]["source_pointer"], channel["actual"]["conversion"] = pointer, conversion
    correction_refresh_comparison(c, store)
    with pytest.raises(ValueError, match="RefusalSourceMismatch"):
        validate_comparison(c, inv, store)


def test_correction_unmodified_valid_controls_keep_numeric_failures_and_both_models():
    from uarch_contract.report_context import validate_report_context

    for track in ("physical_discrepancy", "nominal_compatibility"):
        c, inv, store = correction_comparison(track)
        result = validate_comparison(c, inv, store)
        assert result.evidence_outcome == "failed"
        assert result.gate_outcome == (
            "compatibility_fail"
            if track == "nominal_compatibility"
            else "discrepancy_record_complete"
        )
    context, store = read("r2-semantic-context.json"), artifacts()
    validate_report_context(context, store)
    leaves = validate_metric_dependencies(read("metric-dependencies.json"), store)
    assert (
        len(
            {
                s.artifact_hash
                for s in leaves["/comparisons/0/fixtures/0/channels/4/raw_rel"]
                if s.kind == "model_evidence"
            }
        )
        == 2
    )


@pytest.mark.parametrize(
    "ratio", ["residual_rel", "signed_adjustment_rel", "absolute_adjustment_rel"]
)
@pytest.mark.parametrize("index", [0, 4])
def test_c1_reference_required_for_residual_and_bookkeeping_zero(ratio, index):
    from uarch_contract.report_context import validate_report_context

    context, deps, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    recipe = next(
        r
        for r in deps["recipes"]
        if r["metric_path"] == f"/comparisons/0/fixtures/0/channels/{index}/{ratio}"
    )
    recipe["selectors"].pop(1)
    correction_rebind(context, deps, store)
    for validator, value in (
        (validate_report_context, context),
        (validate_metric_dependencies, deps),
    ):
        with pytest.raises(ValueError, match="IncompleteMetricContributors"):
            validator(value, store)


def test_c1_equal_comparison_substitution_cannot_replace_context_binding():
    from uarch_contract.hashing import content_hash
    from uarch_contract.report_context import validate_report_context

    context, deps, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    clone = read("comparison-physical.json")
    clone["limitations"].append("A separate synthetic comparison, with identical numbers.")
    clone["comparison_hash"] = content_hash(clone, exclude=("comparison_hash",))
    store[clone["comparison_hash"]] = clone
    recipe = next(
        r
        for r in deps["recipes"]
        if r["metric_path"] == "/comparisons/0/fixtures/0/channels/4/raw_rel"
    )
    recipe["selectors"][2]["artifact_hash"] = clone["comparison_hash"]
    correction_rebind(context, deps, store)
    # Standalone closure names a consistent clone; the context identifies
    # which comparison is actually displayed.
    validate_metric_dependencies(deps, store)
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        validate_report_context(context, store)


def test_c1_recursive_sources_retain_both_models_and_original_timing_inputs():
    from copy import deepcopy

    from uarch_contract.report_context import validate_report_context

    context, deps, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    recipe = next(
        r
        for r in deps["recipes"]
        if r["metric_path"] == "/comparisons/0/fixtures/0/channels/4/raw_rel"
    )
    actual = deepcopy(recipe["selectors"][0])
    source = deepcopy(
        next(
            s
            for s in deps["source_recipes"]
            if s["artifact_hash"] == actual["artifact_hash"]
            and s["recipe"]["metric_path"] == actual["json_pointer"]
        )
    )
    source["recipe"]["metric_path"] = "/u_c0_duration_ps"
    source["recipe"]["selectors"] = [actual]
    deps["source_recipes"].append(source)
    recipe["selectors"][0]["json_pointer"] = "/u_c0_duration_ps"
    correction_rebind(context, deps, store)
    validate_report_context(context, store)
    leaves = validate_metric_dependencies(deps, store)[recipe["metric_path"]]
    assert len({s.artifact_hash for s in leaves if s.kind == "model_evidence"}) == 2
    bandwidth = next(s for s in leaves if s.json_pointer == "/memory/dram/bw_bytes_per_s")
    assert (
        store[bandwidth.artifact_hash]["memory"]["dram"]["bw_bytes_per_s"]["provenance"] == "stub"
    )


def test_c1_reference_fixture_join_uses_id_not_positional_coincidence():
    from uarch_contract.hashing import content_hash
    from uarch_contract.report_context import validate_report_context

    context, deps, store = (
        read("r2-semantic-context.json"),
        read("metric-dependencies.json"),
        artifacts(),
    )
    comparison, inventory = read("comparison-physical.json"), read("comparison-inventory.json")
    old_inventory, old_comparison = inventory["inventory_hash"], comparison["comparison_hash"]
    inventory["fixtures"][0], inventory["fixtures"][1] = (
        inventory["fixtures"][1],
        inventory["fixtures"][0],
    )
    inventory["inventory_hash"] = content_hash(inventory, exclude=("inventory_hash",))
    comparison["reference_inventory_hash"] = inventory["inventory_hash"]
    comparison["comparison_hash"] = content_hash(comparison, exclude=("comparison_hash",))
    store[inventory["inventory_hash"]], store[comparison["comparison_hash"]] = inventory, comparison
    context["comparison_hashes"][0] = comparison["comparison_hash"]

    def pointer(path):
        if path.startswith("/fixtures/0/"):
            return path.replace("/fixtures/0/", "/fixtures/1/", 1)
        if path.startswith("/fixtures/1/"):
            return path.replace("/fixtures/1/", "/fixtures/0/", 1)
        return path

    for source in deps["source_recipes"]:
        if source["artifact_hash"] == old_inventory:
            source["artifact_hash"] = inventory["inventory_hash"]
            source["recipe"]["metric_path"] = pointer(source["recipe"]["metric_path"])
    for recipe in [*deps["recipes"], *(s["recipe"] for s in deps["source_recipes"])]:
        for selector in recipe["selectors"]:
            if selector["artifact_hash"] == old_inventory:
                selector["artifact_hash"] = inventory["inventory_hash"]
                selector["json_pointer"] = pointer(selector["json_pointer"])
            elif selector["artifact_hash"] == old_comparison:
                selector["artifact_hash"] = comparison["comparison_hash"]
    correction_rebind(context, deps, store)
    assert validate_comparison(comparison, inventory, store).evidence_outcome == "failed"
    validate_report_context(context, store)
