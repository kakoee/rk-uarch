"""Proposed profile/2 choice only; synthetic anchors, no accepted authority."""

from copy import deepcopy
from typing import Any

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import NativeTestProfile, admit

from validation.component.corpus import build
from validation.component.join_inputs import reseal


def inputs(versioned: Any = False) -> Any:
    c = build()
    item = deepcopy(c["items"]["D01"])
    if versioned:
        p = item["profile"]
        p["format"] = "uarch-native-test-profile/2"
        p["entries"][0]["mapping_policy"] = deepcopy(item["bundle"]["mapping_policy"])
        p["profile_hash"] = content_hash(p, exclude=("profile_hash",))
        item["bundle"]["admission"]["profile_hash"] = p["profile_hash"]
        reseal(item["bundle"])
    return item, c["registry"]


def admit_item(item: Any, reg: Any, anchor: Any = None) -> Any:
    return admit(
        item["bundle"],
        invocation="test",
        checkpoint="B",
        registry=reg,
        trusted_registry_hash=reg["registry_hash"],
        profile=item["profile"],
        trusted_profile_hash=anchor or item["profile"]["profile_hash"],
    )


def test_legacy_graph_point_profile_does_not_bind_policy() -> None:
    item, reg = inputs()
    admit_item(item, reg)
    before = deepcopy(item)
    item["bundle"]["mapping_policy"]["version"] = "2"
    reseal(item["bundle"])
    assert item["bundle"]["points"] == before["bundle"]["points"]
    assert item["profile"] == before["profile"]
    assert item["bundle"]["bundle_hash"] != before["bundle"]["bundle_hash"]
    admit_item(item, reg)  # Honest current promise: accepted, no policy-version binding.


@pytest.mark.parametrize("field,value", [("version", "2"), ("name", "other"), ("buffer_depth", 1)])
def test_new_profile_exact_policy_binding(field: Any, value: Any) -> None:
    item, reg = inputs(True)
    NativeTestProfile.model_validate(item["profile"])
    admit_item(item, reg)
    bad = deepcopy(item)
    bad["bundle"]["mapping_policy"][field] = value
    reseal(bad["bundle"])
    with pytest.raises(ValueError, match="^TestVariantNotAdmitted: profile mapping policy$"):
        admit_item(bad, reg)
    admit_item(item, reg)


def test_profile_edit_cannot_replace_external_anchor() -> None:
    item, reg = inputs(True)
    anchor = item["profile"]["profile_hash"]
    item["profile"]["entries"][0]["mapping_policy"]["version"] = "2"
    item["profile"]["profile_hash"] = content_hash(item["profile"], exclude=("profile_hash",))
    item["bundle"]["admission"]["profile_hash"] = item["profile"]["profile_hash"]
    reseal(item["bundle"])
    with pytest.raises(ValueError, match="^TestProfileMismatch"):
        admit_item(item, reg, anchor)


@pytest.mark.parametrize("fault", ["missing", "legacy_extension", "kernel"])
def test_profile_format_and_scope_cannot_be_mixed(fault: Any) -> None:
    item, _ = inputs(True)
    p = item["profile"]
    if fault == "missing":
        del p["entries"][0]["mapping_policy"]
    if fault == "legacy_extension":
        p["format"] = "uarch-native-test-profile/1"
    if fault == "kernel":
        p["entries"][0]["scope"] = "kernel_fixture"
    p["profile_hash"] = content_hash(p, exclude=("profile_hash",))
    with pytest.raises(ValueError, match="TestProfileMismatch: profile policy format"):
        NativeTestProfile.model_validate(p)
