"""Advisory A1 probe: saved /4 job/result replay is locked to the exact installed package version.

Usage: RUNTIME_PYTHON -I version_lock.py JOB RESULT
Simulates a later install reporting 0.0.2 (only the distribution-version lookup is replaced),
and shows that a build identifier such as 0.0.1+g12be875 cannot be recorded in the carrier.
"""

import json
import sys
from pathlib import Path

import rkuarch.engines.native.ordinary as ordinary
from uarch_contract.hashing import content_hash
from uarch_contract.ordinary import OrdinaryJob

job, result = Path(sys.argv[1]), Path(sys.argv[2])
print("installed version:", ordinary.version("rk-uarch"))
print("replay at installed version:", ordinary.replay(job, result).duration_ps, "ps")
for later in ("0.0.2", "0.0.1+g12be875"):
    ordinary.version = lambda _name, v=later: v
    try:
        ordinary.replay(job, result)
        print(f"replay as if installed {later}: accepted")
    except Exception as e:  # noqa: BLE001
        print(f"replay as if installed {later}: {type(e).__name__}: {str(e)[:80]}")
raw = json.loads(job.read_text())
raw["engine"]["package_version"] = "0.0.1+g12be875"
raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
try:
    OrdinaryJob.model_validate(raw)
    print("carrier with local build identifier: accepted")
except Exception as e:  # noqa: BLE001
    print("carrier with local build identifier:", type(e).__name__, " ".join(str(e).split())[:140])
