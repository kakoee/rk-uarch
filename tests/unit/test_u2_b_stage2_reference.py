"""R202 semantic mutations over exact adopted inputs, not a generated reference.

Only the reference-side input recipe declarations are assembled here. Complete public
package/load/render checks use the inherited reviewer capture in the Stage 2 driver.
No producer execution, support-check override, or numerical expectation synthesis.
"""

import copy
import json
from pathlib import Path

import pytest
import yaml
from uarch_contract.comparison import ReferenceInventory
from uarch_contract.errors import IncompleteMetricContributors
from uarch_contract.hashing import artifact_identity, content_hash, sha256
from uarch_contract.report_context import MetricDependencies

from rkuarch.provenance.reference_contributors import validate_reference_contributors

ROOT = Path(__file__).parents[2]
ADOPTED = ROOT / "contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963"
PRIOR_MANIFEST = "sha256:f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e"
CURRENT_MANIFEST = "sha256:20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad"
ZERO = "sha256:" + "0" * 64


@pytest.fixture(scope="module")
def reference_inputs():
    inventory = json.loads(
        (ROOT / "tests/fixtures/u2_b/stage2/reference-inventory.json").read_text()
    )
    assert inventory["oracle_manifest_sha256"] == PRIOR_MANIFEST
    raw = (ADOPTED / "MANIFEST.json").read_bytes()
    assert sha256(raw) == CURRENT_MANIFEST
    # Create a current carrier while preserving the original v2 fixture and values.
    inventory["oracle_manifest_sha256"] = CURRENT_MANIFEST
    inventory["inventory_hash"] = content_hash(inventory, exclude=("inventory_hash",))
    inv = ReferenceInventory.model_validate(inventory)
    store = {inv.inventory_hash: inventory}
    store[sha256(raw)] = raw
    manifest = json.loads(raw)
    for p in (ADOPTED / "u2-inputs/artifacts").glob("*.json"):
        data = json.loads(p.read_text())
        store[artifact_identity(data)] = data
    for p in (ADOPTED / "u2-inputs/components").glob("*.yaml"):
        data = p.read_bytes()
        store[sha256(data)] = data
        value = yaml.safe_load(data)
        store[content_hash(value)] = value
    raw_rows = (ADOPTED / "parity/fixtures.json").read_bytes()
    assert sha256(raw_rows) == "sha256:" + manifest["files"]["parity/fixtures.json"]
    rows = json.loads(raw_rows)
    assert [r["id"] for r in rows] == [f.fixture_id for f in inv.fixtures]
    sources = []
    for i, (row, fixture) in enumerate(zip(rows, inv.fixtures, strict=True)):
        original = artifact_identity(row)
        store[original] = row
        binding = store[fixture.component_binding_hash]
        raw_hash = binding.get(
            "projected_descriptor_bytes_sha256", binding.get("component_bytes_sha256")
        )
        descriptor = yaml.safe_load(store[raw_hash])
        for channel in (
            "matrix_ops",
            "vector_ops",
            "memory_read_bytes",
            "memory_write_bytes",
            "duration_s",
        ):
            required = [
                ("prepared_content", original, p)
                for p in ("/model", "/model_shape", "/query", "/precision", "/tp")
            ]
            required += [
                (kind, inv.inventory_hash, "/reference_model")
                for kind in ("model_assumption", "model_evidence")
            ]
            if channel == "duration_s":
                for name in (row["precision"]["compute"] + "_tflops", "hbm_bw"):
                    if binding["kind"] == "uarch_projection":
                        truth = store[binding["primary_export_hash"]]
                        j = next(j for j, p in enumerate(truth["params"]) if p["name"] == name)
                        required.append(
                            ("hardware_leaf", binding["primary_export_hash"], f"/params/{j}/value")
                        )
                    else:
                        required.append(
                            ("hardware_leaf", content_hash(descriptor), "/params/" + name)
                        )
                required.append(("model_assumption", binding["execution_model_hash"], "/compute"))
            sources.append(
                dict(
                    artifact_hash=inv.inventory_hash,
                    model_identity_hash=content_hash(inv.reference_model),
                    recipe=dict(
                        metric_path=f"/fixtures/{i}/values/{channel}/value",
                        purpose="duration" if channel == "duration_s" else "counts",
                        granularity="whole_iteration",
                        applicable_dimensions=["model_identity", "precision"],
                        selectors=[
                            dict(kind=k, artifact_hash=h, json_pointer=p) for k, h, p in required
                        ],
                    ),
                )
            )
    deps = dict(
        format="uarch-metric-dependencies/1",
        dependencies_hash=ZERO,
        review_hash=ZERO,
        version="independent-stage2-input-check",
        model_identity_hash=content_hash(inv.reference_model),
        recipes=[sources[0]["recipe"]],
        source_recipes=sources,
    )
    return inv, deps, store


