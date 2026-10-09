"""Pre-freeze controls: actual inputs, synthetic oracle only, no snapshot generation."""

import json
from pathlib import Path

import pytest

from scripts import u2_inputs, vendor_rk

ROOT = Path(__file__).resolve().parents[2]


def test_exact_staged_inputs_and_stale_byte_refusal(tmp_path):
    directory = tmp_path / "inputs"
    identity = u2_inputs.prepare_inputs(directory)
    inputs = u2_inputs.load_inputs(directory, identity)
    assert {name: len(pairs) for name, pairs in inputs.matrix.items()} == {
        "asic_placeholder.yaml": 2,
        "nvidia_h100_sxm.yaml": 4,
        "npu-l4.yaml": 1,
    }
    assert sum(len(p) for p in inputs.matrix.values()) * 3 * 2 * 24 == 1008
    assert (
        inputs.descriptors["compute.asic.npu-l4"]
        == (ROOT / "contract/tests/fixtures/u2_b/a2-export/npu-l4.oracle-compat.yaml").read_bytes()
    )
    assert (
        inputs.artifacts[inputs.entries[-1].binding.execution_model_hash]["compute"]["value"] == 1.0
    )
    (directory / "components/npu-l4.yaml").write_bytes(b"changed")
    with pytest.raises(ValueError, match="input"):
        u2_inputs.load_inputs(directory, identity)


def test_explicit_matrix_does_not_use_filename_defaults(tmp_path):
    directory = tmp_path / "inputs"
    inputs = u2_inputs.load_inputs(directory, u2_inputs.prepare_inputs(directory))
    # Deliberately synthetic outputs for all intended positive identities, not oracle evidence.
    rows = synthetic_matrix(inputs)
    assert len(rows) == 1008
    vendor_rk.validate_matrix(rows, set(inputs.matrix), precisions=inputs.matrix)
    with pytest.raises(ValueError, match="incomplete matrix"):
        vendor_rk.validate_matrix(rows[:-1], set(inputs.matrix), precisions=inputs.matrix)
    rows[-1]["precision"]["kv_cache"] = "fp8"
    with pytest.raises(ValueError, match="incomplete matrix"):
        vendor_rk.validate_matrix(rows, set(inputs.matrix), precisions=inputs.matrix)


def test_refusals_need_four_observed_direct_boundaries():
    synthetic = [
        dict(
            component_params_file="components/" + name,
            compute=fmt,
            kv_cache=fmt,
            exception="UnsupportedPrecision",
            message="synthetic stub refusal",
            boundary="Accelerator.peak_op_per_s",
            callable_source_sha256="a" * 64,
        )
        for name, fmts in [
            ("asic_placeholder.yaml", ("bf16", "fp8")),
            ("npu-l4.yaml", ("fp16", "fp8")),
        ]
        for fmt in fmts
    ]
    vendor_rk.validate_refusals(synthetic, expanded=True, callable_source_sha256="a" * 64)
    with pytest.raises(ValueError):
        vendor_rk.validate_refusals(synthetic[:-1], expanded=True, callable_source_sha256="a" * 64)
    synthetic[0]["boundary"] = "_accelerator"
    with pytest.raises(ValueError, match="direct"):
        vendor_rk.validate_refusals(synthetic, expanded=True, callable_source_sha256="a" * 64)


def test_semantic_diff_uses_keys_and_retains_unknowns():
    a = dict(
        id="old",
        model_id="m",
        component_params_file="components/x",
        tp=1,
        precision={"compute": "bf16", "kv_cache": "bf16"},
        query={"phase": "decode"},
        counts={"matrix_ops": 1, "memory_write_bytes": None},
        duration_s=1,
    )
    b = json.loads(json.dumps(a))
    b["id"] = "renamed"
    b["counts"]["memory_write_bytes"] = 0
    report = u2_inputs.semantic_rows([a], [b])
    assert not report["added"] and not report["removed"]
    assert (
        len(report["changed"]) == 1
        and report["changed"][0]["before"]["counts"]["memory_write_bytes"] is None
    )


