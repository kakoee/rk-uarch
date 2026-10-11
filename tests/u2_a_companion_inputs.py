"""A-owned CLI input scaffolding; reviews are SYNTHETIC and grant no real authority.

Capacity construction below reuses the bounded authentic source selection and actual
preparation refusal from B's test_actual_capacity_failure_and_prior_attempts_survive.
Only test input construction is shared; production B assembly runs at the public CLI.
"""

import copy

import pytest
from uarch_contract.hashing import canonical_json, content_hash

from tests.unit.test_u2_b_companions import canonical_comparisons, change_deps, selected

ZERO = "sha256:" + "0" * 64


def actual_capacity_inputs():
    """Record a real ordinary-analytic refusal; fabricate no bundle/job/result after it."""
    import json

    from uarch_contract.comparison import reduce_outcomes, validate_comparison
    from uarch_contract.hashing import sha256

    from scripts.u2_inputs import Inputs
    from tests import u2_comparison
    from tests.integration.test_u2_b_r202_public import ADOPTED, MANIFEST

    inputs, inv, _ = copy.deepcopy(selected.__wrapped__())
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
    return inputs, h, rh


def write_assembly_inputs(inputs, root):
    """Serialize exact supplied declarations/closure for the real public command."""
    from rkuarch.table.build import captured_artifacts

    root.mkdir(parents=True, exist_ok=True)
    c = inputs["captured"]
    capture_dir = root / "capture"
    capture_dir.mkdir()
    for h, value in captured_artifacts(c).items():
        (capture_dir / (h[7:] + ".json")).write_text(canonical_json(value) + "\n")
    values = {
        "prepared-input": c.bundle,
        "assumptions": c.assumptions,
        "recipes": inputs["dependencies"],
        "model-card": inputs["model_card"],
        "registry": inputs["registry"],
        "recipe-review": inputs["artifacts"][inputs["dependencies"].review_hash],
        "registry-review": inputs["artifacts"][inputs["registry"].review_hash],
    }
    args = ["--capture-dir", str(capture_dir)]
    for name, value in values.items():
        path = root / (name + ".json")
        path.write_text(canonical_json(value) + "\n")
        args += ["--" + name, str(path)]
    artifacts = root / "artifacts"
    artifacts.mkdir()
    for h, value in inputs["artifacts"].items():
        (artifacts / (h[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else canonical_json(value).encode() + b"\n"
        )
    for h in inputs["comparison_hashes"]:
        path = root / (h[7:] + ".json")
        path.write_text(canonical_json(inputs["artifacts"][h]) + "\n")
        args += ["--comparison", str(path)]
    return [*args, "--artifact-dir", str(artifacts), "--output", str(root / "context.json")]


def review_public_draft(root):
    """SYNTHETIC test reviewer reads actual CLI draft bytes; not a real review example."""
    import json

    from uarch_contract.hashing import review_subject_hash

    from tests.unit.test_u2_b_companions import reviewed

    deps = json.loads((root / "draft/metric-dependencies.json").read_text())
    subject = review_subject_hash(deps)
    assert (root / "draft/review-subject.txt").read_text().strip() == subject
    assert deps["review_hash"] == ZERO
    store = {}
    bound = reviewed(deps, "dependencies_hash", store)
    bundle = json.loads((root / "prepared.json").read_text())
    registry = reviewed(
        dict(
            format="uarch-family-registry/1",
            registry_hash=ZERO,
            review_hash=ZERO,
            version="SYNTHETIC-public-subprocess/1",
            entries=[
                dict(
                    family="synthetic-test-family",
                    hardware_spec_hash=bundle["intent"]["hardware_spec_hash"],
                )
            ],
        ),
        "registry_hash",
        store,
    )
    for name, value in (
        ("recipe-review", store[bound["review_hash"]]),
        ("registry", registry),
        ("registry-review", store[registry["review_hash"]]),
    ):
        assert "SYNTHETIC" in str(value)
        (root / (name + ".json")).write_text(canonical_json(value) + "\n")
