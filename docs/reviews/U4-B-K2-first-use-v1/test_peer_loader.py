"""Independent B checks of published A loader; synthetic authority, no native launch."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from uarch_contract.hashing import canonical_json

from rkuarch.workload.mapped import (
    export_fixed_delay_job,
    load_fixed_delay_job,
    loads_fixed_delay_job,
)

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
_spec = importlib.util.spec_from_file_location("b_k2_inputs", PACKAGE / "test_inputs.py")
assert _spec is not None and _spec.loader is not None
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)


@pytest.fixture(scope="module")
def inputs():
    return b.load("profile.json"), b.load("registry.json"), b.load("expectations.json")


def host(inputs):
    return dict(
        trusted_profile_hash=inputs[0]["profile_hash"],
        trusted_registry_hash=inputs[1]["registry_hash"],
        expected_engine=b.synthetic_engine(),
    )


@pytest.mark.parametrize(
    "case",
    [
        "K01",
        "K02",
        "K03-owner",
        "K04",
        "K05",
        "K05-chain",
        "K06-00",
        "K06-01",
        "K06-02",
        "K06-03",
        "K06-04",
        "K07-800000000-24",
        "K07-900000000-24",
        "K07-1000000000-24",
        "K07-1200000000-24",
        "K08-clock-overflow",
        "K08-add-overflow",
    ],
)
def test_actual_loader_positive(case, inputs):
    raw = b.job_for(case, inputs)
    job = loads_fixed_delay_job(canonical_json(raw), **host(inputs))
    assert canonical_json(job) == canonical_json(raw)
    assert job.fidelity_detail is None


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("clock", "TestProfileMismatch"),
        ("case", "TestProfileMismatch"),
        ("source", "EngineIdentityMismatch"),
        ("engine", "EngineIdentityMismatch"),
        ("registry", "RegistryTrustMismatch"),
        ("full-rehash", "TestProfileMismatch"),
    ],
)
def test_actual_loader_attacks(fault, reason, inputs, tmp_path):
    raw = b.job_for("K06-02", inputs)
    authority = host(inputs)
    if fault == "clock":
        raw["clock_setup"][0]["n_cycles"] += 1
    elif fault == "case":
        raw["admission"]["case_id"] = "foreign"
        raw["workload_closure"]["admission"]["case_id"] = "foreign"
        b.seal(raw["workload_closure"], "bundle_hash")
        raw["bundle_hash"] = raw["workload_closure"]["bundle_hash"]
    elif fault in ("source", "engine"):
        raw["engine"]["implementation_hash"] = b.content_hash({"foreign": fault})
    elif fault == "registry":
        raw["registry"]["test_only_specs"][0]["rationale"] += "attacked"
        b.seal(raw["registry"], "registry_hash")
    else:
        raw["seed"] = 1
        raw["clock_setup"][0]["n_cycles"] = 1
        point = raw["mapped_point"]
        point["task_graph"]["jobs"][0]["duration_ps"] += 1
        b.seal(point["task_graph"], "graph_hash")
        b.seal(point, "payload_hash")
        raw["point_hash"] = point["payload_hash"]
        raw["workload_closure"]["points"] = [copy.deepcopy(point)]
        entry = next(e for e in raw["profile"]["entries"] if e["case_id"] == "K06-02")
        entry.update(
            seed=1,
            graph_hash=point["task_graph"]["graph_hash"],
            point_hash=point["payload_hash"],
            clock_setup_hash=b.content_hash(raw["clock_setup"]),
        )
        b.seal(raw["profile"], "profile_hash")
        raw["admission"]["profile_hash"] = raw["profile"]["profile_hash"]
        raw["workload_closure"]["admission"] = copy.deepcopy(raw["admission"])
        b.seal(raw["workload_closure"], "bundle_hash")
        raw["bundle_hash"] = raw["workload_closure"]["bundle_hash"]
        b.seal(raw, "job_hash")
        # Genuine internal-consistency positive under an explicitly attacker-only test anchor.
        attacker = dict(authority, trusted_profile_hash=raw["profile"]["profile_hash"])
        job = loads_fixed_delay_job(canonical_json(raw), **attacker)
        with pytest.raises(ValueError, match=reason):
            export_fixed_delay_job(job, tmp_path / "must-not-exist.json", **authority)
        assert not (tmp_path / "must-not-exist.json").exists()
    with pytest.raises(ValueError, match=reason):
        loads_fixed_delay_job(canonical_json(b.seal(raw, "job_hash")), **authority)
    assert loads_fixed_delay_job(canonical_json(b.job_for("K06-02", inputs)), **authority)


REPLAY = r"""
import importlib.abc, json, pathlib, sys
root, saved, anchor, output = map(pathlib.Path, sys.argv[1:])
sys.path[:0]=[str(root/'src'), str(root/'contract')]
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.startswith(('rkuarch.mapping', 'rkuarch.workload.prepare',
            'rkuarch.workload.producer', 'rkuarch.workload.rotary',
            'rkuarch.engines', 'scripts')):
            raise AssertionError('producer/oracle/native import prohibited: '+fullname)
