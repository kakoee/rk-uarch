"""Focused ordinary-process R checks with literal arithmetic and fault controls."""

import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash

from rkuarch.engines.native.ordinary import replay, run
from rkuarch.mapping.reference import map_reference
from rkuarch.verification.component.reference import check_reference
from rkuarch.workload.reference import (
    matrix_source,
    nominal_hardware,
    operand,
    prepare_job,
    prepared,
    source,
)

pytestmark = pytest.mark.native
BIN = Path(os.environ.get("REFERENCE_NATIVE", "reference-native-unconfigured"))


@pytest.fixture(autouse=True)
def require_native():
    if not BIN.is_file():
        pytest.skip("set REFERENCE_NATIVE to the ordinary native executable")


def invoke(tmp_path, src, *, primes=1):
    job = prepare_job(map_reference(src, nominal_hardware(), priming_iterations=primes))
    saved = tmp_path / f"job-{primes}.json"
    out = tmp_path / f"result-{primes}.json"
    saved.write_text(canonical_json(job))
    result = run(saved, executable=BIN)
    out.write_text(canonical_json(result))
    assert replay(saved, out) == result
    return job, result


def test_literal_tail_process_replay(tmp_path):
    job, r = invoke(tmp_path, matrix_source(3, 130, 7))
    assert r.counts["matrix_ops"] == 5460
    assert r.counts["hbm_read_bytes"] == 2600
    assert r.counts["hbm_write_bytes"] == 42
    assert r.counts["vmem_bytes"] == 2978
    assert r.counts["useful_cast"] == 21
    _, two = invoke(tmp_path, matrix_source(3, 130, 7), primes=2)
    assert r.duration_ps == two.duration_ps and r.counts == two.counts
    for fault in ("service", "count", "owner", "missing", "credit"):
        bad = deepcopy(r.model_dump(mode="json"))
        if fault == "service":
            bad["observations"]["activities"][0]["end_ps"] += 1
        elif fault == "count":
            bad["counts"]["matrix_ops"] += 1
        elif fault == "owner":
            bad["observations"]["activities"][0]["owner"] = 0
        elif fault == "missing":
            bad["observations"]["activities"].pop()
        else:
            bad["observations"]["sequences"][1][1] = 0
        with pytest.raises(ValueError):
            check_reference(job.model_dump(mode="json"), bad)


@pytest.mark.parametrize(
    "operator,expected",
    [
        (
            "normalization",
            {
                "useful_multiply": 26,
                "useful_reduction_sum": 6,
                "useful_add": 2,
                "useful_rsqrt": 2,
                "useful_cast": 20,
            },
        ),
        ("residual_addition", {"useful_add": 8, "useful_cast": 24}),
        ("activation", {"useful_multiply": 16, "useful_exp": 8, "useful_cast": 24}),
    ],
)
def test_small_vector_literals(tmp_path, operator, expected):
    operands = {
        k: operand("bf16", ("D",) if k == "W" and operator == "normalization" else ("M", "D"))
        for k in ("X", "W", "Y")
    }
    _, r = invoke(tmp_path, source([prepared("vector", operator, dict(M=2, D=4), operands)]))
    for k, v in expected.items():
        assert r.counts[k] == v


def test_read_four_elements(tmp_path):
    s = source(
        [
            prepared(
                "read",
                "stream_read_sum",
                dict(E=4, One=1),
                dict(X=operand("bf16", ("E",)), Y=operand("fp32", ("One",))),
            )
        ]
    )
    _, r = invoke(tmp_path, s)
    assert r.counts["useful_cast"] == 4 and r.counts["useful_reduction_sum"] == 3
    assert r.counts["hbm_read_bytes"] == 8 and r.counts["hbm_write_bytes"] == 4


