"""Synthetic structural controls, never accepted records or native execution evidence."""

import copy
import json
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash, sha256

from rkuarch.engines.native.host import HostBindingError, _resolve
from rkuarch.engines.native.records import HostSelector

ROOT = Path(__file__).resolve().parents[2]


def scaffold(root: Path):
    def put(name, value):
        data = value if isinstance(value, bytes) else canonical_json(value).encode()
        (root / name).write_bytes(data)
        return {"path": name, "byte_hash": sha256(data)}

    # All subjects here are explicit synthetic test scaffolding. Neither the
    # installed selector nor a real executable is present, and nothing is run.
    raw = json.loads((ROOT / "contract/fixtures/mapped/kernel-job.json").read_bytes())
    common = put("synthetic.json", {"synthetic_test_only": True})
    source = {**put("source.rs", b"// synthetic test-only source"), "role": "rust"}
    profile = raw["profile"]
    registry = raw["registry"]
    cases = [
        {
            k: e[k]
            for k in (
                "case_id",
                "graph_hash",
                "point_hash",
                "hardware_spec_hash",
                "clock_setup_hash",
                "seed",
            )
        }
        | {"execution_outcome": "success"}
        for e in profile["entries"]
    ]
    trust = {
        "format": "uarch-k2-build-trust/1",
        "purpose": "construction-test-only",
        "semantics_file": common,
        "registry_hash": registry["registry_hash"],
        "registry_file": put("registry.json", registry),
        "profiles": [
            {
                "profile_hash": profile["profile_hash"],
                "file": put("profile.json", profile),
                "cases": cases,
            }
        ],
        "corpus_inventory": common,
    }
    tools = {
        "format": "uarch-k2-tool-inputs/1",
        "compiler_commit": "a" * 40,
        "rust_release": "1.99.0",
        "target": "x86_64-unknown-linux-gnu",
        "image_digest": sha256(b"synthetic-image"),
        "flags": [],
    }
    for field in (
        "accepted_k1_pins",
        "cargo_lock",
        "full_metadata",
        "target_metadata",
        "feature_graph",
        "licence_inventory",
        "crate_checksum_inventory",
        "linker_and_os_inventory",
    ):
        tools[field] = common
    build = {
        "format": "uarch-k2-build-inputs/1",
        "source_commit": "a" * 40,
        "source_files": [source],
        "trust_hash": content_hash(trust),
        "trust_file": put("trust.json", trust),
        "tool_inputs_hash": content_hash(tools),
        "tool_inputs_file": put("tools.json", tools),
        "model_source_paths": ["source.rs"],
        "model_inputs_hash": content_hash([source]),
        "mode_configs": [
            {"mode": m, "cargo_args": [], "rustflags": []} for m in ("debug", "release")
        ],
        "generated_identity_output_paths": ["identity.rs"],
        "permitted_environment": {},
    }
    engine = {
        "name": "native",
        "version": "native-stage/1",
        "implementation_hash": content_hash(build),
        "compiler_lock_hash": content_hash(tools),
        "model": {
            "name": "fixed-delay",
            "version": "1",
            "implementation_hash": build["model_inputs_hash"],
        },
    }
    raw["engine"] = engine
    raw["job_hash"] = content_hash(raw, exclude=("job_hash",))
    jobs = put(
        "jobs.json",
        {
            "format": "uarch-k2-jobs-inventory/1",
            "jobs": [{"file": put("job.json", raw), "job_hash": raw["job_hash"]}],
        },
    )
    generated = put("identity.rs", b"// synthetic generated identity")
    executables = []
    receipts = {}
    for mode in ("debug", "release"):
        exe = put(mode, ("synthetic nonexecutable " + mode).encode())
        receipt = {
            "format": "uarch-k2-build-receipt/1",
            "build_input_hash": content_hash(build),
            "engine": engine,
            "mode": mode,
            "target": tools["target"],
            "executable": exe,
            "image_digest": tools["image_digest"],
            "generated_identity_outputs": [generated],
        }
        for key in (
            "actual_read_inventory",
            "actual_environment",
            "compiler_verbose",
            "build_log",
            "binary_origin_check",
            "software_path_check",
        ):
            receipt[key] = common
        receipts[mode] = receipt
        executables.append(
            {
                "mode": mode,
                "executable": exe,
                "build_receipt": put(mode + ".json", receipt),
                "target": tools["target"],
            }
        )
    record = {
        "format": "uarch-k2-first-use/1",
        "semantics": common,
        "trust_hash": content_hash(trust),
        "trust_file": build["trust_file"],
        "build_input_hash": content_hash(build),
        "build_input_file": put("build.json", build),
        "tool_inputs_hash": content_hash(tools),
        "model_inputs_hash": build["model_inputs_hash"],
        "loader_read_inventory": common,
        "expected_engine": engine,
        "executables": executables,
        "jobs_inventory": jobs,
        "corpus_inventory": common,
        "profile_hashes": [profile["profile_hash"]],
        "registry_hash": registry["registry_hash"],
    }
    subject = {
        "build_input_hash": record["build_input_hash"],
        "tool_inputs_hash": record["tool_inputs_hash"],
        "trust_hash": record["trust_hash"],
        "model_inputs_hash": record["model_inputs_hash"],
        "executable_byte_hashes": [x["executable"]["byte_hash"] for x in executables],
        "corpus_byte_hash": common["byte_hash"],
        "jobs_byte_hash": jobs["byte_hash"],
    }
    record["decision"] = put(
        "decision.json",
        {
            "format": "uarch-k2-human-first-use-decision/1",
            "accepted_by": "Javid (@jjaffari)",
            "reply": "yes",
            "subject": subject,
        },
    )
    record["independent_review"] = put(
        "review.json",
        {
            "format": "uarch-k2-independent-build-review/1",
            "subject": subject,
            "read_audit_complete": True,
            "selected_support_current": True,
        },
    )

    def selector():
        binding = put("host.json", record)
        return HostSelector(
            format="uarch-k2-host-selector/1",
            repository=str(root),
            acceptance_commit="a" * 40,
            record_path=binding["path"],
            record_byte_hash=binding["byte_hash"],
        )

    return selector, record, receipts, put


