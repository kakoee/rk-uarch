"""Archived selection input identities; current source bytes are not release gates."""

import hashlib
import json
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import MappedBundle, NativeTestProfile

from validation.component.corpus import manifest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/reviews/U4-B-component-joins-v2"


def test_exact_future_selection_and_historical_identity():
    selection = json.loads((PACKAGE / "execution-selection.json").read_text())
    assert selection["selection_hash"] == content_hash(selection, exclude=("selection_hash",))
    assert len(selection["cases"]) == 99
    historical = {x["case_id"]: x for x in manifest()["cases"]}
    rows = {x["case_id"]: x for x in selection["cases"]}
    for name, old in historical.items():
        assert all(rows[name][k] == v for k, v in old.items())
    for row in rows.values():
        assert row["native_status"] == "not_run"
        assert all(
            row[k] is None for k in ("job_hash", "engine_identity", "build_identity", "authority")
        )
        if "input_path" not in row:
            continue
        path = ROOT / row["input_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["input_sha256"]
        raw = json.loads(path.read_text())
        if "bundle" in raw:
            profile = NativeTestProfile.model_validate(raw["profile"])
            assert profile.profile_hash == row["profile_hash"]
            b = MappedBundle.model_validate(raw["bundle"])
        else:
            b = MappedBundle.model_validate(raw)
        assert b.bundle_hash == row["bundle_hash"]
        assert b.points[0].payload_hash == row["point_hash"]
        assert b.points[0].task_graph.graph_hash == row["graph_hash"]
    assert sum(r["expected_layer"] == "resource-preflight" for r in rows.values()) == 8
    assert sum(r["expected_layer"] == "profile" for r in rows.values()) == 4
    assert selection["obligations"]["native_calls_executed"] == 0
