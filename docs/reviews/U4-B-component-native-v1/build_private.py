"""Build an explicit published native candidate with B's private cfg(test) probe.

Uses the prior approved monitor, accepted offline cache, controls and strace bytes.
This creates unit executables only; it never generates BuildTrust or public identity.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = Path("/tmp/u4-b-candidate04-audit")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("commit")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", args.commit], cwd=ROOT, text=True).strip()
    assert commit == args.commit and len(commit) == 40
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=ROOT, check=True
    )
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    for name in ("receipts", "canary", "docker-config", "source"):
        (out / name).mkdir()
    export = subprocess.check_output(["git", "archive", commit, "native"], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(export)) as archive:
        archive.extractall(out / "source", filter="data")
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
        result = monitor.run(out, mode, cmd, trace=True, build=True)
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
