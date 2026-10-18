"""Prospective expectation transitions preserve old inputs and evidence."""

import json
from copy import deepcopy

import pytest

from native.tools.component_stage2_inputs import transition_negatives


def test_only_identity_transition_preserves_inherited_expectation(tmp_path):
    import hashlib

    def raw(v):
        return json.dumps(v, sort_keys=True, separators=(",", ":")).encode()

    old, new = tmp_path / "old", tmp_path / "new"
    for root in (old, new):
        (root / "private-component/jobs").mkdir(parents=True)
        (root / "native").mkdir()
        (root / "native/guard.rs").write_bytes(b"unchanged guard")
    job = {"engine": {"implementation_hash": "old"}, "job_hash": "old", "body": "finite"}
    current = dict(job, engine={"implementation_hash": "new"}, job_hash="new")
    (old / "private-component/jobs/case.json").write_bytes(raw(job))
    (new / "private-component/jobs/case.json").write_bytes(raw(current))
    expected = {
        "format": "component-negative-expectations/1",
        "rows": [
            {
                "case_id": "case",
                "input_sha256": hashlib.sha256(raw(job)).hexdigest(),
                "job_hash": "old",
                "engine": job["engine"],
                "envelope": {"code": "CapacityExceeded", "message": "finite", "pointer": None},
                "native_guard_source": {
                    "path": "native/guard.rs",
                    "sha256": hashlib.sha256(b"unchanged guard").hexdigest(),
                },
                "observed": {"attribution": "inherited; no new execution"},
            }
        ],
    }
    preserved = deepcopy(expected)
    result = transition_negatives(new, old, expected)
    assert expected == preserved
    row = result["rows"][0]
    assert row["historical_expectation"] == preserved["rows"][0]
    assert row["input_sha256"] == hashlib.sha256(raw(current)).hexdigest()
    assert row["engine"] == current["engine"]
    assert row["observed"] == preserved["rows"][0]["observed"]
    current["body"] = "different guard input"
    (new / "private-component/jobs/case.json").write_bytes(raw(current))
    with pytest.raises(ValueError, match="identity-only transition"):
        transition_negatives(new, old, expected)
