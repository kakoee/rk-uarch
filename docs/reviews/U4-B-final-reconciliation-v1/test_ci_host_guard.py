"""Synthetic host guards only; never invoke Docker, Cargo or a native executable."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
spec = importlib.util.spec_from_file_location("u4_ci_host_guard", PACKAGE / "ci_host_guard.py")
assert spec and spec.loader
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def plan():
    # Synthetic parser inputs, explicitly not an actual K1 inventory or checked-in plan.
    return {
        "format": "uarch-k1-ci-tests/1",
        "checkpoint": "K1",
        "tool_package_commit": guard.TOOL_COMMIT,
        "target": guard.TARGET,
        "modes": ["debug", "release"],
        "all_features": True,
        "workspace_targets": [{"name": "synthetic", "kind": ["lib"]}],
        "test_names": ["synthetic::control"],
    }


def test_retained_tool_package_consistency():
    assert len(guard.validate_package(ROOT)) == 27


@pytest.mark.parametrize(
    "key,value",
    [
        ("test_names", []),
        ("workspace_targets", []),
        ("modes", ["debug"]),
        ("all_features", False),
        ("tool_package_commit", "unapproved"),
        ("target", "host"),
    ],
)
def test_missing_selection_mode_and_pin_refuse(key, value):
    data = plan()
    guard.validate_plan(data)
    data[key] = value
    with pytest.raises(ValueError):
        guard.validate_plan(data)


def test_image_identity_and_architecture():
    image = "private.example/native@sha256:" + "a" * 64
    data = [{"Os": "linux", "Architecture": "amd64", "RepoDigests": [image]}]
    guard.validate_image(data, image)
    for key, value in [("Os", "windows"), ("Architecture", "arm64"), ("RepoDigests", [])]:
        changed = copy.deepcopy(data)
        changed[0][key] = value
        with pytest.raises(ValueError, match="wrong image"):
            guard.validate_image(changed, image)


def test_container_metadata_uses_actual_mounted_workspace(tmp_path):
    native = tmp_path / "native"
    src = native / "crates/uarch-engine/src/lib.rs"
    src.parent.mkdir(parents=True)
    src.write_text("// synthetic source-presence control, never compiled\n")
    guards = tmp_path / "docs/reviews/U4-B-native-ci-v1"
    guards.mkdir(parents=True)
    (guards / "ci_guard.py").write_bytes(
        (ROOT / "docs/reviews/U4-B-native-ci-v1/ci_guard.py").read_bytes()
    )
    metadata = {
        "workspace_root": str(native),
        "workspace_members": ["engine"],
        "packages": [
            {
                "id": "engine",
                "name": "uarch-engine",
                "source": None,
                "manifest_path": str(native / "crates/uarch-engine/Cargo.toml"),
                "targets": [
                    {"name": "synthetic", "kind": ["lib"], "test": True, "src_path": str(src)}
                ],
            }
        ],
        "resolve": {"nodes": []},
    }
    guard.validate_metadata(tmp_path, metadata, plan(), [])
    wrong = copy.deepcopy(metadata)
    wrong["workspace_root"] = "/different/native"
    with pytest.raises(ValueError, match="wrong workspace root"):
        guard.validate_metadata(tmp_path, wrong, plan(), [])
    wrong = copy.deepcopy(metadata)
    wrong["packages"][0]["manifest_path"] = "/different/Cargo.toml"
    with pytest.raises(ValueError, match="wrong manifest"):
        guard.validate_metadata(tmp_path, wrong, plan(), [])
    src.unlink()
    with pytest.raises(ValueError, match="missing local source"):
        guard.validate_metadata(tmp_path, metadata, plan(), [])


def test_zero_status_is_not_enough_for_results(tmp_path):
    # Missing logs and even all-zero process statuses cannot manufacture test evidence.
    with pytest.raises(FileNotFoundError):
        guard.validate_results(ROOT, tmp_path, plan())


def test_workflow_guards_outside_container():
    import yaml

    data = yaml.safe_load((PACKAGE / "native-job.yml.in").read_text())["native"]
    assert "container" not in data
    assert data["needs"] == "scope"
    assert data["if"] == "needs.scope.outputs.docs_only != 'true'"
    assert data["steps"][-1]["if"] == "always()"
    assert "__POST_ACCEPTANCE_FINAL_BUILDER_" in json.dumps(data)
    host = (PACKAGE / "native-host.sh").read_text()
    assert host.index("run_container inspect\n") < host.index('ci_host_guard.py" metadata')
    assert host.index('ci_host_guard.py" metadata') < host.index("run_container checks\n")
    assert "--network none" in host and "dst=$root,readonly" in host


def test_log_writer_propagates_exact_failure(tmp_path):
    import re
    import subprocess

    shell = (PACKAGE / "native-container.sh").read_text()
    function = re.search(r"run_log\(\) \{.*?\n\}", shell, re.DOTALL)
    assert function
    script = "set -euo pipefail\nreceipts=$1\n" + function.group(0)
    script += '\nrun_log deliberate bash -c "echo diagnostic >&2; exit 7"\nexit 99\n'
    result = subprocess.run(["bash", "-c", script, "guard-control", str(tmp_path)], check=False)
    assert result.returncode == 7
    assert (tmp_path / "deliberate.exit").read_text() == "7\n"
    assert (tmp_path / "deliberate.stderr").read_text() == "diagnostic\n"


def test_results_require_both_modes_exact_tools_and_nonempty_passes(tmp_path):
    receipts = tmp_path
    commands = [
        "inspect-container",
        "checks-container",
        "inspect-inputs",
        "checks-inputs",
        "rustc",
        "cargo",
        "rustfmt",
        "clippy",
        "cargo-deny",
        "targets",
        "metadata",
        "fmt",
        "clippy-tests",
        "licences",
        "debug-list",
        "debug-tests",
        "release-list",
        "release-tests",
    ]
    for command in commands:
        (receipts / (command + ".exit")).write_text("0\n")
    for tool in ("rustc", "cargo", "rustfmt", "clippy", "cargo-deny"):
        (receipts / (tool + ".log")).write_bytes(
            (ROOT / guard.A_PACKAGE / "version-receipts" / (tool + ".txt")).read_bytes()
        )
    for mode in ("debug", "release"):
        (receipts / (mode + "-list.log")).write_text("synthetic::control: test\n")
        (receipts / (mode + "-tests.log")).write_text(
            "test synthetic::control ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored;\n"
        )
    guard.validate_results(ROOT, receipts, plan())
    target = receipts / "release-tests.exit"
    target.write_text("7\n")
    with pytest.raises(ValueError, match="failed command"):
        guard.validate_results(ROOT, receipts, plan())
    target.write_text("0\n")
    (receipts / "release-tests.log").write_text("test result: ok. 0 passed; 0 failed; 0 ignored;\n")
    with pytest.raises(ValueError, match="missing, ignored, failing"):
        guard.validate_results(ROOT, receipts, plan())
    (receipts / "rustc.log").write_text("host rustc, wrong installation\n")
    with pytest.raises(ValueError, match="wrong container tool"):
        guard.validate_results(ROOT, receipts, plan())
