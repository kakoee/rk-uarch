"""Read-only future result checks and synthetic host fixture assembly; no runner."""

import copy
import json
from pathlib import Path

from uarch_contract.hashing import content_hash
from uarch_contract.mapped import (
    MappedBundle,
    NativeEngineIdentity,
    hardware_projection,
    validate_result,
)


def synthetic_engine():
    return NativeEngineIdentity.model_validate(
        dict(
            name="native",
            version="native-stage/1",
            implementation_hash=content_hash({"synthetic": "B-private-first-use-shape-only"}),
            compiler_lock_hash=content_hash({"synthetic": "not-a-tool-or-build"}),
            model=dict(
                name="fixed-delay",
                version="1",
                implementation_hash=content_hash({"synthetic": "not-a-model-identity"}),
            ),
        )
    )


def fixture_job(root, fixtures, case, engine):
    """Fixture assembly only; caller must distinguish synthetic from actual engine."""
    root, fixtures = Path(root), Path(fixtures)
    profile = json.loads((fixtures / "profile.json").read_bytes())
    registry = json.loads((fixtures / "registry.json").read_bytes())
    answer = json.loads((fixtures / "expectations.json").read_bytes())[case]
    bundle = json.loads((fixtures / "bundles" / (case + ".json")).read_bytes())
    point = bundle["points"][0]
    entry = next(e for e in profile["entries"] if e["case_id"] == case)
    job = json.loads((root / "contract/fixtures/mapped/kernel-job.json").read_bytes())
    job.update(
        bundle_hash=bundle["bundle_hash"],
        point_hash=point["payload_hash"],
        engine=engine.model_dump(mode="json"),
        mapped_point=point,
        workload_closure=bundle,
        assumptions_hash=bundle["assumptions_hash"],
        assumptions=bundle["assumptions"],
        hardware=hardware_projection(MappedBundle.model_validate(bundle).hardware_spec).model_dump(
            mode="json"
        ),
        hardware_spec_hash=bundle["hardware_spec_hash"],
        rank=bundle["rank"],
        frequency_ratio=point["frequency_ratio"],
        freq_hz=entry["freq_hz"],
        initial_state=point["initial_state"],
        priming_iterations=0,
        seed=0,
        admission=bundle["admission"],
        clock_setup=answer["clock_setup"],
        owners=[dict(owner_id=i, resource=f"fixture:{i}") for i in bundle["scope"]["owner_ids"]],
        registry=registry,
        profile=profile,
    )
    job["job_hash"] = content_hash(job, exclude=("job_hash",))
    return copy.deepcopy(job)


def exact_selection(expected, actual):
    if (
        not expected
        or not actual
        or len(set(actual)) != len(actual)
        or list(actual) != list(expected)
    ):
        raise ValueError("nonempty exact ordered selection required")


def check_real_result(value, job, answer):
    """For later human-authorized actual results only; no fabricated success fixture."""
    assert answer["outcome"] == "success"
    result = validate_result(value, job)
    assert result.duration_ps == answer["duration_ps"]
    assert [
        (j.job_id, j.owner_id, j.ready_ps, j.start_ps, j.end_ps)
        for j in result.observations.jobs.records
    ] == [tuple(row) for row in answer["intervals"]]
    assert {x.owner_id: x.busy_time_ps for x in result.busy_time_ps} == {
        int(k): v for k, v in answer["busy_by_owner"].items()
    }
    assert [
        (q.queue_id, q.item_id, q.population, q.enter_ps, q.leave_ps, q.owner_id, q.clock_domain)
        for q in result.observations.queue_membership.records
    ] == [tuple(row) for row in answer["queue_rows"]]
    if "critical_positive" in answer:
        wanted = [
            ("release_idle" if kind == "release_offset" else kind, cause, begin, end)
            for kind, cause, begin, end in answer["critical_positive"]
        ]
        assert [
            (x.kind, x.cause_job_id, x.start_ps, x.end_ps)
            for x in result.observations.critical_path.records
        ] == wanted
    if "grant_order" in answer:
        assert [
            e.job_id for e in result.observations.events.records if e.kind == "OWNER_GRANT"
        ] == list(answer["grant_order"])
    if "event_projection" in answer:
        assert [
            (e.t_ps, e.phase, e.job_id, e.kind) for e in result.observations.events.records
        ] == [tuple(x) for x in answer["event_projection"]]
    # Installed validation checks complete tight predecessor sets and canonical chosen causes,
    # phases/notification order, overflow/clock rows, counts and all remaining DTO joins.
    return result
