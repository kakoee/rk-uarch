"""Private cfg(test) file-probe adapter for B's bounded audit; never a public runner.

Each slot launches a fresh test executable in the accepted image with synthetic anchors.
It is NOT an EOF/production-executable success test. Ordinary binary refusals are separate.
No selector, HostRecord, real authority, public replay or caller-supplied raw input exists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uarch_contract.hashing import sha256, strict_json_loads

from native.tools.component_container_guard import cleanup as cleanup_containers
from native.tools.component_container_guard import run_container
from rkuarch.engines.native.component_host import _prepare_payload
from rkuarch.engines.native.component_runner import _consume, require_negative_envelope
from rkuarch.engines.native.host import _read, _require
from rkuarch.engines.native.records import FileBinding

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
TEST = "protocol::component_runtime_tests::private_selected_transport_probe"


def _bytes(path: Path, cap: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(cap + 1)
    _require(len(raw) <= cap, "private probe output limit")
    return raw


def saved_input(
    root: Path, binding: FileBinding, initial: dict[str, Any] | None, cap: int
) -> bytes:
    """Replay reads B's retained bytes; identity comes from A's admitted inventory."""
    if initial is None:
        raw = _read(root, binding)
    else:
        _require(
            initial["raw_input_sha256"] == binding.byte_hash.split(":")[1],
            "durable replay inventory digest",
        )
        raw = _bytes(Path(initial["saved_input_path"]), cap)
    _require(
        len(raw) <= cap and sha256(raw) == binding.byte_hash, "private independent raw inventory"
    )
    return raw


class PrivateAdapter:
    """Finite immutable inputs and byte-bound test executables; synthetic data only."""

    def __init__(self, build_root: Path, output: Path) -> None:
        self.build_root = build_root.resolve()
        self.root = self.build_root / "source"
        _require(
            self.build_root.is_relative_to(Path("/tmp"))
            and output.resolve().is_relative_to(Path("/tmp")),
            "private /tmp roots required",
        )
        self.output = output.resolve()
        self.output.mkdir(exist_ok=False)
        self.container_scope = self.output / "containers"
        self.container_scope.mkdir()
        payload = self.root / "private-component/prospective-payload.json"
        self.binding = FileBinding(
            path=str(payload.relative_to(self.root)), byte_hash=sha256(payload.read_bytes())
        )
        self.prepared = {
            m: _prepare_payload(self.root, self.binding, mode=m) for m in ("debug", "release")
        }
        self.summary = strict_json_loads((self.build_root / "build-summary.json").read_bytes())
        _require(
            self.summary["engine"] == self.prepared["debug"].payload.engine.model_dump(mode="json"),
            "private executable/engine binding",
        )
        self.selection = strict_json_loads(
            (self.root / "private-component/selection.json").read_bytes()
        )
        self.rows = {r["case_id"]: r for r in self.selection["rows"]}
        self.allowed = set(
            strict_json_loads(
                (self.root / "private-component/affected-selection.json").read_bytes()
            )["ids"]
        )
        self.transitions = {
            r["case_id"]: r
            for r in strict_json_loads(
                (self.root / "private-component/job-transitions.json").read_bytes()
            )
        }
        self.negatives = {
            r["case_id"]: r
            for r in strict_json_loads(
                (self.root / "private-component/negative-inventory.json").read_bytes()
            )["cases"]
        }
        self.negative_expectations = {
            r["case_id"]: r
            for r in strict_json_loads(
                (self.root / "private-component/negative-expectations.json").read_bytes()
            )["rows"]
        }
        self.slots: list[dict[str, Any]] = []
        self.files = {}
        for prepared in self.prepared.values():
            for base, binding in prepared.checks:
                self.files[str(base / binding.path)] = binding.byte_hash.split(":")[1]
        for name in ("build-summary.json",):
            path = self.build_root / name
            self.files[str(path)] = sha256(path.read_bytes()).split(":")[1]
        for name in (
            "selection.json",
            "affected-selection.json",
            "job-transitions.json",
            "negative-inventory.json",
            "negative-expectations.json",
        ):
            path = self.root / "private-component" / name
            self.files[str(path)] = sha256(path.read_bytes()).split(":")[1]
        for mode in ("debug", "release"):
            record = self.summary["modes"][mode]
            path = Path(record["test_executable"])
            _require(path.resolve().is_relative_to(self.build_root), "private test executable root")
            self.files[str(path)] = record["test_executable_byte_hash"].split(":")[1]
        for name in self.allowed:
            binding = FileBinding.model_validate(self.transitions[name]["file"])
            _read(self.root, binding)
            self.files[str(self.root / binding.path)] = binding.byte_hash.split(":")[1]
            if name in self.negatives:
                profile = FileBinding.model_validate(self.negatives[name]["profile"])
                _read(self.root, profile)
                self.files[str(self.root / profile.path)] = profile.byte_hash.split(":")[1]
        self._refresh()

    def cleanup(self) -> dict[str, Any]:
        """B parent calls after stopping/joining workers, including failed campaigns."""
        receipts = cleanup_containers(self.container_scope)
        return {"verified_stopped": True, "outstanding": [], "containers": receipts}

    def _refresh(self) -> None:
        for path, wanted in self.files.items():
            _require(
                sha256(Path(path).read_bytes()).split(":")[1] == wanted,
                "private audit setup changed: " + path,
            )
        for prepared in self.prepared.values():
            prepared.refresh()

    def preflight(self, selection: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        self._refresh()
        ids = {r["case_id"] for r in selection["rows"]}
        _require(
            ids <= self.allowed and all(r == self.rows[r["case_id"]] for r in selection["rows"]),
            "private selected definition mismatch",
        )
        _require(
            policy["process_limit_required"] == 64
            and policy["nofile"] == 256
            and policy["per_call_seconds"] == 30,
            "reviewed bounded private policy required",
        )
        from validation.component.runtime_campaign import schedule

        self.slots = schedule(self.selection, sorted(ids))
        return {
            "evidence_kind": "private-synthetic-test",
            "pids_limit": 64,
            "execution_binding": self.binding.byte_hash,
            "files": self.files,
            "input_hashes": {
                n: self.transitions[n]["file"]["byte_hash"].split(":")[1] for n in ids
            },
            "transport": "fresh cfg(test) file-probe process, not production EOF success",
        }

    def call(
        self,
        slot: dict[str, Any],
        row: dict[str, Any],
        initial: dict[str, Any] | None,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        self._refresh()
        _require(slot in self.slots, "preflight selected finite slot required")
        name, mode = slot["case_id"], slot["mode"]
        _require(
            name in self.allowed
            and row == self.rows[name]
            and mode in self.prepared
            and slot["phase"] in ("initial", "replay")
            and slot["repetition"] in (0, 1, 2),
            "private finite slot required",
        )
        admitted_file = FileBinding.model_validate(self.transitions[name]["file"])
        if slot["phase"] == "replay":
            _require(initial is not None, "durable initial receipt required for replay")
        else:
            _require(initial is None, "initial call cannot supply replay descriptor")
        raw = saved_input(
            self.root, admitted_file, initial, self.prepared[mode].payload.budget.stdin_bytes
        )
        job = strict_json_loads(raw)
        _require(
            job["profile"] == row["profile"]
            and job["engine"] == self.prepared[mode].payload.engine.model_dump(mode="json"),
            "independent private job/profile/engine promise",
        )
        if name in self.negatives:
            expected_negative = self.negative_expectations[name]
            _require(
                expected_negative["input_sha256"] == admitted_file.byte_hash.split(":")[1]
                and expected_negative["job_hash"] == job["job_hash"]
                and expected_negative["engine"] == job["engine"],
                "private negative expectation input/engine join",
            )
            guard = expected_negative["native_guard_source"]
            _require(
                sha256((self.root / guard["path"]).read_bytes()).split(":")[1] == guard["sha256"],
                "private negative guard source",
            )
            profile = FileBinding.model_validate(self.negatives[name]["profile"])
            _require(
                job["profile"] == strict_json_loads(_read(self.root, profile)),
                "independent negative profile file",
            )
        # Explicit saved-input producer disable; no producer module is needed to consume it.
        import rkuarch.workload.mapped as producer

        def unavailable(*args: Any, **kwargs: Any) -> None:
            raise ValueError("private replay producer preparation unavailable")

        producer.export_component_job = unavailable
        producer.export_component_bundle = unavailable
        run = self.output / f"{slot['ordinal']:05d}"
        run.mkdir(exist_ok=False)
        inputs, outputs = run / "input", run / "output"
        inputs.mkdir()
        outputs.mkdir()
        (inputs / "case.json").write_bytes(raw)
        exe = Path(self.summary["modes"][mode]["test_executable"])
        argv = [
            "--network",
            "none",
            "--read-only",
            "--user",
            "1000:1000",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            "1g",
            "--cpus",
            "1",
            "--ulimit",
            "nofile=256:256",
            "--tmpfs",
            "/tmp",
            "--mount",
            f"type=bind,src={exe},dst=/private-test,readonly",
            "--mount",
            f"type=bind,src={inputs},dst=/inputs,readonly",
            "--mount",
            f"type=bind,src={outputs},dst=/outputs",
            "--entrypoint",
            "/usr/bin/env",
            IMAGE,
            "-i",
            "COMPONENT_PRIVATE_INPUT=/inputs",
            "COMPONENT_PRIVATE_OUTPUT=/outputs/result",
            "/private-test",
            TEST,
            "--ignored",
            "--exact",
            "--nocapture",
        ]
        cleanup_receipt = run_container(
            self.container_scope / f"{slot['ordinal']:05d}",
            argv,
            timeout=policy["per_call_seconds"],
            cap=1024 * 1024,
        )
        container_run = self.container_scope / f"{slot['ordinal']:05d}"
        stdout = _bytes(container_run / "stdout", 1024 * 1024)
        stderr = _bytes(container_run / "stderr", 1024 * 1024)
        status = cleanup_receipt["exit_code"]
        (run / "harness.stdout").write_bytes(stdout)
        (run / "harness.stderr").write_bytes(stderr)
        _require(cleanup_receipt["reason"] == "completed", "private container incomplete")
        _require(status == 0 and b"1 passed" in stdout, "private unit process failed")
        value = _bytes(outputs / "result/case.json", 64 * 1024**2)
        semantic = int(_bytes(outputs / "result/case.status", 16))
        entries = int(_bytes(outputs / "result/case.runtime-entries", 16))
        result_stdout, result_stderr = (value, b"") if semantic == 0 else (b"", value)
        if row["expected_layer"] == "result":
            _require(semantic == 0 and entries == 1, "private positive native entry")
            _consume(self.prepared[mode], json.loads(raw), value, b"", 0)
            outcome = "success"
        else:
            error = require_negative_envelope(
                result_stdout, result_stderr, semantic, self.negative_expectations[name]["envelope"]
            )
            _require(entries == 0, "private negative zero runtime entry")
            outcome = error["code"]
        self._refresh()
        container = cleanup_receipt["container_id"]
        _require(
            len(container) == 64 and all(c in "0123456789abcdef" for c in container),
            "actual private container identity required",
        )
        receipt = {
            "argv": argv,
            "container_id": container,
            "harness_exit_code": status,
            "semantic_status": semantic,
            "test_executable_byte_hash": self.summary["modes"][mode]["test_executable_byte_hash"],
            "raw_input_byte_hash": sha256(raw),
            "semantic_output_byte_hash": sha256(value),
            "runtime_entries": entries,
            "evidence": "cfg(test) file-probe; synthetic anchors",
        }
        (run / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        witness = {
            "case_id": name,
            "mode": mode,
            "raw_input_sha256": sha256(raw).split(":")[1],
            "semantic_output_sha256": sha256(value).split(":")[1],
            "executable_sha256": self.summary["modes"][mode]["test_executable_byte_hash"].split(
                ":"
            )[1],
            "process_identity": "docker:" + container + ":pid1",
            "runtime_entries": entries,
            "transport_complete": True,
            "evidence": "cfg(test) file-probe; synthetic anchors",
        }
        (run / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
        return {
            "raw_input": raw,
            "stdout": result_stdout,
            "stderr": result_stderr,
            "process_identity": "docker:" + container + ":pid1",
            "outcome": outcome,
            "status": semantic,
            "witness": witness,
            "cleanup": {
                **cleanup_receipt,
                "verified_stopped": cleanup_receipt["stopped"] and cleanup_receipt["removed"],
                "process_identity": "docker:" + container + ":pid1",
            },
            "evidence_path": str(run / "receipt.json"),
        }