def synthetic_matrix(inputs):
    rows = []
    for name, pairs in inputs.matrix.items():
        for sidecar in inputs.models:
            for pair in pairs:
                for tp in (1, 8):
                    for qi, query in enumerate(vendor_rk.QUERIES):
                        rows.append(
                            dict(
                                id=f"synthetic/{name}/{sidecar['id']}/{pair['compute']}/{pair['kv_cache']}/{tp}/{qi}",
                                rk_sha=vendor_rk.PIN,
                                model_id=sidecar["id"],
                                model=sidecar["model"],
                                model_shape=sidecar["shape"],
                                model_sources=sidecar["sources"],
                                component_params_file="components/" + name,
                                component_params_sha256=vendor_rk.digest(
                                    (inputs.root / "components" / name).read_bytes()
                                ),
                                precision=dict(pair),
                                tp=tp,
                                query=dict(query),
                                counts_scope="replica",
                                duration_scope="one_tp_rank_no_collectives",
                                duration_method=query["phase"] + "_s",
                                duration_s=1.0,
                                counts=dict(
                                    matrix_ops=64,
                                    memory_read_bytes=128,
                                    memory_write_bytes=None if query["phase"] == "decode" else 32,
                                ),
                            )
                        )
    return rows


def test_collect_wires_full_inputs_and_detects_midrun_drift(tmp_path, monkeypatch):
    from types import SimpleNamespace

    directory = tmp_path / "inputs"
    identity = u2_inputs.prepare_inputs(directory)
    inputs = u2_inputs.load_inputs(directory, identity)
    rk = tmp_path / "synthetic-upstream"
    rk.mkdir()
    for name in (*vendor_rk.SOURCES, "web/src/schema.json", "uv.lock"):
        target = rk / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"synthetic upstream control, not source evidence")
    monkeypatch.setattr(vendor_rk, "check_clone", lambda *a: None)
    monkeypatch.setattr(vendor_rk, "oracle_environment", lambda *a: {})
    monkeypatch.setattr(vendor_rk, "verify_oracle_environment", lambda *a: None)
    monkeypatch.setattr(vendor_rk, "record_oracle_environment", lambda *a: {"synthetic": "only"})
    observed = []

    def stub(rk, env, program, request):
        req = json.loads(request)
        observed.append(req)
        assert {c["name"]: len(c["precisions"]) for c in req["components"]} == {
            "asic_placeholder.yaml": 2,
            "nvidia_h100_sxm.yaml": 4,
            "npu-l4.yaml": 1,
        }
        assert sum(len(c["direct_refusals"]) for c in req["components"]) == 4
        refusals = [
            dict(
                component_params_file="components/" + c["name"],
                **p,
                exception="UnsupportedPrecision",
                message="synthetic direct refusal",
                boundary="Accelerator.peak_op_per_s",
                callable_source_sha256=req["direct_peak_source_sha256"],
            )
            for c in req["components"]
            for p in c["direct_refusals"]
        ]
        return SimpleNamespace(
            stdout=json.dumps(dict(rows=synthetic_matrix(inputs), refusals=refusals))
        )

    monkeypatch.setattr(vendor_rk, "run_oracle", stub)
    files = vendor_rk.collect_snapshot(
        rk,
        vendor_rk.PIN,
        [],
        directory / "model_shapes",
        input_root=directory,
        input_manifest_sha256=identity,
    )
    assert len(json.loads(files["parity/fixtures.json"])) == 1008
    assert len(json.loads(files["parity/refusals.json"])) == 4
    assert files["components/npu-l4.yaml"] == inputs.descriptors["compute.asic.npu-l4"]
    assert files["u2-inputs/SHA256SUMS"] == (directory / "SHA256SUMS").read_bytes()

    # Exercise both historical acceptance consumers against the explicit full matrix.
    # These are literal stubbed outputs in pytest's temporary directory, not an oracle run.
    from contract.tests.test_committed_snapshot import (
        test_committed_manifest_matrix_and_component_provenance,
        test_placeholder_refuses_unsupported_compute_precision,
    )

    synthetic_root = tmp_path / "synthetic-check-only"
    for name, data in files.items():
        path = synthetic_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    vendor_rk.check_snapshot_inputs(synthetic_root)
    test_committed_manifest_matrix_and_component_provenance(synthetic_root)
    test_placeholder_refuses_unsupported_compute_precision(synthetic_root)

    def drifting(*args):
        result = stub(*args)
        (directory / "support-files.json").write_bytes(b"{}")
        return result

    monkeypatch.setattr(vendor_rk, "run_oracle", drifting)
    with pytest.raises(ValueError, match="input bytes changed"):
        vendor_rk.collect_snapshot(
            rk,
            vendor_rk.PIN,
            [],
            directory / "model_shapes",
            input_root=directory,
            input_manifest_sha256=identity,
        )


