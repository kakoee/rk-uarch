"""Proposal input admission and independent scalar expectations; no native execution."""

import copy
import hashlib
import json
import runpy
from fractions import Fraction
from pathlib import Path

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import admit

PACKAGE = Path(__file__).resolve().parent
IDENTITIES = json.loads((PACKAGE / "fixture-identities.json").read_text())
REGISTRY = json.loads((PACKAGE / "fixtures/registry.json").read_text())
MATH = runpy.run_path(str(PACKAGE.parent / "U4-B-verification-inputs-v1/arithmetic.py"))


def load(case):
    return tuple(
        json.loads((PACKAGE / f"fixtures/{case}.{kind}.json").read_text())
        for kind in ("bundle", "profile")
    )


def seal(value, field):
    value[field] = content_hash(value, exclude=(field,))


def reseal(bundle, profile):
    point = bundle["points"][0]
    seal(point["task_graph"], "graph_hash")
    seal(point, "payload_hash")
    entry = profile["entries"][0]
    entry.update(
        graph_hash=point["task_graph"]["graph_hash"],
        point_hash=point["payload_hash"],
        initial_state=point["initial_state"],
    )
    seal(profile, "profile_hash")
    bundle["admission"]["profile_hash"] = profile["profile_hash"]
    seal(bundle, "bundle_hash")


def check(bundle, profile, *, anchor=None):
    return admit(
        bundle,
        invocation="test",
        checkpoint="B",
        registry=REGISTRY,
        profile=profile,
        trusted_registry_hash=IDENTITIES["registry_hash"],
        trusted_profile_hash=anchor or profile["profile_hash"],
    )


@pytest.mark.parametrize("case", ["D02", "D14"])
def test_exact_resident_control(case):
    bundle, profile = load(case)
    ids = IDENTITIES["cases"][case]
    assert check(bundle, profile, anchor=ids["profile_hash"]).bundle_hash == ids["bundle_hash"]
    assert bundle["points"][0]["initial_state"] == "fixture_resident"
    assert (
        bundle["producer"]["implementation_hash"]
        == "sha256:" + hashlib.sha256((PACKAGE / "fixture_authoring.py").read_bytes()).hexdigest()
    )
    assert bundle["admission"]["eligibility"] == "verification_only"


@pytest.mark.parametrize("case", ["D02", "D14"])
def test_cold_preload_refuses_after_matching_profile(case):
    bundle, profile = load(case)
    bundle["points"][0]["initial_state"] = "cold"
    # Original profile matches the old tuple: profile failure, not the SRAM failure.
    seal(bundle["points"][0], "payload_hash")
    seal(bundle, "bundle_hash")
    with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
        check(bundle, profile)
    reseal(bundle, profile)  # test-only resealed control to reach the resource layer
    with pytest.raises(ValueError, match="UnsupportedInitialState"):
        check(bundle, profile)
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        check(bundle, profile, anchor=IDENTITIES["cases"][case]["profile_hash"])


@pytest.mark.parametrize("case,source", [("D02", "s"), ("D14", "ss")])
def test_uninitialized_source_and_product_refuse(case, source):
    bundle, profile = load(case)
    original = copy.deepcopy(bundle)
    for buf in bundle["points"][0]["task_graph"]["buffers"]:
        if buf["id"] == source:
            buf["initial_residency"] = "uninitialized"
    reseal(bundle, profile)
    with pytest.raises(ValueError, match="InvalidDependency"):
        check(bundle, profile)
    _, original_profile = load(case)
    with pytest.raises(ValueError, match="TestOnlyScope"):
        admit(
            original,
            invocation="test",
            checkpoint="B",
            registry=REGISTRY,
            profile=original_profile,
            trusted_registry_hash=IDENTITIES["registry_hash"],
            trusted_profile_hash=IDENTITIES["cases"][case]["profile_hash"],
            product=True,
        )


def test_d02_independent_expected_lifecycle():
    assert MATH["isolated_dma"](10**9, 10**9, 10**9, write=True) == (
        1000,
        5000,
        53000,
        55250,
        60000,
        60000,
    )
    assert Fraction(53000) + Fraction(159744, 71) == Fraction(3922744, 71)
    b, _ = load("D02")
    job = b["points"][0]["task_graph"]["jobs"][0]
    assert job["direction"] == "write" and job["fragments"][0]["channel_id"] == 6
    assert job["source"]["size_bytes"] == job["destination"]["size_bytes"] == 256


def test_d14_independent_expected_readiness_and_zero_hops():
    # Equal independent channels each have this isolated response; one shared port serializes.
    assert MATH["isolated_dma"](10**9, 1200000000, 10**9) == (0, 3334, 52000, 54250, 58334, 60000)
    first_commit = MATH["next_edge"](10**9, 58334, 1)
    second_commit = first_commit + 1000
    assert second_commit == 61000
    assert MATH["next_edge"](1200000000, second_commit, 0) == 61667  # wrong h=0 alignment
    b, _ = load("D14")
    graph = b["points"][0]["task_graph"]
    assert graph["dependencies"] == [{"after": "c", "before": "b"}]
    assert graph["routes"][0]["core_ids"] == [0]
    assert [j["id"] for j in graph["jobs"]] == ["a", "b", "c"]
    assert sum(j["fragments"][0]["payload_bytes"] for j in graph["jobs"][:2]) == 512
    assert graph["jobs"][2]["payload_bytes"] == 256


def test_d14_registered_variant_never_enters_production():
    bundle, _ = load("D14")
    bundle["admission"].update(
        invocation="production", eligibility="component_only", profile_hash=None, case_id=None
    )
    seal(bundle, "bundle_hash")
    with pytest.raises(ValueError, match="TestOnlyHardware"):
        admit(
            bundle,
            invocation="production",
            checkpoint="B",
            registry=REGISTRY,
            profile=None,
            trusted_registry_hash=IDENTITIES["registry_hash"],
            trusted_profile_hash=None,
        )
