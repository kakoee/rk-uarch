"""Real K1 failure controls, runnable only after a successful exact-image verification."""

import argparse
import hashlib
import importlib.util
import json
import re
import runpy
from contextlib import contextmanager
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "k1_construct", Path(__file__).with_name("construct.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
c = module


def source_snapshot(root):
    return {
        str(p.relative_to(root)): (c.digest(p), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


@contextmanager
def mutation(root, relative, before=None, after=None, expected_sha=None, remove=False):
    """Only a disposable native Rust file; always restore bytes AND timestamps."""
    import os

    path = root / relative
    c.require(
        path.resolve().is_relative_to((root / "native").resolve()) and path.suffix == ".rs",
        "mutation must stay in exported native Rust source",
    )
    data, stat = path.read_bytes(), path.stat()
    if expected_sha is not None:
        c.require(
            hashlib.sha256(data).hexdigest() == expected_sha, "mutation source identity mismatch"
        )
    try:
        if remove:
            path.unlink()
        else:
            c.require(before and data.count(before.encode()) == 1, "mutation anchor must be unique")
            path.write_bytes(data.replace(before.encode(), after.encode(), 1))
        yield
    finally:
        path.write_bytes(data)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def failure(work, name, argv, diagnostic, extra=()):
    receipts = work / "receipts"
    status = c.run(receipts, name, c.container(work, argv, extra), fail=False)
    c.require(status != 0, name + ": required native failure did not occur")
    text = (receipts / (name + ".stdout")).read_text() + (receipts / (name + ".stderr")).read_text()
    c.require(re.search(diagnostic, text, re.IGNORECASE), name + ": failed for an unrelated reason")


def rejected_selection(work, name, tail, plan):
    receipts = work / "receipts"
    c.run(
        receipts,
        name,
        c.container(work, c.cargo("debug", *tail), ["--env", "CARGO_TARGET_DIR=/target/restored"]),
    )
    old = runpy.run_path(str(work / "source" / c.OLD / "ci_guard.py"))
    try:
        old["check_tests"](
            (receipts / "debug-list.stdout").read_text(),
            (receipts / (name + ".stdout")).read_text(),
            plan["test_names"],
        )
    except ValueError as exc:
        c.write_json(receipts / (name + "-guard.json"), {"refused": True, "reason": str(exc)})
    else:
        raise ValueError(name + ": incomplete native selection was accepted")


def execute(work, mutations):
    source, receipts = work / "source", work / "receipts"
    # No fake/synthetic receipt setup in real mode. Require successful predecessor outputs.
    verified = json.loads((receipts / "verified.json").read_text())
    c.require(verified["image_id"] == (work / "image.id").read_text().strip(), "different image")
    c.require(verified["cache_crates"] == 27, "unverified cache")
    c.installed(source)
    plan = json.loads((receipts / "test-plan.candidate.json").read_text())
    metadata = json.loads((receipts / "metadata.log").read_text())
    member = next(p for p in metadata["packages"] if p["id"] in metadata["workspace_members"])
    target = next(t for t in member["targets"] if t["test"] and "lib" in t["kind"])
    relative = str(Path(target["src_path"]).relative_to(source))
    c.require(
        source.resolve().is_relative_to(work.resolve()) and not (source / ".git").exists(),
        "faults require a disposable source export",
    )
    initial = source_snapshot(source)
    completed = []
    try:
        with mutation(source, relative, remove=True):
            failure(
                work,
                "fault-source",
                c.cargo("debug", "--list"),
                r"no targets specified|couldn.t read|could not read|no such file|can.t find",
            )
        completed.append("missing source")
        path = source / relative
        original = path.read_text()
        # Full original file is a unique exact anchor; only this scratch export changes.
        with mutation(
            source,
            relative,
            before=original,
            after=original + '\ncompile_error!("U4_B_COMPILE_FAULT");\n',
        ):
            failure(work, "fault-compile", c.cargo("debug", "--list"), "U4_B_COMPILE_FAULT")
        completed.append("real compiler failure")
        fault_name = "u4_b_injected_runtime_fault"
        c.require(fault_name not in original, "runtime fault name collision")
        with mutation(
            source,
            relative,
            before=original,
            after=original
            + "\n#[test]\nfn "
            + fault_name
            + '() { panic!("U4_B_RUNTIME_FAULT"); }\n',
        ):
            failure(
                work,
                "fault-runtime",
                c.cargo("debug", fault_name, "--exact", "--show-output"),
                "U4_B_RUNTIME_FAULT",
            )
        completed.append("real failing Rust test")
        # Fresh target directory after byte restoration avoids any mutated build reuse.
        extra = ["--env", "CARGO_TARGET_DIR=/target/restored"]
        for mode in ("debug", "release"):
            name = "restored-" + mode
            c.run(receipts, name, c.container(work, c.cargo(mode, "--show-output"), extra))
            old = runpy.run_path(str(source / c.OLD / "ci_guard.py"))
            old["check_tests"](
                (receipts / (mode + "-list.stdout")).read_text(),
                (receipts / (name + ".stdout")).read_text(),
                plan["test_names"],
            )
        completed.append("restored full debug/release positives")
        absent = "__u4_b_intentionally_absent_test__"
        c.require(absent not in plan["test_names"], "empty-selection fault name collision")
        rejected_selection(work, "fault-empty", [absent, "--exact", "--show-output"], plan)
        rejected_selection(work, "fault-ignored", ["--ignored", "--show-output"], plan)
        rejected_selection(
            work, "fault-filtered", ["--skip", plan["test_names"][0], "--show-output"], plan
        )
        completed.append("real empty/ignored/filtered selection refusals")
        failure(
            work,
            "fault-cache",
            ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
            r"offline|no matching package",
            ["--tmpfs", "/usr/local/cargo/registry"],
        )
        completed.append("offline cache absent")
        failure(
            work,
            "fault-toolchain",
            [
                "env",
                "RUSTUP_TOOLCHAIN=u4-b-intentionally-absent",
                "RUSTUP_AUTO_INSTALL=0",
                "rustc",
                "-vV",
            ],
            r"not installed|invalid toolchain",
        )
        completed.append("unavailable toolchain cannot auto-install")
        failure(
            work,
            "fault-license",
            [
                "cargo",
                "deny",
                "--locked",
                "--offline",
                "--all-features",
                "--config",
                str(source / c.A / "deny-current.toml"),
                "check",
                "licenses",
                "bans",
                "sources",
            ],
            "Unicode-3.0",
        )
        completed.append("current policy Unicode refusal")
        for index, fault in enumerate(mutations):
            c.require(
                plan["test_names"].count(fault["test"]) == 1, "mutation must name one actual test"
            )
            for mode in ("debug", "release"):
                name = f"semantic-{index}-{mode}"
                with mutation(
                    source,
                    fault["path"],
                    fault["before"],
                    fault["after"],
                    fault.get("original_sha256", fault.get("sha256")),
                ):
                    failure(
                        work,
                        name,
                        c.cargo(mode, fault["test"], "--exact", "--show-output"),
                        fault["diagnostic"],
                    )
                name += "-restored"
                c.run(
                    receipts,
                    name,
                    c.container(
                        work,
                        c.cargo(mode, fault["test"], "--exact", "--show-output"),
                        ["--env", f"CARGO_TARGET_DIR=/target/{name}"],
                    ),
                )
                old["check_tests"](
                    fault["test"] + ": test\n",
                    (receipts / (name + ".stdout")).read_text(),
                    [fault["test"]],
                )
                completed.append(name)
        replay_controls = runpy.run_path(str(Path(__file__).with_name("replay_control.py")))

        def invoke(name, argv, extra):
            flags = [part for value in extra for part in ("--env", value)]
            return c.run(receipts, name, c.container(work, argv, flags))

        replay_controls["execute"](
            work, invoke, lambda name: f"/receipts/{name}.canonical", "/target/replay-restored"
        )
        completed.append("release-only canonical drift refused and restored")
    finally:
        unchanged = initial == source_snapshot(source)
        c.write_json(
            receipts / "fault-controls.json",
            {
                "completed": completed,
                "source_bytes_and_mtimes_restored": unchanged,
                "semantic_mutations": len(mutations),
                "native_qualification": False,
            },
        )
        c.require(unchanged, "source restoration failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--mutations", type=Path)
    args = parser.parse_args()
    faults = json.loads(args.mutations.read_text()) if args.mutations else []
    execute(args.work.resolve(), faults["faults"] if isinstance(faults, dict) else faults)
