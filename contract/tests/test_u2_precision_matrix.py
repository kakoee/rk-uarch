"""B1 frozen inventory and explicit proposed matrix inputs; no oracle generation."""

import itertools
import json
from collections import Counter
from pathlib import Path

import yaml
from uarch_contract.hashing import canonical_json, sha256

from contract.tests.historical_snapshot import historical_snapshot

ROOT = Path(__file__).resolve().parents[2]
PIN = "1e5706e0ebfcc67c1a7333079a35b75f693e9963"
VENDOR = historical_snapshot()
FIXTURES = ROOT / "contract/tests/fixtures/u2_b"


def test_same_pin_and_complete_frozen_file_hashes() -> None:
    manifest = json.loads((VENDOR / "MANIFEST.json").read_text())
    assert manifest["rk_sha"] == PIN
    assert sha256((VENDOR / "MANIFEST.json").read_bytes()) == (
        "sha256:b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d"
    )
    for name, expected in manifest["files"].items():
        assert sha256((VENDOR / name).read_bytes()) == "sha256:" + expected


def test_retained_component_pairs_bind_real_inputs_and_unchanged_efficiency() -> None:
    components = json.loads((FIXTURES / "component-precisions.json").read_text())
    rows = json.loads((VENDOR / "parity/fixtures.json").read_text())
    observed = Counter(
        (row["component_params_file"], row["precision"]["compute"], row["precision"]["kv_cache"])
        for row in rows
    )
    expected: set[tuple[str, str, str]] = set()
    for entry in components:
        binding = entry["binding"]
        component = VENDOR / binding["component_file"]
        assert binding["component_bytes_sha256"] == sha256(component.read_bytes())
        assert binding["oracle_manifest_sha256"] == sha256((VENDOR / "MANIFEST.json").read_bytes())
        assert binding["upstream_sha"] == PIN
        raw = yaml.safe_load(component.read_text())
        execution = json.loads((FIXTURES / (component.stem + "-execution.json")).read_text())
        assert execution["compute"]["value"] == raw["execution_model"]["value"]["value"] == 0.55
        assert execution["compute"]["provenance"] == "stub"
        assert binding["execution_model_hash"] == execution["execution_model_hash"]
        for obj, own in [
            (entry, "precision_hash"),
            (binding, "binding_hash"),
            (execution, "execution_model_hash"),
        ]:
            assert obj[own] == sha256(canonical_json({k: v for k, v in obj.items() if k != own}))
        pairs = [(p["compute"], p["kv_cache"]) for p in entry["precisions"]]
        assert len(pairs) == len(set(pairs))
        assert all(k in binding["supported_kv_storage"] for _, k in pairs)
        expected.update((binding["component_file"], c, k) for c, k in pairs)
    assert set(observed) == expected
    assert set(observed.values()) == {144}
    assert len(rows) == 864


def test_proposed_selection_is_1008_unique_queries_with_four_separate_refusals() -> None:
    plan = json.loads((ROOT / "tests/fixtures/u2_b/matrix-plan.json").read_text())
    rows = json.loads((VENDOR / "parity/fixtures.json").read_text())
    queries = {canonical_json(row["query"]) for row in rows}
    assert len(queries) == 24
    assert set(plan["models"]) == {row["model_id"] for row in rows}
    assert set(plan["tp"]) == {row["tp"] for row in rows}
    pairs = [(p["component"], p["compute"], p["kv_cache"]) for p in plan["positive_pairs"]]
    assert len(pairs) == len(set(pairs)) == 7
    assert len(set(itertools.product(pairs, plan["models"], plan["tp"], queries))) == 1008
    assert ("npu-l4.yaml", "bf16", "fp8") not in pairs
    refusals = {(p["component"], p["compute"], p["kv_cache"]) for p in plan["direct_peak_refusals"]}
    assert refusals == {
        ("asic_placeholder.yaml", "bf16", "bf16"),
        ("asic_placeholder.yaml", "fp8", "fp8"),
        ("npu-l4.yaml", "fp16", "fp16"),
        ("npu-l4.yaml", "fp8", "fp8"),
    }
    assert not refusals.intersection(pairs)
    assert plan["new_execution_efficiency"]["value"] == 1.0


def test_B2_explicit_bindings_reject_missing_duplicate_and_inferred_inputs() -> None:
    import pytest

    from scripts.vendor_rk import validate_u2_component_inputs

    entries = json.loads((FIXTURES / "component-precisions.json").read_text())
    descriptors = {
        entry["component_id"]: (VENDOR / entry["binding"]["component_file"]).read_bytes()
        for entry in entries
    }
    artifacts = {}
    for name in ["asic_placeholder-execution.json", "nvidia_h100_sxm-execution.json"]:
        value = json.loads((FIXTURES / name).read_text())
        artifacts[value["execution_model_hash"]] = value
    accepted = validate_u2_component_inputs(entries, descriptors, artifacts, require_full=False)
    assert len(accepted) == 2
    with pytest.raises(ValueError):
        validate_u2_component_inputs(
            entries + entries[:1], descriptors, artifacts, require_full=False
        )
    entries[0]["precisions"][0].pop("kv_cache")
    with pytest.raises(ValueError):
        validate_u2_component_inputs(entries, descriptors, artifacts, require_full=False)


def test_B2_staging_preserves_two_distinct_whole_revisions(tmp_path: Path) -> None:
    import pytest

    from scripts.vendor_rk import (
        compare_staged_revisions,
        publish_snapshot,
        snapshot_bytes,
        staging_destination,
    )

    first = staging_destination(tmp_path / "one", ROOT / "contract/vendor")
    second = staging_destination(tmp_path / "two", ROOT / "contract/vendor")
    files = snapshot_bytes({"synthetic.txt": b"SYNTHETIC unit input only\n"}, PIN)
    publish_snapshot(first, files)
    publish_snapshot(second, files)
    assert compare_staged_revisions(first, second) == ()
    third = staging_destination(tmp_path / "three", ROOT / "contract/vendor")
    publish_snapshot(
        third, snapshot_bytes({"synthetic.txt": b"different synthetic unit input\n"}, PIN)
    )
    assert "synthetic.txt" in compare_staged_revisions(first, third)
    with pytest.raises(ValueError):
        staging_destination(ROOT / "contract/vendor/run", ROOT / "contract/vendor")
    with pytest.raises(ValueError):
        compare_staged_revisions(first, first)
