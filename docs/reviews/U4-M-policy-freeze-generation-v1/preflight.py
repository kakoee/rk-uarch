"""Read-only frozen-input/environment checks; no producer, oracle or adoption calls."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COORDINATOR = HERE.parents[2]
SPEC = json.loads((HERE / "freeze.json").read_text())
SOURCE = Path(SPEC["source_root"])
INPUTS = Path(SPEC["inputs"])
OUTPUT = Path(SPEC["generation_output"])
UPSTREAM = Path(SPEC["upstream_root"])


def require(ok, message):
    if not ok:
        raise SystemExit("STOP: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    require(OUTPUT == COORDINATOR / "tables/U4-M-policy-generation-v1", "unexpected output")
    require(
        not OUTPUT.is_relative_to(SOURCE)
        and not OUTPUT.is_relative_to(UPSTREAM)
        and not OUTPUT.is_relative_to(INPUTS),
        "output must be outside read-only inputs/source",
    )
    require(text(COORDINATOR, "check-ignore", str(OUTPUT / "probe")), "output must be ignored")


def source_guard():
    safe(SOURCE)
    require(text(SOURCE, "branch", "--show-current") == "main", "source branch drift")
    require(text(SOURCE, "rev-parse", "HEAD") == SPEC["source_commit"], "source commit drift")
    require(text(SOURCE, "rev-parse", "HEAD^{tree}") == SPEC["source_tree"], "source tree drift")
    require(not text(SOURCE, "status", "--porcelain", "--untracked-files=all"), "source dirty")
    require(
        all(
            row.startswith(b"H ") for row in git(SOURCE, "ls-files", "-v", "-z").split(b"\0") if row
        ),
        "source index flags may hide changes",
    )
    for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        require(
            not Path(
                text(SOURCE, "rev-parse", "--path-format=absolute", "--git-path", name)
            ).exists(),
            "unfinished source Git operation",
        )


def check_package(pin):
    require(
        len(pin) == 40 and all(c in "0123456789abcdef" for c in pin), "full package pin required"
    )
    git(COORDINATOR, "merge-base", "--is-ancestor", pin, "HEAD")
    relative = HERE.relative_to(COORDINATOR).as_posix()
    for name in (
        "freeze.json",
        "input-SHA256SUMS",
        "human-staging-receipt.json",
        "preflight.py",
        "human_generate.py",
        "next-decision.md",
    ):
        safe(HERE / name)
        require(
            (HERE / name).read_bytes()
            == git(COORDINATOR, "show", pin + ":" + relative + "/" + name),
            "package drift: " + name,
        )


def load_source():
    sys.path[:0] = [str(SOURCE), str(SOURCE / "src"), str(SOURCE / "contract")]
    from scripts import u2_inputs, u2_support, vendor_rk

    require(u2_inputs.ROOT == u2_support.ROOT == vendor_rk.ROOT == SOURCE, "wrong source imported")
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"scripts", "rkuarch", "uarch_contract"}:
            origin = getattr(module, "__file__", None)
            require(
                origin is not None and Path(origin).resolve().is_relative_to(SOURCE),
                "origin: " + name,
            )
    return u2_inputs, u2_support, vendor_rk


def preflight(pin, *, during=False):
    require(sys.flags.isolated and sys.dont_write_bytecode, "use reviewed Python -I -B")
    require(sys.prefix == SPEC["source_prefix"], "wrong source interpreter")
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "PARAMS",
        "SHA",
        "RK",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(key), key + " must be unset")
    require(
        not os.environ.get("UV_PROJECT_ENVIRONMENT")
        or os.environ["UV_PROJECT_ENVIRONMENT"] == SPEC["oracle_environment"],
        "oracle override",
    )
    check_package(pin)
    source_guard()
    output_guard()
    require(
        OUTPUT.is_dir() if during else not OUTPUT.exists(),
        "unexpected output state; never overwrite/resume",
    )
    safe(INPUTS)
    require(not INPUTS.is_relative_to(SOURCE), "inputs must be outside source")
    require(digest(INPUTS / "SHA256SUMS") == SPEC["input_manifest_sha256"], "input manifest drift")
    require(
        (INPUTS / "SHA256SUMS").read_bytes() == (HERE / "input-SHA256SUMS").read_bytes(),
        "input bytes drift",
    )
    require(
        digest(INPUTS.parent / "receipt.json") == SPEC["input_receipt_sha256"],
        "human receipt drift",
    )
    u, p, v = load_source()
    checked = u.load_inputs(INPUTS, SPEC["input_manifest_sha256"])
    require(
        p.POLICY == SPEC["policy"] and p.inventory() == SPEC["inventory"], "policy/support drift"
    )
    require(v.PIN == SPEC["upstream_pin"], "upstream pin drift")
    require(digest(Path(v.__file__)) == SPEC["generator_sha256"], "generator drift")
    require(
        hashlib.sha256(v.ORACLE_PROGRAM.encode()).hexdigest() == SPEC["oracle_program_sha256"],
        "oracle drift",
    )
    v.check_contract_pin(SOURCE)
    require(digest(SOURCE / "uv.lock") == SPEC["lock_sha256"], "source lock drift")
    require(
        digest(u.ADOPTED / "MANIFEST.json") == SPEC["current_artifact_manifest_sha256"],
        "adopted pair drift",
    )
    v.check_manifest(
        u.ADOPTED
    )  # Historical integrity only; old currentness is intentionally stale.
    safe(UPSTREAM)
    safe(Path(SPEC["oracle_environment"]))
    require(
        not Path(SPEC["oracle_environment"]).resolve().is_relative_to(UPSTREAM),
        "oracle env inside upstream",
    )
    v.check_clone(UPSTREAM, v.PIN)
    env = {k: val for k, val in os.environ.items() if k != "UARCH_HUMAN"}
    env.update(
        UV_PROJECT_ENVIRONMENT=SPEC["oracle_environment"],
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
    )
    v.verify_oracle_environment(UPSTREAM, env)  # Locked offline check, never install/sync changes.

    def metadata(python, lock):
        data = json.loads(
            subprocess.check_output(
                [str(python), "-I", "-B", "-c", v.ENVIRONMENT_PROGRAM],
                cwd="/tmp",
                env=env,
                text=True,
            )
        )
        data["uv_lock_sha256"] = digest(lock)
        return data

    oracle = metadata(Path(SPEC["oracle_environment"]) / "bin/python", UPSTREAM / "uv.lock")
    v.validate_environment_metadata(oracle, (UPSTREAM / "uv.lock").read_bytes())
    require(oracle == SPEC["oracle_metadata"], "oracle environment changed")
    require(
        metadata(SPEC["source_python"], SOURCE / "uv.lock") == SPEC["source_metadata"],
        "source environment changed",
    )
    require(
        subprocess.check_output(["uv", "--version"], text=True).strip() == SPEC["uv_version"],
        "uv changed",
    )
    source_guard()
    v.check_clone(UPSTREAM, v.PIN)
    return {
        "status": "passed; no oracle executed",
        "source_commit": SPEC["source_commit"],
        "source_tree": SPEC["source_tree"],
        "input_manifest_sha256": checked.manifest_sha256,
        "support_entries": len(SPEC["inventory"]),
        "oracle_environment": oracle,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(preflight(args.package_commit), indent=2, sort_keys=True))
