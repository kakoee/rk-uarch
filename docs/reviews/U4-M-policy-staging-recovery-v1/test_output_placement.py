"""Exercise output creation against the real guard; never prepare nominal inputs."""

import importlib.util
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
SPEC = json.loads((PACKAGE / "source.json").read_text())
spec = importlib.util.spec_from_file_location("staging_recovery", PACKAGE / "human-stage.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


@pytest.fixture
def layout(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    archive = tmp_path / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(
            ["git", "-C", SPEC["source_root"], "archive", SPEC["source_commit"]],
            stdout=stream,
            check=True,
        )
    with tarfile.open(archive) as stream:
        stream.extractall(source, filter="data")
    coordinator = tmp_path / "coordinator"
    coordinator.mkdir()
    subprocess.run(["git", "init", "-q", str(coordinator)], check=True)
    (coordinator / ".gitignore").write_text("tables/\n")
    monkeypatch.setattr(helper, "SOURCE", source)
    monkeypatch.setattr(helper, "COORDINATOR", coordinator)
    monkeypatch.setattr(
        helper, "OUTPUT", coordinator / "tables/U4-M-policy-input-freeze-recovery-v1"
    )
    return source


def inventory(source):
    code = (
        "import sys,json;from pathlib import Path;sys.path[:0]="
        + repr([str(source), str(source / "src"), str(source / "contract")])
        + ";from scripts import u2_support;"
        + "assert Path(u2_support.__file__).is_relative_to(Path("
        + repr(str(source))
        + "));"
        + "print(json.dumps(u2_support.inventory()))"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"}
    }
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        cwd=source,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_old_inside_source_layout_reproduces_guard_failure(layout):
    assert inventory(layout).returncode == 0
    (layout / "tables/U4-M-policy-input-freeze-v1").mkdir(parents=True)
    result = inventory(layout)
    assert result.returncode != 0
    assert "unreviewed import name: tables" in result.stderr


def test_corrected_creation_preserves_inventory(layout):
    before = inventory(layout)
    assert before.returncode == 0
    helper.create_output()
    after = inventory(layout)
    assert after.returncode == 0, after.stderr
    assert json.loads(before.stdout) == json.loads(after.stdout) == SPEC["inventory"]
    assert helper.OUTPUT.is_dir() and not list(helper.OUTPUT.iterdir())
    assert not (layout / "tables").exists()


def test_inside_source_output_refuses_before_creation(layout, monkeypatch):
    monkeypatch.setattr(helper, "OUTPUT", layout / "tables/U4-M-policy-input-freeze-recovery-v1")
    with pytest.raises(SystemExit):
        helper.create_output()
    assert not (layout / "tables").exists()


def test_existing_output_preserved(layout):
    helper.create_output()
    marker = helper.OUTPUT / "keep"
    marker.write_text("preserve failure evidence")
    with pytest.raises(SystemExit, match="already exists"):
        helper.create_output()
    assert marker.read_text() == "preserve failure evidence"
