"""Required companions in the unchanged saved A3 package are enforced by A's loader."""

import json
import shutil
from pathlib import Path

import pytest

from rkuarch.report.complete import write_report

ROOT = Path(__file__).resolve().parents[2]


def test_all_required_saved_companion_absences_refuse_before_outputs(tmp_path):
    source = ROOT / "tests/fixtures/u2_b/a3-proof-capture"
    copied = tmp_path / "inputs"
    shutil.copytree(source, copied)
    files = sorted((copied / "artifacts").iterdir())
    assert len(files) == 15
    # A's loader authenticates the embedded hardware in the prepared bundle and
    # populates that exact identity. Its redundant standalone copy is not required.
    table = json.loads((source / "table.json").read_text())
    # Request is likewise reconstructed from the authenticated captured intent.
    supplied_from_bundle = {table["hardware_spec_hash"], table["request_hash"]}
    files = [p for p in files if "sha256:" + p.stem not in supplied_from_bundle]
    assert len(files) == 13
    for companion in files:
        raw = companion.read_bytes()
        companion.unlink()
        try:
            with pytest.raises(ValueError, match="ArtifactMissing"):
                write_report(
                    copied / "table.json",
                    html_path=tmp_path / "x.html",
                    markdown_path=tmp_path / "x.md",
                )
            assert not (tmp_path / "x.html").exists()
            assert not (tmp_path / "x.md").exists()
        finally:
            companion.write_bytes(raw)
