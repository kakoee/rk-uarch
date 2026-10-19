"""Explicit test-only transition from installed /3 semantics to the Stage 2 checker.

Historical installation records remain immutable. This record grants no execution
or installation authority and does not update any published runtime consumer pins.
"""

import json
from pathlib import Path

from validation.component.installation_identity import digest

RECORD = "tests/fixtures/component_current_identity.json"
REPLACEMENTS = {
    "validation/component/observations_v3.py",
    "validation/component/test_installation_identity.py",
    "validation/component/test_stage2_selection.py",
}
ADDITIONS = {
    "tests/component_current_identity.py",
    "tests/unit/test_component_current_identity.py",
}


def current_test_bindings(root: Path, installed: dict[str, str]) -> dict[str, str]:
    record = json.loads((root / RECORD).read_bytes())
    assert record["format"] == "component-current-test-transition/1"
    assert record["authority"] is None
    base = root / "validation/component/issue-amendment-binding.json"
    assert digest(base.read_bytes()) == record["base_binding_sha256"], "installed binding bytes"
    assert set(record["replacements"]) == REPLACEMENTS, "exact test transition inventory"
    assert set(record["additions"]) == ADDITIONS, "exact test additions"
    expected = dict(installed)
    for path, row in record["replacements"].items():
        assert expected[path] == row["before"], "test transition preimage"
        expected[path] = row["after"]
    assert not (set(expected) & ADDITIONS), "duplicate test addition"
    expected.update(record["additions"])
    assert all(
        len(h) == 64 and all(c in "0123456789abcdef" for c in h) for h in expected.values()
    ), "test transition digest"
    return expected
