"""Reproduce AD-M1 in a disposable exact-source export, never install or generate."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("/home/jjaff/AI-infra-simulation/rk-uarch-u4-a")
BASE = "0cf24d91eeca5cc45182eb6fb03202677fd97dcb"
CANDIDATE = Path(
    "/home/jjaff/AI-infra-simulation/rk-uarch/tables/U4-M-policy-generation-v1/candidate"
)
MANIFEST = "b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc"
PYTHON = "/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python"
TARGET = "tests/unit/test_u2_support_policy.py"
BINDINGS = REPO / "docs/reviews/U4-M-policy-artifact-adoption-v1/adoption-bindings.patch"
PIN = "1e5706e0ebfcc67c1a7333079a35b75f693e9963"
ENV = os.environ.copy()
for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN", "SHA", "RK", "PARAMS"):
    ENV.pop(key, None)
ENV.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", GIT_OPTIONAL_LOCKS="0")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args, cwd=SOURCE):
    return subprocess.check_output(["git", *args], cwd=cwd, env=ENV)


def snapshot(root, names=None):
    paths = (root / n for n in names) if names is not None else root.rglob("*")
    result = {}
    for path in paths:
        if ".git" in path.relative_to(root).parts:
            continue
        assert not path.is_symlink(), path
        if path.is_file():
            result[path.relative_to(root).as_posix()] = (
                sha(path.read_bytes()),
                path.stat().st_mtime_ns,
            )
    return result


# Explicit precedence and origin verification, with ambient import environment unset.
# Disable producers before pytest imports any selected module. Subprocess controls
# invoke only --help/--check or library validation; never a generation command.
BOOT = """
import json, os, sys
from pathlib import Path
root = Path.cwd()
sys.path[:0] = [str(root), str(root / 'src'), str(root / 'contract')]
from scripts import u2_inputs as u, vendor_rk as v, u2_support as p, u2_import_guard as g
import uarch_contract as c
import rkuarch as r
assert 'PYTHONPATH' not in os.environ and 'MYPYPATH' not in os.environ
origins = {m.__name__: str(Path(m.__file__).resolve()) for m in (u,v,p,g,c,r)}
assert all(Path(path).is_relative_to(root) for path in origins.values())
print('VERIFIED_ORIGINS ' + json.dumps(origins), flush=True)
def forbidden(*args, **kwargs):
    raise AssertionError('AD-M1 producer forbidden')
u.prepare_inputs = forbidden
v.run_oracle = v.collect_snapshot = v.publish_snapshot = forbidden
"""


def main():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    tracked = git("ls-files", "-z").decode().rstrip("\0").split("\0")
    live_before = snapshot(SOURCE, tracked)
    saved_before = snapshot(CANDIDATE.parent)
    assert sha(BINDINGS.read_bytes()) == (
        "ed9029f25260abd7b1db21d0bdd3229267315bf22958e447d51a49ac0ad77da4"
    )
    assert sha((CANDIDATE / "MANIFEST.json").read_bytes()) == MANIFEST
    manifest = json.loads((CANDIDATE / "MANIFEST.json").read_bytes())
    members = {p.relative_to(CANDIDATE).as_posix() for p in CANDIDATE.rglob("*") if p.is_file()}
    assert len(members) == 49 and members == set(manifest["files"]) | {"MANIFEST.json"}
    assert all(sha((CANDIDATE / n).read_bytes()) == h for n, h in manifest["files"].items())
    results = {
        "source_commit": BASE,
        "source_tree": git("rev-parse", BASE + "^{tree}").decode().strip(),
        "b_starting_head": git("rev-parse", "HEAD", cwd=REPO).decode().strip(),
        "candidate_manifest_sha256": MANIFEST,
        "candidate_members": 49,
        "adoption_bindings_sha256": sha(BINDINGS.read_bytes()),
        "test_patch_sha256": sha((HERE / "test-control.patch").read_bytes()),
        "conditional_placement_only": True,
        "live_adoption": False,
        "checks": [],
    }
    with tempfile.TemporaryDirectory(prefix="u4-b-ad-m1-verify-") as temporary:
        work = Path(temporary)
        root = work / "source"
        root.mkdir()
        with tarfile.open(fileobj=io.BytesIO(git("archive", BASE))) as archive:
            archive.extractall(root, filter="data")
        git("init", "-q", cwd=root)
        target = root / TARGET
        original = target.read_bytes()
        artifact = root / "contract/vendor" / ("rk-sim@" + PIN)
        old = work / "prior-artifact"
        shutil.copytree(artifact, old)
        prior_snapshot = snapshot(old)
        for name, count in (("parity/fixtures.json", 1008), ("parity/refusals.json", 4)):
            assert (old / name).read_bytes() == (CANDIDATE / name).read_bytes()
            assert len(json.loads((CANDIDATE / name).read_bytes())) == count
        results["unchanged_nominal_rows"] = 1008
        results["unchanged_precision_refusals"] = 4
        shutil.rmtree(artifact)
        shutil.copytree(CANDIDATE, artifact)
        git("apply", "--unidiff-zero", str(BINDINGS), cwd=root)
        baseline = snapshot(root)
        results["test_before_sha256"] = sha(original)
        test_node = TARGET + "::test_fresh_direct_valid_controls"

        def run(label, argv, expected=0):
            done = subprocess.run(argv, cwd=root, env=ENV, capture_output=True, text=True)
            (HERE / (label + ".log")).write_text(done.stdout + done.stderr)
            results["checks"].append(
                {
                    "label": label,
                    "argv": argv,
                    "cwd": str(root),
                    "exit": done.returncode,
                    "expected_exit": expected,
                }
            )
            print(label, "exit", done.returncode, flush=True)
            assert done.returncode == expected, (label, done.stdout[-3000:], done.stderr)
            return done

        def pytest(label, selection, expected=0):
            return run(
                label,
                [
                    PYTHON,
                    "-I",
                    "-B",
                    "-c",
                    BOOT + "\nimport pytest\nsys.exit(pytest.main(sys.argv[1:]))",
                    "-c",
                    str(root / "pyproject.toml"),
                    "--rootdir=" + str(root),
                    "-p",
                    "no:cacheprovider",
                    "--basetemp=" + str(work / label),
                    "-q",
                    "-rs",
                    *selection,
                ],
                expected,
            )

        try:
            strict = (
                BOOT
                + """
