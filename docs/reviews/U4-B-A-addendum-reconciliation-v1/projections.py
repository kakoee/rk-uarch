"""Finite B literal projections into A's proposed subrecords, NEVER EngineResults.

No scheduling, result constructor, native invocation or accepted authority exists here.
Each dispatch premise below is written explicitly; sequence labels are synthetic unique
structural labels, not a claim of executed schedule-time allocation.
"""

from types import SimpleNamespace as NS

from literals import CASES, CHOSEN
from uarch_contract.mapped import (
    ClockObservation,
    ClockSetup,
    CriticalInterval,
    EventObservation,
    FixedDelay,
    JobObservation,
    Observed,
    QueueObservation,
    ResourceInterval,
)

# R=root readiness, L=release, D=dependency notification, G=grant, C=completion.
KINDS = dict(
    R="TASK_READY", L="TASK_RELEASE", D="DEPENDENCY_READY", G="OWNER_GRANT", C="COMPUTE_DONE"
)
# Each row is (time, phase, job ID, kind). No event scheduler is used to produce it.
EVENTS = {
    "S01": [(835, 1, "c", "L"), (835, 2, "c", "G"), (2500, 0, "c", "C")],
    "S02": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (500, 0, "a", "C"),
        (500, 1, "c", "D"),
        (835, 1, "c", "L"),
        (835, 2, "c", "G"),
        (2500, 0, "c", "C"),
    ],
    "S03": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (835, 1, "c", "L"),
        (1000, 0, "a", "C"),
        (1000, 1, "c", "D"),
        (1000, 2, "c", "G"),
        (2500, 0, "c", "C"),
    ],
    "S04": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (835, 1, "c", "L"),
        (3000, 0, "a", "C"),
        (3000, 2, "c", "G"),
        (4167, 0, "c", "C"),
    ],
    "S05": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (835, 1, "z", "L"),
        (3000, 0, "a", "C"),
        (3000, 2, "z", "G"),
        (3000, 2, "z", "C"),
    ],
    "S06": [(835, 1, "z", "L"), (835, 2, "z", "G"), (835, 2, "z", "C")],
    "S07": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (1000, 0, "a", "C"),
        (1000, 1, "b", "L"),
        (1000, 1, "b", "D"),
        (1000, 2, "b", "G"),
        (1000, 2, "b", "C"),
        (1000, 2, "c", "D"),
        (1000, 2, "c", "G"),
        (1000, 2, "c", "C"),
    ],
    "S08": [
        (0, 1, "a", "R"),
        (0, 1, "p", "R"),
        (0, 2, "a", "G"),
        (0, 2, "p", "G"),
        (1000, 0, "p", "C"),
        (1000, 1, "z", "D"),
        (3000, 0, "a", "C"),
        (3000, 2, "z", "G"),
        (3000, 2, "z", "C"),
        (3000, 2, "c", "D"),
        (3000, 2, "c", "G"),
        (5000, 0, "c", "C"),
    ],
    "S09": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (1000, 0, "a", "C"),
        (1000, 1, "b", "L"),
        (1000, 1, "c", "D"),
        (1000, 2, "b", "G"),
        (1000, 2, "b", "C"),
        (1000, 2, "c", "G"),
        (1001, 0, "c", "C"),
    ],
    "S10": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (0, 2, "a", "C"),
        (0, 2, "b", "D"),
        (0, 2, "b", "G"),
        (0, 2, "b", "C"),
        (0, 2, "c", "D"),
        (0, 2, "c", "G"),
        (0, 2, "c", "C"),
    ],
    "S11": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (1000, 0, "a", "C"),
        (1000, 1, "c", "L"),
        (1000, 1, "c", "D"),
        (1000, 2, "c", "G"),
        (2500, 0, "c", "C"),
    ],
    "S12": [
        (0, 1, "a", "R"),
        (0, 1, "b", "R"),
        (0, 2, "a", "G"),
        (0, 2, "b", "G"),
        (500, 0, "a", "C"),
        (835, 1, "c", "L"),
        (2000, 0, "b", "C"),
        (2000, 1, "c", "D"),
        (2000, 2, "c", "G"),
        (3334, 0, "c", "C"),
    ],
    "S13": [(834, 1, "z", "L"), (834, 2, "z", "G"), (834, 2, "z", "C")],
    "S14": [(834, 1, "c", "L"), (834, 2, "c", "G"), (1667, 0, "c", "C")],
    "S15": [(0, 1, "a", "R"), (0, 2, "a", "G"), (835, 0, "a", "C")],
    "S16": [
        (0, 1, "a", "R"),
        (0, 1, "b", "R"),
        (0, 2, "a", "G"),
        (0, 2, "b", "G"),
        (1000, 0, "a", "C"),
        (1000, 0, "b", "C"),
        (1000, 1, "c", "D"),
        (1000, 2, "c", "G"),
        (1001, 0, "c", "C"),
    ],
    "S17": [
        (0, 1, "a", "R"),
        (0, 2, "a", "G"),
        (1, 1, "z", "L"),
        (3, 1, "b", "L"),
        (100, 0, "a", "C"),
        (100, 2, "z", "G"),
        (100, 2, "z", "C"),
        (100, 2, "b", "G"),
        (100, 2, "b", "C"),
    ],
}
ALIGNED = {0: 0, 100: 834, 834: 834, 835: 1667, 1000: 1667, 2000: 2500, 3000: 3334}


