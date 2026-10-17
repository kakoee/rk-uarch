"""Fresh remote-observed object context; never trust a caller's tracking refs/config."""

import contextlib
import datetime
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REPOSITORY = "kakoee/rk-uarch"
REMOTE = "https://github.com/kakoee/rk-uarch.git"
ACTIVE: "RemoteView | None" = None


def environment(home: Path) -> dict[str, str]:
    # No inherited GIT_*, HOME/XDG, proxy, credential, SSH or config environment.
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
    }


class RemoteView:
    def __init__(self, endpoint: str = REMOTE, *, simulated: bool = False):
        if endpoint != REMOTE and not simulated:
            raise ValueError("exact expected repository/remote required")
        self.endpoint, self.simulated = endpoint, simulated
        self.temp: Any = None
        self.reads: dict[tuple[str, str], str] = {}
        self.main = ""

    @classmethod
    def fixture(cls, root: Path) -> "RemoteView":
        return cls(str(root.resolve()), simulated=True)

    def git(self, *args: str) -> bytes:
        argv = [
            "/usr/bin/git",
            "--no-replace-objects",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "http.followRedirects=false",
            "-c",
            "http.sslVerify=true",
            "-c",
            "protocol.allow=never",
            "-c",
            "protocol.https.allow=always",
        ]
        if self.simulated:
            argv += ["-c", "protocol.file.allow=always"]
        try:
            return subprocess.run(
                argv + list(args),
                cwd=self.root,
                env=self.env,
                check=True,
                capture_output=True,
                timeout=120,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            # Never log stderr: endpoints/credential helpers can disclose secrets.
            raise ValueError("verified remote Git operation failed; no offline fallback") from error

    def __enter__(self) -> "RemoteView":
        self.temp = tempfile.TemporaryDirectory(prefix="u4-remote-objects-")
        self.root = Path(self.temp.name)
        self.env = environment(self.root / "empty-home")
        try:
            self.git("init", "--bare", ".")
            observed = (
                self.git("ls-remote", "--exit-code", self.endpoint, "refs/heads/main")
                .decode()
                .splitlines()
            )
            if len(observed) != 1 or not re.fullmatch(
                r"[0-9a-f]{40}\trefs/heads/main", observed[0]
            ):
                raise ValueError("one actual remote main required")
            self.main = observed[0].split()[0]
            self.git(
                "fetch",
                "--no-tags",
                "--no-recurse-submodules",
                self.endpoint,
                "refs/heads/main:refs/heads/observed-main",
            )
            fetched = self.git("rev-parse", "refs/heads/observed-main").decode().strip()
            if fetched != self.main:
                raise ValueError("remote advanced during verification; stop and re-observe")
            self.observed_utc = datetime.datetime.now(datetime.UTC).isoformat()
            return self
        except BaseException:
            self.temp.cleanup()
            raise

    def __exit__(self, *args: Any) -> None:
        self.temp.cleanup()

    def read(self, commit: str, path: str) -> bytes:
        if (
            not re.fullmatch("[0-9a-f]{40}", commit)
            or not path
            or path.startswith("/")
            or any(p in ("", ".", "..") for p in path.split("/"))
        ):
            raise ValueError("exact immutable commit and confined blob path required")
        self.git("merge-base", "--is-ancestor", commit, self.main)
        if self.git("cat-file", "-t", commit).strip() != b"commit":
            raise ValueError("commit object required")
        raw = self.git("show", commit + ":" + path)
        import hashlib

        self.reads[commit, path] = "sha256:" + hashlib.sha256(raw).hexdigest()
        return raw

    def receipt(self) -> dict[str, Any]:
        return {
            "format": "uarch-remote-publication-observation/1",
            "repository": REPOSITORY,
            "remote": self.endpoint,
            "observed_main": self.main,
            "observed_utc": self.observed_utc,
            "simulated_remote": self.simulated,
            "fresh_private_object_database": True,
            "replacement_objects_disabled": True,
            "inherited_git_config_used": False,
            "reads": [
                {"commit": c, "path": p, "sha256": h} for (c, p), h in sorted(self.reads.items())
            ],
            "limit": (
                "Remote publication is not human consent; TLS/DNS and authentic "
                "human records remain trust premises."
            ),
        }


@contextlib.contextmanager
def observe():
    global ACTIVE
    if ACTIVE is not None:
        raise ValueError("nested publication observation")
    with RemoteView() as view:
        ACTIVE = view
        try:
            yield view
        finally:
            ACTIVE = None


def published(commit: str, path: str) -> bytes:
    if ACTIVE is None or ACTIVE.simulated:
        raise ValueError("actual remote observation required; no local/offline fallback")
    return ACTIVE.read(commit, path)
