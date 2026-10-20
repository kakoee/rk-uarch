"""Removal-detection controls for the native F1/F3 corrections (disposable copies only).

Usage: python3 -I native_mutation.py SOURCE_TREE WORK_ROOT NATIVE_BUILD_PROBE MUTANT
MUTANT:
  f1-pin-removed     delete the job-overhead/barrier pin from component_admission.rs
  f3-main-no-stdout  shipping main.rs succeeds with exit 0 but writes no result bytes
Each copies SOURCE_TREE, applies one exact replacement (asserting it matched once), and runs
the unchanged `make native-test` Cargo recipe via NATIVE_BUILD_PROBE (exact-ID cleanup).
"""

import shutil
import subprocess
import sys
from pathlib import Path

source, root, probe, mutant = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
MUTANTS = {
    "f1-pin-removed": (
        "native/crates/uarch-engine/src/component_admission.rs",
        """    require(
        integer(&c["job_overhead_cycles"])? == 32
            && integer(&h["sync"]["barrier_latency_cycles"])? == 32,
        "UnsupportedHardware",
        "model-2 checker requires 32-cycle job overhead and barrier latency",
    )?;
""",
        "",
    ),
    "f3-main-no-stdout": (
        "native/crates/uarch-engine/src/main.rs",
        "std::io::stdout().write_all(&output)",
        "std::io::stdout().write_all(&output[..0])",
    ),
}
path, old, new = MUTANTS[mutant]
tree = root / f"tree-{mutant}"
shutil.copytree(source, tree)
target = tree / path
text = target.read_text()
assert text.count(old) == 1, (mutant, text.count(old))
target.write_text(text.replace(old, new))
print(f"mutant {mutant}: replaced 1 occurrence in {path}", flush=True)
subprocess.run([sys.executable, "-I", probe, str(tree), str(root / f"work-{mutant}"), "test"], check=False)
