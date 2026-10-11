"""Fresh companion closure and exact current imported bytes; reviews are synthetic tests only."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json

from tests.integration.test_u2_a_replay import captured, companions


def cli(*args, env=None):
    return subprocess.run(
        [sys.executable, "-B", "-m", "rkuarch.cli", *map(str, args)],
        env=env or dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=".:contract:src"),
        capture_output=True,
    )


def fresh_inputs(tmp_path):
    c = captured()
    context, card, store = companions(c)
    artifacts = tmp_path / "fresh-companions"
    artifacts.mkdir()
    for identity, value in store.items():
        (artifacts / (identity[7:] + ".json")).write_text(canonical_json(value))
    for name, value in {
        "prepared": c.bundle,
        "intent": c.bundle.intent,
        "hardware": c.bundle.hardware_spec,
        "assumptions": c.assumptions,
        "context": context,
        "card": card,
    }.items():
        (tmp_path / (name + ".json")).write_text(canonical_json(value))
    assert not (artifacts / (c.bundle.intent.hardware_spec_hash[7:] + ".json")).exists()
    options = [
        "--assumptions",
        tmp_path / "assumptions.json",
        "--context",
        tmp_path / "context.json",
        "--model-card",
        tmp_path / "card.json",
        "--artifact-dir",
        artifacts,
    ]
    return c, options


@pytest.mark.parametrize("route", ["intent", "prepared"])
def test_table_indexes_own_hardware_in_fresh_companions(tmp_path, route):
    c, options = fresh_inputs(tmp_path)
    route_args = (
        [tmp_path / "hardware.json", "--intent", tmp_path / "intent.json"]
        if route == "intent"
        else ["--prepared-input", tmp_path / "prepared.json"]
    )
    output = tmp_path / "result/table.json"
    result = cli("table", *route_args, *options, "--output", output)
    assert result.returncode == 0, result.stderr.decode()
    from rkuarch.table.artifacts import load_verified_report_inputs

    verified = load_verified_report_inputs(output)
    assert verified.hardware == c.bundle.hardware_spec
    assert verified.results == c.results
    assert verified.table.rows[0].counts.matrix_ops == 1184


@pytest.mark.parametrize("route", ["intent", "prepared"])
def test_fresh_companions_do_not_allow_wrong_positional_spec(tmp_path, route):
    _, options = fresh_inputs(tmp_path)
    path = tmp_path / "hardware.json"
    raw = json.loads(path.read_text())
    raw["memory"]["dram"]["bw_bytes_per_s"]["value"] *= 2
    path.write_text(canonical_json(raw))
    output = tmp_path / "refused/table.json"
    if route == "prepared":
        from uarch_contract.hashing import content_hash

        prepared = json.loads((tmp_path / "prepared.json").read_text())
        prepared["hardware_spec"] = raw
        prepared["bundle_hash"] = content_hash(prepared, exclude=("bundle_hash",))
        path = tmp_path / "wrong-prepared.json"
        path.write_text(canonical_json(prepared))
        route_args = ["--prepared-input", path]
    else:
        route_args = [path, "--intent", tmp_path / "intent.json"]
    result = cli("table", *route_args, *options, "--output", output)
    assert result.returncode != 0
    assert "SpecHashMismatch" in result.stderr.decode()
    assert not output.exists()


def test_current_import_exact_bytes_without_preparation(tmp_path):
    import hashlib

    root = Path(__file__).resolve().parents[2]
    fixture = root / "tests/fixtures/u2_a/current-import/prepared.json"
    assumptions = fixture.with_name("assumptions.json")
    before = fixture.read_bytes()
    assert hashlib.sha256(before).hexdigest() == CURRENT_IMPORT_SHA256
    trap = tmp_path / "trap"
    trap.mkdir()
    (trap / "sitecustomize.py").write_text(
        "import sys\n"
        "class Trap:\n"
        " def find_spec(self, fullname, path=None, target=None):\n"
        "  if fullname == 'rkuarch.workload.prepare' or fullname == 'rk':\n"
        "   raise RuntimeError('PREPARATION_IMPORT_BLOCKED:' + fullname)\n"
        "sys.meta_path.insert(0, Trap())\n"
    )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{trap}:.:contract:src")
    result = cli(
        "capture",
        "--prepared-input",
        fixture,
        "--assumptions",
        assumptions,
        "--output",
        tmp_path / "captured",
        env=env,
    )
    assert result.returncode == 0, result.stderr.decode()
    values = [json.loads(p.read_text()) for p in (tmp_path / "captured").glob("*.json")]
    results = [v for v in values if "result_hash" in v and "counts" in v]
    assert len(results) == 2
    assert sorted(
        tuple(
            r["counts"][n]
            for n in ("matrix_ops", "vector_ops", "memory_read_bytes", "memory_write_bytes")
        )
        for r in results
    ) == [(672, 252, 1040, 288), (1184, 572, 1296, 288)]
    decode = next(r for r in results if r["counts"]["matrix_ops"] == 1184)
    assert decode["duration_ps"] == 1892000 and decode["u_c0_duration_ps"] == 1584000
    assert fixture.read_bytes() == before
    control = cli(
        "prepare",
        root / "hw/designs/npu-l4.yaml",
        "--model",
        "llama-3.1-8b",
        "--precision",
        "bf16",
        "--output",
        tmp_path / "forbidden.json",
        env=env,
    )
    assert control.returncode != 0 and b"PREPARATION_IMPORT_BLOCKED" in control.stderr


def test_current_import_rehashed_wrong_engine_version_refuses(tmp_path):
    from uarch_contract.hashing import content_hash

    root = Path(__file__).resolve().parents[2] / "tests/fixtures/u2_a/current-import"
    assumptions = json.loads((root / "assumptions.json").read_text())
    assumptions["model"]["version"] = "not-current"
    assumptions["assumptions_hash"] = content_hash(assumptions, exclude=("assumptions_hash",))
    raw = json.loads((root / "prepared.json").read_text())
    raw["intent"]["assumptions_hash"] = assumptions["assumptions_hash"]
    raw["intent_hash"] = content_hash(raw["intent"])
    raw["bundle_hash"] = content_hash(raw, exclude=("bundle_hash",))
    path = tmp_path / "wrong-engine.json"
    path.write_text(canonical_json(raw))
    result = cli("characterize", "--prepared-input", path, "--output", tmp_path / "refused.json")
    assert result.returncode != 0 and b"AssumptionMismatch" in result.stderr
    assert not (tmp_path / "refused.json").exists()


CURRENT_IMPORT_SHA256 = "c12914834103e19dd59bda714b3b832464d6333e19b412e60e8b2dd5481974fc"
