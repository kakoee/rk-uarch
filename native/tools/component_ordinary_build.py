"""Finite ordinary component construction recipe. Planning is not execution authority.

Reuse the accepted construction specification and full-ID guardian. This module
adds no tracer, canary, diagnostic allowlist or startup assurance generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from uarch_contract.hashing import content_hash

from rkuarch.engines.native.component_construction import invocation
from rkuarch.engines.native.component_records import IMAGE, ComponentBuildInputsV3

HOST_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "HOME": "/nonexistent"}

LIMITS = {
    "timeout_s": 600,
    "stdout_bytes": 16 * 1024**2,
    "stderr_bytes": 16 * 1024**2,
    "cpus": 1,
    "memory_bytes": 2 * 1024**3,
    "pids": 256,
    "nofile": 1024,
}


def plan(
    prepared_root: Path, output_root: Path, mode: str, inputs: ComponentBuildInputsV3
) -> dict[str, Any]:
    """Render exact pure command/paths; caller must bind and verify every input."""
    if (
        not prepared_root.is_absolute()
        or not output_root.is_absolute()
        or any(c in str(p) for p in (prepared_root, output_root) for c in (",", "\n", "\x00"))
    ):
        raise ValueError("ordinary build roots must be explicit absolute paths")
    prepared, output = prepared_root.resolve(), output_root.resolve()
    if (
        prepared != prepared_root
        or output != output_root
        or output.is_relative_to(prepared)
        or prepared.is_relative_to(output)
    ):
        raise ValueError("ordinary build roots must be disjoint and canonical")
    inputs = ComponentBuildInputsV3.model_validate(inputs.model_dump(mode="json"))
    argv, environment = invocation([v.model_dump(mode="json") for v in inputs.mode_configs], mode)
    layout = {name: str(output / name) for name in ("target", "outputs", "receipts")}
    layout["artifact"] = str(output / "target" / mode / "uarch-engine")
    mounts = {
        "/work": str(output / "inputs/source"),
        "/cargo-home": str(output / "inputs/cache"),
        "/controls": str(output / "inputs/source/docs/reviews/U4-A-K2-construction-v1/inputs"),
    }
    args = [
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--read-only",
        "--user",
        "1000:1000",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp",
        "--cpus",
        str(LIMITS["cpus"]),
        "--memory",
        str(LIMITS["memory_bytes"]),
        "--pids-limit",
        str(LIMITS["pids"]),
        "--ulimit",
        f"nofile={LIMITS['nofile']}:{LIMITS['nofile']}",
        "--workdir",
        "/work/native",
    ]
    for target, origin in sorted(mounts.items()):
        args += ["--mount", f"type=bind,src={origin},dst={target},readonly"]
    for target, name in (("/target", "target"), ("/outputs", "outputs"), ("/receipts", "receipts")):
        args += ["--mount", f"type=bind,src={layout[name]},dst={target}"]
    args += ["--entrypoint", "/usr/bin/env", IMAGE, "-i"]
    args += [key + "=" + value for key, value in sorted(environment.items())]
    args += argv
    return {
        "format": "uarch-component-ordinary-build-plan/1",
        "mode": mode,
        "prepared_root": str(prepared),
        "output_root": str(output),
        "build_input_hash": content_hash(inputs),
        "image_digest": IMAGE,
        "child_argv": argv,
        "environment": environment,
        "container_argv": args,
        "guardian_environment": dict(HOST_ENVIRONMENT),
        "readonly_mounts": mounts,
        "layout": layout,
        "limits": dict(LIMITS),
    }


def create_outputs(value: dict[str, Any]) -> None:
    """Reserve a fresh private output root; never clean/reuse an old target."""
    root = Path(value["output_root"])
    root.mkdir(parents=True, exist_ok=False)
    # B record_attempt exclusively creates target/ and outputs/ after input validation.
    (root / "receipts").mkdir(exist_ok=False)


def resource_policy() -> dict[str, Any]:
    from validation.component.runtime_campaign import POLICY

    return {
        **POLICY,
        "max_workers": 1,
        "per_worker_memory_bytes": LIMITS["memory_bytes"],
        "per_call_seconds": LIMITS["timeout_s"],
        "nofile": LIMITS["nofile"],
        "process_limit_required": LIMITS["pids"],
    }


def _resource_check(value: dict[str, Any]) -> None:
    """Verify saved visible-hierarchy observations using the existing budget arithmetic."""
    import json

    from uarch_contract.hashing import canonical_json

    from validation.component.runtime_campaign import helpers

    value = json.loads(canonical_json(value))
    affinity = value["affinity"]
    if (
        not affinity
        or len(set(affinity)) != len(affinity)
        or any(type(x) is not int or x < 0 for x in affinity)
    ):
        raise ValueError("ordinary resource affinity")
    mount, membership = Path(value["mount"]), Path(value["membership"])
    if (
        not mount.is_absolute()
        or not membership.is_absolute()
        or value["mounted_root"] != "/"
        or ".." in membership.parts
    ):
        raise ValueError("ordinary visible resource hierarchy")
    current = mount / membership.relative_to("/")
    paths = []
    while True:
        paths.append(str(current))
        if current == mount:
            break
        current = current.parent
    if [v["path"] for v in value["observed_cgroups"]] != paths:
        raise ValueError("ordinary complete resource ancestors")
    quotas, memory = [], []
    for item in value["observed_cgroups"]:
        if "interface" in item:
            if item != {
                "path": str(mount),
                "interface": "hierarchy-root-no-bandwidth-or-memory-interface",
            }:
                raise ValueError("ordinary resource root interface")
            continue
        quota, period = item["cpu.max"].split()
        if int(period) <= 0 or (quota != "max" and int(quota) <= 0):
            raise ValueError("ordinary CPU observation")
        if quota != "max":
            quotas.append([int(quota), int(period)])
        used, limit = item["memory.current"], item["memory.max"]
        if type(used) is not int or used < 0 or (limit != "max" and int(limit) < 0):
            raise ValueError("ordinary memory observation")
        if limit != "max":
            memory.append([int(limit), used])
    if value["cpu_quotas"] != quotas or value["cgroup_memory_limits"] != memory:
        raise ValueError("ordinary observed resource arithmetic")
    policy = resource_policy()
    actual = helpers()["select_resources"](
        affinity,
        quotas,
        value["available_memory_bytes"],
        memory,
        reserve=policy["memory_reserve_bytes"],
        per_worker=policy["per_worker_memory_bytes"],
        tasks=1,
    )
    if any(value.get(key) != item for key, item in actual.items()):
        raise ValueError("ordinary default resource selection")


def verify_transport(
    root: Path, record: dict[str, Any], declaration: dict[str, Any], receipt: dict[str, Any]
) -> list[dict[str, str]]:
    """Reconsume exact ordinary command, bounded resources and owned cleanup ledger."""
    import json
    import re

    from uarch_contract.hashing import sha256

    from validation.component.ordinary_eof_acceptance import GUARD_FILES, read_bound

    if (
        set(record)
        != {
            "format",
            "plan",
            "resources",
            "guardian",
            "parent_cleanup",
            "failure",
            "construction_artifacts",
        }
        or record["format"] != "component-ordinary-build-transport/1"
        or record["failure"] is not None
    ):
        raise ValueError("complete ordinary build transport")
    saved = record["plan"]
    build_file = declaration["inputs"]["build_inputs"][0]
    inputs = ComponentBuildInputsV3.model_validate_json(
        read_bound(root, build_file["path"], build_file["byte_hash"])
    )
    rendered = plan(
        Path(saved["prepared_root"]), Path(saved["output_root"]), declaration["mode"], inputs
    )
    if (
        saved != rendered
        or saved["child_argv"] != declaration["argv"]
        or saved["environment"] != declaration["environment"]
    ):
        raise ValueError("exact ordinary outer/native invocation")
    _resource_check(record["resources"])
    if set(record["guardian"]) != set(GUARD_FILES) | {"stdout", "stderr"}:
        raise ValueError("complete ordinary guardian ledger")
    required = []
    guards = {}
    for name, item in record["guardian"].items():
        if item["path"] != "container/" + name:
            raise ValueError("ordinary guardian path")
        raw = read_bound(
            root,
            item["path"],
            item["byte_hash"],
            max(LIMITS["stdout_bytes"], LIMITS["stderr_bytes"]),
        )
        required.append(item)
        if name in GUARD_FILES:
            guards[name] = json.loads(raw)
        elif sha256(raw) != receipt["streams"][name]["byte_hash"]:
            raise ValueError("ordinary original stream equality")
    intent, prior, created, started, cleanup = (guards[name] for name in GUARD_FILES)
    cid, owner = created["container_id"], created["owner"]
    if re.fullmatch(r"[0-9a-f]{64}", cid) is None or re.fullmatch(r"[0-9a-f]{32}", owner) is None:
        raise ValueError("ordinary full container identity")
    if (
        intent["owner"] != owner
        or cleanup["owner"] != owner
        or intent["name"] != cleanup["name"]
        or intent["name"] != "u4-private-" + owner
    ):
        raise ValueError("ordinary guardian ownership")
    ids = [v["container_id"] for v in prior["containers"]]
    if (
        len(ids) != len(set(ids))
        or any(re.fullmatch(r"[0-9a-f]{64}", x) is None for x in ids)
        or cid in ids
    ):
        raise ValueError("ordinary pre-existing container preservation")
    if started["container_id"] != cid or cleanup["container_id"] != cid:
        raise ValueError("ordinary created/started/cleanup ID join")
    if (
        cleanup["format"] != "private-container-cleanup/1"
        or cleanup["stopped"] is not True
        or cleanup["removed"] is not True
        or cleanup["reason"] != "completed"
        or type(cleanup["exit_code"]) is not int
        or cleanup["exit_code"] != receipt["exit_code"]
        or any(k in cleanup for k in ("error", "cleanup_error", "never_created"))
    ):
        raise ValueError("ordinary verified cleanup completion")
    if (
        intent["args"] != saved["container_argv"]
        or intent["timeout"] != LIMITS["timeout_s"]
        or intent["cap"] != LIMITS["stdout_bytes"]
        or intent["stderr_cap"] != LIMITS["stderr_bytes"]
        or intent["stdin"] is not False
        or intent.get("environment") != HOST_ENVIRONMENT
    ):
        raise ValueError("ordinary exact guardian command/limits")
    parent_file = record["parent_cleanup"]
    parent = json.loads(read_bound(root, parent_file["path"], parent_file["byte_hash"]))
    if parent != {"format": "component-ordinary-build-parent-cleanup/1", "receipts": [cleanup]}:
        raise ValueError("ordinary exact parent cleanup")
    required.append(parent_file)
    artifacts = record["construction_artifacts"]
    names = [v["path"] for v in artifacts]
    if names != sorted(set(names)) or f"receipts/{declaration['mode']}.map" not in names:
        raise ValueError("ordinary construction map/artifact inventory")
    total = 0
    for item in artifacts:
        if not item["path"].startswith("receipts/"):
            raise ValueError("ordinary construction artifact path")
        raw = read_bound(root, item["path"], item["byte_hash"], 64 * 1024**2)
        total += len(raw)
        required.append(item)
    if total > 256 * 1024**2:
        raise ValueError("ordinary retained construction artifact bound")
    return required


def transport(root: Path, spec: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    """Later bounded guardian callback; this task exercises it only with inline mocks."""
    import shutil

    from uarch_contract.hashing import sha256

    from native.tools import component_container_guard as guardian
    from validation.component.runtime_campaign import helpers

    if spec != {
        "argv": value["child_argv"],
        "environment": value["environment"],
        "limits": {key: LIMITS[key] for key in ("timeout_s", "stdout_bytes", "stderr_bytes")},
    }:
        raise ValueError("ordinary transport declaration mismatch")
    if str(root.resolve()) != value["output_root"]:
        raise ValueError("ordinary actual output root")
    record: dict[str, Any] = {
        "format": "component-ordinary-build-transport/1",
        "plan": value,
        "resources": None,
        "guardian": {},
        "parent_cleanup": None,
        "failure": None,
        "construction_artifacts": [],
    }
    cleanup: dict[str, Any] = {}
    try:
        record["resources"] = helpers()["discover"](resource_policy(), 1)
        _resource_check(record["resources"])
        cleanup = guardian.run_container(
            root / "container",
            value["container_argv"],
            timeout=LIMITS["timeout_s"],
            cap=LIMITS["stdout_bytes"],
            stderr_cap=LIMITS["stderr_bytes"],
            environment=HOST_ENVIRONMENT,
        )
    except BaseException as error:
        record["failure"] = repr(error)
    finally:
        try:
            parent = {
                "format": "component-ordinary-build-parent-cleanup/1",
                "receipts": guardian.cleanup(root),
            }
            guardian.save(root / "parent-cleanup.json", parent)
            record["parent_cleanup"] = {
                "path": "parent-cleanup.json",
                "byte_hash": sha256((root / "parent-cleanup.json").read_bytes()),
            }
        except BaseException as error:
            record["failure"] = str(record["failure"]) + "; cleanup: " + repr(error)
    observed: dict[str, int | None] = {}
    complete: dict[str, bool] = {}
    truncated: dict[str, bool | None] = {}
    for name in ("stdout", "stderr"):
        original = root / "container" / name
        cap = LIMITS[name + "_bytes"]
        if original.is_file() and not original.is_symlink():
            size = original.stat().st_size
            observed[name] = size
            complete[name] = size <= cap
            truncated[name] = False
            # Retain observed overshoot as failure; never truncate into successful evidence.
            shutil.copyfile(original, root / name)
        else:
            observed[name], complete[name], truncated[name] = None, False, None
    for name in (
        "intent.json",
        "pre-existing.json",
        "created.json",
        "started.json",
        "cleanup.json",
        "stdout",
        "stderr",
    ):
        path = root / "container" / name
        if path.is_file() and not path.is_symlink():
            record["guardian"][name] = {
                "path": "container/" + name,
                "byte_hash": sha256(path.read_bytes()),
            }
    artifact = root / "target" / value["mode"] / "uarch-engine"
    if (
        artifact.is_file()
        and not artifact.is_symlink()
        and 0 < artifact.stat().st_size <= 256 * 1024**2
    ):
        shutil.copyfile(artifact, root / "outputs/uarch-engine")
        (root / "outputs/uarch-engine").chmod(0o555)
    for artifact_file in sorted((root / "receipts").rglob("*")):
        if artifact_file.is_symlink():
            record["failure"] = "unsafe construction artifact"
        elif artifact_file.is_file():
            if artifact_file.stat().st_size > 64 * 1024**2:
                record["failure"] = "construction artifact over limit"
            else:
                record["construction_artifacts"].append(
                    {
                        "path": str(artifact_file.relative_to(root)),
                        "byte_hash": sha256(artifact_file.read_bytes()),
                    }
                )
    guardian.save(root / "transport.json", record)
    return {
        "exit_code": cleanup.get("exit_code"),
        "completed": record["failure"] is None and cleanup.get("reason") == "completed",
        "timed_out": cleanup.get("reason") == "deadline",
        "resource_failure": record["failure"],
        "observed_bytes": observed,
        "stream_complete": complete,
        "stream_truncated": truncated,
    }


def construct(prepared: Path, output: Path, mode: str, consumers: dict[str, Any]) -> dict[str, Any]:
    """Later build only: stage/recheck inputs, retain failures, freeze actual output.

    The independent reviewer still freezes acceptance, required-check support and
    startup assurance. This producer emits no accepted review or runtime authority.
    """
    import json
    import shutil

    from uarch_contract.hashing import canonical_json

    from rkuarch.engines.native.component_build_review import (
        SOURCE,
        derive_declaration,
        file_binding,
    )
    from rkuarch.engines.native.component_records import ComponentBuildReceiptV2
    from validation.component.ordinary_build_acceptance import consume_build
    from validation.component.ordinary_build_receipt import record_attempt

    source = prepared / "source"
    build_file = file_binding(source, "private-component/BuildInputs.json")
    inputs = ComponentBuildInputsV3.model_validate_json((source / build_file["path"]).read_bytes())
    engine = json.loads((source / "private-component/engine.json").read_bytes())
    value = plan(prepared, output, mode, inputs)
    create_outputs(value)
    (output / "inputs").mkdir()
    shutil.copytree(source, output / "inputs/source", symlinks=True)
    shutil.copytree(prepared / "cache", output / "inputs/cache", symlinks=True)
    for name in ("source.tar", "source-commit.raw"):
        shutil.copyfile(prepared / name, output / "inputs" / name)
    for item in [*consumers["external_files"], consumers["python_executable"]]:
        target = output / "inputs/python" / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("/") / item["path"], target)
    expected = {
        "engine": engine,
        "build_inputs": build_file,
        "build_input_hash": content_hash(inputs),
        "source_commit": inputs.source_commit,
        "source_files": [v.model_dump(mode="json") for v in inputs.source_files],
        "tool_inputs": inputs.tool_inputs_file.model_dump(mode="json"),
        "tool_inputs_hash": inputs.tool_inputs_hash,
        "mode_configs": [v.model_dump(mode="json") for v in inputs.mode_configs],
        "generated_identity_output_paths": list(inputs.generated_identity_output_paths),
        "consumers": consumers,
        "consumer_hash": content_hash(consumers),
    }
    declaration = derive_declaration(output, expected, mode)
    limits = {key: LIMITS[key] for key in ("timeout_s", "stdout_bytes", "stderr_bytes")}
    (output / "plan.json").write_text(canonical_json(value))
    receipt = record_attempt(
        output, declaration, limits, lambda root, spec: transport(root, spec, value)
    )
    # Refuse changed staged inputs, including the accepted source cache, after return.
    if derive_declaration(output, expected, mode) != declaration:
        raise ValueError("ordinary inputs changed during construction")
    expectation = {
        "format": "component-ordinary-build-expectation/1",
        "declaration": declaration,
        "executable": receipt["executable"],
        **limits,
    }
    (output / "expectation.json").write_text(canonical_json(expectation))
    consumed = consume_build(output, receipt, expectation)
    transport_record = json.loads((output / "transport.json").read_bytes())
    verify_transport(output, transport_record, declaration, receipt)
    (output / "consumption.json").write_text(canonical_json(consumed))
    (output / "environment.json").write_text(canonical_json(declaration["environment"]))
    outer = ComponentBuildReceiptV2.model_validate(
        {
            "format": "uarch-component-build-receipt/2",
            "build_input_hash": content_hash(inputs),
            "engine": engine,
            "mode": mode,
            "executable": receipt["executable"],
            "image_digest": value["image_digest"],
            "generated_identity": file_binding(
                output, SOURCE + inputs.generated_identity_output_paths[0]
            ),
            "ordinary_receipt": file_binding(output, "ordinary-build-receipt.json"),
            "environment": file_binding(output, "environment.json"),
            "limitations": [
                "producer evidence; not independent acceptance",
                "no startup assurance or authority",
            ],
        }
    )
    # Per-build relative links must be rebased and independently frozen when assembling
    # a two-mode runtime payload; old payloads/binaries are never silently repointed.
    (output / "component-build-receipt.json").write_text(canonical_json(outer))
    return consumed


def assemble_links(destination: Path, builds: dict[str, Path]) -> dict[str, Any]:
    """Stage two retained builds under one fresh root; never create an accepted review.

    Targets are excluded: executables, logs, map/wrapper artifacts and all declared
    inputs stay retained. Review/startup/authority records must be supplied separately.
    """
    import shutil

    from uarch_contract.hashing import canonical_json

    from rkuarch.engines.native.component_build_review import file_binding
    from rkuarch.engines.native.component_records import ComponentBuildReceiptV2

    if list(builds) != ["debug", "release"] or len({p.resolve() for p in builds.values()}) != 2:
        raise ValueError("separate ordered build roots required")
    if not destination.is_absolute() or any(
        destination.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(destination.resolve())
        for p in builds.values()
    ):
        raise ValueError("fresh disjoint assembly destination required")
    shutil.copytree(builds["debug"] / "inputs/source", destination, symlinks=True)
    rows, executables = [], []
    for mode, source in builds.items():
        prefix = "builds/" + mode + "/"
        target = destination / prefix
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("target"), symlinks=True)
        outer = ComponentBuildReceiptV2.model_validate_json(
            (target / "component-build-receipt.json").read_bytes()
        )
        if outer.mode != mode:
            raise ValueError("assembled build mode mismatch")
        value = outer.model_dump(mode="json")
        for name in ("executable", "ordinary_receipt", "environment"):
            value[name]["path"] = prefix + value[name]["path"]
        generated_path = value["generated_identity"]["path"]
        if not generated_path.startswith("inputs/source/"):
            raise ValueError("staged generated path required")
        generated_path = generated_path.removeprefix("inputs/source/")
        value["generated_identity"] = file_binding(destination, generated_path)
        if value["generated_identity"]["byte_hash"] != outer.generated_identity.byte_hash:
            raise ValueError("same generated bytes across both modes")
        (target / "payload-build-receipt.json").write_text(canonical_json(value))
        rows.append(
            {
                "mode": mode,
                "root": prefix.rstrip("/"),
                **{
                    key: file_binding(destination, prefix + name)
                    for key, name in (
                        ("expectation", "expectation.json"),
                        ("receipt", "ordinary-build-receipt.json"),
                        ("transport", "transport.json"),
                    )
                },
            }
        )
        executables.append(
            {
                "mode": mode,
                "executable": value["executable"],
                "receipt": file_binding(destination, prefix + "payload-build-receipt.json"),
            }
        )
    result = {
        "format": "component-ordinary-build-links/1",
        "builds": rows,
        "executables": executables,
        "authority": None,
        "startup_assurance": "not-supplied",
        "required_checks_review": "not-supplied",
    }
    (destination / "ordinary-build-links.json").write_text(canonical_json(result))
    return result
