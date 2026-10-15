"""Stdlib hosted-runner checks for the proposed, separately accepted native CI job."""

import hashlib
import json
import re
import runpy
import sys
import tomllib
from pathlib import Path

A_PACKAGE = "docs/reviews/U4-A-toolchain-v1"
TOOL_COMMIT = "83a9a14fd76a00b7858ddd140cc0e0589f80a267"
TARGET = "x86_64-unknown-linux-gnu"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_package(root):
    package = root / A_PACKAGE
    for line in (package / "package.sha256").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        require(
            hashlib.sha256((package / name).read_bytes()).hexdigest() == digest,
            "tool-package checksum: " + name,
        )
    installed = {
        "Cargo.toml": "workspace.Cargo.toml",
        "crates/uarch-engine/Cargo.toml": "Cargo.toml.proposed",
        "Cargo.lock": "Cargo.lock",
        "rust-toolchain.toml": "rust-toolchain.toml",
        "deny.toml": "deny-proposed.toml",
    }
    for line in (package / "native-inputs.sha256").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        require(
            hashlib.sha256((package / installed[name]).read_bytes()).hexdigest() == digest,
            "proposed installation mapping: " + name,
        )
    lock = tomllib.loads((package / "Cargo.lock").read_text())
    locked = {(p["name"], p["version"]): p["checksum"] for p in lock["package"] if "source" in p}
    closure = json.loads((package / "crate-closure.json").read_text())
    require(
        len(locked) == 27 and locked == {(p["name"], p["version"]): p["checksum"] for p in closure},
        "lock/closure mismatch",
    )
    pins = json.loads((package / "pins.json").read_text())
    require(pins["target"] == TARGET and pins["release"] == "1.99.0", "wrong Rust selection")
    require(
        pins["compiler_commit"] == "b940084d7eb6a299eb4bfeb8e34901bc051e7ac4",
        "wrong compiler commit",
    )
    manifest = tomllib.loads((package / "Cargo.toml.proposed").read_text())
    for section, name, features in [
        ("dependencies", "serde", ["derive", "std"]),
        ("dependencies", "serde_json", ["std", "float_roundtrip"]),
        ("dev-dependencies", "proptest", ["std"]),
    ]:
        dep = manifest[section][name]
        require(
            dep
            == {
                "version": "=" + pins[name]["version"],
                "default-features": False,
                "features": features,
            },
            "direct feature/version mismatch: " + name,
        )
        require(
            locked[(name, pins[name]["version"])] == pins[name]["checksum"], "crate pin mismatch"
        )
    deny = tomllib.loads((package / "deny-proposed.toml").read_text())
    current = tomllib.loads((package / "deny-current.toml").read_text())
    require(
        deny["licenses"].pop("exceptions")
        == [{"name": "unicode-ident", "version": "=1.0.27", "allow": ["Unicode-3.0"]}],
        "exception scope widened",
    )
    require(deny == current, "unexpected licence policy delta")
    require(deny["graph"]["targets"] == [TARGET], "deny target mismatch")
    binary = json.loads((package / "cargo-deny.json").read_text())
    require(
        binary["version"] == "0.20.2"
        and binary["github_asset_digest"] == "sha256:" + binary["sha256"],
        "deny binary pin",
    )
    recipe = (package / "Dockerfile.engine.proposed").read_text()
    image = json.loads((package / "container.json").read_text())
    require(
        image["platform_digest"] in recipe
        and image["platform"] == {"architecture": "amd64", "os": "linux"},
        "base image mismatch",
    )
    for component in ("clippy-preview", "rustfmt-preview"):
        require(pins["components"][component]["gzip_sha256"] in recipe, "component recipe mismatch")
    require(binary["sha256"] in recipe, "deny recipe mismatch")
    return closure


def target_closure(closure):
    """Exact accepted Linux graph: r-efi 6.0.0 is locked/cached but UEFI-only."""
    require(len(closure) == 27, "unexpected full lock closure")
    selected = [p for p in closure if (p["name"], p["version"]) != ("r-efi", "6.0.0")]
    require(len(selected) == 26, "expected locked UEFI dependency absent")
    return selected


def validate_plan(plan):
    require(
        plan.get("format") == "uarch-k1-ci-tests/1" and plan.get("checkpoint") == "K1",
        "wrong test-plan scope",
    )
    require(
        plan.get("tool_package_commit") == TOOL_COMMIT and plan.get("target") == TARGET,
        "test-plan tool/target mismatch",
    )
    require(
        plan.get("modes") == ["debug", "release"] and plan.get("all_features") is True,
        "missing build mode/features",
    )
    require(
        isinstance(plan.get("test_names"), list)
        and bool(plan["test_names"])
        and all(isinstance(x, str) and x.strip() for x in plan["test_names"]),
        "empty test inventory",
    )
    require(
        isinstance(plan.get("workspace_targets"), list) and bool(plan["workspace_targets"]),
        "empty target inventory",
    )
    # Discovery observes names before selecting A's replay test. CI requires it separately.
    if "replay_test" in plan or "replay_output_env" in plan:
        validate_replay_plan(plan)
    return plan


