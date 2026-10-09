"""Synthetic raw proof/review scaffolding around unchanged, actually captured A3 records."""

import base64

from uarch_contract.evidence import VerificationRecord
from uarch_contract.hashing import canonical_json, content_hash, sha256
from uarch_contract.report_context import ReportContext
from uarch_contract.table import UarchCostTable

from rkuarch.table.build import CapturedWork, source_scopes
from tests.fixtures.u2_b.b2_support import put, review


def encoded(members, kind):
    return canonical_json(
        dict(
            format="u2-proof-bundle/2",
            classification="synthetic_fixture",
            kind=kind,
            members=[
                dict(name=n, sha256=sha256(raw), base64=base64.b64encode(raw).decode())
                for n, raw in sorted(members.items())
            ],
        )
    ).encode()


def raw_json(value):
    return canonical_json(value).encode()


def mr(name, raw, source=None):
    return dict(source_record_hash=source, member_name=name, member_sha256=sha256(raw))


def source(store, members, kind, name):
    blob = encoded(members, kind)
    store[sha256(blob)] = blob
    return put(
        store,
        dict(
            format="uarch-reference-source/1",
            independence_from_candidate=True,
            kind="synthetic_fixture",
            limitation="Synthetic proof; no real silicon/source validation.",
            raw_blob_sha256=sha256(blob),
            reference_identity=name,
            reference_version="1",
        ),
        "source_hash",
    )


