"""Bounded real-adopted validation; no reference synthesis, oracle, or source edits."""

import argparse
import gc
import hashlib
import importlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

from uarch_contract.hashing import content_hash, resolve_pointer
from uarch_contract.report_context import RenderSpec

from rkuarch.report.complete import render_verified
from rkuarch.table.artifacts import load_verified_report_inputs, verify_report_inputs
from rkuarch.table.build import write_table
from scripts import u2_inputs as ui
from tests import u2_comparison as comparison
from tests import u2_refresh as refresh

BASELINE = "7aab97d35ca554b0477ac5719dfa4e5306f8bbab"
MANIFEST = "2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44"
INPUTS = "81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898"
REVIEW = "4aad401c01a828a1463853796c38c19c20359f4649e2c706880c6e8a1cdcdbcf"
RATIOS = ("raw_rel", "residual_rel", "signed_adjustment_rel", "absolute_adjustment_rel")
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RECEIVED = ROOT.parent / "rk-uarch-u2-integration/docs/reviews/U2-adoption-v1-execution/runtime"
AUTHORITY = ROOT / "docs/reviews/U2-adoption-v1-execution/adoption-review.json"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def inventory(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def equal(left, right):
    total = 0
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            x, y = a.read(1048576), b.read(1048576)
            assert x == y, (str(left), str(right), total)
            total += len(x)
            if not x:
                return total


def compare_files(left, right, names):
    return {
        n: {"bytes": equal(left / n, right / n), "sha256": sha(left / n)} for n in sorted(names)
    }


def preflight():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()

    assert git("rev-parse", "HEAD") == BASELINE
    assert git("branch", "--show-current") == "u2/honesty"
    assert not git("diff", "--name-only", BASELINE)
    assert not git("diff", "--cached", "--name-only")
    assert sha(ui.ADOPTED / "MANIFEST.json") == MANIFEST
    assert sha(AUTHORITY) == REVIEW
    audit = refresh.audit_candidate(ui.ADOPTED)
    assert audit["input_manifest_sha256"] == INPUTS
    authority = refresh.adoption_authority(ui.ADOPTED, AUTHORITY, REVIEW)
    support = json.loads((ui.ADOPTED / "u2-inputs/support-files.json").read_text())
    assert len(support) == 84
    assert all(sha(ROOT / n) == h for n, h in support.items())
    expected = {
        "table.report.html": "f8456f7ea568660066714ab0d54274f726c35611f3be091a35388bae9231772c",
        "table.report.md": "e293df4fec1ce6ac9403c6d1944f0942d1bf22dda43a2a24a435127a6007afbd",
    }
    assert all(sha(RECEIVED / n) == h for n, h in expected.items())
    # Stream checker has discriminating negative controls, including a partial last block.
    scratch = Path(tempfile.mkdtemp(prefix="u2-real-driver-controls-"))
    a, b = scratch / "a", scratch / "b"
    a.write_bytes(b"x" * (1048576 + 3))
    b.write_bytes(a.read_bytes())
    assert equal(a, b) == 1048579
    for changed in (b"x" * 1048578, b"x" * 1048578 + b"y"):
        b.write_bytes(changed)
        try:
            equal(a, b)
        except AssertionError:
            pass
        else:
            raise AssertionError("byte checker missed a mutation")
    return dict(
        baseline=BASELINE,
        branch=git("branch", "--show-current"),
        tracked_and_index_clean=True,
        audit=audit,
        support_files=84,
        review_sha256=REVIEW,
        review_identity=authority.review_hash,
        received_root=str(RECEIVED),
        received_hidden=expected,
        received_capture_sha256=sha(RECEIVED / "physical-capture.json"),
        driver_sha256=sha(Path(__file__)),
        python=sys.version,
        platform=platform.platform(),
        argv=sys.argv,
        environment={
            k: os.environ.get(k)
            for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "OMP_NUM_THREADS")
        },
        byte_checker_controls="equal plus changed byte and changed length passed",
        synthetic_reference=False,
        allow_synthetic_presentation=False,
    )


