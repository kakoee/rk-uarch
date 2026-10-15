"""Installer preflight controls; never enable or execute its human installation branch."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("u4_install", PACKAGE / "human-install.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
SELECTION = json.loads((PACKAGE / "selection.json").read_text())


def test_exact_combined_preview_does_not_change_live_sources(tmp_path):
    before = {
        row["path"]: (
            (helper.ROOT / row["path"]).read_bytes()
            if (helper.ROOT / row["path"]).exists()
            else None
        )
        for row in SELECTION["files"]
    }
    helper.preview(helper.ROOT, tmp_path, SELECTION["files"], helper.PINS)
    helper.check_files(tmp_path, SELECTION["files"], "after")
    after = {
        row["path"]: (
            (helper.ROOT / row["path"]).read_bytes()
            if (helper.ROOT / row["path"]).exists()
            else None
        )
        for row in SELECTION["files"]
    }
    assert before == after
    assert len(SELECTION["files"]) == 32


@pytest.mark.parametrize("fault", ["existing-new", "missing", "changed", "symlink", "escape"])
def test_preimage_and_path_refusals(tmp_path, fault):
    source = tmp_path / "source"
    source.write_bytes(b"original")
    row = {"path": "source", "before_sha256": helper.sha(b"original")}
    if fault == "existing-new":
        row["before_sha256"] = None
    elif fault == "missing":
        source.unlink()
    elif fault == "changed":
        source.write_bytes(b"changed")
    elif fault == "symlink":
        real = tmp_path / "real"
        source.rename(real)
        source.symlink_to(real)
    else:
        row["path"] = "../outside"
    with pytest.raises(ValueError):
        helper.check_files(tmp_path, [row], "before")


def test_postimage_drift_refuses(tmp_path):
    (tmp_path / "source").write_bytes(b"wrong")
    with pytest.raises(ValueError, match="after image drift"):
        helper.check_files(
            tmp_path, [{"path": "source", "after_sha256": helper.sha(b"accepted")}], "after"
        )


def test_future_authorization_is_exact_not_a_semantic_approval():
    # Synthetic parser control only: never written as an approval or used for installation.
    record = {
        "format": "uarch-M-policy-install-authorization/1",
        "action": "install-source-only",
        "approved": True,
        "authorizer": "Javid",
        "package_commit": "a" * 40,
        "selection_sha256": "b" * 64,
        "source_parent": "c" * 40,
    }
    helper.authorization(record, "a" * 40, "b" * 64, "c" * 40)
    for key, value in [
        ("action", "generate-and-adopt"),
        ("approved", False),
        ("selection_sha256", "d" * 64),
        ("source_parent", "e" * 40),
        ("package_commit", "f" * 40),
        ("extra", "broader scope"),
    ]:
        changed = copy.deepcopy(record)
        changed[key] = value
        with pytest.raises(ValueError, match="authorization"):
            helper.authorization(changed, "a" * 40, "b" * 64, "c" * 40)


def test_agent_invocation_cannot_install():
    env = {k: v for k, v in os.environ.items() if k != "UARCH_HUMAN"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(PACKAGE / "human-install.py"),
            "--package-commit",
            helper.BASE,
            "--expected-head",
            helper.BASE,
            "--python",
            sys.executable,
            "--install",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "separately authorized human invocation" in result.stderr
