"""Validate proposal in private Git exports using existing Python tools; never run native."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = Path(tempfile.mkdtemp(prefix="u4-a-k2-receipts."))
    baseline, proposed = out / "baseline", out / "proposed"
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    archive = subprocess.check_output(["git", "archive", revision], cwd=REPO)
    for root in (baseline, proposed):
        root.mkdir()
        subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
    env = dict(os.environ)
    for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"):
        env.pop(key, None)
    env["MYPY_CACHE_DIR"] = str(out / "mypy-cache")
    rows = []
    py = [sys.executable, "-I", "-B"]
    ruff = str(Path(sys.executable).parent / "ruff")
    mypy = str(Path(sys.executable).parent / "mypy")

    def run(name, command, cwd):
        start = time.monotonic()
        result = subprocess.run(
            command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        log = out / (name + ".log")
        log.write_text(result.stdout)
        rows.append(
            dict(
                name=name,
                command=command,
                cwd=str(cwd),
                exit_code=result.returncode,
                seconds=round(time.monotonic() - start, 3),
                log_sha256=sha(log),
            )
        )
        print(name, result.returncode, result.stdout[-800:], flush=True)
        if result.returncode:
            (out / "failed-checks.json").write_text(json.dumps(rows, indent=2) + "\n")
            raise RuntimeError(f"{name} failed; retained {out}")

    def setup(root):
        return (
            "import sys; from pathlib import Path; "
            f"r=Path({str(root)!r}); sys.path[:0]=[str(r),str(r/'src'),str(r/'contract'),"
            "str(r/'docs/reviews/U4-B-K2-semantic-reconciliation-v1')]; "
        )

    run("prepare", py + [str(PACKAGE / "prepare_patch.py"), str(proposed)], REPO)
    changed_py = [
        "contract/uarch_contract/mapped.py",
        "contract/tests/mapped/test_k2_semantic_completion.py",
    ]
    run(
        "format-imports",
        [ruff, "check", "--no-cache", "--fix", "--ignore", "E501", *changed_py],
        proposed,
    )
    run("format", [ruff, "format", "--no-cache", *changed_py], proposed)
    run(
        "generate-proposed-mirrors",
        py
        + [
            "-c",
            setup(proposed)
            + "from uarch_contract.generate_mapped import generate; print(generate())",
        ],
        proposed,
    )
    selection = [
        "contract/tests/mapped",
        "tests/unit/test_u4_a_mapped_loader.py",
        "tests/unit/test_prompt_sync.py",
    ]
    run(
        "proposed-tests",
        py
        + [
            "-c",
            setup(proposed)
            + "import pytest; raise SystemExit(pytest.main("
            + repr(["-q", "-p", "no:cacheprovider", *selection])
            + "))",
        ],
        proposed,
    )
    run("source-types", [mypy, "src", "contract/uarch_contract", "scripts"], proposed)
    run("contract-test-types", [mypy, "--no-explicit-package-bases", "contract/tests"], proposed)
    run(
        "proposed-lint",
        [
            ruff,
            "check",
            "--no-cache",
            *changed_py,
            "contract/tests/mapped/test_admission.py",
            "tests/unit/test_u4_a_mapped_loader.py",
        ],
        proposed,
    )
    selection = [
        str(PACKAGE / "test_semantics.py"),
        str(PACKAGE / "test_records.py"),
        str(PACKAGE / "test_construction.py"),
        "docs/reviews/U4-B-K2-semantic-reconciliation-v1/test_literals.py",
        "docs/reviews/U4-B-K2-semantic-reconciliation-v1/test_membership.py",
        "docs/reviews/U4-B-K2-semantic-reconciliation-v1/test_boundary.py",
        "tests/unit/test_u4_a_mapped_loader.py",
        "tests/unit/test_prompt_sync.py",
    ]
    args = [
        "-q",
        "-c",
        str(baseline / "pyproject.toml"),
        "--rootdir=" + str(baseline),
        "-p",
        "no:cacheprovider",
        *selection,
    ]
    run(
        "baseline-host-tests",
        py
        + [
            "-c",
            setup(baseline) + "import pytest; raise SystemExit(pytest.main(" + repr(args) + "))",
        ],
        baseline,
    )
    run(
        "baseline-schema-freshness",
        py
        + [
            "-c",
            setup(baseline)
            + "from uarch_contract.generate_mapped import generate; "
            "assert generate(check=True)==[]",
        ],
        baseline,
    )
    run("baseline-currentness", py + [str(baseline / "scripts/vendor_rk.py"), "--check"], baseline)
    run(
        "baseline-read-audit",
        py
        + [
            str(baseline / "docs/reviews/U4-B-K2-semantic-reconciliation-v1/audit.py"),
            str(baseline),
            str(out / "read-audit.json"),
        ],
        baseline,
    )
    run("live-lint", [ruff, "check", "--no-cache", "."], REPO)
    run(
        "collect-patch",
        py + [str(PACKAGE / "prepare_patch.py"), str(proposed), "--collect", str(PACKAGE)],
        REPO,
    )
    run(
        "patch-apply-check",
        ["git", "apply", "--check", str(PACKAGE / "complete.proposed.patch")],
        REPO,
    )
    # Exact patch postimages, independently applied to a third fresh export.
    replay = out / "replay"
    replay.mkdir()
    subprocess.run(["tar", "-x", "-C", str(replay)], input=archive, check=True)
    run("patch-replay", ["git", "apply", str(PACKAGE / "complete.proposed.patch")], replay)
    manifest = json.loads((PACKAGE / "patch-manifest.json").read_text())
    for row in manifest:
        assert sha(replay / row["path"]) == row["after_sha256"], row
    run(
        "replay-schema-freshness",
        py
        + [
            "-c",
            setup(replay)
            + "from uarch_contract.generate_mapped import generate; "
            "assert generate(check=True)==[]",
        ],
        replay,
    )
    receipt = dict(
        source_commit=revision,
        private_root=str(out),
        python=sys.version,
        commands=rows,
        patch_postimages_reproduced=len(manifest),
        native_execution=False,
        dependency_construction=False,
        protected_installed=False,
    )
    (out / "checks.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("RECEIPTS", out, flush=True)


if __name__ == "__main__":
    main()
