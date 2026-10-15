"""M schema/admission controls only; no fabricated native execution result."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import content_hash, strict_json_loads
from uarch_contract.mapped import (
    MappedBundle,
    MappedEngineJob,
    MappedEngineResult,
    NativeTestProfile,
    NativeTestRegistry,
    TaskGraph,
    validate_result,
)
from uarch_contract.mapped import (
    admit as contract_admit,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures/mapped"


def admit(value: Any, **kwargs: Any) -> Any:
    # Only test scaffolding supplies the independently selected local fixture anchors.
    return contract_admit(
        value,
        trusted_registry_hash=kwargs["registry"]["registry_hash"],
        trusted_profile_hash=(
            kwargs["profile"]["profile_hash"] if kwargs["profile"] is not None else None
        ),
        **kwargs,
    )


def load(name: Any) -> Any:
    return strict_json_loads((FIXTURES / (name + ".json")).read_text())


def rehash(value: Any, field: Any) -> Any:
    value[field] = content_hash(value, exclude=(field,))
    return value


def seal(bundle: Any) -> Any:
    for point in bundle["points"]:
        rehash(point["task_graph"], "graph_hash")
        rehash(point, "payload_hash")
    return rehash(bundle, "bundle_hash")


def check(bundle: Any, **kwargs: Any) -> Any:
    return admit(
        bundle,
        invocation="production",
        checkpoint="B",
        registry=load("registry"),
        profile=None,
        **kwargs,
    )


def test_positive_component_and_identity() -> None:
    b = load("component")
    assert check(b).bundle_hash == b["bundle_hash"]
    assert MappedEngineJob.model_validate(load("component-job"))
    assert MappedBundle.model_validate(b).model_dump(mode="json") == b
    changed = copy.deepcopy(b)
    changed["points"][0]["task_graph"]["jobs"][0]["id"] = "changed"
    assert seal(changed)["bundle_hash"] != b["bundle_hash"]


def test_positive_kernel_profile_and_host_binding() -> None:
    b, profile, registry = load("kernel"), load("profile"), load("registry")
    assert NativeTestProfile.model_validate(profile)
    assert NativeTestRegistry.model_validate(registry)
    assert admit(b, invocation="test", checkpoint="K2", registry=registry, profile=profile)
    with pytest.raises(ValueError, match="AdmissionMismatch"):
        admit(b, invocation="production", checkpoint="K2", registry=registry, profile=profile)
    profile["entries"][0]["seed"] += 1
    rehash(profile, "profile_hash")
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        admit(b, invocation="test", checkpoint="K2", registry=registry, profile=profile)


@pytest.mark.parametrize(
    ("rid", "path", "value", "error"),
    [
        (
            "R04",
            ("scope", "ops", 0, "spec", "operands", "X", "dtype"),
            "fp16",
            "UnsupportedPrecision",
        ),
        ("R05", ("rank", "tp"), 8, "UnsupportedRankScope"),
        ("R06", ("scope", "ops", 0, "spec", "operator"), "normalization", "UnsupportedOperator"),
        ("R07", ("points", 0, "initial_state"), "steady", "UnsupportedInitialState"),
        ("R08", ("scope", "ops", 0, "spec", "dimensions", "K"), 257, "UnsupportedShape"),
        ("R09", ("mapping_policy", "name"), "unknown", "UnsupportedMapping"),
        (
            "R10",
            ("points", 0, "task_graph", "buffers", 6, "offset_bytes"),
            16777216,
            "SramCapacityExceeded",
        ),
        ("R11", ("points", 0, "task_graph", "jobs", 2, "core_id"), 4, "InvalidResource"),
        (
            "R12",
            ("points", 0, "task_graph", "dependencies", 0, "before"),
            "missing",
            "InvalidDependency",
        ),
        ("R13", ("hardware_spec_hash",), "sha256:" + "0" * 64, "HardwareMismatch"),
        ("R19", ("scope", "ops", 0, "work_repeat"), 2, "UnsupportedCapability"),
        ("R21", ("points", 0, "frequency_ratio"), 0, "greater than"),
    ],
)
def test_rehashed_refusals(rid: Any, path: Any, value: Any, error: Any) -> None:
    b = load("component")
    cursor = b
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    seal(b)
    with pytest.raises(ValueError, match=error):
        check(b)


def test_r01_protocol_and_old_roots_strict() -> None:
    from rkuarch.engines.protocol import EngineJob
    from rkuarch.engines.protocol_v2 import EngineJobV2

    for version in ("uarch-engine/1", "uarch-engine/2"):
        raw = load("kernel-job")
        raw["protocol"] = version
        with pytest.raises(ValueError):
            MappedEngineJob.model_validate(raw)
    for root in (EngineJob, EngineJobV2):
        with pytest.raises(ValueError):
            root.model_validate(load("kernel-job"))


def test_r14_explicit_requested_coverage() -> None:
    with pytest.raises(ValueError, match="MissingCoverage"):
        check(load("component"), point_hash="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="HardwareMismatch"):
        check(load("component"), hardware_hash="sha256:" + "0" * 64)


def test_r15_fixture_cannot_be_component_or_product() -> None:
    b = load("component")
    b["points"][0]["task_graph"]["jobs"][2] = {
        "kind": "fixed_delay",
        "id": "c",
        "duration_ps": 0,
        "owner_id": 0,
    }
    b["points"][0]["task_graph"]["coverage"] = []
    seal(b)
    with pytest.raises(ValueError, match="TestOnlyScope"):
        check(b)
    with pytest.raises(ValueError, match="TestOnlyScope"):
        admit(
            load("kernel"),
            invocation="test",
            checkpoint="K2",
            registry=load("registry"),
            profile=load("profile"),
            product=True,
        )


def test_r16_r20_no_success_from_missing_observations() -> None:
    job = MappedEngineJob.model_validate(load("kernel-job"))
    # Deliberately incomplete wire projections: never serialized as a completed fixture.
    with pytest.raises(ValueError):
        validate_result({"protocol": "uarch-engine/3", "completion": "incomplete"}, job)
    with pytest.raises(ValueError):
        MappedEngineResult.model_validate({"protocol": "uarch-engine/3", "completion": "complete"})


def test_r17_r18_job_fidelity_and_hardware() -> None:
    b = load("component")
    b["hardware_spec"]["id"] = "different-design"
    b["hardware_spec_hash"] = content_hash(b["hardware_spec"])
    seal(b)
    with pytest.raises(ValueError, match="UnsupportedHardware"):
        check(b)
    job = load("kernel-job")
    job["fidelity_detail"] = {
        "compute": 1,
        "noc": 0,
        "dram": 0,
        "sync": "exact",
        "layer_reuse": False,
    }
    rehash(job, "job_hash")
    with pytest.raises(ValueError, match="UnsupportedFidelity"):
        MappedEngineJob.model_validate(job)


def test_strict_scalars_duplicates_unknown_and_stale() -> None:
    b = load("component")
    b["rank"]["tp"] = True
    with pytest.raises(ValueError):
        check(seal(b))
    b = load("component")
    b["unexpected"] = 1
    with pytest.raises(ValueError):
        check(seal(b))
    b = load("component")
    b["points"][0]["task_graph"]["jobs"][0]["id"] = "changed"
    with pytest.raises(ValueError, match="HashMismatch"):
        check(b)
    with pytest.raises(ValueError, match="DuplicateJsonKey"):
        strict_json_loads('{"id":1,"id":2}')
    with pytest.raises(ValueError, match="NonFinite"):
        strict_json_loads('{"duration_ps":NaN}')


def test_graph_cycles_coverage_and_u64() -> None:
    g = load("kernel")["points"][0]["task_graph"]
    g["dependencies"].append({"before": "c", "after": "a"})
    g["dependencies"].sort(key=lambda edge: (edge["before"], edge["after"]))
    rehash(g, "graph_hash")
    with pytest.raises(ValueError, match="InvalidDependency"):
        TaskGraph.model_validate(g)
    g = load("kernel")["points"][0]["task_graph"]
    g["jobs"][0]["duration_ps"] = 2**64
    with pytest.raises(ValueError):
        TaskGraph.model_validate(g)


def test_schema_freshness_and_mutation(tmp_path: Any) -> None:
    from uarch_contract.generate_mapped import generate

    assert generate(check=True) == []
    generate(tmp_path)
    target = tmp_path / "TaskGraph.json"
    target.write_text("{}\n")
    assert "TaskGraph.json" in generate(tmp_path, check=True)
    assert json.loads(target.read_text()) == {}  # read-only check


def model_wrapper(version: Any) -> Any:
    import runpy

    cases = runpy.run_path(str(FIXTURES.parents[1] / "tests/rotary_v2_cases.py"))
    example = cases["examples"]()
    if version == 2:
        source, assumptions = example["bundle"], example["assumptions"]
    else:
        source = json.loads(
            (FIXTURES.parents[1] / "tests/fixtures/u2/independent-bundle.json").read_text()
        )
        # A distinct explicit source fixture identity; never relabel the historical bytes.
        assumptions = copy.deepcopy(example["assumptions"])
        assumptions["model"]["version"] = "1"
        rehash(assumptions, "assumptions_hash")
        source["intent"]["assumptions_hash"] = assumptions["assumptions_hash"]
        source["intent_hash"] = content_hash(source["intent"])
        rehash(source, "bundle_hash")
    b = load("component")
    original = source["points"][0]
    b["source"] = {
        "format": source["format"],
        "bundle_hash": source["bundle_hash"],
        "bundle": source,
        "assumptions": assumptions,
    }
    b["scope"] = {"kind": "prepared_model", "selected_point_hashes": [original["payload_hash"]]}
    b["points"][0]["identity"] = {
        "kind": "prepared_model",
        "original_point_hash": original["payload_hash"],
        "query": original["query"],
    }
    return seal(b)


@pytest.mark.parametrize("version", [1, 2], ids=["R02", "R03"])
def test_original_authenticated_model_refused_before_mapping_semantics(version: Any) -> None:
    b = model_wrapper(version)
    MappedBundle.model_validate(b)  # closure syntax/identity, not model graph admission
    with pytest.raises(ValueError, match="UnsupportedWorkloadScope"):
        check(b)


def test_r13_v2_coefficient_tamper_precedes_scope_refusal() -> None:
    b = model_wrapper(2)
    b["source"]["bundle"]["coefficients"]["cos_bits"][0][0] = "00000000"
    rehash(b["source"]["bundle"], "bundle_hash")
    b["source"]["bundle_hash"] = b["source"]["bundle"]["bundle_hash"]
    seal(b)
    with pytest.raises(ValueError, match="HashMismatch"):
        check(b)


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("live_alias", "LiveBufferAlias"),
        ("bank", "InvalidBank"),
        ("missing_hop", "InvalidRoute"),
        ("stripe", "InvalidTransfer"),
        ("coverage", "InvalidCoverage"),
        ("missing_producer", "InvalidDependency"),
        ("assumptions", "ContentHashMismatch"),
        ("multicast", "literal_error"),
        ("rotary_v1", "type=enum"),
        ("unknown_job", "union_tag_invalid"),
        ("negative_delay", "greater_than_equal"),
        ("boolean_delay", "int_type"),
    ],
)
def test_additional_rehashed_attacks(mutation: Any, error: Any) -> None:
    b = load("component")
    g = b["points"][0]["task_graph"]
    byid = {x["id"]: x for x in g["buffers"]}
    if mutation == "live_alias":
        byid["sw"]["offset_bytes"] = 0
    elif mutation == "bank":
        byid["sx"]["bank"] = 1
    elif mutation == "missing_hop":
        g["routes"][1]["core_ids"] = [0]
    elif mutation == "stripe":
        g["jobs"][0]["fragments"][0]["channel_id"] = 7
    elif mutation == "coverage":
        g["coverage"].append(copy.deepcopy(g["coverage"][0]))
    elif mutation == "missing_producer":
        byid["sx"]["producer_id"] = None
    elif mutation == "assumptions":
        b["assumptions_hash"] = "sha256:" + "0" * 64
    elif mutation == "multicast":
        g["jobs"][0] = {
            "kind": "noc_transfer",
            "id": "a",
            "op_id": None,
            "source": {"buffer_id": "sx", "offset_bytes": 0, "size_bytes": 30},
            "destination": {"buffer_id": "sw", "offset_bytes": 0, "size_bytes": 30},
            "payload_bytes": 30,
            "route_id": "r0",
            "multicast": True,
        }
    elif mutation == "rotary_v1":
        b["scope"]["ops"][0]["spec"]["operator"] = "rotary_embedding"
    elif mutation == "unknown_job":
        g["jobs"][0]["kind"] = "cancel"
    else:
        b = load("kernel")
        b["points"][0]["task_graph"]["jobs"][0]["duration_ps"] = (
            -1 if mutation == "negative_delay" else True
        )
    seal(b)
    with pytest.raises(ValueError, match=error):
        check(b)


def test_fixture_registry_is_content_bound_and_production_denied() -> None:
    b = load("component")
    b["hardware_spec"]["id"] = "test-only-renamed-file-is-irrelevant"
    b["hardware_spec_hash"] = content_hash(b["hardware_spec"])
    seal(b)
    r = load("registry")
    r["test_only_specs"] = [
        {
            "hardware_spec_hash": b["hardware_spec_hash"],
            "rationale": "schema registry refusal control",
        }
    ]
    rehash(r, "registry_hash")
    with pytest.raises(ValueError, match="TestOnlyHardware"):
        admit(b, invocation="production", checkpoint="B", registry=r, profile=None)
    r["test_only_specs"][0]["rationale"] += " tampered"
    with pytest.raises(ValueError, match="HashMismatch"):
        admit(b, invocation="production", checkpoint="B", registry=r, profile=None)


def test_job_closure_and_native_count_channels() -> None:
    from uarch_contract.mapped import Observations, TrafficCounts, WorkCounts

    j = load("kernel-job")
    assert MappedEngineJob.model_validate(j)
    j["seed"] = 1
    rehash(j, "job_hash")
    with pytest.raises(ValueError, match="TestVariantNotAdmitted"):
        MappedEngineJob.model_validate(j)
    work = {
        "format": "uarch-native-work-counts/1",
        "completed_mac_count": 105,
        "issued_matrix_ops": 393216,
        "vector_arithmetic_ops": 0,
        "cast_ops": 0,
    }
    traffic = {
        "format": "uarch-native-traffic-counts/1",
        "read_payload_bytes": 100,
        "write_payload_bytes": 42,
        "read_transaction_bytes": 512,
        "write_transaction_bytes": 256,
        "unicast_payload_bytes": 0,
    }
    assert WorkCounts.model_validate(work).completed_mac_count == 105
    assert TrafficCounts.model_validate(traffic).write_payload_bytes == 42
    # These are field projections, never a completed native result.
    work["completed_mac_count"] = True
    with pytest.raises(ValueError):
        WorkCounts.model_validate(work)
    with pytest.raises(ValueError):
        Observations.model_validate({"format": "uarch-native-observations/1"})


def test_untrusted_registry_cannot_authorize_job() -> None:
    from uarch_contract.mapped import validate_job

    raw = load("kernel-job")
    parsed = MappedEngineJob.model_validate(raw)
    with pytest.raises(ValueError, match="RegistryTrustMismatch"):
        validate_job(
            raw,
            invocation="test",
            checkpoint="K2",
            trusted_registry_hash="sha256:" + "0" * 64,
            trusted_profile_hash=raw["profile"]["profile_hash"],
            expected_engine=parsed.engine,
        )
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        validate_job(
            raw,
            invocation="test",
            checkpoint="K2",
            trusted_registry_hash=raw["registry"]["registry_hash"],
            trusted_profile_hash="sha256:" + "0" * 64,
            expected_engine=parsed.engine,
        )


def test_clock_setup_must_be_in_profile() -> None:
    j = load("kernel-job")
    j["clock_setup"] = [{"job_id": "a", "domain": "core", "start_ps": 0, "n_cycles": 3}]
    rehash(j, "job_hash")
    with pytest.raises(ValueError, match="TestProfileMismatch.*clock setup"):
        MappedEngineJob.model_validate(j)


def test_second_slot_and_lifetime_inventory() -> None:
    b = load("component")
    b["points"][0]["task_graph"]["buffers"] = [
        x for x in b["points"][0]["task_graph"]["buffers"] if x["id"] != "slot1"
    ]
    with pytest.raises(ValueError, match="CapacityExceeded.*second slot"):
        check(seal(b))
    b = load("component")
    next(x for x in b["points"][0]["task_graph"]["buffers"] if x["id"] == "sx")[
        "final_consumer_ids"
    ] = []
    with pytest.raises(ValueError, match="InvalidDependency.*final consumers"):
        check(seal(b))


def test_component_16_positive_17_refusal() -> None:
    b = load("component")
    original = copy.deepcopy(b)
    graph = b["points"][0]["task_graph"]
    graph["buffers"], graph["jobs"], graph["dependencies"], graph["coverage"] = [], [], [], []
    b["scope"]["ops"], b["scope"]["op_ids"] = [], []
    for index in range(16):
        prefix = f"g{index:02d}"
        op = copy.deepcopy(original["scope"]["ops"][0])
        op["id"] = prefix
        b["scope"]["ops"].append(op)
        b["scope"]["op_ids"].append(prefix)
        old = copy.deepcopy(original["points"][0]["task_graph"])
        for buf in old["buffers"]:
            buf["id"] = prefix + "." + buf["id"]
            buf["op_id"] = prefix
            buf["offset_bytes"] += index * (
                2048 if buf["space"] == "hbm" else 1536 if buf["space"] == "sram" else 256
            )
            if buf["producer_id"] is not None:
                buf["producer_id"] = prefix + "." + buf["producer_id"]
            buf["final_consumer_ids"] = [prefix + "." + x for x in buf["final_consumer_ids"]]
        for job in old["jobs"]:
            job["id"] = prefix + "." + job["id"]
            job["op_id"] = prefix
            if job["kind"] == "compute":
                job["operand_buffers"] = {
                    k: prefix + "." + v for k, v in job["operand_buffers"].items()
                }
                job["accumulator_buffer_id"] = prefix + "." + job["accumulator_buffer_id"]
            else:
                for field in ("source", "destination"):
                    job[field]["buffer_id"] = prefix + "." + job[field]["buffer_id"]
                for fragment in job["fragments"]:
                    fragment["request_id"] = prefix + "." + fragment["request_id"]
        for edge in old["dependencies"]:
            for field in ("before", "after"):
                edge[field] = prefix + "." + edge[field]
        for item in old["coverage"]:
            item["job_id"] = prefix + "." + item["job_id"]
            item["op_id"] = prefix
        for field in ("buffers", "jobs", "dependencies", "coverage"):
            graph[field].extend(old[field])
    b["points"][0]["identity"]["op_ids"] = b["scope"]["op_ids"]
    assert check(seal(b))
    b["scope"]["ops"].append(copy.deepcopy(b["scope"]["ops"][-1]))
    with pytest.raises(ValueError, match="at most 16"):
        check(seal(b))


@pytest.mark.parametrize("dtype", ["fp16", "fp32", "fp8"])
def test_every_unsupported_precision(dtype: str) -> None:
    b = load("component")
    for operand in b["scope"]["ops"][0]["spec"]["operands"].values():
        operand["dtype"] = dtype
    with pytest.raises(ValueError, match="UnsupportedPrecision"):
        check(seal(b))


def test_canonical_vectors_are_protected_input_controls() -> None:
    from uarch_contract.hashing import canonical_json, sha256

    for vector in load("canonical-vectors"):
        encoded = canonical_json(strict_json_loads(vector["input_json"]))
        assert encoded == vector["canonical_utf8"]
        assert sha256(encoded) == vector["sha256"]


def test_no_numeric_coercion_in_native_counts_or_fidelity() -> None:
    from uarch_contract.mapped import NativeCounts, NativeFidelity

    for value in (True, "1", float("inf")):
        with pytest.raises(ValueError):
            NativeCounts.model_validate(
                {
                    "matrix_ops": value,
                    "vector_ops": 0,
                    "memory_read_bytes": 0,
                    "memory_write_bytes": 0,
                }
            )
    with pytest.raises(ValueError, match="UnsupportedFidelity"):
        NativeFidelity.model_validate(
            {"compute": True, "noc": 0, "dram": 0, "sync": "exact", "layer_reuse": False}
        )


@pytest.mark.parametrize("name", ["transport", "resident"])
def test_positive_b_fixture_admission(name: str) -> None:
    assert admit(
        load(name),
        invocation="test",
        checkpoint="B",
        registry=load("registry"),
        profile=load(name + "-profile"),
    )


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("M1025", "UnsupportedShape"),
        ("padding", "UnsupportedShape"),
        ("pp", "extra_forbidden"),
        ("priming", "UnsupportedInitialState"),
        ("dataflow", "UnsupportedMapping"),
        ("kv_write", "UnsupportedOperator"),
        ("attention_fused", "UnsupportedOperator"),
        ("paged", "UnsupportedCapability"),
        ("retry", "extra_forbidden"),
        ("spill", "extra_forbidden"),
        ("bias", "extra_forbidden"),
        ("sparsity", "extra_forbidden"),
        ("stripe-cross", "InvalidTransfer"),
    ],
)
def test_remaining_input_refusal_variants(mutation: str, error: str) -> None:
    b = load("component")
    op = b["scope"]["ops"][0]
    g = b["points"][0]["task_graph"]
    if mutation == "M1025":
        op["spec"]["dimensions"]["M"] = 1025
    elif mutation == "padding":
        op["padding"] = [{"dimension": "K", "logical": 4, "physical": 5}]
    elif mutation == "pp":
        b["rank"]["pp"] = 2
    elif mutation == "priming":
        b["points"][0]["priming_iterations"] = 1
    elif mutation == "dataflow":
        g["jobs"][2]["dataflow"] = "output_stationary"
    elif mutation == "attention_fused":
        original = json.loads(
            (FIXTURES.parents[1] / "tests/fixtures/u2/independent-bundle.json").read_text()
        )
        op["spec"] = next(
            item["spec"]
            for group in original["points"][0]["graph"]["groups"]
            for item in group["ops"]
            if item["spec"]["operator"] == "attention_fused"
        )
    elif mutation == "kv_write":
        op["spec"]["operator"] = mutation
    elif mutation == "paged":
        op["spec"]["operands"]["X"].update(layout="paged", block_size_tokens=16)
    elif mutation == "stripe-cross":
        hx = next(x for x in g["buffers"] if x["id"] == "hx")
        hx.update(offset_bytes=2048, size_bytes=512)
        g["jobs"][0]["source"]["offset_bytes"] = 255
        g["jobs"][0]["fragments"][0]["source_offset_bytes"] = 255
    else:
        g["jobs"][2][mutation] = True
    with pytest.raises(ValueError, match=error):
        check(seal(b))


def test_literal_integer_and_boolean_types_are_not_interchangeable() -> None:
    from uarch_contract.mapped import Buffer, ComponentScope, NocTransfer

    scope = load("component")["scope"]
    scope["repeat"] = True
    with pytest.raises(ValueError):
        ComponentScope.model_validate(scope)
    buffer = next(
        x for x in load("component")["points"][0]["task_graph"]["buffers"] if x["id"] == "sx"
    )
    buffer["slot_index"] = False
    with pytest.raises(ValueError):
        Buffer.model_validate(buffer)
    with pytest.raises(ValueError):
        NocTransfer.model_validate(
            {
                "kind": "noc_transfer",
                "id": "t",
                "op_id": None,
                "source": {"buffer_id": "x", "offset_bytes": 0, "size_bytes": 1},
                "destination": {"buffer_id": "y", "offset_bytes": 0, "size_bytes": 1},
                "payload_bytes": 1,
                "route_id": "r",
                "multicast": 0,
            }
        )


def test_frozen_nonempty_clock_setup_positive_and_rehashed_refusal() -> None:
    from uarch_contract.mapped import validate_job

    j = load("kernel-job")
    j["mapped_point"]["task_graph"]["jobs"][0]["duration_ps"] = 0
    rehash(j["mapped_point"]["task_graph"], "graph_hash")
    rehash(j["mapped_point"], "payload_hash")
    j["point_hash"] = j["mapped_point"]["payload_hash"]
    j["workload_closure"]["points"] = [copy.deepcopy(j["mapped_point"])]
    j["profile"]["entries"][0]["graph_hash"] = j["mapped_point"]["task_graph"]["graph_hash"]
    j["profile"]["entries"][0]["point_hash"] = j["point_hash"]
    j["clock_setup"] = [{"job_id": "a", "domain": "core", "start_ps": 0, "n_cycles": 3}]
    j["profile"]["entries"][0]["clock_setup_hash"] = content_hash(j["clock_setup"])
    rehash(j["profile"], "profile_hash")
    anchor = j["profile"]["profile_hash"]  # explicit test-host authority, not caller trust
    j["admission"]["profile_hash"] = anchor
    j["workload_closure"]["admission"]["profile_hash"] = anchor
    rehash(j["workload_closure"], "bundle_hash")
    j["bundle_hash"] = j["workload_closure"]["bundle_hash"]
    rehash(j, "job_hash")
    parsed = MappedEngineJob.model_validate(j)
    assert validate_job(
        j,
        invocation="test",
        checkpoint="K2",
        expected_engine=parsed.engine,
        trusted_registry_hash=j["registry"]["registry_hash"],
        trusted_profile_hash=anchor,
    )
    j["clock_setup"][0]["n_cycles"] = 4
    rehash(j, "job_hash")
    with pytest.raises(ValueError, match="TestProfileMismatch.*clock setup"):
        validate_job(
            j,
            invocation="test",
            checkpoint="K2",
            expected_engine=parsed.engine,
            trusted_registry_hash=j["registry"]["registry_hash"],
            trusted_profile_hash=anchor,
        )
    # Rehashing the caller's profile too cannot replace the independently held anchor.
    j["profile"]["entries"][0]["clock_setup_hash"] = content_hash(j["clock_setup"])
    rehash(j["profile"], "profile_hash")
    j["admission"]["profile_hash"] = j["profile"]["profile_hash"]
    j["workload_closure"]["admission"]["profile_hash"] = j["profile"]["profile_hash"]
    rehash(j["workload_closure"], "bundle_hash")
    j["bundle_hash"] = j["workload_closure"]["bundle_hash"]
    rehash(j, "job_hash")
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        validate_job(
            j,
            invocation="test",
            checkpoint="K2",
            expected_engine=parsed.engine,
            trusted_registry_hash=j["registry"]["registry_hash"],
            trusted_profile_hash=anchor,
        )
