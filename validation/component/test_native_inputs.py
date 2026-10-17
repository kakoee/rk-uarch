"""Preparation identity and Python-gate checks; zero native execution."""

import json
from copy import deepcopy

import pytest
from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedEngineJob, admit

from validation.component.native_inputs import HISTORY, private_job, prospective_inputs


@pytest.fixture(scope="module")
def proposal():
    return prospective_inputs()


def test_all_historical_inputs_and_expectations_remain_distinct(proposal):
    old = json.loads(HISTORY.read_text())
    assert len(old["cases"]) == len(proposal["transitions"]) == 106
    assert len(proposal["items"]) == 111
    for row in old["cases"]:
        item = proposal["items"][row["case_id"]]
        point = item["bundle"]["points"][0]
        assert point["payload_hash"] == row["point_hash"]
        assert point["task_graph"]["graph_hash"] == row["graph_hash"]
        assert item["bundle"]["bundle_hash"] != row["bundle_hash"]
        assert item["expected"] == row["expected"]
        assert item["expected_layer"] == row["expected_layer"]
        assert item["profile"]["entries"][0]["mapping_policy"] == item["bundle"]["mapping_policy"]
    assert (
        proposal["items"]["A-C02-resident"]["bundle"]["points"]
        != proposal["items"]["C02"]["bundle"]["points"]
    )
    assert proposal["authority"] is None


@pytest.mark.parametrize("case", ["C02", "D01", "B-native-O2", "B2-C04-transient"])
def test_exact_p2_promise_and_external_anchor(proposal, case):
    item = proposal["items"][case]
    b, p = deepcopy(item["bundle"]), item["profile"]
    args = dict(
        invocation="test",
        checkpoint="B",
        registry=proposal["registry"],
        profile=p,
        trusted_registry_hash=proposal["registry"]["registry_hash"],
        trusted_profile_hash=p["profile_hash"],
    )
    admit(b, **args)
    b["mapping_policy"]["version"] = "1" if b["mapping_policy"]["version"] == "2" else "2"
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    with pytest.raises(ValueError, match="TestVariantNotAdmitted: profile mapping policy"):
        admit(b, **args)
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        admit(
            item["bundle"],
            **(args | dict(trusted_profile_hash=content_hash("wrong external anchor"))),
        )


def test_o2_private_job_keeps_true_transient_input_and_literal(proposal):
    item = proposal["items"]["B-native-O2"]
    job = MappedEngineJob.model_validate(private_job(item, proposal["registry"]))
    acc = next(b for b in job.mapped_point.task_graph.buffers if b.id == "bacc")
    assert (acc.producer_id, list(acc.final_consumer_ids), acc.offset_bytes, acc.size_bytes) == (
        "b",
        ["c", "d"],
        256,
        84,
    )
    assert job.workload_closure.mapping_policy.version == "2"
    assert item["expected"]["transient_bacc"] == [547000, 2188000]
    assert item["expected"]["duration_ps"] == 2735000


def test_resource_negatives_have_separate_positive_synthetic_profiles(proposal):
    for name in ("C04-carrier", "C06-small", "C07-hbm-1", "C07-sram-1"):
        early = proposal["items"][name]
        targeted = proposal["items"]["B-native-resource-" + name]
        assert early["expected_layer"] == "profile"
        assert early["profile"]["entries"][0]["expected_outcome"] != "success"
        assert targeted["expected_layer"] == "resource-preflight"
        assert targeted["profile"]["entries"][0]["expected_outcome"] == "success"
        assert early["bundle"]["points"] == targeted["bundle"]["points"]
        args = dict(
            invocation="test",
            checkpoint="B",
            registry=proposal["registry"],
            trusted_registry_hash=proposal["registry"]["registry_hash"],
        )
        with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
            admit(
                early["bundle"],
                profile=early["profile"],
                trusted_profile_hash=early["profile"]["profile_hash"],
                **args,
            )
        # The same admission API now reaches its later resource preflight.
        with pytest.raises(ValueError, match=targeted["expected_public_code"]):
            admit(
                targeted["bundle"],
                profile=targeted["profile"],
                trusted_profile_hash=targeted["profile"]["profile_hash"],
                **args,
            )
        with pytest.raises(ValueError, match=targeted["expected_public_code"]):
            MappedEngineJob.model_validate(private_job(targeted, proposal["registry"]))
