"""Recovery equivalence and refusals on already completed small suite cases."""

import gzip
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "validation/L3_silicon/tpu-v5e"
UTILITY = BASE / "freeze/recovery.py"


@pytest.fixture
def helper(monkeypatch):
    monkeypatch.syspath_prepend(str(UTILITY.parent))
    return runpy.run_path(str(UTILITY))


@pytest.mark.native
@pytest.mark.parametrize("case", ["matrix-bf16-01", "matrix-int8-01"])
def test_recovery_matches_surviving_canonical_content(tmp_path, case):
    executable = Path(os.environ.get("REFERENCE_NATIVE", "unconfigured"))
    if not executable.is_file():
        pytest.skip("set REFERENCE_NATIVE to the reconstructed release executable")
    old = json.loads((BASE / "predictions" / (case + ".json")).read_text())
    environment = tmp_path / "environment.json"
    environment.write_text(json.dumps(old["provenance"]))
    out = tmp_path / "predictions"
    command = [
        sys.executable,
        str(UTILITY),
        "run",
        "--id",
        case,
        "--source",
        os.environ.get("U5_RECOVERY_SOURCE", str(ROOT)),
        "--work",
        str(tmp_path / "work"),
        "--out",
        str(out),
        "--environment",
        str(environment),
        "--executable",
        str(executable),
        "--journal",
        str(tmp_path / "performance.jsonl"),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    new = json.loads((out / (case + ".json")).read_text())
    for name, ref in old["artifacts"].items():
        assert gzip.decompress(
            (BASE / "predictions" / ref["path"]).read_bytes()
        ) == gzip.decompress((out / new["artifacts"][name]["path"]).read_bytes())
    assert {k: v for k, v in new.items() if k not in ("provenance", "artifacts")} == {
        k: v for k, v in old.items() if k not in ("provenance", "artifacts")
    }
    replay = subprocess.run(
        [
            sys.executable,
            str(BASE / "freeze/replay_without_producers.py"),
            str(out / (case + ".json")),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert replay.returncode == 0, replay.stderr
    events = [
        json.loads(line) for line in (tmp_path / "performance.jsonl").read_text().splitlines()
    ]
    assert events[-1]["status"] == "complete"
    assert len([r for r in events if r["event"] == "python_worker_rss"]) == 8
    assert len([r for r in events if r["event"] == "native_rss"]) == 1
    again = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert again.returncode != 0 and "nonempty" in again.stderr


def test_recovery_retains_input_and_output_refusals(tmp_path, helper, monkeypatch):
    from uarch_contract.reference_json import canonical_json, content_hash

    from rkuarch.engines.native import transport

    old = json.loads((BASE / "predictions/matrix-bf16-01.json").read_text())
    job = gzip.decompress(
        (BASE / "predictions" / old["artifacts"]["prepared_job"]["path"]).read_bytes()
    )
    result = gzip.decompress(
        (BASE / "predictions" / old["artifacts"]["native_output"]["path"]).read_bytes()
    )
    args = SimpleNamespace(
        id="matrix-bf16-01",
        case=tmp_path,
        journal=tmp_path / "performance.jsonl",
        executable=Path("/bin/true"),
    )
    (tmp_path / "job.json").write_bytes(job + b"\n")
    with pytest.raises(ValueError, match="canonical saved job"):
        helper["validate_input"](args)
    (tmp_path / "job.json").write_bytes(job)
    helper["validate_input"](args)
    metadata = (tmp_path / "job-summary.json").read_bytes()
    bad = json.loads(result)
    bad["counts"]["matrix_ops"] += 1
    bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
    refusal = canonical_json(
        dict(code="UnsupportedScope", message="test refusal", pointer=None)
    ).encode()
    faults = [
        (canonical_json(bad).encode(), b"", 0),
        (result + b"\n", b"", 0),
        (result, b"bad", 0),
        (b"", refusal, 2),
    ]
    for i, payload in enumerate(faults):
        args.case = tmp_path / str(i)
        args.case.mkdir()
        (args.case / "job.json").write_bytes(job)
        (args.case / "job-summary.json").write_bytes(metadata)
        monkeypatch.setattr(transport, "_exchange", lambda *a, value=payload, **kw: value)
        helper["native"](args)
        if i == 0:
            helper["validate_output"](args)
            with pytest.raises(ValueError):
                helper["independent_check"](args)
        else:
            with pytest.raises(transport.NativeRefusal if i == 3 else ValueError):
                helper["validate_output"](args)
    assert not (tmp_path / "matrix-bf16-01.json").exists()


def test_recovery_refuses_low_headroom_before_workers(tmp_path, helper, monkeypatch):
    args = SimpleNamespace(
        id="test",
        case=tmp_path / "work",
        out=tmp_path / "out",
        journal=tmp_path / "performance.jsonl",
        min_available_gib=10,
    )
    monkeypatch.setitem(
        helper["run_case"].__globals__, "memory", lambda: dict(MemAvailable=1024, swap_used_bytes=0)
    )
    with pytest.raises(RuntimeError, match="resource preflight"):
        helper["run_case"](args)
    events = [json.loads(line) for line in args.journal.read_text().splitlines()]
    assert events[-1]["status"] == "failure"
    assert not list(args.case.iterdir())


def test_recovery_refuses_changed_saved_input_before_workers(tmp_path, helper):
    saved = tmp_path / "saved.json"
    saved.write_bytes(b"changed after inspection")
    args = SimpleNamespace(
        id="matrix-bf16-01",
        case=tmp_path / "work",
        out=tmp_path / "out",
        journal=tmp_path / "performance.jsonl",
        min_available_gib=0,
        prepared_job=saved,
        prepared_job_sha256="sha256:" + "0" * 64,
        preparation_generator_sha256="sha256:" + "1" * 64,
    )
    with pytest.raises(ValueError, match="reused prepared input hash mismatch"):
        helper["run_case"](args)
    events = [json.loads(line) for line in args.journal.read_text().splitlines()]
    assert events[-1]["status"] == "failure"
    assert not any(r["event"] == "worker_start" for r in events)
    assert not (args.case / "job.json").exists()