def coverage(v):
    ratios = {}
    for ci, c in enumerate(v.comparisons):
        assert len(c.fixtures) == 1008 and c.classification == "executed_comparison"
        for fi, f in enumerate(c.fixtures):
            for ki, ch in enumerate(f.channels):
                for name in RATIOS:
                    ratios[f"/comparisons/{ci}/fixtures/{fi}/channels/{ki}/{name}"] = (
                        getattr(ch, name),
                        f.execution,
                    )
    assert len(ratios) == 40320
    assert len(v.table.rows) == 24
    assert len(v.dependencies.recipes) == 46296
    assert len(v.dependencies.source_recipes) == 14904
    recipes = {r.metric_path: r for r in v.dependencies.recipes}
    assert len(recipes) == len(v.dependencies.recipes)
    assert {p for p in recipes if p.startswith("/comparisons/")} == set(ratios)
    sources = {(r.artifact_hash, r.recipe.metric_path): r for r in v.dependencies.source_recipes}

    def key(selector):
        return (selector.kind, selector.artifact_hash, selector.json_pointer)

    @lru_cache(None)
    def expand_source(identity, pointer):
        source = sources[(identity, pointer)]
        leaves = {("result_field", identity, pointer)}
        for selector in source.recipe.selectors:
            leaves.update(
                expand_source(selector.artifact_hash, selector.json_pointer)
                if selector.kind == "result_field"
                else {key(selector)}
            )
        return frozenset(leaves)

    closures = {}
    for path in ratios:
        leaves = set()
        for selector in recipes[path].selectors:
            leaves.update(
                expand_source(selector.artifact_hash, selector.json_pointer)
                if selector.kind == "result_field"
                else {key(selector)}
            )
        models = {
            content_hash(resolve_pointer(v.artifacts[h], p))
            for kind, h, p in leaves
            if kind == "model_evidence"
        }
        closures[path] = (frozenset(leaves), models)
    return ratios, closures


