"""Synthetic host-authority controls only: no approved profile or native execution."""

import copy
import importlib.abc
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from uarch_contract.hashing import canonical_json, content_hash
from uarch_contract.mapped import NativeEngineIdentity

from rkuarch.workload.mapped import (
    export_fixed_delay_job,
    load_fixed_delay_job,
    loads_fixed_delay_job,
)

FIXTURES = Path(__file__).resolve().parents[2] / "contract/fixtures/mapped"


@pytest.fixture
def raw() -> dict[str, Any]:
    return json.loads((FIXTURES / "kernel-job.json").read_bytes())


@pytest.fixture
def authority(raw: dict[str, Any]) -> dict[str, Any]:
    # Frozen by the test harness BEFORE caller mutations; never runtime discovery.
    return {
        "trusted_registry_hash": raw["registry"]["registry_hash"],
        "trusted_profile_hash": raw["profile"]["profile_hash"],
        "expected_engine": NativeEngineIdentity.model_validate(copy.deepcopy(raw["engine"])),
    }


def rehash(value: dict[str, Any], field: str) -> None:
    value[field] = content_hash(value, exclude=(field,))


def seal(raw: dict[str, Any]) -> None:
    point = raw["mapped_point"]
    rehash(point["task_graph"], "graph_hash")
    rehash(point, "payload_hash")
    raw["point_hash"] = point["payload_hash"]
    raw["workload_closure"]["points"] = [copy.deepcopy(point)]
    rehash(raw["workload_closure"], "bundle_hash")
    raw["bundle_hash"] = raw["workload_closure"]["bundle_hash"]
    rehash(raw, "job_hash")


class NoProducers(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, *args: object) -> None:
        if fullname.startswith(
            (
                "rkuarch.mapping",
                "rkuarch.workload.prepare",
                "rkuarch.workload.producer",
                "rkuarch.engines.native",
            )
        ):
            raise AssertionError("producer/native import: " + fullname)


def test_saved_export_relocation_without_producers(
    raw: dict[str, Any],
    authority: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("subprocess launch")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    guard = NoProducers()
    sys.meta_path.insert(0, guard)
    try:
        # Also guard previously imported producer modules in a full-suite invocation.
        for name, module in tuple(sys.modules.items()):
            if (
                name.startswith(
                    ("rkuarch.mapping", "rkuarch.workload.prepare", "rkuarch.workload.producer")
                )
                and module is not None
            ):
                for key, value in vars(module).copy().items():
                    if callable(value) and not key.startswith("_"):
                        monkeypatch.setattr(module, key, forbidden)
        job = loads_fixed_delay_job(json.dumps(raw), **authority)
        source = tmp_path / "saved.json"
        export_fixed_delay_job(job, source, **authority)
        relocated = tmp_path / "elsewhere"
        relocated.mkdir()
        source.rename(relocated / "input.json")
        monkeypatch.chdir(relocated)
        # Ambient files are untrusted and must never be consulted.
        Path("registry.json").write_text('{"approved":true}')
        replay = load_fixed_delay_job(Path("input.json"), **authority)
        assert replay.model_dump(mode="json") == raw
        assert Path("input.json").read_bytes() == canonical_json(raw).encode()
        export_fixed_delay_job(replay, Path("again.json"), **authority)
        assert Path("again.json").read_bytes() == Path("input.json").read_bytes()
        with pytest.raises(FileExistsError):
            export_fixed_delay_job(replay, Path("again.json"), **authority)
    finally:
        sys.meta_path.remove(guard)


@pytest.mark.parametrize(
    "text",
    [
        '{"protocol":"uarch-engine/3","protocol":"uarch-engine/3"}',
        '{"x":{"seed":0,"seed":1}}',
        '{"seed":NaN}',
        '{"seed":Infinity}',
        "{} {}",
        "[]",
        "null",
        "",
    ],
)
def test_strict_json(text: str, authority: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        loads_fixed_delay_job(text, **authority)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("extra",), 1),
        (("seed",), True),
        (("seed",), "0"),
        (("seed",), 0.0),
        (("seed",), 2**64),
        (("freq_hz", "core"), True),
        (("mapped_point", "task_graph", "jobs", 0, "duration_ps"), True),
        (("protocol",), "uarch-engine/1"),
        (("protocol",), "uarch-engine/2"),
        (("workload_closure", "format"), "uarch-prepared/2"),
        (("workload_closure", "source"), {}),
        (("workload_closure", "points"), []),
        (("profile",), None),
        (("registry", "unexpected"), True),
        (("job_hash",), "sha256:" + "0" * 64),
    ],
)
def test_strict_types_versions_and_closure(
    raw: dict[str, Any],
    authority: dict[str, Any],
    path: tuple[Any, ...],
    value: Any,
) -> None:
    cursor = raw
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError):
        loads_fixed_delay_job(json.dumps(raw), **authority)


@pytest.mark.parametrize(
    "field", ["bundle_hash", "point_hash", "hardware_spec_hash", "assumptions_hash"]
)
def test_rehashed_broken_joins(
    raw: dict[str, Any],
    authority: dict[str, Any],
    field: str,
) -> None:
    raw[field] = "sha256:" + "0" * 64
    rehash(raw, "job_hash")
    with pytest.raises(ValueError):
        loads_fixed_delay_job(json.dumps(raw), **authority)


