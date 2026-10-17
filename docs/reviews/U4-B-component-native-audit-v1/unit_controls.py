"""Run selected existing native tests in immutable private executables; no public CLI."""

import argparse
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    out = args.output.resolve()
    assert out.is_relative_to(Path("/tmp"))
    out.mkdir(exist_ok=False)
    meta = json.loads((build / "build.json").read_text())
    rows = []
    selections = [
        ["--list"],
        ["component", "--nocapture"],
        ["release_tests::", "--nocapture"],
        ["tests::canonical_replay_private_bytes", "--exact", "--nocapture"],
    ]
    for mode in ("debug", "release"):
        target = build / (mode + "-target")
        command = meta["commands"][mode]
        executable = target / command["test_executable"]
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        assert digest == command["test_executable_sha256"]
        for index, selection in enumerate(selections):
            name = "u4-b-native-control-" + uuid.uuid4().hex
            argv = [
                "/usr/bin/docker",
                "--host",
                "unix:///var/run/docker.sock",
                "run",
                "--rm",
                "--name",
                name,
                "--pull",
                "never",
                "--network",
                "none",
                "--read-only",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--tmpfs",
                "/tmp",
                "--mount",
                f"type=bind,src={target},dst=/target,readonly",
                "--entrypoint",
                "/usr/bin/env",
                meta["image"],
                "-i",
                "LC_ALL=C",
                "/target/" + command["test_executable"],
                *selection,
            ]
            env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(build / "docker-config")}
            try:
                p = subprocess.run(argv, env=env, capture_output=True, timeout=30)
            except subprocess.TimeoutExpired:
                subprocess.run(argv[:3] + ["kill", name], env=env, capture_output=True, timeout=5)
                raise
            prefix = mode + "-" + str(index)
            (out / (prefix + ".stdout")).write_bytes(p.stdout)
            (out / (prefix + ".stderr")).write_bytes(p.stderr)
            rows.append(
                dict(
                    mode=mode,
                    selection=selection,
                    argv=argv,
                    exit=p.returncode,
                    binary_sha256=digest,
                    stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),
                )
            )
            (out / "checks.json").write_text(
                json.dumps(
                    dict(
                        source_commit=meta["source_commit"],
                        synthetic_unit_anchors=True,
                        recipe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        build_sha256=hashlib.sha256(
                            (build / "build.json").read_bytes()
                        ).hexdigest(),
                        observations=rows,
                    ),
                    indent=2,
                )
                + "\n"
            )
            assert p.returncode == 0, p.stdout.decode() + p.stderr.decode()
            print(prefix, p.stdout.decode().splitlines()[-2:], flush=True)


if __name__ == "__main__":
    main()
