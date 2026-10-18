"""Private cfg(test) file-probe adapter for B's bounded audit; never a public runner.

Each slot launches a fresh test executable in the accepted image with synthetic anchors.
It is NOT an EOF/production-executable success test. Ordinary binary refusals are separate.
No selector, HostRecord, real authority, public replay or caller-supplied raw input exists.
"""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from typing import Any

from uarch_contract.hashing import sha256, strict_json_loads

from rkuarch.engines.native.component_host import _prepare_payload
from rkuarch.engines.native.component_runner import _consume
from rkuarch.engines.native.host import _read, _require
from rkuarch.engines.native.records import FileBinding
from rkuarch.engines.native.runner import Limits, _decode_envelope, _exchange

IMAGE = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
TEST = "protocol::component_runtime_tests::private_selected_transport_probe"


def _bytes(path: Path, cap: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(cap + 1)
    _require(len(raw) <= cap, "private probe output limit")
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
        raw = _read(self.root, FileBinding.model_validate(self.transitions[name]["file"]))
        job = strict_json_loads(raw)
        _require(
            job["profile"] == row["profile"]
            and job["engine"] == self.prepared[mode].payload.engine.model_dump(mode="json"),
            "independent private job/profile/engine promise",
        )
        if name in self.negatives:
            profile = FileBinding.model_validate(self.negatives[name]["profile"])
            _require(
                job["profile"] == strict_json_loads(_read(self.root, profile)),
                "independent negative profile file",
            )
        if slot["phase"] == "replay":
            _require(
                initial is not None
                and initial["outcome"] == "success"
                and initial["raw_input_sha256"] == sha256(raw).split(":")[1]
                and initial["execution_binding"] == self.binding.byte_hash,
                "private successful receipt required for replay",
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
        (run / "docker-config").mkdir()
        argv = [
            "/usr/bin/docker",
            "--config",
            str(run / "docker-config"),
            "--host",
            "unix:///var/run/docker.sock",
            "run",
            "--rm",
            "--pull",
            "never",
            "--cidfile",
            str(run / "container.id"),
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
        shell = run / "bounded-probe.sh"
        shell.write_text("#!/bin/sh\nexec " + shlex.join(argv) + "\n")
        shell.chmod(0o555)
        fd = os.open(shell, os.O_RDONLY)
        try:
            stdout, stderr, status = _exchange(fd, b"", Limits(30, 1, 1024 * 1024, 1024 * 1024))
        finally:
            os.close(fd)
        (run / "harness.stdout").write_bytes(stdout)
        (run / "harness.stderr").write_bytes(stderr)
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
            error = _decode_envelope(result_stdout, result_stderr, semantic)
            _require(
                semantic == 2
                and entries == 0
                and error["code"] == row["expected_code"]
                and error["pointer"] == self.negatives[name]["expected_pointer"],
                "private exact refusal and zero runtime entry",
            )
            outcome = error["code"]
        self._refresh()
        container = (run / "container.id").read_text().strip()
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
        return {
            "raw_input": raw,
            "stdout": result_stdout,
            "stderr": result_stderr,
            "process_identity": "docker:" + container + ":pid1",
            "checked": True,
            "outcome": outcome,
            "producers_disabled": True,
            "expected_pointer_verified": semantic == 2,
            "zero_dispatch_evidence": str(run / "receipt.json") if semantic == 2 else None,
        }
