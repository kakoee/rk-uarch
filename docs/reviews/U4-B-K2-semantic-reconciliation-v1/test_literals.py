"""Mathematical witnesses and discriminating wrong laws; no native invocation."""

import copy

import pytest
from literals import CASES, CHOSEN, GRANT_ORDER, raw_edge


def verify_witness(case):
    jobs = {j[0]: j for j in case["jobs"]}
    assert len(jobs) == len(case["jobs"])
    for job in jobs.values():
        name, owner, release, deps, ready, grant, end, ps, cycles = job
        assert ready == max([release, *(jobs[d][6] for d in deps)])
        assert ready <= grant <= end
        if cycles is None:
            assert release == 0
            assert end == grant + ps
        else:
            assert ps == 0
            assert end == (grant if cycles == 0 else raw_edge(grant, cycles))
    assert max(j[6] for j in jobs.values()) == case["duration"]
    for owner, busy in case["busy"].items():
        pieces = sorted((j[5], j[6]) for j in jobs.values() if j[1] == owner and j[5] < j[6])
        assert all(a[1] <= b[0] for a, b in zip(pieces, pieces[1:], strict=False))
        assert sum(end - start for start, end in pieces) == busy
    cursor = 0
    for kind, cause, start, end in case["critical"]:
        assert start == cursor <= end
        row = jobs[cause]
        if kind == "release_offset":
            assert (start, end) == (0, row[2])
        else:
            assert kind == "service" and (start, end) == (row[5], row[6])
        cursor = end
    assert cursor == case["duration"]
    if case["duration"] == 0:
        assert case["critical"] == [] and all(x == 0 for x in case["busy"].values())


@pytest.mark.parametrize("case", list(CASES))
def test_literal_witness(case):
    verify_witness(CASES[case])


def test_raw_edge_and_owned_zero_are_distinct():
    assert raw_edge(835, 0) == 1667
    assert CASES["S06-off-edge-owned-zero"]["jobs"][0][6] == 835
    assert 1667 - 835 == 832
    assert raw_edge(834, 0) == 834
    assert raw_edge(835, 1) == 2500
    assert raw_edge(834, 1) == 1667
    assert raw_edge(835, 0) != 835  # omit primitive alignment
    assert CASES["S06-off-edge-owned-zero"]["duration"] != raw_edge(835, 0)  # align owned zero
    assert raw_edge(834, 0) != 1667  # strictly-after primitive
    assert raw_edge(835, 1) != 3 * 833  # rounded period


@pytest.mark.parametrize(
    ("case", "job", "field", "wrong"),
    [
        ("S01-late-release-positive", "c", 4, 0),
        ("S02-dependency-before-release", "c", 4, 500),
        ("S03-dependency-after-release", "c", 4, 835),
        ("S04-busy-owner-positive", "c", 5, 835),
        ("S04-busy-owner-positive", "c", 6, 2500),
        ("S05-busy-owner-zero", "z", 6, 835),
        ("S06-off-edge-owned-zero", "z", 6, 1667),
        ("S08-zero-bridge", "z", 5, 1000),
        ("S12-idle-owner-history", "c", 4, 500),
        ("S14-on-edge-positive", "c", 6, 2500),
    ],
)
def test_discriminating_wrong_laws(case, job, field, wrong):
    verify_witness(CASES[case])
    altered = copy.deepcopy(CASES[case])
    altered["jobs"] = [list(row) for row in altered["jobs"]]
    next(row for row in altered["jobs"] if row[0] == job)[field] = wrong
    with pytest.raises(AssertionError):
        verify_witness(altered)
    verify_witness(CASES[case])


def test_idle_and_busy_are_not_interchangeable():
    c = CASES["S02-dependency-before-release"]
    assert c["critical"][0] == ("release_offset", "c", 0, 835)
    assert c["busy"] == {0: 1665, 1: 500}
    assert 835 - 500 == 335  # globally idle gap, unlike835 critical release offset
    assert sum(c["busy"].values()) == 2165 != c["duration"]
    c = CASES["S12-idle-owner-history"]
    assert 2000 - 500 == 1500  # owner0 idle; owner1 is busy
    assert c["critical"][0][1] == "b"  # stale owner job a is not a blocker
    for fault in ("busy", "critical"):
        changed = copy.deepcopy(c)
        if fault == "busy":
            changed["busy"][0] += 1500
        else:
            changed["critical"][0] = ("service", "a", 0, 2000)
        with pytest.raises(AssertionError):
            verify_witness(changed)


