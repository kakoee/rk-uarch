"""Build the exact reconstructed amendment with a private cfg(test) probe.

Uses the prior bounded monitor and accepted offline cache/controls. No trace capture.
This creates unit executables only; it never generates BuildTrust or public identity.
"""

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = Path("/tmp/u4-b-candidate04-audit")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patched_source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(
        (ROOT / "docs/reviews/U4-A-issue-edge-amendment-v2/manifest.json").read_text()
    )
    for row in manifest["files"]:
        assert digest(args.patched_source / row["path"]) == row["postimage_sha256"]
    commit = "7d61d6a02644519d4a7b8b1ce9287e60cd03ca13 plus exact manifest patches"
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    for name in ("receipts", "canary", "docker-config", "source", "output"):
        (out / name).mkdir()
    shutil.copytree(args.patched_source / "native", out / "source/native")
    source = out / "source"
    assert (source / "native/crates/uarch-engine/src/component.rs").is_file()
    preimages = {str(p.relative_to(source)): digest(p) for p in source.rglob("*") if p.is_file()}
    for name in ("cache", "controls", "diagnostics"):
        shutil.copytree(OLD / name, out / name, symlinks=True)
    preserved = json.loads(
        (ROOT / "docs/reviews/U4-B-K2-candidate-04-audit-v1/preservation.json").read_text()
    )
    for path, binding in preserved["diagnostics"].items():
        assert "sha256:" + digest(out / "diagnostics" / path) == binding["byte_hash"]
    cache = {
        str(p.relative_to(out / "cache")): digest(p)
        for p in (out / "cache").rglob("*")
        if p.is_file()
    }
    assert all(digest(OLD / "cache" / p) == value for p, value in cache.items())
    accepted_cache = json.loads(
        (ROOT / "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json").read_text()
    )["files"]
    assert cache == {p: value["sha256"] for p, value in accepted_cache.items()}
    lib = source / "native/crates/uarch-engine/src/lib.rs"
    lib.write_bytes(lib.read_bytes() + b"\n#[cfg(test)]\nmod b_private_probe;\n")
    shutil.copyfile(HERE / "private_probe.rs", lib.with_name("b_private_probe.rs"))
    postimages = {str(p.relative_to(source)): digest(p) for p in source.rglob("*") if p.is_file()}
    manifest = dict(
        source_commit=commit,
        source_preimages=preimages,
        private_postimages=postimages,
        synthetic_harness_sha256=digest(HERE / "private_probe.rs"),
        cache=cache,
        public_executable_built=False,
        authority_created=False,
        commands={},
    )
    monitor_path = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1/trace_monitor.py"
    spec = importlib.util.spec_from_file_location("approved_monitor", monitor_path)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    manifest["monitor_sha256"] = digest(monitor_path)
    manifest["image"] = monitor.IMAGE
    manifest["controls"] = {p.name: digest(p) for p in (out / "controls").iterdir()}
    for mode in ("debug", "release"):
        cmd = [
            monitor.TOOL + "cargo",
            "test",
            "--offline",
            "--locked",
            "-p",
            "uarch-engine",
            "--lib",
            "--no-run",
            "--message-format=json",
        ]
        if mode == "release":
            cmd.append("--release")
        result = monitor.run(out, mode, cmd, trace=False, build=True)
        manifest["commands"][mode] = result
        (out / "build.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        assert result["exit_code"] == 0 and not result["stop_reason"], result
        records = [
            json.loads(line)
            for line in (out / "receipts" / mode / "stdout").read_text().splitlines()
            if line.startswith("{")
        ]
        executables = [
            r["executable"]
            for r in records
            if r.get("reason") == "compiler-artifact"
            and r.get("executable")
            and r["target"]["name"] == "uarch_engine"
        ]
        assert len(executables) == 1
        relative = str(Path(executables[0]).relative_to("/target"))
        result.update(
            test_executable=relative,
            test_executable_sha256=digest(out / (mode + "-target") / relative),
        )
        (out / "build.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(mode, result["test_executable_sha256"], flush=True)
    assert all(digest(source / p) == value for p, value in postimages.items())
    assert all(digest(out / "cache" / p) == value for p, value in cache.items())


if __name__ == "__main__":
    main()
