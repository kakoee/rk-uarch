"""Exact proposal shape/constraint review only; synthetic values confer no authority."""

import copy
import hashlib
import json
import tomllib
from pathlib import Path

import pytest
import record_models as m
from uarch_contract.hashing import content_hash

A = Path(m.__file__).resolve().parent
ROOT = A.parents[2]
H = "sha256:" + "1" * 64
OTHER = "sha256:" + "2" * 64
F = dict(path="synthetic/input.json", byte_hash=H)
ENGINE = dict(
    name="native",
    version="native-stage/1",
    implementation_hash=H,
    compiler_lock_hash=H,
    model=dict(name="fixed-delay", version="1", implementation_hash=H),
)


def shapes():
    case = dict(
        case_id="synthetic",
        graph_hash=H,
        point_hash=H,
        hardware_spec_hash=H,
        clock_setup_hash=H,
        seed=0,
        execution_outcome="success",
    )
    trust = dict(
        format="uarch-k2-build-trust/1",
        purpose="construction-test-only",
        semantics_file=F,
        registry_hash=H,
        registry_file=F,
        profiles=[dict(profile_hash=H, file=F, cases=[case])],
        corpus_inventory=F,
    )
    tool = dict(
        format="uarch-k2-tool-inputs/1",
        accepted_k1_pins=F,
        compiler_commit="1" * 40,
        rust_release="1.99.0",
        target="x86_64-unknown-linux-gnu",
        image_digest=H,
        cargo_lock=F,
        full_metadata=F,
        target_metadata=F,
        feature_graph=F,
        licence_inventory=F,
        crate_checksum_inventory=F,
        linker_and_os_inventory=F,
        flags=[],
    )
    source = dict(path="src/example.rs", byte_hash=H, role="rust")
    build = dict(
        format="uarch-k2-build-inputs/1",
        source_commit="1" * 40,
        source_files=[source],
        trust_hash=H,
        trust_file=F,
        tool_inputs_hash=H,
        tool_inputs_file=F,
        model_source_paths=["src/example.rs"],
        model_inputs_hash=H,
        mode_configs=[dict(mode=x, cargo_args=[], rustflags=[]) for x in ("debug", "release")],
        generated_identity_output_paths=["generated/identity.rs"],
        permitted_environment={},
    )
    receipt = dict(
        format="uarch-k2-build-receipt/1",
        build_input_hash=H,
        engine=ENGINE,
        mode="debug",
        target="x86_64-unknown-linux-gnu",
        executable=F,
        image_digest=H,
        generated_identity_outputs=[F],
        actual_read_inventory=F,
        actual_environment=F,
        compiler_verbose=F,
        build_log=F,
        binary_origin_check=F,
        software_path_check=F,
    )
    host = dict(
        format="uarch-k2-first-use/1",
        decision=F,
        independent_review=F,
        semantics=F,
        trust_hash=H,
        trust_file=F,
        build_input_hash=H,
        build_input_file=F,
        tool_inputs_hash=H,
        model_inputs_hash=H,
        loader_read_inventory=F,
        expected_engine=ENGINE,
        executables=[
            dict(mode=x, executable=F, build_receipt=F, target="x86_64-unknown-linux-gnu")
            for x in ("debug", "release")
        ],
        jobs_inventory=F,
        corpus_inventory=F,
        profile_hashes=[H],
        registry_hash=H,
    )
    selector = dict(
        format="uarch-k2-host-selector/1",
        repository="synthetic-not-authority",
        acceptance_commit="1" * 40,
        record_path="synthetic/record.json",
        record_byte_hash=H,
    )
    return dict(
        BuildTrust=trust,
        ToolInputs=tool,
        BuildInputs=build,
        BuildReceipt=receipt,
        HostRecord=host,
        HostSelector=selector,
    )


@pytest.mark.parametrize("name", [x.__name__ for x in m.ROOTS])
def test_six_exact_shapes_and_mirrors(name, tmp_path):
    model = getattr(m, name)
    model.model_validate(shapes()[name])
    m.schemas(tmp_path)
    assert (tmp_path / (name + ".json")).read_bytes() == (
        A / "record-schemas" / (name + ".json")
    ).read_bytes()
    with pytest.raises(ValueError):
        model.model_validate(dict(shapes()[name], invented_authority=True))


