"""Discriminating host controls over genuine saved native receipts; no native execution."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "installed_inventory", Path(__file__).with_name("reconcile.py")
)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


@pytest.fixture
def evidence():
    plan = m.read(m.PUB / "inventory.candidate.json")
    binding = m.read(m.PUB / "metadata-binding.json")
    receipts = Path(m.read(m.PUB / "verification.json")["raw_work"]) / "receipts"
    listings = {mode: (receipts / (mode + "-list.log")).read_text() for mode in plan["modes"]}
    outputs = {mode: (receipts / (mode + "-tests.log")).read_text() for mode in plan["modes"]}
    payloads = {
        f"{mode}-{n}": (receipts / f"replay-{mode}-{n}.bin").read_bytes()
        for mode in plan["modes"]
        for n in range(3)
    }
    return plan, binding, listings, outputs, payloads


def test_actual_candidate_and_bound_controls(evidence):
    m.validate_plan(*evidence)
    m.validate_controls(m.read(m.HERE / "controls.candidate.json"))
    m.validate_subject(m.read(m.PUB / "subject.json"), m.read(m.STAGE2 / "subject.json"))


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "extra",
        "duplicate",
        "old19",
        "fault_source",
        "untested_head",
        "review_tree",
        "stale_replay",
        "image",
        "features",
        "metadata",
    ],
)
def test_plan_refusals(evidence, fault):
    plan, binding, listings, outputs, payloads = copy.deepcopy(evidence)
    if fault == "missing":
        plan["test_names"].pop()
    elif fault == "extra":
        plan["test_names"].append("unreviewed::extra")
    elif fault == "duplicate":
        plan["test_names"][-1] = plan["test_names"][0]
    elif fault == "old19":
        plan["test_names"] = json.loads(m.git("show", m.SOURCE + ":.github/native-k1-tests.json"))[
            "test_names"
        ]
    elif fault == "fault_source":
        plan["source_commit"] = binding["source_commit"] = m.FAULT_SOURCE
    elif fault == "untested_head":
        plan["source_commit"] = binding["source_commit"] = (
            m.git("rev-parse", "HEAD").decode().strip()
        )
    elif fault == "review_tree":
        plan["source_tree"] = binding["source_tree"] = m.read(m.STAGE2 / "subject.json")["tree"]
    elif fault == "stale_replay":
        plan["canonical_payload_sha256"] = "0" * 64
    elif fault == "image":
        plan["image_id"] = "sha256:" + "0" * 64
    elif fault == "features":
        plan["all_features"] = False
    else:
        binding["metadata_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        m.validate_plan(plan, binding, listings, outputs, payloads)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_list",
        "extra_list",
        "duplicate_list",
        "missing_pass",
        "duplicate_pass",
        "failed",
        "ignored",
        "empty",
        "one_replay_drift",
        "equal_stale_replays",
        "missing_replay",
    ],
)
def test_receipt_refusals(evidence, fault):
    plan, binding, listings, outputs, payloads = copy.deepcopy(evidence)
    first = plan["test_names"][0]
    if fault == "missing_list":
        listings["debug"] = listings["debug"].replace(first + ": test\n", "")
    elif fault == "extra_list":
        listings["debug"] += "unreviewed::extra: test\n"
    elif fault == "duplicate_list":
        listings["debug"] += first + ": test\n"
    elif fault == "missing_pass":
        outputs["debug"] = outputs["debug"].replace("test " + first + " ... ok\n", "")
    elif fault == "duplicate_pass":
        outputs["debug"] += "test " + first + " ... ok\n"
    elif fault == "failed":
        outputs["debug"] = outputs["debug"].replace("test result: ok", "test result: FAILED")
    elif fault == "ignored":
        outputs["debug"] = outputs["debug"].replace("0 ignored;", "1 ignored;")
    elif fault == "empty":
        outputs["debug"] = ""
    elif fault == "one_replay_drift":
        payloads["release-2"] += b" "
    elif fault == "equal_stale_replays":
        payloads = {key: value + b" " for key, value in payloads.items()}
    else:
        payloads.pop("debug-0")
    with pytest.raises(ValueError):
        m.validate_plan(plan, binding, listings, outputs, payloads)


@pytest.mark.parametrize(
    "fault",
    ["wrong_source", "wrong_fault_source", "stale_anchor", "stale_replay", "fault_attribution"],
)
def test_control_binding_refusals(fault):
    value = m.proposed_controls()
    if fault == "wrong_source":
        value["source_commit"] = m.FAULT_SOURCE
    elif fault == "wrong_fault_source":
        value["fault_evidence"]["source_commit"] = m.SOURCE
    elif fault == "stale_anchor":
        value["semantic_faults"]["sha256"] = "0" * 64
    elif fault == "stale_replay":
        value["replay"]["mutation"]["path"] = (
            "docs/reviews/U4-B-K1-environment-v1/replay-mutation.json"
        )
    else:
        value["fault_evidence"]["new_fault_run_on_final_source"] = True
    with pytest.raises(ValueError, match="control binding drift"):
        m.validate_controls(value)


@pytest.mark.parametrize(
    "fault",
    ["second_hash", "old_format_hash", "missing", "extra", "decision", "source", "tree_scope"],
)
def test_only_approved_exception(fault):
    original, value = m.read(m.STAGE2 / "subject.json"), m.read(m.PUB / "subject.json")
    if fault == "second_hash":
        value["postimages"]["native/README.md"] = "0" * 64
    elif fault == "old_format_hash":
        value["postimages"][m.WRAPPED] = original["postimages"][m.WRAPPED]
    elif fault == "missing":
        value["postimages"].pop("native/README.md")
    elif fault == "extra":
        value["postimages"]["unreviewed.py"] = "0" * 64
    elif fault == "decision":
        value["approved_exception"]["decision"] = "unapproved"
    elif fault == "source":
        value["approved_exception"]["source_commit"] = m.FAULT_SOURCE
    else:
        value["approved_exception"]["original_tree_is_review_reference_only"] = False
    with pytest.raises(ValueError):
        m.validate_subject(value, original)
