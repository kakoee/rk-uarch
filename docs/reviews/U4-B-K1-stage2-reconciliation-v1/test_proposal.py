"""Pre-install refusal controls; no container or native command is invoked."""

import json
import runpy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HELPER = runpy.run_path(str(HERE / "post_install.py"))
SUBJECT = json.loads((HERE / "subject.json").read_text())


@pytest.mark.parametrize("value", [None, "", "base-plus-patch"])
def test_no_invented_installed_commit(value):
    with pytest.raises(ValueError, match="actual full installed commit"):
        HELPER["committed_source"](ROOT, value, SUBJECT)


def test_reviewed_base_is_not_installed_stage2():
    with pytest.raises(ValueError, match="installed K1 footprint requires new review"):
        HELPER["committed_source"](ROOT, SUBJECT["base_commit"], SUBJECT)
