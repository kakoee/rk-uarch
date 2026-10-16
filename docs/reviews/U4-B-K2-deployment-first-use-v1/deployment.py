"""Pure plan/byte/seal guards. No installation, container launch or authority creation."""

import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
SOURCE = "24fa36803081e5077d5977baa91441a2c8534ec8"
HOST_ROOT = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
HERE = Path(__file__).resolve().parent
MEMBERSHIP_HASH = "sha256:7fd2b4e89a9a29dd17f90a310cd8050cd6bec0165da683b153b8bacf456d1aa7"


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def require(ok, why):
    if not ok:
        raise ValueError(why)


def relative(name):
    require(
        isinstance(name, str)
        and not name.startswith("/")
        and "\\" not in name
        and all(x not in ("", ".", "..") for x in name.split("/")),
        "confined relative path required",
    )
    return Path(name)


def slots(plan):
    require(plan["source"] == SOURCE, "wrong source")
    require(plan["modes"] == ["debug", "release"], "exact modes")
    require(plan["repetitions"] == [0, 1, 2], "exact repetitions")
    cases = plan["case_membership"]
    require(
        digest(json.dumps(cases, sort_keys=True, separators=(",", ":")).encode())
        == MEMBERSHIP_HASH,
        "exact frozen case/job membership",
    )
    ids = [c["case_id"] for c in cases]
    require(len(ids) == 133 and ids == sorted(set(ids)), "exact ordered nonempty 133 cases")
    require(len({c["job_hash"] for c in cases}) == 133, "duplicate jobs")
    require(sum(c["outcome"] == "success" for c in cases) == 130, "success membership")
    require(sum(c["outcome"] == "TimeOverflow" for c in cases) == 3, "overflow membership")
    require(plan["total_calls"] == 798, "exact call count")
    return [(m, r, c) for m in plan["modes"] for r in plan["repetitions"] for c in cases]


def verify_bytes(root, files, *, sealed=False):
    """Verify exact declared files, root ownership, no writable inode or ancestor."""
    root = Path(root)
    if sealed:
        for p in (root, *root.parents):
            st = p.lstat()
            require(stat.S_ISDIR(st.st_mode) and st.st_uid == 0, "root-owned real ancestors")
            require(not st.st_mode & 0o022, "writable ancestor")
    for name, binding in files.items():
        path = root / relative(name)
        for parent in path.parents:
            if parent == root:
                break
            require(not parent.is_symlink(), "symlink directory")
            if sealed:
                st = parent.stat()
                require(st.st_uid == 0 and not st.st_mode & 0o222, "unsealed directory")
        st = path.lstat()
        require(stat.S_ISREG(st.st_mode), "regular bound file required")
        require(digest(path.read_bytes()) == binding["byte_hash"], "file digest mismatch")
        if sealed:
            require(st.st_uid == 0 and st.st_nlink == 1, "root-owned single-link file")
            require(not st.st_mode & 0o222, "writable bound file")
            require(stat.S_IMODE(st.st_mode) == int(binding["mode"], 8), "file mode mismatch")


def publication_blob(repo, commit, name, expected):
    require(bool(re.fullmatch("[0-9a-f]{40}", commit)), "full commit required")
    relative(name)
    env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
    kind = subprocess.check_output(["git", "cat-file", "-t", commit], cwd=repo, env=env)
    require(kind == b"commit\n", "actual immutable commit required")
    data = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=repo, env=env)
    require(digest(data) == expected, "published blob mismatch")
    return data


def verify_saved_campaign(root, plan, record):
    require(
        record.get("complete") is True and record.get("mapped_calls") == 798,
        "actual complete campaign required",
    )
    require(record.get("subject") == plan["subject"], "campaign subject drift")
    expected = slots(plan)
    rows = record.get("calls", [])
    require(len(rows) == len(expected), "missing/extra saved calls")
    baseline = {}
    for row, (mode, repetition, case) in zip(rows, expected, strict=True):
        require(
            (row["mode"], row["repetition"], row["case_id"]) == (mode, repetition, case["case_id"]),
            "saved call membership/order",
        )
        require(
            row["executable_hash"]
            == plan["subject"]["executable_byte_hashes"][plan["modes"].index(mode)],
            "saved executable drift",
        )
        require(row["request_hash"] == case["file"]["byte_hash"], "saved request drift")
        require(row["status"] == (0 if case["outcome"] == "success" else 2), "saved outcome drift")
        for field in ("request", "stdout", "stderr"):
            file = Path(root) / relative(row[field])
            require(file.is_file() and not file.is_symlink(), "saved regular blob")
            require(digest(file.read_bytes()) == row[field + "_hash"], "saved stream drift")
        key = (row["stdout_hash"], row["stderr_hash"], row["status"])
        require(baseline.setdefault(case["case_id"], key) == key, "saved replay drift")
        path = Path(root) / "calls" / f"{mode}-{repetition}-{case['case_id']}.json"
        require(json.loads(path.read_bytes()) == row, "saved individual receipt drift")


def docker_argv(action, output, selector=False):
    require(action in ("preflight", "campaign", "replay"), "explicit action")
    require(selector == (action != "preflight"), "authority mount/action mismatch")
    output = Path(output).resolve()
    require(output.is_relative_to(Path("/tmp")), "private output under /tmp required")
    require(not output.is_relative_to(HOST_ROOT), "outputs cannot alias authority")
    argv = [
        "/usr/bin/docker",
        "--host",
        "unix:///var/run/docker.sock",
        "run",
        "--rm",
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
        "/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
        "--workdir",
        "/tmp",
    ]
    for src, dst in [
        (HOST_ROOT / "candidate", "/candidate"),
        (HOST_ROOT / "python", "/python"),
        (HOST_ROOT / "site", "/site"),
        (HOST_ROOT / "campaign", "/campaign"),
        (HOST_ROOT / "manifests", "/manifests"),
    ]:
        argv += ["--mount", f"type=bind,src={src},dst={dst},readonly,bind-propagation=rprivate"]
    if selector:
        argv += [
            "--mount",
            "type=bind,src="
            + str(HOST_ROOT / "authority/k2-host-selector.json")
            + ",dst=/etc/rkuarch/k2-host-selector.json,readonly",
        ]
    argv += ["--mount", f"type=bind,src={output},dst=/receipts,bind-propagation=rprivate"]
    argv += [
        "--entrypoint",
        "/usr/bin/env",
        IMAGE,
        "-i",
        "PATH=/usr/bin:/bin",
        "LC_ALL=C",
        "/python/bin/python3.12",
        "-I",
        "-S",
        "-B",
        "/campaign/entrypoint.py",
        action,
    ]
    return argv


def main():
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["preflight", "campaign", "replay"])
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(docker_argv(a.action, a.output, a.action != "preflight"), indent=2))


if __name__ == "__main__":
    main()
