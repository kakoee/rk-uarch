"""Preserve exact historical bindings while checking the declared current transition."""

import json
from pathlib import Path

import pytest

from tests.component_current_identity import RECORD, current_test_bindings
from validation.component.installation_identity import (
    SELECTION,
    installation_bindings,
    verify_postimages,
)

ROOT = Path(__file__).resolve().parents[2]


def installed():
    return installation_bindings(ROOT, json.loads((ROOT / SELECTION).read_bytes()))


def test_current_transition_preserves_historical_and_detects_checker_edit(tmp_path):
    old = installed()
    path = "validation/component/observations_v3.py"
    with pytest.raises(AssertionError, match="installed postimage"):
        verify_postimages(ROOT, {path: old[path]})
    new = current_test_bindings(ROOT, old)
    assert old[path] != new[path]
    verify_postimages(ROOT, new)
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / path).read_bytes() + b"\n# changed\n")
    with pytest.raises(AssertionError, match="installed postimage"):
        verify_postimages(tmp_path, {path: new[path]})


@pytest.mark.parametrize("fault", ["missing", "extra", "preimage", "authority", "base"])
def test_transition_refuses_undeclared_changes(tmp_path, fault):
    record = json.loads((ROOT / RECORD).read_bytes())
    path = "validation/component/observations_v3.py"
    if fault == "missing":
        del record["replacements"][path]
    elif fault == "extra":
        record["replacements"]["arbitrary.py"] = record["replacements"][path]
    elif fault == "preimage":
        record["replacements"][path]["before"] = "0" * 64
    elif fault == "authority":
        record["authority"] = "not permitted"
    else:
        record["base_binding_sha256"] = "0" * 64
    destination = tmp_path / RECORD
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(record))
    base = tmp_path / "validation/component/issue-amendment-binding.json"
    base.parent.mkdir(parents=True)
    base.write_bytes((ROOT / base.relative_to(tmp_path)).read_bytes())
    with pytest.raises(AssertionError):
        current_test_bindings(tmp_path, installed())
