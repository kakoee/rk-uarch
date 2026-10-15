"""Private pull shell controls use a fake Docker; they do not establish registry access."""

import json
import os
import subprocess
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent
IMAGE = "ghcr.io/kakoee/rk-uarch-k1-builder@sha256:" + "a" * 64


@pytest.mark.parametrize("failure", ["none", "login", "pull"])
def test_credentials_cleaned_before_native_work(tmp_path, failure):
    docker = tmp_path / "docker"
    docker.write_text(r"""#!/usr/bin/env python3
import json, os, pathlib, sys
config = pathlib.Path(sys.argv[2])
assert sys.argv[1] == '--config' and config.is_dir()
command = sys.argv[3]
if command == 'login':
    assert not list(config.iterdir())
    assert sys.stdin.read() == 'synthetic-secret'
    (config / 'config.json').write_text('synthetic authentication state')
else:
    assert command == 'pull' and (config / 'config.json').is_file()
    assert 'K1_GHCR_READ_TOKEN' not in os.environ
with open(os.environ['CALLS'], 'a') as stream:
    stream.write(json.dumps({'command': command, 'config': str(config)}) + '\n')
sys.exit(7 if os.environ['FAILURE'] == command else 0)
""")
    docker.chmod(0o755)
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    calls = tmp_path / "calls.jsonl"
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"])
    env.update(
        K1_GHCR_USER="synthetic-user",
        K1_GHCR_READ_TOKEN="synthetic-secret",
        RUNNER_TEMP=str(tmp_path),
        GITHUB_EVENT_NAME="push",
        GITHUB_REF="refs/heads/main",
        CALLS=str(calls),
        FAILURE=failure,
    )
    result = subprocess.run(
        ["bash", "-x", str(PACKAGE / "private-pull.sh"), IMAGE, str(receipts)],
        env=env,
        capture_output=True,
        check=False,
    )
    assert result.returncode == (0 if failure == "none" else 7)
    observed = [json.loads(line) for line in calls.read_text().splitlines()]
    assert [entry["command"] for entry in observed] == (
        ["login"] if failure == "login" else ["login", "pull"]
    )
    assert all(not Path(entry["config"]).exists() for entry in observed)
    assert not list(tmp_path.glob("k1-ghcr.*"))
    logs = b"".join(path.read_bytes() for path in receipts.iterdir())
    assert b"synthetic-secret" not in result.stdout + result.stderr + logs


@pytest.mark.parametrize(
    "event,ref,image",
    [
        ("pull_request", "refs/pull/1/merge", IMAGE),
        ("pull_request_target", "refs/heads/main", IMAGE),
        ("push", "refs/heads/other", IMAGE),
        ("push", "refs/tags/main", IMAGE),
        ("push", "refs/heads/main", "ghcr.io/kakoee/rk-uarch-k1-builder:latest"),
        ("push", "refs/heads/main", "public.example/builder@sha256:" + "a" * 64),
    ],
)
def test_wrong_ref_or_destination_refuses_before_login(tmp_path, event, ref, image):
    env = dict(
        os.environ,
        K1_GHCR_USER="synthetic-user",
        K1_GHCR_READ_TOKEN="synthetic-secret",
        RUNNER_TEMP=str(tmp_path),
        GITHUB_EVENT_NAME=event,
        GITHUB_REF=ref,
    )
    result = subprocess.run(
        ["bash", str(PACKAGE / "private-pull.sh"), image, str(tmp_path)],
        env=env,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert not list(tmp_path.iterdir())


def registry_helper():
    import runpy

    return runpy.run_path(str(PACKAGE / "owner-registry.py"))


def test_owner_identity_and_minimal_separate_credentials():
    helper = registry_helper()
    helper["identity"]({"login": "kakoee"}, "write:packages, read:packages", "publish")
    helper["identity"]({"login": "kakoee"}, "read:packages", "check-reader")
    for user, scopes, mode in [
        ("jjaffari", "write:packages", "publish"),
        ("kakoee", "repo, write:packages", "publish"),
        ("kakoee", "read:packages", "publish"),
        ("kakoee", "write:packages, read:packages", "check-reader"),
        ("kakoee", "delete:packages, read:packages", "check-reader"),
    ]:
        with pytest.raises(ValueError):
            helper["identity"]({"login": user}, scopes, mode)


def test_public_package_and_existing_conflicting_tag_refuse():
    helper = registry_helper()
    package = {"name": "rk-uarch-k1-builder", "package_type": "container", "visibility": "private"}
    helper["private"](package)
    package["visibility"] = "public"
    with pytest.raises(ValueError, match="non-private"):
        helper["private"](package)
    version = {"name": helper["IMAGE_ID"], "metadata": {"container": {"tags": ["k1-892b9ee"]}}}
    helper["tag_conflicts"]([version])
    version["name"] = "sha256:" + "f" * 64
    with pytest.raises(ValueError, match="do not overwrite"):
        helper["tag_conflicts"]([version])
    with pytest.raises(ValueError, match="identity differs"):
        helper["image"]([{"Id": version["name"], "Os": "linux", "Architecture": "amd64"}])