@pytest.mark.parametrize(
    "change", ["engine", "registry", "profile", "seed", "clock", "dependency", "point", "scope"]
)
def test_rehashed_refusals(
    raw: dict[str, Any],
    authority: dict[str, Any],
    change: str,
) -> None:
    if change == "engine":
        raw["engine"]["implementation_hash"] = "sha256:" + "1" * 64
    elif change == "registry":
        raw["registry"]["test_only_specs"] = [
            {"hardware_spec_hash": "sha256:" + "1" * 64, "rationale": "synthetic test"}
        ]
        rehash(raw["registry"], "registry_hash")
    elif change == "profile":
        raw["profile"]["owner"] = "caller-controlled"
        rehash(raw["profile"], "profile_hash")
        raw["admission"]["profile_hash"] = raw["profile"]["profile_hash"]
        raw["workload_closure"]["admission"] = copy.deepcopy(raw["admission"])
    elif change == "seed":
        raw["seed"] += 1
    elif change == "clock":
        raw["clock_setup"] = [
            {
                "job_id": raw["mapped_point"]["task_graph"]["jobs"][0]["id"],
                "domain": "core",
                "start_ps": 1,
                "n_cycles": 1,
            }
        ]
    elif change == "dependency":
        raw["mapped_point"]["task_graph"]["dependencies"] = [
            {"before": "absent", "after": raw["mapped_point"]["task_graph"]["jobs"][0]["id"]}
        ]
    elif change == "point":
        raw["mapped_point"]["point_id"] = "not-selected"
    else:
        raw["workload_closure"]["scope"] = {"kind": "transport_fixture"}
    seal(raw)
    with pytest.raises(ValueError):
        loads_fixed_delay_job(json.dumps(raw), **authority)


def test_full_caller_rehash_cannot_replace_host_anchor(
    raw: dict[str, Any],
    authority: dict[str, Any],
    tmp_path: Path,
) -> None:
    raw["seed"] += 1
    raw["clock_setup"] = [
        {
            "job_id": raw["mapped_point"]["task_graph"]["jobs"][0]["id"],
            "domain": "core",
            "start_ps": 0,
            "n_cycles": 3,
        }
    ]
    raw["mapped_point"]["task_graph"]["jobs"][0]["duration_ps"] = 0
    seal(raw)
    entry = raw["profile"]["entries"][0]
    entry.update(
        seed=raw["seed"],
        clock_setup_hash=content_hash(raw["clock_setup"]),
        graph_hash=raw["mapped_point"]["task_graph"]["graph_hash"],
        point_hash=raw["point_hash"],
    )
    rehash(raw["profile"], "profile_hash")
    raw["admission"]["profile_hash"] = raw["profile"]["profile_hash"]
    raw["workload_closure"]["admission"] = copy.deepcopy(raw["admission"])
    seal(raw)
    # Internal consistency is a positive control, not host permission.
    attacker = dict(authority, trusted_profile_hash=raw["profile"]["profile_hash"])
    job = loads_fixed_delay_job(json.dumps(raw), **attacker)
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        loads_fixed_delay_job(json.dumps(raw), **authority)
    with pytest.raises(ValueError, match="TestProfileMismatch"):
        export_fixed_delay_job(job, tmp_path / "refused.json", **authority)
    assert not (tmp_path / "refused.json").exists()


def test_export_revalidates_nested_mutation(
    raw: dict[str, Any],
    authority: dict[str, Any],
    tmp_path: Path,
) -> None:
    job = loads_fixed_delay_job(json.dumps(raw), **authority)
    job.workload_closure.hardware_spec.formats.clear()
    with pytest.raises(ValueError):
        export_fixed_delay_job(job, tmp_path / "refused.json", **authority)
    assert not (tmp_path / "refused.json").exists()


@pytest.mark.parametrize("name", ["component-job", "resident", "transport"])
def test_other_scopes_refuse(name: str, authority: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        loads_fixed_delay_job((FIXTURES / (name + ".json")).read_bytes(), **authority)


def test_host_arguments_mandatory(raw: dict[str, Any]) -> None:
    with pytest.raises(TypeError):
        loads_fixed_delay_job(json.dumps(raw))  # type: ignore[call-arg]


def test_fresh_process_replay_blocks_producer_imports(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    saved = tmp_path / "input.json"
    saved.write_bytes((FIXTURES / "kernel-job.json").read_bytes())
    script = r"""
import importlib.abc
import json
import pathlib
import sys
root, saved = map(pathlib.Path, sys.argv[1:])
sys.path[:0] = [str(root / "src"), str(root / "contract")]
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.startswith(("rkuarch.mapping", "rkuarch.workload.prepare",
                                "rkuarch.workload.producer", "rkuarch.engines.native")):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Guard())
from rkuarch.workload.mapped import load_fixed_delay_job
from uarch_contract.hashing import canonical_json
from uarch_contract.mapped import NativeEngineIdentity
# Synthetic harness authority frozen from an independent installed test input.
a = json.loads((root / "contract/fixtures/mapped/kernel-job.json").read_bytes())
job = load_fixed_delay_job(saved, trusted_registry_hash=a["registry"]["registry_hash"],
    trusted_profile_hash=a["profile"]["profile_hash"],
    expected_engine=NativeEngineIdentity.model_validate(a["engine"]))
for name in ("rkuarch.workload.mapped", "uarch_contract.mapped"):
    assert pathlib.Path(sys.modules[name].__file__).resolve().is_relative_to(root)
sys.stdout.write(canonical_json(job))
"""
    outputs = [
        subprocess.run(
            [sys.executable, "-I", "-c", script, str(root), str(saved)],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        ).stdout
        for _ in range(3)
    ]
    assert outputs == [canonical_json(json.loads(saved.read_bytes())).encode()] * 3
