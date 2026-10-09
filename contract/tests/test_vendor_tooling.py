"""U-P2 tooling acceptance tests use synthetic bytes, never an rk-sim oracle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.vendor_rk import (
    PIN,
    QUERIES,
    check_adr_pin,
    check_clone,
    check_manifest,
    publish_snapshot,
    snapshot_bytes,
)


def test_manifest_tamper_names_file(tmp_path: Path) -> None:
    files = snapshot_bytes({"schema.json": b'{"synthetic": true}\n'}, PIN)
    publish_snapshot(tmp_path / "snapshot", files)
    check_manifest(tmp_path / "snapshot", PIN)
    target = tmp_path / "snapshot/schema.json"
    target.chmod(0o644)
    target.write_bytes(b'{"synthetic": True}\n')
    with pytest.raises(ValueError, match="schema.json"):
        check_manifest(tmp_path / "snapshot", PIN)


def test_synthetic_staging_is_byte_identical_and_read_only(tmp_path: Path) -> None:
    files = snapshot_bytes({"schema.json": b"{}\n"}, PIN)
    for name in ("first", "second"):
        publish_snapshot(tmp_path / name, files)
    assert {p.name: p.read_bytes() for p in (tmp_path / "first").iterdir()} == {
        p.name: p.read_bytes() for p in (tmp_path / "second").iterdir()
    }
    assert all(p.stat().st_mode & 0o222 == 0 for p in (tmp_path / "first").iterdir())
    publish_snapshot(tmp_path / "first", files)  # identical rerun is a verified no-op
    with pytest.raises(ValueError, match="different"):
        publish_snapshot(tmp_path / "first", snapshot_bytes({"schema.json": b"[]"}, PIN))


@pytest.mark.parametrize("mutation", ["missing", "extra", "traversal", "symlink"])
def test_manifest_rejects_incomplete_or_unsafe_tree(tmp_path: Path, mutation: str) -> None:
    root = tmp_path / "snapshot"
    publish_snapshot(root, snapshot_bytes({"schema.json": b"{}"}, PIN))
    if mutation == "missing":
        (root / "schema.json").unlink()
    elif mutation == "extra":
        (root / "extra").write_text("unexpected")
    elif mutation == "symlink":
        (root / "schema.json").unlink()
        (root / "schema.json").symlink_to(tmp_path / "outside")
    else:
        manifest = root / "MANIFEST.json"
        data = json.loads(manifest.read_text())
        data["files"]["../outside"] = "0" * 64
        manifest.chmod(0o644)
        manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        check_manifest(root, PIN)


def test_query_matrix_has_24_distinct_points_and_g2_decode_points() -> None:
    assert len(QUERIES) >= 24
    assert len({json.dumps(q, sort_keys=True) for q in QUERIES}) == len(QUERIES)
    decode = {(q["batch"], q["total_context_tokens"]) for q in QUERIES if q["phase"] == "decode"}
    assert {(b, b * t) for b in (1, 8, 32) for t in (512, 4096)} <= decode
    assert any(q["phase"] == "prefill" for q in QUERIES)


def test_absent_u0001_allows_preparation(tmp_path: Path) -> None:
    check_adr_pin(tmp_path / "U0001.md", PIN, pre_contract=True)


def test_explicit_upstream_pin_ignores_repository_history(tmp_path: Path) -> None:
    adr = tmp_path / "U0001.md"
    adr.write_text(
        f"**Reference:** rk-sim `{PIN}`, read only from\n"
        "`../rk-sim-u1-pin`, verified clean. Lane A baseline:\n"
        "`af3b1bc3df3171d196394a58f62202ad50845dfa`; parent\n"
        "`fa16aeb5671f0f0fbfc372d7d57487fddaf65933`.\n"
    )
    check_adr_pin(adr, PIN)


def test_wrong_upstream_pin_fails_even_if_correct_pin_appears_elsewhere(tmp_path: Path) -> None:
    adr = tmp_path / "U0001.md"
    adr.write_text(f"**Reference:** rk-sim `{'a' * 40}`\n\nHistorical note: `{PIN}`\n")
    with pytest.raises(ValueError, match="U0001.*upstream"):
        check_adr_pin(adr, PIN)


@pytest.mark.parametrize(
    "text",
    [
        "No reference yet.",
        f"Historical rk-sim pin: `{PIN}`",
        f"**Reference:** rk-uarch `{PIN}`",
        f"**Reference:** rk-sim `{PIN[:7]}`\nElsewhere: `{PIN}`",
        f"**Reference:** rk-sim `{PIN}` or `{'a' * 40}`",
        f"**Reference:** rk-sim `{PIN}`\n**Reference:** rk-sim `{'a' * 40}`",
        f"**Reference:** rk-sim `{PIN}`\n**Reference:** rk-sim `{PIN}`",
    ],
)
def test_existing_adr_requires_one_unambiguous_upstream_reference(
    tmp_path: Path, text: str
) -> None:
    adr = tmp_path / "U0001.md"
    adr.write_text(text)
    with pytest.raises(ValueError, match="U0001.*upstream"):
        check_adr_pin(adr, PIN)


def test_changed_generator_fingerprint_never_overwrites_existing_snapshot(tmp_path: Path) -> None:
    original = snapshot_bytes({"GENERATOR.json": b'{"script_sha256": "old"}'}, PIN)
    destination = tmp_path / "snapshot"
    publish_snapshot(destination, original)
    updated = snapshot_bytes({"GENERATOR.json": b'{"script_sha256": "new"}'}, PIN)
    with pytest.raises(ValueError, match="different output"):
        publish_snapshot(destination, updated)
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == original
    check_manifest(destination, PIN)


def test_clone_refuses_wrong_sha_and_dirty_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.vendor_rk.git", lambda root, *args: "a" * 40)
    with pytest.raises(ValueError, match="HEAD"):
        check_clone(Path("."), PIN)
    monkeypatch.setattr(
        "scripts.vendor_rk.git", lambda root, *args: PIN if args[0] == "rev-parse" else " M file"
    )
    with pytest.raises(ValueError, match="clean"):
        check_clone(Path("."), PIN)


def test_component_precision_coverage() -> None:
    from scripts.vendor_rk import component_precisions

    baseline = list(component_precisions("asic_placeholder.yaml"))
    assert baseline == [
        {"compute": "fp16", "kv_cache": "fp16"},
        {"compute": "fp16", "kv_cache": "fp8"},
    ]
    assert list(component_precisions("nvidia_h100_sxm.yaml")) == baseline + [
        {"compute": "bf16", "kv_cache": "bf16"},
        {"compute": "fp8", "kv_cache": "fp8"},
    ]


def test_channel_translation_is_exact_and_preserves_values() -> None:
    from .vendor_support import COUNT_CHANNELS, translate_count_names

    assert COUNT_CHANNELS == {
        "matrix_ops": "matrix_ops",
        "vector_ops": "vector_ops",
        "memory_read_bytes": "memory_read",
        "memory_write_bytes": "memory_write",
    }
    counts = {
        "matrix_ops": 100,
        "vector_ops": None,
        "memory_read_bytes": 80,
        "memory_write_bytes": None,
    }
    assert translate_count_names(counts) == {
        "matrix_ops": 100,
        "vector_ops": None,
        "memory_read": 80,
        "memory_write": None,
    }
    with pytest.raises(ValueError, match="unknown"):
        translate_count_names(counts | {"unknown": 1})


def test_oracle_bridge_synthetic_dispatch_self_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Execute the bridge with sentinels, proving dispatch, NOT real rk-sim parity."""
    import builtins
    import io
    import subprocess
    from types import SimpleNamespace
    from typing import Any

    from scripts import vendor_rk as vendor

    class FakeModel:
        @classmethod
        def model_validate(cls, raw: dict[str, Any]) -> Any:
            return SimpleNamespace(model_dump=lambda **kw: raw)

    class FakePrecision:
        def __init__(self, compute: str, kv_cache: str) -> None:
            self.compute = SimpleNamespace(value=compute)
            self.kv_cache = SimpleNamespace(value=kv_cache)

        @classmethod
        def model_validate(cls, raw: dict[str, str]) -> FakePrecision:
            return cls(**raw)

        def model_dump(self, **kwargs: Any) -> dict[str, str]:
            return {"compute": self.compute.value, "kv_cache": self.kv_cache.value}

    class UnsupportedPrecision(ValueError):
        pass

    calls: list[tuple[Any, ...]] = []

    def iteration_cost(model: Any, accelerator: Any, precision: Any, *, tp: int = 1) -> Any:
        calls.append(("iteration_cost", accelerator, precision.compute.value, tp))
        if accelerator == "asic_placeholder.yaml" and precision.compute.value != "fp16":
            raise UnsupportedPrecision("synthetic unsupported format")

        def counts(*args: Any, phase: str) -> Any:
            calls.append(("counts", phase, args))
            return SimpleNamespace(
                matrix_ops=1234.0,
                memory_read_bytes=5678.0,
                memory_write_bytes=None if phase == "decode" else 9012.0,
            )

        return SimpleNamespace(
            decode_counts=lambda *args: counts(*args, phase="decode"),
            prefill_counts=lambda *args: counts(*args, phase="prefill"),
            decode_s=lambda *args: 0.123,
            prefill_s=lambda *args: 0.456,
        )

    fake_modules = {
        "rk.components.loader": SimpleNamespace(
            load_component_file=lambda path: SimpleNamespace(id=path.name)
        ),
        "rk.engine.f0.compute": SimpleNamespace(
            iteration_cost=iteration_cost, UnsupportedPrecision=UnsupportedPrecision
        ),
        "rk.engine.orchestrator": SimpleNamespace(
            _Instance=lambda *args: args,
            _accelerator=lambda instance, precision: (
                instance[0],
                ["synthetic"],
                SimpleNamespace(value="stub"),
            ),
        ),
        "rk.schema.execution": SimpleNamespace(Precision=FakePrecision),
        "rk.schema.fidelity": SimpleNamespace(FidelityMap=lambda **kw: kw),
        "rk.schema.workloads": SimpleNamespace(ModelSpec=FakeModel),
    }
    captured: list[str] = []

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        assert command[:4] == ["uv", "run", "--project", str(tmp_path)]
        assert "--no-sync" in command and "--frozen" in command and "-B" in command
        assert kwargs["cwd"] == tmp_path
        assert "PYTHONPATH" not in kwargs["env"]

        def importer(name: str, *args: Any, **kw: Any) -> Any:
            if name in fake_modules:
                return fake_modules[name]
            if name == "sys":
                return SimpleNamespace(stdin=io.StringIO(kwargs["input"]))
            return builtins.__import__(name, *args, **kw)

        scope = {
            "__builtins__": dict(
                vars(builtins), __import__=importer, print=lambda value: captured.append(value)
            )
        }
        exec(compile(command[-1], "<synthetic-oracle-bridge>", "exec"), scope)
        return subprocess.CompletedProcess(command, 0, captured[-1], "")

    for name in (*vendor.SOURCES, "web/src/schema.json", "uv.lock"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}")
    for name in vendor.REQUIRED_COMPONENTS:
        path = tmp_path / "rk/components/library/compute" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic " + name)
    extra = tmp_path / "custom chip.yaml"
    extra.write_text("synthetic extra params")
    monkeypatch.setattr(
        vendor, "git", lambda root, *args: vendor.PIN if args[0] == "rev-parse" else ""
    )
    monkeypatch.setattr(subprocess, "run", fake_run)
    environment = {
        "python_version": "3.12.0",
        "implementation": "CPython",
        "packages": {"synthetic": "1"},
        "uv_lock_sha256": vendor.digest(b"{}"),
    }
    environment_checks: list[str] = []
    monkeypatch.setattr(
        vendor, "verify_oracle_environment", lambda *args: environment_checks.append("verified")
    )
    monkeypatch.setattr(vendor, "record_oracle_environment", lambda *args: environment)
    interpreter = tmp_path.parent / (tmp_path.name + "-external-env/bin/python")
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(interpreter.parent.parent))
    shapes = vendor.ROOT / "contract/fixtures/model_shapes"
    first = vendor.collect_snapshot(tmp_path, vendor.PIN, [], shapes)
    second = vendor.collect_snapshot(tmp_path, vendor.PIN, [], shapes)
    assert first == second
    assert environment_checks == ["verified"] * 4  # before and after both collections
    assert json.loads(first["GENERATOR.json"])["environment"] == environment
    assert first["uv.lock"] == b"{}"
    rows = json.loads(first["parity/fixtures.json"])
    assert len(rows) == 864  # retained explicit pairs only; unknown inputs must refuse
    assert {r["duration_s"] for r in rows} == {0.123, 0.456}
    assert {r["counts"]["matrix_ops"] for r in rows} == {1234.0}
    assert len([call for call in calls if call[0] == "counts"]) == 1728
    vendor.validate_refusals(json.loads(first["parity/refusals.json"]))
    with pytest.raises(ValueError, match="incomplete matrix"):
        vendor.validate_matrix(rows[:-1])
    publish_snapshot(tmp_path / "synthetic-output", first)
    check_manifest(tmp_path / "synthetic-output")
    with pytest.raises(ValueError, match="Explicit ComponentPrecision"):
        vendor.collect_snapshot(tmp_path, vendor.PIN, [extra], shapes)