v.check_contract_pin(root)
v.check_manifest(u.ADOPTED)
v.check_snapshot_inputs(u.ADOPTED)
v.check_generator(u.ADOPTED, current=True)
print('GENUINE_STRICT_CURRENT_SUCCESS')
"""
            )
            run("candidate-strict", [PYTHON, "-I", "-B", "-c", strict])
            failure = pytest("baseline", [test_node], 1)
            assert "assert 0 == 1" in failure.stdout and "1 failed" in failure.stdout
            git("apply", "--unidiff-zero", str(HERE / "test-control.patch"), cwd=root)
            corrected = target.read_bytes()
            results["test_after_sha256"] = sha(corrected)
            pytest("corrected", [test_node])
            git("apply", "--unidiff-zero", "--reverse", str(HERE / "test-control.patch"), cwd=root)
            assert target.read_bytes() == original
            failure = pytest("reverted", [test_node], 1)
            assert "assert 0 == 1" in failure.stdout and "1 failed" in failure.stdout
            git("apply", "--unidiff-zero", str(HERE / "test-control.patch"), cwd=root)
            assert target.read_bytes() == corrected
            pytest("restored", [test_node])
            pytest(
                "affected-selection",
                [
                    TARGET,
                    "contract/tests/test_u2_historical_snapshot.py",
                    "tests/integration/test_u2_b_r202_public.py",
                    "tests/unit/test_u2_b_stage2_reference.py",
                    "contract/tests/mapped/test_admission.py",
                    "--deselect=contract/tests/test_u2_historical_snapshot.py::"
                    "test_historical_guard_refuses_current_canonical_before_candidate",
                ],
            )
            run("test-ruff", [PYTHON, "-B", "-m", "ruff", "check", "--no-cache", TARGET])
            after = snapshot(root)
            assert after.keys() == baseline.keys()
            assert {n for n in after if after[n] != baseline[n]} == {TARGET}
            results["conditional_export_isolation"] = {
                "files": len(after),
                "only_changed_path": TARGET,
                "test_patch_exact": target.read_bytes() == corrected,
                "all_other_bytes_and_mtimes_unchanged": True,
            }
            shutil.rmtree(artifact)
            shutil.copytree(old, artifact)
            stale_before = snapshot(root)
            run(
                "prior-strict-refusal",
                [
                    PYTHON,
                    "-I",
                    "-B",
                    "-c",
                    BOOT
                    + """
v.check_manifest(u.ADOPTED)
v.check_snapshot_inputs(u.ADOPTED)
v.check_generator(u.ADOPTED, current=False)
try:
    v.check_generator(u.ADOPTED, current=True)
except ValueError as exc:
    assert str(exc) == 'input support inventory changed', str(exc)
    print('EXPECTED_STRICT_REFUSAL: ' + str(exc))
else:
    raise AssertionError('stale artifact incorrectly accepted')
""",
                ],
            )
            pytest("prior-policy-selection", [TARGET])
            assert snapshot(root) == stale_before
            assert snapshot(old) == prior_snapshot
            results["prior_export_isolation"] = {"files": len(stale_before), "unchanged": True}
            results["status"] = "passed; correction unapplied; live adoption still pending"
        finally:
            assert git("rev-parse", "HEAD").decode().strip() == BASE
            assert snapshot(SOURCE, tracked) == live_before
            assert snapshot(CANDIDATE.parent) == saved_before
            results["live_preservation"] = {
                "A_tracked_files_bytes_mtimes": len(live_before),
                "saved_generation_files_bytes_mtimes": len(saved_before),
                "A_head_unchanged": True,
                "unchanged": True,
            }
            (HERE / "verification.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