def test_direct_native_rejects_changed_closure(tmp_path):
    job, _ = invoke(tmp_path, matrix_source(3, 130, 7))
    data = job.model_dump(mode="json")
    data["job_hash"] = "sha256:" + "0" * 64
    p = subprocess.run(
        [str(BIN), "--protocol", "uarch-engine/5"],
        input=canonical_json(data).encode(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert p.returncode == 2 and json.loads(p.stderr)["code"] == "ContentHashMismatch"


def synthetic_scalar_job(window=2, bandwidth=2_000_000_000_000):
    from uarch_contract.reference import TpuV5eReference

    hardware = nominal_hardware().model_dump(mode="json")
    choices = dict(
        hbm_latency_ps=10,
        hbm_issue_interval_ps=1,
        hbm_max_outstanding=window,
        hbm_peak_bytes_per_s=bandwidth,
        vmem_bytes_per_s=4_000_000_000_000,
        kernel_startup_ps=11,
        scalar_op_ps=1,
        vector_group_startup_ps=1,
        vector_tile_ps=1,
    )
    for name, value in choices.items():
        hardware[name].update(
            value=value, provenance="stub", source=None, date=None, rationale=None
        )
    src = source(
        [
            prepared(
                "add",
                "scalar_add",
                dict(M=1, D=1),
                {k: operand("fp32", ("M", "D")) for k in ("X", "W", "Y")},
            )
        ]
    )
    return prepare_job(
        map_reference(
            src, TpuV5eReference.model_validate(hardware), priming_iterations=0, test_only=True
        )
    )


@pytest.mark.parametrize(
    "window,bandwidth,duration",
    [(2, 2_000_000_000_000, 42), (1, 2_000_000_000_000, 52), (2, 3_000_000_000_000, 41)],
)
def test_literal_hbm_overlap_and_fractional_cursor(tmp_path, window, bandwidth, duration):
    job = synthetic_scalar_job(window, bandwidth)
    saved = tmp_path / "synthetic.json"
    saved.write_text(canonical_json(job))
    r = run(saved, executable=BIN, test_only=True)
    assert r.duration_ps == duration
    assert r.counts["hbm_read_bytes"] == 8 and r.counts["hbm_write_bytes"] == 4
    if bandwidth == 3_000_000_000_000:
        from fractions import Fraction

        service = [x for x in r.observations.activities if x.phase == "r_hbm"]
        assert Fraction(*service[1].ratio_start) == Fraction(67, 3)


def reseal(data):
    b = data["workload_closure"]
    p = b["points"][0]
    g = p["task_graph"]
    g["graph_hash"] = content_hash(g, exclude=("graph_hash",))
    p["payload_hash"] = content_hash(p, exclude=("payload_hash",))
    b["source"]["source_hash"] = content_hash(b["source"], exclude=("source_hash",))
    b["hardware_spec_hash"] = content_hash(b["hardware_spec"])
    b["assumptions"]["assumptions_hash"] = content_hash(
        b["assumptions"], exclude=("assumptions_hash",)
    )
    b["assumptions_hash"] = b["assumptions"]["assumptions_hash"]
    b["bundle_hash"] = content_hash(b, exclude=("bundle_hash",))
    data["bundle_hash"] = b["bundle_hash"]
    data["point_hash"] = p["payload_hash"]
    data["job_hash"] = content_hash(data, exclude=("job_hash",))
    return data


@pytest.mark.parametrize(
    "fault",
    [
        "missing_tile",
        "duplicate_tail",
        "dtype",
        "unit",
        "capacity",
        "preload",
        "missing_store",
        "missing_cast",
        "missing_partial",
        "producer_edge",
        "window",
        "unearned_fact",
    ],
)
def test_rehashed_native_semantic_faults(tmp_path, fault):
    from uarch_contract.reference import ReferenceJob

    data = prepare_job(map_reference(matrix_source(3, 130, 7), nominal_hardware())).model_dump(
        mode="json"
    )
    b = data["workload_closure"]
    g = b["points"][0]["task_graph"]
    dots = [j for j in g["jobs"] if j["kind"] == "compute"]
    if fault == "missing_tile":
        g["coverage"].pop()
    elif fault == "duplicate_tail":
        dots[1]["tile_origin"]["K"] = 0
        next(c for c in g["coverage"] if c["job_id"] == dots[1]["id"])["tile_origin"]["K"] = 0
    elif fault == "dtype":
        dots[0]["accumulator_dtype"] = "int32"
    elif fault == "unit":
        b["hardware_spec"]["vector_tile_ps"]["unit"] = "Hz"
    elif fault == "capacity":
        b["assumptions"]["accumulator_window_bytes"] = 16
    elif fault == "preload":
        next(x for x in g["buffers"] if x["id"] == "x0.0")["initial_residency"] = "preloaded"
    elif fault in {"missing_store", "missing_cast"}:
        victim = next(
            j
            for j in reversed(g["jobs"])
            if j["kind"] == ("dma" if fault == "missing_store" else "vector")
        )
        g["jobs"].remove(victim)
        g["dependencies"] = [e for e in g["dependencies"] if victim["id"] not in e.values()]
        for buffer in g["buffers"]:
            if buffer["producer_id"] == victim["id"]:
                buffer["producer_id"] = None
            buffer["final_consumer_ids"] = [
                x for x in buffer["final_consumer_ids"] if x != victim["id"]
            ]
    elif fault == "missing_partial":
        # Remove a real transfer but preserve its transitive dependency order.
        # Hashes and generic producer/reuse checks alone cannot catch this omission.
        victim = next(j for j in g["jobs"] if j["kind"] == "local_transfer")
        predecessors = [e["before"] for e in g["dependencies"] if e["after"] == victim["id"]]
        successors = [e["after"] for e in g["dependencies"] if e["before"] == victim["id"]]
        g["jobs"].remove(victim)
        g["dependencies"] = [e for e in g["dependencies"] if victim["id"] not in e.values()]
        for before in predecessors:
            for after in successors:
                edge = dict(before=before, after=after)
                if edge not in g["dependencies"]:
                    g["dependencies"].append(edge)
        for buffer in g["buffers"]:
            if buffer["producer_id"] == victim["id"]:
                buffer["producer_id"] = None
            buffer["final_consumer_ids"] = [
                x for x in buffer["final_consumer_ids"] if x != victim["id"]
            ]
    elif fault == "producer_edge":
        g["dependencies"] = [e for e in g["dependencies"] if e["after"] != dots[0]["id"]]
    elif fault == "window":
        b["hardware_spec"]["hbm_max_outstanding"]["value"] = 1.5
    else:
        b["hardware_spec"]["kernel_startup_ps"].update(provenance="spec_derived", source=None)
    reseal(data)
    with pytest.raises(
        ValueError, match="mandatory accumulator traffic" if fault == "missing_partial" else None
    ):
        ReferenceJob.model_validate(data)
    p = subprocess.run(
        [str(BIN), "--protocol", "uarch-engine/5"],
        input=canonical_json(data).encode(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert p.returncode == 2 and not p.stdout, (fault, p.returncode, p.stderr[:500])
    if fault == "missing_partial":
        assert b"mandatory accumulator traffic" in p.stderr


def coefficients():
    from uarch_contract.rotary_v2 import RotaryCoefficients

    from rkuarch.workload.reference import sealed

    return RotaryCoefficients.model_validate(
        sealed(
            dict(
                format="uarch-rotary-coefficients/1",
                position_count=3,
                rotary_dim=4,
                dtype="fp32",
                cos_bits=[["3f800000", "3f800000"]] * 3,
                sin_bits=[["00000000", "00000000"]] * 3,
                producer=dict(
                    name="literal-test-coefficients",
                    version="1",
                    implementation_hash="sha256:" + "0" * 64,
                ),
            ),
            "coefficients_hash",
        )
    )


def test_rotary_literal_work_and_coefficients(tmp_path):
    from rkuarch.workload.reference import dot

    c = coefficients()
    ops = []
    for target, heads in (("q", 2), ("k", 1)):
        ops.append(dot(target, 1, 4, heads * 4, operator=target + "_projection"))
        ops.append(
            prepared(
                target + "rope",
                "rotary_embedding",
                dict(B=1, S=1, H=heads, D=4, R=4),
                {k: operand("bf16", ("B", "S", "H", "D")) for k in ("X", "Y")},
                depends=[target],
                rotary=dict(
                    target=target,
                    coefficients_hash=c.coefficients_hash,
                    pairing="split_halves",
                    numeric_policy="fp32-separate-round-rne/1",
                    position_ids=[[0]],
                    input_op_id=target,
                ),
            )
        )
    job, r = invoke(tmp_path, source(ops, coefficients=c))
    counts = [r.per_op_counts[k] for k in ("qrope", "krope")]
    assert sum(x["useful_multiply"] + x["useful_add"] + x["useful_subtract"] for x in counts) == 36
    assert sum(x["useful_cast"] for x in counts) == 24
    assert (
        sum(x["issued_multiply"] + x["issued_add"] + x["issued_subtract"] for x in counts) == 12288
    )
    assert sum(x["issued_cast"] for x in counts) == 4096
    assert sum(x["hbm_read_bytes"] for x in counts) == 56
    assert sum(x["hbm_write_bytes"] for x in counts) == 24
    bad = job.model_dump(mode="json")
    bad["workload_closure"]["source"]["coefficients"]["cos_bits"][0][0] = "7f800000"
    reseal(bad)
    p = subprocess.run(
        [str(BIN), "--protocol", "uarch-engine/5"],
        input=canonical_json(bad).encode(),
        capture_output=True,
        check=False,
    )
    assert p.returncode == 2 and not p.stdout


@pytest.mark.parametrize("page,index_bytes", [(16, 516), (32, 260)])
def test_gather_2049_tail_state_and_page_fault(tmp_path, page, index_bytes):
    from rkuarch.workload.reference import suite_source

    supplied = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "validation/L3_silicon/tpu-v5e/u4b/inputs/gather-page-indices.json"
        ).read_text()
    )
    src = suite_source(
        dict(
            id="gather",
            benchmark_class="DRAM gather",
            work=dict(valid_tokens=2049, block_tokens=page, kv_heads=8, head_dim=128),
        ),
        page_indices=supplied[f"gather-p{page}-c2049"],
    )
    job, r = invoke(tmp_path, src)
    assert r.counts["hbm_read_bytes"] == 8392704 + index_bytes
    assert r.counts["hbm_write_bytes"] == 8392704
    assert r.observations.persistent_before == r.observations.persistent_after
    _, r2 = invoke(tmp_path, src, primes=2)
    assert (r.duration_ps, r.counts, r.observations.state_after) == (
        r2.duration_ps,
        r2.counts,
        r2.observations.state_after,
    )
    bad = job.model_dump(mode="json")
    g = bad["workload_closure"]["points"][0]["task_graph"]
    cache = {b["id"] for b in g["buffers"] if b["layout"] == "paged"}
    read = next(j for j in g["jobs"] if j["kind"] == "dma" and j["source"]["buffer_id"] in cache)
    read["source"]["offset_bytes"] = 0
    read["spans"][0]["source_offset_bytes"] = 0
    reseal(bad)
    from uarch_contract.reference import ReferenceJob

    with pytest.raises(ValueError):
        ReferenceJob.model_validate(bad)
    p = subprocess.run(
        [str(BIN), "--protocol", "uarch-engine/5"],
        input=canonical_json(bad).encode(),
        capture_output=True,
        check=False,
    )
    assert p.returncode == 2 and not p.stdout


@pytest.mark.parametrize("tokens,queries,heads", [(3, 1, 4), (3, 3, 2)])
def test_small_gqa_and_causal_attention(tmp_path, tokens, queries, heads):
    dims = dict(B=1, S=queries, T=tokens, Hq=heads, H=2, D=2, P=16)
    operands = {
        k: operand(
            "bf16",
            ("B", "S", "Hq", "D") if k in ("Q", "O") else ("B", "T", "H", "D"),
            page=16 if k in ("K", "V") else None,
        )
        for k in ("Q", "K", "V", "O")
    }
    src = source(
        [prepared("attention", "attention_fused", dims, operands)],
        before=tokens - queries,
        after=tokens,
        pages=[0],
    )
    _, r = invoke(tmp_path, src)
    assert r.counts["matrix_ops"] == r.counts["semantic_matrix_ops"] == 96
    assert r.counts["semantic_vector_ops"] == 60
    assert r.counts["issued_matrix_ops"] > 96


def test_check_faults_cause_allocation_state_and_cli(tmp_path):
    job, r = invoke(tmp_path, matrix_source(3, 130, 7))
    for fault in ("cause", "allocation", "state", "critical"):
        bad = r.model_dump(mode="json")
        if fault == "cause":
            activity = next(x for x in bad["observations"]["activities"] if x["causes"])
            activity["causes"][0][1] = "credit"
        elif fault == "allocation":
            bad["observations"]["allocation_intervals"][0][1] += 1
        elif fault == "state":
            bad["observations"]["context_after"] += 1
        else:
            bad["observations"]["critical_path"][-1]["end_ps"] -= 1
        with pytest.raises(ValueError):
            check_reference(job.model_dump(mode="json"), bad)
    p = subprocess.run(
        [str(BIN), "--protocol", "uarch-engine/4"],
        input=canonical_json(job).encode(),
        capture_output=True,
        check=False,
    )
    assert p.returncode == 2 and json.loads(p.stderr)["code"] == "UnsupportedProtocol"


def test_explicit_spill_and_half_rate(tmp_path):
    from uarch_contract.reference import TpuV5eReference

    src = matrix_source(3, 130, 7)
    _, base = invoke(tmp_path, src)
    spill = prepare_job(map_reference(src, nominal_hardware(), spill_accumulator=True))
    path = tmp_path / "spill.json"
    path.write_text(canonical_json(spill))
    r = run(path, executable=BIN)
    assert r.counts["matrix_ops"] == base.counts["matrix_ops"] == 5460
    assert r.counts["hbm_read_bytes"] == base.counts["hbm_read_bytes"] + 84
    assert r.counts["hbm_write_bytes"] == base.counts["hbm_write_bytes"] + 84
    assert r.counts["vmem_bytes"] == base.counts["vmem_bytes"] + 168
    assert r.duration_ps >= base.duration_ps
    hardware = nominal_hardware().model_dump(mode="json")
    hardware["bf16_mxu_mac_per_s"]["value"] /= 2
    slower = prepare_job(map_reference(src, TpuV5eReference.model_validate(hardware)))
    path.write_text(canonical_json(slower))
    slow = run(path, executable=BIN)
    assert slow.duration_ps > base.duration_ps and slow.counts == base.counts


def test_length_one_reduction_has_no_combine_or_cost_read(tmp_path):
    src = source(
        [
            prepared(
                "read",
                "stream_read_sum",
                dict(E=1, One=1),
                dict(X=operand("bf16", ("E",)), Y=operand("fp32", ("One",))),
            )
        ]
    )
    _, result = invoke(tmp_path, src)
    assert result.counts["useful_reduction_sum"] == 0
    assert result.counts.get("issued_reduction_sum", 0) == 0
    assert result.counts["useful_cast"] == 1
    assert result.counts["hbm_read_bytes"] == 2 and result.counts["hbm_write_bytes"] == 4
    assert "reduction_cost_ratio" not in result.consumed_stubs


def dependency_violation(job, good):
    """Independent review B2's 41 ps forgery; keep every downstream field consistent.

    Adapted from U4b-native-reference-independent-review-v1/probes/dependency_violation.py.
    The vector starts at 25 ps although its W input arrives at 26 ps. Resealing proves
    this is a semantic check, not merely a content-hash refusal.
    """
    bad = deepcopy(good)
    obs = bad["observations"]
    acts = obs["activities"]
    for i, ready, start, end in (
        (7, 25, 25, 26),
        (8, 26, 26, 27),
        (9, 27, 27, 28),
        (10, 28, 28, 29),
        (11, 29, 29, 39),
        (12, 39, 39, 41),
    ):
        acts[i].update(
            ready_ps=ready,
            start_ps=start,
            end_ps=end,
            ratio_start=[start, 1],
            ratio_end=[end, 1],
        )
    acts[7]["causes"] = []
    jobs = [list(j) for j in obs["jobs"]]
    jobs[3] = [26, 25, 28]
    jobs[4] = [28, 28, 41]
    obs["jobs"] = jobs
    seqs = [list(s) for s in obs["sequences"]]
    seqs[3] = [3, 26, 28, 0]
    seqs[4] = [4, 29, 41, 4]
    obs["sequences"] = seqs
    bad["duration_ps"] = 41
    g = job["workload_closure"]["points"][0]["task_graph"]
    ids = {t["id"]: i + 1 for i, t in enumerate(g["jobs"])}
    intervals = []
    for buffer in g["buffers"]:
        start = (
            0
            if buffer["persistent"] or buffer["initial_residency"] == "preloaded"
            else jobs[ids[buffer["producer_id"]]][1]
            if buffer["producer_id"]
            else 0
        )
        end = (
            41
            if buffer["persistent"] or not buffer["final_consumer_ids"]
            else max(jobs[ids[j]][2] for j in buffer["final_consumer_ids"])
        )
        intervals.append([start, end])
    obs["allocation_intervals"] = intervals
    obs["critical_path"] = [
        dict(activity=a, start_ps=s, end_ps=e, cause="service")
        for a, s, e in (
            (0, 0, 11),
            (1, 11, 21),
            (3, 21, 23),
            (4, 23, 25),
            (7, 25, 26),
            (8, 26, 27),
            (9, 27, 28),
            (10, 28, 29),
            (11, 29, 39),
            (12, 39, 41),
        )
    ]
    bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
    return bad


@pytest.mark.parametrize("boundary", ["checker", "replay"])
def test_dependency_readiness_rejects_impossible_schedule(tmp_path, boundary):
    job = synthetic_scalar_job()
    saved = tmp_path / "job.json"
    saved.write_text(canonical_json(job))
    good = run(saved, executable=BIN, test_only=True).model_dump(mode="json")
    raw_job = job.model_dump(mode="json")
    assert good["duration_ps"] == 42
    assert good["observations"]["jobs"][2][2] == 26  # W input arrival
    assert good["observations"]["jobs"][3] == [26, 26, 29]  # equality is legal
    # HBM's first read issues exactly at readiness, the second legally waits for spacing.
    assert good["observations"]["jobs"][1][:2] == [11, 11]
    assert good["observations"]["jobs"][2][:2] == [11, 12]
    assert good["observations"]["activities"][1]["ready_ps"] == 11
    assert good["observations"]["activities"][2]["ready_ps"] == 12
    bad = dependency_violation(raw_job, good)
    assert bad["observations"]["jobs"][3] == [26, 25, 28]
    assert bad["duration_ps"] == 41

    def check(result):
        if boundary == "checker":
            check_reference(raw_job, result)
        else:
            output = tmp_path / "result.json"
            output.write_text(canonical_json(result))
            replay(saved, output, test_only=True)

    check(good)
    with pytest.raises(ValueError, match="first activity dependency readiness"):
        check(bad)
    check(good)
