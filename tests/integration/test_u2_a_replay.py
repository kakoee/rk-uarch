"""Actual producer/table/replay tests; review records here are explicitly synthetic scaffolding."""

import importlib
import os
import subprocess
import sys

import pytest
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.model_card import ModelCard
from uarch_contract.report_context import ReportContext

from rkuarch.workload.prepared import physical_assumptions
from tests.unit.test_u2_a_loader import ZERO, read, reviewed, seal
from tests.unit.test_u2_a_shapes import inputs, prepare


def build_module():
    return importlib.import_module("rkuarch.table.build")


def captured():
    i, hw = inputs()
    return build_module().capture(prepare(i, hw), assumptions=physical_assumptions())


def companions(c, generic=False):
    """Test-only synthetic reviews. Production must receive actual reviewed context from B."""
    mod = build_module()
    recipes, sources = mod.table_recipes(c, generic_rows=generic)
    store = {}
    deps = dict(
        format="uarch-metric-dependencies/1",
        dependencies_hash=ZERO,
        review_hash=ZERO,
        version="synthetic-replay-test/1",
        model_identity_hash=content_hash(c.assumptions.model),
        recipes=[r.model_dump(mode="json") for r in recipes],
        source_recipes=[r.model_dump(mode="json") for r in sources],
    )
    reviewed(deps, "dependencies_hash", store)
    registry = read("family-registry.json")
    reviewed(registry, "registry_hash", store)
    context = ReportContext.model_validate(
        seal(
            dict(
                format="uarch-report-context/2",
                context_hash=ZERO,
                assumptions_hash=c.assumptions.assumptions_hash,
                comparison_hashes=[],
                evidence_index={},
                family_registry_hash=registry["registry_hash"],
                limitations=["Synthetic test review only; no report or model validation."],
                metric_dependencies_hash=deps["dependencies_hash"],
                model_identity=c.assumptions.model.model_dump(mode="json"),
                request_hash=content_hash(c.request),
                used_energy_families=[],
                verification_hashes=[],
            ),
            "context_hash",
        )
    )
    identity = importlib.import_module("rkuarch.workload.identity").legacy_model_id(
        c.jobs[0], c.bundle
    )
    card = ModelCard(model_id=identity, badge="stub", evidence=(), verification={})
    return context, card, store


def package(c, generic=False):
    context, card, store = companions(c, generic)
    return build_module().build_table(c, context=context, model_card=card, artifacts=store)


def test_actual_table_and_disabled_producer_replay(tmp_path, monkeypatch):
    c = captured()
    p = package(c)
    path = tmp_path / "table.json"
    build_module().write_table(p, path)
    from rkuarch.table.artifacts import load_verified_report_inputs

    v = load_verified_report_inputs(path)
    assert v.table.rows[0].duration_s == 0.000001892
    assert v.table.rows[0].u_c0_duration_s == 0.000001584
    assert v.table.rows[0].counts.matrix_ops == 1184
    assert v.table.rows[0].peak_resident_bytes == {"hbm": None, "sram": None}
    assert v.table.measured_error.layer_reuse.n_samples == 0
    assert v.table.measured_error.layer_reuse.max_rel is None
    saved = tmp_path / "prepared.json"
    saved.write_bytes(canonical_json(c.bundle).encode())
    monkeypatch.setattr(
        importlib.import_module("rkuarch.workload.prepare"),
        "prepare",
        lambda *a, **kw: pytest.fail("producer called"),
    )
    from rkuarch.workload.prepared import load_prepared_input

    replay = build_module().capture(load_prepared_input(saved), assumptions=c.assumptions)
    assert package(replay) == p
    assert canonical_json(package(replay).table) == canonical_json(p.table)


