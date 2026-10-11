"""Assembly boundary tests; accepted reviews here are explicitly SYNTHETIC scaffolding."""

import copy
import importlib
import shutil
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash, review_subject_hash
from uarch_contract.report_context import MetricDependencies

from rkuarch.provenance.companions import assemble_stub_context
from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from rkuarch.table.build import CapturedWork, build_table, write_table

ROOT = Path(__file__).resolve().parents[2]
ZERO = "sha256:" + "0" * 64


def reviewed(value, field, store):
    """Test-only declaration review. Never an example of production review issuance."""
    value = copy.deepcopy(value)
    review = dict(
        format="uarch-evidence-review/1",
        decision="accepted",
        independent=True,
        reviewer="SYNTHETIC B assembly test",
        rationale="Test scaffolding, no authority.",
        reviewed_subject_hashes=[review_subject_hash(value)],
    )
    review["review_hash"] = content_hash(review)
    store[review["review_hash"]] = review
    value["review_hash"] = review["review_hash"]
    value[field] = content_hash(value, exclude=(field,))
    store[value[field]] = value
    return value


def arguments(v, artifacts=None):
    return dict(
        captured=CapturedWork(v.bundle, v.assumptions, v.request, v.derivation, v.jobs, v.results),
        dependencies=v.dependencies,
        registry=v.registry,
        model_card=v.model_card,
        comparison_hashes=v.context.comparison_hashes,
        artifacts=dict(v.artifacts if artifacts is None else artifacts),
    )


