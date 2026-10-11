"""Exercise the unapplied patch in a disposable Git export; never install it live.

Run from the lane clone with its existing development interpreter. No installs, engine
runs, generation/adoption of oracle artifacts, or modifications to the live clone.
"""

from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BASE = "531d9c923c30dd465cf56c8a5865cd9ce62cdd84"
PACKAGE = Path(__file__).resolve().parent
REPOSITORY = PACKAGE.parents[2]


def run(args: list[str], root: Path, env: dict[str, str]) -> None:
    print("CHECK:", " ".join(args), flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


def compare_prototype(root: Path) -> None:
    """Called only in a fresh subprocess whose imports point at the temporary export."""
    from uarch_contract.rotary_v2 import SCHEMA_ROOTS

    path = root / "docs/reviews/U3-RoPE-schema-v1/schema_prototype.py"
    spec = importlib.util.spec_from_file_location("accepted_schema_prototype", path)
    assert spec is not None and spec.loader is not None
    prototype = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = prototype
    spec.loader.exec_module(prototype)
    approved = {m.__name__: m.model_json_schema() for m in prototype.CONTRACT_ROOTS}
    actual = {m.__name__: m.model_json_schema() for m in SCHEMA_ROOTS}
    assert actual == approved
    print("All 11 contract schemas equal the accepted prototype.", flush=True)


def main() -> None:
    archive = subprocess.run(
        ["git", "archive", BASE], cwd=REPOSITORY, check=True, capture_output=True
    ).stdout
    with tempfile.TemporaryDirectory(prefix="rkuarch-rope-patch-check-") as directory:
        root = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
            snapshot.extractall(root, filter="data")
        env = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join((str(root), str(root / "src"), str(root / "contract"))),
        )
        patch = str(PACKAGE / "protected.patch")
        run(["git", "apply", "--check", "--unidiff-zero", patch], root, env)
        run(["git", "apply", "--unidiff-zero", patch], root, env)
        python = sys.executable
        # This branch compares carrier schemas; it never executes an engine.
        run([python, str(Path(__file__).resolve()), "--compare", str(root)], root, env)
        run([python, "-m", "ruff", "check", "."], root, env)
        run([python, "-m", "mypy", "src", "contract/uarch_contract", "scripts"], root, env)
        run([python, "-m", "mypy", "--no-explicit-package-bases", "contract/tests"], root, env)
        run([str(Path(python).with_name("lint-imports"))], root, env)
        run([python, "-m", "uarch_contract.generate", "--check"], root, env)
        run([python, "-m", "uarch_contract.generate_rotary_v2", "--check"], root, env)
        run(
            [
                python,
                "-m",
                "pytest",
                "-q",
                "-rs",
                "contract/tests/test_rotary_v2.py",
                "contract/tests/test_rotary_v2_runtime_pending.py",
                "contract/tests/test_u2_schema_freshness.py",
            ],
            root,
            env,
        )
        strict = subprocess.run(
            [python, "scripts/vendor_rk.py", "--check"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        assert strict.returncode != 0
        assert "input support inventory changed" in strict.stdout + strict.stderr
        print(
            "EXPECTED REFUSAL in patched export: input support inventory changed. "
            "U0002 human lifecycle remains required.",
            flush=True,
        )
    print("Temporary export removed. No protected/live installation or runtime evidence.")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--compare":
        compare_prototype(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: exercise.py")