def verification_fixture(v, mutate=None, outcome="passed", expected="64", extra_members=None):
    """Known q-projection=64 literal; original expected text independently authored here.

    Direct NamedTuple replacement is synthetic test assembly, never an alternate loader.
    The assembly's declared table/context closure is real and separately loader-tested.
    """
    store = dict(v.artifacts)
    job, result = v.jobs[0], v.results[0]
    op = result.per_op[2]
    scopes = source_scopes(
        CapturedWork(v.bundle, v.assumptions, v.request, v.derivation, v.jobs, v.results),
        family=v.registry.entries[0].family,
    )
    scope = scopes[(result.result_hash, "/per_op/2/counts/matrix_ops")][0].model_dump(mode="json")
    model = job.engine.model.model_dump(mode="json")
    mh = content_hash(model)
    original = expected.encode()
    expected_data = dict(
        format="u2-proof-independent-expected/2",
        suite_id="B-captured-q",
        suite_version="1",
        cases=[
            dict(
                case_id="q-count",
                model_input_hash=job.job_hash,
                quantity="matrix_ops",
                source_unit="count",
                value_decimal=expected,
                absolute_tolerance_decimal="0",
                rule="absolute-difference-le-tolerance",
                original_reference=mr("original-expected.txt", original),
            )
        ],
    )
    expected_raw = raw_json(expected_data)
    es = source(
        store,
        {"independent-expected.json": expected_raw, "original-expected.txt": original},
        "capture_support",
        "B-independent-literal-q",
    )
    eref = mr("independent-expected.json", expected_raw, es["source_hash"])
    ref = dict(
        kind="engine_result",
        value=dict(artifact_hash=result.result_hash, json_pointer="/per_op/2/counts/matrix_ops"),
        model_identity_hash=mh,
        input_hash=job.job_hash,
        bundle_hash=job.bundle_hash,
        point_hash=job.point_hash,
        group_id=op.group_id,
        operator_id=op.id,
        quantity="matrix_ops",
        source_unit="count",
    )
    case = dict(
        case_id="q-count",
        benchmark_id="historical-q",
        model_identity_hash=mh,
        input_hash=job.job_hash,
        kind="engine_result",
        metric_pointer=ref["value"]["json_pointer"],
        group_id=op.group_id,
        operator_id=op.id,
        quantity="matrix_ops",
        source_unit="count",
        purpose="counts",
        granularity="operator",
        required_roles=["verification_observed"],
        independent_expected=eref,
    )
    plan = dict(
        format="u2-proof-suite-plan/2", suite_id="B-captured-q", suite_version="1", cases=[case]
    )
    inventory = dict(
        format="u2-proof-capture-inventory/2",
        suite_plan=None,
        cases=[dict(case_id="q-count", benchmark_id="historical-q", capture=ref, outcome=outcome)],
    )
    checks = dict(
        format="u2-proof-checks/1",
        model_identity_hash=mh,
        scope_sha256=sha256(raw_json(scope)),
        purpose="counts",
        family=None,
        rung="L2",
        reference_kind="hand_derived",
        reference_identity=es["reference_identity"],
        reference_version="1",
        candidate_used_for_expected=False,
        cases=[
            dict(
                case_id="q-count",
                operation="identity",
                operands=[expected],
                expected=expected,
                observed="64",
                absolute_tolerance="0",
                unit="count",
            )
        ],
    )
    links = dict(
        format="u2-proof-capture-links/2",
        suite_plan=None,
        capture_inventory=None,
        entries=[
            dict(
                role="verification_observed",
                case_id="q-count",
                benchmark_id="historical-q",
                proof_member="checks.json",
                proof_pointer="/cases/0/observed",
                independent_reference=eref,
            )
        ],
    )
    data = dict(plan=plan, inventory=inventory, checks=checks, links=links)
    if mutate:
        mutate(data)
    plan_raw = raw_json(plan)
    inventory["suite_plan"] = mr("suite-plan.json", plan_raw)
    inv_raw = raw_json(inventory)
    links["suite_plan"] = mr("suite-plan.json", plan_raw)
    links["capture_inventory"] = mr("capture-inventory.json", inv_raw)
    checks_raw = raw_json(checks)
    verification = dict(
        format="u2-proof-verification/1",
        model_identity_hash=mh,
        purpose="counts",
        family=None,
        rung="L2",
        outcome=outcome,
        scope_sha256=sha256(raw_json(scope)),
        source_identity="B-observed-q",
        source_version="1",
        checks_sha256=sha256(checks_raw),
    )
    members = {
        "model.json": raw_json(model),
        "scope.json": raw_json(scope),
        "verification.json": raw_json(verification),
        "checks.json": checks_raw,
        "capture-links.json": raw_json(links),
        "suite-plan.json": plan_raw,
        "capture-inventory.json": inv_raw,
    }
    members.update(extra_members or {})
    observed = source(store, members, "verification", "B-observed-q")
    common = dict(
        format="uarch-verification/1",
        model_identity_hash=mh,
        purpose="counts",
        rung="L2",
        scope=[scope],
    )
    # Independent expected-reference review is a relevant, separate synthetic record.
    ew = review(
        store, dict(**common, outcome="not_run", source_hash=es["source_hash"]), "verification_hash"
    )
    w = review(
        store,
        dict(**common, outcome=outcome, source_hash=observed["source_hash"]),
        "verification_hash",
    )
    context = v.context.model_dump(mode="json")
    context["verification_hashes"] = [w["verification_hash"], ew["verification_hash"]]
    put(store, context, "context_hash")
    table = v.table.model_dump(mode="json")
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    put(store, table, "table_hash")
    from uarch_contract.evidence import ReviewRecord, SourceRecord

    records = [VerificationRecord.model_validate(w), VerificationRecord.model_validate(ew)]
    reviews = tuple(
        ReviewRecord.model_validate(x)
        for x in store.values()
        if isinstance(x, dict) and x.get("format") == "uarch-evidence-review/1"
    )
    return v._replace(
        table=UarchCostTable.model_validate(table),
        context=ReportContext.model_validate(context),
        artifacts=store,
        sources=(SourceRecord.model_validate(observed), SourceRecord.model_validate(es)),
        verifications=tuple(records),
        reviews=reviews,
    ), w["verification_hash"]