def test_structural_resolver_joins_do_not_make_synthetic_bytes_executable(tmp_path):
    selector, record, _, _ = scaffold(tmp_path)
    resolved = _resolve(selector(), mode="debug")
    assert resolved.record.expected_engine.implementation_hash == record["build_input_hash"]
    with pytest.raises(HostBindingError, match="read-only"):
        with resolved.open_executable():
            pytest.fail("synthetic nonexecutable became executable")


@pytest.mark.parametrize("mode", ["debug", "release"])
def test_each_actual_executable_is_verified_even_when_selecting_debug(tmp_path, mode):
    selector, _, _, _ = scaffold(tmp_path)
    anchor = selector()
    (tmp_path / mode).write_bytes(b"changed")
    with pytest.raises(HostBindingError, match="digest mismatch"):
        _resolve(anchor, mode="debug")


def test_receipt_mode_join_refuses_rehashed_wrong_mode(tmp_path):
    selector, record, receipts, put = scaffold(tmp_path)
    receipt = copy.deepcopy(receipts["release"])
    receipt["mode"] = "debug"
    record["executables"][1]["build_receipt"] = put("release.json", receipt)
    with pytest.raises(HostBindingError, match="mode/executable"):
        _resolve(selector(), mode="debug")


def test_decision_subject_cannot_be_replaced_by_record_rehash(tmp_path):
    selector, record, _, put = scaffold(tmp_path)
    decision = json.loads((tmp_path / "decision.json").read_bytes())
    decision["subject"]["build_input_hash"] = sha256(b"other")
    record["decision"] = put("decision.json", decision)
    with pytest.raises(HostBindingError, match="human first-use"):
        _resolve(selector(), mode="debug")


