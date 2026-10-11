"""Capture/draft acceptance; no synthetic review is a real declaration review."""

import copy
import importlib
import shutil

import pytest
from uarch_contract.hashing import (
    artifact_identity,
    canonical_json,
    content_hash,
    review_subject_hash,
)
from uarch_contract.report_context import validate_metric_dependencies

from tests.integration.test_u2_a_replay import captured


def module():
    return importlib.import_module("rkuarch.table.companions")


@pytest.fixture
def saved(tmp_path):
    from rkuarch.table.build import captured_artifacts

    c = captured()
    directory = tmp_path / "capture"
    directory.mkdir()
    for h, value in captured_artifacts(c).items():
        (directory / (h[7:] + ".json")).write_text(canonical_json(value) + "\n")
    return c, directory


def block_producers(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("capture replay called a producer")

    for mod, names in (
        ("rkuarch.table.build", ("capture",)),
        ("rkuarch.workload.prepare", ("prepare",)),
        ("rkuarch.workload.prepared", ("prepare_engine_job", "execute_prepared_point")),
        ("rkuarch.engines.analytic.core", ("run_analytic",)),
    ):
        for name in names:
            monkeypatch.setattr(importlib.import_module(mod), name, forbidden)


def test_offline_capture_load_and_draft_with_producers_disabled(saved, tmp_path, monkeypatch):
    c, directory = saved
    relocated = tmp_path / "relocated"
    shutil.copytree(directory, relocated)
    block_producers(monkeypatch)
    for path in (directory, relocated):
        loaded = module().load_captured_work(path, c.bundle, c.assumptions)
        assert loaded == c
        card, deps, subject = module().draft_companions(loaded)
        assert card.badge == "stub" and card.evidence == ()
        assert card.validated_error_band is None and card.energy_verification is None
        assert all(v is None for v in card.verification.model_dump().values())
        assert card.model_id.engine == c.jobs[0].engine.name
        assert card.model_id.mapping_policy == c.request.mapping_policy
        assert deps.review_hash == "sha256:" + "0" * 64
        assert subject == review_subject_hash(deps)
        assert deps.dependencies_hash == content_hash(deps, exclude=("dependencies_hash",))
        # Literal expectations independent of table_recipes implementation.
        for i, result in enumerate(c.results):
            recipe = next(r for r in deps.recipes if r.metric_path == f"/rows/{i}/duration_s")
            assert len(recipe.selectors) == 1
            assert recipe.selectors[0].artifact_hash == result.result_hash
            assert recipe.selectors[0].json_pointer == "/duration_ps"
            source = next(
                s
                for s in deps.source_recipes
                if s.artifact_hash == result.result_hash and s.recipe.metric_path == "/duration_ps"
            )
            assert source.recipe.granularity == "whole_iteration"
            assert source.recipe.purpose == "duration"
            assert "/memory/dram/bw_bytes_per_s" in {
                s.json_pointer for s in source.recipe.selectors
            }
            for oi, _ in enumerate(result.per_op):
                assert any(
                    s.recipe.metric_path == f"/per_op/{oi}/counts/matrix_ops"
                    and s.artifact_hash == result.result_hash
                    for s in deps.source_recipes
                )
        from rkuarch.table.build import captured_artifacts

        with pytest.raises(ValueError):
            validate_metric_dependencies(deps, captured_artifacts(c))
    assert module().draft_companions(c) == (card, deps, subject)


@pytest.mark.parametrize(
    "member", ["bundle", "assumptions", "request", "derivation", "job", "result"]
)
def test_missing_capture_member_refuses(saved, member):
    c, directory = saved
    value = {
        "bundle": c.bundle,
        "assumptions": c.assumptions,
        "request": c.request,
        "derivation": c.derivation,
        "job": c.jobs[0],
        "result": c.results[0],
    }[member]
    h = artifact_identity(value.model_dump(mode="json"))
    (directory / (h[7:] + ".json")).unlink()
    with pytest.raises(ValueError, match="Capture|Artifact"):
        module().load_captured_work(directory, c.bundle, c.assumptions)


@pytest.mark.parametrize("kind", ["extra", "renamed", "stale-hash", "subdirectory"])
def test_capture_membership_is_exact(saved, kind):
    c, directory = saved
    path = directory / (c.results[0].result_hash[7:] + ".json")
    if kind == "extra":
        extra = {"unrelated": 1}
        (directory / (content_hash(extra)[7:] + ".json")).write_text(canonical_json(extra))
    elif kind == "renamed":
        path.rename(directory / "result.json")
    elif kind == "subdirectory":
        (directory / "unexpected").mkdir()
    else:
        value = c.results[0].model_dump(mode="json")
        value["duration_ps"] += 1
        path.write_text(canonical_json(value))
    with pytest.raises(ValueError, match="Capture|Artifact|Hash"):
        module().load_captured_work(directory, c.bundle, c.assumptions)


def replace_record(directory, old, raw, field):
    (directory / (getattr(old, field)[7:] + ".json")).unlink()
    raw[field] = content_hash(raw, exclude=(field,))
    (directory / (raw[field][7:] + ".json")).write_text(canonical_json(raw))


@pytest.mark.parametrize("field", ["request_hash", "engine", "hardware", "point_hash"])
def test_rehashed_job_substitutions_refuse(saved, field):
    c, directory = saved
    raw = c.jobs[0].model_dump(mode="json")
    if field == "engine":
        raw[field]["model"]["version"] = "wrong-model"
    elif field == "hardware":
        raw[field]["hardware_spec_hash"] = "sha256:" + "f" * 64
    else:
        raw[field] = "sha256:" + "f" * 64
    replace_record(directory, c.jobs[0], raw, "job_hash")
    with pytest.raises(ValueError):
        module().load_captured_work(directory, c.bundle, c.assumptions)


@pytest.mark.parametrize("field", ["job_hash", "counts", "u_c0_duration_ps"])
def test_rehashed_result_substitutions_refuse(saved, field):
    c, directory = saved
    raw = c.results[0].model_dump(mode="json")
    if field == "counts":
        raw[field]["matrix_ops"] += 1
    elif field == "job_hash":
        raw[field] = c.jobs[1].job_hash
    else:
        raw[field] *= 0.5
    replace_record(directory, c.results[0], raw, "result_hash")
    with pytest.raises(ValueError):
        module().load_captured_work(directory, c.bundle, c.assumptions)


def test_draft_authenticates_direct_captured_input(saved):
    c, _ = saved
    bad = copy.deepcopy(c.results[0]).model_copy(update={"duration_ps": 1.0})
    with pytest.raises(ValueError):
        module().draft_companions(c._replace(results=(bad, *c.results[1:])))
    with pytest.raises(ValueError):
        module().draft_companions(c._replace(jobs=c.jobs[:-1], results=c.results[:-1]))


@pytest.mark.parametrize("mutation", ["engine", "hardware-rate", "duplicate-point"])
def test_coherently_rehashed_jobs_and_results_do_not_escape_source_validation(saved, mutation):
    c, directory = saved
    job = c.jobs[0].model_dump(mode="json")
    result = c.results[0].model_dump(mode="json")
    if mutation == "engine":
        job["engine"]["version"] = "substitute"
        result["engine"] = job["engine"]
    elif mutation == "hardware-rate":
        job["hardware"]["dram_bw_bytes_per_s"] *= 2
    else:
        job["point"] = c.jobs[1].point.model_dump(mode="json")
        job["point_hash"] = c.jobs[1].point_hash
    replace_record(directory, c.jobs[0], job, "job_hash")
    result["job_hash"] = job["job_hash"]
    replace_record(directory, c.results[0], result, "result_hash")
    with pytest.raises(ValueError, match="Capture"):
        module().load_captured_work(directory, c.bundle, c.assumptions)


def test_rehashed_assumptions_and_replaced_request_refuse(saved):
    c, directory = saved
    assumptions = c.assumptions.model_copy(update={"limitations": ("different input",)})
    assumptions = assumptions.model_copy(
        update={"assumptions_hash": content_hash(assumptions, exclude=("assumptions_hash",))}
    )
    with pytest.raises(ValueError, match="Assumption"):
        module().load_captured_work(directory, c.bundle, assumptions)
    request = c.request.model_dump(mode="json")
    (directory / (content_hash(c.request)[7:] + ".json")).unlink()
    request["seed"] += 1
    (directory / (content_hash(request)[7:] + ".json")).write_text(canonical_json(request))
    with pytest.raises(ValueError, match="Membership"):
        module().load_captured_work(directory, c.bundle, c.assumptions)
