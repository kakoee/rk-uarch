"""Independent nonpreemptive FIFO-ready matrix arbitration; no engine imports."""

from collections import defaultdict
from typing import Any

from validation.component.checks import need


def check_matrix_order(job: dict[str, Any], result: dict[str, Any]) -> None:
    graph = job["mapped_point"]["task_graph"]
    need(graph["arbitration"] == "fifo-ready/1", "matrix arbitration contract")
    observed = {j["job_id"]: j for j in result["observations"]["jobs"]["records"]}
    queues: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for task in graph["jobs"]:
        if task["kind"] != "compute":
            continue
        ready = max(
            (
                observed[e["before"]]["end_ps"]
                for e in graph["dependencies"]
                if e["after"] == task["id"]
            ),
            default=0,
        )
        need(observed[task["id"]]["ready_ps"] == ready, "matrix dependency readiness")
        queues[task["core_id"]].append((ready, task["id"]))
    # Matrix ownership spans all four phases, including receiving-clock alignment.
    # Dependencies establish readiness; the reported order cannot supply the oracle.
    for queue in queues.values():
        previous = 0
        for ready, tid in sorted(queue):
            row = observed[tid]
            need(row["start_ps"] == max(ready, previous), "matrix FIFO-ready grant")
            previous = row["end_ps"]
