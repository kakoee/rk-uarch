"""Independent synthetic binding/lifecycle controls; never an oracle run or adoption."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from contract.tests.historical_snapshot import historical_snapshot
from scripts import u2_inputs as ui
from scripts import vendor_rk as vr
from tests.unit.test_u2_b_tooling import synthetic_matrix


def rehash(root):
    files = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p != root / "MANIFEST.json"
    }
    (root / "MANIFEST.json").write_bytes(vr.snapshot_bytes(files, vr.PIN)["MANIFEST.json"])


def rehash_inputs(root):
    data = "".join(
        vr.digest(p.read_bytes()) + "  " + p.relative_to(root).as_posix() + "\n"
        for p in sorted(root.rglob("*"))
        if p.is_file() and p != root / "SHA256SUMS"
    )
    (root / "SHA256SUMS").write_text(data)
    return vr.digest(data.encode())


def strict(root):
    vr.check_manifest(root)
    vr.check_snapshot_inputs(root)
    vr.check_generator(root)


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    def denied(*a, **k):
        pytest.fail("oracle invoked in synthetic lifecycle check")

    from contract.tests import nominal_candidate as nominal
    from rkuarch.engines.analytic import core
    from rkuarch.table import build
    from rkuarch.workload import prepare as producer
    from rkuarch.workload import prepared

    monkeypatch.setattr(vr, "run_oracle", denied)
    monkeypatch.setattr(producer, "prepare", denied)
    monkeypatch.setattr(prepared, "execute_prepared_point", denied)
    monkeypatch.setattr(nominal, "evaluate_nominal", denied)
    monkeypatch.setattr(build, "capture", denied)
    monkeypatch.setattr(core, "run_analytic", denied)
    frozen = tmp_path / "inputs"
    inputs = ui.load_inputs(frozen, ui.prepare_inputs(frozen))
    root = tmp_path / "synthetic-candidate"
    shutil.copytree(historical_snapshot(), root)
    shutil.copytree(frozen, root / "u2-inputs")
    for name in vr.SOURCES:
        p = root / name
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"SYNTHETIC source control, not upstream evidence\n")
    for name in inputs.matrix:
        shutil.copyfile(frozen / "components" / name, root / "components" / name)
    (root / "parity/fixtures.json").write_bytes(vr.canonical(synthetic_matrix(inputs)))
    source = vr.digest((root / "rk/engine/f0/compute.py").read_bytes())
    refusals = [
        dict(
            component_params_file="components/" + name,
            compute=fmt,
            kv_cache=fmt,
            exception="UnsupportedPrecision",
            message="synthetic direct refusal",
            boundary="Accelerator.peak_op_per_s",
            callable_source_sha256=source,
        )
        for name, fmts in [
            ("asic_placeholder.yaml", ("bf16", "fp8")),
            ("npu-l4.yaml", ("fp16", "fp8")),
        ]
        for fmt in fmts
    ]
    (root / "parity/refusals.json").write_bytes(vr.canonical(refusals))
    metadata = json.loads((root / "GENERATOR.json").read_bytes())
    metadata.update(
        script_sha256=vr.digest(Path(vr.__file__).read_bytes()),
        oracle_program_sha256=vr.digest(vr.ORACLE_PROGRAM.encode()),
    )
    (root / "GENERATOR.json").write_bytes(vr.canonical(metadata))
    rehash(root)
    strict(root)
    return root


@pytest.mark.parametrize("attack", ["descriptor", "sidecar", "extra_component", "missing_sidecar"])
def test_rehashed_outer_copies_cannot_replace_frozen_inputs(candidate, attack):
    from contract.tests.test_committed_snapshot import (
        test_committed_manifest_matrix_and_component_provenance,
    )

    root = candidate
    rows = json.loads((root / "parity/fixtures.json").read_bytes())
    frozen_hash = vr.digest((root / "u2-inputs/SHA256SUMS").read_bytes())
    if attack == "descriptor":
        path = root / "components/npu-l4.yaml"
        data = yaml.safe_load(path.read_bytes())
        assert data["params"]["bf16_tflops"]["value"] == 524.288
        data["params"]["bf16_tflops"]["value"] = 1048.576
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        for row in rows:
            if row["component_params_file"] == "components/npu-l4.yaml":
                row["component_params_sha256"] = vr.digest(path.read_bytes())
    elif attack == "sidecar":
        path = root / "model_shapes/llama-3.1-8b.json"
        data = json.loads(path.read_bytes())
        data["sources"][0]["note"] = "substituted attribution, same numerical dimensions"
        path.write_bytes(vr.canonical(data))
        for row in rows:
            if row["model_id"] == data["id"]:
                row["model_sources"] = data["sources"]
    elif attack == "extra_component":
        (root / "components/extra.yaml").write_bytes(b"synthetic extra file")
    else:
        (root / "model_shapes/llama-3.1-8b.json").unlink()  # temporary synthetic control only
    (root / "parity/fixtures.json").write_bytes(vr.canonical(rows))
    rehash(root)
    vr.check_manifest(root)  # attacks deliberately repair the outer checksum layer
    assert vr.digest((root / "u2-inputs/SHA256SUMS").read_bytes()) == frozen_hash
    for check in [
        vr.check_snapshot_inputs,
        vr.check_generator,
        test_committed_manifest_matrix_and_component_provenance,
    ]:
        with pytest.raises(ValueError, match="frozen"):
            check(root)


def test_same_candidate_survives_adoption_and_fresh_layout(candidate, tmp_path, monkeypatch):
    original = {
        p.relative_to(candidate): p.read_bytes() for p in candidate.rglob("*") if p.is_file()
    }
    repo = tmp_path / "repository"
    support = json.loads((candidate / "u2-inputs/support-files.json").read_bytes())
    for name in support:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ui.ROOT / name, target)
    adopted = repo / "contract/vendor" / ("rk-sim@" + vr.PIN)
    shutil.copytree(candidate, adopted)
    with monkeypatch.context() as m:
        m.setattr(vr, "ROOT", repo)
        m.setattr(ui, "ROOT", repo)
        m.setattr(ui, "ADOPTED", adopted)
        strict(adopted)
        from tests.u2_comparison import run_historical

        with pytest.raises(ValueError, match="historical adopted identity changed"):
            run_historical(None)  # refuses before using inputs or candidate
        ui.load_inputs(
            adopted / "u2-inputs", vr.digest((adopted / "u2-inputs/SHA256SUMS").read_bytes())
        )
    fresh = tmp_path / "fresh-layout"
    shutil.copytree(repo, fresh)
    code = """
