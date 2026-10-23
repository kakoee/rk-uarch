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
    expected = {r["id"]: r for r in rows}
    classes = Counter()
    used = set()
    for path in files:
        p = json.loads(path.read_text())
        classes[p["benchmark_class"]] += 1
        assert p["benchmark"] == expected[p["id"]]
        recovered = p["id"] in {
            "layer-b32-s1",
            "layer-b1-s128",
            "gather-p16-c2048",
            "gather-p32-c2048",
            "launch-minimal",
        }
        generator = "recovery.py" if recovered else "freeze.py"
        assert p["provenance"]["generator_sha256"] == sha(
            (BASE / "freeze" / generator).read_bytes()
        )
        if recovered:
            assert p["provenance"]["generator_helper_sha256"] == sha(
                (BASE / "freeze/freeze.py").read_bytes()
            )
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
        "matrix": 12,
        "memory": 9,
        "operator": 24,
        "end-to-end": 4,
        "DRAM gather": 2,
        "launch overhead": 1,
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
        closure = job["workload_closure"]
        assert closure["hardware_spec_hash"] == p["spec_hash"]
        assert closure["mapping_policy"] == p["mapping_policy"]
        assert closure["producer"] == p["prepared_input"]["producer"]
        assert closure["points"][0]["initial_state"] == p["initial_state"]
        assert closure["points"][0]["priming_iterations"] == 1
        assert p["native"]["predicted_bytes"] == (
            result["counts"].get("hbm_read_bytes", 0) + result["counts"].get("hbm_write_bytes", 0)
        )
        for mode in ("aggregate", "per_op"):
            for key in ("predicted_flops", "predicted_integer_ops", "predicted_bytes"):
                assert p["u_c0"][mode][key] == sum(r[key] for r in p["u_c0"]["ops"].values())
        assert p["native"]["predicted_flops"] == p["u_c0"]["aggregate"]["predicted_flops"]
        assert result["duration_ps"] == p["native"]["duration_ps"]
        assert result["counts"] == p["native"]["counts"]
        assert result["consumed_stubs"] == p["native"]["consumed_stubs"]
        assert result["observations"]["format"] == "uarch-native-observations/4"
        # Do not retain the previous large trace while loading the next archive.
        del job, result, closure, objects, decoded, raw


def test_raw_int8_is_not_reported_as_flops_and_archive_refuses_overwrite(tmp_path):
    import runpy

    from rkuarch.workload.reference import matrix_source

    helper = runpy.run_path(str(BASE / "freeze/freeze.py"))
    for precision, flops, integer_ops in (("bf16", 32768, 0), ("int8", 0, 32768)):
        work = helper["semantic_work"](
            matrix_source(1, 128, 128, precision).model_dump(mode="json")
        )
        assert work["dot"]["predicted_flops"] == flops
        assert work["dot"]["predicted_integer_ops"] == integer_ops
    path = tmp_path / "immutable.json"
    helper["write_new"](path, b"original")
    import pytest

    with pytest.raises(FileExistsError):
        helper["write_new"](path, b"changed")
    assert path.read_bytes() == b"original"


def test_relocated_replay_with_producers_disabled_and_corrupt_archive(tmp_path):
    import shutil
    import subprocess
    import sys

    original = BASE / "predictions/matrix-bf16-01.json"
    prediction = tmp_path / original.name
    shutil.copyfile(original, prediction)
    p = json.loads(prediction.read_text())
    for ref in p["artifacts"].values():
        target = tmp_path / ref["path"]
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(original.parent / ref["path"], target)
    command = [sys.executable, str(BASE / "freeze/replay_without_producers.py"), str(prediction)]
    good = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert good.returncode == 0, good.stderr
    target = tmp_path / p["artifacts"]["prepared_job"]["path"]
    target.write_bytes(target.read_bytes() + b"corrupt")
    bad = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert bad.returncode != 0 and "archive hash mismatch" in bad.stderr
