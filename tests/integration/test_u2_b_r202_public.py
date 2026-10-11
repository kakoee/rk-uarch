"""R202 public-loader regressions over a bounded, genuine adopted-oracle selection.

Only administrative dependency reviews are synthetic. Raw oracle members are read
from the committed adopted snapshot and authenticated, never generated. Saved A3
capture supplies the actual table; no preparation, engine or external review output.
"""

import copy
import json
from pathlib import Path

import pytest
import yaml
from uarch_contract.comparison import ReferenceInventory, reduce_outcomes, validate_comparison
from uarch_contract.errors import IncompleteMetricContributors
from uarch_contract.exports import ComponentPrecision
from uarch_contract.hashing import (
    artifact_identity,
    canonical_json,
    content_hash,
    resolve_pointer,
    review_subject_hash,
    sha256,
    verify_declared_artifact_closure,
    verify_review,
)
from uarch_contract.table import UarchCostTable

from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from rkuarch.table.build import CapturedWork
from scripts.u2_inputs import Inputs, role
from tests import u2_comparison, u2_refresh

ROOT = Path(__file__).resolve().parents[2]
ADOPTED = ROOT / "contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963"
MANIFEST = "sha256:20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad"
PRIOR_MANIFEST = "sha256:f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e"
PROFILES = ("retained-.55", "projection-1.0")
CATEGORIES = (
    "model",
    "shape",
    "query",
    "precision",
    "tp",
    "reference-model-assumption",
    "reference-model-evidence",
    "original-peak",
    "bandwidth",
    "execution-efficiency",
)


def put(store, value, field):
    value[field] = content_hash(value, exclude=(field,))
    store[value[field]] = value
    return value


def rebind(table, context, dependencies, store):
    """Re-review the EXACT changed subject and rehash every parent, never bless a hash drift."""
    review = put(
        store,
        dict(
            format="uarch-evidence-review/1",
            reviewer="SYNTHETIC R202 regression scaffolding",
            independent=True,
            decision="accepted",
            rationale="Adversarial declaration only; no source authority or accuracy approval.",
            reviewed_subject_hashes=[review_subject_hash(dependencies)],
        ),
        "review_hash",
    )
    dependencies["review_hash"] = review["review_hash"]
    put(store, dependencies, "dependencies_hash")
    verify_review(dependencies, store)
    context = dict(context, metric_dependencies_hash=dependencies["dependencies_hash"])
    put(store, context, "context_hash")
    data = table.model_dump(mode="json")
    data["artifacts"].update(
        report_context_hash=context["context_hash"], comparison_hashes=context["comparison_hashes"]
    )
    put(store, data, "table_hash")
    # An independent structural preflight, followed by the FULL production boundary in tests.
    verify_declared_artifact_closure(data["table_hash"], store)
    return UarchCostTable.model_validate(data), store


