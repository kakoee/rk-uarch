"""Human-only input staging; check-only never prepares inputs or invokes an oracle."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COORDINATOR = HERE.parents[2]
SPEC = json.loads((HERE / "source.json").read_text())
SOURCE = Path(SPEC["source_root"])
OUTPUT = Path(SPEC["output_root"])


def require(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    require(result.returncode == 0, result.stderr.decode().strip() or "Git check failed")
    return result.stdout


def text(root, *args):
    return git(root, *args).decode().strip()


def safe(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink: " + str(path))


def output_guard():
    safe(OUTPUT)
    require(
        OUTPUT == COORDINATOR / "tables/U4-M-policy-input-freeze-recovery-v1",
        "unexpected recovery output location",
    )
    require(not OUTPUT.is_relative_to(SOURCE), "output must remain outside frozen source")
    require(text(COORDINATOR, "check-ignore", str(OUTPUT / "probe")), "output must be ignored")


def create_output():
    output_guard()
    require(not OUTPUT.exists(), "output already exists; preserve and audit before any retry")
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.mkdir()


def source_guard():
    safe(SOURCE)
    require(text(SOURCE, "branch", "--show-current") == "main", "source branch drift")
    require(text(SOURCE, "rev-parse", "HEAD") == SPEC["source_commit"], "source HEAD drift")
    require(text(SOURCE, "rev-parse", "HEAD^{tree}") == SPEC["source_tree"], "source tree drift")
    require(not text(SOURCE, "status", "--porcelain", "--untracked-files=all"), "source dirty")
    require(
        all(
            row.startswith(b"H ") for row in git(SOURCE, "ls-files", "-v", "-z").split(b"\0") if row
        ),
        "hidden index flags",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        require(
            not Path(
                text(SOURCE, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished source Git operation",
        )
    for name, digest in SPEC["inventory"].items():
        path = SOURCE / name
        safe(path)
        require(sha(path.read_bytes()) == digest, "support drift: " + name)
    require(sha((SOURCE / "uv.lock").read_bytes()) == SPEC["lock_sha256"], "lock drift")
    artifact = SOURCE / "contract/vendor" / ("rk-sim@" + SPEC["upstream_pin"])
    require(
        sha((artifact / "MANIFEST.json").read_bytes()) == SPEC["current_artifact_manifest_sha256"],
        "adopted manifest drift",
    )
    output_guard()


def snapshot():
    # In-memory preservation assertion only; never publish a source-wide manifest.
    return {
        name: (sha((SOURCE / name).read_bytes()), (SOURCE / name).stat().st_mtime_ns)
        for name in git(SOURCE, "ls-files", "-z").decode().split("\0")
        if name
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-commit", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--stage", action="store_true")
    parser.add_argument("--authorization-commit")
    args = parser.parse_args()
    require(args.check_only or os.environ.get("UARCH_HUMAN") == "1", "human approval/flag required")
    require(sys.flags.isolated and sys.dont_write_bytecode, "use reviewed Python -I -B")
    require(sys.prefix == SPEC["source_prefix"], "wrong staging environment")
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "PARAMS",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(key), key + " must be unset")
    require(
        len(args.package_commit) == 40
        and all(c in "0123456789abcdef" for c in args.package_commit),
        "full package commit required",
    )
    git(COORDINATOR, "merge-base", "--is-ancestor", args.package_commit, "HEAD")
    relative = HERE.relative_to(COORDINATOR).as_posix()
    for name in ("human-stage.py", "source.json", "README.md"):
        path = relative + "/" + name
        safe(COORDINATOR / path)
        require(
            (HERE / name).read_bytes()
            == git(COORDINATOR, "show", args.package_commit + ":" + path),
            "package drift: " + name,
        )
    prior = SPEC["prior_authorization"]
    git(COORDINATOR, "merge-base", "--is-ancestor", prior["commit"], "HEAD")
    record = json.loads(git(COORDINATOR, "show", prior["commit"] + ":" + prior["path"]))
    require(record == prior["record"], "prior authorization drift")
    require(
        record["approved"] is True
        and record["authorizer"] == "Javid"
        and record["action"] == "prepare-inputs-only",
        "staging scope mismatch",
    )
    old_path = "docs/reviews/U4-M-policy-input-staging-v1/source.json"
    old_bytes = git(COORDINATOR, "show", record["package_commit"] + ":" + old_path)
    require(sha(old_bytes) == record["source_spec_sha256"], "approved old source spec mismatch")
    old_spec = json.loads(old_bytes)
    require(
        record["source_commit"] == old_spec["source_commit"] == SPEC["source_commit"],
        "approved source changed",
    )
    require(record["output_root"] == old_spec["output_root"], "old output binding mismatch")
    require(
        {k: v for k, v in SPEC.items() if k not in {"output_root", "prior_authorization"}}
        == {k: v for k, v in old_spec.items() if k != "output_root"},
        "recovery changes more than output placement",
    )
    if args.stage:
        require(args.authorization_commit == prior["commit"], "use the existing staging approval")
    environment = {
        "implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in SPEC["staging_environment"]["packages"]
        },
    }
    require(environment == SPEC["staging_environment"], "staging environment drift")
    source_guard()
    require(not OUTPUT.exists(), "output already exists; preserve and audit before any retry")
    sys.path[:0] = [str(SOURCE), str(SOURCE / "src"), str(SOURCE / "contract")]
    from scripts import u2_inputs, u2_support, vendor_rk

    require(u2_inputs.ROOT == u2_support.ROOT == vendor_rk.ROOT == SOURCE, "wrong imported source")
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"scripts", "rkuarch", "uarch_contract"}:
            origin = getattr(module, "__file__", None)
            require(
                origin is not None and Path(origin).resolve().is_relative_to(SOURCE),
                "module origin: " + name,
            )
    require(u2_support.POLICY == SPEC["policy"], "policy drift")
    require(u2_support.inventory() == SPEC["inventory"], "inventory drift")
    require(vendor_rk.PIN == SPEC["upstream_pin"], "upstream pin drift")
    require(
        sha(Path(vendor_rk.__file__).read_bytes()) == SPEC["generator_sha256"], "generator drift"
    )
    require(
        sha(vendor_rk.ORACLE_PROGRAM.encode()) == SPEC["oracle_program_sha256"],
        "oracle program drift",
    )
    vendor_rk.check_contract_pin(SOURCE)
    source_guard()
    print(
        json.dumps(
            {
                "preflight": "passed",
                "source_commit": SPEC["source_commit"],
                "support_entries": len(SPEC["inventory"]),
                "staging_executed": False,
            }
        ),
        flush=True,
    )
    if args.check_only:
        return
    before = snapshot()
    create_output()
    inputs = OUTPUT / "inputs"
    identity = u2_inputs.prepare_inputs(inputs)  # Pure export/copy only, never oracle execution.
    verified = u2_inputs.load_inputs(inputs, identity)
    require(verified.manifest_sha256 == identity, "staged manifest identity mismatch")
    require(
        json.loads((inputs / "support-files.json").read_text()) == SPEC["inventory"],
        "staged support drift",
    )
    require(
        json.loads((inputs / "support-policy.json").read_text()) == SPEC["policy"],
        "staged policy drift",
    )
    source_guard()
    require(
        snapshot() == before, "source bytes or modification times changed; preserve output and stop"
    )
    receipt = {
        "decision": "U4-M-policy-input-staging-v1",
        "recovery": "U4-M-policy-staging-recovery-v1",
        "status": "staged and strictly verified; freeze acceptance pending",
        "source_commit": SPEC["source_commit"],
        "source_tree": SPEC["source_tree"],
        "package_commit": args.package_commit,
        "authorization_commit": args.authorization_commit,
        "inputs": str(inputs),
        "input_manifest_sha256": identity,
        "policy": SPEC["policy"],
        "support_entries": len(SPEC["inventory"]),
        "staging_environment": environment,
        "platform": platform.platform(),
        "matrix": verified.matrix,
        "tracked_source_preserved": True,
        "generation_adoption_commit_push": False,
    }
    with (OUTPUT / "receipt.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print(
        "STOP: return this receipt for exact freeze review. "
        "No oracle generation or adoption occurred."
    )


if __name__ == "__main__":
    main()
