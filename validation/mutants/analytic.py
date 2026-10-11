"""Test-only faults at the accepted EngineJob -> EngineResult callable boundary.

Results are resealed so identity corruption alone does not kill the mutant. These
wrappers are injected faults, never registered production engines or evidence.
"""

from uarch_contract.hashing import content_hash

from rkuarch.engines.analytic.core import run_analytic
from rkuarch.engines.protocol import EngineJob, EngineResult


def mutant(name):
    calls = 0

    def execute(job):
        nonlocal calls
        calls += 1
        if name == "wrong_bandwidth_field":
            raw_job = job.model_dump(mode="json")
            raw_job["hardware"]["dram_bw_bytes_per_s"] = job.hardware.vector_peak_ops_per_s
            raw_job["job_hash"] = content_hash(raw_job, exclude=("job_hash",))
            result = run_analytic(EngineJob.model_validate(raw_job))
        else:
            result = run_analytic(job)
        raw = result.model_dump(mode="json")
        raw["job_hash"] = job.job_hash
        if name == "off_by_one_matrix":
            op = next(o for o in raw["per_op"] if o["counts"]["matrix_ops"] > 0)
            op["counts"]["matrix_ops"] += 2
            raw["counts"]["matrix_ops"] += 2
        elif name == "double_attribution":
            raw["attribution_ps"]["overhead"] += result.duration_ps
        elif name == "zero_unmodelled_diagnostic":
            raw["busy_time_ps"]["compute"] = 0.0
        elif name == "nondeterministic_output":
            # Valid string field, changing across calls; all numeric values stay fixed.
            raw["unrepresented"].append(f"injected-call-{calls}")
        elif name != "wrong_bandwidth_field":
            raise ValueError(f"Unknown mutant: {name}")
        raw["result_hash"] = content_hash(raw, exclude=("result_hash",))
        return EngineResult.model_validate(raw)

    return execute