def synthetic_result(raw):
    """Hand-written structural example only; never a native run or golden evidence."""

    def observed(rows):
        return {"status": "observed", "records": rows}

    rows = [("a", 0, 0, 0, 3000, []), ("b", 1, 0, 0, 5000, []), ("c", 0, 5000, 5000, 7000, ["b"])]
    jobs = [
        {
            "job_id": j,
            "owner_id": owner,
            "release_ps": 0,
            "ready_ps": ready,
            "start_ps": start,
            "end_ps": end,
            "blocking_predecessor_ids": pred,
            "op_id": None,
            "group_id": None,
            "repeat_index": None,
            "tile_origin": None,
            "tile_extents": None,
            "useful_matrix_ops": 0,
            "issued_matrix_ops": 0,
            "vector_arithmetic_ops": 0,
            "cast_ops": 0,
        }
        for j, owner, ready, start, end, pred in rows
    ]
    literal_events = [
        (0, 0, 1, 0, "TASK_READY", "a"),
        (1, 0, 1, 1, "TASK_READY", "b"),
        (2, 0, 2, 0, "OWNER_GRANT", "a"),
        (4, 0, 2, 1, "OWNER_GRANT", "b"),
        (3, 3000, 0, 0, "COMPUTE_DONE", "a"),
        (6, 3000, 1, 0, "DEPENDENCY_READY", "c"),
        (5, 5000, 0, 1, "COMPUTE_DONE", "b"),
        (7, 5000, 1, 0, "DEPENDENCY_READY", "c"),
        (8, 5000, 2, 0, "OWNER_GRANT", "c"),
        (9, 7000, 0, 0, "COMPUTE_DONE", "c"),
    ]
    events = [
        {
            "event_seq": seq,
            "observation_ordinal": i,
            "t_ps": t,
            "phase": phase,
            "target_id": owner,
            "kind": kind,
            "job_id": j,
        }
        for i, (seq, t, phase, owner, kind, j) in enumerate(literal_events)
    ]
    intervals = sorted(
        [
            {
                "owner_id": owner,
                "job_id": j,
                "start_ps": start,
                "end_ps": end,
                "activity": "fixed_delay",
                "limiting_resource_id": owner,
                "service_start_ps_ratio": None,
                "service_end_ps_ratio": None,
            }
            for j, owner, _, start, end, _ in rows
        ],
        key=lambda x: (x["owner_id"], x["job_id"]),
    )
    queues = sorted(
        [
            {
                "queue_id": f"owner:{owner}:{pop}",
                "item_id": j,
                "population": pop,
                "enter_ps": a,
                "leave_ps": b,
                "owner_id": owner,
                "clock_domain": None,
            }
            for j, owner, ready, start, end, _ in rows
            for pop, a, b in [("waiting", ready, start), ("service", start, end)]
        ],
        key=lambda x: (x["queue_id"], x["item_id"], x["population"]),
    )
    critical = [
        {
            "kind": "service",
            "start_ps": a,
            "end_ps": b,
            "cause_job_id": j,
            "predecessor_id": pred,
            "limiting_resource_id": owner,
            "category": "overhead",
        }
        for a, b, j, pred, owner in [(0, 5000, "b", None, 1), (5000, 7000, "c", "b", 0)]
    ]
    result = {
        "protocol": "uarch-engine/3",
        "job_hash": raw["job_hash"],
        "engine": raw["engine"],
        "scope": "kernel_fixture",
        "completion": "complete",
        "duration_ps": 7000,
        "completed_jobs": ["a", "b", "c"],
        "admission": raw["admission"],
        "counts": dict(
            matrix_ops=0.0, vector_ops=0.0, memory_read_bytes=0.0, memory_write_bytes=0.0
        ),
        "ext_counts": dict(sram_read_bytes=0.0, sram_write_bytes=0.0, noc_flit_hop_count=None),
        "work_counts": dict(
            format="uarch-native-work-counts/1",
            completed_mac_count=0,
            issued_matrix_ops=0,
            vector_arithmetic_ops=0,
            cast_ops=0,
        ),
        "traffic_counts": dict(
            format="uarch-native-traffic-counts/1",
            read_payload_bytes=0,
            write_payload_bytes=0,
            read_transaction_bytes=0,
            write_transaction_bytes=0,
            unicast_payload_bytes=0,
        ),
        "per_op": [],
        "busy_time_ps": [
            {"owner_id": 0, "busy_time_ps": 5000},
            {"owner_id": 1, "busy_time_ps": 5000},
        ],
        "attribution_ps": dict(compute=0, memory=0, noc=0, sync=0, overhead=7000),
        "diagnostics": {
            k: None
            for k in [
                "matrix_util_ratio",
                "vector_util_ratio",
                "dma_compute_overlap_ratio",
                "sram_bank_conflict_stall_ratio",
                "noc_latency_p50_ps",
                "noc_latency_p99_ps",
                "noc_max_link_util_ratio",
                "dram_bw_util_ratio",
                "dram_row_hit_ratio",
                "energy_pj",
            ]
        },
        "fidelity_detail": None,
        "unrepresented": ["allocations", "dma", "transfers"],
        "simulator_metrics": dict(event_count=10, completed_job_count=3, max_live_events=2),
        "trace_hash": None,
        "u_c0_duration_ps": None,
        "owners": raw["owners"],
        "observations": {
            "format": "uarch-native-observations/1",
            "events": observed(events),
            "jobs": observed(jobs),
            "clocks": observed([]),
            "resource_intervals": observed(intervals),
            "critical_path": observed(critical),
            "queue_membership": observed(queues),
            **{
                k: {"status": "unrepresented", "reason": "synthetic structural control only"}
                for k in ["dma", "transfers", "allocations"]
            },
        },
    }
    result["result_hash"] = content_hash(result)
    return result


