"""Python removal/drift controls for F1, F2 and consumer wiring (disposable copies only).

Usage: DEV_PYTHON -I python_controls.py TREE WORK_ROOT REACH_FILES_TXT BINARY [NAME ...]
Each control copies TREE, applies one exact replacement (asserted to match once), checks the
mutated module is the one imported under pytest's configured pythonpath, then runs pytest
with bytecode disabled. `-x` is used only where a failure is the expected outcome.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

tree, work, reach_file, binary = map(Path, sys.argv[1:5])
selected = set(sys.argv[5:])
reach = reach_file.read_text().split()
DEFAULT = ["-m", "not nightly and not silicon and not native"]
CONTROLS = [
    # name, file, old, new, module, pytest args, with_binary
    ("f1-python-pin-removed", "contract/uarch_contract/ordinary.py",
     """        m.require(
            self.hardware_spec.cores.core_type.job_overhead_cycles.value == 32
            and self.hardware_spec.sync.barrier_latency_cycles.value == 32,
            "UnsupportedHardware",
            "model-2 checker requires 32-cycle job overhead and barrier latency",
        )
""", "", "uarch_contract.ordinary", ["tests/unit/test_ordinary_native.py"], False),
    ("f2-v3-compute-overhead-31", "src/rkuarch/verification/component/observations_v3.py",
     '("compute_overhead", 32)', '("compute_overhead", 31)',
     "rkuarch.verification.component.observations_v3", DEFAULT + reach, False),
    ("f2-v3-compute-overhead-31+binary", "src/rkuarch/verification/component/observations_v3.py",
     '("compute_overhead", 32)', '("compute_overhead", 31)',
     "rkuarch.verification.component.observations_v3",
     ["-x", "tests/native/test_ordinary_process.py"], True),
    ("f2-v3-barrier-31", "src/rkuarch/verification/component/observations_v3.py",
     'phase_specs[tid, None, "barrier"] = (32, "noc")', 'phase_specs[tid, None, "barrier"] = (31, "noc")',
     "rkuarch.verification.component.observations_v3", ["-x"] + DEFAULT + reach, False),
    ("f2-phase-laws-overhead-31", "src/rkuarch/verification/component/phase_laws.py",
     "overhead=32,", "overhead=31,",
     "rkuarch.verification.component.phase_laws", ["-x"] + DEFAULT + reach, False),
    ("wiring-consume-skips-check_v3+binary", "src/rkuarch/engines/native/ordinary.py",
     "    check_v3(\n", "    (lambda *_: None)(\n",
     "rkuarch.engines.native.ordinary", ["-m", "not nightly and not silicon"] + reach, True),
]
results = []
for name, path, old, new, module, args, with_binary in CONTROLS:
    if selected and name not in selected:
        continue
    copy = work / name
    if copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(tree, copy)
    target = copy / path
    text = target.read_text()
    assert text.count(old) == 1, (name, text.count(old))
    target.write_text(text.replace(old, new))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "ORDINARY_NATIVE")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if with_binary:
        env["ORDINARY_NATIVE"] = str(binary)
    origin = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path[:0]=['.','src','contract'];"
         f"import {module} as m; print(m.__file__)"],
        cwd=copy, env=env, capture_output=True, text=True, check=True).stdout.strip()
    assert origin == str(target), (origin, target)
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", *args],
                       cwd=copy, env=env, capture_output=True, text=True)
    lines = p.stdout.strip().splitlines()
    failed = [line for line in lines if line.startswith("FAILED")]
    row = dict(control=name, mutated=path, imported_from_mutated_copy=True, binary=with_binary,
               exit=p.returncode, summary=lines[-1] if lines else p.stderr[-300:],
               first_failures=[f[:160] for f in failed[:4]])
    results.append(row)
    print(json.dumps(row), flush=True)
    shutil.rmtree(copy)