def test_oracle_program_calls_direct_peak_not_iteration_for_refusals(tmp_path, monkeypatch):
    import contextlib
    import hashlib
    import inspect
    import io
    import sys
    from types import ModuleType, SimpleNamespace

    directory = tmp_path / "inputs"
    identity = u2_inputs.prepare_inputs(directory)
    inputs = u2_inputs.load_inputs(directory, identity)
    calls = []

    class UnsupportedPrecision(Exception):
        pass

    class Precision:
        def __init__(self, compute, kv_cache):
            self.compute = SimpleNamespace(value=compute)
            self.kv_cache = SimpleNamespace(value=kv_cache)

        @classmethod
        def model_validate(cls, data):
            return cls(**data)

        def model_dump(self, **kw):
            return dict(compute=self.compute.value, kv_cache=self.kv_cache.value)

    class Model:
        def __init__(self, value):
            self.value = value

        @classmethod
        def model_validate(cls, value):
            return cls(value)

        def model_dump(self, **kw):
            return self.value

    class Accelerator:
        def __init__(self, descriptor):
            self.descriptor = descriptor

        def peak_op_per_s(self, fmt):
            calls.append(("direct", self.descriptor["id"], fmt.value))
            if fmt.value + "_tflops" not in self.descriptor["params"]:
                raise UnsupportedPrecision("synthetic missing peak")
            return 1

    import yaml

    def accelerator(instance, precision):
        return Accelerator(instance.descriptor), (), SimpleNamespace(value="stub")

    def iteration(model, accel, precision, tp=1):
        calls.append(("iteration", accel.descriptor["id"], precision.compute.value))
        counts = SimpleNamespace(matrix_ops=64, memory_read_bytes=128, memory_write_bytes=32)
        return SimpleNamespace(
            decode_counts=lambda *a: SimpleNamespace(
                matrix_ops=64, memory_read_bytes=128, memory_write_bytes=None
            ),
            prefill_counts=lambda *a: counts,
            decode_s=lambda *a: 1.0,
            prefill_s=lambda *a: 1.0,
        )

    modules = {
        "rk.components.loader": dict(
            load_component_file=lambda p: SimpleNamespace(
                id=yaml.safe_load(p.read_bytes())["id"], raw=yaml.safe_load(p.read_bytes())
            )
        ),
        "rk.engine.f0.compute": dict(
            UnsupportedPrecision=UnsupportedPrecision, iteration_cost=iteration
        ),
        "rk.engine.orchestrator": dict(
            _Instance=lambda id, n, d, *a: SimpleNamespace(descriptor=d.raw),
            _accelerator=accelerator,
        ),
        "rk.schema.execution": dict(Precision=Precision),
        "rk.schema.fidelity": dict(FidelityMap=lambda **kw: None),
        "rk.schema.workloads": dict(ModelSpec=Model),
    }
    for name, attrs in modules.items():
        module = ModuleType(name)
        module.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, module)
    source = tmp_path / "synthetic-compute.py"
    source.write_bytes(b"explicit synthetic callable source")
    monkeypatch.setattr(inspect, "getsourcefile", lambda obj: str(source))
    components = [
        dict(
            name=name,
            path=str(directory / "components" / name),
            sha256="0" * 64,
            precisions=pairs,
            direct_refusals=[
                dict(compute=f, kv_cache=f)
                for f in (
                    ("bf16", "fp8")
                    if name == "asic_placeholder.yaml"
                    else ("fp16", "fp8")
                    if name == "npu-l4.yaml"
                    else ()
                )
            ],
        )
        for name, pairs in inputs.matrix.items()
    ]
    request = dict(
        sha=vendor_rk.PIN,
        models=inputs.models,
        queries=vendor_rk.QUERIES,
        components=components,
        direct_peak_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(request)))
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(vendor_rk.ORACLE_PROGRAM, "synthetic-oracle-control", "exec"), {})
    data = json.loads(output.getvalue())
    assert len(data["rows"]) == 1008 and len(data["refusals"]) == 4
    assert len([c for c in calls if c[0] == "direct"]) == 4
    assert not any(
        c[0] == "iteration" and c[1] == "compute.asic.npu-l4" and c[2] in ("fp16", "fp8")
        for c in calls
    )
