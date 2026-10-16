"""Reproducible private offline candidate construction; never public successful execution.

prepare copies only explicitly bound inputs and verified cache, creates real identities
and pending jobs. build/test run the approved targets. No pull/install/global overrides.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import time
from pathlib import Path

from generate_identity import generate
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import canonical_json, content_hash, sha256, strict_json_loads
from uarch_contract.mapped import NativeEngineIdentity, hardware_projection, validate_job

from rkuarch.engines.native.records import BuildInputs

ROOT = Path(__file__).resolve().parents[2]
C1 = ROOT / "docs/reviews/U4-A-K2-C1-precise-v1"
PACKAGE = ROOT / "docs/reviews/U4-A-K2-construction-v1"
BIN = "/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/"
IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value))


def digest(path: Path) -> str:
    return sha256(path.read_bytes())


def cache_inventory(root: Path) -> dict:
    return {
        str(p.relative_to(root)): {
            "sha256": digest(p).removeprefix("sha256:"),
            "bytes": p.stat().st_size,
        }
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def command(
    scratch: Path, name: str, argv: list[str], *, stdin: bytes | None = None
) -> tuple[int, bytes, bytes]:
    receipts = scratch / "commands"
    receipts.mkdir(exist_ok=True)
    assert not (receipts / (name + ".json")).exists(), "never overwrite a command receipt"
    env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(scratch / "docker-config")}
    start = time.time_ns()
    failure = None
    cleanup = None
    with (
        (receipts / (name + ".stdout")).open("wb") as stdout,
        (receipts / (name + ".stderr")).open("wb") as stderr,
    ):
        try:
            result = subprocess.run(
                argv, input=stdin, stdout=stdout, stderr=stderr, env=env, timeout=600
            )
            status = result.returncode
        except (subprocess.TimeoutExpired, OSError) as exc:
            failure = repr(exc)
            status = 124 if isinstance(exc, subprocess.TimeoutExpired) else 127
            if "--cidfile" in argv:
                cid = Path(argv[argv.index("--cidfile") + 1])
                if cid.exists():
                    container_id = cid.read_text().strip()
                    if len(container_id) == 64 and all(
                        c in "0123456789abcdef" for c in container_id
                    ):
                        cleanup_argv = argv[:3] + ["rm", "--force", container_id]
                        cleaned = subprocess.run(
                            cleanup_argv, env=env, capture_output=True, timeout=30
                        )
                        cleanup = {
                            "argv": cleanup_argv,
                            "exit_code": cleaned.returncode,
                            "stdout": cleaned.stdout.decode(errors="replace"),
                            "stderr": cleaned.stderr.decode(errors="replace"),
                        }

    output = (receipts / (name + ".stdout")).read_bytes()
    error = (receipts / (name + ".stderr")).read_bytes()
    write(
        receipts / (name + ".json"),
        {
            "argv": argv,
            "environment": env,
            "exit_code": status,
            "failure": failure,
            "timeout_cleanup": cleanup,
            "started_ns": start,
            "elapsed_ns": time.time_ns() - start,
            "stdout_byte_hash": sha256(output),
            "stderr_byte_hash": sha256(error),
            "stdin_byte_hash": None if stdin is None else sha256(stdin),
            "network": "Docker --network none; local Unix socket; no registry access",
        },
    )
    print(name, status, flush=True)
    if status:
        print(error.decode(errors="replace")[-4000:], flush=True)
    return status, output, error


def base(scratch: Path, mode: str, phase: str, build: BuildInputs) -> list[str]:
    receipt_dir = scratch / "receipts" / mode / phase
    receipt_dir.mkdir(parents=True, exist_ok=True)
    argv = [
        "/usr/bin/docker",
        "--host",
        "unix:///var/run/docker.sock",
        "run",
        "--rm",
        "--cidfile",
        str(scratch / "commands" / (mode + "-" + phase + "-container-id")),
        "--pull",
        "never",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp",
        "--workdir",
        "/work/native",
    ]
    for src, dst, readonly in [
        (scratch / "workspace", "/work", True),
        (scratch / "cache", "/cargo-home", True),
        (scratch / "targets" / mode, "/target", False),
        (scratch / "controls", "/controls", True),
        (scratch / "vectors", "/vectors", True),
        (receipt_dir, "/receipts", False),
    ]:
        src.mkdir(parents=True, exist_ok=True)
        argv += ["--mount", f"type=bind,src={src},dst={dst}" + (",readonly" if readonly else "")]
    argv += ["--entrypoint", "/usr/bin/env", IMAGE, "-i"]
    argv += [k + "=" + v for k, v in build.permitted_environment.items()]
    return argv


def prepare(scratch: Path, inputs: Path) -> None:
    scratch.mkdir(exist_ok=False)
    for directory in [
        "workspace",
        "cache",
        "controls",
        "vectors/jobs",
        "docker-config",
        "commands",
        "targets/debug",
        "targets/release",
    ]:
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    build = BuildInputs.model_validate(strict_json_loads(inputs.read_bytes()))
    # Actual image must exist and match before cache copying, generation or builds.
    status, output, _ = command(
        scratch,
        "image-inspect",
        [
            "/usr/bin/docker",
            "--host",
            "unix:///var/run/docker.sock",
            "image",
            "inspect",
            IMAGE,
            "--format",
            "{{json .Id}} {{json .Os}} {{json .Architecture}}",
        ],
    )
    assert status == 0 and output == (C1 / "image-inspect.stdout").read_bytes()
    expected = json.loads((C1 / "cache-inventory.json").read_bytes())
    cache = Path(expected["private_root"])
    assert cache_inventory(cache) == expected["files"]
    shutil.copytree(cache, scratch / "cache", dirs_exist_ok=True)
    assert cache_inventory(scratch / "cache") == expected["files"]
    for file in build.source_files:
        path = ROOT / file.path
        assert digest(path) == file.byte_hash
        target = scratch / "workspace" / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name in ["rustc-wrapper.sh", "linker.sh"]:
        shutil.copy2(PACKAGE / "inputs" / name, scratch / "controls" / name)
        (scratch / "controls" / name).chmod(0o555)
    for name, tool, args in [
        ("rustc", BIN + "rustc", ["-vV"]),
        ("cargo", BIN + "cargo", ["-vV"]),
        ("cargo-deny", "/usr/local/cargo/bin/cargo-deny", ["--version"]),
        ("rustfmt", BIN + "rustfmt", ["--version"]),
        ("clippy", BIN + "clippy-driver", ["--version"]),
    ]:
        status, output, _ = command(
            scratch, name, base(scratch, "debug", "preflight-" + name, build) + [tool, *args]
        )
        assert status == 0 and output == (C1 / (name + ".stdout")).read_bytes(), name
    identity = generate(ROOT, inputs, scratch / "workspace")
    write(scratch / "identity.json", identity)
    write(scratch / "BuildInputs.json", build)
    corpus = json.loads((PACKAGE / "corpus/inventory.json").read_bytes())
    registry = json.loads((ROOT / corpus["registry"]["path"]).read_bytes())
    trust = json.loads((ROOT / build.trust_file.path).read_bytes())
    write(scratch / "vectors/authority.json", {"engine": identity["engine"], "trust": trust})
    names = []
    jobs = []
    maximum = 0
    for case in corpus["cases"]:
        b = json.loads((ROOT / case["bundle"]["path"]).read_bytes())
        p = b["points"][0]
        profile = json.loads((ROOT / case["profile"]["path"]).read_bytes())
        entry = next(e for e in profile["entries"] if e["case_id"] == case["case_id"])
        raw = {
            "protocol": "uarch-engine/3",
            "bundle_hash": b["bundle_hash"],
            "point_hash": p["payload_hash"],
            "request_hash": None,
            "assumptions_hash": b["assumptions_hash"],
            "engine": identity["engine"],
            "mapped_point": p,
            "workload_closure": b,
            "assumptions": b["assumptions"],
            "hardware": hardware_projection(
                HardwareSpec.model_validate(b["hardware_spec"])
            ).model_dump(mode="json"),
            "hardware_spec_hash": b["hardware_spec_hash"],
            "rank": b["rank"],
            "precision": None,
            "fidelity_detail": None,
            "frequency_ratio": p["frequency_ratio"],
            "freq_hz": entry["freq_hz"],
            "initial_state": p["initial_state"],
            "priming_iterations": p["priming_iterations"],
            "seed": entry["seed"],
            "admission": b["admission"],
            "state_model": "fixed_delay/1",
            "clock_setup": case["clock_setup"],
            "owner_enumeration": "native-owners/1",
            "owners": [
                {"owner_id": owner, "resource": f"fixture:{owner}"}
                for owner in b["scope"]["owner_ids"]
            ],
            "registry": registry,
            "profile": profile,
        }
        raw["job_hash"] = content_hash(raw)
        validated = validate_job(
            raw,
            invocation="test",
            checkpoint="K2",
            trusted_registry_hash=trust["registry_hash"],
            trusted_profile_hash=profile["profile_hash"],
            expected_engine=NativeEngineIdentity.model_validate(identity["engine"]),
        )
        name = "jobs/" + case["case_id"] + ".json"
        write(scratch / "vectors" / name, validated)
        names.append(name)
        maximum = max(maximum, (scratch / "vectors" / name).stat().st_size)
        jobs.append(
            {
                "case_id": case["case_id"],
                "job_hash": validated.job_hash,
                "file": {
                    "path": "vectors/" + name,
                    "byte_hash": digest(scratch / "vectors" / name),
                },
                "expected_outcome": case["execution_outcome"],
            }
        )
    peer = ROOT / "docs/reviews/U4-B-K2-construction-audit-v1"
    directory = scratch / "vectors/peer-dto"
    directory.mkdir()
    frozen = {}
    for module_name, filename, receipt in [
        ("dto_vectors", "b-dto.json", "dto-freeze.json"),
        ("dto_key_vectors", "b-keys.json", "dto-key-freeze.json"),
        ("dto_coordinate_vectors", "b-coordinates.json", "dto-coordinate-freeze.json"),
    ]:
        spec = importlib.util.spec_from_file_location(module_name, peer / (module_name + ".py"))
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = module.prepare(ROOT, directory / filename)
        expected_peer = json.loads((peer / receipt).read_bytes())
        assert actual == expected_peer
        frozen[filename] = actual
    shutil.copyfile(PACKAGE / "inputs/peer-dto-expectations.json", directory / "expectations.json")
    write(directory / "freeze.json", frozen)
    write(scratch / "vectors/index.json", names)
    write(
        scratch / "pending-jobs.json",
        {
            "format": "uarch-k2-pending-jobs/1",
            "status": "no public execution; final human authority absent",
            "jobs": jobs,
            "maximum_input_bytes": maximum,
        },
    )
    assert maximum <= 64 * 1024 * 1024
    assert cache_inventory(cache) == expected["files"]
    write(
        scratch / "preservation-before.json",
        {
            "accepted_cache_unchanged": True,
            "private_cache_matches": True,
            "live_lock_hash": digest(ROOT / "native/Cargo.lock"),
            "source_files": {f.path: f.byte_hash for f in build.source_files},
        },
    )
    print(
        "Prepared",
        len(jobs),
        "actual-identity pending jobs; executed zero; max bytes",
        maximum,
        flush=True,
    )


def execute(scratch: Path, action: str, mode: str) -> None:
    build = BuildInputs.model_validate_json((scratch / "BuildInputs.json").read_bytes())
    for file in build.source_files:
        assert digest(scratch / "workspace" / file.path) == file.byte_hash
    expected = json.loads((C1 / "cache-inventory.json").read_bytes())
    assert cache_inventory(scratch / "cache") == expected["files"]
    argv = base(scratch, mode, action, build)
    if action == "build":
        config = next(x for x in build.mode_configs if x.mode == mode)
        argv += [BIN + "cargo", *config.cargo_args]
    elif action in ("test", "validate", "peer"):
        if action == "validate":
            argv += ["K2_CARRIER_CORPUS=/vectors"]
        if action == "peer":
            argv += ["K2_PEER_DTO_DIR=/vectors/peer-dto"]
        argv += [BIN + "cargo", "test", "--offline", "--locked", "-p", "uarch-engine", "--lib"]
        if mode == "release":
            argv.append("--release")
        if action == "validate":
            argv += [
                "admission::tests::frozen_full_corpus_validation_only",
                "--",
                "--ignored",
                "--exact",
                "--nocapture",
            ]
        if action == "peer":
            argv += [
                "peer_dto_tests::published_peer_dto_cases",
                "--",
                "--ignored",
                "--exact",
                "--nocapture",
            ]
    elif action == "clippy":
        argv += [
            BIN + "cargo",
            "clippy",
            "--offline",
            "--locked",
            "--all-targets",
            "--",
            "-D",
            "warnings",
        ]
    else:
        raise ValueError("explicit bounded action required")
    status, _, _ = command(scratch, mode + "-" + action, argv)
    assert cache_inventory(scratch / "cache") == expected["files"]
    assert digest(scratch / "workspace/native/Cargo.lock") == digest(ROOT / "native/Cargo.lock")
    if status:
        raise SystemExit(status)
    if action == "build":
        target = scratch / "targets" / mode / mode
        # Cargo's debug profile directory is debug; release is release.
        executable = target / "uarch-engine"
        assert executable.is_file()
        write(
            scratch / (mode + "-binaries.json"),
            {
                "executable_byte_hash": digest(executable),
                "executable_path": str(executable),
                "rlibs": {
                    str(p.relative_to(scratch)): digest(p)
                    for p in sorted((target / "deps").glob("libuarch_engine-*.rlib"))
                },
                "engine": json.loads((scratch / "identity.json").read_bytes())["engine"],
            },
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "build", "test", "validate", "peer", "clippy"])
    p.add_argument("--scratch", type=Path, required=True)
    p.add_argument("--inputs", type=Path)
    p.add_argument("--mode", choices=["debug", "release"], default="debug")
    args = p.parse_args()
    if args.action == "prepare":
        if args.inputs is None:
            p.error("--inputs required for prepare")
        prepare(args.scratch, args.inputs)
    else:
        execute(args.scratch, args.action, args.mode)


if __name__ == "__main__":
    main()
