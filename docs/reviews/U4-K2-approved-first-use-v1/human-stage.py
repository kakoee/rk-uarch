"""Human-invoked placement wrapper for the exact approved B procedure, step 2.

Default is read-only verification. --place invokes only the approved sudo copy/seal.
Never run this Python interpreter as root; no authority or native execution occurs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

REPO = Path("/home/jjaff/AI-infra-simulation/rk-uarch")
PACKAGE_COMMIT = "f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f"
PACKAGE_REL = Path("docs/reviews/U4-B-K2-deployment-first-use-v1")
PACKAGE = Path("/tmp/u4-k2-approved-preparation") / PACKAGE_REL
PAYLOAD = Path("/tmp/u4-k2-approved-payload")
DEST = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
OWN_REL = Path("docs/reviews/U4-K2-approved-first-use-v1")


def require(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def unescape_mount(value):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)


def no_nested_mounts(root):
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        mount = Path(unescape_mount(line.split()[4]))
        require(not mount.is_relative_to(root), "mount at or below " + str(root))


def assert_regular(path, digest):
    st = path.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, "regular single-link file: " + str(path))
    require(sha(path.read_bytes()) == digest, "byte mismatch: " + str(path))


def verify(helper_commit, placed=False):
    require(
        os.getuid() == os.geteuid() == 1000, "invoke as the existing UID1000 user, not sudo Python"
    )
    if helper_commit:
        require(re.fullmatch("[0-9a-f]{40}", helper_commit), "full helper commit required")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", helper_commit, "origin/main"],
            cwd=REPO,
            check=True,
        )
        for name in ["human-stage.py", "acceptance.json"]:
            relative = OWN_REL / name
            frozen = subprocess.check_output(
                ["git", "show", f"{helper_commit}:{relative}"], cwd=REPO
            )
            require((REPO / relative).read_bytes() == frozen, "changed published helper/approval")
    approval = read(REPO / OWN_REL / "acceptance.json")
    require(
        approval["approval_text"] == "yes" and approval["preparation_commit"] == PACKAGE_COMMIT,
        "exact recorded approval required",
    )
    for relative, digest in approval["approved_files_sha256"].items():
        raw = subprocess.check_output(["git", "show", f"{PACKAGE_COMMIT}:{relative}"], cwd=REPO)
        require(sha(raw) == digest, "approved package hash")
        require(
            (Path("/tmp/u4-k2-approved-preparation") / relative).read_bytes() == raw,
            "private package differs from approved publication",
        )
    for ancestor in reversed(DEST.parents):
        if ancestor.exists() or ancestor.is_symlink():
            st = ancestor.lstat()
            require(
                stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022,
                "unsafe existing destination ancestor: " + str(ancestor),
            )
        else:
            require(
                ancestor in [Path("/var/lib/rkuarch"), Path("/var/lib/rkuarch/k2")],
                "unexpected missing ancestor",
            )
    require(placed or not os.path.lexists(DEST), "destination already exists; no overwrite")
    root = DEST if placed else PAYLOAD
    require(root.is_dir() and not root.is_symlink(), "real payload directory required")
    no_nested_mounts(root)
    no_nested_mounts(DEST)
    layout = read(PACKAGE / "candidate-layout.json")
    runtime = read(PACKAGE / "runtime.json")
    expected = set()
    regular_count = 0
    symlink_count = 0
    total_bytes = 0
    executable_names = {
        "python/bin/python3.12",
        "candidate/targets/debug/debug/uarch-engine",
        "candidate/targets/release/release/uarch-engine",
    }
    for name, binding in layout["files"].items():
        path = root / "candidate" / name
        assert_regular(path, binding["byte_hash"])
        expected.add("candidate/" + name)
    manifest_expected = (PACKAGE / "campaign-files.expected.json").read_bytes()
    require(
        (root / "manifests/campaign-files.json").read_bytes() == manifest_expected,
        "five-file campaign manifest",
    )
    expected.add("manifests/campaign-files.json")
    for name, binding in json.loads(manifest_expected).items():
        assert_regular(root / "campaign" / name, binding["sha256"])
        expected.add("campaign/" + name)
    for inventory_name, subtree in [("python-files.json", "python"), ("site-files.json", "site")]:
        inventory_path = root / "manifests" / inventory_name
        assert_regular(inventory_path, runtime["inventories"][inventory_name])
        expected.add("manifests/" + inventory_name)
        for name, binding in read(inventory_path).items():
            path = root / subtree / name
            expected.add(subtree + "/" + name)
            if "symlink" in binding:
                require(
                    path.is_symlink() and str(path.readlink()) == binding["symlink"],
                    "runtime symlink changed",
                )
                require(path.resolve().is_relative_to(root / subtree), "runtime symlink escape")
            else:
                assert_regular(path, binding["sha256"])
    actual = set()
    for path in [root, *root.rglob("*")]:
        st = path.lstat()
        relative = str(path.relative_to(root))
        if stat.S_ISLNK(st.st_mode):
            actual.add(relative)
            require(relative.startswith("python/"), "only frozen Python symlinks allowed")
            symlink_count += 1
        elif stat.S_ISREG(st.st_mode):
            actual.add(relative)
            regular_count += 1
            total_bytes += st.st_size
        else:
            require(stat.S_ISDIR(st.st_mode), "unexpected special file")
        require(st.st_uid == (0 if placed else 1000), "unexpected payload owner")
        if placed and not stat.S_ISLNK(st.st_mode):
            mode = 0o555 if stat.S_ISDIR(st.st_mode) or relative in executable_names else 0o444
            require(stat.S_IMODE(st.st_mode) == mode, "incorrect sealed mode: " + relative)
    require(actual == expected, "extra or missing payload members")
    for name in layout["reserved_authority_paths"]:
        require(not os.path.lexists(root / "candidate" / name), "authority must remain absent")
    return {
        "decision": "U4-K2-deployment-and-first-use-v1",
        "package_commit": PACKAGE_COMMIT,
        "root": str(root),
        "regular_files": regular_count,
        "symlinks": symlink_count,
        "bytes": total_bytes,
        "exact_payload_verified": True,
        "sealed": placed,
        "authority_installed": False,
        "runtime_executed": False,
    }


# Exact new-root copy/seal from the approved procedure, with repeated parent guards.
ROOT_STEP = r"""
root=/var/lib/rkuarch/k2/candidate-04-first-use-v1
payload=/tmp/u4-k2-approved-payload
test "$(id -u)" = 0
test ! -e "$root"
test ! -L "$root"
test -d "$payload"
test ! -L "$payload"
for parent in / /var /var/lib /var/lib/rkuarch /var/lib/rkuarch/k2; do
  if test -e "$parent" || test -L "$parent"; then
    test -d "$parent"
    test ! -L "$parent"
    test "$(stat -c %u -- "$parent")" = 0
    mode=$(stat -c %a -- "$parent")
    test "$((8#$mode & 0022))" = 0
  fi
