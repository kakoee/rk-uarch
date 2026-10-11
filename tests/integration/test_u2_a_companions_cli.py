"""Public workflow tests; any review fixtures are explicitly synthetic scaffolding."""

import json

import pytest
from typer.testing import CliRunner

from rkuarch.cli import app
from tests.unit import test_u2_a_companions as helpers


@pytest.fixture(name="saved")
def saved_capture(tmp_path):
    return helpers.saved.__wrapped__(tmp_path)


RUN = CliRunner()


def options(c, directory, root):
    from uarch_contract.hashing import canonical_json

    for name, value in (("prepared", c.bundle), ("assumptions", c.assumptions)):
        (root / (name + ".json")).write_text(canonical_json(value))
    return [
        "--prepared-input",
        str(root / "prepared.json"),
        "--assumptions",
        str(root / "assumptions.json"),
        "--capture-dir",
        str(directory),
    ]


def test_public_assumptions_and_deterministic_unreviewed_draft(saved, tmp_path):
    c, directory = saved
    out = tmp_path / "physical.json"
    result = RUN.invoke(app, ["assumptions", "--model", "physical-resolved", "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_bytes()) == c.assumptions.model_dump(mode="json")
    opts = options(c, directory, tmp_path)
    for name in ("draft-a", "draft-b"):
        result = RUN.invoke(app, ["companions", "draft", *opts, "--output", str(tmp_path / name)])
        assert result.exit_code == 0, result.output
        assert "UNREVIEWED" in result.output
    a, b = tmp_path / "draft-a", tmp_path / "draft-b"
    assert {p.name: p.read_bytes() for p in a.iterdir()} == {
        p.name: p.read_bytes() for p in b.iterdir()
    }
    assert "UNREVIEWED" in (a / "README.txt").read_text()
    deps = json.loads((a / "metric-dependencies.json").read_text())
    assert deps["review_hash"] == "sha256:" + "0" * 64
    assert not any(
        "review_hash" in json.loads(p.read_text())
        and json.loads(p.read_text()).get("format") == "uarch-evidence-review/1"
        for p in a.glob("*.json")
    )


def test_draft_preflights_all_outputs(saved, tmp_path):
    c, directory = saved
    out = tmp_path / "draft"
    out.mkdir()
    (out / "metric-dependencies.json").write_text("conflict")
    result = RUN.invoke(
        app, ["companions", "draft", *options(c, directory, tmp_path), "--output", str(out)]
    )
    assert result.exit_code == 2 and "OutputConflict" in result.output
    assert sorted(p.name for p in out.iterdir()) == ["metric-dependencies.json"]


def assembly_inputs(c, directory, root):
    """Synthetic declaration reviews for tests ONLY; not an actual review or public exit."""
    from uarch_contract.hashing import canonical_json

    from rkuarch.table.companions import draft_companions
    from tests.unit.test_u2_a_loader import ZERO, reviewed

    card, deps, _ = draft_companions(c)
    store = {}
    reviewed_deps = deps.model_dump(mode="json")
    reviewed(reviewed_deps, "dependencies_hash", store)
    registry = dict(
        format="uarch-family-registry/1",
        registry_hash=ZERO,
        review_hash=ZERO,
        version="synthetic-companion-test/1",
        entries=[
            dict(family="synthetic-test-family", hardware_spec_hash=c.request.hardware_spec_hash)
        ],
    )
    reviewed(registry, "registry_hash", store)
    values = {
        "recipes": deps,
        "recipe-review": store[reviewed_deps["review_hash"]],
        "registry": registry,
        "registry-review": store[registry["review_hash"]],
        "model-card": card,
    }
    opts = options(c, directory, root)
    for name, value in values.items():
        path = root / (name + ".json")
        path.write_text(canonical_json(value))
        opts += ["--" + name, str(path)]
    return opts + [
        "--no-comparisons",
        "--artifact-dir",
        str(root / "artifacts"),
        "--output",
        str(root / "context.json"),
    ]


def test_assembly_adapter_uses_exact_peer_api_standin_only(saved, tmp_path, monkeypatch):
    """A disk/CLI adapter test, NOT production assembly or the complete public chain."""
    import sys
    import types

    from uarch_contract.hashing import content_hash, review_subject_hash
    from uarch_contract.report_context import ReportContext

    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    calls = []

    def standin(actual, *, dependencies, registry, model_card, comparison_hashes, artifacts):
        assert actual == c and comparison_hashes == ()
        assert dependencies.review_hash != "sha256:" + "0" * 64
        assert (
            review_subject_hash(dependencies)
            in artifacts[dependencies.review_hash]["reviewed_subject_hashes"]
        )
        calls.append(actual)
        # Valid carrier only: this stand-in does NOT perform B's assembly validation.
        ctx = ReportContext(
            format="uarch-report-context/2",
            context_hash="sha256:" + "0" * 64,
            assumptions_hash=c.assumptions.assumptions_hash,
            comparison_hashes=(),
            evidence_index={},
            family_registry_hash=registry.registry_hash,
            limitations=("SYNTHETIC STAND-IN; not production validation",),
            metric_dependencies_hash=dependencies.dependencies_hash,
            model_identity=c.assumptions.model,
            request_hash=content_hash(c.request),
            used_energy_families=(),
            verification_hashes=(),
        )
        ctx = ctx.model_copy(update={"context_hash": content_hash(ctx, exclude=("context_hash",))})
        return ctx, artifacts

    monkeypatch.setitem(
        sys.modules,
        "rkuarch.provenance.companions",
        types.SimpleNamespace(assemble_stub_context=standin),
    )
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 0, result.output
    assert len(calls) == 1 and (tmp_path / "context.json").exists()
    data = json.loads((tmp_path / "context.json").read_text())
    assert data["evidence_index"] == {} and data["comparison_hashes"] == []
    assert (tmp_path / "artifacts" / (data["metric_dependencies_hash"][7:] + ".json")).exists()


def test_assembly_requires_explicit_comparison_intake(saved, tmp_path):
    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    opts.remove("--no-comparisons")
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2 and "comparison" in result.output.lower()
    assert not (tmp_path / "context.json").exists()


@pytest.mark.parametrize(
    "missing_name", ["rkuarch.provenance.companions", "synthetic_peer_dependency"]
)
def test_missing_peer_refuses_without_breaking_other_commands(
    saved, tmp_path, monkeypatch, missing_name
):
    import builtins

    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    original = builtins.__import__
    attempts = []
    failure = ModuleNotFoundError("synthetic import failure", name=missing_name)

    def missing(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "rkuarch.provenance.companions":
            attempts.append(fromlist)
            raise failure
        return original(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", missing)
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert attempts == [("assemble_stub_context",)]
    if missing_name == "rkuarch.provenance.companions":
        assert result.exit_code == 2 and "PeerImplementationMissing" in result.output
    else:
        assert result.exception is failure
        assert "PeerImplementationMissing" not in result.output
    assert not (tmp_path / "context.json").exists()
    assert (
        RUN.invoke(
            app,
            [
                "assumptions",
                "--model",
                "physical-resolved",
                "--output",
                str(tmp_path / "still-usable.json"),
            ],
        ).exit_code
        == 0
    )


def test_saved_table_replay_no_producers_with_synthetic_existing_context(
    saved, tmp_path, monkeypatch
):
    """Uses real builder/loader with existing synthetic context, NOT the pending B assembly."""
    from uarch_contract.hashing import canonical_json

    from rkuarch.table.artifacts import load_verified_report_inputs
    from tests.integration.test_u2_a_replay import companions, package
    from tests.unit.test_u2_a_companions import block_producers

    c, directory = saved
    expected = package(c)
    ctx, card, store = companions(c)
    artifacts = tmp_path / "companions"
    artifacts.mkdir()
    for h, value in store.items():
        (artifacts / (h[7:] + ".json")).write_text(canonical_json(value))
    (tmp_path / "context.json").write_text(canonical_json(ctx))
    (tmp_path / "card.json").write_text(canonical_json(card))
    opts = options(c, directory, tmp_path)
    block_producers(monkeypatch)
    out = tmp_path / "replay/table.json"
    result = RUN.invoke(
        app,
        [
            "table",
            *opts,
            "--context",
            str(tmp_path / "context.json"),
            "--model-card",
            str(tmp_path / "card.json"),
            "--artifact-dir",
            str(artifacts),
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.read_bytes() == canonical_json(expected.table).encode() + b"\n"
    assert load_verified_report_inputs(out).results == c.results


def test_capture_replay_rejects_model_route_before_preparation(saved, tmp_path, monkeypatch):
    from tests.unit.test_u2_a_companions import block_producers

    _, directory = saved
    block_producers(monkeypatch)
    result = RUN.invoke(
        app,
        [
            "table",
            "--model",
            "llama-3.1-8b",
            "--capture-dir",
            str(directory),
            "--assumptions",
            "absent",
            "--context",
            "absent",
            "--model-card",
            "absent",
            "--artifact-dir",
            "absent",
            "--output",
            str(tmp_path / "no"),
        ],
    )
    assert result.exit_code == 2 and "CaptureReplay" in result.output


def require_real_peer():
    from rkuarch.provenance.companions import assemble_stub_context

    assert assemble_stub_context.__module__ == "rkuarch.provenance.companions"


def test_real_peer_roundtrip_relocation_determinism_and_offline_replay(
    saved, tmp_path, monkeypatch
):
    """Received production B code; reviews are synthetic, never an external-review exit."""
    import shutil

    from rkuarch.table.artifacts import load_verified_report_inputs
    from tests.unit.test_u2_a_companions import block_producers

    require_real_peer()
    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    block_producers(monkeypatch)
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 0, result.output
    relocated = tmp_path / "relocated"
    relocated.mkdir()
    for name in ("prepared.json", "assumptions.json", "model-card.json", "context.json"):
        shutil.copyfile(tmp_path / name, relocated / name)
    shutil.copytree(directory, relocated / "capture")
    shutil.copytree(tmp_path / "artifacts", relocated / "artifacts")
    tables, reports = [], []
    for root in (tmp_path, relocated):
        out = root / "table-out/table.json"
        result = RUN.invoke(
            app,
            [
                "table",
                "--prepared-input",
                str(root / "prepared.json"),
                "--assumptions",
                str(root / "assumptions.json"),
                "--capture-dir",
                str(root / "capture"),
                "--model-card",
                str(root / "model-card.json"),
                "--context",
                str(root / "context.json"),
                "--artifact-dir",
                str(root / "artifacts"),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        verified = load_verified_report_inputs(out)
        assert verified.table.comparison_state == "not_attempted"
        assert verified.model_card.energy_verification is None
        assert verified.model_card.validated_error_band is None
        assert verified.results == c.results
        tables.append(out.read_bytes())
        outputs = []
        for optin in (False, True):
            report = root / ("optin.html" if optin else "default.html")
            markdown = report.with_suffix(".md")
            args = ["report", str(out), "--output", str(report), "--markdown", str(markdown)]
            if optin:
                args += ["--show-unvalidated-predictions", "--allow-synthetic-presentation"]
            result = RUN.invoke(app, args)
            assert result.exit_code == 0, result.output
            outputs.append((report.read_bytes(), markdown.read_bytes()))
        reports.append(outputs)
    assert tables[0] == tables[1] and reports[0] == reports[1]
    assert reports[0][0] != reports[0][1]  # Opt-in changes presentation, not output guards.
    conflict = RUN.invoke(
        app,
        [
            "report",
            str(tmp_path / "table-out/table.json"),
            "--output",
            str(tmp_path / "default.html"),
            "--markdown",
            str(tmp_path / "default.md"),
            "--show-unvalidated-predictions",
        ],
    )
    assert conflict.exit_code == 2 and "OutputConflict" in conflict.output
    assert (tmp_path / "default.html").read_bytes() == reports[0][0][0]
    assert (tmp_path / "default.md").read_bytes() == reports[0][0][1]


@pytest.mark.parametrize(
    "mutation", ["missing-review", "stale-subject", "unreviewed", "wrong-model"]
)
def test_real_peer_review_and_model_refusals(saved, tmp_path, mutation):
    from uarch_contract.hashing import canonical_json, content_hash

    require_real_peer()
    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    path = tmp_path / "recipe-review.json"
    if mutation == "missing-review":
        path.unlink()
    elif mutation in ("stale-subject", "unreviewed"):
        raw = json.loads(path.read_text())
        if mutation == "stale-subject":
            raw["reviewed_subject_hashes"] = ["sha256:" + "f" * 64]
        else:
            raw["decision"] = "rejected"
        raw["review_hash"] = content_hash(raw, exclude=("review_hash",))
        path.write_text(canonical_json(raw))
    else:
        path = tmp_path / "model-card.json"
        raw = json.loads(path.read_text())
        raw["model_id"]["engine_version"] = "substitute"
        path.write_text(canonical_json(raw))
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2, result.output
    assert not (tmp_path / "context.json").exists()


def test_fresh_public_subprocess_complete_chain_and_relocated_replay(saved, tmp_path):
    import os
    from pathlib import Path

    from uarch_contract.hashing import canonical_json

    from tests.integration.test_u2_a_stage2_cli import cli
    from tests.u2_a_companion_inputs import review_public_draft

    require_real_peer()
    c, _ = saved
    trap = tmp_path / "trap"
    trap.mkdir()
    (trap / "sitecustomize.py").write_text(
        "import rkuarch.table.build as b\n"
        "import rkuarch.workload.prepared as p\n"
        "import rkuarch.engines.analytic.core as c\n"
        "def forbidden(*a, **kw):\n raise RuntimeError('PRODUCER_DISABLED')\n"
        "b.capture = p.prepare_engine_job = p.execute_prepared_point = c.run_analytic = forbidden\n"
        "import sys\n"
        "class Trap:\n"
        " def find_spec(self, fullname, path=None, target=None):\n"
        "  if fullname == 'rkuarch.workload.prepare': raise RuntimeError('PRODUCER_DISABLED')\n"
        "sys.meta_path.insert(0, Trap())\n"
    )
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=f"{trap}:{root}:{root / 'src'}:{root / 'contract'}",
    )

    def snapshot(directory):
        return {
            str(p.relative_to(directory)): p.read_bytes()
            for p in directory.rglob("*")
            if p.is_file()
        }

    def complete_public_outputs(directory):
        # Real B production assembly; only declaration review inputs are SYNTHETIC.
        commands = [
            (
                "companions",
                "assemble",
                "--prepared-input",
                directory / "prepared.json",
                "--assumptions",
                directory / "assumptions.json",
                "--capture-dir",
                directory / "capture",
                "--recipes",
                directory / "draft/metric-dependencies.json",
                "--recipe-review",
                directory / "recipe-review.json",
                "--registry",
                directory / "registry.json",
                "--registry-review",
                directory / "registry-review.json",
                "--model-card",
                directory / "draft/model-card.json",
                "--no-comparisons",
                "--artifact-dir",
                directory / "companions",
                "--output",
                directory / "context.json",
            ),
            (
                "table",
                "--prepared-input",
                directory / "prepared.json",
                "--assumptions",
                directory / "assumptions.json",
                "--capture-dir",
                directory / "capture",
                "--context",
                directory / "context.json",
                "--model-card",
                directory / "draft/model-card.json",
                "--artifact-dir",
                directory / "companions",
                "--output",
                directory / "table/table.json",
            ),
        ]
        for mode in ("default", "optin"):
            report_args = [
                "report",
                directory / "table/table.json",
                "--output",
                directory / (mode + ".html"),
                "--markdown",
                directory / (mode + ".md"),
            ]
            if mode == "optin":
                report_args += ["--show-unvalidated-predictions", "--allow-synthetic-presentation"]
            commands.append(tuple(report_args))
        for command in commands:
            result = cli(*command, env=env)
            assert result.returncode == 0, result.stderr.decode()
        from rkuarch.table.artifacts import load_verified_report_inputs

        verified = load_verified_report_inputs(directory / "table/table.json")
        assert verified.model_card.badge == "stub"
        assert verified.model_card.validated_error_band is None
        assert verified.model_card.energy_verification is None
        assert verified.results == c.results
        assert "1.892e-06" not in (directory / "default.md").read_text()
        assert "1.892e-06" in (directory / "optin.md").read_text()
        assert "STUB" in (directory / "default.md").read_text()
        assert "STUB" in (directory / "optin.md").read_text()

    snapshots = []
    replay_inputs = None
    for name in ("fresh-a", "fresh-b"):
        dest = tmp_path / name
        dest.mkdir()
        (dest / "intent.json").write_text(canonical_json(c.bundle.intent))
        (dest / "hardware.json").write_text(canonical_json(c.bundle.hardware_spec))
        commands = [
            ("assumptions", "--model", "physical-resolved", "--output", dest / "assumptions.json"),
            (
                "prepare",
                dest / "hardware.json",
                "--intent",
                dest / "intent.json",
                "--output",
                dest / "prepared.json",
            ),
            (
                "capture",
                "--prepared-input",
                dest / "prepared.json",
                "--assumptions",
                dest / "assumptions.json",
                "--output",
                dest / "capture",
            ),
        ]
        for args in commands:
            result = cli(*args)
            assert result.returncode == 0, result.stderr.decode()
        args = (
            "companions",
            "draft",
            "--prepared-input",
            dest / "prepared.json",
            "--assumptions",
            dest / "assumptions.json",
            "--capture-dir",
            dest / "capture",
            "--output",
            dest / "draft",
        )
        result = cli(*args, env=env)
        assert result.returncode == 0, result.stderr.decode()
        review_public_draft(dest)
        replay_inputs = snapshot(dest)
        complete_public_outputs(dest)
        snapshots.append(snapshot(dest))
        negative = cli(
            "capture",
            "--prepared-input",
            dest / "prepared.json",
            "--assumptions",
            dest / "assumptions.json",
            "--output",
            dest / "forbidden",
            env=env,
        )
        assert negative.returncode != 0 and b"PRODUCER_DISABLED" in negative.stderr
    assert snapshots[0] == snapshots[1]

    # Relocate only saved inputs. All assembled/table/report outputs are created anew
    # with preparation and analytic producers disabled in every subprocess.
    assert replay_inputs is not None
    relocated = tmp_path / "relocated"
    for name, data in replay_inputs.items():
        target = relocated / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    complete_public_outputs(relocated)
    assert snapshot(relocated) == snapshots[0]


def test_peer_refusal_is_propagated_before_any_output(saved, tmp_path, monkeypatch):
    """Stand-in verifies error propagation only; B's actual review decisions remain pending."""
    import sys
    import types

    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)

    def refuse(*a, **kw):
        raise ValueError("SYNTHETIC peer refusal control")

    monkeypatch.setitem(
        sys.modules,
        "rkuarch.provenance.companions",
        types.SimpleNamespace(assemble_stub_context=refuse),
    )
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2 and "SYNTHETIC peer refusal" in result.output
    assert not (tmp_path / "context.json").exists()
    assert not (tmp_path / "artifacts").exists()


def test_missing_explicit_review_refuses_before_peer(saved, tmp_path):
    c, directory = saved
    opts = assembly_inputs(c, directory, tmp_path)
    (tmp_path / "recipe-review.json").unlink()
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2 and "recipe-review.json" in result.output
    assert not (tmp_path / "context.json").exists()


def test_adapter_passes_supplied_comparisons_and_raw_closure_without_filtering(
    saved, tmp_path, monkeypatch
):
    """STAND-IN intake test only; includes a synthetic capacity failure, not a real attempt."""
    import sys
    import types

    from uarch_contract.hashing import canonical_json, content_hash

    from tests.integration.test_u2_b_r202_public import selected_package

    c, directory = saved
    verified, _, _, _ = selected_package.__wrapped__()
    opts = assembly_inputs(c, directory, tmp_path)
    opts.remove("--no-comparisons")
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for h, v in verified.artifacts.items():
        (artifacts / (h[7:] + ".json")).write_bytes(
            v if isinstance(v, bytes) else canonical_json(v).encode() + b"\n"
        )
    supplied = []
    for i, comp in enumerate(verified.comparisons):
        raw = comp.model_dump(mode="json")
        # Test-only rejected intake: transport must not discard capacity failures or refusals.
        raw["fixtures"][0]["execution"] = "execution_failed"
        raw["fixtures"][0]["outcome"] = "execution_failed"
        raw["limitations"].append("SYNTHETIC capacity failure transport control; not evidence")
        raw["comparison_hash"] = content_hash(raw, exclude=("comparison_hash",))
        path = tmp_path / f"comparison-{i}.json"
        path.write_text(canonical_json(raw))
        opts += ["--comparison", str(path)]
        supplied.append(raw)
    seen = []

    def refuse_after_inspection(
        actual, *, dependencies, registry, model_card, comparison_hashes, artifacts
    ):
        assert comparison_hashes == tuple(c["comparison_hash"] for c in supplied)
        for comp in supplied:
            assert artifacts[comp["comparison_hash"]] == comp
            assert comp["precision_refusal_observations"]
        for h, value in verified.artifacts.items():
            if isinstance(value, bytes):
                assert artifacts[h] == value
            else:
                # JSON canonicalization turns YAML numeric mapping keys into strings.
                assert canonical_json(artifacts[h]) == canonical_json(value)
        seen.append(True)
        raise ValueError("SYNTHETIC transport inspected; no assembly acceptance")

    monkeypatch.setitem(
        sys.modules,
        "rkuarch.provenance.companions",
        types.SimpleNamespace(assemble_stub_context=refuse_after_inspection),
    )
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2 and "transport inspected" in result.output, result.output
    assert seen == [True] and not (tmp_path / "context.json").exists()


def test_real_peer_preserves_complete_supplied_comparisons(tmp_path):
    """Bounded adopted input selection; no new engine/oracle execution or actual review."""
    from uarch_contract.hashing import canonical_json

    from rkuarch.table.build import CapturedWork, captured_artifacts
    from tests.integration.test_u2_b_r202_public import selected_package
    from tests.unit.test_u2_b_companions import arguments, canonical_comparisons

    require_real_peer()
    verified, _, _, _ = selected_package.__wrapped__()
    # Explicitly SYNTHETIC review of canonical indexes BEFORE the production boundary.
    canonical = canonical_comparisons(arguments(verified))
    c = CapturedWork(
        verified.bundle,
        verified.assumptions,
        verified.request,
        verified.derivation,
        verified.jobs,
        verified.results,
    )
    directory = tmp_path / "capture"
    directory.mkdir()
    for h, value in captured_artifacts(c).items():
        (directory / (h[7:] + ".json")).write_text(canonical_json(value) + "\n")
    opts = options(c, directory, tmp_path)
    values = {
        "recipes": canonical["dependencies"],
        "model-card": verified.model_card,
        "registry": verified.registry,
        "recipe-review": canonical["artifacts"][canonical["dependencies"].review_hash],
        "registry-review": verified.artifacts[verified.registry.review_hash],
    }
    for name, value in values.items():
        path = tmp_path / (name + ".json")
        path.write_text(canonical_json(value) + "\n")
        opts += ["--" + name, str(path)]
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for h, value in canonical["artifacts"].items():
        (artifacts / (h[7:] + ".json")).write_bytes(
            value if isinstance(value, bytes) else canonical_json(value).encode() + b"\n"
        )
    for i, comp in enumerate(verified.comparisons):
        path = tmp_path / f"comparison-{i}.json"
        path.write_text(canonical_json(comp) + "\n")
        opts += ["--comparison", str(path)]
    result = RUN.invoke(
        app,
        [
            "companions",
            "assemble",
            *opts,
            "--artifact-dir",
            str(artifacts),
            "--output",
            str(tmp_path / "context.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    context = json.loads((tmp_path / "context.json").read_text())
    assert context["comparison_hashes"] == sorted(c.comparison_hash for c in verified.comparisons)
    for h, value in verified.artifacts.items():
        expected = value if isinstance(value, bytes) else canonical_json(value).encode() + b"\n"
        assert (artifacts / (h[7:] + ".json")).read_bytes() == expected
    for comp in verified.comparisons:
        assert json.loads(
            (artifacts / (comp.comparison_hash[7:] + ".json")).read_text()
        ) == comp.model_dump(mode="json")


@pytest.mark.parametrize("attack", ["wrong-index", "omit"])
def test_real_cli_rejects_wrong_indexes_or_missing_attempts(tmp_path, attack):
    from tests.integration.test_u2_b_r202_public import selected_package
    from tests.u2_a_companion_inputs import write_assembly_inputs
    from tests.unit.test_u2_b_companions import arguments, canonical_comparisons

    require_real_peer()
    verified, _, _, _ = selected_package.__wrapped__()
    inputs = arguments(verified)
    assert inputs["comparison_hashes"] != tuple(sorted(inputs["comparison_hashes"]))
    if attack == "omit":
        canonical_comparisons(inputs)
        # Full store/declarations still contain the omitted attempt.
        inputs["comparison_hashes"] = inputs["comparison_hashes"][:-1]
    opts = write_assembly_inputs(inputs, tmp_path)
    before = {p.name: p.read_bytes() for p in (tmp_path / "artifacts").iterdir()}
    result = RUN.invoke(app, ["companions", "assemble", *opts])
    assert result.exit_code == 2, result.output
    assert (
        "bound comparison identity" if attack == "wrong-index" else "ComparisonIntakeMismatch"
    ) in result.output
    assert not (tmp_path / "context.json").exists()
    assert {p.name: p.read_bytes() for p in (tmp_path / "artifacts").iterdir()} == before


def test_real_cli_capacity_failure_prior_comparisons_and_refusals_survive(tmp_path):
    import copy

    from uarch_contract.hashing import canonical_json

    from rkuarch.table.artifacts import load_verified_report_inputs
    from tests.integration.test_u2_a_stage2_cli import cli
    from tests.u2_a_companion_inputs import actual_capacity_inputs, write_assembly_inputs

    require_real_peer()
    inputs, capacity_hash, refusal_hash = actual_capacity_inputs()
    assert len(inputs["comparison_hashes"]) == 3
    capacity = inputs["artifacts"][capacity_hash]
    failed = capacity["fixtures"][1]
    assert failed["execution"] == failed["outcome"] == "execution_failed"
    assert all(failed[key] is None for key in ("bundle_hash", "job_hash", "result_hash"))
    record = inputs["artifacts"][refusal_hash]
    assert "WeightCapacityExceeded" in record["error"]
    root = tmp_path / "complete"
    opts = write_assembly_inputs(inputs, root)
    result = cli("companions", "assemble", *opts)
    assert result.returncode == 0, result.stderr.decode()
    context = json.loads((root / "context.json").read_text())
    assert context["comparison_hashes"] == sorted(inputs["comparison_hashes"])
    for h, value in inputs["artifacts"].items():
        expected = value if isinstance(value, bytes) else canonical_json(value).encode() + b"\n"
        assert (root / "artifacts" / (h[7:] + ".json")).read_bytes() == expected
    out = root / "saved/table.json"
    result = cli(
        "table",
        "--prepared-input",
        root / "prepared-input.json",
        "--assumptions",
        root / "assumptions.json",
        "--capture-dir",
        root / "capture",
        "--context",
        root / "context.json",
        "--model-card",
        root / "model-card.json",
        "--artifact-dir",
        root / "artifacts",
        "--output",
        out,
    )
    assert result.returncode == 0, result.stderr.decode()
    replay = load_verified_report_inputs(out)
    assert replay.table.comparison_state == "attempted"
    assert tuple(c.comparison_hash for c in replay.comparisons) == tuple(
        context["comparison_hashes"]
    )
    for comparison in replay.comparisons:
        expected = inputs["artifacts"][comparison.comparison_hash]
        assert comparison.model_dump(mode="json") == expected
        assert comparison.precision_refusal_observations
        assert (
            out.parent / "artifacts" / (comparison.comparison_hash[7:] + ".json")
        ).read_bytes() == canonical_json(expected).encode() + b"\n"
    assert replay.artifacts[refusal_hash] == record
    assert record["model_id"] == "llama-3.1-70b" and record["tp"] == 1
    # Every original source and raw refusal input survives the saved package unchanged.
    for h, value in inputs["artifacts"].items():
        expected = value if isinstance(value, bytes) else canonical_json(value).encode() + b"\n"
        assert (out.parent / "artifacts" / (h[7:] + ".json")).read_bytes() == expected
    assert replay.model_card.validated_error_band is None
    assert replay.model_card.energy_verification is None
    omitted = copy.deepcopy(inputs)
    omitted["comparison_hashes"] = tuple(
        h for h in inputs["comparison_hashes"] if h != capacity_hash
    )
    rejected = tmp_path / "omitted-capacity"
    result = cli("companions", "assemble", *write_assembly_inputs(omitted, rejected))
    assert result.returncode == 2 and b"ComparisonIntakeMismatch" in result.stderr
    assert not (rejected / "context.json").exists()

    # The new complete-intake path must still refuse a missing original reference blob.
    # These are temporary test copies, never modifications to adopted reference files.
    import shutil

    from tests.integration.test_u2_b_r202_public import MANIFEST

    manifest = json.loads(inputs["artifacts"][MANIFEST])
    rows_name = manifest["files"]["parity/fixtures.json"] + ".json"
    broken = tmp_path / "missing-original"
    shutil.copytree(root / "artifacts", broken)
    (broken / rows_name).unlink()
    result = cli(
        "table",
        "--prepared-input",
        root / "prepared-input.json",
        "--assumptions",
        root / "assumptions.json",
        "--capture-dir",
        root / "capture",
        "--context",
        root / "context.json",
        "--model-card",
        root / "model-card.json",
        "--artifact-dir",
        broken,
        "--output",
        tmp_path / "refused/table.json",
    )
    assert result.returncode == 2
    assert b"original full rows blob required" in result.stderr
    assert not (tmp_path / "refused/table.json").exists()
