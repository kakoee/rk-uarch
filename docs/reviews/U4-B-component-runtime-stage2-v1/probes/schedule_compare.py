"""Compare selected workload semantics, retaining full scenario identities separately."""

import hashlib
import json
import sys
from pathlib import Path

base, output = map(Path, sys.argv[1:])
excluded = {"point_id", "fixture_id", "producer", "case_id"}


def clean(value):
    if isinstance(value, dict):
        return {
            k: clean(v) for k, v in value.items() if not k.endswith("_hash") and k not in excluded
        }
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


report = []
for name in ("C04-carrier", "C06-small", "C07-hbm-1", "C07-sram-1"):
    ids = ["v3:B-native-resource-" + name, "v3:B2-resource-" + name]
    raw = [(base / "jobs" / (case + ".json")).read_bytes() for case in ids]
    jobs = [json.loads(value) for value in raw]
    assert clean(jobs[0]["workload_closure"]) == clean(jobs[1]["workload_closure"])
    report.append(
        dict(
            cases=ids,
            equal_semantic_workload_after_declared_metadata=True,
            input_hashes=[hashlib.sha256(value).hexdigest() for value in raw],
        )
    )
output.write_text(
    json.dumps(
        dict(
            pairs=report,
            exclusions=sorted(excluded) + ["*_hash"],
            scope=(
                "Workload closure comparison only. Full input/profile/scenario "
                "identities remain frozen; no gate changed."
            ),
        ),
        indent=2,
    )
    + "\n"
)