def test_zero_partition_and_inline_partial_order():
    assert CASES["S10-all-zero-at-zero"]["critical"] == []
    assert len(CASES["S10-all-zero-at-zero"]["jobs"]) == 3
    # Literal logical transitions, not manufactured EventObservation/native result bytes.
    transitions = [
        (1000, 0, "release/complete"),
        (1000, 1, "ready"),
        (1000, 2, "grant b"),
        (1000, 2, "complete b"),
        (1000, 2, "ready c inline"),
        (1000, 2, "grant c"),
        (1000, 2, "complete c"),
    ]
    assert [(t, phase) for t, phase, _ in transitions] == sorted(
        (t, phase) for t, phase, _ in transitions
    )
    wrong = list(transitions)
    wrong[3] = (1000, 0, "retroactive complete b")
    assert [(t, phase) for t, phase, _ in wrong] != sorted((t, phase) for t, phase, _ in wrong)
    # Sorting a zero closure by owner would be an invalid rewrite of actual causal order.
    owner_order = [1, 0]
    assert sorted(owner_order) != owner_order


def verify_links(case, order, chosen):
    """Check finite witnesses, never schedule jobs or construct a result."""
    jobs = {j[0]: j for j in case["jobs"]}
    assert len(order) == len(jobs) and set(order) == set(jobs) == set(chosen)
    seen = set()
    previous = {}
    for name in order:
        j = jobs[name]
        assert set(j[3]) <= seen
        # Among jobs already enabled by this dispatch, compare ready time then ID.
        waiting = [
            k
            for k in jobs.values()
            if k[0] not in seen and k[1] == j[1] and set(k[3]) <= seen and k[4] <= j[5]
        ]
        assert name == min(waiting, key=lambda k: (k[4], k[0]))[0]
        candidates = set(j[3]) | ({previous[j[1]]} if j[1] in previous else set())
        tight = sorted(k for k in candidates if jobs[k][6] == j[5])
        assert set(tight) <= seen  # no forward/same-time causal cycles
        assert chosen[name] == (tight[0] if tight else None)
        if not tight:
            assert j[5] == j[2]  # no unexplained gap on the chosen causal chain
        previous[j[1]] = name
        seen.add(name)
    service = [r[1] for r in case["critical"] if r[0] == "service"]
    for left, right in zip(service, service[1:], strict=False):
        assert chosen[right] == left
    if case["duration"]:
        terminal = min(j[0] for j in jobs.values() if j[6] == case["duration"])
        # Root zero jobs at a late release need only the release-offset interval.
        assert (service[-1] if service else case["critical"][-1][1]) == terminal
        if service:
            assert chosen[service[0]] is None


@pytest.mark.parametrize("case", list(CASES))
def test_literal_causality_and_fifo(case):
    verify_links(CASES[case], GRANT_ORDER[case], CHOSEN[case])


def test_wrong_fifo_stale_cause_and_tie_refuse_then_restore():
    for key, wrong in [
        ("S09-same-ready-fifo-zero", ("a", "c", "b")),
        ("S17-oldest-ready-before-id", ("a", "b", "z")),
    ]:
        verify_links(CASES[key], GRANT_ORDER[key], CHOSEN[key])
        with pytest.raises(AssertionError):
            verify_links(CASES[key], wrong, CHOSEN[key])
        verify_links(CASES[key], GRANT_ORDER[key], CHOSEN[key])
    for key, wrong in [
        ("S12-idle-owner-history", "a"),
        ("S16-equal-owner-dependency-causes", "b"),
        ("S11-release-dependency-tie", None),
    ]:
        changed = dict(CHOSEN[key], c=wrong)
        verify_links(CASES[key], GRANT_ORDER[key], CHOSEN[key])
        with pytest.raises(AssertionError):
            verify_links(CASES[key], GRANT_ORDER[key], changed)
        verify_links(CASES[key], GRANT_ORDER[key], CHOSEN[key])


def test_all_zero_has_one_partition_representation():
    case = CASES["S10-all-zero-at-zero"]
    verify_witness(case)
    changed = copy.deepcopy(case)
    changed["critical"] = [("service", "a", 0, 0)]
    with pytest.raises(AssertionError):
        verify_witness(changed)
    verify_witness(case)
