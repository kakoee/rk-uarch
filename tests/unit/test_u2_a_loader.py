"""Offline loader tests built from independent captured A1 records, never run as workloads."""

import copy
import importlib
import json
from pathlib import Path

import pytest
from uarch_contract.hashing import (
    artifact_identity,
    canonical_json,
    content_hash,
    review_subject_hash,
    sha256,
)

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "docs/reviews/U2-U0003-proposal/fixtures"
ZERO = "sha256:" + "0" * 64


def read(name):
    return json.loads((FIX / name).read_text())


def seal(value, field):
    value[field] = content_hash(value, exclude=(field,))
    return value


def reviewed(value, field, store):
    review = dict(
        format="uarch-evidence-review/1",
        review_hash=ZERO,
        decision="accepted",
        independent=True,
        reviewer="synthetic loader test",
        rationale="No real evidence.",
        reviewed_subject_hashes=[review_subject_hash(value)],
    )
    seal(review, "review_hash")
    store[review["review_hash"]] = review
    value["review_hash"] = review["review_hash"]
    seal(value, field)
    store[value[field]] = value
    return value


def offline_fixture():
    table, bundle, context = (
        read("table.json"),
        read("independent-bundle.json"),
        read("report-context.json"),
    )
    store = {}
    for name in (
        "engine-job-0.json",
        "engine-result-0.json",
        "engine-job-1.json",
        "engine-result-1.json",
        "model-card.json",
        "derivation.json",
        "assumptions.json",
        "family-registry.json",
        "registry-review.json",
    ):
        value = read(name)
        store[artifact_identity(value)] = value
    store[bundle["bundle_hash"]] = bundle
    # Literal dependency declaration: each count depends on captured work/algorithms/model;
    # timings ALSO consume exactly these six sourced rate inputs plus point frequency.
    sources, recipes = [], []
    results = [store[row["result_hash"]] for row in table["rows"]]
    for ri, result in enumerate(results):
        point = next(
            i
            for i, p in enumerate(bundle["points"])
            if p["payload_hash"] == table["rows"][ri]["point_hash"]
        )
        base = f"/points/{point}/graph"
        selectors = [
            dict(
                kind="prepared_content",
                artifact_hash=bundle["bundle_hash"],
                json_pointer=base + "/attention_mask",
            ),
            dict(
                kind="model_assumption",
                artifact_hash=context["assumptions_hash"],
                json_pointer="/algorithms",
            ),
            dict(
                kind="model_evidence",
                artifact_hash=context["assumptions_hash"],
                json_pointer="/model",
            ),
        ]
        for gi, g in enumerate(bundle["points"][point]["graph"]["groups"]):
            selectors.append(
                dict(
                    kind="prepared_content",
                    artifact_hash=bundle["bundle_hash"],
                    json_pointer=base + f"/groups/{gi}/repeat",
                )
            )
            for oi, _ in enumerate(g["ops"]):
                for field in ("spec", "operand_access", "embedding_local_tokens", "work_repeat"):
                    selectors.append(
                        dict(
                            kind="prepared_content",
                            artifact_hash=bundle["bundle_hash"],
                            json_pointer=base + f"/groups/{gi}/ops/{oi}/{field}",
                        )
                    )
        targets = [
            "duration_ps",
            "u_c0_duration_ps",
            "counts/matrix_ops",
            "counts/vector_ops",
            "counts/memory_read_bytes",
            "counts/memory_write_bytes",
        ]
        # Literal inventory of every numeric OpResult surface, not obtained from the implementation.
        for oi in range(len(result["per_op"])):
            targets += [
                f"per_op/{oi}/{field}"
                for field in (
                    "counts/matrix_ops",
                    "counts/vector_ops",
                    "counts/memory_read_bytes",
                    "counts/memory_write_bytes",
                    "instances",
                    "duration_ps",
                    "compute_time_ps",
                    "memory_time_ps",
                    "operational_intensity_ops_per_byte",
                    "achieved_ops_per_s",
                    "ridge_ops_per_byte",
                    "matrix_peak_ops_per_s",
                    "vector_peak_ops_per_s",
                    "dram_bw_bytes_per_s",
                )
            ]
        for target in targets:
            chosen = copy.deepcopy(selectors)
            if target.startswith("per_op/"):
                ordinal = int(target.split("/")[1])
                positions = [
                    (gi, oi)
                    for gi, g in enumerate(bundle["points"][point]["graph"]["groups"])
                    for oi, _ in enumerate(g["ops"])
                ]
                gi, oi = positions[ordinal]
                prefix = base + f"/groups/{gi}"
                chosen = [
                    s
                    for s in chosen
                    if s["kind"] != "prepared_content"
                    or s["json_pointer"] == base + "/attention_mask"
                    or s["json_pointer"] == prefix + "/repeat"
                    or s["json_pointer"].startswith(prefix + f"/ops/{oi}/")
                ]
            purpose = (
                "counts" if "counts/" in target or target.endswith("instances") else "duration"
            )
            if purpose == "duration":
                chosen += [
                    dict(
                        kind="hardware_leaf",
                        artifact_hash=table["hardware_spec_hash"],
                        json_pointer=p,
                    )
                    for p in (
                        "/clock_domains/core/freq_hz",
                        "/cores/grid/rows",
                        "/cores/grid/cols",
                        "/cores/core_type/matrix_engine/macs_per_cycle/bf16",
                        "/cores/core_type/vector_engine/ops_per_cycle",
                        "/memory/dram/bw_bytes_per_s",
                    )
                ]
                chosen.append(
                    dict(
                        kind="prepared_content",
                        artifact_hash=bundle["bundle_hash"],
                        json_pointer=f"/points/{point}/frequency_ratio",
                    )
                )
            recipe = dict(
                metric_path="/" + target,
                purpose=purpose,
                granularity="operator" if target.startswith("per_op/") else "whole_iteration",
                applicable_dimensions=["model_identity"],
                selectors=chosen,
            )
            sources.append(
                dict(
                    artifact_hash=result["result_hash"],
                    model_identity_hash=content_hash(context["model_identity"]),
                    recipe=recipe,
                )
            )
            render_target = (
                target.replace("per_op/", "op_results/")
                if target.startswith("per_op/")
                else target.replace("_ps", "_s")
            )
            recipes.append(
                dict(
                    metric_path=f"/rows/{ri}/" + render_target,
                    purpose=purpose,
                    granularity="whole_iteration",
                    applicable_dimensions=["model_identity"],
                    selectors=[
                        dict(
                            kind="result_field",
                            artifact_hash=result["result_hash"],
                            json_pointer="/" + target,
                        )
                    ],
                )
            )
    deps = dict(
        format="uarch-metric-dependencies/1",
        dependencies_hash=ZERO,
        review_hash=ZERO,
        version="loader-literal/1",
        model_identity_hash=content_hash(context["model_identity"]),
        recipes=recipes,
        source_recipes=sources,
    )
    reviewed(deps, "dependencies_hash", store)
    context.update(
        comparison_hashes=[],
        verification_hashes=[],
        evidence_index={},
        metric_dependencies_hash=deps["dependencies_hash"],
    )
    seal(context, "context_hash")
    store[context["context_hash"]] = context
    table["artifacts"].update(comparison_hashes=[], report_context_hash=context["context_hash"])
    table["comparison_state"] = "not_attempted"
    seal(table, "table_hash")
    return table, store