from unittest.mock import patch
from scripts import u2_inputs as ui
from scripts import vendor_rk as vr
import rkuarch.workload.prepare as producer
import rkuarch.workload.prepared as prepared
from contract.tests import nominal_candidate as nominal
from rkuarch.table import build
from rkuarch.engines.analytic import core
from pathlib import Path
assert ui.ROOT == vr.ROOT == Path.cwd()
assert Path(ui.__file__).is_relative_to(Path.cwd())
assert Path(producer.__file__).is_relative_to(Path.cwd())

def denied(*a, **k): raise AssertionError("oracle/producer forbidden")
with (patch.object(vr, "run_oracle", denied), patch.object(producer, "prepare", denied),
      patch.object(prepared, "execute_prepared_point", denied),
      patch.object(nominal, "evaluate_nominal", denied),
      patch.object(build, "capture", denied), patch.object(core, "run_analytic", denied)):
    vr.check_manifest(ui.ADOPTED)
    vr.check_snapshot_inputs(ui.ADOPTED)
    vr.check_generator(ui.ADOPTED)
    frozen = ui.ADOPTED / "u2-inputs"
    ui.load_inputs(frozen, vr.digest((frozen / "SHA256SUMS").read_bytes()))
print("same candidate accepted from fresh committed-required layout; no old checkout")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=fresh,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".:contract:src"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert {
        p.relative_to(adopted): p.read_bytes() for p in adopted.rglob("*") if p.is_file()
    } == original
    assert {
        p.relative_to(fresh / adopted.relative_to(repo)): p.read_bytes()
        for p in (fresh / adopted.relative_to(repo)).rglob("*")
        if p.is_file()
    } == original


