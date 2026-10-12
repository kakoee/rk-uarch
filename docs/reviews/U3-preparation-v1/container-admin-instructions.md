# Proposed rootless Podman setup on the designated U3 host

Python3.12.14, uv and Rust are available in Javid's user-local directories. Podman and
newuidmap/newgidmap are absent on the expanded PATH. Existing Javid subuid/subgid entries
are each `165536:65536`; do not replace or duplicate them. Namespace checks will verify
that the installed tools can use them. This is preparation for the runbook's recommended
rootless runtime; final U0005 records the runtime/version/image and accepted G2 criteria.

The server administrator runs on `152.53.209.203`:

```bash
sudo apt-get update
sudo apt-get install -y podman uidmap slirp4netns fuse-overlayfs
```

Use Debian12's packages. This installs software system-wide; it does not grant Javid sudo
or Docker-group privileges. The latter two packages supply rootless networking/storage
helpers. No account-ID modifications or system upgrade command is proposed. Sources:
[Debian Podman package](https://packages.debian.org/bookworm/podman),
[Podman installation](https://podman.io/docs/installation),
[rootless configuration](https://docs.podman.io/en/latest/markdown/podman.1.html#rootless-mode).

After installation, Javid runs from the laptop:

```bash
ssh javid@152.53.209.203 'bash -s' < /home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/U3-preparation-v1/host-podman-check.sh
```

This may initialize Javid's Podman storage. It checks rootless information and actual UID/GID
namespace mappings without downloading images or running a simulator. It is not G2(a) or a
benchmark. Return its output before claiming container readiness. If it fails, preserve the
error; do not switch to privileged mode or weaken checks.

Runner registration can be prepared in parallel using `host-next-steps.md`, but registration
and persistent service changes remain human tasks. Keep the nightly schedule paused until
the correctly labelled runner is online and the agreed setup can execute there.
