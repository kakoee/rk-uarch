"""Apply the proposal in a disposable Git export; never install into the live tree."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    return {
        "command": command,
        "exit": completed.returncode,
        "output": completed.stdout + completed.stderr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    root = package.parents[2]
    interpreter = args.python.absolute()
    base = subprocess.check_output(["git", "rev-parse", args.base], cwd=root, text=True).strip()
    patch = package / "protected.patch"
    evidence: dict[str, object] = {
        "base": base,
        "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
    }
    checks = []
    with tempfile.TemporaryDirectory(prefix=".u4-a-validation-", dir=root) as name:
        export = Path(name)
        archive = subprocess.check_output(["git", "archive", base], cwd=root)
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            stream.extractall(export, filter="data")
        subprocess.run(["git", "init", "-q"], cwd=export, check=True)
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=export, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=export, check=True)
        env = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join(str(export / x) for x in ("contract", "src", ".")),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONNOUSERSITE="1",
        )
        env.pop("UARCH_HUMAN", None)
        origins = run(
            [
                str(interpreter),
                "-c",
                "import uarch_contract,rkuarch; print(uarch_contract.__file__); "
                "print(rkuarch.__file__)",
            ],
            export,
            env,
        )
        assert origins["exit"] == 0 and str(export) in str(origins["output"])
        checks.append(origins)
        commands = [
            [
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "contract/tests/mapped",
                "contract/tests/test_rotary_v2.py",
                "tests/rotary_v2",
                "tests/unit/test_u2_a_prepared.py",
            ],
            ["-m", "uarch_contract.generate_mapped", "--check"],
            ["-m", "uarch_contract.generate", "--check"],
            ["-m", "uarch_contract.generate_rotary_v2", "--check"],
            ["-m", "mypy", "src", "contract/uarch_contract", "scripts"],
            ["-m", "mypy", "--no-explicit-package-bases", "contract/tests"],
            [
                "-m",
                "ruff",
                "check",
                "contract/uarch_contract/mapped.py",
                "contract/uarch_contract/generate_mapped.py",
                "contract/tests/mapped",
            ],
        ]
        for command in commands:
            item = run([str(interpreter), *command], export, env)
            checks.append(item)
            print("exit", item["exit"], " ".join(command), flush=True)
            if item["exit"] != 0:
                evidence["checks"] = checks
                (package / "validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
                raise SystemExit(str(item["output"]))
        item = run([str(interpreter.parent / "lint-imports"), "--no-cache"], export, env)
        checks.append(item)
        assert item["exit"] == 0, item
        item = run([str(interpreter), "scripts/vendor_rk.py", "--check"], export, env)
        checks.append(item)
        assert item["exit"] == 1 and "input support inventory changed" in str(item["output"]), item
        # Structural refusal discriminator, not a runtime timing mutant.
        target = export / "contract/uarch_contract/mapped.py"
        original = target.read_text()
        selector = [
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "contract/tests/mapped",
            "-k",
            "rehashed_refusals and (R04 or R09)",
        ]
        baseline = run([str(interpreter), *selector], export, env)
        checks.append(baseline)
        assert baseline["exit"] == 0
        try:
            target.write_text(original.replace('raise ValueError(code + ": " + detail)', "pass"))
            faulty = run([str(interpreter), *selector], export, env)
            checks.append(faulty)
            assert faulty["exit"] == 1 and "DID NOT RAISE" in str(faulty["output"]), faulty
        finally:
            target.write_text(original)
        restored = run([str(interpreter), *selector], export, env)
        checks.append(restored)
        assert restored["exit"] == 0
        evidence["checks"] = checks
        evidence["classification"] = (
            "schema/prototype and legacy compatibility; no native execution"
        )
        evidence["export_removed"] = True
        (package / "validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("Disposable validation complete; expected refusals retained.")


if __name__ == "__main__":
    main()
