"""Exercise CI selection with real Git histories and the Actions entry point."""

import json
import os
import runpy
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/ci_scope.py"
SCOPE = runpy.run_path(str(SCRIPT))["documentation_only"]


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root, path, text="content\n"):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    git(root, "add", "--", path)
    git(root, "commit", "-qm", "test change")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "config", "core.hooksPath", "/dev/null")
    commit(tmp_path, "README.md")
    return tmp_path


@pytest.mark.parametrize("path", ["docs/how-it-works.md", "docs/prompts/task.md",
                                  "docs/decisions/example.md", "rk-sim-side/prompts/task.md"])
def test_markdown_push_and_pr_merge_use_short_path(repo, path):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "topic")
    commit(repo, path)
    git(repo, "checkout", "-q", "main")
    commit(repo, "base.py")
    current_base = git(repo, "rev-parse", "HEAD")
    git(repo, "merge", "--no-ff", "-qm", "merge topic", "topic")
    assert SCOPE(repo, "pull_request", {"pull_request": {"base": {"sha": current_base}}})
    assert SCOPE(repo, "push", {"before": current_base})
    assert not SCOPE(repo, "push", {"before": base})  # Whole push includes base.py.


@pytest.mark.parametrize("path", ["src/rkuarch/new.py", "tests/unit/new.py", "uv.lock",
                                  "pyproject.toml", ".github/workflows/ci.yml",
                                  "docs/reviews/example.json", "docs/reviews/probe.py",
                                  "docs/reviews/run.sh", "contract/schema/new.md"])
def test_non_markdown_or_unknown_paths_keep_full_suite(repo, path):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, path)
    commit(repo, "docs/last-commit.md")
    assert not SCOPE(repo, "push", {"before": base})


def test_source_renamed_to_markdown_still_runs_full(repo):
    base = commit(repo, "source.py")
    (repo / "docs").mkdir()
    git(repo, "mv", "source.py", "docs/source.md")
    git(repo, "commit", "-qm", "rename")
    assert not SCOPE(repo, "push", {"before": base})


def test_document_deletion_and_space_in_filename(repo):
    base = commit(repo, "docs/a document.md")
    git(repo, "rm", "docs/a document.md")
    git(repo, "commit", "-qm", "delete")
    assert SCOPE(repo, "push", {"before": base})


@pytest.mark.parametrize("mode", ["symlink", "executable"])
def test_non_regular_markdown_is_full(repo, mode):
    base = git(repo, "rev-parse", "HEAD")
    p = repo / "docs/example.md"
    p.parent.mkdir()
    if mode == "symlink":
        p.symlink_to("../README.md")
    else:
        p.write_text("#!/bin/sh\n")
        p.chmod(0o755)
    git(repo, "add", "docs/example.md")
    git(repo, "commit", "-qm", "special mode")
    assert not SCOPE(repo, "push", {"before": base})


@pytest.mark.parametrize("base", [None, "0" * 40, "1" * 40, "--help", "HEAD~1"])
def test_missing_or_invalid_history_runs_full(repo, base):
    commit(repo, "docs/example.md")
    assert not SCOPE(repo, "push", {"before": base})


def test_empty_diff_and_nonancestor_and_unknown_event_run_full(repo):
    base = git(repo, "rev-parse", "HEAD")
    assert not SCOPE(repo, "push", {"before": base})
    sibling = commit(repo, "docs/sibling.md")
    git(repo, "checkout", "-q", "--detach", base)
    commit(repo, "docs/current.md")
    assert not SCOPE(repo, "push", {"before": sibling})
    assert not SCOPE(repo, "workflow_dispatch", {"before": base})


@pytest.mark.parametrize("valid", [True, False])
def test_actions_output_entry_point(repo, valid):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, "docs/example.md")
    payload = repo / "event.json"
    payload.write_text(json.dumps({"before": base}) if valid else "not json")
    output = repo / "output.txt"
    env = {**os.environ, "GITHUB_EVENT_PATH": str(payload), "GITHUB_EVENT_NAME": "push",
           "GITHUB_OUTPUT": str(output)}
    subprocess.run([sys.executable, str(SCRIPT)], cwd=repo, env=env, check=True)
    assert output.read_text() == f"docs_only={str(valid).lower()}\n"