def test_both_original_efficiencies_and_manifest_control(reference_inputs):
    inv, deps, store = reference_inputs
    values = {
        store[store[f.component_binding_hash]["execution_model_hash"]]["compute"]["value"]
        for f in inv.fixtures
    }
    assert values == {0.55, 1.0}
    validate_reference_contributors(
        MetricDependencies.model_validate(deps), (inv.inventory_hash,), store
    )


@pytest.mark.parametrize("fixture_index", [0, 864], ids=["retained-point55", "projection-one"])
@pytest.mark.parametrize(
    "selector_index",
    range(10),
    ids=[
        "model",
        "shape",
        "query",
        "precision",
        "tp",
        "reference-assumption",
        "reference-model",
        "peak",
        "bandwidth",
        "efficiency",
    ],
)
@pytest.mark.parametrize("attack", ["delete", "wrong-source"])
def test_each_required_reference_input_is_bound(
    reference_inputs, fixture_index, selector_index, attack
):
    inv, original, original_store = reference_inputs
    deps = copy.deepcopy(original)
    store = dict(original_store)
    recipe = deps["source_recipes"][fixture_index * 5 + 4]["recipe"]
    if attack == "delete":
        del recipe["selectors"][selector_index]
    else:
        other_index = 864 if fixture_index == 0 else 0
        replacement = original["source_recipes"][other_index * 5 + 4]["recipe"]["selectors"][
            selector_index
        ]
        if replacement == recipe["selectors"][selector_index]:
            # The shared reference model is attacked with an independently hashed actual model.
            model = dict(name="physical-resolved", version="test", implementation_hash=ZERO)
            container = dict(reference_model=model)
            store[content_hash(container)] = container
            replacement = dict(replacement, artifact_hash=content_hash(container))
        recipe["selectors"][selector_index] = replacement
    with pytest.raises(IncompleteMetricContributors):
        validate_reference_contributors(
            MetricDependencies.model_validate(deps), (inv.inventory_hash,), store
        )


@pytest.mark.parametrize("attack", ["control", "missing-raw", "changed-row"])
def test_selected_inventory_requires_authenticated_original_member(reference_inputs, attack):
    inv, original, original_store = reference_inputs
    inventory = inv.model_dump(mode="json")
    inventory["fixtures"] = inventory["fixtures"][:1]
    inventory["inventory_hash"] = content_hash(inventory, exclude=("inventory_hash",))
    identity = inventory["inventory_hash"]
    store = dict(original_store)
    store[identity] = inventory
    raw_rows = (ADOPTED / "parity/fixtures.json").read_bytes()
    if attack != "missing-raw":
        store[sha256(raw_rows)] = raw_rows
    deps = copy.deepcopy(original)
    deps["source_recipes"] = deps["source_recipes"][:5]
    for source in deps["source_recipes"]:
        source["artifact_hash"] = identity
        for selector in source["recipe"]["selectors"]:
            if selector["artifact_hash"] == inv.inventory_hash:
                selector["artifact_hash"] = identity
    if attack == "changed-row":
        row = json.loads(raw_rows)[0]
        row["model_shape"]["vocab_size"] += 1
        changed_hash = content_hash(row)
        store[changed_hash] = row
        for source in deps["source_recipes"]:
            for selector in source["recipe"]["selectors"]:
                if selector["kind"] == "prepared_content":
                    selector["artifact_hash"] = changed_hash
    if attack == "control":
        validate_reference_contributors(MetricDependencies.model_validate(deps), (identity,), store)
    else:
        with pytest.raises(IncompleteMetricContributors):
            validate_reference_contributors(
                MetricDependencies.model_validate(deps), (identity,), store
            )


@pytest.mark.parametrize("mode", ["valid", "missing", "cycle"])
def test_recursive_reference_recipe_preserves_original_source(reference_inputs, mode):
    inv, original, original_store = reference_inputs
    deps = copy.deepcopy(original)
    store = dict(original_store)
    container = {"intermediate_duration": 1.0}
    intermediate = content_hash(container)
    store[intermediate] = container
    source = deps["source_recipes"][4]
    original_selector = source["recipe"]["selectors"].pop()
    link = dict(
        kind="result_field", artifact_hash=intermediate, json_pointer="/intermediate_duration"
    )
    source["recipe"]["selectors"].append(link)
    if mode != "missing":
        nested = copy.deepcopy(source)
        nested["artifact_hash"] = intermediate
        nested["recipe"]["metric_path"] = "/intermediate_duration"
        nested["recipe"]["selectors"] = [link if mode == "cycle" else original_selector]
        deps["source_recipes"].append(nested)
    if mode == "valid":
        validate_reference_contributors(
            MetricDependencies.model_validate(deps), (inv.inventory_hash,), store
        )
    else:
        with pytest.raises(IncompleteMetricContributors):
            validate_reference_contributors(
                MetricDependencies.model_validate(deps), (inv.inventory_hash,), store
            )
