"""Disposable accepted K1 construction; no registry publication or host installation."""

import argparse
import hashlib
import io
import json
import os
import re
import runpy
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

A = "docs/reviews/U4-A-toolchain-v1"
B = "docs/reviews/U4-B-final-reconciliation-v1"
OLD = "docs/reviews/U4-B-native-ci-v1"
ADR = "docs/decisions/U0011-the-native-engine-core.md"
ADR_SHA = "f452e2263b9e64a837e0a9fccaae73c7a5b01bd601a5f7cee141e06a7ca23a8f"
TARGET = "x86_64-unknown-linux-gnu"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(receipts, name, argv, cwd=None, fail=True):
    """Retain exact argv, stdout, stderr and exit even for expected failures."""
    require(not (receipts / (name + ".json")).exists(), "refuse receipt overwrite: " + name)
    with (receipts / (name + ".stdout")).open("wb") as out:
        with (receipts / (name + ".stderr")).open("wb") as err:
            try:
                result = subprocess.run(argv, cwd=cwd, stdout=out, stderr=err, check=False)
                status = result.returncode
            except OSError as exc:
                err.write(str(exc).encode())
                status = 127
    write_json(receipts / (name + ".json"), {"argv": argv, "cwd": str(cwd), "exit": status})
    if fail:
        require(status == 0, f"{name} exited {status}; retained receipts")
    return status


def export(root, revision, destination):
    require(bool(re.fullmatch("[0-9a-f]{40}", revision)), "full published commit required")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "origin/main"], cwd=root, check=True
    )
    paths = [
        "native",
        A,
        ADR,
        B + "/native-container.sh",
        B + "/offline-cache.fragment",
        B + "/ci_host_guard.py",
        OLD + "/ci_guard.py",
    ]
    archive = subprocess.check_output(["git", "archive", revision, "--", *paths], cwd=root)
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            target = destination / member.name
            require(target.resolve().is_relative_to(destination.resolve()), "unsafe archive path")
            if member.isdir():
                target.mkdir(exist_ok=True, parents=True)
            else:
                require(member.isfile(), "symlinks/special files require review")
                target.parent.mkdir(exist_ok=True, parents=True)
                with source.extractfile(member) as data:
                    target.write_bytes(data.read())


def installed(root):
    require(digest(root / ADR) == ADR_SHA, "installed human release mismatch")
    guard = runpy.run_path(str(root / B / "ci_host_guard.py"))
    closure = guard["validate_package"](root)
    for line in (root / A / "native-inputs.sha256").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        path = root / "native" / name
        require(
            path.is_file() and digest(path) == expected,
            "accepted native input missing/drift: " + name,
        )
    require(
        any(f.read_text().strip() for f in (root / "native").rglob("*.rs")),
        "no actual K1 source; no synthetic seed allowed",
    )
    return closure


def recipe(root):
    return (root / A / "Dockerfile.engine.proposed").read_bytes() + (
        root / B / "offline-cache.fragment"
    ).read_bytes()


def image_identity(data, identity, base_config):
    require(bool(re.fullmatch(r"sha256:[0-9a-f]{64}", identity)), "real local image ID required")
    require(len(data) == 1 and data[0]["Id"] == identity, "wrong built image")
    require(identity != base_config, "base config is not the final builder")
    require(data[0]["Os"] == "linux" and data[0]["Architecture"] == "amd64", "wrong platform")
    require(bool(data[0]["RootFS"]["Layers"]), "missing image layer identity")


def container(work, argv, extra=()):
    root = (work / "source").resolve()
    identity = (work / "image.id").read_text().strip()
    target = work / "target"
    target.mkdir(exist_ok=True)
    return [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--mount",
        f"type=bind,src={root},dst={root},readonly",
        "--mount",
        f"type=bind,src={target.resolve()},dst=/target",
        "--mount",
        f"type=bind,src={(work / 'receipts').resolve()},dst=/receipts",
        "--tmpfs",
        "/tmp",
        "--workdir",
        str(root / "native"),
        "--env",
        "CARGO_HOME=/usr/local/cargo",
        "--env",
        "RUSTUP_HOME=/usr/local/rustup",
        "--env",
        "RUSTUP_TOOLCHAIN=1.99.0-x86_64-unknown-linux-gnu",
        "--env",
        "RUSTUP_AUTO_INSTALL=0",
        "--env",
        "CARGO_NET_OFFLINE=true",
        "--env",
        "CARGO_TARGET_DIR=/target",
        *extra,
        "--entrypoint",
        argv[0],
        identity,
        *argv[1:],
    ]


