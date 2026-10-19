"""Synthetic review records only. No startup, native process or genuine authority."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native import component_review as review
from rkuarch.engines.native.records import FileBinding


@pytest.fixture
def records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    def put(name: str, value: Any) -> dict[str, str]:
        raw = canonical_json(value).encode()
        (tmp_path / name).write_bytes(raw)
        return {"path": name, "byte_hash": sha256(raw)}

    launcher = put("launcher.py", {"synthetic": "not executable"})
    payload = put("payload.json", {"synthetic": "no executable"})
    consumers = {"files": [launcher], "import_root": str(tmp_path)}
    subject = {"runtime_payload_byte_hash": payload["byte_hash"]}
    provenance = put("provenance.json", {"synthetic": "independent B seam mocked"})
    evidence = put("evidence.json", {"synthetic": "not actual startup assurance"})
    manifest = put("startup-manifest.json", {"synthetic": True})
    startup = {
        "format": "uarch-component-startup-assurance/1",
        "subject": {**subject, "consumer_hash": content_hash(consumers)},
        "verdict": "accepted",
        "launcher": launcher,
        "manifest": manifest,
        "evidence": [evidence],
    }
    record = {
        "format": "uarch-component-runtime-review/2",
        "subject": subject,
        "build_provenance": provenance,
        "startup_assurance": put("startup.json", startup),
        "selected_support_current": True,
        "selected_support_evidence": [evidence],
        "optional_read_evidence": None,
    }
    calls: list[Any] = []

    def consume(root: Path, raw: Any, expected: Any) -> list[FileBinding]:
        calls.append((root, raw, expected))
        return [FileBinding.model_validate(evidence)]

    monkeypatch.setattr(review, "_consume_provenance", consume)
    expected = {**subject, "consumer_hash": content_hash(consumers)}
    return dict(
        root=tmp_path,
        put=put,
        record=record,
        startup=startup,
        calls=calls,
        expected=expected,
        launcher=FileBinding.model_validate(launcher),
    )


def checked(f: dict[str, Any]) -> Any:
    return review.check_runtime_review(
        f["root"], f["record"], expected=f["expected"], launcher=f["launcher"]
    )


def test_trace_absence_does_not_substitute_for_or_block_required_review(
    records: dict[str, Any],
) -> None:
    result = checked(records)
    assert len(records["calls"]) == 1
    assert result.startup_manifest.path == "startup-manifest.json"
    assert result.optional_read_evidence is None
    assert {x.path for x in result.required_files} >= {
        "provenance.json",
        "startup.json",
        "evidence.json",
        "launcher.py",
        "startup-manifest.json",
    }
    assert "read_audit_complete" not in records["record"]


@pytest.mark.parametrize(
    "field", ["build_provenance", "startup_assurance", "selected_support_evidence"]
)
def test_missing_required_review_refuses(records: dict[str, Any], field: str) -> None:
    del records["record"][field]
    with pytest.raises(ValueError):
        checked(records)


@pytest.mark.parametrize(
    "mutation", ["old", "subject", "read-flag", "false-support", "numeric-support"]
)
def test_wrong_or_stale_review_refuses(records: dict[str, Any], mutation: str) -> None:
    record = records["record"]
    if mutation == "old":
        record["format"] = "uarch-component-runtime-review/1"
    elif mutation == "subject":
        record["subject"]["runtime_payload_byte_hash"] = "sha256:" + "f" * 64
    elif mutation == "read-flag":
        record["read_audit_complete"] = True
    else:
        record["selected_support_current"] = False if mutation == "false-support" else 1
    with pytest.raises(ValueError):
        checked(records)


@pytest.mark.parametrize("mutation", ["consumer", "payload", "launcher", "evidence", "verdict"])
def test_startup_is_separate_exact_assurance(records: dict[str, Any], mutation: str) -> None:
    value = deepcopy(records["startup"])
    if mutation in ("consumer", "payload"):
        key = "consumer_hash" if mutation == "consumer" else "runtime_payload_byte_hash"
        value["subject"][key] = "sha256:" + "f" * 64
    elif mutation == "launcher":
        value["launcher"] = records["put"]("other-launcher.py", {"synthetic": "wrong"})
    elif mutation == "evidence":
        value["evidence"] = []
    else:
        value["verdict"] = "pending"
    records["record"]["startup_assurance"] = records["put"]("startup.json", value)
    with pytest.raises(ValueError):
        checked(records)


def test_optional_read_evidence_is_only_hash_bound(records: dict[str, Any]) -> None:
    records["record"]["optional_read_evidence"] = records["put"](
        "optional.json", {"read_audit_complete": False, "status": "NONE CAPTURED"}
    )
    result = checked(records)
    assert result.optional_read_evidence is not None
    assert result.optional_read_evidence.path == "optional.json"
    assert (records["root"] / "optional.json").read_text().find("false") >= 0


def test_bad_provenance_cannot_be_replaced_by_good_startup(
    records: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*args: Any) -> Any:
        raise ValueError("synthetic independent build refusal")

    monkeypatch.setattr(review, "_consume_provenance", refuse)
    with pytest.raises(ValueError, match="independent build refusal"):
        checked(records)


def test_stale_required_evidence_refuses(records: dict[str, Any]) -> None:
    (records["root"] / "evidence.json").write_text("changed")
    with pytest.raises(ValueError, match="digest mismatch"):
        checked(records)


def test_D3_review_has_its_own_subject_and_runtime_review_link() -> None:
    pin = "sha256:" + "1" * 64
    binding = {"path": "synthetic.json", "byte_hash": pin}
    value = {
        "format": "uarch-component-negative-review/3",
        "subject": {"runtime_payload_byte_hash": pin, "negative_inventory_byte_hash": pin},
        "runtime_review": binding,
        "finite_refusals_current": True,
        "finite_refusals_evidence": [binding],
    }
    assert (
        review.ComponentNegativeReview.model_validate(value).runtime_review.path == "synthetic.json"
    )
    for changed in (
        {**value, "format": "uarch-component-negative-review/2"},
        {**value, "finite_refusals_current": 1},
        {**value, "finite_refusals_evidence": []},
        {**value, "read_audit_complete": True},
    ):
        with pytest.raises(ValueError):
            review.ComponentNegativeReview.model_validate(changed)