done
mkdir -m 0755 -p /var/lib/rkuarch/k2
cp -a --no-preserve=ownership -- "$payload" "$root"
chown -hR root:root -- "$root"
find "$root" -type d -exec chmod 0555 {} +
find "$root" -type f -exec chmod 0444 {} +
chmod 0555 "$root/python/bin/python3.12" "$root/candidate/targets/debug/debug/uarch-engine" "$root/candidate/targets/release/release/uarch-engine"
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper-commit")
    parser.add_argument("--place", action="store_true")
    args = parser.parse_args()
    require(not args.place or args.helper_commit, "--place requires the published helper commit")
    result = verify(args.helper_commit)
    print(json.dumps({"preflight": "passed", **result}, indent=2), flush=True)
    if not args.place:
        return
    subprocess.run(["sudo", "/bin/bash", "-eu", "-c", ROOT_STEP], check=True)
    result = verify(args.helper_commit, placed=True)
    receipt = REPO / "tables/U4-K2-first-use-v1/human-placement.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("x") as stream:
        json.dump(
            {
                "status": "human root placement and seal verified",
                "helper_commit": args.helper_commit,
                **result,
            },
            stream,
            indent=2,
        )
        stream.write("\n")
    print(json.dumps({"status": "human root placement and seal verified", **result}, indent=2))
    print(
        "STOP: return this receipt. Existing approval covers the next runtime preflight; no authority or mapped job has run."
    )


if __name__ == "__main__":
    main()