def hashes(output):
    result = {}
    for line in output.splitlines():
        sha, name = line.split(maxsplit=1)
        require(bool(re.fullmatch("[0-9a-f]{64}", sha)), "invalid hash receipt")
        require(name not in result, "duplicate hash receipt")
        result[name] = sha
    return result


def verify_cache(closure, output, notices):
    archives = hashes(output)
    expected = {p["name"] + "-" + p["version"] + ".crate": p["checksum"] for p in closure}
    require(len(archives) == len(expected), "cache archive count mismatch")
    require(
        {Path(k).name: v for k, v in archives.items()} == expected,
        "cache archive checksum mismatch",
    )
    wanted = {
        p["name"] + "-" + p["version"] + "/" + n["path"]: n["sha256"]
        for p in closure
        for n in p["notice_files"]
    }
    actual = hashes(notices)
    require(len(actual) == len(wanted), "cache notice count mismatch")
    for suffix, sha in wanted.items():
        matches = [v for k, v in actual.items() if k.endswith("/" + suffix)]
        require(matches == [sha], "cache notice mismatch: " + suffix)


def cargo(mode, *tail):
    return [
        "cargo",
        "test",
        "--locked",
        "--offline",
        "--workspace",
        "--all-targets",
        "--all-features",
        "--target",
        TARGET,
        *(["--release"] if mode == "release" else []),
        "--",
        *tail,
    ]


def discovery(root, metadata, outputs, selected_metadata):
    guard = runpy.run_path(str(root / B / "ci_host_guard.py"))
    old = runpy.run_path(str(root / OLD / "ci_guard.py"))
    names = [old["listed_tests"](outputs[mode]) for mode in ("debug", "release")]
    require(
        names[0] and names[0] == names[1],
        "empty or mode-dependent inventory requires reconciliation",
    )
    packages = {p["id"]: p for p in metadata["packages"]}
    targets = [
        {"name": t["name"], "kind": t["kind"]}
        for member in metadata["workspace_members"]
        for t in packages[member]["targets"]
        if t["test"]
    ]
    plan = {
        "format": "uarch-k1-ci-tests/1",
        "checkpoint": "K1",
        "tool_package_commit": guard["TOOL_COMMIT"],
        "target": TARGET,
        "modes": ["debug", "release"],
        "all_features": True,
        "workspace_targets": targets,
        "test_names": sorted(names[0].elements()),
    }
    guard["validate_plan"](plan)
    closure = installed(root)
    guard["validate_metadata"](root, metadata, plan, closure)
    selected = [p for p in closure if (p["name"], p["version"]) != ("r-efi", "6.0.0")]
    require(len(selected) == 26, "unexpected selected Linux closure")
    guard["validate_metadata"](root, selected_metadata, plan, selected)
    return plan


def compare_replays(outputs):
    require(
        set(outputs) == {f"{mode}-{n}" for mode in ("debug", "release") for n in range(3)},
        "six fresh process receipts required",
    )
    values = list(outputs.values())
    require(all(isinstance(value, bytes) and value for value in values), "missing replay bytes")
    require(len(set(values)) == 1, "canonical debug/release replay mismatch")
    return hashlib.sha256(values[0]).hexdigest()


def build(root, revision, work):
    work.mkdir()  # New directory only. Never reuse stale receipts/cache/source.
    receipts = work / "receipts"
    receipts.mkdir()
    write_json(
        receipts / "subject.json", {"revision": revision, "driver_sha256": digest(Path(__file__))}
    )
    export(root, revision, work / "source")
    source = work / "source"
    installed(source)
    context = work / "context"
    context.mkdir()
    # Minimal Docker context: only exact native Git bytes and the accepted hash list.
    import shutil

    shutil.copytree(source / "native", context / "native")
    dest = context / A
    dest.mkdir(parents=True)
    shutil.copyfile(source / A / "native-inputs.sha256", dest / "native-inputs.sha256")
    (context / "Dockerfile").write_bytes(recipe(source))
    write_json(
        receipts / "construction.json",
        {
            "recipe_sha256": digest(context / "Dockerfile"),
            "native_git_tree": subprocess.check_output(
                ["git", "rev-parse", revision + ":native"], cwd=root, text=True
            ).strip(),
            "base": json.loads((source / A / "container.json").read_text())["platform_digest"],
            "distribution": "none; local image only",
        },
    )
    run(receipts, "docker-version", ["docker", "version"])
    run(
        receipts,
        "build",
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "--iidfile",
            str(work / "image.id"),
            str(context),
        ],
    )
    identity = (work / "image.id").read_text().strip()
    run(receipts, "image-inspect", ["docker", "image", "inspect", identity])
    info = json.loads((receipts / "image-inspect.stdout").read_text())
    base = json.loads((source / A / "container.json").read_text())["manifest"]["config"]["digest"]
    image_identity(info, identity, base)


