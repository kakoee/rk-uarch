"""Exact CI-C1 identity transition; no authority, optional fallback or current-hash adoption.

The external proposal pins installation-binding.json; that record pins this helper and
all changed tests. The code never embeds that record's digest: the hash graph is acyclic.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

ADR = "docs/decisions/U0011-the-native-engine-core.md"
SELF_TEST = "validation/component/test_stage2_selection.py"
F5_TEST = "validation/component/test_f5_mechanism_duration.py"
BINDING = "validation/component/installation-binding.json"
SELECTION = "docs/reviews/U4-B-component-stage2-v1/execution-selection.json"
SELECTION_SHA = "a8b94f0d83f429e5101b2b62ba5ed91d9b98d0d228330f5185acc37aab29319c"
OLD_ADR = "4f7a90b201c0425a9906d746e4235ec4df362c15ffe91138f827edf2529f6140"
NEW_ADR = "edf565f9094c524b280888feaf29bcecc63b176aa573393c136b3494c7c640fd"
OLD_TEST = "b7fb959ee27df2542c8bb60e13b3932a1218257e28610bc603d980da1d167d95"
F5_SHA = "e4f9f8693f20031ccf8b97d24a141b0aa63725e220fb6a754d2275cb5c6b0f8a"
INSTALLED_BYTES = 32221
INSTALLED_SHA = "afae0ebea7dfdfe761ec76ae374a35441db989f866a4ca4f5c29f0169a49e69b"
COMPONENT_SHA = "ad9b5369073403fa8a881a04e628db620c89f21d66ec062e90c3bc753c7eadba"
ADDITIONS = {
    F5_TEST,
    "validation/component/installation_identity.py",
    "validation/component/test_installation_identity.py",
    "validation/component/transient_carrier.py",
    "validation/component/test_transient_lifetime.py",
}

ISSUE_BINDING = "validation/component/issue-amendment-binding.json"
ISSUE_BASE_SHA = "a1d6ac18f52295aaf63a6c23b2dbf4815a8bfbef437c2e67782463a7e05f4f8b"
ISSUE_ADR_SHA = "79ec2b939d5cdd02905861c03e1a8f32733648f47cfbb4db2d1d477dd0a414a7"
ISSUE_APPENDIX_SHA = "b6f868c5dcd7ee610d85da2396bb5f617687fc8dbb0aa6f84941d62f6a057247"
ISSUE_ADR_BYTES = 67486
ISSUE_REPLACEMENTS = {
    "docs/decisions/U0011-the-native-engine-core.md",
    "validation/component/test_installation_identity.py",
    "contract/schema/mapped/MappedEngineJob.json",
    "contract/schema/mapped/MappedEngineResult.json",
    "contract/uarch_contract/mapped.py",
    "validation/component/installation_identity.py",
}
ISSUE_ADDITIONS = {
    "contract/tests/mapped/test_component_capacity_integration_v3.py",
    "contract/tests/mapped/fixtures/issue_capacity/sr2-v3-job.json",
    "contract/tests/mapped/fixtures/issue_capacity/sr2-v3-result.json",
    "contract/tests/mapped/test_component_credit_cursor_v3.py",
    "validation/component/issue_checks.py",
    "validation/component/test_issue_checks.py",
    "contract/tests/mapped/test_component_issue_v3.py",
    "validation/component/transition_checks_v3.py",
    "contract/uarch_contract/mapped_issue.py",
    "validation/component/observations_v3.py",
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_adr(raw: bytes) -> None:
    assert digest(raw[:INSTALLED_BYTES]) == INSTALLED_SHA, "installed K2 ADR prefix"
    assert digest(raw[INSTALLED_BYTES:48294]) == COMPONENT_SHA, "reviewed component suffix"
    assert len(raw) == ISSUE_ADR_BYTES, "exact issue ADR length"
    assert digest(raw[48294:]) == ISSUE_APPENDIX_SHA, "reviewed issue appendix"
    assert digest(raw) == ISSUE_ADR_SHA, "exact issue ADR"


def installation_bindings(
    root: Path, selection: dict[str, Any], record: Any = None
) -> dict[str, str]:
    raw_selection = (root / SELECTION).read_bytes()
    assert digest(raw_selection) == SELECTION_SHA, "historical selection bytes"
    assert json.loads(raw_selection) == selection, "historical selection value"
    if record is None:
        record = json.loads((root / BINDING).read_text())
    assert record["format"] == "component-installation-binding/1"
    assert record["historical_selection_sha256"] == SELECTION_SHA
    assert record["authority"] is None
    expected = {row["path"]: row["postimage_sha256"] for row in selection["candidate_files"]}
    assert len(expected) == len(selection["candidate_files"]) == 23, "candidate inventory"
    replacements = record["replacements"]
    assert set(replacements) == {ADR, SELF_TEST}, "exact transition inventory"
    assert replacements[ADR] == dict(before=OLD_ADR, after=NEW_ADR), "exact ADR transition"
    assert replacements[SELF_TEST]["before"] == OLD_TEST, "historical identity test"
    for path, transition in replacements.items():
        assert expected[path] == transition["before"], "transition preimage"
        expected[path] = transition["after"]
    additions = record["additions"]
    assert set(additions) == ADDITIONS, "exact added inventory"
    assert additions[F5_TEST] == F5_SHA, "reviewed F5 identity"
    assert not (set(additions) & set(expected)), "duplicate added path"
    expected.update(additions)
    assert all(
        len(value) == 64 and all(c in "0123456789abcdef" for c in value)
        for value in expected.values()
    ), "SHA256 shape"
    expected = issue_bindings(root, expected)
    verify_adr((root / ADR).read_bytes())
    return expected


def verify_postimages(root: Path, expected: dict[str, str]) -> None:
    for path, value in expected.items():
        assert digest((root / path).read_bytes()) == value, f"installed postimage: {path}"


def issue_bindings(root: Path, expected: dict[str, str], record: Any = None) -> dict[str, str]:
    """Required prospective overlay; original installation record remains byte frozen."""
    assert digest((root / BINDING).read_bytes()) == ISSUE_BASE_SHA, "historical binding bytes"
    if record is None:
        record = json.loads((root / ISSUE_BINDING).read_text())
    assert record["format"] == "component-issue-amendment-binding/1"
    assert record["authority"] is None
    assert record["base_binding_sha256"] == ISSUE_BASE_SHA
    assert set(record["replacements"]) == ISSUE_REPLACEMENTS, "exact issue replacements"
    assert set(record["additions"]) == ISSUE_ADDITIONS, "exact issue additions"
    output = dict(expected)
    for path, transition in record["replacements"].items():
        assert output[path] == transition["before"], "issue transition preimage"
        output[path] = transition["after"]
    assert output[ADR] == ISSUE_ADR_SHA, "exact issue ADR transition"
    assert not (set(output) & set(record["additions"])), "issue duplicate addition"
    output.update(record["additions"])
    assert all(len(v) == 64 and all(c in "0123456789abcdef" for c in v) for v in output.values()), (
        "issue SHA256 shape"
    )
    return output
