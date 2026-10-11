"""Apply the proposed protected-test patch and reversible faults ONLY in a Git export.

No oracle generation/adoption, live protected edits, installs, branches or retained trees.
Run with the existing environment, supplying the reviewed local runtime commit as --revision.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = "src/rkuarch/engines/analytic/rotary_v2.py"
PREPARED = "src/rkuarch/workload/prepared_v2.py"
PROTOCOL = "src/rkuarch/engines/protocol_v2.py"
COUNTS = ["tests/rotary_v2/test_boundary.py", "-k", "independent_rotary_count_literals"]


def run(command: list[str], cwd: Path, env: dict[str, str], expected: int = 0) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=180)
    output = result.stdout + result.stderr
    if result.returncode != expected:
        raise RuntimeError(f"{command}: exit {result.returncode}, expected {expected}\n{output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "rev-parse", args.revision], cwd=ROOT, text=True
    ).strip()
    archive = subprocess.check_output(["git", "archive", revision], cwd=ROOT)
    outcomes: dict[str, object] = dict(revision=revision, protected_patch_installed_live=False)
    with tempfile.TemporaryDirectory(prefix="u3-rope-review-") as directory:
        scratch = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            stream.extractall(scratch, filter="data")
        env = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join(
                (str(scratch), str(scratch / "src"), str(scratch / "contract"))
            ),
            PYTHONDONTWRITEBYTECODE="1",
        )
        env.pop("MYPYPATH", None)
        patch = Path(__file__).with_name("protected-tests.patch")
        run(["git", "apply", "--check", str(patch)], scratch, env)
        run(["git", "apply", str(patch)], scratch, env)
        python = sys.executable
        tests = [python, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
        carrier = run(
            tests
            + [
                "contract/tests/test_rotary_v2.py",
                "contract/tests/test_rotary_v2_runtime_pending.py",
            ],
            scratch,
            env,
        )
        outcomes["activated_contract_tests"] = carrier.strip().splitlines()[-1]
        print("Activated protected tests: " + str(outcomes["activated_contract_tests"]), flush=True)
        faults = [
            ("omit-casts", CORE, "vector += 2 * elements", "vector += 0 * elements", COUNTS),
            (
                "wrong-pair-arithmetic",
                CORE,
                "vector = 3 * elements",
                "vector = 2 * elements",
                COUNTS,
            ),
            (
                "coefficient-per-head",
                CORE,
                "extent = math.prod(dims[d] for d in operand.dimensions)",
                "extent = math.prod(dims[d] for d in operand.dimensions)\n"
                '            if name == "rotary_embedding" and key in ("Cos", "Sin"):\n'
                '                extent *= dims["H"]',
                COUNTS,
            ),
            (
                "omit-k-coefficients",
                CORE,
                "extent = math.prod(dims[d] for d in operand.dimensions)",
                "extent = math.prod(dims[d] for d in operand.dimensions)\n"
                '            if op.id == "rope_k" and key in ("Cos", "Sin"):\n'
                "                extent = 0",
                COUNTS,
            ),
            (
                "drop-partial-tail",
                CORE,
                "extent = math.prod(dims[d] for d in operand.dimensions)",
                "extent = math.prod(dims[d] for d in operand.dimensions)\n"
                '            if name == "rotary_embedding" and key in ("X", "Y"):\n'
                '                extent = dims["B"] * dims["S"] * dims["H"] * dims["R"]',
                COUNTS,
            ),
            (
                "double-repeat",
                CORE,
                "instances = repeat * op.work_repeat",
                "instances = repeat * repeat * op.work_repeat",
                COUNTS,
            ),
            (
                "extra-tp-division",
                CORE,
                "vector = 3 * elements",
                'elements = elements // 2 if op.id == "rope_k" else elements\n'
                "        vector = 3 * elements",
                COUNTS,
            ),
            (
                "page-round-rotary",
                CORE,
                'elements = dims["B"] * dims["S"] * dims["H"] * dims["R"]',
                'elements = dims["B"] * 16 * dims["S"] * dims["H"] * dims["R"]',
                COUNTS,
            ),
            (
                "remove-rotary-graph-guard",
                PREPARED,
                "    _validate_rotary_graph(b)",
                "    pass  # injected fault",
                ["tests/rotary_v2/test_boundary.py", "-k", "rehashed_admission and q-bypass"],
            ),
            (
                "remove-engine-identity-join",
                PROTOCOL,
                "if j.engine != engine_identity():",
                "if False:",
                ["tests/rotary_v2/test_boundary.py", "-k", "rehashed_job and engine"],
            ),
            (
                "remove-result-recomputation",
                PROTOCOL,
                "if r != _evaluate(j):",
                "if False:",
                ["tests/rotary_v2/test_boundary.py", "-k", "result_cannot_invent_work"],
            ),
        ]
        faults.append(
            (
                "coefficient-retention-across-layers",
                CORE,
                "memory_read_bytes=reads * instances,",
                'memory_read_bytes=reads * instances - ((repeat - 1) * 4 * dims["B"] * '
                'dims["S"] * dims["R"] if name == "rotary_embedding" else 0),',
                COUNTS,
            )
        )
        faults.extend(
            [
                (
                    "remove-active-assumptions-join",
                    PREPARED,
                    "actual != physical_assumptions()",
                    "False",
                    ["tests/rotary_v2/test_boundary.py", "-k", "active_assumptions"],
                ),
                (
                    "remove-request-intent-join",
                    PROTOCOL,
                    "r.prepared_input_hash != b.bundle_hash\n"
                    '        or content_hash(r, exclude=("prepared_input_hash",)) != b.intent_hash',
                    "False",
                    ["tests/rotary_v2/test_boundary.py", "-k", "request_intent_join"],
                ),
            ]
        )
        mutation_results = []
        for name, file, before, after, selection in faults:
            target = scratch / file
            original = target.read_text()
            if original.count(before) != 1:
                raise RuntimeError(f"{name}: expected one exact fault site")
            run(tests + selection, scratch, env)  # valid baseline, not merely a failing mutant
            try:
                target.write_text(original.replace(before, after))
                failed = run(tests + selection, scratch, env, expected=1)
                if "FAILED " not in failed or "ERROR collecting" in failed:
                    raise RuntimeError(f"{name}: not an assertion failure\n{failed}")
            finally:
                target.write_text(original)
            restored = run(tests + selection, scratch, env)
            mutation_results.append(
                dict(
                    name=name,
                    mutant=failed.strip().splitlines()[-1],
                    reverted=restored.strip().splitlines()[-1],
                )
            )
            print(name + ": failed as intended; restored control passed", flush=True)
        outcomes["faults"] = mutation_results
        # A fresh interpreter must also reject an old job after source bytes change,
        # without changing the public engine version. Data lives only in this export.
        make = """