def write_package(directory, table, store):
    """Serialize all companions verbatim/canonically; no verifier or symlink bypass."""
    art = directory / "artifacts"
    art.mkdir(parents=True)
    for identity, value in store.items():
        (art / (identity[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else canonical_json(value).encode()
        )
    path = directory / "table.json"
    path.write_text(canonical_json(table))
    return path


@pytest.fixture(scope="module")
def selected_package():
    raw_manifest = (ADOPTED / "MANIFEST.json").read_bytes()
    assert sha256(raw_manifest) == MANIFEST
    manifest = json.loads(raw_manifest)

    def member(name):
        raw = (ADOPTED / name).read_bytes()
        assert sha256(raw) == "sha256:" + manifest["files"][name], name
        return raw

    # Offline historical input carriers, not a current-source input-staging run.
    # Never call load_inputs(check_support=False), a producer or an oracle generator.
    artifacts = {}
    for name in manifest["files"]:
        if name.startswith("u2-inputs/artifacts/"):
            value = json.loads(member(name))
            artifacts[artifact_identity(value)] = value
    entries = tuple(
        ComponentPrecision.model_validate(v)
        for v in json.loads(member("u2-inputs/component-precisions.json"))
    )
    descriptors = {e.component_id: member("components/" + role(e)) for e in entries}
    for e in entries:
        artifacts[e.binding.binding_hash] = e.binding.model_dump(mode="json")
    hardware_bytes = (ROOT / "hw/designs/npu-l4.yaml").read_bytes()
    frozen_support = json.loads(member("u2-inputs/support-files.json"))
    assert sha256(hardware_bytes) == "sha256:" + frozen_support["hw/designs/npu-l4.yaml"]
    hardware = yaml.safe_load(hardware_bytes)
    artifacts[content_hash(hardware)] = hardware
    assert any(
        e.binding.kind == "uarch_projection"
        and e.binding.hardware_spec_hash == content_hash(hardware)
        for e in entries
    )
    inputs = Inputs(
        ADOPTED / "u2-inputs",
        entries,
        descriptors,
        artifacts,
        {},
        (),
        sha256(member("u2-inputs/SHA256SUMS")),
    )
    store = dict(artifacts)
    store[MANIFEST] = raw_manifest
    historical = member("u2-inputs/historical-source/MANIFEST.json")
    store[sha256(historical)] = historical
    raw_rows = member("parity/fixtures.json")
    store[sha256(raw_rows)] = raw_rows  # Full original raw member is REQUIRED for a selection.
    rows = json.loads(raw_rows)
    original = json.loads(
        (ROOT / "tests/fixtures/u2_b/stage2/reference-inventory.json").read_text()
    )
    assert original["oracle_manifest_sha256"] == PRIOR_MANIFEST
    metadata = json.loads(member("GENERATOR.json"))
    assert original["reference_model"]["implementation_hash"] == (
        "sha256:" + metadata["oracle_program_sha256"]
    )
    pointer, expected, observations = u2_refresh.precision_records(
        inputs,
        member("parity/refusals.json"),
        member("rk/engine/f0/compute.py"),
        store,
        synthetic=False,
    )
    assert [e.model_dump(mode="json") for e in expected] == original["refusals"]
    assert pointer == original["refusal_inventory_source"]
    inventory = copy.deepcopy(original)
    # Bind this new selection to the exact adopted v3 bytes; retain the v2 fixture.
    inventory["oracle_manifest_sha256"] = MANIFEST
    inventory["fixtures"] = [inventory["fixtures"][i] for i in (0, 864)]
    put(store, inventory, "inventory_hash")
    inv = ReferenceInventory.model_validate(inventory)
    assert inv.classification == "adopted_oracle"
    selected_rows = [rows[i] for i in (0, 864)]
    for profile, row, fixture in zip(PROFILES, selected_rows, inv.fixtures, strict=True):
        assert row["id"] == fixture.fixture_id
        assert row["component_params_file"] == (
            "components/asic_placeholder.yaml"
            if profile == "retained-.55"
            else "components/npu-l4.yaml"
        )
        assert sha256(member(row["component_params_file"])) == (
            "sha256:" + row["component_params_sha256"]
        )
        binding = store[fixture.component_binding_hash]
        assert store[binding["execution_model_hash"]]["compute"]["value"] == (
            0.55 if profile == "retained-.55" else 1.0
        )
        store[artifact_identity(row)] = row
    # Keep the real saved actual source independent of both reference profiles.
    saved = load_verified_report_inputs(ROOT / "tests/fixtures/u2_b/a3-proof-capture/table.json")
    captured = CapturedWork(
        saved.bundle, saved.assumptions, saved.request, saved.derivation, saved.jobs, saved.results
    )
    comparisons = {}
    for name, track, model in (
        ("nominal", "nominal_compatibility", u2_comparison.nominal.candidate_identity()),
        ("physical", "physical_discrepancy", captured.assumptions.model),
    ):
        fixtures = []
        for f in inv.fixtures:
            common = f.model_dump(mode="json", exclude={"values"})
            fixtures.append(
                dict(
                    common,
                    execution="not_run",
                    outcome="unassessed",
                    bundle_hash=None,
                    job_hash=None,
                    result_hash=None,
                    candidate_input_hash=None,
                    candidate_output_hash=None,
                    channels=[
                        u2_comparison.channel(
                            n,
                            None,
                            getattr(f.values, n).value,
                            None,
                            "",
                            reference_state=getattr(f.values, n).state,
                            execution="not_run",
                        )
                        for n in u2_comparison.CHANNELS
                    ],
                )
            )
        comp = put(
            store,
            dict(
                format="uarch-comparison/1",
                classification="executed_comparison",
                candidate=model.model_dump(mode="json"),
                reference_model=inventory["reference_model"],
                reference_inventory_hash=inv.inventory_hash,
                track=track,
                reference_basis="nominal_aggregate_divided_by_tp"
                if name == "nominal"
                else "physical_vs_nominal_rank_projection",
                fixtures=fixtures,
                precision_refusal_observations=[o.model_dump(mode="json") for o in observations],
                evidence_outcome=reduce_outcomes(
                    ("unassessed", *(o.evidence_outcome for o in observations)), artifact=True
                ),
                gate_outcome="compatibility_fail" if name == "nominal" else "not_assessed",
                limitations=["Selected adopted inputs; comparison runs not executed."],
            ),
            "comparison_hash",
        )
        comparisons[name] = validate_comparison(comp, inv, store)
    package = u2_comparison.report_package(
        captured,
        dict(
            **comparisons,
            artifacts=store,
            inventory=inv,
            original_rows=selected_rows,
            limitations=["Synthetic administrative reviews only; adopted oracle bytes unchanged."],
        ),
        inputs,
    )
    verified = verify_report_inputs(package.table, package.artifacts)
    assert verified.model_card.badge == "stub"
    # Distinct valid inventory carriers scoped ONLY to the other reference profile.
    # Equal model value does not make these the required inventory/source identity.
    donors = []
    store = dict(package.artifacts)
    for f in inv.fixtures:
        donor = dict(inventory, fixtures=[f.model_dump(mode="json")])
        put(store, donor, "inventory_hash")
        ReferenceInventory.model_validate(donor)
        donors.append(donor["inventory_hash"])
    return verified, store, inv, donors


def duration_recipe(dependencies, inventory_hash, index):
    return next(
        s["recipe"]
        for s in dependencies["source_recipes"]
        if s["artifact_hash"] == inventory_hash
        and s["recipe"]["metric_path"] == f"/fixtures/{index}/values/duration_s/value"
    )


def public_load(boundary, table, store, tmp_path):
    if boundary == "memory":
        return verify_report_inputs(table, store)
    return load_verified_report_inputs(write_package(tmp_path / "package", table, store))


@pytest.mark.parametrize("boundary", ["memory", "disk"])
@pytest.mark.parametrize("profile", PROFILES)
def test_selected_adopted_positive(selected_package, profile, boundary, tmp_path):
    v, store, inv, _ = selected_package
    result = public_load(boundary, v.table, store, tmp_path)
    assert result.table == v.table
    assert result.comparisons[0].reference_inventory_hash == inv.inventory_hash
    i = PROFILES.index(profile)
    assert result.comparisons[0].fixtures[i].fixture_id == inv.fixtures[i].fixture_id
    assert result.model_card.badge == "stub"
    raw = canonical_json(v.table).encode()
    sizes = [len(x if isinstance(x, bytes) else canonical_json(x).encode()) for x in store.values()]
    assert len(store) < 100 and len(raw) + sum(sizes) < 8_000_000


@pytest.mark.parametrize("boundary", ["memory", "disk"])
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("attack", ["delete", "wrong-source"])
@pytest.mark.parametrize("category", CATEGORIES)
def test_r202_public_refuses(selected_package, category, attack, profile, boundary, tmp_path):
    v, original_store, inv, donors = selected_package
    store = dict(original_store)
    deps = v.dependencies.model_dump(mode="json")
    index, si = PROFILES.index(profile), CATEGORIES.index(category)
    selectors = duration_recipe(deps, inv.inventory_hash, index)["selectors"]
    old = selectors[si]
    if attack == "delete":
        del selectors[si]
    else:
        replacement = copy.deepcopy(
            duration_recipe(deps, inv.inventory_hash, 1 - index)["selectors"][si]
        )
        if category.startswith("reference-model-"):
            replacement["artifact_hash"] = donors[1 - index]
        assert replacement != old
        assert replacement["artifact_hash"] != old["artifact_hash"]
        # A real existing source and valid pointer, never an incidental missing artifact.
        resolve_pointer(store[replacement["artifact_hash"]], replacement["json_pointer"])
        selectors[si] = replacement
    table, store = rebind(v.table, v.context.model_dump(mode="json"), deps, store)
    with pytest.raises(IncompleteMetricContributors, match="IncompleteMetricContributors"):
        public_load(boundary, table, store, tmp_path)
