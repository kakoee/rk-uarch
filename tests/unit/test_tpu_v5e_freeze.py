"""Acceptance checks for the prediction-only U5 archive; never open silicon results."""

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "validation/L3_silicon/tpu-v5e"


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def test_exact_accepted_suite_and_provenance():
    rows = json.loads((BASE / "u4b/suite-proposed.json").read_text())["benchmarks"]
    files = sorted((BASE / "predictions").glob("*.json"))
    assert {p.stem for p in files} == {r["id"] for r in rows}
    assert len(files) == 52
    classes = Counter()
    used = set()
    for path in files:
        p = json.loads(path.read_text())
        classes[p["benchmark_class"]] += 1
        assert p["mapping_match"] == "compiler-chosen"
        assert p["initial_state"] == "steady"
        assert p["calibration"] == "stub" and p["error"] == "unknown"
        assert p["compiler_reported"] == {"status": "not_observed", "flops": None, "bytes": None}
        assert p["engine"]["version"] == "native-stage/3"
        assert p["provenance"]["image_digest"].startswith("sha256:")
        assert p["provenance"]["suite_sha256"] == sha(
            (BASE / "u4b/suite-proposed.json").read_bytes()
        )
        assert p["native"]["duration_ps"] > 0
        assert p["native"]["predicted_flops"] >= 0
        assert p["native"]["predicted_bytes"] > 0
        for mode in ("aggregate", "per_op"):
            assert p["u_c0"][mode]["duration_ps"] > 0
            assert p["u_c0"][mode]["predicted_flops"] >= 0
            assert p["u_c0"][mode]["predicted_bytes"] > 0
        used.update(p["native"]["consumed_stubs"])
    assert classes == {
        "matrix": 12, "memory": 9, "operator": 24, "end-to-end": 4,
        "DRAM gather": 2, "launch overhead": 1,
    }
    unknowns = (BASE / "predictions/UNKNOWNS.md").read_text()
    assert all(f"`{name}`" in unknowns for name in used)


def test_frozen_artifact_hashes_and_cross_bindings():
    files = sorted((BASE / "predictions").glob("*.json"))
    assert len(files) == 52
    for path in files:
        p = json.loads(path.read_text())
        objects = {}
        for name, ref in p["artifacts"].items():
            raw = (BASE / "predictions" / ref["path"]).read_bytes()
            assert sha(raw) == ref["sha256"]
            decoded = gzip.decompress(raw)
            assert sha(decoded) == ref["uncompressed_sha256"]
            objects[name] = json.loads(decoded)
        job, result = objects["prepared_job"], objects["native_output"]
        assert job["job_hash"] == result["job_hash"] == p["prepared_input"]["job_hash"]
        assert job["bundle_hash"] == result["bundle_hash"] == p["prepared_input"]["bundle_hash"]
        assert job["workload_closure"]["hardware_spec_hash"] == p["spec_hash"]
        assert result["duration_ps"] == p["native"]["duration_ps"]
        assert result["counts"] == p["native"]["counts"]
        assert result["consumed_stubs"] == p["native"]["consumed_stubs"]
        assert result["observations"]["format"] == "uarch-observations/4"