def validate_replay_plan(plan):
    require(
        isinstance(plan.get("replay_test"), str)
        and plan["test_names"].count(plan["replay_test"]) == 1
        and plan.get("replay_output_env") == "UARCH_K1_REPLAY_OUT",
        "replay selection/sink mismatch",
    )
    return plan


def validate_image(data, expected):
    require(bool(re.fullmatch(r"\S+@sha256:[0-9a-f]{64}", expected)), "image must use digest")
    require(len(data) == 1, "ambiguous image receipt")
    require(
        data[0]["Os"] == "linux"
        and data[0]["Architecture"] == "amd64"
        and expected in data[0]["RepoDigests"],
        "wrong image installation",
    )


def validate_metadata(root, metadata, plan, closure):
    native = root / "native"
    require(Path(metadata["workspace_root"]).resolve() == native.resolve(), "wrong workspace root")
    guards = runpy.run_path(str(root / "docs/reviews/U4-B-native-ci-v1/ci_guard.py"))
    guards["check_source"](native, metadata)
    packages = {p["id"]: p for p in metadata["packages"]}
    members = [packages[p] for p in metadata["workspace_members"]]
    require(len(members) == 1 and members[0]["name"] == "uarch-engine", "wrong workspace members")
    require(
        Path(members[0]["manifest_path"]).resolve()
        == (native / "crates/uarch-engine/Cargo.toml").resolve(),
        "wrong manifest installation",
    )
    targets = [{"name": t["name"], "kind": t["kind"]} for t in members[0]["targets"] if t["test"]]
    require(
        sorted(targets, key=lambda x: x["name"])
        == sorted(plan["workspace_targets"], key=lambda x: x["name"]),
        "target inventory drift",
    )
    expected = {(p["name"], p["version"]): p for p in closure}
    actual = {(p["name"], p["version"]) for p in packages.values() if p["source"] is not None}
    require(actual == set(expected), "external dependency inventory drift")
    for node in metadata["resolve"]["nodes"]:
        package = packages[node["id"]]
        if package["source"] is not None:
            require(
                package["source"] == "registry+https://github.com/rust-lang/crates.io-index",
                "unexpected registry",
            )
            wanted = expected[(package["name"], package["version"])]
            require(sorted(node["features"]) == sorted(wanted["features"]), "feature drift")


def validate_results(root, receipts, plan):
    validate_replay_plan(plan)
    guards = runpy.run_path(str(root / "docs/reviews/U4-B-native-ci-v1/ci_guard.py"))
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
        "metadata-target",
        "fmt",
        "clippy-tests",
        "licences",
        "debug-list",
        "debug-tests",
        "release-list",
        "release-tests",
    ]
    for name in commands:
        require((receipts / (name + ".exit")).read_text().strip() == "0", "failed command: " + name)
    for tool in ("rustc", "cargo", "rustfmt", "clippy", "cargo-deny"):
        require(
            (receipts / (tool + ".log")).read_bytes()
            == (root / A_PACKAGE / "version-receipts" / (tool + ".txt")).read_bytes(),
            "wrong container tool: " + tool,
        )
    for mode in plan["modes"]:
        guards["check_tests"](
            (receipts / (mode + "-list.log")).read_text(),
            (receipts / (mode + "-tests.log")).read_text(),
            plan["test_names"],
        )

    validate_replays(root, receipts, plan)


def validate_replays(root, receipts, plan):
    guards = runpy.run_path(str(root / "docs/reviews/U4-B-native-ci-v1/ci_guard.py"))
    payloads = []
    for mode in plan["modes"]:
        listing = receipts / ("replay-" + mode + "-list")
        require(listing.with_suffix(".exit").read_text().strip() == "0", "replay list failed")
        for number in range(3):
            name = f"replay-{mode}-{number}"
            require((receipts / (name + ".exit")).read_text().strip() == "0", "replay failed")
            guards["check_tests"](
                listing.with_suffix(".log").read_text(),
                (receipts / (name + ".log")).read_text(),
                [plan["replay_test"]],
            )
            payloads.append((receipts / (name + ".bin")).read_bytes())
    require(len(payloads) == 6 and bool(payloads[0]), "empty replay payload")
    require(all(data == payloads[0] for data in payloads), "replay bytes differ")


def main():
    mode, *args = sys.argv[1:]
    if mode == "package":
        print("verified external locked crates:", len(validate_package(Path(args[0]))))
    elif mode == "preflight":
        validate_package(Path(args[0]))
        validate_replay_plan(validate_plan(json.loads(Path(args[1]).read_text())))
    elif mode == "image":
        validate_image(json.loads(Path(args[0]).read_text()), args[1])
    elif mode in ("metadata", "metadata-target"):
        root, filename, plan = map(Path, args)
        validate_metadata(
            root,
            json.loads(filename.read_text()),
            validate_plan(json.loads(plan.read_text())),
            target_closure(validate_package(root))
            if mode == "metadata-target"
            else validate_package(root),
        )
    elif mode == "results":
        root, receipts, plan = map(Path, args)
        validate_results(root, receipts, validate_plan(json.loads(plan.read_text())))
    else:
        raise ValueError("unknown mode")


if __name__ == "__main__":
    main()