import json, runpy
from pathlib import Path
from rkuarch.workload.prepared_v2 import physical_assumptions
from rkuarch.table.capture_v2 import capture
ns = runpy.run_path('tests/rotary_v2/test_boundary.py')
c = capture(ns['active_bundle'](), assumptions=physical_assumptions())
Path('captured-test.json').write_text(json.dumps({
 'bundle': c.bundle.model_dump(mode='json'), 'request': c.request.model_dump(mode='json'),
 'assumptions': c.assumptions.model_dump(mode='json'),
 'job': c.jobs[0].model_dump(mode='json')}))
"""
        run([python, "-c", make], scratch, env)
        target = scratch / CORE
        original = target.read_text()
        try:
            target.write_text(original + "\n# deliberate new implementation bytes\n")
            check = """
import json
from pathlib import Path
from uarch_contract.assumptions import AssumptionSet
from rkuarch.engines.protocol_v2 import validate_engine_job
from rkuarch.engines.analytic.rotary_v2 import engine_identity
c = json.loads(Path('captured-test.json').read_text())
assert c['job']['engine']['version'] == engine_identity().version
assert c['job']['engine']['implementation_hash'] != engine_identity().implementation_hash
try:
 validate_engine_job(c['job'], c['bundle'], c['request'],
                     assumptions=AssumptionSet.model_validate(c['assumptions']))
except ValueError:
 print('changed bytes / same version refused in fresh process')
else:
 raise AssertionError('stale capture admitted')
"""
            outcomes["fresh_process_identity"] = run([python, "-c", check], scratch, env).strip()
        finally:
            target.write_text(original)
    print(json.dumps(outcomes, indent=2))


if __name__ == "__main__":
    main()
