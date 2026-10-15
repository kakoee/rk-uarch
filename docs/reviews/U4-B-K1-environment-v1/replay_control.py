"""Deliberate release-only byte drift through A's actual private replay sink."""

import importlib.util
import json
import runpy
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay_controls", PACKAGE / "controls.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.c


def execute(work, invoke, output_path, target_directory):
    source, receipts = work / "source", work / "receipts"
    fault = json.loads((PACKAGE / "replay-mutation.json").read_text())
    before = c.snapshot(source)
    old = runpy.run_path(str(source / c.OLD / "ci_guard.py"))
    original = {
        f"{mode}-{n}": (receipts / f"replay-{mode}-{n}.canonical").read_bytes()
        for mode in ("debug", "release")
        for n in range(3)
    }
    c.compare_replays(original)
    name = "fault-release-replay"
    with m.mutation(source, fault["path"], fault["before"], fault["after"], fault["sha256"]):
        invoke(
            name,
            c.cargo("release", fault["test"], "--exact", "--show-output"),
            ["UARCH_K1_REPLAY_OUT=" + output_path(name)],
        )
        old["check_tests"](
            fault["test"] + ": test\n", (receipts / (name + ".stdout")).read_text(), [fault["test"]]
        )
        altered = dict(original)
        altered["release-2"] = (receipts / (name + ".canonical")).read_bytes()
        try:
            c.compare_replays(altered)
        except ValueError as exc:
            c.write_json(
                receipts / "fault-release-replay-guard.json", {"refused": True, "reason": str(exc)}
            )
        else:
            raise ValueError("release-only native replay mutation was not caught")
    name = "restored-release-replay"
    invoke(
        name,
        c.cargo("release", fault["test"], "--exact", "--show-output"),
        [
            "UARCH_K1_REPLAY_OUT=" + output_path(name),
            "CARGO_TARGET_DIR=" + target_directory,
        ],
    )
    old["check_tests"](
        fault["test"] + ": test\n", (receipts / (name + ".stdout")).read_text(), [fault["test"]]
    )
    restored = (receipts / (name + ".canonical")).read_bytes()
    c.require(restored == original["release-2"], "restored canonical output differs")
    c.require(before == c.snapshot(source), "replay control source not restored")
