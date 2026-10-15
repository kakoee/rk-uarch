"""Synthetic B subrecord checks on exact A validators; no complete/native results."""

import copy

import pytest
from projections import project, subrecords
from uarch_contract.mapped import ClockObservation, CriticalInterval, MappedEngineResult, Observed
from uarch_contract.mapped import validate_fixed_delay_observations as validate


def check(key):
    r, j = project(key)
    validate(r, j)
    assert [(e.t_ps, e.phase) for e in r.observations.events.records] == sorted(
        (e.t_ps, e.phase) for e in r.observations.events.records
    )
    return (r, j)


@pytest.mark.parametrize("key", [f"S{i:02}" for i in range(1, 18)])
def test_all_seventeen_retained_timings_in_new_representation(key):
    r, j = check(key)
    with pytest.raises(ValueError):
        MappedEngineResult.model_validate(r)
    assert len(r.observations.queue_membership.records) == 2 * len(r.observations.jobs.records)


@pytest.mark.parametrize(
    "fault",
    [
        "raw",
        "clock_missing",
        "owned",
        "queue_domain",
        "queue_zero_missing",
        "release_phase",
        "completion_phase",
        "zero_link",
        "stale_cause",
    ],
)
def test_discriminating_baseline_fault_restoration(fault):
    key = {"zero_link": "S08", "stale_cause": "S12", "completion_phase": "S07"}.get(fault, "S06")
    r, j = check(key)
    bad = copy.deepcopy(r)
    if fault == "raw":
        c = bad.observations.clocks.records[0]
        bad.observations.clocks = bad.observations.clocks.model_copy(
            update={"records": (c.model_copy(update={"aligned_start_ps": 835}),)}
        )
    elif fault == "clock_missing":
        bad.observations.clocks = Observed[ClockObservation](status="observed", records=())
    elif fault == "owned":
        b = bad.observations.jobs.records[0]
        bad.observations.jobs.records = (b.model_copy(update={"end_ps": 1667}),)
    elif fault == "queue_domain":
        qs = bad.observations.queue_membership.records
        bad.observations.queue_membership = bad.observations.queue_membership.model_copy(
            update={"records": (qs[0].model_copy(update={"clock_domain": "core"}), *qs[1:])}
        )
    elif fault == "queue_zero_missing":
        bad.observations.queue_membership = bad.observations.queue_membership.model_copy(
            update={"records": bad.observations.queue_membership.records[1:]}
        )
    elif fault in ("release_phase", "completion_phase"):
        bad.observations.events.records = tuple(
            e.model_copy(update={"phase": 0 if fault == "release_phase" else 1})
            if e.kind == ("TASK_RELEASE" if fault == "release_phase" else "COMPUTE_DONE")
            else e
            for e in bad.observations.events.records
        )
    elif fault == "zero_link":
        xs = bad.observations.critical_path.records
        bad.observations.critical_path.records = (
            xs[0],
            xs[1].model_copy(update={"predecessor_id": "a"}),
        )
    else:
        bad.observations.jobs.records = tuple(
            x.model_copy(update={"blocking_predecessor_ids": ("a",)}) if x.job_id == "c" else x
            for x in bad.observations.jobs.records
        )
    with pytest.raises(
        ValueError, match="IncompleteObservations|InvalidResource|AttributionMismatch"
    ):
        validate(bad, j)
    validate(r, j)


def test_same_k06_02_job_raw_and_owned():
    case = dict(
        jobs=[
            ("a-wait", 1, 0, (), 0, 0, 835, 835, None),
            ("b-clock", 0, 835, ("a-wait",), 835, 835, 835, 0, 0),
        ],
        critical=[("service", "a-wait", 0, 835)],
        duration=835,
    )
    ev = [
        (0, 1, "a-wait", "R"),
        (0, 2, "a-wait", "G"),
        (835, 0, "a-wait", "C"),
        (835, 1, "b-clock", "L"),
        (835, 1, "b-clock", "D"),
        (835, 2, "b-clock", "G"),
        (835, 2, "b-clock", "C"),
    ]
    r, j = subrecords(
        case, {"a-wait": (), "b-clock": ("a-wait",)}, {"a-wait": None, "b-clock": "a-wait"}, ev
    )
    validate(r, j)
    c = r.observations.clocks.records[0]
    assert (c.grant_ps, c.aligned_start_ps, c.completion_ps) == (835, 1667, 835)
    for wrong in ({"aligned_start_ps": 835}, {"completion_ps": 1667}):
        bad = copy.deepcopy(r)
        bad.observations.clocks = bad.observations.clocks.model_copy(
            update={"records": (c.model_copy(update=wrong),)}
        )
        with pytest.raises(ValueError, match="IncompleteObservations"):
            validate(bad, j)
        validate(r, j)