def measurement_fixture(v, prediction_value="64"):
    """Typed captured q-count prediction plus unsupported old aggregate CSV scaffold."""
    import json
    from pathlib import Path

    v, wid = verification_fixture(v)
    store = dict(v.artifacts)
    w = next(w for w in v.verifications if w.verification_hash == wid)
    old_source = store[w.source_hash]
    old = json.loads(store[old_source["raw_blob_sha256"]])
    members = {m["name"]: base64.b64decode(m["base64"]) for m in old["members"]}
    root = Path(__file__).resolve().parents[3]
    original = json.loads(
        (
            root / "tests/fixtures/u2_b/proof-inputs/actual-measurement.json"
        ).read_bytes()
    )
    base = {m["name"]: base64.b64decode(m["base64"]) for m in original["members"]}
    base["model.json"] = members["model.json"]
    base["scope.json"] = members["scope.json"]
    plan = json.loads(members["suite-plan.json"])
    case = plan["cases"][0]
    case["required_roles"] = ["prediction"]
    case["independent_expected"] = None
    base["suite-plan.json"] = raw_json(plan)
    inv = json.loads(members["capture-inventory.json"])
    inv["suite_plan"] = mr("suite-plan.json", base["suite-plan.json"])
    base["capture-inventory.json"] = raw_json(inv)
    links = json.loads(members["capture-links.json"])
    links["suite_plan"] = inv["suite_plan"]
    links["capture_inventory"] = mr("capture-inventory.json", base["capture-inventory.json"])
    links["entries"][0].update(
        role="prediction",
        proof_member="prediction.json",
        proof_pointer="/value",
        independent_reference=None,
    )
    base["capture-links.json"] = raw_json(links)
    suite = json.loads(base["suite.json"])
    suite.update(
        benchmark_id="historical-q",
        purpose="counts",
        channel="matrix_ops",
        granularity="operator",
        unit="count",
    )
    base["suite.json"] = raw_json(suite)
    pred = json.loads(base["prediction.json"])
    pred.update(
        benchmark_id="historical-q",
        model_identity_hash=case["model_identity_hash"],
        scope_sha256=sha256(base["scope.json"]),
        source_identity="B-measurement-q",
        source_version="1",
        purpose="counts",
        channel="matrix_ops",
        granularity="operator",
        unit="count",
        value=prediction_value,
        suite_sha256=sha256(base["suite.json"]),
    )
    base["prediction.json"] = raw_json(pred)
    fidelity = json.loads(
        (root / "tests/fixtures/u2_b/proof-inputs/fidelity.json").read_text()
    )
    base["fidelity.json"] = raw_json(fidelity)
    ms = source(store, base, "measurement", "B-measurement-q")
    from uarch_contract.evidence import EvidenceRecord, SourceRecord

    evidence = dict(
        format="uarch-evidence/1",
        evidence_id="synthetic-measurement-q",
        classification="synthetic_fixture",
        channel="matrix_ops",
        energy_family=None,
        error_band=None,
        granularity="operator",
        ordering_hash=None,
        purpose="counts",
        rung="L3",
        scope=[json.loads(base["scope.json"])],
        source_hash=ms["source_hash"],
        verification_hashes=[],
    )
    review(store, evidence, "evidence_hash")
    c = v.context.model_dump(mode="json")
    c["verification_hashes"] = []
    c["evidence_index"] = {evidence["evidence_id"]: evidence["evidence_hash"]}
    put(store, c, "context_hash")
    t = v.table.model_dump(mode="json")
    t["artifacts"]["report_context_hash"] = c["context_hash"]
    put(store, t, "table_hash")
    return (
        v._replace(
            table=UarchCostTable.model_validate(t),
            context=ReportContext.model_validate(c),
            artifacts=store,
            sources=(SourceRecord.model_validate(ms),),
            verifications=(),
            evidence=(EvidenceRecord.model_validate(evidence),),
        ),
        ms["source_hash"],
        store[ms["raw_blob_sha256"]],
    )


