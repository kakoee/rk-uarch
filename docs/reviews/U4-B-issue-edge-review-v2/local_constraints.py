"""B literal opportunity witnesses; synthetic helper tests, not mapped/native outputs."""

import json
import sys
from copy import deepcopy
from pathlib import Path

from validation.component.issue_checks import check_reservation_opportunities, credit_predecessors

from validation.component.checks import CheckFailure

records = []


def check(label, witness, refuse=False):
    try:
        check_reservation_opportunities(**witness)
        assert not refuse, label + " unsafely accepted"
        records.append(dict(name=label, outcome="pass"))
    except CheckFailure as error:
        assert refuse, (label, str(error))
        records.append(dict(name=label, outcome="intended helper refusal", detail=str(error)))


def opportunity(i, t, c, granted):
    return dict(opportunity_ordinal=i, t_ps=t, event_cursor=c, granted_request_ids=granted)


for cap, independent in ((1, False), (2, False), (1, True)):
    simultaneous = cap == 2 or independent
    rows = {
        "a": dict(job_id="a", dma_engine_id=0, reservation_ps=0),
        "b": dict(
            job_id="b", dma_engine_id=int(independent), reservation_ps=0 if simultaneous else 60000
        ),
    }
    w = dict(
        rows=rows,
        jobs={key: dict(ready_ps=0) for key in rows},
        limit=cap,
        opportunities=[
            opportunity(0, 0, 0, ["a", "b"] if simultaneous else ["a"]),
            opportunity(1, 60000, 1, [] if simultaneous else ["b"]),
            opportunity(2, 120000, 2, []),
        ],
        events=[
            dict(observation_ordinal=i, t_ps=t, phase=0) for i, t in enumerate((60000, 120000))
        ],
        job_ends={"a": 0, "b": 1},
        request_ends={"a": 0, "b": 1},
        dependencies={},
    )
    label = f"cap{cap}-independent{independent}"
    check(label, w)
    if cap == 2:
        bad = deepcopy(w)
        bad["opportunities"][0]["granted_request_ids"].reverse()
        check("same-opportunity-reversed-ready-tie", bad, True)
    elif not independent:
        bad = deepcopy(w)
        bad["rows"]["b"]["reservation_ps"] = 0
        bad["opportunities"][0]["granted_request_ids"] = ["a", "b"]
        bad["opportunities"][1]["granted_request_ids"] = []
        check("already-reserved-capacity-not-available", bad, True)

for phase in (0, 2):
    # Producer p has two sequence terminals at the same time. One free credit after
    # the first inline terminal cannot make c eligible until p's SECOND terminal.
    w = dict(
        rows={
            "p.0": dict(job_id="p", dma_engine_id=0, reservation_ps=0),
            "p.1": dict(job_id="p", dma_engine_id=0, reservation_ps=0),
            "c.0": dict(job_id="c", dma_engine_id=0, reservation_ps=60000),
        },
        jobs={"p": dict(ready_ps=0), "c": dict(ready_ps=60000)},
        limit=2,
        events=[
            dict(observation_ordinal=i, t_ps=t, phase=ph)
            for i, (t, ph) in enumerate(((60000, phase), (60000, phase), (120000, 0)))
        ],
        job_ends={"p": 1, "c": 2},
        request_ends={"p.0": 0, "p.1": 1, "c.0": 2},
        dependencies={"c": ["p"]},
    )
    w["opportunities"] = [opportunity(0, 0, 0, ["p.0", "p.1"])]
    if phase == 2:
        w["opportunities"].append(opportunity(1, 60000, 1, []))
    w["opportunities"] += [
        opportunity(len(w["opportunities"]), 60000, 2, ["c.0"]),
        opportunity(len(w["opportunities"]) + 1, 120000, 3, []),
    ]
    check("all-predecessor-terminals-phase" + str(phase), w)
    bad = deepcopy(w)
    if phase == 2:
        bad["opportunities"][1]["granted_request_ids"] = ["c.0"]
        bad["opportunities"][2]["granted_request_ids"] = []
        check("free-credit-but-predecessor-still-incomplete", bad, True)
    else:
        bad["opportunities"].insert(1, opportunity(1, 60000, 1, []))
        for i, o in enumerate(bad["opportunities"]):
            o["opportunity_ordinal"] = i
        check("split-phase-zero-batch", bad, True)

for ready, reserved, acquired, wanted in (
    (59999, 60000, 60000, {"old"}),
    (60000, 60000, 60000, set()),
    (60001, 60001, 61000, set()),
):
    rows = {
        "old": dict(job_id="old", dma_engine_id=0, reservation_ps=0, issue_ps=0, complete_ps=60000),
        "new": dict(
            job_id="new",
            dma_engine_id=0,
            reservation_ps=reserved,
            issue_ps=acquired,
            complete_ps=120000,
        ),
    }
    actual = credit_predecessors(
        "new", rows, {"old": dict(ready_ps=0), "new": dict(ready_ps=ready)}, 1
    )
    assert actual == wanted
    records.append(
        dict(
            name="strict-wait-ready-" + str(ready),
            outcome="pass",
            credit_predecessors=sorted(actual),
        )
    )
Path(sys.argv[1]).write_text(
    json.dumps(dict(label="independent synthetic helper literals only", records=records), indent=2)
    + "\n"
)
print(len(records), "bounded independent helper controls passed")
