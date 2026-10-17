"""Independent arithmetic for the unapplied issue-reservation proposal, not human L1."""

import json
from fractions import Fraction

from validation.component.arithmetic import SERVICE, ceil, edge_after


def read_at(issue):
    request = edge_after(1_200_000_000, issue, 4)
    latency = edge_after(1_000_000_000, request, 48)
    channel = ceil(Fraction(latency) + SERVICE)
    response = edge_after(1_200_000_000, channel, 4)
    return edge_after(1_000_000_000, response, 1)


assert read_at(27000) == 86000
assert read_at(86000) == 146000
shared = [
    edge_after(1_000_000_000, edge_after(1_200_000_000, ceil(Fraction(79000) + n * SERVICE), 4), 1)
    for n in (1, 2)
]
assert shared == [86000, 89000]
print(
    json.dumps(
        dict(
            label="unapplied proposal arithmetic; no observed native result or human working",
            ready_ps=26667,
            cap1=dict(
                pending_before_edge=1,
                inflight_before_edge=0,
                issue_ps=[27000, 86000],
                complete_ps=[86000, 146000],
            ),
            cap2=dict(
                pending_before_edge=2,
                inflight_before_edge=0,
                issue_ps=[27000, 27000],
                complete_ps=shared,
            ),
        ),
        indent=2,
    )
)
