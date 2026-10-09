"""Synthetic refreshed premises with independent expected arithmetic; no oracle invocation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from contract.tests.historical_snapshot import historical_snapshot
from scripts import u2_inputs as ui
from scripts import vendor_rk as vr
from tests import u2_refresh as refresh
from tests.unit.test_u2_b_tooling_binding import rehash

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def reference(tmp_path_factory):
    """864 historical numeric literals plus synthetic H1 premises, never nominal output echo."""
    parent = tmp_path_factory.mktemp("refresh")
    inputs_root = parent / "inputs"
    inputs = ui.load_inputs(inputs_root, ui.prepare_inputs(inputs_root))
    root = parent / "synthetic-reference"
    shutil.copytree(historical_snapshot(), root)
    shutil.copytree(inputs_root, root / "u2-inputs")
    for role in inputs.matrix:
        shutil.copyfile(inputs_root / "components" / role, root / "components" / role)
    for name in vr.SOURCES:
        path = root / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            basename = (
                "pinned-compute.py.txt"
                if name.endswith("f0/compute.py")
                else "pinned-" + Path(name).parent.name + "-" + Path(name).name + ".txt"
            )
            shutil.copyfile(ROOT / "tests/fixtures/u2_b/refresh" / basename, path)
    rows = json.loads((historical_snapshot() / "parity/fixtures.json").read_bytes())
    h1 = []
    for original in rows:
        if original["component_params_file"] != "components/nvidia_h100_sxm.yaml" or original[
            "precision"
        ] != dict(compute="bf16", kv_cache="bf16"):
            continue
        row = json.loads(json.dumps(original))
        row["id"] = row["id"].replace("nvidia_h100_sxm.yaml", "npu-l4.yaml")
        row["component_params_file"] = "components/npu-l4.yaml"
        row["component_params_sha256"] = vr.digest((root / "components/npu-l4.yaml").read_bytes())
        # Independent explicit synthetic roofline premise; .55 is not applied to H1.
        c = row["counts"]
        row["duration_s"] = (
            max(
                c["matrix_ops"] / 524288000000000,
                (c["memory_read_bytes"] + (c["memory_write_bytes"] or 0)) / 1000000000000,
            )
            / row["tp"]
        )
        row["contributors"] = ["SYNTHETIC H1 expected premise, not upstream output"]
        h1.append(row)
    assert len(h1) == 144
    rows.extend(h1)
    (root / "parity/fixtures.json").write_bytes(vr.canonical(rows))
    source = vr.digest((root / "rk/engine/f0/compute.py").read_bytes())
    events = [
        dict(
            component_params_file="components/" + name,
            compute=fmt,
            kv_cache=fmt,
            component_params_sha256=vr.digest((root / "components" / name).read_bytes()),
            rk_sha=vr.PIN,
            execution="refused",
            exception="UnsupportedPrecision",
            message="SYNTHETIC direct-refusal premise",
            boundary="Accelerator.peak_op_per_s",
            callable_source_sha256=source,
        )
        for name, fmts in [
            ("asic_placeholder.yaml", ("bf16", "fp8")),
            ("npu-l4.yaml", ("fp16", "fp8")),
        ]
        for fmt in fmts
    ]
    (root / "parity/refusals.json").write_bytes(vr.canonical(events))
    metadata = json.loads((root / "GENERATOR.json").read_bytes())
    metadata.update(
        script_sha256=vr.digest(Path(vr.__file__).read_bytes()),
        oracle_program_sha256=vr.digest(vr.ORACLE_PROGRAM.encode()),
    )
    (root / "GENERATOR.json").write_bytes(vr.canonical(metadata))
    (root / "SYNTHETIC-REFERENCE").write_text(
        "Explicit synthetic test premises; not real adoption or oracle output.\n"
    )
    rehash(root)
    return root


@pytest.fixture(scope="module")
def run(reference):
    import os

    value = refresh.consume_synthetic(reference)
    if target := os.environ.get("U2_B_REFRESH_EVIDENCE_DIR"):
        destination = Path(target)
        refresh.save_comparisons(value, destination / "final-synthetic-execution")
        shutil.copytree(reference, destination / "final-synthetic-reference")
    return value


def test_full_reference_executes_actual_candidates_and_preserves_physical_failures(run):
    from collections import Counter

    assert len(run["nominal"].fixtures) == len(run["physical"].fixtures) == 1008
    assert run["inventory"].classification == "synthetic_reference"
    assert run["nominal"].classification == "synthetic_presentation"
    assert run["nominal"].gate_outcome == "compatibility_pass"
    assert run["nominal"].evidence_outcome == "refused"
    assert Counter(f.execution for f in run["physical"].fixtures) == dict(
        not_run=864, executed=96, execution_failed=48
    )
    assert run["physical"].gate_outcome == "not_assessed"
    assert all(o.match_result == "matched" for o in run["nominal"].precision_refusal_observations)
    assert len(run["physical_errors"]) == 48


def test_raw_inspection_does_not_authorize_adoption(reference):
    audit = refresh.audit_candidate(reference)
    assert audit["rows"] == 1008 and audit["adopted"] is False
    with pytest.raises(ValueError):
        refresh.consume_adopted(adoption_review=reference / "MANIFEST.json", review_sha256="0" * 64)


def test_physical_replay_uses_captured_identities_with_producers_disabled(
    reference, run, monkeypatch
):
    from tests import u2_comparison as old

    monkeypatch.setattr(old, "prepare_h1", lambda *a, **k: pytest.fail("prepare called"))
    monkeypatch.setattr(old, "physical_point", lambda *a, **k: pytest.fail("engine called"))
    replay = refresh.consume_synthetic(reference, physical_replay=run["physical_capture"])
    assert replay["physical"] == run["physical"]


@pytest.fixture(scope="module")
def report_subset(run):
    """Three explicit diagnostic fixtures, not the complete matrix report exit."""
    from uarch_contract.comparison import ReferenceInventory
    from uarch_contract.hashing import content_hash

    from contract.tests.u2_comparison import assemble_comparison
    from tests import u2_comparison as old

    wanted = set()
    for state in ("executed", "execution_failed", "not_run"):
        wanted.add(next(f.fixture_id for f in run["physical"].fixtures if f.execution == state))
    subset = dict(run, artifacts=dict(run["artifacts"]))
    value = run["inventory"].model_dump(mode="json", exclude={"inventory_hash"})
    value["fixtures"] = [f for f in value["fixtures"] if f["fixture_id"] in wanted]
    value["inventory_hash"] = content_hash(value)
    inv = ReferenceInventory.model_validate(value)
    subset["inventory"] = inv
    subset["artifacts"][inv.inventory_hash] = value
    for key in ("nominal", "physical"):
        c = run[key]
        new = assemble_comparison(
            candidate=c.candidate,
            inventory=inv,
            fixtures=tuple(f for f in c.fixtures if f.fixture_id in wanted),
            observations=c.precision_refusal_observations,
            track=c.track,
            classification=c.classification,
            limitations=("THREE-FIXTURE diagnostic subset; not complete refreshed acceptance.",),
            artifacts=subset["artifacts"],
        )
        subset[key] = new
        subset["artifacts"][new.comparison_hash] = new.model_dump(mode="json")
    captured = old.capture_h1(run["inputs"], model_id="llama-3.1-8b", tp=1, compact=True)
    return refresh.report_package(subset, captured=captured)


def test_offline_report_subset_and_capabilities(report_subset, tmp_path, monkeypatch):
    from rkuarch.report.complete import render_verified
    from rkuarch.table.artifacts import load_verified_report_inputs
    from rkuarch.table.build import write_table
    from tests import u2_comparison as old

    monkeypatch.setattr(old, "prepare_h1", lambda *a, **k: pytest.fail("prepare called"))
    monkeypatch.setattr(old, "physical_point", lambda *a, **k: pytest.fail("engine called"))
    monkeypatch.setattr(
        old.nominal, "evaluate_nominal", lambda *a, **k: pytest.fail("candidate called")
    )
    path = tmp_path / "table.json"
    write_table(report_subset, path)
    verified = load_verified_report_inputs(path)
    assert [len(c.fixtures) for c in verified.comparisons] == [3, 3]
    hidden = render_verified(verified)
    shown = render_verified(
        verified, show_unvalidated_predictions=True, allow_synthetic_presentation=True
    )
    assert all(m.number is None for p, m in hidden.metrics.items() if p.startswith("/comparisons/"))
    assert "STUB" in shown.html and "STUB" in shown.markdown
    assert all(
        m.assessment.badge == "stub"
        for p, m in shown.metrics.items()
        if p.startswith("/comparisons/")
    )
    # A display capability from another request cannot authorize this report.
    bad = shown.render_spec.model_dump(mode="json", exclude={"render_hash"})
    from uarch_contract.hashing import content_hash
    from uarch_contract.report_context import RenderSpec

    bad["table_hash"] = "sha256:" + "0" * 64
    bad["render_hash"] = content_hash(bad)
    with pytest.raises(ValueError):
        render_verified(verified, render_spec=RenderSpec.model_validate(bad))

    import os

    if target := os.environ.get("U2_B_REFRESH_REPORT_DIR"):
        destination = Path(target) / "three-fixture-report"
        shutil.copytree(tmp_path, destination)
        (destination / "hidden.html").write_text(hidden.html)
        (destination / "hidden.md").write_text(hidden.markdown)
        (destination / "stub-opt-in.html").write_text(shown.html)
        (destination / "stub-opt-in.md").write_text(shown.markdown)


@pytest.mark.parametrize(
    "change,match",
    [
        ("missing", "not_run"),
        ("boundary", "wrong_boundary"),
        ("class", "wrong_error_class"),
        ("success", "unexpected_success"),
        ("failure", "execution_failed"),
    ],
)
def test_full_coverage_precision_reductions(reference, run, change, match):
    from contract.tests.u2_comparison import assemble_comparison

    events = json.loads((reference / "parity/refusals.json").read_bytes())
    if change == "missing":
        events.pop(0)
    elif change == "boundary":
        events[0]["boundary"] = "iteration"
    elif change == "class":
        events[0]["exception"] = "ValueError"
    elif change == "success":
        events[0].update(execution="succeeded", exception=None)
    else:
        events[0].update(execution="execution_failed", exception="RuntimeError")
    store = dict(run["artifacts"])
    _, _, observations = refresh.precision_records(
        run["inputs"],
        vr.canonical(events),
        (reference / "rk/engine/f0/compute.py").read_bytes(),
        store,
        synthetic=True,
    )
    assert observations[0].match_result == match
    c = run["nominal"]
    changed = assemble_comparison(
        candidate=c.candidate,
        inventory=run["inventory"],
        fixtures=c.fixtures,
        observations=observations,
        track=c.track,
        classification=c.classification,
        limitations=c.limitations,
        artifacts=store,
    )
    assert changed.gate_outcome == "compatibility_fail"
    assert len(changed.fixtures) == 1008


@pytest.mark.parametrize(
    "change", ["source", "pin", "component", "duplicate", "extra", "field", "raw_source"]
)
def test_direct_capture_binding_refuses(reference, run, change):
    events = json.loads((reference / "parity/refusals.json").read_bytes())
    source = (reference / "rk/engine/f0/compute.py").read_bytes()
    if change == "source":
        events[0]["callable_source_sha256"] = "0" * 64
    elif change == "pin":
        events[0]["rk_sha"] = "0" * 40
    elif change == "component":
        events[0]["component_params_sha256"] = "0" * 64
    elif change == "duplicate":
        events.append(events[0])
    elif change == "extra":
        events[0]["component_params_file"] = "components/nvidia_h100_sxm.yaml"
    elif change == "field":
        del events[0]["execution"]
    else:
        source += b"changed"
    with pytest.raises(ValueError):
        refresh.precision_records(run["inputs"], vr.canonical(events), source, {}, synthetic=True)


@pytest.mark.parametrize("field", ["result_hash", "job_hash", "bundle_hash"])
def test_physical_replay_rejects_substitution(run, field):
    import copy

    capture = copy.deepcopy(run["physical_capture"])
    executed = [a for a in capture["attempts"].values() if a["execution"] == "executed"]
    first = executed[0]
    other = next(a for a in executed if a[field] != first[field])
    first[field] = other[field]
    with pytest.raises(ValueError):
        refresh.verify_physical(run["inputs"], run["original_rows"], capture)


def test_failure_capture_rejects_changed_requested_inputs(run):
    import copy

    from uarch_contract.hashing import artifact_identity

    capture = copy.deepcopy(run["physical_capture"])
    a = next(a for a in capture["attempts"].values() if a["execution"] == "execution_failed")
    failure = capture["artifacts"][a["failure_hash"]]
    failure["requested"]["tp"] = 8
    a["failure_hash"] = artifact_identity(failure)
    capture["artifacts"][a["failure_hash"]] = failure
    with pytest.raises(ValueError):
        refresh.verify_physical(run["inputs"], run["original_rows"], capture)


def test_independent_numeric_perturbation_fails_full_gate(reference, run, monkeypatch):
    from uarch_contract.hashing import content_hash

    from tests import u2_comparison as old

    evaluate = old.nominal.evaluate_nominal

    def changed(value):
        result = evaluate(value).model_dump(mode="json")
        result["duration_s"] *= 1.01
        result.pop("output_hash")
        result["output_hash"] = content_hash(result)
        return old.nominal.NominalOutput.model_validate(result)

    monkeypatch.setattr(old.nominal, "evaluate_nominal", changed)
    replay = refresh.consume_synthetic(reference, physical_replay=run["physical_capture"])
    assert len(replay["nominal"].fixtures) == 1008
    assert all(f.execution == "executed" for f in replay["nominal"].fixtures)
    assert replay["nominal"].gate_outcome == "compatibility_fail"
    assert any(c.outcome == "failed" for f in replay["nominal"].fixtures for c in f.channels)


def test_trace_closure_requires_raw_events_and_pinned_source(run):
    from uarch_contract.hashing import sha256, verify_declared_artifact_closure

    from tests import u2_comparison as old

    store = run["artifacts"]
    closed = verify_declared_artifact_closure(run["nominal"].comparison_hash, store)
    assert "sha256:" + old.DIRECT_SOURCE in closed
    sources = [
        store[h]
        for h in closed
        if isinstance(store[h], dict) and store[h].get("format") == "uarch-reference-source/1"
    ]
    assert len(sources) == 2
    assert {s["kind"] for s in sources} == {"synthetic_fixture", "contract_test"}
    for source in sources:
        identity = source["raw_blob_sha256"]
        assert sha256(store[identity]) == identity
        changed = dict(store)
        changed[identity] = store[identity] + b"tampered"
        with pytest.raises(ValueError, match="ArtifactHashMismatch"):
            verify_declared_artifact_closure(run["nominal"].comparison_hash, changed)


@pytest.mark.parametrize("mutation", ["model", "purpose", "anchor"])
def test_refreshed_recipe_mutations_with_fresh_review_refuse(report_subset, mutation):
    from copy import deepcopy

    from uarch_contract.hashing import content_hash, review_subject_hash
    from uarch_contract.report_context import validate_metric_dependencies

    store = dict(report_subset.artifacts)
    context = store[report_subset.table.artifacts.report_context_hash]
    deps = deepcopy(store[context["metric_dependencies_hash"]])
    source = next(
        s
        for s in deps["source_recipes"]
        if s["recipe"]["metric_path"] == "/counts/matrix_ops"
        and store[s["artifact_hash"]].get("format") == "uarch-nominal-output/1"
    )
    if mutation == "model":
        source["model_identity_hash"] = "sha256:" + "0" * 64
    elif mutation == "purpose":
        source["recipe"]["purpose"] = "duration"
    else:
        recipe = next(r for r in deps["recipes"] if r["metric_path"].startswith("/comparisons/"))
        recipe["selectors"] = [s for s in recipe["selectors"] if s["kind"] != "model_assumption"]
    review = deepcopy(store[deps["review_hash"]])
    review["reviewed_subject_hashes"] = [review_subject_hash(deps)]
    review["review_hash"] = content_hash(review, exclude=("review_hash",))
    store[review["review_hash"]] = review
    deps["review_hash"] = review["review_hash"]
    deps["dependencies_hash"] = content_hash(deps, exclude=("dependencies_hash",))
    with pytest.raises(ValueError, match="IncompleteMetricContributors|MetricPurposeMismatch"):
        validate_metric_dependencies(deps, store)


def test_separate_adoption_record_is_exact_not_manifest_inference(tmp_path, monkeypatch):
    from uarch_contract.hashing import content_hash, sha256

    root = tmp_path / "canonical-adopted-control"
    root.mkdir()
    (root / "MANIFEST.json").write_bytes(b"Explicit synthetic authority-interface test only\n")
    monkeypatch.setattr(ui, "ADOPTED", root)
    record = dict(
        format="uarch-evidence-review/1",
        reviewer="Javid (@jjaffari)",
        independent=True,
        decision="accepted",
        rationale="SYNTHETIC authority-interface control, not Javid's actual review.",
        reviewed_subject_hashes=[sha256((root / "MANIFEST.json").read_bytes())],
    )
    record["review_hash"] = content_hash(record)
    review_path = tmp_path / "synthetic-review.json"
    review_path.write_bytes(vr.canonical(record))
    digest = vr.digest(review_path.read_bytes())
    assert refresh.adoption_authority(root, review_path, digest).decision == "accepted"
    with pytest.raises(ValueError):
        refresh.adoption_authority(tmp_path, review_path, digest)
    (root / "MANIFEST.json").write_bytes(b"changed")
    with pytest.raises(ValueError):
        refresh.adoption_authority(root, review_path, digest)
    with pytest.raises(ValueError):
        refresh.adoption_authority(root, review_path, "0" * 64)


@pytest.mark.parametrize(
    "source", ["rk/engine/orchestrator.py", "rk/components/loader.py", "rk/schema/channels.py"]
)
def test_rehashed_pinned_source_substitution_refuses(reference, tmp_path, source):
    root = tmp_path / "source-substitution"
    shutil.copytree(reference, root)
    path = root / source
    path.write_bytes(path.read_bytes() + b"\n# altered after capture\n")
    rehash(root)
    with pytest.raises(ValueError, match="pinned source bytes"):
        refresh.audit_candidate(root)


def test_synthetic_reference_ignores_mutable_canonical(tmp_path, monkeypatch):
    class Factory:
        def mktemp(self, name):
            directory = tmp_path / name
            directory.mkdir()
            return directory

    monkeypatch.setattr(ui, "ADOPTED", tmp_path / "canonical-must-not-be-read")
    root = reference.__wrapped__(Factory())
    rows = json.loads((root / "parity/fixtures.json").read_bytes())
    assert len(rows) == len({row["id"] for row in rows}) == 1008
    assert sum(row["component_params_file"] == "components/npu-l4.yaml" for row in rows) == 144
    events = json.loads((root / "parity/refusals.json").read_bytes())
    assert len(events) == 4
    assert all("SYNTHETIC" in event["message"] for event in events)
    assert (root / "SYNTHETIC-REFERENCE").is_file()
