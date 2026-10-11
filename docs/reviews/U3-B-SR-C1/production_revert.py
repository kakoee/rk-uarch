"""SR-C1 discriminator: restore the pre-fix recorder method in process memory only.

Run from repo root with PYTHONPATH=.:src:contract. No checkout/tree copy or live
source edit. Other code and tests are current. Exit status is pytest's result.
"""

import ast
import subprocess
import sys

import pytest

from validation.reporting import analytic_report as report

BASE = "7454ececbdc03cddd83194ac756a41cd06d99392"
SELECTION = (
    "invalid_return_full or diagnostic_is_deterministic or all_calls_and_errors or malformed_result"
)


def main():
    source = subprocess.check_output(
        ["git", "show", BASE + ":validation/reporting/analytic_report.py"], text=True
    )
    recorder = next(
        n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Recorder"
    )
    invoke = next(n for n in recorder.body if isinstance(n, ast.FunctionDef) and n.name == "invoke")
    namespace = dict(vars(report))
    exec(
        compile(ast.Module(body=[invoke], type_ignores=[]), "<pre-SR-C1-invoke>", "exec"), namespace
    )
    fixed = report.Recorder.invoke
    try:
        report.Recorder.invoke = namespace["invoke"]
        return pytest.main(
            [
                "-q",
                "validation/reporting/test_analytic_report.py",
                "-k",
                SELECTION,
                *sys.argv[1:],
            ]
        )
    finally:
        report.Recorder.invoke = fixed


if __name__ == "__main__":
    raise SystemExit(main())
