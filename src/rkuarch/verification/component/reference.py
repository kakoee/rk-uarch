"""Packaged model-3 observation checker. Fraction arithmetic; no mapper/native imports.

Checks supplied observations against independent local laws. It does not schedule work
or generate durations, and deterministic agreement is not TPU accuracy evidence.
"""

from collections import Counter, defaultdict
from fractions import Fraction
from math import ceil, prod
from typing import Any

from uarch_contract.mapped import require


def check_reference(job: Any, result: Any) -> Any:
    b = job["workload_closure"]
    g = b["points"][0]["task_graph"]
    h = {k: Fraction(str(v["value"])) for k, v in b["hardware_spec"].items() if isinstance(v, dict)}
    obs = result["observations"]
    tasks = [None] + g["jobs"]
    records = obs["activities"]
    by_sequence = defaultdict(list)
    by_task = defaultdict(list)
    owners = defaultdict(list)
    for i, x in enumerate(records):
        require(0 <= x["task"] < len(tasks), "IncompleteObservations", "task index")
        require(
            x["ready_ps"] <= x["start_ps"] <= x["end_ps"], "IncompleteObservations", "time order"
        )
        by_sequence[x["sequence"]].append((i, x))
        by_task[x["task"]].append((i, x))
        if x["occupies"]:
            owners[x["owner"]].append(x)
    require(set(by_task) == set(range(len(tasks))), "IncompleteObservations", "missing task")
    require(
        set(by_sequence) == set(range(len(obs["sequences"]))),
        "IncompleteObservations",
        "missing sequence",
    )
    require(len(obs["jobs"]) == len(tasks), "IncompleteObservations", "job count")
    task_sequences = defaultdict(list)
    for s, seq in enumerate(obs["sequences"]):
        task_sequences[seq[0]].append(s)
    consumed = {
        "tensorcore_count",
        "mxu_count",
        "mxu_rows",
        "mxu_cols",
        "hbm_max_outstanding",
        "bf16_mxu_mac_per_s",
        "int8_mxu_mac_per_s",
        "bf16_peak_ops_per_s",
        "int8_peak_ops_per_s",
        "hbm_capacity_bytes",
        "vmem_capacity_bytes",
        "smem_capacity_bytes",
        "kernel_startup_ps",
    }
    for task in g["jobs"]:
        kind = task["kind"]
        if kind == "compute":
            consumed.update(("scalar_op_ps", "matrix_fill_equivalent_macs"))
        elif kind == "vector":
            consumed.update(("scalar_op_ps", "vector_group_startup_ps", "vector_tile_ps"))
            for primitive_record in task["primitives"]:
                primitive_kind = primitive_record["kind"]
                if primitive_kind.startswith("reduction_") and primitive_record["cols"] > 1:
                    consumed.add("reduction_cost_ratio")
                elif primitive_kind in {"exp", "reciprocal", "rsqrt"}:
                    consumed.add(primitive_kind + "_cost_ratio")
        elif kind == "dma":
            consumed.update(
                (
                    "hbm_latency_ps",
                    "hbm_peak_bytes_per_s",
                    "vmem_bytes_per_s",
                    "hbm_issue_interval_ps",
                )
            )
        elif kind == "local_transfer":
            consumed.add("vmem_bytes_per_s")
        elif kind == "control":
            consumed.add("scalar_op_ps")
        elif kind == "barrier":
            consumed.add("barrier_latency_ps")
    expected_stubs = sorted(k for k in consumed if b["hardware_spec"][k]["provenance"] == "stub")
    require(
        result["consumed_stubs"] == expected_stubs, "IncompleteObservations", "consumed STUB inputs"
    )
    require(
        result["calibration"] == "stub"
        and result["error"] == "unknown"
        and result["energy"] == "unverified"
        and result["physical_transactions"] is None
        and result["energy_pj"] is None,
        "IncompleteObservations",
        "model claim limits",
    )
    expected_counts: Counter[str] = Counter()
    per_op: defaultdict[str, Counter[str]] = defaultdict(Counter)
    dma = []
    cursors: dict[Any, Fraction] = {}
    prior_owner: dict[Any, Any] = {}

    def check_phase(x: Any, name: Any, owner: Any, duration: Any, occupies: Any = True) -> Any:
        require(
            x["phase"] == name and x["owner"] == owner and x["occupies"] == occupies,
            "IncompleteObservations",
            "phase identity",
        )
        lo = Fraction(*x["ratio_start"])
        hi = Fraction(*x["ratio_end"])
        require(
            hi - lo == duration and ceil(hi) == x["end_ps"],
            "IncompleteObservations",
            "independent service law",
        )
        if name in {"r_hbm", "r_vmem"}:
            expected = max(cursors.get(owner, Fraction(0)), x["ready_ps"])
            require(lo == expected, "IncompleteObservations", "bandwidth cursor")
            cursors[owner] = hi
        else:
            require(lo == x["start_ps"], "IncompleteObservations", "service start")

    # In actual dispatch order, validate every owner-service cursor without replaying scheduling.
    for x in records:
        if x["phase"] in {"r_hbm", "r_vmem"}:
            lo = Fraction(*x["ratio_start"])
            hi = Fraction(*x["ratio_end"])
            require(
                lo == max(cursors.get(x["owner"], Fraction(0)), x["ready_ps"]),
                "IncompleteObservations",
                "rational cursor",
            )
            cursors[x["owner"]] = hi
        if x["occupies"]:
            prev = prior_owner.get(x["owner"])
            require(
                x["start_ps"] == max(x["ready_ps"], 0 if prev is None else prev["end_ps"]),
                "IncompleteObservations",
                "owner earliest grant",
            )
            prior_owner[x["owner"]] = x
    cursors = {}

    def primitive(p: Any) -> Any:
        k = p["kind"]
        r = p["rows"]
        c = p["cols"]
        repeat = p["repeat"] * p["leading"]
        counts: Counter[str] = Counter()
        if k.startswith("reduction_"):
            active = c
            tiles = 0
            while active > 1:
                active = (active + 1) // 2
                tiles += ((r + 7) // 8) * ((active + 127) // 128) * repeat
            counts["useful_" + k] = r * (c - 1) * repeat
            counts["issued_" + k] = tiles * 1024
            service = tiles * h["reduction_cost_ratio"] * h["vector_tile_ps"]
        else:
            tiles = ((r + 7) // 8) * ((c + 127) // 128) * repeat
            counts["useful_" + k] = r * c * repeat
            counts["issued_" + k] = tiles * 1024
            service = tiles * h["vector_tile_ps"] * h.get(k + "_cost_ratio", 1)
        return service, counts

    # Local law tests in sequence order. Cursor ordering was checked above separately.
    def local(x: Any, name: Any, owner: Any, duration: Any, occupies: Any = True) -> Any:
        require(
            x["phase"] == name and x["owner"] == owner and x["occupies"] == occupies,
            "IncompleteObservations",
            "phase identity",
        )
        lo = Fraction(*x["ratio_start"])
        hi = Fraction(*x["ratio_end"])
        require(
            hi - lo == duration and ceil(hi) == x["end_ps"],
            "IncompleteObservations",
            "service arithmetic",
        )
        if name not in {"r_hbm", "r_vmem"}:
            require(lo == x["start_ps"], "IncompleteObservations", "start law")

    for task_index, task in enumerate(tasks):
        seqs = task_sequences[task_index]
        require(bool(seqs), "IncompleteObservations", "sequence coverage")
        if task is None:
            require(
                len(seqs) == 1 and len(by_sequence[seqs[0]]) == 1,
                "IncompleteObservations",
                "one startup",
            )
            local(by_sequence[seqs[0]][0][1], "r_startup", 8, h["kernel_startup_ps"])
            continue
        counts: Counter[str] = Counter()
        kind = task["kind"]
        if kind == "dma":
            expected_sizes = []
            for span in task["spans"]:
                size = span["payload_bytes"]
                expected_sizes.extend(
                    [8192] * (size // 8192) + ([size % 8192] if size % 8192 else [])
                )
            require(
                [obs["sequences"][s][3] for s in seqs] == expected_sizes,
                "IncompleteObservations",
                "payload tails",
            )
            for s, size in zip(seqs, expected_sizes, strict=True):
                xs = [x for _, x in by_sequence[s]]
                write = task["direction"] == "write"
                require(len(xs) == 3, "IncompleteObservations", "DMA phases")
                if write:
                    local(xs[0], "r_vmem", 6, size * 10**12 / h["vmem_bytes_per_s"])
                    xs = xs[1:]
                local(xs[0], "r_latency", 7, h["hbm_latency_ps"], False)
                local(xs[1], "r_hbm", 7, size * 10**12 / h["hbm_peak_bytes_per_s"])
                if not write:
                    local(xs[2], "r_vmem", 6, size * 10**12 / h["vmem_bytes_per_s"])
                dma.append((obs["sequences"][s][1], xs[1]["end_ps"], s))
            size = task["payload_bytes"]
            counts["hbm_" + task["direction"] + "_bytes"] += size
            counts["vmem_bytes"] += size
        else:
            require(len(seqs) == 1, "IncompleteObservations", "one compute/control sequence")
            xs = [x for _, x in by_sequence[seqs[0]]]
            if kind == "compute":
                require(len(xs) == 2, "IncompleteObservations", "matrix phases")
                local(xs[0], "r_dispatch", 4, h["scalar_op_ps"])
                d = task["tile_extents"]
                precision = "int8" if task["accumulator_dtype"] == "int32" else "bf16"
                local(
                    xs[1],
                    "r_mxu",
                    task["matrix_engine_index"],
                    (d["M"] * 128 * 128 + h["matrix_fill_equivalent_macs"])
                    * 10**12
                    / h[precision + "_mxu_mac_per_s"],
                )
                mac = prod(d.values())
                if task["valid_pairs"] is not None:
                    mac = task["valid_pairs"] * (d["K"] if task["member"] == "qk" else d["N"])
                counts["matrix_ops"] = 2 * mac
                counts["issued_matrix_ops"] = 2 * d["M"] * 128 * 128
            elif kind == "vector":
                local(xs[0], "r_dispatch", 4, h["scalar_op_ps"])
                local(xs[1], "r_vector_setup", 5, h["vector_group_startup_ps"])
                index = 2
                for p in task["primitives"]:
                    service, c = primitive(p)
                    counts.update(c)
                    if p["kind"].startswith("reduction_"):
                        active = p["cols"]
                        while active > 1:
                            active = (active + 1) // 2
                            stage = (
                                ((p["rows"] + 7) // 8)
                                * ((active + 127) // 128)
                                * p["repeat"]
                                * p["leading"]
                                * h["vector_tile_ps"]
                                * h["reduction_cost_ratio"]
                            )
                            require(
                                index < len(xs), "IncompleteObservations", "reduction stage missing"
                            )
                            local(xs[index], "r_reduction", 5, stage)
                            index += 1
                    else:
                        require(index < len(xs), "IncompleteObservations", "primitive missing")
                        local(xs[index], "r_vector", 5, service)
                        index += 1
                require(index == len(xs), "IncompleteObservations", "vector phase count")
            elif kind == "local_transfer":
                require(len(xs) == 1, "IncompleteObservations")
                local(
                    xs[0],
                    "r_vmem",
                    6,
                    task["source"]["size_bytes"] * 10**12 / h["vmem_bytes_per_s"],
                )
                counts["vmem_bytes"] = task["source"]["size_bytes"]
            elif kind == "control":
                require(len(xs) == 1, "IncompleteObservations")
                local(xs[0], "r_control", 4, task["instructions"] * h["scalar_op_ps"])
                counts["scalar_instructions"] = task["instructions"]
            else:
                require(len(xs) == 1, "IncompleteObservations")
                local(xs[0], "r_barrier", 8, h["barrier_latency_ps"])
        expected_counts.update(counts)
        per_op[task["op_id"]].update(counts)
    for op in b["source"]["ops"]:
        d = op["spec"]["dimensions"]
        kind = op["spec"]["operator"]
        matrix = vector = 0
        if kind in {
            "q_projection",
            "k_projection",
            "v_projection",
            "output_projection",
            "ffn_up",
            "ffn_gate",
            "ffn_down",
        }:
            matrix = 2 * d["M"] * d["K"] * d["N"]
        elif kind in {"normalization", "activation"}:
            vector = 6 * d["M"] * d["D"]
        elif kind == "residual_addition":
            vector = d["M"] * d["D"]
        elif kind == "rotary_embedding":
            vector = 3 * d["B"] * d["S"] * d["H"] * d["R"]
        elif kind == "attention_fused":
            pairs = (
                d["B"]
                * d["Hq"]
                * (d["S"] * (d["S"] + 1) // 2 if d["S"] == d["T"] else d["S"] * d["T"])
            )
            matrix = 4 * pairs * d["D"]
            vector = 5 * pairs
        elif kind == "stream_read_sum":
            vector = d["E"] - 1
        elif kind == "scalar_add":
            vector = 1
        for key, value in (("semantic_matrix_ops", matrix), ("semantic_vector_ops", vector)):
            expected_counts[key] += value
            per_op[op["id"]][key] += value
    require(
        result["counts"].keys() <= expected_counts.keys()
        and expected_counts == Counter(result["counts"])
        and per_op.keys() == result["per_op_counts"].keys()
        and all(
            result["per_op_counts"][key].keys() <= value.keys()
            and value == Counter(result["per_op_counts"][key])
            for key, value in per_op.items()
        ),
        "IncompleteObservations",
        "completed work",
    )
    ids = {t["id"]: i + 1 for i, t in enumerate(g["jobs"])}
    before = defaultdict(list)
    for edge in g["dependencies"]:
        before[ids[edge["after"]]].append(ids[edge["before"]])
    for j in range(1, len(tasks)):
        ready = max((obs["jobs"][i][2] for i in before[j]), default=obs["jobs"][0][2])
        require(obs["jobs"][j][0] == ready, "IncompleteObservations", "dependency readiness")
    for j, xs in by_task.items():
        require(
            obs["jobs"][j][1] == min(x["start_ps"] for _, x in xs)
            and obs["jobs"][j][2] == max(x["end_ps"] for _, x in xs),
            "IncompleteObservations",
            "job endpoints",
        )
    for s, xs in by_sequence.items():
        task_index = obs["sequences"][s][0]
        task = tasks[task_index]
        job_ready = obs["jobs"][task_index][0]
        first_ready = xs[0][1]["ready_ps"]
        hbm_read = task is not None and task["kind"] == "dma" and task["direction"] == "read"
        # Reads may wait for the issue FIFO/window; other sequences enter at job readiness.
        require(
            obs["jobs"][task_index][1] >= job_ready
            and (first_ready >= job_ready if hbm_read else first_ready == job_ready),
            "IncompleteObservations",
            "first activity dependency readiness",
        )
        require(
            obs["sequences"][s][2] == xs[-1][1]["end_ps"],
            "IncompleteObservations",
            "sequence completion",
        )
        for (_, a), (_, z) in zip(xs, xs[1:], strict=False):
            require(
                z["ready_ps"]
                == (obs["sequences"][s][1] if z["phase"] == "r_latency" else a["end_ps"]),
                "IncompleteObservations",
                "sequence readiness",
            )
    dma.sort()
    active = []
    previous = None
    previous_issue: dict[int, int | None] = {}
    waited_for_credit = set()
    last_sequence: int | None = None
    import heapq

    expected_order = []
    for _issue, _end, s in dma:
        task_index = obs["sequences"][s][0]
        task = tasks[task_index]
        ready = (
            obs["jobs"][task_index][0]
            if task["direction"] == "read"
            else by_sequence[s][0][1]["end_ps"]
        )
        relative = task_sequences[task_index].index(s)
        expected_order.append((ready, f"{task['id']}:{relative:08d}", s))
    require(
        [s for _, _, s in dma] == [s for _, _, s in sorted(expected_order)],
        "IncompleteObservations",
        "issue FIFO",
    )
    request_ready = {s: r for r, _, s in expected_order}
    for issue, end, s in dma:
        earliest = max(
            request_ready[s], 0 if previous is None else ceil(previous + h["hbm_issue_interval_ps"])
        )
        while active and active[0] <= earliest:
            heapq.heappop(active)
        if len(active) >= h["hbm_max_outstanding"]:
            waited_for_credit.add(s)
            earliest = max(earliest, active[0])
            while active and active[0] <= earliest:
                heapq.heappop(active)
        require(issue == earliest, "IncompleteObservations", "earliest issue/window release")
        previous_issue[s] = last_sequence
        last_sequence = s
        previous = issue
        heapq.heappush(active, end)
        require(
            next(x["start_ps"] for _, x in by_sequence[s] if x["phase"] == "r_latency") == issue,
            "IncompleteObservations",
            "latency begins at issue",
        )
    require(
        result["duration_ps"] == max(j[2] for j in obs["jobs"]),
        "IncompleteObservations",
        "duration",
    )
    require(
        obs["priming_iterations"] == b["points"][0]["priming_iterations"],
        "IncompleteObservations",
        "priming count",
    )
    from uarch_contract.hashing import content_hash

    persistent = sorted(x["id"] for x in g["buffers"] if x["persistent"])
    require(
        obs["persistent_before"] == (persistent if obs["priming_iterations"] else [])
        and obs["persistent_after"] == persistent,
        "IncompleteObservations",
        "metadata residency",
    )
    require(
        obs["context_before"] == b["source"]["context_before"]
        and obs["context_after"] == b["source"]["context_after"],
        "IncompleteObservations",
        "fixed logical context",
    )
    for when in ("before", "after"):
        state = dict(
            context_before=obs["context_before"],
            context_after=obs["context_after"],
            persistent_metadata=obs["persistent_" + when],
            reload="payload-every-invocation",
        )
        require(
            content_hash(state) == obs["state_" + when], "IncompleteObservations", "state identity"
        )
    allocations = []
    for buffer in g["buffers"]:
        start = (
            0
            if buffer["persistent"] or buffer["initial_residency"] == "preloaded"
            else obs["jobs"][ids[buffer["producer_id"]]][1]
            if buffer["producer_id"]
            else 0
        )
        end = (
            result["duration_ps"]
            if buffer["persistent"] or not buffer["final_consumer_ids"]
            else max(obs["jobs"][ids[j]][2] for j in buffer["final_consumer_ids"])
        )
        allocations.append([start, end])
    require(
        obs["allocation_intervals"] == allocations, "IncompleteObservations", "allocation lifetimes"
    )
    sequence_prior: dict[int, int] = {}
    resource_prior: dict[int, int] = {}
    for i, x in enumerate(records):
        for prior, cause in x["causes"]:
            require(0 <= prior < i, "IncompleteObservations", "cause index")
            parent = records[prior]
            if cause == "sequence":
                valid = sequence_prior.get(x["sequence"]) == prior
            elif cause == "resource":
                valid = x["occupies"] and resource_prior.get(x["owner"]) == prior
            elif cause == "dependency":
                valid = (
                    parent["task"] in (before[x["task"]] or [0])
                    and parent["end_ps"] == obs["jobs"][parent["task"]][2]
                )
            elif cause == "issue_spacing":
                valid = (
                    x["phase"] == "r_latency"
                    and parent["phase"] == "r_latency"
                    and previous_issue.get(x["sequence"]) == parent["sequence"]
                )
            elif cause == "credit":
                valid = (
                    x["phase"] == "r_latency"
                    and parent["phase"] == "r_hbm"
                    and x["sequence"] in waited_for_credit
                )
            else:
                valid = False
            require(valid, "IncompleteObservations", "cause relationship")
        sequence_prior[x["sequence"]] = i
        if x["occupies"]:
            resource_prior[x["owner"]] = i
    for i, x in enumerate(records):
        for prior, cause in x["causes"]:
            require(
                prior < i
                and cause in {"sequence", "resource", "dependency", "credit", "issue_spacing"},
                "IncompleteObservations",
                "cause identity",
            )
            require(
                (
                    ceil(records[prior]["start_ps"] + h["hbm_issue_interval_ps"])
                    if cause == "issue_spacing"
                    else records[prior]["end_ps"]
                )
                == x["start_ps"],
                "IncompleteObservations",
                "cause time",
            )
    demand: defaultdict[int, Fraction] = defaultdict(Fraction)
    for x in records:
        if x["occupies"] and x["phase"] != "r_startup":
            demand[x["owner"]] += Fraction(*x["ratio_end"]) - Fraction(*x["ratio_start"])
    if dma:
        demand[9] = max(0, len(dma) - 1) * h["hbm_issue_interval_ps"]
    require(
        result["duration_ps"]
        >= ceil(h["kernel_startup_ps"]) + ceil(max(demand.values(), default=Fraction(0))),
        "IncompleteObservations",
        "resource-demand lower bound",
    )
    cursor = 0
    for part in obs["critical_path"]:
        x = records[part["activity"]]
        require(
            part["start_ps"] == cursor and part["end_ps"] >= cursor,
            "IncompleteObservations",
            "critical path partition",
        )
        if part["cause"] == "service":
            require(
                part["start_ps"] == x["start_ps"] and part["end_ps"] <= x["end_ps"],
                "IncompleteObservations",
                "critical service identity",
            )
        else:
            require(
                any(
                    cause == "issue_spacing" and records[prior]["start_ps"] == cursor
                    for prior, cause in x["causes"]
                )
                and part["end_ps"] == x["start_ps"],
                "IncompleteObservations",
                "critical issue identity",
            )
        cursor = part["end_ps"]
    require(cursor == result["duration_ps"], "IncompleteObservations", "critical parts sum")
    return True
