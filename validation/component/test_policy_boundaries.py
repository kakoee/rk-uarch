"""Independent placement and profile promise boundaries; synthetic anchors only."""

from copy import deepcopy
from pathlib import Path

from uarch_contract.mapped import MappedBundle, admit
from uarch_contract.prepared import PreparedOp

from rkuarch.mapping.component import map_component
from validation.component.corpus import build
from validation.component.join_inputs import reseal

ROOT = Path(__file__).resolve().parents[2]


def test_uniform_reverse_id_placement_is_versioned():
    base = MappedBundle.model_validate_json(
        (ROOT / "contract/fixtures/mapped/component.json").read_bytes()
    )
    ops = []
    for name, deps in [("a", ["b"]), ("b", [])]:
        raw = deepcopy(base.scope.ops[0].model_dump(mode="json"))
        raw.update(id=name, depends_on=deps)
        raw["spec"]["dimensions"] = dict(M=256, K=256, N=256)
        ops.append(PreparedOp.model_validate(raw))
    old = map_component(ops, base.hardware_spec, mapping_version="1")
    default = map_component(ops, base.hardware_spec)
    new = map_component(ops, base.hardware_spec, mapping_version="2")
    assert old.model_dump(mode="json") == default.model_dump(mode="json")
    assert not [b for b in new.buffers if b.space == "accumulator" and b.producer_id]
    assert old.dependencies == new.dependencies
    first = {b.id: b.offset_bytes for b in old.buffers}
    second = {b.id: b.offset_bytes for b in new.buffers}
    assert sum(first[k] != second[k] for k in first) == 14
    # The first topological op b takes a's old operand addresses, prefixes stay sorted IDs.
    for k in first:
        if k.startswith("op0000") and k in second and first[k] != second[k]:
            assert first[k] < second[k]
    assert old.graph_hash != new.graph_hash


def test_legacy_profile_is_graph_point_only():
    corpus = build()
    item = deepcopy(corpus["items"]["D01"])
    original = item["bundle"]
    changed = deepcopy(original)
    changed["mapping_policy"]["version"] = "2"
    reseal(changed)
    assert changed["points"] == original["points"]
    assert changed["bundle_hash"] != original["bundle_hash"]
    registry = corpus["registry"]
    admit(
        changed,
        invocation="test",
        checkpoint="B",
        registry=registry,
        profile=item["profile"],
        trusted_registry_hash=registry["registry_hash"],
        trusted_profile_hash=item["profile"]["profile_hash"],
    )
    # A whole-bundle execution selection discriminates the relabel, but it is a distinct
    # promise and requires actual external authority. This unit anchor creates none.
    assert changed["bundle_hash"] != item["bundle"]["bundle_hash"]


def test_proposed_profile_promise_and_external_anchor_are_distinct():
    import pytest
    from uarch_contract.hashing import content_hash

    corpus = build()
    for case in ("C02", "D01"):
        old = deepcopy(corpus["items"][case])
        item = deepcopy(old)
        profile = item["profile"]
        profile["format"] = "uarch-native-test-profile/2"
        profile["entries"][0]["mapping_policy"] = deepcopy(item["bundle"]["mapping_policy"])
        profile["profile_hash"] = content_hash(profile, exclude=("profile_hash",))
        item["bundle"]["admission"]["profile_hash"] = profile["profile_hash"]
        reseal(item["bundle"])
        assert item["bundle"]["points"] == old["bundle"]["points"]
        assert item["bundle"]["bundle_hash"] != old["bundle"]["bundle_hash"]
        args = dict(
            invocation="test",
            checkpoint="B",
            registry=corpus["registry"],
            profile=profile,
            trusted_registry_hash=corpus["registry"]["registry_hash"],
        )
        with pytest.raises(ValueError, match="^TestProfileMismatch"):
            admit(item["bundle"], trusted_profile_hash=old["profile"]["profile_hash"], **args)
        admit(item["bundle"], trusted_profile_hash=profile["profile_hash"], **args)
        item["bundle"]["mapping_policy"]["version"] = "2"
        reseal(item["bundle"])
        with pytest.raises(ValueError, match="^TestVariantNotAdmitted: profile mapping policy$"):
            admit(item["bundle"], trusted_profile_hash=profile["profile_hash"], **args)
