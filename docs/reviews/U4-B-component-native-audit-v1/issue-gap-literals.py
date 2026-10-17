"""Independent prospective issue-gap arithmetic; not human L1 or native output."""

import json
from fractions import Fraction

from validation.component.arithmetic import SERVICE, ceil, edge_after

rows = []
for write in (False, True):
    ready = edge_after(1_200_000_000, 0, 32)
    issue = edge_after(1_000_000_000, ready, 0)
    port = edge_after(1_000_000_000, issue, 1) if write else issue
    request = edge_after(1_200_000_000, port, 4)
    latency = edge_after(1_000_000_000, request, 48)
    channel = ceil(Fraction(latency) + SERVICE)
    response = edge_after(1_200_000_000, channel, 4)
    done = edge_after(1_000_000_000, response, 0 if write else 1)
    noc = request - port + response - channel
    memory = issue - ready + port - issue + latency - request + channel - latency + done - response
    expected = (
        (26667, 27000, 28000, 31667, 80000, 82250, 85834, 86000)
        if write
        else (26667, 27000, 27000, 30834, 79000, 81250, 85000, 86000)
    )
    assert (ready, issue, port, request, latency, channel, response, done) == expected
    assert (ready, memory, noc) == ((26667, 52082, 7251) if write else (26667, 51749, 7584))
    assert ready + memory + noc == done
    rows.append(
        dict(
            direction="write" if write else "read",
            dependency_ready_ps=ready,
            issue_ps=issue,
            port_or_issue_ps=port,
            request_arrival_ps=request,
            latency_end_ps=latency,
            channel_end_ps=channel,
            response_end_ps=response,
            complete_ps=done,
            proposed_causal_partition_ps=dict(sync=ready, memory=memory, noc=noc),
            payload_bytes=256,
            transaction_bytes=256,
            useful_matrix_ops=0,
            busy_issue_interval=None,
            issue_alignment_occupies_resource=False,
        )
    )
print(
    json.dumps(
        dict(
            label="independent prospective mathematical literals; not native result or human worksheet",  # noqa: E501
            rows=rows,
        ),
        indent=2,
    )
)
