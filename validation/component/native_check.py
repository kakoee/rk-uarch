"""Independent consumption of real private /2 output; never synthesizes a result."""

import json
from pathlib import Path
from typing import Any

from uarch_contract.mapped import MappedEngineJob, MappedEngineResult

from validation.component.checks import need
from validation.component.selection import assert_case

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads(
    (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
)["observation_contract"]


def check_native(raw_job: dict[str, Any], raw_result: dict[str, Any], item: dict[str, Any]) -> None:
    job = MappedEngineJob.model_validate(raw_job)
    result = MappedEngineResult.model_validate(raw_result)
    assert_case(job, result, item, CONTRACT)
    expected = item["expected"]
    obs = raw_result["observations"]
    if "job_ready_ps" in expected:
        need(
            {x["job_id"]: x["ready_ps"] for x in obs["jobs"]["records"]}
            == expected["job_ready_ps"],
            "O2 literal dependency readiness",
        )
    if "transient_bacc" in expected:
        rows = [x for x in obs["allocations"]["records"] if x["buffer_id"] == "bacc"]
        need(len(rows) == 1, "O2 exact allocation inventory")
        need(
            [rows[0]["allocate_ps"], rows[0]["free_ps"]] == expected["transient_bacc"],
            "O2 literal final-consumer endpoints",
        )
