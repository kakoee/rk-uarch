"""Current candidate identity checks. Exclude these from behavioral mutation scores."""

import hashlib
import json
from pathlib import Path

from uarch_contract.hashing import content_hash

from tests.component_current_identity import current_test_bindings
from validation.component.installation_identity import installation_bindings, verify_postimages

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/reviews/U4-B-component-stage2-v1"


def test_current_selection_and_historical_mapping() -> None:
    s = json.loads((PACKAGE / "execution-selection.json").read_text())
    old = json.loads(
        (ROOT / "docs/reviews/U4-B-component-joins-v2/execution-selection.json").read_text()
    )
    assert s["selection_hash"] == content_hash(s, exclude=("selection_hash",))
    rows = {row["case_id"]: row for row in s["cases"]}
    assert len(rows) == 106
    for row in old["cases"]:
        assert rows[row["case_id"]] == row
    assert s["historical_selection_hash"] == old["selection_hash"]
    assert {row["old"]: row["new"] for row in s["old_to_new"]} == {
        row["case_id"]: row["case_id"] for row in old["cases"]
    }
    installed = current_test_bindings(ROOT, installation_bindings(ROOT, s))
    for path, digest in (s["checker_bindings"] | s["test_bindings"]).items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == installed.get(path, digest)
    for row in s["candidate_files"]:
        assert (
            hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == installed[row["path"]]
        )
    verify_postimages(ROOT, installed)
    for row in s["cases"]:
        assert row["native_status"] == "not_run"
        for key in ("engine_identity", "build_identity", "authority", "job_hash"):
            assert row[key] is None
        if "input_path" in row:
            assert (
                hashlib.sha256((ROOT / row["input_path"]).read_bytes()).hexdigest()
                == row["input_sha256"]
            )