def test_raw_overflow_does_not_hide_owned_positive_overflow():
    maximum = 2**64 - 1
    assert 18446744073709552000 > maximum
    assert 18446744073709553000 > 18446744073709552000
    case = dict(
        jobs=[("z", 0, maximum, (), maximum, maximum, maximum, 0, 0)],
        critical=[("release_offset", "z", 0, maximum)],
        duration=maximum,
    )
    events = [(maximum, 1, "z", "L"), (maximum, 2, "z", "G"), (maximum, 2, "z", "C")]
    r, j = subrecords(case, {"z": ()}, {"z": None}, events, frequency=10**9, raw={"z": None})
    validate(r, j)
    bad = copy.deepcopy(r)
    bad.observations.clocks = bad.observations.clocks.model_copy(
        update={"records": (r.observations.clocks.records[0].model_copy(update={"n_cycles": 1}),)}
    )
    positive = copy.deepcopy(j)
    positive.clock_setup = (j.clock_setup[0].model_copy(update={"n_cycles": 1}),)
    with pytest.raises(ValueError, match="IncompleteObservations"):
        validate(bad, positive)
    validate(r, j)
    j.freq_hz.core = 10**12
    c = r.observations.clocks.records[0]
    r.observations.clocks = r.observations.clocks.model_copy(
        update={
            "records": (
                c.model_copy(update={"raw_edge_outcome": "success", "aligned_start_ps": maximum}),
            )
        }
    )
    validate(r, j)
    positive = copy.deepcopy(j)
    positive.clock_setup = (j.clock_setup[0].model_copy(update={"n_cycles": 1}),)
    bad = copy.deepcopy(r)
    bad.observations.clocks = bad.observations.clocks.model_copy(
        update={"records": (r.observations.clocks.records[0].model_copy(update={"n_cycles": 1}),)}
    )
    with pytest.raises(ValueError, match="IncompleteObservations"):
        validate(bad, positive)
    validate(r, j)


def test_s08_positive_partition_retains_immediate_zero_bridge():
    r, j = check("S08")
    assert [
        (x.cause_job_id, x.predecessor_id, x.start_ps, x.end_ps)
        for x in r.observations.critical_path.records
    ] == [("a", None, 0, 3000), ("c", "z", 3000, 5000)]
    by_id = {x.job_id: x for x in r.observations.jobs.records}
    assert by_id["z"].blocking_predecessor_ids == ("a",)
    assert by_id["c"].blocking_predecessor_ids == ("z",)
    with pytest.raises(ValueError, match="AttributionMismatch"):
        CriticalInterval(
            kind="service",
            cause_job_id="z",
            predecessor_id="a",
            start_ps=3000,
            end_ps=3000,
            limiting_resource_id=0,
            category="overhead",
        )
    validate(r, j)


def test_phase_one_eligibility_is_canonical_not_notification_sequence():
    r, j = check("S09")
    events = list(r.observations.events.records)
    events[3], events[4] = (events[4], events[3])
    r.observations.events.records = tuple(
        (
            e.model_copy(update={"observation_ordinal": i, "event_seq": i})
            for i, e in enumerate(events)
        )
    )
    validate(r, j)
    assert [e.job_id for e in r.observations.events.records if e.kind == "OWNER_GRANT"] == [
        "a",
        "b",
        "c",
    ]


def test_notification_must_follow_its_zero_completion():
    r, j = check("S07")
    bad = copy.deepcopy(r)
    events = list(bad.observations.events.records)
    # At1000 phase2: grant b, notify c, complete b, grant c, complete c.
    # Final times, all causes, all counters and all (time,phase) ordering unchanged.
    events[6], events[7] = events[7], events[6]
    bad.observations.events.records = tuple(
        e.model_copy(update={"observation_ordinal": i}) for i, e in enumerate(events)
    )
    assert [(e.t_ps, e.phase) for e in bad.observations.events.records] == sorted(
        (e.t_ps, e.phase) for e in bad.observations.events.records
    )
    with pytest.raises(ValueError, match="IncompleteObservations"):
        validate(bad, j)
    validate(r, j)
