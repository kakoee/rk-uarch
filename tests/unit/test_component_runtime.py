"""Synthetic component integration; no selector, human decision or public authority."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json, content_hash

from rkuarch.engines.native import component_host, component_runner

ROOT = Path(__file__).resolve().parents[2]


def prospective_pair():
    """Explicit new profile/2 identity; preserve every historical input/output."""
    old = ROOT / "docs/reviews/U4-A-issue-edge-stage2-v1/private-probes/cc0-v3"
    job = json.loads((old / "job.json").read_bytes())
    profile = job["profile"]
    profile["format"] = "uarch-native-test-profile/2"
    for entry in profile["entries"]:
        entry["mapping_policy"] = job["workload_closure"]["mapping_policy"]
    profile["profile_hash"] = content_hash(profile, exclude=("profile_hash",))
    closure = job["workload_closure"]
    closure["admission"]["profile_hash"] = profile["profile_hash"]
    closure["bundle_hash"] = content_hash(closure, exclude=("bundle_hash",))
    job["bundle_hash"] = closure["bundle_hash"]
    job["admission"] = deepcopy(closure["admission"])
    job["job_hash"] = content_hash(job, exclude=("job_hash",))
    result = json.loads((old / "debug.json").read_bytes())
    result.update(job_hash=job["job_hash"], admission=job["admission"], engine=job["engine"])
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    return job, result


def test_component_public_entry_requires_its_own_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(component_host, "_SELECTOR", tmp_path / "absent-selector.json")
    with pytest.raises((OSError, ValueError)):
        component_host.prepare_component(mode="debug")
    with pytest.raises(ValueError, match="component authority"):
        component_runner.run_component(tmp_path / "absent-job", session=object())


def test_component_route_is_job_selected_before_output_consumer():
    job, result = prospective_pair()
    component_runner.require_route(job, result)
    for model, observations in [
        ("1", "uarch-native-observations/3"),
        ("2", "uarch-native-observations/2"),
    ]:
        badjob, badresult = deepcopy(job), deepcopy(result)
        badjob["engine"]["model"]["version"] = model
        badresult["observations"]["format"] = observations
        with pytest.raises(ValueError, match="model/observation/checker"):
            component_runner.require_route(badjob, badresult)


def test_saved_result_core_uses_both_consumers_and_no_producers(monkeypatch):
    job, result = prospective_pair()
    expected = json.loads(
        (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
    )["observation_contract"]
    import rkuarch.workload.mapped as imported

    def unavailable(*args, **kwargs):
        raise AssertionError("producer unavailable")

    monkeypatch.setattr(imported, "export_component_job", unavailable)
    checked = component_runner.validate_component_response(
        canonical_json(result).encode(), b"", 0, job=job, observation_contract=expected
    )
    assert checked.observations.format == "uarch-native-observations/3"
    assert checked.duration_ps == 121000
    # Resealed invalid predecessor exercises structural refusal through the runner.
    # Historical A7 cursor discrimination is separate, inherited evidence.
    first = next(
        a
        for a in result["observations"]["activities"]["records"]
        if a["request_id"] == "r02.00" and a["kind"] == "alignment" and a["subphase"] == "dma_issue"
    )
    first["predecessors"].append({"activity_id": "activity-00000027", "relation": "credit"})
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    with pytest.raises(ValueError):
        component_runner.validate_component_response(
            canonical_json(result).encode(), b"", 0, job=job, observation_contract=expected
        )


@pytest.fixture
def prepared_payload(tmp_path):
    """Synthetic record graph + shell echo executable. Not a native build or authority."""
    import importlib.util
    import shutil

    from rkuarch.engines.native.component_records import IMAGE
    from rkuarch.engines.native.records import FileBinding, ToolInputs

    spec = importlib.util.spec_from_file_location(
        "private_recipe", ROOT / "native/tools/component_runtime_candidate.py"
    )
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    job, result = prospective_pair()

    def put(name, value):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(value))
        return recipe.binding(tmp_path, path)

    semantics = put("semantics.json", {"synthetic": True})
    registry = put("registry.json", job["registry"])
    profile = put("profile.json", job["profile"])
    row = {
        "case_id": job["admission"]["case_id"],
        "expected_layer": "result",
        "profile": job["profile"],
        "bundle_hash": job["bundle_hash"],
        "point_hash": job["point_hash"],
        "graph_hash": job["mapped_point"]["task_graph"]["graph_hash"],
        "policy": job["workload_closure"]["mapping_policy"],
    }
    selection = put(
        "selection.json",
        {
            "format": "B-component-prospective-v3-selection/1",
            "model": ["native-intervals", "2"],
            "observations": "uarch-native-observations/3",
            "checker": "validation.component.observations_v3:check_v3",
            "rows": [row],
        },
    )
    trust = {
        "format": "uarch-component-build-trust/2",
        "purpose": "private-synthetic-tests-only",
        "semantics_file": semantics,
        "registry_hash": job["registry"]["registry_hash"],
        "registry_file": registry,
        "profiles": [profile],
        "selection": selection,
    }
    trust_file = put("trust.json", trust)
    tools_path = ROOT / "docs/reviews/U4-A-K2-construction-v1/candidate-04/ToolInputs.json"
    tools = ToolInputs.model_validate_json(tools_path.read_bytes())
    for value in tools.model_dump(mode="json").values():
        if isinstance(value, dict) and "path" in value:
            dest = tmp_path / value["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / value["path"], dest)
    put(
        "private-component/observation-contract.json",
        json.loads(
            (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
        )["observation_contract"],
    )
    consumers = recipe.imports(ROOT, tmp_path)
    # The import recipe's expected observation file belongs to this synthetic data root.
    consumers["observation_contract"] = recipe.binding(
        tmp_path, tmp_path / "private-component/observation-contract.json"
    )
    sources = []
    for f in consumers["files"]:
        dest = tmp_path / f["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / f["path"], dest)
        sources.append(dict(f, role="config"))
    sources.append({**tools.cargo_lock.model_dump(mode="json"), "role": "config"})
    sources.sort(key=lambda f: f["path"])
    model = [sources[0]]
    build = {
        "format": "uarch-component-build-inputs/2",
        "source_commit": "0" * 40,
        "source_files": sources,
        "trust_hash": content_hash(trust),
        "trust_file": trust_file,
        "tool_inputs_hash": content_hash(tools),
        "tool_inputs_file": put("tools.json", tools),
        "model_source_paths": [model[0]["path"]],
        "model_inputs_hash": content_hash(model),
        "mode_configs": [
            {"mode": m, "cargo_args": ["synthetic"], "rustflags": list(tools.flags)}
            for m in ("debug", "release")
        ],
        "generated_identity_output_paths": ["native/crates/uarch-engine/generated/identity.rs"],
        "permitted_environment": {},
    }
    build_file = put("build.json", build)
    engine = deepcopy(job["engine"])
    engine.update(implementation_hash=content_hash(build), compiler_lock_hash=content_hash(tools))
    engine["model"]["implementation_hash"] = content_hash(model)
    job["engine"] = engine
    job["job_hash"] = content_hash(job, exclude=("job_hash",))
    result.update(job_hash=job["job_hash"], engine=engine)
    result["result_hash"] = content_hash(result, exclude=("result_hash",))
    job_file = put("job.json", job)
    put("output.json", result)
    executable = tmp_path / "synthetic-echo"
    executable.write_text("#!/bin/sh\nexec /bin/cat '" + str(tmp_path / "output.json") + "'\n")
    executable.chmod(0o555)
    exe = recipe.binding(tmp_path, executable)
    generated = put("native/crates/uarch-engine/generated/identity.rs", {"synthetic": True})
    note = put("synthetic-receipt.json", {"synthetic": True})
    executables = []
    for mode in ("debug", "release"):
        receipt = put(
            mode + ".json",
            {
                "format": "uarch-component-build-receipt/1",
                "build_input_hash": content_hash(build),
                "engine": engine,
                "mode": mode,
                "executable": exe,
                "image_digest": IMAGE,
                "generated_identity": generated,
                "build_log": note,
                "environment": note,
                "loader_observations": note,
                "limitations": ["synthetic shell echo; no construction evidence"],
            },
        )
        executables.append({"mode": mode, "executable": exe, "receipt": receipt})
    payload = {
        "format": "uarch-component-runtime-payload/1",
        "engine": engine,
        "build_inputs": build_file,
        "registry": registry,
        "profiles": [profile],
        "jobs": [
            {
                "case_id": job["admission"]["case_id"],
                "job_hash": job["job_hash"],
                "profile_hash": job["admission"]["profile_hash"],
                "file": job_file,
            }
        ],
        "executables": executables,
        "consumers": consumers,
        "budget": {
            "calls": 2,
            "session_seconds": 30,
            "timeout_s": 5,
            "stdin_bytes": 1048576,
            "stdout_bytes": 1048576,
            "stderr_bytes": 1024,
        },
    }
    payload_file = FileBinding.model_validate(put("payload.json", payload))
    return tmp_path, payload_file, payload, put


def test_complete_private_preparation_and_echo_transport(prepared_payload):
    root, binding, _, _ = prepared_payload
    prepared = component_host._prepare_payload(root, binding, mode="debug")
    result, receipt = component_runner._run_prepared(root / "job.json", prepared)
    assert result.duration_ps == 121000
    assert receipt["exit_code"] == 0
    assert receipt["independent_checker"] == "validation.component.observations_v3:check_v3"
    # Shape-valid private preparation cannot be supplied to either public entry point.
    for entry, args in [
        (component_runner.run_component, [root / "job.json"]),
        (component_runner.replay_component, [root / "job.json", root / "output.json"]),
    ]:
        with pytest.raises(ValueError, match="component authority"):
            entry(*args, session=prepared)


def test_prepared_current_bytes_and_executable_are_rechecked(prepared_payload):
    root, binding, _, _ = prepared_payload
    prepared = component_host._prepare_payload(root, binding, mode="debug")
    original = (root / "job.json").read_bytes()
    (root / "job.json").write_bytes(original + b" ")
    with pytest.raises(ValueError, match="digest mismatch"):
        component_runner._run_prepared(root / "job.json", prepared)
    (root / "job.json").write_bytes(original)
    prepared.refresh()
    exe = root / "synthetic-echo"
    exe.chmod(0o755)
    with pytest.raises(ValueError, match="read-only"):
        with prepared.executable():
            pytest.fail("writable executable opened")
    exe.chmod(0o555)
    with prepared.executable() as fd:
        assert fd >= 0


@pytest.mark.parametrize("field", ["model", "checker", "profile", "case", "source"])
def test_payload_substitutions_refuse_before_transport(prepared_payload, field):
    from rkuarch.engines.native.records import FileBinding

    root, _, payload, put = prepared_payload
    if field == "model":
        payload["engine"]["model"]["version"] = "1"
    elif field == "checker":
        payload["consumers"]["observations"] = "uarch-native-observations/2"
    elif field == "profile":
        payload["profiles"] = [payload["registry"]]
    elif field == "case":
        payload["jobs"][0]["case_id"] = "not-selected"
    else:
        payload["consumers"]["files"][0]["byte_hash"] = "sha256:" + "f" * 64
    binding = FileBinding.model_validate(put("changed.json", payload))
    with pytest.raises(ValueError):
        component_host._prepare_payload(root, binding, mode="debug")


def test_budget_and_token_controls(prepared_payload, monkeypatch):
    from types import SimpleNamespace

    root, binding, payload, _ = prepared_payload
    prepared = component_host._prepare_payload(root, binding, mode="debug")
    with pytest.raises(ValueError, match="component authority"):
        component_host.ComponentSession(prepared, (), token=object())
    # A synthetic capability model exercises budget mechanics only, never public resolve.
    session = component_host.ComponentSession(prepared, (), token=component_host._AUTHORITY)
    assert session.claim() is prepared
    assert session.claim() is prepared
    with pytest.raises(ValueError, match="budget exhausted"):
        session.claim()
    session = component_host.ComponentSession(prepared, (), token=component_host._AUTHORITY)
    monkeypatch.setattr(component_host, "time", SimpleNamespace(monotonic=lambda: float("inf")))
    with pytest.raises(ValueError, match="budget exhausted"):
        session.claim()


def test_independent_checker_is_mandatory_for_valid_saved_response(monkeypatch):
    import validation.component.observations_v3 as independent

    job, result = prospective_pair()
    expected = json.loads(
        (ROOT / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_bytes()
    )["observation_contract"]

    def refuse(*args, **kwargs):
        raise ValueError("independent consumer sentinel")

    monkeypatch.setattr(independent, "check_v3", refuse)
    with pytest.raises(ValueError, match="independent consumer sentinel"):
        component_runner.validate_component_response(
            canonical_json(result).encode(), b"", 0, job=job, observation_contract=expected
        )


def test_import_origin_is_checked_even_when_bytes_match(prepared_payload, monkeypatch):
    root, binding, _, _ = prepared_payload
    prepared = component_host._prepare_payload(root, binding, mode="debug")
    elsewhere = root / "same-bytes-different-origin.py"
    elsewhere.write_bytes(Path(component_runner.__file__).read_bytes())
    monkeypatch.setattr(component_runner, "__file__", str(elsewhere))
    with pytest.raises(ValueError, match="imported source identity"):
        prepared.refresh()