def test_declared_identity_guards_and_nonrecursive_order():
    values = shapes()
    for field in ("engine", "job_hash", "binary_hash", "host_record_hash"):
        with pytest.raises(ValueError):
            m.BuildTrust.model_validate(dict(values["BuildTrust"], **{field: H}))
    bad = copy.deepcopy(values["BuildInputs"])
    bad["generated_identity_output_paths"] = ["src/example.rs"]
    with pytest.raises(ValueError, match="cannot hash itself"):
        m.BuildInputs.model_validate(bad)
    for field in ("model_source_paths", "mode_configs"):
        bad = copy.deepcopy(values["BuildInputs"])
        bad[field] = ["missing.rs"] if field == "model_source_paths" else [bad[field][0]] * 2
        with pytest.raises(ValueError):
            m.BuildInputs.model_validate(bad)
    with pytest.raises(ValueError, match="Engine/build input mismatch"):
        m.BuildReceipt.model_validate(dict(values["BuildReceipt"], build_input_hash=OTHER))
    for field in ("build_input_hash", "tool_inputs_hash", "model_inputs_hash"):
        with pytest.raises(ValueError, match="Final identity joins"):
            m.HostRecord.model_validate(dict(values["HostRecord"], **{field: OTHER}))
    bad = copy.deepcopy(values["HostRecord"])
    bad["executables"] = [bad["executables"][0]] * 2
    with pytest.raises(ValueError, match="Both actual executable"):
        m.HostRecord.model_validate(bad)
    with pytest.raises(ValueError):
        m.HostRecord.model_validate(dict(values["HostRecord"], acceptance_commit="1" * 40))
    # Changing model bytes changes the independently hashed subset, not just path names.
    source = values["BuildInputs"]["source_files"]
    assert content_hash(source) != content_hash([dict(source[0], byte_hash=OTHER)])


def test_shape_checks_do_not_claim_a_working_cross_file_resolver():
    values = shapes()
    # All these shapes parse. The declared future resolver MUST refuse their joins.
    # Neither a file nor any qualifying authority/decision is created by this test.
    m.HostRecord.model_validate(dict(values["HostRecord"], registry_hash=OTHER))
    m.BuildReceipt.model_validate(dict(values["BuildReceipt"], image_digest=OTHER))
    m.BuildInputs.model_validate(dict(values["BuildInputs"], model_inputs_hash=OTHER))
    m.BuildInputs.model_validate(dict(values["BuildInputs"], source_commit="2" * 40))
    m.HostSelector.model_validate(dict(values["HostSelector"], record_byte_hash=OTHER))
    # Reusing the same synthetic executable path/digest for both modes is shape-valid,
    # not evidence of two actual builds, actual source origin, or host installation.
    host = m.HostRecord.model_validate(values["HostRecord"])
    assert host.executables[0].executable == host.executables[1].executable


def entries_allowed(entries, plan):
    """Finite allowlist predicate; input here is a synthetic lock-entry mutation control."""
    old = plan["existing_packages_must_retain"]
    added = [
        {k: x[k] for k in ("name", "version", "checksum")}
        | {"source": "registry+https://github.com/rust-lang/crates.io-index"}
        for x in plan["only_permitted_additional_packages"]
    ]

    def key(x):
        return (x["name"], x["version"])

    assert len(entries) == len({key(x) for x in entries})
    assert sorted(entries, key=key) == sorted(old + added, key=key)


def test_c1_exact_old_lock_and_candidate_allowlist():
    plan = json.loads((A / "construction-plan.json").read_bytes())
    lock = (ROOT / "native/Cargo.lock").read_bytes()
    assert hashlib.sha256(lock).hexdigest() == plan["existing_lock_sha256"]
    old = [
        {k: x[k] for k in ("name", "version", "source", "checksum") if k in x}
        for x in tomllib.loads(lock.decode())["package"]
    ]
    assert old == plan["existing_packages_must_retain"]
    added = [
        {k: x[k] for k in ("name", "version", "checksum")}
        | {"source": "registry+https://github.com/rust-lang/crates.io-index"}
        for x in plan["only_permitted_additional_packages"]
    ]
    entries = old + added  # synthetic constraint vector, NOT a resolved lock or graph
    entries_allowed(entries, plan)
    bad_sets = [
        entries[1:],
        entries[:-1],
        entries + [entries[-1]],
        entries + [dict(name="unapproved", version="1", source="registry", checksum="0" * 64)],
    ]
    for field, value in [
        ("version", "0"),
        ("checksum", "0" * 64),
        ("source", "git+https://invalid"),
    ]:
        changed = copy.deepcopy(entries)
        changed[0][field] = value
        bad_sets.append(changed)
    for bad in bad_sets:
        with pytest.raises(AssertionError):
            entries_allowed(bad, plan)
        entries_allowed(entries, plan)
    assert plan["direct_dependencies"]["sha2"] == dict(
        version="=0.10.9", default_features=False, features=["std", "force-soft"]
    )
    assert plan["direct_dependencies"]["serde_json"]["features"] == [
        "std",
        "float_roundtrip",
        "arbitrary_precision",
    ]
    assert plan["target"] == "x86_64-unknown-linux-gnu" and plan["new_git_dependencies"] is False
    assert plan["network_sources"] == [
        "https://index.crates.io/",
        "https://static.crates.io/crates/",
    ]
