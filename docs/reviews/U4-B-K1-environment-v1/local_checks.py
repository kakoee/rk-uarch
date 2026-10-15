"""Separate existing-host checks. These NEVER claim a built container or qualifying CI."""

import importlib.util
import json
import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("k1_controls", PACKAGE / "controls.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.c


def execute(root, revision, work):
    work.mkdir()
    receipts = work / "receipts"
    receipts.mkdir()
    c.export(root, revision, work / "source")
    source = work / "source"
    closure = c.installed(source)
    cargo_home = work / "cargo"
    cargo_home.mkdir()
    before = c.snapshot(source)
    prefix = [
        "env",
        "RUSTUP_TOOLCHAIN=stable",
        "RUSTUP_AUTO_INSTALL=0",
        "CARGO_HOME=" + str(cargo_home),
        "CARGO_TARGET_DIR=" + str(work / "target"),
        "CARGO_NET_OFFLINE=true",
    ]

    def run(name, argv, extra=(), fail=True):
        return c.run(receipts, name, [*prefix, *extra, *argv], cwd=source / "native", fail=fail)

    def fail(name, argv, pattern, extra=()):
        import re

        code = run(name, argv, extra, fail=False)
        text = (receipts / (name + ".stdout")).read_text() + (
            receipts / (name + ".stderr")
        ).read_text()
        c.require(
            code != 0 and re.search(pattern, text, re.IGNORECASE), "wrong expected failure: " + name
        )

    complete = []
    try:
        for name, argv in [
            ("rustc", ["rustc", "-vV"]),
            ("cargo", ["cargo", "-V"]),
            ("rustfmt", ["cargo", "fmt", "--version"]),
            ("clippy", ["cargo", "clippy", "--version"]),
        ]:
            run("version-" + name, argv)
            c.require(
                (receipts / ("version-" + name + ".stdout")).read_bytes()
                == (source / c.A / "version-receipts" / (name + ".txt")).read_bytes(),
                "wrong local tool " + name,
            )
        paths = {}
        for name in ("rustc", "cargo", "rustfmt", "clippy-driver"):
            path = Path(
                subprocess.check_output(
                    ["rustup", "which", "--toolchain", "stable", name], text=True
                ).strip()
            )
            paths[name] = {"path": str(path), "sha256": c.digest(path)}
        c.write_json(
            receipts / "environment.json",
            {
                "kind": "existing-host-only",
                "subject": revision,
                "toolchain_alias": "stable; full receipts compared with accepted versions",
                "tools": paths,
                "uname": list(os.uname()),
                "image_id": None,
                "qualifying_ci": False,
            },
        )
        run("fetch", ["cargo", "fetch", "--locked"], ["CARGO_NET_OFFLINE=false"])
        archives = "".join(
            c.digest(p) + "  " + str(p) + "\n"
            for p in sorted((cargo_home / "registry/cache").rglob("*.crate"))
        )
        notices = ""
        for entry in closure:
            for notice in entry["notice_files"]:
                matches = list(
                    (cargo_home / "registry/src").glob(
                        "*/" + entry["name"] + "-" + entry["version"] + "/" + notice["path"]
                    )
                )
                c.require(len(matches) == 1, "missing notice")
                notices += c.digest(matches[0]) + "  " + str(matches[0]) + "\n"
        (receipts / "cache-archives.stdout").write_text(archives)
        (receipts / "cache-notices.stdout").write_text(notices)
        c.verify_cache(closure, archives, notices)
        complete.append("27 checksum-bound cache archives and retained notices")
        tool = json.loads((source / c.A / "cargo-deny.json").read_text())
        archive = work / "cargo-deny.tar.gz"
        with urllib.request.urlopen(tool["url"]) as response:
            archive.write_bytes(response.read())
        c.require(c.digest(archive) == tool["sha256"], "cargo-deny archive checksum")
        with tarfile.open(archive) as tar:
            members = [x for x in tar if x.isfile() and Path(x.name).name == "cargo-deny"]
            c.require(len(members) == 1, "ambiguous deny binary")
            binary = work / "cargo-deny"
            with tar.extractfile(members[0]) as stream:
                binary.write_bytes(stream.read())
            binary.chmod(0o700)
        run("version-cargo-deny", [str(binary), "--version"])
        c.require(
            (receipts / "version-cargo-deny.stdout").read_bytes()
            == (source / c.A / "version-receipts/cargo-deny.txt").read_bytes(),
            "deny version mismatch",
        )
        c.write_json(
            receipts / "deny-tool.json",
            {
                "url": tool["url"],
                "archive_sha256": c.digest(archive),
                "binary_sha256": c.digest(binary),
                "installation": "disposable directory only",
            },
        )
        run(
            "metadata",
            [
                "cargo",
                "metadata",
                "--locked",
                "--offline",
                "--all-features",
                "--format-version",
                "1",
                "--filter-platform",
                c.TARGET,
            ],
        )
        outputs = {}
        for mode in ("debug", "release"):
            run(mode + "-list", c.cargo(mode, "--list"))
            outputs[mode] = (receipts / (mode + "-list.stdout")).read_text()
        run(
            "metadata-full",
            [
                "cargo",
                "metadata",
                "--locked",
                "--offline",
                "--all-features",
                "--format-version",
                "1",
            ],
        )
        plan = c.discovery(
            source,
            json.loads((receipts / "metadata-full.stdout").read_text()),
            outputs,
            json.loads((receipts / "metadata.stdout").read_text()),
        )
        replay = "tests::canonical_replay_private_bytes"
        c.require(plan["test_names"].count(replay) == 1, "actual replay test missing")
        plan.update(
            source_commit=revision,
            evidence_environment="existing-host-only",
            replay_test=replay,
            replay_output_env="UARCH_K1_REPLAY_OUT",
        )
        c.write_json(receipts / "test-plan.local.json", plan)
        old = __import__("runpy").run_path(str(source / c.OLD / "ci_guard.py"))
        for name, argv in [
            ("fmt", ["cargo", "fmt", "--all", "--", "--check"]),
            (
                "clippy",
                [
                    "cargo",
                    "clippy",
                    "--locked",
                    "--offline",
                    "--workspace",
                    "--all-targets",
                    "--all-features",
                    "--target",
                    c.TARGET,
                    "--",
                    "-D",
                    "warnings",
                ],
            ),
            (
                "deny",
                [
                    str(binary),
                    "--locked",
                    "--offline",
                    "--all-features",
                    "--config",
                    "deny.toml",
                    "check",
                    "licenses",
                    "bans",
                    "sources",
                ],
            ),
        ]:
            run(name, argv)
        results = {}
        for mode in ("debug", "release"):
            run(mode + "-tests", c.cargo(mode, "--show-output"))
            old["check_tests"](
                outputs[mode], (receipts / (mode + "-tests.stdout")).read_text(), plan["test_names"]
            )
            for n in range(3):
                name = f"replay-{mode}-{n}"
                path = receipts / (name + ".canonical")
                run(
                    name,
                    c.cargo(mode, replay, "--exact", "--show-output"),
                    ["UARCH_K1_REPLAY_OUT=" + str(path)],
                )
                old["check_tests"](
                    replay + ": test\n", (receipts / (name + ".stdout")).read_text(), [replay]
                )
                results[f"{mode}-{n}"] = path.read_bytes()
        canonical_sha = c.compare_replays(results)
        complete.append("full debug/release tests and six fresh-process byte-identical replays")
        for name, args in [
            ("empty", ["__u4_b_absent__", "--exact"]),
            ("ignored", ["--ignored"]),
            ("filtered", ["--skip", plan["test_names"][0]]),
        ]:
            run("fault-" + name, c.cargo("debug", *args, "--show-output"))
            try:
                old["check_tests"](
                    outputs["debug"],
                    (receipts / ("fault-" + name + ".stdout")).read_text(),
                    plan["test_names"],
                )
            except ValueError:
                complete.append(name + " selection rejected")
            else:
                raise ValueError("guard accepted " + name)
        fail(
            "fault-cache",
            ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
            r"offline|no matching package",
            ["CARGO_HOME=" + str(work / "empty-cargo")],
        )
        fail(
            "fault-toolchain",
            ["rustc", "-vV"],
            r"not installed|invalid toolchain",
            ["RUSTUP_TOOLCHAIN=u4-b-intentionally-absent"],
        )
        fail(
            "fault-license",
            [
                str(binary),
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
        complete.append("missing cache/toolchain and current Unicode-policy refusals")
        relative = "native/crates/uarch-engine/src/lib.rs"
        with m.mutation(source, relative, remove=True):
            fail(
                "fault-source",
                c.cargo("debug", "--list"),
                r"no targets specified|couldn.t read|could not read|no such file|can.t find",
            )
        original = (source / relative).read_text()
        with m.mutation(
            source, relative, original, original + '\ncompile_error!("U4_B_COMPILE_FAULT");\n'
        ):
            fail("fault-compile", c.cargo("debug", "--list"), "U4_B_COMPILE_FAULT")
        with m.mutation(
            source,
            relative,
            original,
            original
            + '\n#[test]\nfn u4_b_injected_runtime_fault() { panic!("U4_B_RUNTIME_FAULT"); }\n',
        ):
            fail(
                "fault-runtime",
                c.cargo("debug", "u4_b_injected_runtime_fault", "--exact", "--show-output"),
                "U4_B_RUNTIME_FAULT",
            )
        complete.append("actual missing source, compiler and Rust test failures")
        anchor_record = json.loads((PACKAGE / "fault-inputs.json").read_text())
        anchors = root / anchor_record["path"]
        c.require(c.digest(anchors) == anchor_record["sha256"], "fault anchor identity drift")
        mutants = json.loads(anchors.read_text())["faults"]
        for index, fault in enumerate(mutants):
            for mode in ("debug", "release"):
                name = f"semantic-{index}-{mode}"
                with m.mutation(
                    source, fault["path"], fault["before"], fault["after"], fault["original_sha256"]
                ):
                    fail(
                        name,
                        c.cargo(mode, fault["test"], "--exact", "--show-output"),
                        fault["diagnostic"],
                    )
                name += "-restored"
                run(
                    name,
                    c.cargo(mode, fault["test"], "--exact", "--show-output"),
                    ["CARGO_TARGET_DIR=" + str(work / name)],
                )
                old["check_tests"](
                    fault["test"] + ": test\n",
                    (receipts / (name + ".stdout")).read_text(),
                    [fault["test"]],
                )
        complete.append(
            str(len(mutants)) + " real semantic faults and restored positives in both modes"
        )
        replay_controls = __import__("runpy").run_path(str(PACKAGE / "replay_control.py"))
        replay_controls["execute"](
            work,
            run,
            lambda name: str(receipts / (name + ".canonical")),
            str(work / "replay-restored"),
        )
        complete.append("real release-only replay byte drift refused and restored")
        for mode in ("debug", "release"):
            name = "restored-" + mode
            run(
                name,
                c.cargo(mode, "--show-output"),
                ["CARGO_TARGET_DIR=" + str(work / "restored-all")],
            )
            old["check_tests"](
                outputs[mode], (receipts / (name + ".stdout")).read_text(), plan["test_names"]
            )
        c.write_json(
            receipts / "local-results.json",
            {
                "completed": complete,
                "canonical_payload_sha256": canonical_sha,
                "image_id": None,
                "qualifying_ci": False,
            },
        )
    finally:
        unchanged = before == c.snapshot(source)
        c.write_json(
            receipts / "local-isolation.json",
            {
                "files_compared": len(before),
                "source_bytes_and_mtimes_restored": unchanged,
                "completed": complete,
            },
        )
        c.require(unchanged, "source restoration failed")


if __name__ == "__main__":
    import sys

    execute(Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve())