def save_render(v, directory, mode, expectations):
    result = render_verified(v, show_unvalidated_predictions=(mode == "opt-in"))
    assert not result.render_spec.allow_synthetic_presentation
    ratios, closures = expectations
    seen = {
        p
        for p in result.metrics
        if p.startswith("/comparisons/") and p.rsplit("/", 1)[-1] in RATIOS
    }
    assert seen == set(ratios)
    # Parse whole outputs once, avoiding repeated scans of the large documents.
    html_paths = set(re.findall(r"<dt>(/comparisons/[^<]+)</dt>", result.html))
    md_paths = {
        p.replace("\\_", "_")
        for p in re.findall(r"^\*\*(/comparisons/[^\n]+?)\*\*:", result.markdown, re.M)
    }
    assert set(ratios) <= html_paths and set(ratios) <= md_paths
    counts = Counter()
    proof_rows = []
    for path, (value, execution) in ratios.items():
        metric = result.metrics[path]
        a = metric.assessment
        wanted, models = closures[path]
        assert {(s.kind, s.artifact_hash, s.json_pointer) for s in a.contributors} == wanted, path
        assert {m.model_identity_hash for m in a.models} == models, path
        assert a.badge == "stub" and a.error_band is None
        assert all(m.error_band is None for m in a.models)
        eligible = (
            value is not None
            and execution == "executed"
            and a.complete
            and a.display_recipe
            and a.nonempty
            and not a.synthetic
            and mode == "opt-in"
        )
        assert (metric.number is not None) == eligible, (path, a, metric.number)
        if eligible:
            assert metric.number == repr(0.0 if value == 0 else float(value))
        assert "STUB" in metric.text and "error unknown" in metric.text
        counts["visible" if eligible else "hidden"] += 1
        counts["null_value"] += value is None
        counts["synthetic_assessment"] += a.synthetic
        counts["missing_or_incomplete"] += not (a.complete and a.display_recipe and a.nonempty)
        proof_rows.append(
            dict(
                path=path,
                execution=execution,
                value=value,
                contributors=len(wanted),
                model_identities=sorted(models),
                contributor_set_sha256=content_hash(sorted(wanted)),
            )
        )
    assert counts["synthetic_assessment"] == 0
    if mode == "opt-in":
        assert counts["visible"] > 0
    else:
        assert all(
            m.number is None for p, m in result.metrics.items() if p.startswith("/comparisons/")
        )
    assert "Energy is unverified" in result.html and "Energy is unverified" in result.markdown
    directory.mkdir(parents=True, exist_ok=True)
    for suffix, text in (("html", result.html), ("md", result.markdown)):
        (directory / f"{mode}.{suffix}").write_text(text)
    put(directory / f"{mode}-render-spec.json", result.render_spec.model_dump(mode="json"))
    # Full path/contributor identity index is an output artifact, not a source manifest.
    put(directory.parent / (directory.name + "-" + mode + "-coverage.json"), proof_rows)
    metadata = dict(
        ratio_paths=len(ratios),
        counters=dict(counts),
        render_spec=result.render_spec.model_dump(mode="json"),
        files={
            n: dict(bytes=(directory / n).stat().st_size, sha256=sha(directory / n))
            for n in (f"{mode}.html", f"{mode}.md", f"{mode}-render-spec.json")
        },
    )
    del result, proof_rows
    gc.collect()
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--resume-written-package", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    pre = preflight()
    if args.preflight:
        put(HERE / "preflight.json", pre)
        print("real authority/support/input and driver preconditions passed", flush=True)
        return
    out = args.output
    assert out is not None
    out.mkdir(parents=True, exist_ok=args.resume_written_package)
    put(HERE / "output-location.json", dict(root=str(out.resolve()), baseline=BASELINE))
    state = (
        json.loads((HERE / "attempt-1-progress.json").read_text())
        if args.resume_written_package
        else dict(preflight=pre, phases=[], output_root=str(out.resolve()))
    )
    state.update(status="running", resume_preflight=pre)
    if args.resume_written_package:
        assert any(
            p["name"] == "public_write_table" and p["status"] == "passed" for p in state["phases"]
        )
        state["source_blocker"] = (
            "RR-C1: condition ordering changes table identity after canonical saved-input replay"
        )
        state["received_hidden_control"] = (
            "Not reused: table identity differs; original failed byte comparison preserved"
        )

    def flush():
        put(HERE / "progress.json", state)

    def phase(name, fn):
        row = dict(name=name, status="running")
        state["phases"].append(row)
        flush()
        print(name, "started", flush=True)
        start = time.monotonic()
        try:
            result = fn()
        except BaseException as exc:
            row.update(status="failed", error=repr(exc), elapsed_s=time.monotonic() - start)
            state["status"] = "failed"
            flush()
            raise
        row.update(status="passed", elapsed_s=time.monotonic() - start)
        flush()
        print(name, row["elapsed_s"], flush=True)
        return result

    def trap(*a, **kw):
        raise AssertionError("producer called during saved-input replay")

    nominal = comparison.nominal.evaluate_nominal
    calls = [0]

    def counted(*a, **kw):
        calls[0] += 1
        return nominal(*a, **kw)

    comparison.prepare_h1 = trap
    comparison.physical_point = trap
    importlib.import_module("rkuarch.workload.prepare").prepare = trap
    importlib.import_module("rkuarch.engines.analytic.core").run_analytic = trap
    comparison.nominal.evaluate_nominal = counted
    state["physical_traps"] = [
        "tests.u2_comparison.prepare_h1",
        "tests.u2_comparison.physical_point",
        "rkuarch.workload.prepare.prepare",
        "rkuarch.engines.analytic.core.run_analytic",
    ]
    package = None
    run = None
    if not args.resume_written_package:
        received_capture = json.loads((RECEIVED / "physical-capture.json").read_bytes())
        run = phase(
            "public_adopted_consume_received_physical_replay",
            lambda: refresh.consume_adopted(
                adoption_review=AUTHORITY, review_sha256=REVIEW, physical_replay=received_capture
            ),
        )
        assert calls[0] == 1008 and not run["synthetic"]
        assert run["inputs"].manifest_sha256 == INPUTS
        assert Counter(f.execution for f in run["physical"].fixtures) == {
            "not_run": 864,
            "executed": 96,
            "execution_failed": 48,
        }
        assert len(run["physical_errors"]) == 48
        assert all("WeightCapacityExceeded" in e["reason"] for e in run["physical_errors"])
        assert not run["nominal_errors"]
        assert (run["nominal"].gate_outcome, run["nominal"].evidence_outcome) == (
            "compatibility_pass",
            "refused",
        )
        assert (run["physical"].gate_outcome, run["physical"].evidence_outcome) == (
            "not_assessed",
            "execution_failed",
        )
        assert all(len(run[n].precision_refusal_observations) == 4 for n in ("nominal", "physical"))
        phase("save_adopted_comparisons", lambda: refresh.save_comparisons(run, out / "captured"))
        names = {
            n
            for n in inventory(RECEIVED)
            if n.startswith("comparison-artifacts/")
            or n in {"nominal.json", "physical.json", "inventory.json", "physical-capture.json"}
        }
        assert names == {n for n in inventory(out / "captured") if n != "observations.json"}
        received_equal = phase(
            "received_comparison_bytes", lambda: compare_files(RECEIVED, out / "captured", names)
        )
        put(out / "received-comparison-byte-equality.json", received_equal)
        state["nominal_calls_initial"] = calls[0]
        state["captured"] = dict(
            nominal_gate=run["nominal"].gate_outcome,
            nominal_evidence=run["nominal"].evidence_outcome,
            physical_gate=run["physical"].gate_outcome,
            physical_evidence=run["physical"].evidence_outcome,
            physical_states=dict(Counter(f.execution for f in run["physical"].fixtures)),
            direct_observations_per_track=4,
            physical_errors=48,
        )
        comparison.nominal.evaluate_nominal = trap
        state["packaging_nominal_trap"] = "tests.u2_comparison.nominal.evaluate_nominal"
        package = phase(
            "package_saved_results_all_producers_trapped", lambda: refresh.report_package(run)
        )
        phase("public_write_table", lambda: write_table(package, out / "report/table.json"))
        package_names = inventory(out / "report")
        assert package_names == {
            n for n in inventory(RECEIVED) if n == "table.json" or n.startswith("artifacts/")
        }
        put(
            out / "received-package-byte-equality.json",
            phase(
                "received_full_package_bytes",
                lambda: compare_files(RECEIVED, out / "report", package_names),
            ),
        )
    else:
        package_names = inventory(out / "report")
        assert package_names == {
            n for n in inventory(RECEIVED) if n == "table.json" or n.startswith("artifacts/")
        }
        comparison.nominal.evaluate_nominal = trap
    verified = phase(
        "public_disk_load", lambda: load_verified_report_inputs(out / "report/table.json")
    )
    memory = phase(
        "public_memory_verify", lambda: verify_report_inputs(verified.table, verified.artifacts)
    )
    assert memory == verified
    del memory
    expect = phase("independent_ratio_contributor_inventory", lambda: coverage(verified))
    state["coverage"] = dict(
        ratios=len(expect[0]),
        rows=len(verified.table.rows),
        recipes=len(verified.dependencies.recipes),
        sources=len(verified.dependencies.source_recipes),
        raw_blobs=sum(isinstance(v, bytes) for v in verified.artifacts.values()),
        package_files=len(package_names),
    )
    state["renders"] = {}
    for mode in ("hidden", "opt-in"):
        state["renders"][mode] = phase(
            "render_" + mode, lambda mode=mode: save_render(verified, out / "report", mode, expect)
        )
        flush()
    if not args.resume_written_package:
        state["received_hidden_bytes_equal"] = {
            suffix: equal(
                RECEIVED / ("table.report." + suffix), out / "report" / ("hidden." + suffix)
            )
            for suffix in ("html", "md")
        }
    for mode in ("hidden", "opt-in"):
        repeated = phase(
            "repeat_render_" + mode,
            lambda mode=mode: save_render(verified, out / "repeat", mode, expect),
        )
        assert repeated == state["renders"][mode]
    repeated_names = inventory(out / "repeat")
    assert len(repeated_names) == 6
    put(
        out / "repeat-byte-equality.json",
        phase(
            "repeat_stream_bytes",
            lambda: compare_files(out / "report", out / "repeat", repeated_names),
        ),
    )
    comparison.nominal.evaluate_nominal = counted
    saved_capture = json.loads((out / "captured/physical-capture.json").read_bytes())
    calls_before_replay = calls[0]
    replay = phase(
        "new_saved_physical_replay_nominal_executes",
        lambda: refresh.consume_adopted(
            adoption_review=AUTHORITY, review_sha256=REVIEW, physical_replay=saved_capture
        ),
    )
    assert calls[0] - calls_before_replay == 1008
    if run is not None:
        assert replay["artifacts"] == run["artifacts"]
    phase(
        "save_replayed_comparisons",
        lambda: refresh.save_comparisons(replay, out / "replayed-captured"),
    )
    assert inventory(out / "captured") == inventory(out / "replayed-captured")
    put(
        out / "replayed-comparison-byte-equality.json",
        phase(
            "replayed_comparison_bytes",
            lambda: compare_files(
                out / "captured", out / "replayed-captured", inventory(out / "captured")
            ),
        ),
    )
    comparison.nominal.evaluate_nominal = trap
    again = phase("replay_package_all_producers_trapped", lambda: refresh.report_package(replay))
    assert again.table == verified.table
    if package is not None:
        assert again == package
    phase("replay_public_write", lambda: write_table(again, out / "replay-report/table.json"))
    assert inventory(out / "replay-report") == package_names
    put(
        out / "replayed-package-byte-equality.json",
        phase(
            "replayed_full_package_bytes",
            lambda: compare_files(out / "report", out / "replay-report", package_names),
        ),
    )
    loaded = phase(
        "replay_public_disk_load",
        lambda: load_verified_report_inputs(out / "replay-report/table.json"),
    )
    assert loaded == verified
    for mode in ("hidden", "opt-in"):
        rendered = phase(
            "replay_render_" + mode,
            lambda mode=mode: save_render(loaded, out / "replay-report", mode, expect),
        )
        assert rendered == state["renders"][mode]
    assert inventory(out / "report") == inventory(out / "replay-report")
    put(
        out / "replayed-all-byte-equality.json",
        phase(
            "replayed_all_stream_bytes",
            lambda: compare_files(out / "report", out / "replay-report", inventory(out / "report")),
        ),
    )
    state["nominal_calls_total"] = state["nominal_calls_initial"] + calls[0] - calls_before_replay
    state["capability_refusals"] = {}
    for field, value in (
        ("table_hash", "sha256:" + "0" * 64),
        ("report_context_hash", "sha256:" + "0" * 64),
        ("renderer_version", "unreviewed-renderer"),
    ):
        bad = dict(state["renders"]["opt-in"]["render_spec"])
        bad[field] = value
        bad["render_hash"] = content_hash(bad, exclude=("render_hash",))

        def refusal(bad=bad):
            try:
                render_verified(verified, render_spec=RenderSpec.model_validate(bad))
            except ValueError as exc:
                assert str(exc) == "RenderIdentityBindingMismatch"
                return str(exc)
            raise AssertionError("changed capability accepted")

        state["capability_refusals"][field] = phase("capability_" + field, refusal)
        flush()
    assert preflight()["audit"] == pre["audit"]
    files = {
        n: dict(bytes=(out / n).stat().st_size, sha256=sha(out / n)) for n in sorted(inventory(out))
    }
    put(out / "artifact-index.json", files)
    (out / "SHA256SUMS").write_text(
        "".join(v["sha256"] + "  " + n + "\n" for n, v in files.items())
        + sha(out / "artifact-index.json")
        + "  artifact-index.json\n"
    )
    state["artifact_manifest"] = dict(
        path=str(out / "SHA256SUMS"), sha256=sha(out / "SHA256SUMS"), entries=len(files) + 1
    )
    state["status"] = (
        "completed_with_source_blocker" if state.get("source_blocker") else "completed"
    )
    flush()


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        progress = HERE / "progress.json"
        if progress.exists():
            failed = json.loads(progress.read_text())
            failed.update(status="failed", error=repr(exc))
            put(progress, failed)
        raise