def test_generic_recipes_keep_each_exact_source_and_scopes(tmp_path):
    c = captured()
    p = package(c, True)
    path = tmp_path / "table.json"
    build_module().write_table(p, path)
    from rkuarch.table.artifacts import load_verified_report_inputs

    v = load_verified_report_inputs(path)
    assert "/rows/*/duration_s" in v.terminal_contributors
    scopes = build_module().source_scopes(c, family="synthetic-test-family")
    for result in c.results:
        assert len(scopes[(result.result_hash, "/duration_ps")]) == len(result.per_op)
        assert len(scopes[(result.result_hash, "/per_op/0/duration_ps")]) == 1
    assert build_module().consumed_energy_families(c) == ()
    assert v.context.used_energy_families == ()


def test_package_tampering_refuses_before_destination(tmp_path):
    c = captured()
    ctx, card, store = companions(c)
    bad = ctx.model_copy(update={"request_hash": ZERO})
    bad = bad.model_copy(update={"context_hash": content_hash(bad, exclude=("context_hash",))})
    with pytest.raises(ValueError, match="ReportContextMismatch"):
        build_module().build_table(c, context=bad, model_card=card, artifacts=store)
    assert not (tmp_path / "table.json").exists()


def test_single_conversion_and_refusals():
    m = importlib.import_module("rkuarch.table.time_units")
    assert m.ps_to_seconds(1) == 1e-12
    assert m.ps_to_seconds(0.5) == 0.5e-12
    for value in (True, -1, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            m.ps_to_seconds(value)


def test_engine_subprocess_and_cli_replay(tmp_path):
    c = captured()
    p = package(c)
    build_module().write_table(p, tmp_path / "original/table.json")
    env = dict(os.environ, PYTHONPATH="contract:src", PYTHONDONTWRITEBYTECODE="1")
    job = c.jobs[0]
    out = subprocess.run(
        [sys.executable, "-B", "-m", "rkuarch.engines.analytic"],
        input=canonical_json(job).encode(),
        capture_output=True,
        env=env,
        check=True,
    )
    assert out.stdout == canonical_json(c.results[0]).encode() + b"\n"
    (tmp_path / "prepared.json").write_bytes(canonical_json(c.bundle).encode())
    (tmp_path / "assumptions.json").write_bytes(canonical_json(c.assumptions).encode())
    (tmp_path / "context.json").write_bytes(
        canonical_json(p.artifacts[p.table.artifacts.report_context_hash]).encode()
    )
    (tmp_path / "card.json").write_bytes(
        canonical_json(p.artifacts[p.table.artifacts.model_card_hash]).encode()
    )
    for threads in ("1", "4"):
        args = [
            sys.executable,
            "-B",
            "-m",
            "rkuarch.cli",
            "table",
            "--prepared-input",
            str(tmp_path / "prepared.json"),
            "--assumptions",
            str(tmp_path / "assumptions.json"),
            "--context",
            str(tmp_path / "context.json"),
            "--model-card",
            str(tmp_path / "card.json"),
            "--artifact-dir",
            str(tmp_path / "original/artifacts"),
            "--output",
            str(tmp_path / f"run{threads}/table.json"),
        ]
        subenv = dict(
            env,
            OMP_NUM_THREADS=threads,
            OPENBLAS_NUM_THREADS=threads,
            MKL_NUM_THREADS=threads,
            PYTHONHASHSEED=threads,
        )
        result = subprocess.run(args, capture_output=True, env=subenv)
        assert result.returncode == 0, result.stderr.decode()
        assert (tmp_path / f"run{threads}/table.json").read_bytes() == (
            tmp_path / "original/table.json"
        ).read_bytes()
    refused = subprocess.run(args + ["--intent", "unused.json"], capture_output=True, env=env)
    assert refused.returncode != 0


def test_unused_raw_artifact_identity_is_checked_before_writes(tmp_path):
    c = captured()
    p = package(c)
    store = dict(p.artifacts)
    store["sha256:" + "a" * 64] = b"wrong unused raw bytes"
    forged = build_module().TablePackage(p.table, store)
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        build_module().write_table(forged, tmp_path / "must-not-exist/table.json")
    assert not (tmp_path / "must-not-exist").exists()