def write_fixture(tmp_path, table, store):
    directory = tmp_path / "artifacts"
    directory.mkdir(exist_ok=True)
    for identity, value in store.items():
        (directory / (identity[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else (canonical_json(value) + "\n").encode()
        )
    path = tmp_path / "table.json"
    path.write_text(canonical_json(table) + "\n")
    return path


def loader():
    return importlib.import_module("rkuarch.table.artifacts").load_verified_report_inputs


def test_offline_typed_closure_and_metadata(tmp_path, monkeypatch):
    table, store = offline_fixture()
    path = write_fixture(tmp_path, table, store)
    from rkuarch.engines.analytic import core

    monkeypatch.setattr(core, "run_analytic", lambda *a: pytest.fail("loader executed engine"))
    value = loader()(path)
    assert value.table.table_hash == table["table_hash"]
    assert len(value.jobs) == len(value.results) == len(value.table.rows)
    assert value.bundle.bundle_hash == table["artifacts"]["prepared_bundle_hash"]
    assert value.dependencies.source_recipes[0].recipe.granularity == "whole_iteration"
    assert value.dependencies.source_recipes[0].recipe.applicable_dimensions == ("model_identity",)
    assert value.hardware == value.bundle.hardware_spec
    moved = tmp_path / "relocated"
    moved.mkdir()
    moved_path = write_fixture(moved, table, store)
    assert loader()(moved_path).table == value.table
    assert loader()(moved_path, artifact_dir=tmp_path / "artifacts").context == value.context


@pytest.mark.parametrize(
    "which", ["job", "result", "bundle", "context", "review", "derivation", "card"]
)
def test_missing_companions_refuse(tmp_path, which):
    table, store = offline_fixture()
    keys = dict(
        job=next(k for k, v in store.items() if "job_hash" in v and "result_hash" not in v),
        result=table["rows"][0]["result_hash"],
        bundle=table["artifacts"]["prepared_bundle_hash"],
        context=table["artifacts"]["report_context_hash"],
        review=next(k for k, v in store.items() if v.get("format") == "uarch-evidence-review/1"),
        derivation=table["artifacts"]["derivation_hash"],
        card=table["artifacts"]["model_card_hash"],
    )
    store.pop(keys[which])
    path = write_fixture(tmp_path, table, store)
    with pytest.raises(ValueError, match="ArtifactMissing"):
        loader()(path)


def test_duplicate_json_and_tampered_hash_refused(tmp_path):
    table, store = offline_fixture()
    path = write_fixture(tmp_path, table, store)
    artifact = tmp_path / "artifacts" / (table["rows"][0]["result_hash"][7:] + ".json")
    original = artifact.read_text()
    artifact.write_text('{"duration_ps":0,"duration_ps":1}')
    with pytest.raises(ValueError, match="DuplicateJsonKey"):
        loader()(path)
    artifact.write_text(original.replace('"duration_ps":1892000.0', '"duration_ps":1892001.0'))
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        loader()(path)


def test_rehashed_reviewed_omitted_actual_input_refused(tmp_path):
    table, store = offline_fixture()
    context = store[table["artifacts"]["report_context_hash"]]
    deps = store[context["metric_dependencies_hash"]]
    source = deps["source_recipes"][0]
    source["recipe"]["selectors"] = [
        s
        for s in source["recipe"]["selectors"]
        if not s["json_pointer"].endswith("/ops/0/work_repeat")
    ]
    reviewed(deps, "dependencies_hash", store)
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    seal(context, "context_hash")
    store[context["context_hash"]] = context
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    seal(table, "table_hash")
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        loader()(write_fixture(tmp_path, table, store))


def test_per_op_source_omission_is_not_hidden_by_complete_row_source(tmp_path):
    table, store = offline_fixture()
    context = store[table["artifacts"]["report_context_hash"]]
    deps = store[context["metric_dependencies_hash"]]
    source = next(
        s for s in deps["source_recipes"] if s["recipe"]["metric_path"] == "/per_op/0/duration_ps"
    )
    source["recipe"]["selectors"] = [
        s
        for s in source["recipe"]["selectors"]
        if not s["json_pointer"].endswith("/ops/0/work_repeat")
    ]
    reviewed(deps, "dependencies_hash", store)
    context["metric_dependencies_hash"] = deps["dependencies_hash"]
    seal(context, "context_hash")
    store[context["context_hash"]] = context
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    seal(table, "table_hash")
    with pytest.raises(ValueError, match="IncompleteMetricContributors"):
        loader()(write_fixture(tmp_path, table, store))


def test_raw_source_blob_closure_and_tampering(tmp_path):
    table, store = offline_fixture()
    raw = b"independent hand-authored loader source, not silicon or executed workload\n"
    source = read("evidence-source.json")
    source["raw_blob_sha256"] = sha256(raw)
    seal(source, "source_hash")
    store[source["source_hash"]] = source
    store[source["raw_blob_sha256"]] = raw
    verification = read("verification.json")
    verification["source_hash"] = source["source_hash"]
    reviewed(verification, "verification_hash", store)
    context = store[table["artifacts"]["report_context_hash"]]
    context["verification_hashes"] = [verification["verification_hash"]]
    seal(context, "context_hash")
    store[context["context_hash"]] = context
    table["artifacts"]["report_context_hash"] = context["context_hash"]
    seal(table, "table_hash")
    path = write_fixture(tmp_path, table, store)
    value = loader()(path)
    assert value.sources[0].raw_blob_sha256 == sha256(raw)
    assert value.artifacts[sha256(raw)] == raw
    raw_path = tmp_path / "artifacts" / (sha256(raw)[7:] + ".json")
    raw_path.write_bytes(raw + b"altered")
    with pytest.raises(ValueError, match="ArtifactHashMismatch"):
        loader()(path)


def test_card_energy_verification_cannot_name_an_untyped_blob(tmp_path):
    table, store = offline_fixture()
    card = copy.deepcopy(store[table["artifacts"]["model_card_hash"]])
    unrelated = {"not_a_verification_record": True}
    identity = content_hash(unrelated)
    store[identity] = unrelated
    card["energy_verification"] = {"L0": {"mac": identity}, "L2": {"mac": None}}
    card_hash = content_hash(card)
    store[card_hash] = card
    table["artifacts"]["model_card_hash"] = card_hash
    table["provenance"]["model_card"]["hash"] = card_hash
    table["provenance"]["model_card"]["energy_verification"] = card["energy_verification"]
    seal(table, "table_hash")
    with pytest.raises(ValueError, match="VerificationRecord"):
        loader()(write_fixture(tmp_path, table, store))
