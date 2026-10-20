"""v2 saved-result replay (no binary involved) and the Stage 1 wrong-law relabel control.

Usage: DEV_PYTHON -I v2_replay.py INPUTS_DIR V2_OUTPUT_DIR V1_WRONG_LAW_OUTPUT
The wrong-law output was produced in Stage 1 by the v1 binary for 16-cycle-overhead hardware
(now refused at admission); here it is relabelled to the production job as before.
"""

import json
import sys
from pathlib import Path

import rkuarch.engines.native.ordinary as ordinary
from uarch_contract.hashing import canonical_json, content_hash, strict_json_loads
from uarch_contract.ordinary import OrdinaryJob, validate_result

from rkuarch.verification.component.observations_v3 import check_v3

inputs, outputs, wrong_src = map(Path, sys.argv[1:4])
print("ordinary module:", ordinary.__file__)
for name in ("production", "test-synthetic-stage2-cc-v3", "test-synthetic-stage2-sr-v3",
             "test-synthetic-runtime-cc0-v3"):
    r = ordinary.replay(inputs / f"{name}.json", outputs / f"{name}-release.json",
                        test_only=name.startswith("test-"))
    print(f"replay {name}: {r.duration_ps} ps {r.admission.eligibility}")
job = OrdinaryJob.model_validate(strict_json_loads((inputs / "production.json").read_bytes()))
wrong = strict_json_loads(wrong_src.read_bytes())
wrong["job_hash"] = job.job_hash
wrong["admission"] = job.admission.model_dump(mode="json")
wrong["result_hash"] = content_hash(wrong, exclude=("result_hash",))
outcomes = {}
for label, call in (("structural validate_result", lambda: validate_result(wrong, job)),
                    ("shipped check_v3", lambda: check_v3(job.model_dump(mode="json"), wrong,
                                                          {"unrepresented": ordinary.UNREPRESENTED}))):
    try:
        call()
        outcomes[label] = "accepted"
    except Exception as e:  # noqa: BLE001
        outcomes[label] = f"{type(e).__name__}: {str(e)[:60]}"
target = outputs / "wrong-law-relabelled.json"
target.write_bytes(canonical_json(wrong).encode())
try:
    ordinary.replay(inputs / "production.json", target)
    outcomes["ordinary.replay"] = "ACCEPTED"
except Exception as e:  # noqa: BLE001
    outcomes["ordinary.replay"] = f"{type(e).__name__}: {str(e)[:60]}"
print("wrong-law relabel (duration", wrong["duration_ps"], "ps):", json.dumps(outcomes))
