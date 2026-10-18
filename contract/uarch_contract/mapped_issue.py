"""Structural /3 issue witnesses. Private proposal until exact human installation.

No native execution or independent-checker imports. /2 validation never calls here.
"""

from typing import Any

from .mapped import require


def validate_issue_observations(result: Any, job: Any) -> None:
    obs = result.observations
    tasks = {t.id: t for t in job.mapped_point.task_graph.jobs}
    jobs = {r.job_id: r for r in obs.jobs.records}
    acts = {a.activity_id: a for a in obs.activities.records}
    events = {e.observation_ordinal: e for e in obs.events.records}
    owners = {o.owner_id: o.resource for o in job.owners}
    declared = {
        f.request_id: (t, f) for t in tasks.values() if t.kind == "dma" for f in t.fragments
    }
    requests = {r.request_id: r for r in obs.dma.records if r.direction != "unicast"}
    require(requests.keys() == declared.keys(), "IncompleteObservations", "issue request inventory")
    require(
        all(r.reservation_ps is None for r in obs.dma.records if r.direction == "unicast"),
        "IncompleteObservations",
        "unicast has no credit reservation",
    )
    limit = int(job.workload_closure.hardware_spec.cores.core_type.dma.max_outstanding.value)
    engines = int(job.workload_closure.hardware_spec.cores.core_type.dma.engines.value)
    firsts = {}
    lasts = {}
    for req, row in requests.items():
        task, _ = declared[req]
        members = [a for a in acts.values() if a.request_id == req and a.job_id == task.id]
        issue = [a for a in members if a.subphase == "dma_issue"]
        alignment = [a for a in issue if a.kind == "alignment"]
        service = [a for a in issue if a.kind == "service"]
        require(
            len(alignment) == len(service) == 1,
            "IncompleteObservations",
            "exact issue phase inventory",
        )
        a, b = alignment[0], service[0]
        firsts[req] = a
        lasts[req] = max(members, key=lambda x: x.completion_ordinal)
        require(row.reservation_ps is not None, "IncompleteObservations", "missing reservation")
        require(
            (a.ready_ps, a.start_ps, a.end_ps)
            == (jobs[task.id].ready_ps, row.reservation_ps, row.issue_ps),
            "IncompleteObservations",
            "issue alignment binding",
        )
        require(
            (b.ready_ps, b.start_ps, b.end_ps) == (row.issue_ps, row.issue_ps, row.issue_ps),
            "IncompleteObservations",
            "atomic zero issue service",
        )
        require(
            a.completion_ordinal < b.dispatch_ordinal < b.completion_ordinal,
            "IncompleteObservations",
            "atomic issue endpoint order",
        )
        require(
            events[a.dispatch_ordinal].phase
            == events[b.dispatch_ordinal].phase
            == events[b.completion_ordinal].phase
            == 2,
            "IncompleteObservations",
            "issue phase2 dispatch",
        )
        require(
            events[a.completion_ordinal].phase == (0 if a.end_ps > a.start_ps else 2),
            "IncompleteObservations",
            "alignment completion phase",
        )
        require(
            row.credit_acquire_ps == row.issue_ps <= row.complete_ps == row.credit_release_ps,
            "IncompleteObservations",
            "acquired credit lifecycle",
        )
        require(
            jobs[task.id].ready_ps <= row.reservation_ps <= row.issue_ps,
            "IncompleteObservations",
            "reservation lifecycle",
        )
        for name, population, begin, end in (
            ("dma_waiting", "waiting", jobs[task.id].ready_ps, row.reservation_ps),
            ("dma_pending", "pending", row.reservation_ps, row.issue_ps),
            ("dma_inflight", "inflight", row.issue_ps, row.complete_ps),
        ):
            qs = [
                q
                for q in obs.queue_membership.records
                if q.queue_id == f"{name}:{task.dma_engine_id}" and q.item_id == req
            ]
            require(len(qs) == 1, "IncompleteObservations", "issue population inventory")
            q = qs[0]
            require(
                (q.population, q.enter_ps, q.leave_ps, q.clock_domain, q.activity_id)
                == (population, begin, end, None, None),
                "IncompleteObservations",
                "issue population lifecycle",
            )
            require(
                owners[q.owner_id]
                == f"dma:{task.dma_engine_id // engines}:{task.dma_engine_id % engines}",
                "InvalidResource",
                "issue population owner",
            )
    # A reservation cursor is captured before the grant, independently of issue dispatch.
    opportunities = obs.reservation_opportunities.records
    require(bool(opportunities), "IncompleteObservations", "reservation opportunity inventory")
    granted = set()
    previous_cursor = -1
    for index, opportunity in enumerate(opportunities):
        cursor, time = opportunity.event_cursor, opportunity.t_ps
        require(
            opportunity.opportunity_ordinal == index
            and previous_cursor < cursor <= len(events)
            and (index != 0 or (cursor, time) == (0, 0)),
            "IncompleteObservations",
            "reservation opportunity order",
        )
        require(
            (cursor == 0 or events[cursor - 1].t_ps <= time)
            and (cursor == len(events) or time <= events[cursor].t_ps),
            "IncompleteObservations",
            "reservation cursor time",
        )
        for request_id in opportunity.granted_request_ids:
            require(
                request_id in requests and request_id not in granted,
                "IncompleteObservations",
                "reservation grant inventory",
            )
            row = requests[request_id]
            require(
                row.reservation_ps == time and cursor <= firsts[request_id].dispatch_ordinal,
                "IncompleteObservations",
                "reservation grant binding",
            )
            granted.add(request_id)
        previous_cursor = cursor
    require(granted == requests.keys(), "IncompleteObservations", "reservation grant inventory")
    # Reservations consume capacity before acquisition. Half-open intervals include
    # pending and acquired exactly once; conversion changes neither total nor owner.
    for engine in {r.dma_engine_id for r in requests.values()}:
        members = [r for r in requests.values() if r.dma_engine_id == engine]
        for time in {r.reservation_ps for r in members}:
            require(
                sum(r.reservation_ps <= time < r.complete_ps for r in members) <= limit,
                "IncompleteObservations",
                "pending plus acquired capacity",
            )
    cursors = {
        request: opportunity.event_cursor
        for opportunity in opportunities
        for request in opportunity.granted_request_ids
    }
    validate_reservation_capacity(requests, lasts, opportunities, limit)
    validate_credit_causes(requests, jobs, firsts, lasts, cursors, limit)
    # /3 makes job-start reservation-based; producer allocations follow that endpoint,
    # while unchanged terminal-reader laws determine free, including transport buffers.
    allocations = {a.buffer_id: a for a in obs.allocations.records}
    for buffer in job.mapped_point.task_graph.buffers:
        persistent = buffer.producer_id is None or (
            buffer.space == "accumulator" and job.workload_closure.mapping_policy.version == "1"
        )
        if not persistent:
            row = allocations[buffer.id]
            end = max((jobs[x].end_ps for x in buffer.final_consumer_ids), default=None)
            require(
                (row.allocate_ps, row.free_ps) == (jobs[buffer.producer_id].start_ps, end),
                "IncompleteObservations",
                "producer allocation endpoints",
            )


