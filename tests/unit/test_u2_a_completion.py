"""Independent acceptance for A3-C1/C2; no reference drafts or B report implementation."""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import typer
import yaml
from uarch_contract.hashing import canonical_json, sha256

from tests.unit.test_u2_a_shapes import inputs, prepare

ROOT = Path(__file__).resolve().parents[2]


def cli(*args, seed="1"):
    return subprocess.run(
        [sys.executable, "-B", "-m", "rkuarch.cli", *map(str, args)],
        capture_output=True,
        env=dict(
            os.environ,
            PYTHONPATH="contract:src",
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONHASHSEED=seed,
            OMP_NUM_THREADS=seed,
        ),
    )


def hardware():
    # Independently authored tiny hardware fixture has49 sourced leaves, all initially stub.
    value = json.loads((ROOT / "contract/tests/fixtures/u2/independent-bundle.json").read_text())[
        "hardware_spec"
    ]
    value["design_status"] = "proposed"
    value["clock_domains"]["core"]["freq_hz"].update(
        provenance="spec_derived", source="https://example.test/synthetic-clock", date="2026-01-01"
    )
    value["cores"]["grid"]["rows"].update(
        kind="stipulation",
        provenance=None,
        source=None,
        date=None,
        rationale="Synthetic design choice for this test.",
    )
    return value


def test_cli_uses_required_typer_framework():
    assert isinstance(importlib.import_module("rkuarch.cli").app, typer.Typer)


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
def test_validate_lists_disjoint_categories_and_exact_paths(tmp_path, suffix):
    value = hardware()
    path = tmp_path / ("hardware" + suffix)
    path.write_text(json.dumps(value) if suffix == ".json" else yaml.safe_dump(value))
    p = cli("validate", path)
    assert p.returncode == 0, p.stderr.decode()
    text = p.stdout.decode()
    assert "Sourced values: 49" in text
    assert "Claims: 48 (including 47 stubs)" in text
    assert "Stipulations: 1" in text
    assert "Non-stub claims (1)" in text and "Stubs (47)" in text
    assert "clock_domains.core.freq_hz" in text and "https://example.test/synthetic-clock" in text
    assert "cores.grid.rows" in text and "Synthetic design choice for this test." in text
    assert "nocs[0].link_bytes_per_cycle" in text
    assert "spec_derived" in text
    assert cli("validate", path, seed="4").stdout == p.stdout


@pytest.mark.parametrize(
    "mutation,path",
    [
        ("reference", "cores.grid.rows"),
        ("unit", "clock_domains.core.freq_hz"),
        ("source", "clock_domains.core.freq_hz"),
        ("rationale", "cores.grid.rows"),
        ("negative", "memory.dram.capacity_bytes"),
        ("missing", "clock_domains.core.freq_hz"),
    ],
)
def test_validate_invalid_specs_fail_with_offending_path(tmp_path, mutation, path):
    value = hardware()
    if mutation == "reference":
        value["design_status"] = "reference"
    elif mutation == "unit":
        value["clock_domains"]["core"]["freq_hz"]["unit"] = "byte"
    elif mutation == "source":
        value["clock_domains"]["core"]["freq_hz"]["source"] = None
    elif mutation == "rationale":
        value["cores"]["grid"]["rows"]["rationale"] = ""
    elif mutation == "negative":
        value["memory"]["dram"]["capacity_bytes"]["value"] = -1
    else:
        del value["clock_domains"]["core"]["freq_hz"]
    spec = tmp_path / "bad.yaml"
    spec.write_text(yaml.safe_dump(value))
    p = cli("validate", spec)
    assert p.returncode == 2
    assert path in p.stderr.decode()
    assert not p.stdout and "Traceback" not in p.stderr.decode()


def test_validate_reference_claims_only_and_malformed_input(tmp_path):
    value = json.loads((ROOT / "contract/tests/fixtures/u2/independent-bundle.json").read_text())[
        "hardware_spec"
    ]
    value["design_status"] = "reference"  # Synthetic claims-only input, not a B draft.
    path = tmp_path / "reference.json"
    path.write_text(json.dumps(value))
    p = cli("validate", path)
    assert p.returncode == 0, p.stderr.decode()
    assert "Stipulations: 0" in p.stdout.decode()
    path.write_text('{"id":"one","id":"two"}')
    p = cli("validate", path)
    assert p.returncode == 2 and b"DuplicateJsonKey" in p.stderr
    broken = tmp_path / "broken.yaml"
    broken.write_text("x: [\n")
    p = cli("validate", broken)
    assert p.returncode == 2 and b"Traceback" not in p.stderr


def prepared_path(tmp_path):
    i, hw = inputs()
    b = prepare(i, hw)
    path = tmp_path / "prepared.json"
    path.write_text(canonical_json(b))
    return path


