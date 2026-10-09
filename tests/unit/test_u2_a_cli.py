"""CLI acceptance without oracle entry points or generated reference artifacts."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def cli(*args):
    return subprocess.run(
        [sys.executable, "-B", "-m", "rkuarch.cli", *map(str, args)],
        capture_output=True,
        env=dict(os.environ, PYTHONPATH="contract:src"),
    )


def test_named_model_characterize_h2_fp8(tmp_path):
    out = tmp_path / "characterize.json"
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
    )
    assert p.returncode == 0, p.stderr.decode()
    report = json.loads(out.read_bytes())
    assert len(report["results"]) == 2
    assert all(
        op["scope"]["intensity_regime"] in ("low", "middle", "high")
        for result in report["results"]
        for op in result["per_op"]
    )
    assert report["capacity"][0]["total_peak_bytes"] is None
    assert (
        cli(
            "characterize",
            ROOT / "hw/designs/npu-m256.yaml",
            "--model",
            "llama-3.1-70b",
            "--precision",
            "fp8",
            "--tp",
            "8",
            "--output",
            tmp_path / "refused.json",
        ).returncode
        != 0
    )


def test_actual_h1_export_preserves_accepted_bytes(tmp_path):
    p = cli(
        "rk-component",
        ROOT / "hw/designs/npu-l4.yaml",
        "--component-id",
        "compute.asic.npu-l4",
        "--execution-model",
        ROOT / "docs/reviews/U2-A-checkpoint-2/export/npu-l4.execution-model.json",
        "--oracle-compat",
        "--output",
        tmp_path,
    )
    assert p.returncode == 0, p.stderr.decode()
    assert (tmp_path / "oracle-compat.yaml").read_bytes() == (
        ROOT / "docs/reviews/U2-A-checkpoint-2/export/npu-l4.oracle-compat.yaml"
    ).read_bytes()
    assert (
        json.loads((tmp_path / "truth.json").read_bytes())["component_id"] == "compute.asic.npu-l4"
    )


def test_imported_input_rejects_even_zero_valued_override(tmp_path):
    p = cli(
        "prepare",
        "--prepared-input",
        ROOT / "contract/tests/fixtures/u2/independent-bundle.json",
        "--tp",
        "0",
        "--output",
        tmp_path / "bad.json",
    )
    assert p.returncode != 0
    assert not (tmp_path / "bad.json").exists()


@pytest.mark.parametrize(
    "model,ffn_ops,moe", [("llama-3.1-8b", 469762048, False), ("mixtral-8x7b", 939524096, True)]
)
def test_other_declared_model_sidecars_execute_independent_projection_counts(
    tmp_path, model, ffn_ops, moe
):
    out = tmp_path / "characterize.json"
    p = cli(
        "characterize",
        ROOT / "hw/designs/npu-m256.yaml",
        "--model",
        model,
        "--precision",
        "fp8",
        "--tp",
        "8",
        "--synthetic-assignment",
        "--output",
        out,
    )
    assert p.returncode == 0, p.stderr.decode()
    value = json.loads(out.read_bytes())
    by = {op["id"]: op for op in value["results"][0]["per_op"]}
    # 2*M1*K4096*N512 * 32 layers. FFN N1792, active experts1 or2.
    assert by["decoder-0/q_projection"]["counts"]["matrix_ops"] == 134217728
    assert by["decoder-0/ffn_up"]["counts"]["matrix_ops"] == ffn_ops
    assert any("MoE" in s for s in value["jobs"][0]["point"]["graph"]["omissions"]) is moe