def test_response_parser_independently_validates_synthetic_structure(tmp_path):
    from rkuarch.engines.native.runner import parse_response

    selector, _, _, _ = scaffold(tmp_path)
    host = _resolve(selector(), mode="debug")
    raw = json.loads((tmp_path / "job.json").read_bytes())
    result = synthetic_result(raw)
    parsed = parse_response(
        canonical_json(result).encode(),
        b"",
        0,
        request_bytes=canonical_json(raw).encode(),
        host=host,
    )
    assert parsed.duration_ps == 7000


@pytest.mark.parametrize(
    "path,value,reason",
    [
        (
            ("observations", "queue_membership", "records", 0, "clock_domain"),
            "core",
            "IncompleteObservations",
        ),
        (("busy_time_ps", 0, "busy_time_ps"), 7000, "IncompleteObservations"),
        (
            ("observations", "jobs", "records", 2, "blocking_predecessor_ids"),
            ["a", "b"],
            "AttributionMismatch",
        ),
        (
            ("observations", "critical_path", "records", 1, "predecessor_id"),
            "a",
            "AttributionMismatch",
        ),
        (("observations", "events", "records", 4, "event_seq"), 0, "IncompleteObservations"),
    ],
)
def test_response_rehash_does_not_hide_bad_observations(tmp_path, path, value, reason):
    from rkuarch.engines.native.runner import ProtocolViolation, parse_response

    selector, _, _, _ = scaffold(tmp_path)
    host = _resolve(selector(), mode="debug")
    raw = json.loads((tmp_path / "job.json").read_bytes())
    result = synthetic_result(raw)
    cursor = result
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    with pytest.raises(ProtocolViolation) as failure:
        parse_response(
            canonical_json(result).encode(),
            b"",
            0,
            request_bytes=canonical_json(raw).encode(),
            host=host,
        )
    assert reason in str(failure.value.__cause__)
