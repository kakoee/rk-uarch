"""Invoke B's unchanged installed-source helper with the exact KI-C1 hash exception."""

import copy
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent / "U4-B-K1-stage2-reconciliation-v1"
PATH = "tests/unit/test_third_party_patch_check.py"
OLD = "85c5590b7eccd3265b893e33458f1d94250dba4f81fa8af4d6bb6a90ec3737cb"
NEW = "26a882fdb9c0930864e47c88dae36c571085c614c64dd425a1cdbcb66f4c8762"


def main():
    original = json.loads((B / "subject.json").read_text())
    revised = json.loads((HERE / "subject.json").read_text())
    assert original["postimages"][PATH] == OLD
    assert revised["postimages"][PATH] == NEW
    comparable = copy.deepcopy(revised)
    exception = comparable.pop("approved_exception")
    assert exception["decision"] == "U4-K1-KI-C1-formatting-v1"
    assert exception["path"] == PATH and exception["previous_sha256"] == OLD
    comparable["postimages"][PATH] = OLD
    comparable["kind"] = original["kind"]
    assert comparable == original, "only the approved one-file hash may differ"
    assert (HERE / "inventory.proposed.json").read_bytes() == (
        B / "inventory.proposed.json"
    ).read_bytes()
    helper = runpy.run_path(str(B / "post_install.py"))
    run = helper["main"]
    run.__globals__["HERE"] = HERE
    run()


if __name__ == "__main__":
    main()