@pytest.fixture(scope="module")
def saved():
    return load_verified_report_inputs(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json")


@pytest.fixture
def inputs(saved):
    return copy.deepcopy(arguments(saved))


def change_deps(inputs, mutate):
    d = inputs["dependencies"].model_dump(mode="json")
    mutate(d)
    inputs["dependencies"] = MetricDependencies.model_validate(
        reviewed(d, "dependencies_hash", inputs["artifacts"])
    )


def test_no_comparison_positive_is_pure_deterministic_and_offline(inputs, tmp_path, monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("assembly/replay called a producer or performed hidden IO")

    before = copy.deepcopy(inputs)
    producer = importlib.import_module("rkuarch.workload.prepare")
    # Assembly receives actual carriers, not an A-loader stand-in.
    with monkeypatch.context() as m:
        m.setattr(Path, "read_bytes", forbidden)
        m.setattr(Path, "read_text", forbidden)
        m.setattr(Path, "write_bytes", forbidden)
        m.setattr(Path, "write_text", forbidden)
        m.setattr(importlib.import_module("rkuarch.table.build"), "capture", forbidden)
        m.setattr(producer, "prepare", forbidden)
        context, store = assemble_stub_context(**inputs)
        again, reordered = assemble_stub_context(
            **dict(inputs, artifacts=dict(reversed(list(inputs["artifacts"].items()))))
        )
    assert inputs == before
    assert context == again and store == reordered and list(store) == sorted(store)
    assert context.evidence_index == {} and context.used_energy_families == ()
    assert context.verification_hashes == () and context.comparison_hashes == ()
    assert dict(inputs["artifacts"].items()).items() <= dict(store).items()
    package = build_table(
        inputs["captured"], context=context, model_card=inputs["model_card"], artifacts=store
    )
    assert verify_report_inputs(package.table, package.artifacts).model_card.badge == "stub"
    assert package.table.comparison_state == "not_attempted"
    for directory in ("fresh", "repeat"):
        write_table(package, tmp_path / directory / "table.json")
    assert (tmp_path / "fresh/table.json").read_bytes() == (
        tmp_path / "repeat/table.json"
    ).read_bytes()
    shutil.copytree(tmp_path / "fresh", tmp_path / "relocated")
    monkeypatch.setattr(importlib.import_module("rkuarch.workload.prepare"), "prepare", forbidden)
    replay = load_verified_report_inputs(tmp_path / "relocated/table.json")
    assert replay.table == package.table
    from rkuarch.report.complete import write_report

    write_report(
        tmp_path / "relocated/table.json",
        html_path=tmp_path / "report.html",
        markdown_path=tmp_path / "report.md",
    )
    assert "STUB" in (tmp_path / "report.html").read_text()
    assert "1.892e-06" not in (tmp_path / "report.md").read_text()
    assert replay.model_card.validated_error_band is None
    assert replay.model_card.energy_verification is None
    write_report(
        tmp_path / "relocated/table.json",
        html_path=tmp_path / "opt-in.html",
        markdown_path=tmp_path / "opt-in.md",
        show_unvalidated_predictions=True,
    )
    assert "STUB" in (tmp_path / "opt-in.md").read_text()
    assert "1.892e-06" in (tmp_path / "opt-in.md").read_text()
    # Returned JSON is detached, not a mutable alias into caller storage.
    key = context.metric_dependencies_hash
    store[key]["version"] = "return-only mutation"
    assert inputs == before


@pytest.mark.parametrize("subject", ["dependencies", "registry"])
@pytest.mark.parametrize(
    "attack",
    ["missing", "pending", "rejected", "not-independent", "wrong-subject", "stale", "unreviewed"],
)
def test_external_review_is_required(inputs, subject, attack):
    value = inputs[subject].model_dump(mode="json")
    field = "dependencies_hash" if subject == "dependencies" else "registry_hash"
    store = inputs["artifacts"]
    if attack == "missing":
        del store[value["review_hash"]]
    elif attack == "stale":
        value["version"] += "/unreviewed-change"
    elif attack == "unreviewed":
        value["review_hash"] = ZERO
    else:
        r = copy.deepcopy(store[value["review_hash"]])
        if attack in ("pending", "rejected"):
            r["decision"] = attack
        elif attack == "not-independent":
            r["independent"] = False
        else:
            r["reviewed_subject_hashes"] = [ZERO]
        r["review_hash"] = content_hash(r, exclude=("review_hash",))
        store[r["review_hash"]] = r
        value["review_hash"] = r["review_hash"]
    value[field] = content_hash(value, exclude=(field,))
    inputs[subject] = type(inputs[subject]).model_validate(value)
    with pytest.raises(ValueError, match="ArtifactMissing|ReviewSubjectMismatch|UnacceptedReview"):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize(
    "attack",
    [
        "unused-json",
        "unused-raw",
        "capture-key",
        "request",
        "model",
        "missing-point",
        "reordered-points",
    ],
)
def test_artifact_and_complete_capture_binding(inputs, attack):
    c = inputs["captured"]
    if attack == "unused-json":
        inputs["artifacts"][ZERO] = {"unused": "bad identity"}
    elif attack == "unused-raw":
        inputs["artifacts"][ZERO] = b"bad raw identity"
    elif attack == "capture-key":
        inputs["artifacts"][c.jobs[0].job_hash] = {"wrong": "job"}
    elif attack == "request":
        inputs["captured"] = c._replace(request=c.request.model_copy(update={"seed": 99}))
    elif attack == "model":
        inputs["captured"] = c._replace(
            assumptions=c.assumptions.model_copy(
                update={"model": c.assumptions.model.model_copy(update={"version": "other"})}
            )
        )
    elif attack == "missing-point":
        inputs["captured"] = c._replace(jobs=c.jobs[:1], results=c.results[:1])
    else:
        inputs["captured"] = c._replace(jobs=c.jobs[::-1], results=c.results[::-1])
    with pytest.raises(
        ValueError, match="ArtifactHashMismatch|CapturedWorkMismatch|ModelCardMismatch"
    ):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize("attack", ["missing", "ambiguous"])
def test_family_refusal(inputs, attack):
    reg = inputs["registry"].model_dump(mode="json")
    if attack == "missing":
        reg["entries"][0]["hardware_spec_hash"] = ZERO
    else:
        reg["entries"].append(dict(reg["entries"][0], family="second"))
    reg = reviewed(reg, "registry_hash", inputs["artifacts"])
    # Deliberately bypass model construction to exercise assembly's revalidation.
    inputs["registry"] = inputs["registry"].model_copy(
        update={
            "entries": tuple(
                type(inputs["registry"].entries[0]).model_validate(e) for e in reg["entries"]
            ),
            "review_hash": reg["review_hash"],
            "registry_hash": reg["registry_hash"],
        }
    )
    with pytest.raises(ValueError, match="AmbiguousFamily"):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize(
    "attack",
    [
        "delete",
        "equal-wrong-source",
        "model",
        "purpose",
        "granularity",
        "dimensions",
        "render-missing",
    ],
)
def test_intrinsic_recipe_scope_refusal(inputs, attack):
    def mutate(d):
        s = d["source_recipes"][0]
        if attack == "delete":
            s["recipe"]["selectors"].pop(0)
        elif attack == "equal-wrong-source":
            sel = s["recipe"]["selectors"][0]
            original = inputs["artifacts"][sel["artifact_hash"]]
            # Generic equal-value container, not a forged declared envelope.
            clone = {"original": original}
            h = content_hash(clone)
            inputs["artifacts"][h] = clone
            sel["artifact_hash"] = h
            sel["json_pointer"] = "/original" + sel["json_pointer"]
        elif attack == "model":
            s["model_identity_hash"] = ZERO
        elif attack == "render-missing":
            d["recipes"].pop(0)
        else:
            s["recipe"][attack if attack != "dimensions" else "applicable_dimensions"] = {
                "purpose": "energy",
                "granularity": "input",
                "dimensions": ["model_identity"],
            }[attack]

    change_deps(inputs, mutate)
    with pytest.raises(ValueError, match="IncompleteMetricContributors|MetricPurposeMismatch"):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize("attack", ["estimated", "band", "energy"])
def test_assembly_refuses_card_promotions(inputs, saved, attack):
    from tests.unit.test_u2_b_stage2_cards import altered

    _, _, card, store = altered(
        (inputs["captured"], saved.context, inputs["model_card"], inputs["artifacts"]), attack
    )
    inputs.update(model_card=card, artifacts=store)
    with pytest.raises(ValueError, match="UnsupportedModelCardAssertion"):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize(
    "declaration",
    [
        "generic",
        "recursive",
        "child-model",
        "child-purpose",
        "child-granularity",
        "child-dimensions",
        "cycle",
    ],
)
def test_reviewed_intrinsic_factoring(inputs, declaration):
    from uarch_contract.hashing import resolve_pointer

    from rkuarch.table.build import table_recipes

    def mutate(d):
        if declaration == "generic":
            recipes, _ = table_recipes(inputs["captured"], generic_rows=True)
            d["recipes"] = [r.model_dump(mode="json") for r in recipes]
        else:
            original = d["source_recipes"][0]
            data = {
                "value": resolve_pointer(
                    inputs["artifacts"][original["artifact_hash"]],
                    original["recipe"]["metric_path"],
                )
            }
            h = content_hash(data)
            inputs["artifacts"][h] = data
            child = copy.deepcopy(original)
            child["artifact_hash"] = h
            child["recipe"]["metric_path"] = "/value"
            if declaration == "child-model":
                child["model_identity_hash"] = ZERO
            elif declaration == "child-purpose":
                child["recipe"]["purpose"] = "energy"
            elif declaration == "child-granularity":
                child["recipe"]["granularity"] = "input"
            elif declaration == "child-dimensions":
                child["recipe"]["applicable_dimensions"] = ["model_identity"]
            elif declaration == "cycle":
                child["recipe"]["selectors"] = [
                    dict(kind="result_field", artifact_hash=h, json_pointer="/value")
                ]
            d["source_recipes"].append(child)
            original["recipe"]["selectors"] = [
                dict(kind="result_field", artifact_hash=h, json_pointer="/value")
            ]

    change_deps(inputs, mutate)
    if declaration not in ("generic", "recursive"):
        with pytest.raises(
            ValueError,
            match=("IncompleteMetricContributors|MetricPurposeMismatch|CyclicMetricRecipe"),
        ):
            assemble_stub_context(**inputs)
        return
    context, store = assemble_stub_context(**inputs)
    package = build_table(
        inputs["captured"], context=context, model_card=inputs["model_card"], artifacts=store
    )
    assert verify_report_inputs(package.table, package.artifacts).model_card.badge == "stub"


def canonical_comparisons(inputs):
    """Test reviewer explicitly reviews canonical indexes; production never repairs them."""
    old = inputs["comparison_hashes"]
    ordered = tuple(sorted(old))

    def mutate(d):
        for recipe in d["recipes"]:
            path = recipe["metric_path"]
            if path.startswith("/comparisons/"):
                parts = path.split("/")
                parts[2] = str(ordered.index(old[int(parts[2])]))
                recipe["metric_path"] = "/".join(parts)

    change_deps(inputs, mutate)
    inputs["comparison_hashes"] = ordered
    return inputs


@pytest.fixture(scope="module")
def selected():
    from tests.integration.test_u2_b_r202_public import selected_package

    v, store, inv, donors = selected_package.__wrapped__()
    return canonical_comparisons(arguments(v, store)), inv, donors


def test_all_supplied_comparisons_and_refusals_survive(selected, tmp_path):
    inputs, _, _ = copy.deepcopy(selected)
    before = copy.deepcopy(inputs)
    context, store = assemble_stub_context(**inputs)
    again, reverse = assemble_stub_context(
        **dict(inputs, comparison_hashes=inputs["comparison_hashes"][::-1])
    )
    assert inputs == before and context == again and store == reverse
    assert context.comparison_hashes == tuple(sorted(inputs["comparison_hashes"]))
    assert all(
        store[k] == v if isinstance(v, bytes) else canonical_json(store[k]) == canonical_json(v)
        for k, v in inputs["artifacts"].items()
    )
    package = build_table(
        inputs["captured"], context=context, model_card=inputs["model_card"], artifacts=store
    )
    write_table(package, tmp_path / "table.json")
    replay = load_verified_report_inputs(tmp_path / "table.json")
    assert len(replay.comparisons) == 2
    for c in replay.comparisons:
        assert c.model_dump(mode="json") == inputs["artifacts"][c.comparison_hash]
        assert c.precision_refusal_observations
        assert c.gate_outcome in ("compatibility_fail", "not_assessed")
    assert replay.model_card.badge == "stub"


@pytest.mark.parametrize("attack", ["omit", "empty", "duplicate", "missing-recipe"])
def test_comparison_intake_cannot_erase_supplied_attempts(selected, attack):
    inputs, _, _ = copy.deepcopy(selected)
    if attack == "missing-recipe":

        def mutate(d):
            target = next(
                r["metric_path"]
                for r in d["recipes"]
                if r["metric_path"].startswith("/comparisons/")
            )
            d["recipes"] = [r for r in d["recipes"] if r["metric_path"] != target]

        change_deps(inputs, mutate)
    else:
        hashes = inputs["comparison_hashes"]
        inputs["comparison_hashes"] = {
            "omit": hashes[:1],
            "empty": (),
            "duplicate": (*hashes, hashes[0]),
        }[attack]
    with pytest.raises(ValueError, match="ComparisonIntakeMismatch|IncompleteMetricContributors"):
        assemble_stub_context(**inputs)


@pytest.mark.parametrize("profile", [0, 1], ids=["retained-.55", "projection-1.0"])
@pytest.mark.parametrize("attack", ["delete", "wrong-source"])
def test_assembly_enforces_r202_original_peak(selected, profile, attack):
    from tests.integration.test_u2_b_r202_public import duration_recipe

    inputs, inv, _ = copy.deepcopy(selected)

    def mutate(d):
        selectors = duration_recipe(d, inv.inventory_hash, profile)["selectors"]
        if attack == "delete":
            del selectors[7]
        else:
            replacement = copy.deepcopy(
                duration_recipe(d, inv.inventory_hash, 1 - profile)["selectors"][7]
            )
            assert replacement["artifact_hash"] != selectors[7]["artifact_hash"]
            selectors[7] = replacement

    change_deps(inputs, mutate)
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        assemble_stub_context(**inputs)


def test_actual_capacity_failure_and_prior_attempts_survive(selected, tmp_path):
    import json

    from uarch_contract.comparison import reduce_outcomes, validate_comparison
    from uarch_contract.hashing import sha256

    from scripts.u2_inputs import Inputs
    from tests import u2_comparison
    from tests.integration.test_u2_b_r202_public import ADOPTED, MANIFEST

    inputs, inv, _ = copy.deepcopy(selected)
    raw_manifest = (ADOPTED / "MANIFEST.json").read_bytes()
    assert sha256(raw_manifest) == MANIFEST
    manifest = json.loads(raw_manifest)
    name = "u2-inputs/model_shapes/llama-3.1-70b.json"
    raw_model = (ADOPTED / name).read_bytes()
    assert sha256(raw_model) == "sha256:" + manifest["files"][name]
    # Ordinary analytic preparation is authorized; no oracle or reference output is generated.
    frozen = Inputs(ADOPTED / "u2-inputs", (), {}, {}, {}, (json.loads(raw_model),), ZERO)
    with pytest.raises(ValueError, match="WeightCapacityExceeded") as failure:
        u2_comparison.prepare_h1(frozen, model_id="llama-3.1-70b", tp=1, compact=True)
    # Current A preparation refuses before returning a bundle; do not counterfeit one.
    fixture = inv.fixtures[1]
    store = inputs["artifacts"]
    store[sha256(raw_model)] = raw_model
    record = dict(
        error=str(failure.value),
        model_input_hash=sha256(raw_model),
        model_id="llama-3.1-70b",
        tp=1,
        compact=True,
        hardware_spec_hash=inputs["captured"].request.hardware_spec_hash,
    )
    rh = content_hash(record)
    store[rh] = record
    original_hash = next(
        h for h in inputs["comparison_hashes"] if store[h]["track"] == "physical_discrepancy"
    )
    comparison = copy.deepcopy(store[original_hash])
    f = comparison["fixtures"][1]
    assert f["fixture_id"] == fixture.fixture_id
    f.update(execution="execution_failed", outcome="execution_failed")
    f["channels"] = [
        u2_comparison.channel(
            n,
            None,
            getattr(fixture.values, n).value,
            rh,
            "/error",
            reference_state=getattr(fixture.values, n).state,
            execution="execution_failed",
        )
        for n in u2_comparison.CHANNELS
    ]
    comparison["evidence_outcome"] = reduce_outcomes(
        tuple(f["outcome"] for f in comparison["fixtures"])
        + tuple(o["evidence_outcome"] for o in comparison["precision_refusal_observations"]),
        artifact=True,
    )
    comparison["limitations"] = [
        "Actual analytic H1 capacity refusal; other workload fixture not run. No hardware data."
    ]
    h = content_hash(comparison, exclude=("comparison_hash",))
    comparison["comparison_hash"] = h
    store[h] = comparison
    validate_comparison(comparison, inv, store)
    # Add this recorded attempt; do not replace or delete either prior comparison.
    old_index = inputs["comparison_hashes"].index(original_hash)
    new_index = len(inputs["comparison_hashes"])

    def mutate(d):
        added = []
        prefix = f"/comparisons/{old_index}/"
        for recipe in d["recipes"]:
            if not recipe["metric_path"].startswith(prefix):
                continue
            r = copy.deepcopy(recipe)
            r["metric_path"] = r["metric_path"].replace(prefix, f"/comparisons/{new_index}/", 1)
            for s in r["selectors"]:
                if s["artifact_hash"] == original_hash:
                    s["artifact_hash"] = h
            added.append(r)
        d["recipes"].extend(added)

    change_deps(inputs, mutate)
    inputs["comparison_hashes"] = (*inputs["comparison_hashes"], h)
    canonical_comparisons(inputs)
    context, retained = assemble_stub_context(**inputs)
    assert retained[rh] == record and retained[original_hash] == store[original_hash]
    assert context.comparison_hashes == tuple(sorted(inputs["comparison_hashes"]))
    package = build_table(
        inputs["captured"], context=context, model_card=inputs["model_card"], artifacts=retained
    )
    write_table(package, tmp_path / "table.json")
    replay = load_verified_report_inputs(tmp_path / "table.json")
    failed = next(c for c in replay.comparisons if c.comparison_hash == h)
    assert failed.model_dump(mode="json") == comparison
    assert failed.fixtures[1].outcome == "execution_failed"
    assert replay.artifacts[rh] == record
    assert len(replay.comparisons) == 3
    inputs["comparison_hashes"] = tuple(x for x in inputs["comparison_hashes"] if x != h)
    with pytest.raises(ValueError, match="ComparisonIntakeMismatch"):
        assemble_stub_context(**inputs)


def test_re_reviewed_subset_cannot_erase_supplied_capacity_failure():
    from tests.u2_a_companion_inputs import actual_capacity_inputs

    inputs, capacity_hash, failure_hash = actual_capacity_inputs()
    full = tuple(sorted(inputs["comparison_hashes"]))
    assert len(full) == 3 and capacity_hash in full
    context, store = assemble_stub_context(**copy.deepcopy(inputs))
    package = build_table(
        inputs["captured"], context=context, model_card=inputs["model_card"], artifacts=store
    )
    verified = verify_report_inputs(package.table, package.artifacts)
    assert tuple(c.comparison_hash for c in verified.comparisons) == full
    assert verified.artifacts[capacity_hash] == inputs["artifacts"][capacity_hash]
    assert verified.artifacts[failure_hash] == inputs["artifacts"][failure_hash]

    attack = copy.deepcopy(inputs)
    subset = tuple(h for h in full if h != capacity_hash)
    new_index = {h: i for i, h in enumerate(subset)}

    def omit_and_reindex(d):
        kept = []
        for recipe in d["recipes"]:
            parts = recipe["metric_path"].split("/")
            if parts[1] == "comparisons":
                identity = full[int(parts[2])]
                if identity == capacity_hash:
                    continue
                parts[2] = str(new_index[identity])
                recipe["metric_path"] = "/".join(parts)
            kept.append(recipe)
        d["recipes"] = kept

    # Explicitly SYNTHETIC re-review and rehash, outside the refusal assertion.
    change_deps(attack, omit_and_reindex)
    attack["comparison_hashes"] = subset
    assert attack["dependencies"].review_hash != inputs["dependencies"].review_hash
    assert attack["artifacts"][capacity_hash] == inputs["artifacts"][capacity_hash]
    assert attack["artifacts"][failure_hash] == inputs["artifacts"][failure_hash]
    assert all(attack["artifacts"][h] == value for h, value in inputs["artifacts"].items())
    with pytest.raises(ValueError, match="ComparisonIntakeMismatch"):
        assemble_stub_context(**attack)
