"""Source-read-only freeze preflight; temporary pure inputs, never oracle execution.

Use A's existing interpreter with -I -B. This file may live in B or primary.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "proposal.json").read_bytes())
A = Path(SPEC["source_root"])
OUTPUT = Path(SPEC["output_root"])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    ).strip()


def safe(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), f"symlink: {path}")


def check_proposal(commit):
    require(
        len(commit) == 40 and all(c in "0123456789abcdef" for c in commit),
        "full reviewed proposal commit required",
    )
    repository = Path(git(HERE, "rev-parse", "--show-toplevel"))
    relative = HERE.relative_to(repository).as_posix()
    names = git(repository, "ls-tree", "-r", "--name-only", commit, "--", relative).splitlines()
    actual = {p.relative_to(repository).as_posix() for p in HERE.rglob("*") if p.is_file()}
    require(actual == set(names) and names, "proposal file inventory drift")
    for name in names:
        path = repository / name
        safe(path)
        committed = subprocess.check_output(
            ["git", "-C", str(repository), "show", commit + ":" + name]
        )
        require(path.read_bytes() == committed, "proposal bytes drift: " + name)


def source_guard():
    safe(A)
    require((A / ".git").is_dir() and not (A / ".git").is_symlink(), "independent clone required")
    require(git(A, "branch", "--show-current") == "main", "A must remain on main")
    require(git(A, "rev-parse", "HEAD") == SPEC["source_commit"], "reviewed source HEAD drift")
    require(git(A, "rev-parse", "HEAD^{tree}") == SPEC["source_tree"], "reviewed source tree drift")
    require(
        not git(A, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"),
        "A tracked/index/untracked state changed",
    )
    require(
        all(
            not line or line.startswith("H ") for line in git(A, "ls-files", "-v", "-z").split("\0")
        ),
        "hidden index flags",
    )
    for ancestor in (SPEC["human_schema_ancestor"], SPEC["published_peer_ancestor"]):
        git(A, "merge-base", "--is-ancestor", ancestor, "HEAD")
    hooks = Path(git(A, "rev-parse", "--git-path", "hooks"))
    if not hooks.is_absolute():
        hooks = A / hooks
    require(hooks.resolve() == A / ".git/hooks", "nonstandard hooks path")
    for name, expected in SPEC["safety_hooks_sha256"].items():
        path = A / name
        safe(path)
        require(
            path.is_file() and os.access(path, os.X_OK) and digest(path) == expected,
            "normal safety hook drift: " + name,
        )


def load_source():
    require(sys.flags.isolated and sys.dont_write_bytecode, "use A python -I -B")
    require(Path(sys.prefix) == Path(SPEC["source_environment"]), "wrong source environment")
    sys.path[:0] = [str(A), str(A / "src"), str(A / "contract")]
    from scripts import u2_inputs, vendor_rk

    require(u2_inputs.ROOT == vendor_rk.ROOT == A, "wrong checkout imported")
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in ("scripts", "rkuarch", "uarch_contract"):
            origin = getattr(module, "__file__", None)
            if origin:
                require(Path(origin).resolve().is_relative_to(A), "wrong module: " + name)
    return u2_inputs, vendor_rk


def metadata(python, program, env):
    # Distribution metadata only. Never vendor.run_oracle, oracle_command or rk imports.
    return json.loads(
        subprocess.check_output(
            [str(python), "-I", "-B", "-c", program],
            cwd="/tmp",
            env=env,
            text=True,
        )
    )


def preflight(*, proposal_commit=None, stage="before"):
    require(not os.environ.get("PARAMS"), "PARAMS override forbidden")
    for key in (
        "PYTHONPATH",
        "MYPYPATH",
        "VIRTUAL_ENV",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    ):
        require(not os.environ.get(key), key + " must be unset")
    if proposal_commit is not None:
        check_proposal(proposal_commit)
    source_guard()
    u, v = load_source()
    require(v.PIN == SPEC["upstream_pin"], "upstream pin drift")
    require(digest(Path(v.__file__)) == SPEC["generator_sha256"], "generator drift")
    require(
        hashlib.sha256(v.ORACLE_PROGRAM.encode()).hexdigest() == SPEC["oracle_program_sha256"],
        "oracle program drift",
    )
    v.check_contract_pin(A)
    support = json.loads((HERE / "support-files.json").read_bytes())
    enumerated = {p.relative_to(A).as_posix(): digest(p) for p in u.support_files()}
    require(enumerated == support, "complete support inventory/bytes drift")
    tracked = set(git(A, "ls-files").splitlines())
    require(set(support) <= tracked, "support includes unreviewed untracked file")
    for name in support:
        safe(A / name)
    with tempfile.TemporaryDirectory(prefix="u3-freeze-input-check-") as tmp:
        staged = Path(tmp) / "inputs"
        identity = u.prepare_inputs(staged)
        require(identity == SPEC["input_manifest_sha256"], "prepared input digest drift")
        require(
            (staged / "SHA256SUMS").read_bytes() == (HERE / "input-SHA256SUMS").read_bytes(),
            "prepared input manifest drift",
        )
        checked = u.load_inputs(staged, identity)  # strict support; no historical fallback
        matrix = checked.matrix
    old = A / "contract/vendor" / ("rk-sim@" + v.PIN)
    require(
        digest(old / "MANIFEST.json") == SPEC["previous_artifact_manifest_sha256"],
        "adopted predecessor drift",
    )
    v.check_manifest(old)  # integrity only; not old-artifact currentness
    safe(OUTPUT)
    require(
        not OUTPUT.parent.exists() or OUTPUT.parent.is_dir(), "tables parent is not a directory"
    )
    require(OUTPUT.parent == A / "tables", "output must be the proposed ignored tables child")
    require(git(A, "check-ignore", str(OUTPUT)) == str(OUTPUT), "output not ignored")
    if stage == "before":
        require(not OUTPUT.exists(), "generation output must be absent; never resume/overwrite")
    else:
        require(OUTPUT.is_dir(), "generation root missing")
        u.load_inputs(OUTPUT / "inputs", SPEC["input_manifest_sha256"])
    rk = Path(SPEC["upstream_root"])
    safe(rk)
    v.check_clone(rk, v.PIN)
    env = dict(
        os.environ,
        UV_PROJECT_ENVIRONMENT=SPEC["oracle_environment"],
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
    )
    env.pop("UARCH_HUMAN", None)  # preflight never needs the human-only flag
    oracle_env = v.oracle_environment(rk) if os.environ.get("UV_PROJECT_ENVIRONMENT") else None
    if oracle_env is not None:
        require(
            oracle_env["UV_PROJECT_ENVIRONMENT"] == SPEC["oracle_environment"],
            "ambient oracle environment override",
        )
    require(
        not Path(SPEC["oracle_environment"]).resolve().is_relative_to(rk.resolve()),
        "oracle environment must be external",
    )
    v.verify_oracle_environment(rk, env)  # uv --locked --check --offline, never installs
    oracle = metadata(Path(SPEC["oracle_environment"]) / "bin/python", v.ENVIRONMENT_PROGRAM, env)
    oracle["uv_lock_sha256"] = digest(rk / "uv.lock")
    v.validate_environment_metadata(oracle, (rk / "uv.lock").read_bytes())
    source_env = dict(env, UV_PROJECT_ENVIRONMENT=SPEC["source_environment"])
    subprocess.run(
        ["uv", "sync", "--project", str(A), "--locked", "--check", "--offline", "--extra", "dev"],
        env=source_env,
        capture_output=True,
        text=True,
        check=True,
    )
    source = metadata(A / ".venv/bin/python", v.ENVIRONMENT_PROGRAM, source_env)
    source["uv_lock_sha256"] = digest(A / "uv.lock")
    expected = json.loads((HERE / "environments.json").read_bytes())
    require(
        oracle == expected["oracle"] and source == expected["source"], "environment identity drift"
    )
    require(
        subprocess.check_output(["uv", "--version"], text=True).strip() == expected["uv_version"],
        "uv version drift",
    )
    source_guard()
    v.check_clone(rk, v.PIN)
    return dict(
        status="preflight passed; no oracle executed",
        source_commit=SPEC["source_commit"],
        source_tree=SPEC["source_tree"],
        input_manifest_sha256=identity,
        support_count=len(support),
        matrix=matrix,
        oracle_environment=oracle,
        source_environment=source,
        output_absent=not OUTPUT.exists(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-commit")
    args = parser.parse_args()
    print(json.dumps(preflight(proposal_commit=args.proposal_commit), indent=2, sort_keys=True))
