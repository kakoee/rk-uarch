import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

primary = Path("/home/jjaff/AI-infra-simulation/rk-uarch")
a = primary.with_name("rk-uarch-u3-a")
review = primary / "docs/reviews/U3-artifact-adoption-v1"
archive = subprocess.check_output(
    ["git", "-C", str(a), "archive", "187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f"]
)
with tempfile.TemporaryDirectory(prefix="u3-adoption-proposal-check-") as tmp:
    scratch = Path(tmp)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(scratch, filter="data")
    destination = scratch / "contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963"
    shutil.rmtree(destination)
    shutil.copytree(a / "tables/U3-rope-generation-v1/candidate", destination)
    subprocess.run(
        ["git", "apply", "--check", "--unidiff-zero", str(review / "adoption-bindings.patch")],
        cwd=scratch,
        check=True,
    )
    subprocess.run(
        ["git", "apply", "--unidiff-zero", str(review / "adoption-bindings.patch")],
        cwd=scratch,
        check=True,
    )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    env.pop("MYPYPATH", None)
    env.pop("UARCH_HUMAN", None)
    # This draft approval record is only a conditional test premise in disposable scratch.
    # It is not a human decision or live canonical adoption.
    bootstrap = (
        "import sys,runpy;sys.path[:0]="
        + repr([str(scratch), str(scratch / "src"), str(scratch / "contract")])
        + ";sys.argv=['vendor_rk','--check'];"
        "runpy.run_module('scripts.vendor_rk',run_name='__main__')"
    )
    strict = subprocess.run(
        [str(a / ".venv/bin/python"), "-I", "-B", "-c", bootstrap],
        cwd=scratch,
        env=env,
        text=True,
        capture_output=True,
    )
    (review / "scratch-strict-check.txt").write_text(strict.stdout + strict.stderr)
    assert strict.returncode == 0
    bootstrap = (
        "import sys;sys.path[:0]="
        + repr([str(scratch), str(scratch / "src"), str(scratch / "contract")])
        + ";import pytest;raise SystemExit(pytest.main(['-q','-rs','contract/tests',"
        "'tests/unit/test_u2_b_stage2_reference.py',"
        "'tests/integration/test_u2_b_r202_public.py','--require-vendor']))"
    )
    with (review / "scratch-tests.log").open("w") as log:
        tests = subprocess.run(
            [str(a / ".venv/bin/python"), "-I", "-B", "-c", bootstrap],
            cwd=scratch,
            env=env,
            text=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    (review / "scratch-results.json").write_text(
        json.dumps(
            dict(
                source_commit="187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f",
                strict_check_exit=strict.returncode,
                tests_exit=tests.returncode,
                adoption_installed_live=False,
                draft_review_is_conditional_test_premise=True,
                protected_test_activation_applied=False,
            ),
            indent=2,
        )
        + "\n"
    )
    assert tests.returncode == 0
    print((review / "scratch-tests.log").read_text().splitlines()[-1])