def project(key):
    name = next(k for k in CASES if k.startswith(key + "-"))
    case = CASES[name]
    tight = {k: (() if v is None else (v,)) for k, v in CHOSEN[name].items()}
    if key in ("S09", "S16"):
        tight["c"] = ("a", "b")
    return subrecords(case, tight, CHOSEN[name], EVENTS[key])


def subrecords(case, tight, chosen, events, frequency=1200000000, raw=None):
    """Translate supplied finite assertions only; no grants, times or causes computed."""
    declared = []
    records = []
    setups = []
    clocks = []
    for k, o, release, _deps, ready, grant, end, ps, cycles in case["jobs"]:
        declared.append(FixedDelay(kind="fixed_delay", id=k, owner_id=o, duration_ps=ps))
        records.append(
            JobObservation(
                job_id=k,
                owner_id=o,
                release_ps=release,
                ready_ps=ready,
                start_ps=grant,
                end_ps=end,
                blocking_predecessor_ids=tight[k],
                op_id=None,
                group_id=None,
                repeat_index=None,
                tile_origin=None,
                tile_extents=None,
                useful_matrix_ops=0,
                issued_matrix_ops=0,
                vector_arithmetic_ops=0,
                cast_ops=0,
            )
        )
        if cycles is not None:
            setups.append(ClockSetup(job_id=k, domain="core", start_ps=release, n_cycles=cycles))
            aligned = ALIGNED[grant] if raw is None else raw[k]
            clocks.append(
                ClockObservation(
                    job_id=k,
                    domain="core",
                    grant_ps=grant,
                    n_cycles=cycles,
                    raw_edge_outcome="TimeOverflow" if aligned is None else "success",
                    aligned_start_ps=aligned,
                    completion_ps=end,
                )
            )
    deps = tuple(NS(before=d, after=j[0]) for j in case["jobs"] for d in j[3])
    job = NS(
        clock_setup=tuple(setups),
        freq_hz=NS(core=frequency),
        mapped_point=NS(task_graph=NS(jobs=tuple(declared), dependencies=deps)),
    )
    by_id = {j.job_id: j for j in records}
    ev = tuple(
        EventObservation(
            event_seq=i,
            observation_ordinal=i,
            t_ps=t,
            phase=phase,
            target_id=by_id[k].owner_id,
            kind=KINDS[kind],
            job_id=k,
        )
        for i, (t, phase, k, kind) in enumerate(events)
    )
    queue = sorted(
        (
            QueueObservation(
                queue_id=f"owner:{j.owner_id}:{p}",
                item_id=j.job_id,
                population=p,
                enter_ps=a,
                leave_ps=b,
                owner_id=j.owner_id,
                clock_domain=None,
            )
            for j in records
            for p, a, b in [("waiting", j.ready_ps, j.start_ps), ("service", j.start_ps, j.end_ps)]
        ),
        key=lambda q: (q.queue_id, q.item_id, q.population),
    )
    intervals = sorted(
        (
            ResourceInterval(
                owner_id=j.owner_id,
                job_id=j.job_id,
                start_ps=j.start_ps,
                end_ps=j.end_ps,
                activity="fixed_delay",
                limiting_resource_id=j.owner_id,
                service_start_ps_ratio=None,
                service_end_ps_ratio=None,
            )
            for j in records
            if j.start_ps < j.end_ps
        ),
        key=lambda x: (x.owner_id, x.job_id),
    )
    critical = tuple(
        CriticalInterval(
            kind="release_idle" if kind == "release_offset" else "service",
            cause_job_id=k,
            start_ps=a,
            end_ps=b,
            predecessor_id=None if kind == "release_offset" else chosen[k],
            limiting_resource_id=None if kind == "release_offset" else by_id[k].owner_id,
            category="overhead",
        )
        for kind, k, a, b in case["critical"]
        if a < b
    )
    result = NS(
        duration_ps=case["duration"],
        simulator_metrics=NS(event_count=len(ev), max_live_events=1),
        observations=NS(
            jobs=NS(records=tuple(records)),
            events=NS(records=ev),
            clocks=Observed[ClockObservation](status="observed", records=tuple(clocks)),
            queue_membership=Observed[QueueObservation](status="observed", records=tuple(queue)),
            resource_intervals=NS(records=tuple(intervals)),
            critical_path=NS(records=critical),
            dma=NS(status="unrepresented"),
            transfers=NS(status="unrepresented"),
            allocations=NS(status="unrepresented"),
        ),
    )
    return result, job
