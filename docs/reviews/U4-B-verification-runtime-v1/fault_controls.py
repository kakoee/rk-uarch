"""Apply one exact optimization fault in a disposable clone, restoring in finally."""

import argparse
import hashlib
import subprocess
from pathlib import Path

PREPARATION = "validation/reporting/analytic_report.py"
KEY = "[as_json(bundle), as_json(physical_assumptions()), as_json(core.engine_identity())]"
FAULTS = {
    "claimed-hash": (PREPARATION, KEY, "bundle.bundle_hash"),
    "shared-output": (
        PREPARATION,
        "return copy.deepcopy(self._jobs[key])",
        "return self._jobs[key]",
    ),
    "stale-context": (PREPARATION, KEY, "[as_json(bundle)]"),
    "inactive-preparation": (
        PREPARATION,
        "bound_jobs = expected_jobs(cell, bundles, preparation=preparation)",
        "bound_jobs = expected_jobs(cell, bundles)",
    ),
    "executable-docs": (
        ".github/ci_scope.py",
        'return p.suffix == ".md" and (',
        'return p.suffix in (".md", ".py") and (',
    ),
}
TESTS = {
    "claimed-hash": "validation/reporting/test_preparation_reuse.py::"
    "test_preparation_reuse_returns_isolated_equal_jobs_and_rejects_drift",
    "shared-output": "validation/reporting/test_preparation_reuse.py::"
    "test_preparation_reuse_returns_isolated_equal_jobs_and_rejects_drift",
    "stale-context": "validation/reporting/test_preparation_reuse.py::"
    "test_current_assumptions_and_engine_are_part_of_preparation_key",
    "inactive-preparation": "validation/reporting/test_analytic_report.py::"
    "test_public_validation_reuses_only_preparation_within_one_call",
    "executable-docs": "tests/unit/test_ci_scope.py::"
    "test_non_markdown_or_unknown_paths_keep_full_suite[docs/reviews/probe.py]",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--fault", choices=FAULTS, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    authoritative = Path(__file__).resolve().parents[3]
    if root == authoritative or authoritative in root.parents:
        raise ValueError("faults require a separate disposable clone")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != args.commit:
        raise ValueError("fault clone commit mismatch")
    path, old, new = FAULTS[args.fault]
    target = root / path
    original = subprocess.check_output(["git", "show", f"{args.commit}:{path}"], cwd=root)
    if target.read_bytes() != original or original.count(old.encode()) != 1:
        raise ValueError("fault preimage mismatch")
    try:
        target.write_bytes(original.replace(old.encode(), new.encode()))
        result = subprocess.run(
            [str(root / ".venv/bin/python"), "-m", "pytest", "-q", TESTS[args.fault]],
            cwd=root,
            check=False,
        )
    finally:
        target.write_bytes(original)
        if target.read_bytes() != original:
            raise ValueError("restoration mismatch")
        print("restored_sha256=" + hashlib.sha256(original).hexdigest(), flush=True)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