def test_workflow_runs_full_suite_unless_explicit_docs_result():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    jobs = workflow["jobs"]
    assert jobs["scope"]["steps"][0]["with"]["fetch-depth"] == 0
    assert jobs["scope"]["outputs"]["docs_only"] == "${{ steps.classify.outputs.docs_only }}"
    python = jobs["python"]
    assert python["needs"] == "scope"
    full = next(s for s in python["steps"] if s.get("name", "").startswith("tests ("))
    assert full["if"] == "needs.scope.outputs.docs_only != 'true'"
    assert 'not nightly and not silicon and not native and not golden and not determinism' in full[
        "run"
    ]
    short = next(s for s in python["steps"] if s.get("name") == "documentation checks")
    assert short["if"] == "needs.scope.outputs.docs_only == 'true'"
    assert "tests/unit/test_prompt_sync.py" in short["run"]
    assert "tests/unit/test_ci_scope.py" in short["run"]
    for name in ("golden", "determinism", "perf", "ordering"):
        assert jobs[name]["needs"] == "scope"
        assert jobs[name]["if"] == "needs.scope.outputs.docs_only != 'true'"
    # Explicit user deferral: native must not execute on either docs or code pushes.
    assert jobs["native"]["needs"] == "scope"
    assert jobs["native"]["if"] == "${{ false }}"
    for name in ("contract", "licences-and-patches"):
        assert "if" not in jobs[name]


def test_contract_ownership_strict_flags_and_currentness_are_retained():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    full = next(s for s in jobs["python"]["steps"] if s.get("name", "").startswith("tests ("))
    assert "tests validation" in full["run"]
    contract = jobs["contract"]
    assert "if" not in contract
    commands = [s["run"] for s in contract["steps"] if "run" in s]
    suite = next(s for s in commands if "--require-vendor" in s)
    assert "contract/tests --require-vendor" in suite
    assert "--pre-contract" not in suite and "--ignore" not in suite
    assert "-m" not in suite.split("pytest", 1)[1].split()
    assert any("scripts/vendor_rk.py --check" in s for s in commands)
    assert any("uarch_contract.generate --check" in s for s in commands)
    for name in ("python", "contract"):
        steps = jobs[name]["steps"]
        sync = next(s["run"] for s in steps if s.get("run", "").startswith("uv sync"))
        assert sync == "uv sync --locked --extra dev"
        setup = next(s for s in steps if s.get("uses", "").startswith("astral-sh/setup-uv@"))
        assert setup["with"]["enable-cache"] is True
        assert set(setup["with"]["cache-dependency-glob"].split()) == {"uv.lock", "pyproject.toml"}
        summary = next(s for s in steps if "phase summary" in s.get("name", ""))
        assert summary["if"] == "always()"


def test_actual_ci_collection_partitions_default_selection(tmp_path):
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]

    def arguments(job, token):
        command = next(s["run"] for s in jobs[job]["steps"] if token in s.get("run", ""))
        argv = shlex.split(command.replace("${{ runner.temp }}", str(tmp_path)))
        assert argv[:5] == ["uv", "run", "python", "-m", "pytest"]
        # Use exactly the workflow selection, with its real strict flags/plugin.
        return argv[5:]

    def collect(args):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", *args],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        nodes = {line for line in result.stdout.splitlines()
                 if "::" in line and line.startswith(("tests/", "contract/tests/", "validation/"))}
        assert nodes
        return nodes

    python_args = arguments("python", "--timing-jsonl")
    contract_args = arguments("contract", "--require-vendor")
    python_nodes = collect(python_args)
    contract_nodes = collect(contract_args)
    marker = python_args[python_args.index("-m") + 1]
    default_nodes = collect(["-q", "-m", marker])
    assert python_nodes.isdisjoint(contract_nodes)
    assert python_nodes | contract_nodes == default_nodes


def test_ordering_runs_even_when_predictions_are_missing():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    steps = jobs["ordering"]["steps"]
    assert steps[0]["with"]["fetch-depth"] == 0
    assert steps[1]["run"] == "python3 validation/L3_silicon/check_ordering.py"