def test_characterize_twin_uses_same_capture_and_exact_literals(tmp_path):
    source = prepared_path(tmp_path)
    out = tmp_path / "selection.json"
    p = cli("characterize", "--prepared-input", source, "--output", out)
    assert p.returncode == 0, p.stderr.decode()
    report = json.loads(out.read_bytes())
    md = out.with_suffix(".md")
    assert md.is_file()
    text = md.read_text()
    assert "Workload selection" in text and "unvalidated" in text
    assert sha256(out.read_bytes()) in text
    assert report["prepared_bundle_hash"] in text and report["request_hash"] in text
    assert set(report) == {"capacity", "jobs", "results", "prepared_bundle_hash", "request_hash"}
    for job, result in zip(report["jobs"], report["results"], strict=True):
        assert job["job_hash"] in text and result["result_hash"] in text
        assert job["hardware"]["hardware_spec_hash"] in text
        assert job["point_hash"] in text and job["engine"]["model"]["implementation_hash"] in text
        for omission in job["point"]["graph"]["omissions"]:
            assert omission in text
        for op in result["per_op"]:
            assert op["id"] in text and op["scope"]["op_class"] in text
            for v in op["counts"].values():
                assert str(v) in text
    assert "| 1184.0 | 572.0 | 1296.0 | 288.0 | 1892000.0 |" in text
    assert "total_context_tokens" in text and "prompt_tokens" in text
    assert "Array fill" in text and "Intensity regime" in text and "Dimensions" in text
    assert "unknown" in text and "Energy: unverified" in text
    before = (out.read_bytes(), md.read_bytes())
    p = cli("characterize", "--prepared-input", source, "--output", out, seed="4")
    assert p.returncode == 0, p.stderr.decode()
    assert before == (out.read_bytes(), md.read_bytes())


@pytest.mark.parametrize("conflict", ["json", "markdown", "alias"])
def test_characterize_conflicts_do_not_write_either_output(tmp_path, conflict):
    source = prepared_path(tmp_path)
    out = tmp_path / ("selection.md" if conflict == "alias" else "selection.json")
    md = out.with_suffix(".md")
    if conflict != "alias":
        (out if conflict == "json" else md).write_bytes(b"KEEP\n")
    p = cli("characterize", "--prepared-input", source, "--output", out)
    assert p.returncode == 2 and b"OutputConflict" in p.stderr
    if conflict == "alias":
        assert not out.exists()
    else:
        preserved, absent = (out, md) if conflict == "json" else (md, out)
        assert preserved.read_bytes() == b"KEEP\n" and not absent.exists()


def test_h2_70b_fp8_twin_determinism_and_scope(tmp_path):
    outputs = []
    for seed in ("1", "4"):
        out = tmp_path / seed / "characterize.json"
        p = cli(
            "characterize",
            ROOT / "hw/designs/npu-m256.yaml",
            "--model",
            "llama-3.1-70b",
            "--precision",
            "fp8",
            "--tp",
            "8",
            "--synthetic-assignment",
            "--output",
            out,
            seed=seed,
        )
        assert p.returncode == 0, p.stderr.decode()
        outputs.append((out.read_bytes(), out.with_suffix(".md").read_bytes()))
    assert outputs[0] == outputs[1]
    result = json.loads(outputs[0][0])
    md = outputs[0][1].decode()
    assert len(result["results"]) == 2
    q = next(o for o in result["results"][0]["per_op"] if o["id"] == "decoder-0/q_projection")
    assert q["counts"]["matrix_ops"] == 1342177280  # 2*8192*1024*80 layers
    assert "1342177280.0" in md and "fp8" in md and "tp=8" in md
    assert result["capacity"][0]["total_peak_bytes"] is None


def test_normal_model_tp_inventory_has_logical_vocab_slots():
    # Accepted matrix TP1/8 plus adjacent TP2/4: logical geometry only, not execution coverage.
    for name in ("llama-3.1-8b", "llama-3.1-70b", "mixtral-8x7b"):
        value = json.loads((ROOT / f"contract/fixtures/model_shapes/{name}.json").read_text())
        for tp in (1, 2, 4, 8):
            width = (value["shape"]["vocab_size"] + tp - 1) // tp
            assert all(value["shape"]["vocab_size"] - rank * width > 0 for rank in range(tp))


@pytest.mark.parametrize(
    "command", ["prepare", "capture", "table", "characterize", "rk-component", "validate"]
)
def test_typer_dispatch_preserves_command_help(command):
    p = cli(command, "--help")
    assert p.returncode == 0, p.stderr.decode()
    assert command in p.stdout.decode().lower()


def test_characterize_refuses_output_symlink_without_following_it(tmp_path):
    source = prepared_path(tmp_path)
    out = tmp_path / "selection.json"
    protected = tmp_path / "protected.txt"
    protected.write_bytes(b"KEEP\n")
    out.with_suffix(".md").symlink_to(protected)
    p = cli("characterize", "--prepared-input", source, "--output", out)
    assert p.returncode == 2 and b"OutputConflict" in p.stderr
    assert protected.read_bytes() == b"KEEP\n" and not out.exists()
