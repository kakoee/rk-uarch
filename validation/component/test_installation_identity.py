"""CI-C1 identity controls, explicitly not behavioral checker mutation scores."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests.component_current_identity import current_test_bindings
from validation.component.installation_identity import (
    ADR,
    BINDING,
    COMPONENT_SHA,
    F5_TEST,
    INSTALLED_BYTES,
    INSTALLED_SHA,
    ISSUE_ADR_BYTES,
    ISSUE_ADR_SHA,
    ISSUE_APPENDIX_SHA,
    ISSUE_BINDING,
    SELECTION,
    SELF_TEST,
    digest,
    installation_bindings,
    issue_bindings,
    verify_adr,
    verify_postimages,
)

ROOT = Path(__file__).resolve().parents[2]


def test_exact_installed_and_component_text_control() -> None:
    raw = (ROOT / ADR).read_bytes()
    assert len(raw) == ISSUE_ADR_BYTES
    assert digest(raw) == ISSUE_ADR_SHA
    assert digest(raw[:INSTALLED_BYTES]) == INSTALLED_SHA
    assert digest(raw[INSTALLED_BYTES:48294]) == COMPONENT_SHA
    assert digest(raw[48294:]) == ISSUE_APPENDIX_SHA
    verify_adr(raw)
    selection = json.loads((ROOT / SELECTION).read_text())
    verify_postimages(ROOT, current_test_bindings(ROOT, installation_bindings(ROOT, selection)))


@pytest.mark.parametrize(
    "part,detail", [("K2", "installed K2 ADR prefix"), ("component", "reviewed component suffix")]
)
def test_adr_stream_tamper(part: str, detail: str) -> None:
    raw = bytearray((ROOT / ADR).read_bytes())
    raw[INSTALLED_BYTES - 10 if part == "K2" else INSTALLED_BYTES + 10] ^= 1
    with pytest.raises(AssertionError, match=detail):
        verify_adr(bytes(raw))


@pytest.mark.parametrize("change", ["omit_component", "append", "drop_K2_suffix"])
def test_adr_omission_and_arbitrary_later_edits(change: str) -> None:
    raw = (ROOT / ADR).read_bytes()
    forged = {
        "omit_component": raw[:INSTALLED_BYTES],
        "append": raw + b"later edit\n",
        "drop_K2_suffix": raw[:28596] + raw[INSTALLED_BYTES:],
    }[change]
    with pytest.raises(AssertionError):
        verify_adr(forged)


@pytest.mark.parametrize(
    "change", ["missing_F5", "missing_self", "extra_override", "arbitrary_ADR"]
)
def test_binding_transition_inventory_is_exact(change: str) -> None:
    record = json.loads((ROOT / BINDING).read_text())
    record = deepcopy(record)
    if change == "missing_F5":
        del record["additions"][F5_TEST]
    elif change == "missing_self":
        del record["replacements"][SELF_TEST]
    elif change == "extra_override":
        record["replacements"]["contract/uarch_contract/mapped.py"] = dict(
            before="0" * 64, after="1" * 64
        )
    else:
        record["replacements"][ADR]["after"] = "0" * 64
    with pytest.raises(AssertionError):
        installation_bindings(ROOT, json.loads((ROOT / SELECTION).read_text()), record)


@pytest.mark.parametrize("path", [F5_TEST, SELF_TEST])
@pytest.mark.parametrize("change", ["edit", "omit"])
def test_f5_and_changed_identity_test_are_bound(tmp_path: Path, path: str, change: str) -> None:
    expected = installation_bindings(ROOT, json.loads((ROOT / SELECTION).read_text()))
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    if change == "edit":
        target.write_bytes((ROOT / path).read_bytes() + b"\n# changed\n")
    with pytest.raises((AssertionError, FileNotFoundError)):
        verify_postimages(tmp_path, {path: expected[path]})


@pytest.mark.parametrize("change", ["missing", "extra", "preimage", "authority"])
def test_issue_transition_exact_inventory(change: str) -> None:
    record = json.loads((ROOT / ISSUE_BINDING).read_text())
    before = {p: t["before"] for p, t in record["replacements"].items()}
    if change == "missing":
        record["additions"].pop("validation/component/issue_checks.py")
    elif change == "extra":
        record["replacements"]["unexpected.py"] = dict(before="0" * 64, after="1" * 64)
    elif change == "preimage":
        record["replacements"][ADR]["before"] = "0" * 64
    else:
        record["authority"] = "manufactured"
    with pytest.raises(AssertionError):
        issue_bindings(ROOT, before, record)


@pytest.mark.parametrize(
    "path",
    ["validation/component/issue_checks.py", "validation/component/installation_identity.py"],
)
def test_issue_checker_and_identity_helper_are_bound(tmp_path: Path, path: str) -> None:
    expected = installation_bindings(ROOT, json.loads((ROOT / SELECTION).read_text()))
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / path).read_bytes() + b"\n# changed\n")
    with pytest.raises(AssertionError, match="installed postimage"):
        verify_postimages(tmp_path, {path: expected[path]})