def validate_reservation_capacity(
    requests: dict[str, Any], lasts: dict[str, Any], opportunities: Any, limit: int
) -> None:
    """Necessary capacity join at actual reservation cursors; no grant scheduler."""
    granted: set[str] = set()
    for opportunity in opportunities:
        cursor = opportunity.event_cursor
        active = {request for request in granted if lasts[request].completion_ordinal >= cursor}
        for request in opportunity.granted_request_ids:
            active.add(request)
            engine = requests[request].dma_engine_id
            require(
                sum(requests[key].dma_engine_id == engine for key in active) <= limit,
                "IncompleteObservations",
                "reservation cursor capacity",
            )
        granted.update(opportunity.granted_request_ids)


def validate_credit_causes(
    requests: dict[str, Any],
    jobs: dict[str, Any],
    firsts: dict[str, Any],
    lasts: dict[str, Any],
    cursors: dict[str, int],
    limit: int,
) -> None:
    """Approved a1: all eligible same-time releases already observed at this cursor.

    This is an attribution set, not exclusive assignment of a particular released slot.
    Earlier opportunities do not remove an otherwise eligible same-time release.
    """
    terminals = {last.activity_id: last for last in lasts.values()}
    for request, row in requests.items():
        time, cursor = row.reservation_ps, cursors[request]
        prior = [
            old
            for key, old in requests.items()
            if key != request
            and old.dma_engine_id == row.dma_engine_id
            and old.reservation_ps < time <= old.complete_ps
        ]
        eligible = (
            {
                lasts[old.request_id].activity_id
                for old in prior
                if old.issue_ps <= time == old.complete_ps
                and lasts[old.request_id].completion_ordinal < cursor
            }
            if time > jobs[row.job_id].ready_ps and len(prior) == limit
            else set()
        )
        supplied = {p.activity_id for p in firsts[request].predecessors if p.relation == "credit"}
        require(
            all(
                key in terminals and terminals[key].completion_ordinal < cursor for key in supplied
            ),
            "AttributionMismatch",
            "credit predecessor before reservation opportunity",
        )
        require(supplied == eligible, "AttributionMismatch", "exact per-opportunity credit causes")