def _verify(work, replay_test):
    source = work / "source"
    receipts = work / "receipts"
    closure = installed(source)
    run(
        receipts,
        "inspect",
        container(
            work, ["/bin/bash", str(source / B / "native-container.sh"), str(source), "inspect"]
        ),
    )
    run(
        receipts,
        "cache-archives",
        container(
            work,
            [
                "/bin/bash",
                "-c",
                "find /usr/local/cargo/registry/cache -type f -name '*.crate' -exec sha256sum {} +",
            ],
        ),
    )
    suffixes = [
        p["name"] + "-" + p["version"] + "/" + n["path"] for p in closure for n in p["notice_files"]
    ]
    script = (
        "set -euo pipefail; for wanted do "
        'for file in /usr/local/cargo/registry/src/*/"$wanted"; '
        'do sha256sum "$file"; done; done'
    )
    run(
        receipts,
        "cache-notices",
        container(work, ["/bin/bash", "-c", script, "cache-notices", *suffixes]),
    )
    verify_cache(
        closure,
        (receipts / "cache-archives.stdout").read_text(),
        (receipts / "cache-notices.stdout").read_text(),
    )
    outputs = {}
    for mode in ("debug", "release"):
        run(receipts, mode + "-list", container(work, cargo(mode, "--list")))
        outputs[mode] = (receipts / (mode + "-list.stdout")).read_text()
    for name, flags in [
        ("metadata-full", []),
        ("metadata-selected", ["--filter-platform", TARGET]),
    ]:
        run(
            receipts,
            name,
            container(
                work,
                [
                    "cargo",
                    "metadata",
                    "--locked",
                    "--offline",
                    "--all-features",
                    "--format-version",
                    "1",
                    *flags,
                ],
            ),
        )
    metadata = json.loads((receipts / "metadata-full.stdout").read_text())
    selected = json.loads((receipts / "metadata-selected.stdout").read_text())
    plan = discovery(source, metadata, outputs, selected)
    require(
        Counter(plan["test_names"])[replay_test] == 1, "replay test must identify one actual test"
    )
    plan.update(replay_test=replay_test, replay_output_env="UARCH_K1_REPLAY_OUT")
    write_json(receipts / "test-plan.candidate.json", plan)
    # A review of this observed candidate precedes CI installation; discovery is not approval.
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
                TARGET,
                "--",
                "-D",
                "warnings",
            ],
        ),
        (
            "deny",
            [
                "cargo",
                "deny",
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
        run(receipts, name, container(work, argv))
    old = runpy.run_path(str(source / OLD / "ci_guard.py"))
    replays = {}
    for mode in ("debug", "release"):
        run(receipts, mode + "-tests", container(work, cargo(mode, "--show-output")))
        old["check_tests"](
            outputs[mode], (receipts / (mode + "-tests.stdout")).read_text(), plan["test_names"]
        )
        for n in range(3):
            name = f"replay-{mode}-{n}"
            run(
                receipts,
                name,
                container(
                    work,
                    cargo(mode, replay_test, "--exact", "--show-output", "--test-threads=1"),
                    ["--env", f"UARCH_K1_REPLAY_OUT=/receipts/{name}.canonical"],
                ),
            )
            result = (receipts / (name + ".stdout")).read_text()
            old["check_tests"](replay_test + ": test\n", result, [replay_test])
            replays[f"{mode}-{n}"] = (receipts / (name + ".canonical")).read_bytes()
    write_json(
        receipts / "verified.json",
        {
            "cache_crates": len(closure),
            "image_id": (work / "image.id").read_text().strip(),
            "canonical_payload_sha256": compare_replays(replays),
            "native_qualification": False,
        },
    )


def snapshot(root):
    return {
        str(p.relative_to(root)): (digest(p), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def verify(work, replay_test):
    source = work / "source"
    require(
        source.resolve().is_relative_to(work.resolve()) and not (source / ".git").exists(),
        "disposable export required",
    )
    before = snapshot(source)
    try:
        _verify(work, replay_test)
    finally:
        unchanged = before == snapshot(source)
        write_json(
            work / "receipts" / "isolation.json",
            {"files_compared": len(before), "source_bytes_and_mtimes_unchanged": unchanged},
        )
        require(unchanged, "source isolation failure")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("root", type=Path)
    b.add_argument("revision")
    b.add_argument("work", type=Path)
    v = sub.add_parser("verify")
    v.add_argument("work", type=Path)
    v.add_argument("--replay-test", required=True)
    args = parser.parse_args()
    if args.command == "build":
        build(args.root.resolve(), args.revision, args.work.resolve())
    else:
        verify(args.work.resolve(), args.replay_test)


if __name__ == "__main__":
    main()