sys.meta_path.insert(0,Deny())
from rkuarch.workload.mapped import load_fixed_delay_job, export_fixed_delay_job
from uarch_contract.mapped import NativeEngineIdentity
from uarch_contract.hashing import canonical_json
h=json.loads(anchor.read_bytes())
h['expected_engine']=NativeEngineIdentity.model_validate(h['expected_engine'])
def prohibit(event, args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):
        raise AssertionError('producer/oracle process prohibited')
sys.addaudithook(prohibit)
job=load_fixed_delay_job(saved,**h)
export_fixed_delay_job(job,output,**h)
origins={}
for name,module in list(sys.modules.items()):
    if name.split('.')[0] in ('rkuarch','uarch_contract','scripts'):
        file=getattr(module,'__file__',None)
        assert file and pathlib.Path(file).resolve().is_relative_to(root),(name,file)
        origins[name]=str(pathlib.Path(file).resolve().relative_to(root))
# Exercise the denial itself; success was not due to an inert guard.
for name in ('rkuarch.mapping','rkuarch.workload.prepare','rkuarch.workload.producer',
             'rkuarch.workload.rotary','rkuarch.engines.native','scripts.vendor_rk'):
    try: __import__(name)
    except AssertionError: pass
    else: raise AssertionError('denial did not discriminate: '+name)
assert output.read_bytes()==canonical_json(job).encode()
print(json.dumps({'job_hash':job.job_hash,'origins':origins},sort_keys=True))
"""


def test_relocated_producer_disabled_replay(inputs, tmp_path):
    authority = host(inputs)
    raw = b.job_for("K04", inputs)
    job = loads_fixed_delay_job(canonical_json(raw), **authority)
    original = tmp_path / "original.json"
    export_fixed_delay_job(job, original, **authority)
    payload = original.read_bytes()
    # Snapshot exact peer runtime closure after importing the real loader in this process.
    # Independent static closure reconciliation is in peer-audit.json.
    sources = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"rkuarch", "uarch_contract"}:
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(ROOT), (name, path)
            sources[str(path.relative_to(ROOT))] = path.read_bytes()
    layout = tmp_path / "relocated"
    for relative, data in sources.items():
        target = layout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    saved = layout / "saved.json"
    saved.write_bytes(payload)
    anchor = tmp_path / "synthetic-host.json"
    anchor.write_text(
        json.dumps(
            dict(authority, expected_engine=authority["expected_engine"].model_dump(mode="json"))
        )
    )
    env = os.environ.copy()
    for key in ("PYTHONPATH", "MYPYPATH", "VIRTUAL_ENV", "UARCH_HUMAN"):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    receipts = []
    for index, root in enumerate((ROOT, layout, layout)):
        output = tmp_path / f"replay-{index}.json"
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                REPLAY,
                str(root),
                str(saved),
                str(anchor),
                str(output),
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            check=True,
        )
        assert output.read_bytes() == payload
        receipts.append(json.loads(proc.stdout))
    assert len({r["job_hash"] for r in receipts}) == 1
    assert original.read_bytes() == saved.read_bytes() == payload
    assert all((layout / rel).read_bytes() == data for rel, data in sources.items())
    assert load_fixed_delay_job(saved, **authority).job_hash == job.job_hash
    # Missing actual consumer source must fail, not fall through to the editable installation.
    (layout / "src/rkuarch/workload/mapped.py").unlink()
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            REPLAY,
            str(layout),
            str(saved),
            str(anchor),
            str(tmp_path / "bad.json"),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
    )
    assert proc.returncode != 0 and b"ModuleNotFoundError" in proc.stderr
    assert not (tmp_path / "bad.json").exists()
    assert hashlib.sha256(payload).hexdigest() == hashlib.sha256(saved.read_bytes()).hexdigest()