def nominal_capture_fixture(v, *, wrong_binding_execution=False, retained=False):
    """Execute A's existing test-only nominal seam with literal tiny input, no oracle."""
    import json
    from pathlib import Path

    from uarch_contract.hashing import artifact_identity
    from uarch_contract.report_context import MetricDependencies

    from contract.tests.nominal_candidate import evaluate_nominal
    from contract.tests.test_u2_nominal_candidate import nominal_input

    root = Path(__file__).resolve().parents[3]
    export = root / "contract/tests/fixtures/u2_b/a2-export"
    store = dict(v.artifacts)
    for path in export.glob("*.json"):
        data = json.loads(path.read_text())
        store[artifact_identity(data)] = data
    binding = json.loads((export / "npu-l4.binding.json").read_text())
    execution = json.loads((export / "npu-l4.execution-model.json").read_text())
    if retained:
        from tests.fixtures.u2_b.b2_support import proposal_artifacts

        originals = proposal_artifacts()
        binding = json.loads(
            (
                root
                / "docs/reviews/U2-U0003-proposal/fixtures"
                / "retained-asic_placeholder.yaml.binding.json"
            ).read_text()
        )
        execution = originals[binding["execution_model_hash"]]
        store[binding["binding_hash"]] = binding
        store[binding["execution_model_hash"]] = execution
    if wrong_binding_execution:
        execution["compute"]["value"] = 0.5
        execution["execution_model_hash"] = content_hash(
            execution, exclude=("execution_model_hash",)
        )
    original = nominal_input(
        component_binding_hash=binding["binding_hash"], execution_model=execution
    )
    result = evaluate_nominal(original)
    store[original.input_hash] = original.model_dump(mode="json")
    store[result.output_hash] = result.model_dump(mode="json")
    selectors = [
        dict(kind=kind, artifact_hash=original.input_hash, json_pointer=ptr)
        for kind, ptr in [
            ("prepared_content", "/model"),
            ("prepared_content", "/query"),
            ("model_assumption", "/execution_model"),
            ("model_evidence", "/model_identity"),
        ]
    ]
    selectors.append(
        dict(
            kind="model_assumption",
            artifact_hash=binding["binding_hash"],
            json_pointer="/execution_model_hash",
        )
    )
    model = content_hash(original.model_identity)
    recipe = dict(
        metric_path="/duration_s",
        purpose="duration",
        granularity="whole_iteration",
        applicable_dimensions=["model_identity_hash"],
        selectors=selectors,
    )
    deps = v.dependencies.model_dump(mode="json")
    deps["source_recipes"].append(
        dict(artifact_hash=result.output_hash, model_identity_hash=model, recipe=recipe)
    )
    deps["recipes"].append(
        dict(
            metric_path="/reference-duration",
            purpose="duration",
            granularity="whole_iteration",
            applicable_dimensions=["model_identity_hash"],
            selectors=[
                dict(
                    kind="result_field",
                    artifact_hash=result.output_hash,
                    json_pointer="/duration_s",
                )
            ],
        )
    )
    review(store, deps, "dependencies_hash")
    context = v.context.model_dump(mode="json")
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    put(store, context, "context_hash")
    table = v.table.model_dump(mode="json")
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    put(store, table, "table_hash")
    ref = dict(
        kind="nominal_output",
        value=dict(artifact_hash=result.output_hash, json_pointer="/duration_s"),
        model_identity_hash=model,
        input_hash=original.input_hash,
        bundle_hash=None,
        point_hash=None,
        group_id=None,
        operator_id=None,
        quantity="duration",
        source_unit="s",
    )
    case = dict(
        case_id="reference-duration",
        benchmark_id="independent-tiny-decode",
        model_identity_hash=model,
        input_hash=original.input_hash,
        kind="nominal_output",
        metric_pointer="/duration_s",
        group_id=None,
        operator_id=None,
        quantity="duration",
        source_unit="s",
        purpose="duration",
        granularity="whole_iteration",
        required_roles=["prediction"],
        independent_expected=None,
    )
    return (
        v._replace(
            table=UarchCostTable.model_validate(table),
            context=ReportContext.model_validate(context),
            dependencies=MetricDependencies.model_validate(deps),
            artifacts=store,
        ),
        ref,
        case,
    )