@pytest.mark.parametrize(
    "attack", ["missing_manifest", "wrong_manifest", "changed_component", "changed_sidecar"]
)
def test_rehashed_bad_historical_provenance_refuses(candidate, attack):
    frozen = candidate / "u2-inputs"
    historical = frozen / "historical-source"
    if attack == "missing_manifest":
        (historical / "MANIFEST.json").unlink()
    elif attack == "wrong_manifest":
        data = json.loads((historical / "MANIFEST.json").read_bytes())
        data["files"]["components/asic_placeholder.yaml"] = "0" * 64
        (historical / "MANIFEST.json").write_bytes(vr.canonical(data))
    elif attack == "changed_component":
        path = historical / "components/asic_placeholder.yaml"
        path.write_bytes(path.read_bytes() + b"\n# changed historical bytes\n")
    else:
        path = historical / "model_shapes/llama-3.1-8b.json"
        path.write_bytes(path.read_bytes() + b"\n")
    identity = rehash_inputs(frozen)
    rehash(candidate)
    vr.check_manifest(candidate)
    with pytest.raises(ValueError, match="historical"):
        ui.load_inputs(frozen, identity)
    with pytest.raises(ValueError, match="historical"):
        strict(candidate)


@pytest.mark.parametrize("attack", ["retained_bytes_and_binding", "sidecar_attribution"])
def test_frozen_inputs_remain_joined_to_historical_members(candidate, attack):
    from uarch_contract.hashing import content_hash, sha256

    frozen = candidate / "u2-inputs"
    if attack == "retained_bytes_and_binding":
        path = frozen / "components/asic_placeholder.yaml"
        raw = path.read_bytes() + b"\n# attempted retained descriptor substitution\n"
        path.write_bytes(raw)
        path = frozen / "component-precisions.json"
        entries = json.loads(path.read_bytes())
        entry = next(e for e in entries if e["component_id"] == "compute.asic.placeholder")
        binding = entry["binding"]
        binding["component_bytes_sha256"] = sha256(raw)
        binding["binding_hash"] = content_hash(binding, exclude=("binding_hash",))
        entry["precision_hash"] = content_hash(entry, exclude=("precision_hash",))
        path.write_bytes(vr.canonical(entries))
        expected = "retained bytes/manifest"
    else:
        path = frozen / "model_shapes/llama-3.1-8b.json"
        value = json.loads(path.read_bytes())
        value["sources"][0]["note"] = "wrong frozen attribution"
        path.write_bytes(vr.canonical(value))
        expected = "retained sidecars/attribution"
    identity = rehash_inputs(frozen)
    with pytest.raises(ValueError, match=expected):
        ui.load_inputs(frozen, identity)


def test_strict_cli_enforces_frozen_copy_join(candidate, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["vendor-rk", "--check", "--output-root", str(candidate)])
    vr.main()
    assert "current compatibility verified" in capsys.readouterr().out
    (candidate / "components/npu-l4.yaml").write_bytes(b"tampered frozen copy")
    rehash(candidate)
    with pytest.raises(SystemExit) as exc:
        vr.main()
    assert exc.value.code == 1
    assert "frozen output copy" in capsys.readouterr().err


def test_synthetic_binding_builder_ignores_mutable_canonical(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "ADOPTED", tmp_path / "canonical-must-not-be-read")
    root = candidate.__wrapped__(tmp_path, monkeypatch)
    rows = json.loads((root / "parity/fixtures.json").read_bytes())
    assert len(rows) == len({row["id"] for row in rows}) == 1008
    assert sum(row["component_params_file"] == "components/npu-l4.yaml" for row in rows) == 144
    events = json.loads((root / "parity/refusals.json").read_bytes())
    assert len(events) == 4
    assert all("synthetic" in event["message"] for event in events)
