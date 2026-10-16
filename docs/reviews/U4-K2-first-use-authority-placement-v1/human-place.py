"""Human-only five-file authority placement. Default verifies without writing root."""

import argparse
import base64
import hashlib
import json
import os
import re
import runpy
import shlex
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/jjaff/AI-infra-simulation/rk-uarch")
OWN = Path("docs/reviews/U4-K2-first-use-authority-placement-v1")
ROOT = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
BASE_COMMIT = "ffc1a9884b6080692c8a93b4ec6c165ea038fe45"
BASE_REL = Path("docs/reviews/U4-K2-approved-first-use-v1/human-stage.py")
PREFIX = "candidate/docs/reviews/U4-K2-first-use-authorization-v1/"
TARGETS = {
    "human-decision.json": PREFIX + "human-decision.json",
    "HostRecord.json": PREFIX + "HostRecord.json",
    "preflight.json": "manifests/preflight.json",
    "k2-host-selector.json": "authority/k2-host-selector.json",
    "runtime-release.json": "manifests/runtime-release.json",
}
NEW_DIRS = {PREFIX.rstrip("/"), "authority"}


def require(ok, why):
    if not ok:
        raise SystemExit("STOP: " + why)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def snapshot(root):
    result = {}
    for p in [root, *root.rglob("*")]:
        s = p.lstat()
        identity = [s.st_mode, s.st_uid, s.st_gid, s.st_ino]
        if stat.S_ISREG(s.st_mode):
            identity += [s.st_nlink, s.st_mtime_ns, sha(p.read_bytes())]
        elif stat.S_ISLNK(s.st_mode):
            identity += [s.st_mtime_ns, str(p.readlink())]
        else:
            require(stat.S_ISDIR(s.st_mode), "unexpected special file")
        result[str(p.relative_to(root))] = identity
    return result


def verify(helper_commit=None):
    require(os.getuid() == os.geteuid() == 1000, "run as UID1000, not sudo Python")
    if helper_commit:
        require(re.fullmatch("[0-9a-f]{40}", helper_commit), "full helper commit required")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", helper_commit, "origin/main"],
            cwd=REPO,
            check=True,
        )
        names = (
            git("ls-tree", "-r", "--name-only", helper_commit, "--", str(OWN)).decode().splitlines()
        )
        actual = {str(p.relative_to(REPO)) for p in (REPO / OWN).rglob("*") if p.is_file()}
        require(set(names) == actual, "exact published helper package membership")
        for name in names:
            path = REPO / name
            require(
                not path.is_symlink()
                and path.read_bytes() == git("show", helper_commit + ":" + name),
                "changed helper package: " + name,
            )
    base_raw = git("show", BASE_COMMIT + ":" + str(BASE_REL))
    require((REPO / BASE_REL).read_bytes() == base_raw, "changed base placement verifier")
    base = runpy.run_path(str(REPO / BASE_REL))
    base["verify"](BASE_COMMIT, placed=True)
    receipt = json.loads((REPO / OWN / "placement.json").read_bytes())
    require({n: v["target"] for n, v in receipt["files"].items()} == TARGETS, "exact five targets")
    sys.path.insert(0, str(base["PACKAGE"]))
    from verify_publication import verify as verify_publication

    objects = verify_publication(
        REPO,
        receipt["package_commit"],
        receipt["acceptance_commit"],
        receipt["published_blob_hashes"],
    )
    payload = {}
    for name, target in TARGETS.items():
        raw = (REPO / OWN / "payload" / name).read_bytes()
        require(sha(raw) == receipt["files"][name]["sha256"], "placement digest mismatch")
        if name in ("human-decision.json", "HostRecord.json", "preflight.json"):
            source = "docs/reviews/U4-K2-first-use-authorization-v1/" + name
            require(
                raw == git("show", receipt["acceptance_commit"] + ":" + source),
                "published bytes mismatch",
            )
        else:
            key = "selector" if name == "k2-host-selector.json" else "runtime_release"
            require(json.loads(raw) == objects[key], "downstream authority mismatch")
        require(not os.path.lexists(ROOT / target), "no overwrite: " + target)
        payload[target] = raw
    for name in NEW_DIRS:
        require(not os.path.lexists(ROOT / name), "new authority directory already exists")
    return receipt, payload


