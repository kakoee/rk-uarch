"""Independent fixture integrity, not the pending A1 closure/evidence evaluator."""
import json
from pathlib import Path

from uarch_contract.hashing import canonical_json, sha256, spec_hash

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/u2_b"
SELF_KEYS = {
    "uarch-reference-source/1": "source_hash", "uarch-evidence-review/1": "review_hash",
    "uarch-family-registry/1": "registry_hash", "uarch-assumptions/1": "assumptions_hash",
    "uarch-evidence/1": "evidence_hash", "uarch-metric-dependencies/1": "dependencies_hash",
}


def digest(value):
    return sha256(canonical_json(value))


def payloads():
    return [json.loads(path.read_text()) for path in sorted(FIXTURES.glob("*.json"))]


def test_fixture_self_hashes_and_review_subjects_bind_exact_bodies():
    objects = payloads()
    reviews = {obj["review_hash"]: obj for obj in objects
               if obj.get("format") == "uarch-evidence-review/1"}
    for obj in objects:
        if obj.get("format") not in SELF_KEYS:
            continue
        own = SELF_KEYS[obj["format"]]
        body = {key: value for key, value in obj.items() if key != own}
        assert obj[own] == digest(body)
        if own != "review_hash" and "review_hash" in body:
            review = reviews[body.pop("review_hash")]
            assert review["reviewed_subject_hashes"] == [digest(body)]
            assert "synthetic" in review["reviewer"].lower()


def test_synthetic_source_bytes_and_independent_model_bindings():
    source = json.loads((FIXTURES / "evidence-source.json").read_text())
    assert source["raw_blob_sha256"] == sha256((FIXTURES / "source-literals.json").read_bytes())
    assert source["kind"] == "synthetic_fixture"
    actual = json.loads((FIXTURES / "actual-assumptions.json").read_text())
    reference = json.loads((FIXTURES / "reference-assumptions.json").read_text())
    assert digest(actual["model"]) != digest(reference["model"])
    hw = json.loads((FIXTURES / "hardware-input.json").read_text())
    registry = json.loads((FIXTURES / "family-registry.json").read_text())
    assert registry["entries"][0]["hardware_spec_hash"] == spec_hash(hw)
    for name, assumptions in [("evidence-no-band.json", actual),
                              ("reference-evidence-no-band.json", reference)]:
        evidence = json.loads((FIXTURES / name).read_text())
        assert evidence["scope"][0]["model_identity_hash"] == digest(assumptions["model"])
        assert evidence["source_hash"] == source["source_hash"]
        assert evidence["error_band"] is None
        assert evidence["classification"] == "synthetic_fixture"
        # This incomplete input must never be described as positive L3 evidence.
        assert evidence["scope"][0]["prepared_bundle_hash"] is None
        assert evidence["ordering_hash"] is None
        assert evidence["verification_hashes"] == []


def test_source_recipe_pointers_resolve_without_using_a_primary_model_for_both():
    objects = payloads()
    by_hash = {}
    for obj in objects:
        if obj.get("format") in SELF_KEYS:
            by_hash[obj[SELF_KEYS[obj["format"]]]] = obj
    hardware = json.loads((FIXTURES / "hardware-input.json").read_text())
    literal = json.loads((FIXTURES / "source-literals.json").read_text())
    by_hash[spec_hash(hardware)] = hardware
    by_hash[digest(literal)] = literal
    deps = json.loads((FIXTURES / "metric-dependencies.json").read_text())
    targets = set()
    for source in deps["source_recipes"]:
        recipe = source["recipe"]
        target = (source["artifact_hash"], recipe["metric_path"])
        assert target not in targets
        targets.add(target)
        for selector in recipe["selectors"]:
            value = by_hash[selector["artifact_hash"]]
            for part in selector["json_pointer"].lstrip("/").split("/"):
                value = value[part.replace("~1", "/").replace("~0", "~")]
            if selector["kind"] == "model_evidence":
                assert digest(value) == source["model_identity_hash"]
    for recipe in deps["recipes"]:
        for selector in recipe["selectors"]:
            assert (selector["artifact_hash"], selector["json_pointer"]) in targets
    timing = deps["source_recipes"][1]["recipe"]
    assert any(s["kind"] == "hardware_leaf" for s in timing["selectors"])
    assert hardware["memory"]["dram"]["bw_bytes_per_s"]["provenance"] == "stub"