def test_vendor_cli_refuses_without_human_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    from scripts.vendor_rk import main

    monkeypatch.delenv("UARCH_HUMAN", raising=False)
    monkeypatch.setattr(sys, "argv", ["vendor_rk.py", "--sha", PIN])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_path_loader_resolves_synthetic_absolute_imports_without_registering_rk(
    tmp_path: Path,
) -> None:
    import sys

    from .vendor_support import VendorLoader

    (tmp_path / "rk/schema").mkdir(parents=True)
    (tmp_path / "rk/provenance.py").write_text("SENTINEL = 42\n")
    (tmp_path / "rk/schema/fidelity.py").write_text(
        "from rk.provenance import SENTINEL\nVALUE = SENTINEL\n"
    )
    assert VendorLoader(tmp_path).load("rk.schema.fidelity").VALUE == 42
    assert "rk" not in sys.modules


def test_oracle_environment_must_already_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.vendor_rk import oracle_environment

    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    with pytest.raises(ValueError, match="provision"):
        oracle_environment(tmp_path)
    monkeypatch.setenv(
        "UV_PROJECT_ENVIRONMENT", str(tmp_path.parent / (tmp_path.name + "-external-env"))
    )
    interpreter = tmp_path.parent / (tmp_path.name + "-external-env/bin/python")
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    assert oracle_environment(tmp_path)["UV_PROJECT_ENVIRONMENT"] == str(
        tmp_path.parent / (tmp_path.name + "-external-env")
    )