def root_script(payload):
    # Only fixed target paths and verified literal bytes; never execute user-owned files as root.
    require(set(payload) == set(TARGETS.values()), "exact root-write set")
    q = shlex.quote
    lines = ["set -euo pipefail", "set -o noclobber", "umask 077", 'test "$(id -u)" = 0']
    parents = set()
    for name in TARGETS.values():
        for parent in (ROOT / name).parents:
            if str(parent) not in {str(ROOT / d) for d in NEW_DIRS}:
                parents.add(parent)
    for parent in sorted(parents, key=str):
        path = q(str(parent))
        lines += [
            f"test -d {path}",
            f"test ! -L {path}",
            f'test "$(stat -c %u -- {path})" = 0',
            f"mode=$(stat -c %a -- {path})",
            'test "$((8#$mode & 0022))" = 0',
        ]
    for name in sorted(set(TARGETS.values()) | NEW_DIRS):
        path = q(str(ROOT / name))
        lines += [f"test ! -e {path}", f"test ! -L {path}"]
    for name in sorted(NEW_DIRS):
        lines.append(f"mkdir -m 0555 -- {q(str(ROOT / name))}")
    for name, raw in payload.items():
        path = q(str(ROOT / name))
        encoded = q(base64.b64encode(raw).decode())
        lines += [
            f"printf '%s' {encoded} | /usr/bin/base64 -d > {path}",
            f"chown root:root -- {path}",
            f"chmod 0444 -- {path}",
            f'test "$(sha256sum -- {path} | cut -d " " -f 1)" = {sha(raw)[7:]}',
        ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit")
    parser.add_argument("--place", action="store_true")
    args = parser.parse_args()
    require(not args.place or args.helper_commit, "--place requires published helper commit")
    receipt, payload = verify(args.helper_commit)
    script = root_script(payload)
    subprocess.run(["/bin/bash", "-n"], input=script.encode(), check=True)
    print(
        json.dumps(
            {
                "preflight": "passed",
                "files": 5,
                "authority_installed": False,
                "acceptance_commit": receipt["acceptance_commit"],
            }
        ),
        flush=True,
    )
    if not args.place:
        return
    output = REPO / "tables/U4-K2-first-use-v1/human-authority-placement.json"
    require(not os.path.lexists(output), "existing authority receipt; no overwrite")
    before = snapshot(ROOT)
    subprocess.run(["sudo", "/bin/bash", "-eu", "-c", script], check=True)
    after = snapshot(ROOT)
    require(set(after) == set(before) | set(payload) | NEW_DIRS, "unexpected membership change")
    require(
        all(after[name] == value for name, value in before.items()), "existing deployment changed"
    )
    for name, raw in payload.items():
        path = ROOT / name
        s = path.lstat()
        require(
            stat.S_ISREG(s.st_mode)
            and stat.S_IMODE(s.st_mode) == 0o444
            and s.st_uid == s.st_gid == 0
            and s.st_nlink == 1
            and path.read_bytes() == raw,
            "authority placement/seal mismatch",
        )
    for name in NEW_DIRS:
        s = (ROOT / name).lstat()
        require(
            stat.S_ISDIR(s.st_mode)
            and stat.S_IMODE(s.st_mode) == 0o555
            and s.st_uid == s.st_gid == 0,
            "authority directory seal mismatch",
        )
    result = {
        "decision": receipt["decision"],
        "status": "human authority placement verified",
        "helper_commit": args.helper_commit,
        "acceptance_commit": receipt["acceptance_commit"],
        "files": receipt["files"],
        "existing_payload_preserved": True,
        "authority_installed": True,
        "mapped_jobs_executed": 0,
    }
    with output.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("STOP: return this receipt. Existing approval covers the 798-call campaign and replay.")


if __name__ == "__main__":
    main()
