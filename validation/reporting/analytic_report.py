"""Accepted U0006 standalone reports for the captured model-v1 graph only.

U2 physical-resolved/1 excludes RoPE rotation/conversion work and coefficient
traffic; these checks do not certify complete RoPE-equipped decoder work.
No SourceRecord, review, card, production dispatcher or hardware accuracy claim.
"""

from __future__ import annotations

import argparse
import base64
import copy
import importlib.metadata
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from hypothesis import Phase, given, settings
from hypothesis import strategies as st
from uarch_contract.assumptions import AssumptionSet
from uarch_contract.hardware import HardwareSpec
from uarch_contract.hashing import (
    canonical_json,
    content_hash,
    sha256,
    spec_hash,
    strict_json_loads,
    verify_identity,
)
from uarch_contract.request import CharacterizationRequest, RequestIntent

from rkuarch.engines.analytic import core
from rkuarch.engines.protocol import EngineIdentity, EngineJob, EngineResult, validate_engine_result
from rkuarch.workload import prepare as producer
from rkuarch.workload.prepared import (
    load_prepared_input,
    physical_assumptions,
    validate_execution_bundle,
)
from validation.analytic_checks import check_attribution, check_counts, check_nulls
from validation.mutants.analytic import mutant
from validation.strategies import FIXTURE, fixed_bundle, hardware_specs, jobs, replace_hardware_leaf

ROOT = Path(__file__).resolve().parents[2]
FORMAT = "uarch-analytic-verification-source/1"
ENTRYPOINT = "validation.reporting.analytic_report"
LOADED_SUITE_HASH = sha256(Path(__file__).read_bytes())
V1_HASH = "sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea"
V1_ASSUMPTIONS = "sha256:255afd1ceb9c02a4909464c41e98e16085485a8e500090a8e2d98dc2ee56a896"
MODES = ["aggregate", "per_op"]
LEDGERS = ("discovery", "candidate", "mutant")
# Report implementation binding, not U0002's independent support inventory/check.
# Explanatory Markdown may advance with peer work without changing execution bytes.
BOUND_PATHS = (
    "src",
    "contract",
    "validation",
    "pyproject.toml",
    "uv.lock",
    ":(exclude,glob)**/*.md",
)
L0 = {
    "fixed_counts": ("counts", "off_by_one_matrix"),
    "count_rollup": ("counts", None),
    "attribution_sum": ("duration", "double_attribution"),
    "repeat_bytes": ("duration", "nondeterministic_output"),
    "saved_replay": ("duration", None),
    "input_refusal": ("duration", None),
    "null_diagnostics": ("diagnostics", "zero_unmodelled_diagnostic"),
}
L0_SKIPS = {
    "executed_mac_conservation": ("counts", "UNOBSERVABLE_EXECUTED_MACS"),
    "dma_conservation": ("counts", "UNOBSERVABLE_DMA"),
    "window_utilisation": ("diagnostics", "UNOBSERVABLE_BUSY_WINDOWS"),
    "little_law": ("diagnostics", "UNOBSERVABLE_QUEUE"),
    "causality": ("diagnostics", "UNOBSERVABLE_TRACE"),
    "sram_placement": ("diagnostics", "UNOBSERVABLE_PLACEMENT"),
    "energy_conservation": ("energy", "UNOBSERVABLE_ENERGY"),
}
L0M_SKIPS = {
    "noc_sram_bandwidth": "UNREPRESENTED_BANDWIDTH",
    "core_permutation": "UNREPRESENTED_CORE_IDS",
    "idle_core": "UNREPRESENTED_PLACEMENT",
    "unused_stipulation": "DEFERRED_STIPULATION_FIXTURE",
    "latency_monotonicity": "UNREPRESENTED_LATENCY",
    "dma_outstanding": "UNREPRESENTED_DMA_CONCURRENCY",
    "cold_steady": "STATELESS_ROOFLINE",
    "per_op_exact_clock": "MEMORY_ONLY_EMBEDDING",
    "dram_bound_clock": "DEFERRED_DRAM_CLOCK_RELATION",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return strict_json_loads(Path(path).read_bytes())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_head():
    return git("rev-parse", "HEAD")


def check_implementation(commit, *, actual=False):
    require(
        len(commit) == 40 and all(c in "0123456789abcdef" for c in commit),
        "Implementation commit must be a full Git identity",
    )
    git("cat-file", "-e", commit + "^{commit}")
    require(not git("diff", commit, "--", *BOUND_PATHS), "Implementation bytes changed")
    require(
        core.engine_identity().implementation_hash == V1_HASH,
        "Engine implementation is not the accepted model-v1 implementation",
    )
    require(sha256(Path(core.__file__).read_bytes()) == V1_HASH, "Engine implementation changed")
    require(
        physical_assumptions().assumptions_hash == V1_ASSUMPTIONS,
        "Implementation assumptions changed",
    )
    if actual:
        require(
            sha256(Path(__file__).read_bytes()) == LOADED_SUITE_HASH,
            "Loaded suite implementation changed",
        )
        git("cat-file", "-e", commit + ":validation/reporting/analytic_report.py")


def require_committed():
    require(not git("status", "--porcelain"), "Uncommitted implementation or work tree")
    commit = git_head()
    check_implementation(commit, actual=True)
    return commit


def profile(name):
    require(
        name in {"analytic-l0", "analytic-l0m", "analytic-l0-smoke", "analytic-l0m-smoke"},
        "Unknown profile: " + name,
    )
    rung = "L0m" if "l0m" in name else "L0"
    smoke = name.endswith("-smoke")
    cells = []

    def add(relation, purpose, modes, fault=None, reason=None):
        domain = "d4-bf16-v1"
        path = "standalone_producer" if relation.startswith("producer.") else "fixed_prepared"
        ranges = [
            {
                "pointer": "/clock_domains/core/freq_hz/value",
                "minimum": 1_000_000,
                "maximum": 2_000_000_000,
            },
            {
                "pointer": "/cores/core_type/matrix_engine/macs_per_cycle/bf16/value",
                "minimum": 1,
                "maximum": 64,
            },
            {
                "pointer": "/cores/core_type/vector_engine/ops_per_cycle/value",
                "minimum": 1,
                "maximum": 64,
            },
            {
                "pointer": "/memory/dram/bw_bytes_per_s/value",
                "minimum": 1000,
                "maximum": 10_000 if relation == "analytic.dram_memory_response" else 10**12,
            },
        ]
        if relation == "analytic.aggregate_clock":
            ranges.append({"pointer": "/factor", "minimum": 2, "maximum": 4})
        if path == "standalone_producer":
            ranges.extend(
                [
                    {"pointer": "/batch", "minimum": 1, "maximum": 8},
                    {"pointer": "/context", "minimum": 1, "maximum": 64},
                ]
            )
        cells.append(
            {
                "cell_id": relation + "/1:" + "+".join(modes) + ":" + domain,
                "relation_id": relation + "/1",
                "purpose": purpose,
                "modes": modes,
                "path": path,
                "domain": {
                    "id": domain,
                    "definition": {
                        "fixed": {"/engine/model/version": "1", "/precision/compute": "bf16"},
                        "ranges": ranges,
                        "transformation": {
                            "id": relation + "/1",
                            "arguments": {
                                "model_scope": "captured-v1-graph-excludes-rope/1",
                                "selection": "literal" if smoke else "generated",
                                "disposition": reason,
                            },
                        },
                        "tolerance": {"relative": 1e-9, "absolute": 0, "unit": "ps"},
                    },
                    "input_fixture_hashes": [sha256(FIXTURE.read_bytes())],
                    "scope_dimensions": {},
                },
                "premises": [
                    {
                        "id": "domain",
                        "predicate": relation + "-domain/1",
                        "observation_selectors": [{"role": "input_bundle", "json_pointer": ""}],
                    }
                ],
                "budget": {
                    "max_examples": 1 if smoke else 24,
                    "required_valid_examples": 1 if smoke else 24,
                    "max_engine_invocations": 8 if smoke else 240,
                },
                "required_mutants": [] if fault is None else [fault],
            }
        )

    if rung == "L0":
        for key, (purpose, fault) in L0.items():
            for mode in MODES:
                add("analytic." + key, purpose, [mode], fault)
        for key, (purpose, reason) in L0_SKIPS.items():
            for mode in MODES:
                add("L0." + key, purpose, [mode], reason=reason)
    else:
        for key in ("dram_monotone", "dram_memory_response"):
            for mode in MODES:
                add(
                    "analytic." + key,
                    "duration",
                    [mode],
                    "wrong_bandwidth_field" if key == "dram_memory_response" else None,
                )
        add("analytic.aggregate_clock", "duration", ["aggregate"])
        add("analytic.mode_order", "duration", MODES)
        for key in ("decode_batch", "decode_context"):
            for mode in MODES:
                add("producer." + key, "duration", [mode])
        for key, reason in L0M_SKIPS.items():
            for mode in ["per_op"] if key == "per_op_exact_clock" else MODES:
                add("L0m." + key, "duration", [mode], reason=reason)
    return {
        "profile_id": name,
        "profile_version": "1",
        "rung": rung,
        "purposes": sorted({c["purpose"] for c in cells}),
        "modes": MODES.copy(),
        "cells": cells,
        "selection": {
            "policy": "hypothesis-freeze-replay/1",
            "database": None,
            "derandomize": True,
            "seed": None,
            "phases": ["generate", "shrink"],
            "deadline_ms": None,
            "retain": "all_engine_calls_and_counterexamples",
            "corpus_hash": None,
        },
    }


def disposition(cell):
    return cell["domain"]["definition"]["transformation"]["arguments"]["disposition"]


def relation_name(cell):
    return cell["relation_id"].split("/")[0]


def as_json(value):
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def invalid_output_diagnostic(value):
    """Keep JSON exactly when encodable; otherwise describe, never repair, the return.

    The tagged fallback is diagnostic data, not EngineResult JSON. Only built-in
    containers are traversed; opaque values explicitly retain type only, without
    invoking repr, user serializers or property access. Cycles/depth are explicit.
    """
    try:
        raw = strict_json_loads(canonical_json(value).encode("utf-8"))
    except Exception:
        pass
    else:
        return {"code": "INVALID_ENGINE_OUTPUT", "output": raw}

    def describe(item, ancestors=()):
        kind = type(item)
        node = {"type": kind.__module__ + "." + kind.__qualname__}
        if kind is float and not math.isfinite(item):
            node.update(
                encoding="nonfinite",
                value="nan" if math.isnan(item) else ("+infinity" if item > 0 else "-infinity"),
            )
        elif kind is int and item.bit_length() > 4096:
            node.update(encoding="hex", value=hex(item))
        elif kind is str:
            # Surrogates cannot enter the canonical UTF-8 diagnostic bytes.
            node.update(
                encoding="unicode_escape", value=item.encode("unicode_escape").decode("ascii")
            )
        elif kind in (type(None), bool, int, float):
            node["value"] = item
        elif id(item) in ancestors:
            node["unavailable"] = "cycle"
        elif len(ancestors) >= 64:
            node["unavailable"] = "depth_limit"
        elif kind in (dict, list, tuple):
            path = (*ancestors, id(item))
            if kind is dict:
                node["items"] = sorted(
                    [[describe(k, path), describe(v, path)] for k, v in item.items()],
                    key=canonical_json,
                )
            else:
                node["items"] = [describe(v, path) for v in item]
        else:
            node["unavailable"] = "unsupported_python_value"
        return node

    return {
        "code": "INVALID_ENGINE_OUTPUT",
        "output_representation": {"format": "invalid-engine-output/1", "value": describe(value)},
    }


def request_for(bundle):
    return CharacterizationRequest.model_validate(
        {**as_json(bundle.intent), "prepared_input_hash": bundle.bundle_hash}
    )


class Objects:
    def __init__(self, entries=(), sink=None):
        self.sink = sink
        self.bundle_cache = {}
        self.values = {o["hash"]: copy.deepcopy(o) for o in entries}

    def add(self, kind, value):
        raw = as_json(value)
        if kind != "diagnostic":
            raw = strict_json_loads(canonical_json(raw))
        if kind == "diagnostic":
            data = value if isinstance(value, bytes) else canonical_json(raw).encode()
            identity, raw = sha256(data), base64.b64encode(data).decode("ascii")
        elif kind in ("bundle", "job", "result"):
            identity = verify_identity(
                raw, {"bundle": "bundle_hash", "job": "job_hash", "result": "result_hash"}[kind]
            )
        else:
            identity = spec_hash(raw) if kind == "hardware" else content_hash(raw)
        entry = {"hash": identity, "kind": kind, "value": raw}
        require(
            identity not in self.values or self.values[identity] == entry,
            "Object identity collision",
        )
        if identity not in self.values and self.sink is not None:
            self.sink("object", entry)
        self.values[identity] = entry
        return identity

    def bundle(self, bundle):
        self.add("hardware", bundle.hardware_spec)
        self.add("request", request_for(bundle))
        return self.add("bundle", bundle)

    def get(self, identity, kind=None):
        require(identity in self.values, "Missing object " + identity)
        obj = self.values[identity]
        require(kind is None or obj["kind"] == kind, "Object kind mismatch")
        return obj["value"]

    def parsed_bundle(self, identity):
        if identity not in self.bundle_cache:
            self.bundle_cache[identity] = validate_execution_bundle(self.get(identity, "bundle"))
        return self.bundle_cache[identity]

    def export(self):
        return [self.values[k] for k in sorted(self.values)]


class InvocationLimit(BaseException):
    """Abort this discovery cell without a Hypothesis assertion/shrinking failure."""


class EngineStopped(BaseException):
    """A recorded infrastructure error stops this cell, not a counterexample."""


@dataclass
class Recorder:
    objects: Objects = field(default_factory=Objects)
    ledgers: dict = field(default_factory=lambda: {name: [] for name in LEDGERS})
    counters: dict = field(default_factory=dict)
    operational: list = field(default_factory=list)
    interrupted: bool = False
    sink: object = None

    def __post_init__(self):
        self.objects.sink = self.sink

    def emit(self, kind, value):
        if self.sink is not None:
            self.sink(kind, value)

    def invoke(self, case, cell, ledger, engine, job):
        job_hash = self.objects.add("job", job)
        call = {
            "job_hash": job_hash,
            "result_hash": None,
            "diagnostic_hash": None,
            "state": "not_run",
        }
        case["calls"].append(call)
        key = (ledger, cell["cell_id"])
        count = self.counters.get(key, 0)
        if count >= cell["budget"]["max_engine_invocations"]:
            call["diagnostic_hash"] = self.objects.add("diagnostic", {"code": "INVOCATION_CAP"})
            self.interrupted = True
            raise InvocationLimit()
        self.counters[key] = count + 1
        call["state"] = "error"  # Intent is retained before entering the callable.
        self.emit(
            "call_started",
            {"case_id": case["case_id"], "ordinal": len(case["calls"]) - 1, "job_hash": job_hash},
        )
        try:
            output = engine(job)
        except (Exception, KeyboardInterrupt) as exc:
            call["diagnostic_hash"] = self.objects.add(
                "diagnostic", {"code": "ENGINE_EXCEPTION", "type": type(exc).__name__}
            )
            self.operational.append(traceback.format_exc())
            self.interrupted = True
            self.emit("call_finished", {"case_id": case["case_id"], "call": call})
            raise EngineStopped() from exc
        raw = output
        try:
            raw = as_json(output)
            EngineResult.model_validate(raw)
            result_hash = self.objects.add("result", raw)
        except Exception as exc:
            # Diagnostic encoding must not repeat the output's serialization failure.
            call["diagnostic_hash"] = self.objects.add("diagnostic", invalid_output_diagnostic(raw))
            self.operational.append(traceback.format_exc())
            self.interrupted = True
            self.emit("call_finished", {"case_id": case["case_id"], "call": call})
            raise EngineStopped() from exc
        call.update(result_hash=result_hash, state="completed")
        case["results"].append(result_hash)
        self.emit("call_finished", {"case_id": case["case_id"], "call": call})
        return EngineResult.model_validate(raw)


def build_inputs(cell, hardware, factor=2, batch=1, context=1):
    name = relation_name(cell)
    mode = cell["modes"][0]
    if name == "analytic.aggregate_clock":
        hardware = replace_hardware_leaf(hardware, "memory.dram.bw_bytes_per_s", 1e18)
    low = fixed_bundle(mode, hardware)
    if name.startswith("producer."):

        def produce(b, t):
            raw = as_json(low.intent)
            raw["grid"]["decode"] = {"batch": [b], "context_per_seq": [t]}
            raw["envelope"]["decode"] = {"batch_max": b, "context_per_seq_max": t}
            return producer.prepare(RequestIntent.model_validate(raw), hardware)

        return [
            produce(batch, context),
            produce(
                batch * (2 if name.endswith("batch") else 1),
                context * (2 if name.endswith("context") else 1),
            ),
        ]
    if name in ("analytic.dram_monotone", "analytic.dram_memory_response"):
        higher = replace_hardware_leaf(
            hardware, "memory.dram.bw_bytes_per_s", hardware.memory.dram.bw_bytes_per_s.value * 2
        )
        return [low, fixed_bundle(mode, higher)]
    if name == "analytic.aggregate_clock":
        higher = replace_hardware_leaf(
            hardware,
            "clock_domains.core.freq_hz",
            hardware.clock_domains.core.freq_hz.value * factor,
        )
        return [low, fixed_bundle(mode, higher)]
    if name == "analytic.mode_order":
        return [low, fixed_bundle("per_op", hardware)]
    return [low]


def validate_inputs(cell, bundles):
    """Authenticate the declared domain and transformation, without invoking a producer."""
    name = relation_name(cell)
    paired = name in (
        "analytic.dram_monotone",
        "analytic.dram_memory_response",
        "analytic.aggregate_clock",
        "analytic.mode_order",
    ) or name.startswith("producer.")
    require(len(bundles) == (2 if paired else 1), "Domain input arity")
    for index, bundle in enumerate(bundles):
        mode = cell["modes"][index] if name == "analytic.mode_order" else cell["modes"][0]
        require(bundle.intent.analytic_mode == mode, "Domain mode mismatch")
        if not name.startswith("producer."):
            require(
                bundle == fixed_bundle(mode, bundle.hardware_spec), "Domain fixed graph mismatch"
            )
    low = bundles[0]
    hw = low.hardware_spec
    if not cell["domain"]["definition"]["transformation"]["arguments"]["selection"] == "literal":
        for bound in cell["domain"]["definition"]["ranges"]:
            pointer = bound["pointer"]
            if pointer in ("/factor", "/batch", "/context"):
                continue
            if (
                name == "analytic.aggregate_clock"
                and pointer == "/memory/dram/bw_bytes_per_s/value"
            ):
                continue  # Prospectively declared fixed compute-dominant bandwidth.
            value = as_json(hw)
            for part in pointer.strip("/").split("/"):
                value = value[part]
            require(bound["minimum"] <= value <= bound["maximum"], "Domain hardware range")
    if not paired:
        return
    high = bundles[1]
    if name.startswith("producer."):
        require(low.hardware_spec == high.hardware_spec, "Producer transformation hardware")
        a, b = as_json(low.intent), as_json(high.intent)
        batch = a["grid"]["decode"]["batch"][0]
        context = a["grid"]["decode"]["context_per_seq"][0]
        require(1 <= batch <= 8 and 1 <= context <= 64, "Producer domain range")
        new_batch = batch * (2 if name.endswith("batch") else 1)
        new_context = context * (2 if name.endswith("context") else 1)
        a["grid"]["decode"] = {"batch": [new_batch], "context_per_seq": [new_context]}
        a["envelope"]["decode"] = {"batch_max": new_batch, "context_per_seq_max": new_context}
        require(a == b, "Producer transformation intent")
        return
    if name.startswith("analytic.dram_"):
        expected = replace_hardware_leaf(
            hw, "memory.dram.bw_bytes_per_s", hw.memory.dram.bw_bytes_per_s.value * 2
        )
        require(high.hardware_spec == expected, "Bandwidth transformation")
        if name == "analytic.dram_memory_response":
            require(
                1000 <= hw.memory.dram.bw_bytes_per_s.value <= 10_000, "Memory domain bandwidth"
            )
    elif name == "analytic.aggregate_clock":
        require(hw.memory.dram.bw_bytes_per_s.value == 1e18, "Clock domain bandwidth")
        factor = (
            high.hardware_spec.clock_domains.core.freq_hz.value
            / hw.clock_domains.core.freq_hz.value
        )
        require(factor in (2, 3, 4), "Clock transformation factor")
        expected = replace_hardware_leaf(
            hw, "clock_domains.core.freq_hz", hw.clock_domains.core.freq_hz.value * factor
        )
        require(high.hardware_spec == expected, "Clock transformation hardware")
    else:
        require(high.hardware_spec == hw and high.points == low.points, "Mode transformation")


class _ValidationPreparation:
    """Bounded job preparation for ONE synchronous report validation.

    Keys contain full current bundle, assumptions and engine bytes, not a caller's
    claimed hash. Copies keep cases independent. This never caches a response,
    domain verdict or report acceptance; discovery and replay still execute all calls.
    """

    def __init__(self):
        self._jobs = {}

    def jobs(self, bundle):
        key = canonical_json(
            [as_json(bundle), as_json(physical_assumptions()), as_json(core.engine_identity())]
        )
        if key not in self._jobs:
            prepared = jobs(bundle)
            if len(self._jobs) >= 64:
                self._jobs.pop(next(iter(self._jobs)))
            self._jobs[key] = copy.deepcopy(prepared)
        return copy.deepcopy(self._jobs[key])


def expected_jobs(cell, bundles, *, preparation=None):
    name = relation_name(cell)
    groups = [list(jobs(b) if preparation is None else preparation.jobs(b)) for b in bundles]
    if name.startswith("producer."):
        return [next(j for j in group if j.point.query.phase == "decode") for group in groups]
    if len(groups) == 2:
        return [j for pair in zip(*groups, strict=True) for j in pair]
    if name in ("analytic.repeat_bytes", "analytic.saved_replay"):
        return [j for j in groups[0] for _ in range(2)]
    return groups[0]


def premise_results(cell, state="true", reason=None, pointers=()):
    return [
        {"id": p["id"], "state": state, "reason": reason, "observation_pointers": list(pointers)}
        for p in cell["premises"]
    ]


class PremiseFalse(Exception):
    pass


def observed_premises(cell, bundles, results):
    pointers = [{"artifact_hash": b.bundle_hash, "json_pointer": ""} for b in bundles]
    name = relation_name(cell)
    if name in ("analytic.dram_memory_response", "analytic.aggregate_clock"):
        pointers.extend(
            {"artifact_hash": r.result_hash, "json_pointer": "/per_op"} for r in results[1::2]
        )
        if name == "analytic.dram_memory_response":
            applicable = all(
                o.memory_time_ps > o.compute_time_ps for r in results[1::2] for o in r.per_op
            )
        else:
            applicable = all(
                sum(o.compute_time_ps for o in r.per_op) > sum(o.memory_time_ps for o in r.per_op)
                for r in results[1::2]
            )
        if not applicable:
            return premise_results(cell, "false", "BOUND_PREMISE_FALSE", pointers)
    return premise_results(cell, pointers=pointers)


def check_relation(cell, bound_jobs, results):
    """Only retained observations: no hidden engine or producer invocation."""
    name = relation_name(cell)
    if name == "analytic.fixed_counts":
        for j, r in zip(bound_jobs, results, strict=True):
            check_counts(j, r)
    elif name == "analytic.count_rollup":
        for r in results:
            assert all(
                getattr(r.counts, f) == sum(getattr(o.counts, f) for o in r.per_op)
                for f in type(r.counts).model_fields
            ), "count_rollup"
    elif name == "analytic.attribution_sum":
        for r in results:
            check_attribution(r)
    elif name == "analytic.null_diagnostics":
        for r in results:
            check_nulls(r)
    elif name in ("analytic.repeat_bytes", "analytic.saved_replay"):
        for a, b in zip(results[::2], results[1::2], strict=True):
            assert canonical_json(a) == canonical_json(b), "nondeterministic_output"
    elif name in (
        "analytic.dram_monotone",
        "analytic.dram_memory_response",
        "analytic.aggregate_clock",
        "analytic.mode_order",
    ) or name.startswith("producer."):
        for i in range(0, len(results), 2):
            a, b = results[i : i + 2]
            if not name.startswith("producer."):
                assert a.counts == b.counts, "transformation_counts"
            if name == "analytic.dram_monotone":
                assert b.duration_ps <= a.duration_ps, "dram_monotone"
            elif name == "analytic.dram_memory_response":
                # The domain is independently established from the captured job and fixed counts.
                assert math.isclose(b.duration_ps, a.duration_ps / 2, rel_tol=1e-9, abs_tol=0), (
                    "wrong_bandwidth_field"
                )
            elif name == "analytic.aggregate_clock":
                factor = (
                    bound_jobs[i + 1].hardware.core_freq_hz / bound_jobs[i].hardware.core_freq_hz
                )
                assert math.isclose(
                    b.duration_ps, a.duration_ps / factor, rel_tol=1e-9, abs_tol=0
                ), "aggregate_clock"
            elif name == "analytic.mode_order":
                assert a.per_op == b.per_op and b.duration_ps >= a.duration_ps, "mode_order"
            else:
                assert b.duration_ps >= a.duration_ps, "producer_monotone"
                assert b.counts.matrix_ops >= a.counts.matrix_ops, "producer_matrix"
                assert b.counts.memory_read_bytes >= a.counts.memory_read_bytes, "producer_bytes"
    for j, r in zip(bound_jobs, results, strict=True):
        validate_engine_result(r, j)


def assertion_name(cell):
    return (cell["required_mutants"] or [relation_name(cell).split(".")[-1]])[0]


def exercise(recorder, cell, bundles, ledger, engine, origin=None, control=None):
    ordinal = len(recorder.ledgers[ledger])
    case = {
        "case_id": f"{ledger}:{cell['cell_id']}:{ordinal}",
        "cell_id": cell["cell_id"],
        "ordinal": ordinal,
        "stage": "discovery" if ledger == "discovery" else "replay",
        "origin_case_id": origin,
        "status": "not_run",
        "reason": "UNSTARTED",
        "inputs": [recorder.objects.bundle(b) for b in bundles],
        "results": [],
        "calls": [],
        "premise_results": (
            copy.deepcopy(control["premise_results"])
            if control is not None
            else observed_premises(cell, bundles, [])
        ),
        "assertion_id": cell["relation_id"],
        "failure_fingerprint": None,
    }
    recorder.ledgers[ledger].append(case)
    recorder.emit("case_started", case)
    try:
        validate_inputs(cell, bundles)
        name = relation_name(cell)
        if name.startswith("producer.") and ledger != "discovery":
            actual = [producer.prepare(b.intent, b.hardware_spec) for b in bundles]
            for value in actual:
                recorder.objects.bundle(value)
            if actual != bundles:
                case["failure_fingerprint"] = {
                    "assertion_id": "producer_replay_binding",
                    "observed": {
                        "results": [],
                        "producer_outputs": [b.bundle_hash for b in actual],
                    },
                }
                raise AssertionError("producer_replay_binding")
        if name == "analytic.saved_replay":
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "prepared.json"
                path.write_text(canonical_json(bundles[0]))
                loaded = load_prepared_input(path)
                assert loaded == bundles[0], "saved_replay_binding"
        if name == "analytic.input_refusal":
            invalid = as_json(bundles[0])
            invalid["points"][0]["graph"]["groups"][1]["repeat"] += 1
            case["inputs"].append(recorder.objects.add("diagnostic", invalid))
            try:
                validate_execution_bundle(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError("input_refusal")
        bound_jobs = expected_jobs(cell, bundles)
        results = [recorder.invoke(case, cell, ledger, engine, j) for j in bound_jobs]
        case["premise_results"] = (
            copy.deepcopy(control["premise_results"])
            if control is not None
            else observed_premises(cell, bundles, results)
        )
        if any(p["state"] != "true" for p in case["premise_results"]):
            raise PremiseFalse()
        check_relation(cell, bound_jobs, results)
        case.update(status="pass", reason=None)
    except PremiseFalse:
        case.update(status="skip", reason="BOUND_PREMISE_FALSE")
    except InvocationLimit:
        case.update(reason="INVOCATION_CAP")
    except EngineStopped:
        case.update(reason="ENGINE_ERROR")
    except AssertionError as exc:
        name = str(exc) or assertion_name(cell)
        case.update(
            status="fail",
            reason="ASSERTION_FAILED",
            failure_fingerprint=case["failure_fingerprint"]
            or {
                "assertion_id": name.split(":")[0],
                "observed": {"results": case["results"].copy()},
            },
        )
    except (ValueError, TypeError) as exc:
        # A semantic protocol rejection is not a target mutant assertion.
        case.update(reason="PROTOCOL_REJECTION")
        recorder.operational.append(str(exc))
        recorder.interrupted = True
    recorder.emit("case_finished", case)
    return case


@dataclass
class Discovery:
    plan: dict
    cases: list
    objects: list
    observed: dict
    interrupted: bool
    operational: list


def discover(plan, *, engine=core.run_analytic, sink=None):
    recorder = Recorder(sink=sink)
    observed = {c["cell_id"]: 0 for c in plan["cells"]}
    for cell in plan["cells"]:
        if disposition(cell):
            continue

        def body(hardware, factor=2, batch=1, context=1, *, cell=cell):
            observed[cell["cell_id"]] += 1
            case = exercise(
                recorder,
                cell,
                build_inputs(cell, hardware, factor, batch, context),
                "discovery",
                engine,
            )
            if case["status"] == "fail":
                raise AssertionError(case["failure_fingerprint"]["assertion_id"])
            if case["reason"] == "INVOCATION_CAP":
                raise InvocationLimit()
            if case["status"] == "not_run":
                raise EngineStopped()

        try:
            if plan["profile_id"].endswith("-smoke"):
                hardware = fixed_bundle(cell["modes"][0]).hardware_spec
                if relation_name(cell) == "analytic.dram_memory_response":
                    hardware = replace_hardware_leaf(hardware, "memory.dram.bw_bytes_per_s", 1000)
                body(hardware)
            else:
                strategy = hardware_specs(
                    memory_bound=relation_name(cell) == "analytic.dram_memory_response"
                )

                def generated(hardware, factor, batch, context):
                    body(hardware, factor, batch, context)

                name = relation_name(cell)
                decorated = settings(
                    max_examples=cell["budget"]["max_examples"],
                    database=None,
                    derandomize=True,
                    deadline=None,
                    phases=(Phase.generate, Phase.shrink),
                )(
                    given(
                        hardware=strategy,
                        factor=st.integers(2, 4)
                        if name == "analytic.aggregate_clock"
                        else st.just(2),
                        batch=st.integers(1, 8) if name.startswith("producer.") else st.just(1),
                        context=st.integers(1, 64) if name.startswith("producer.") else st.just(1),
                    )(generated)
                )
                decorated()
        except (AssertionError, InvocationLimit, EngineStopped):
            pass  # Cases already persist; discovery failure is never erased by replay.
        except Exception:
            recorder.interrupted = True
            recorder.operational.append(traceback.format_exc())
    return Discovery(
        copy.deepcopy(plan),
        recorder.ledgers["discovery"],
        recorder.objects.export(),
        observed,
        recorder.interrupted,
        recorder.operational,
    )


def corpus_from(cases):
    entries, seen = [], set()
    for case in cases:
        key = (case["cell_id"], tuple(case["inputs"]))
        if key not in seen:
            seen.add(key)
            entries.append(
                {
                    "cell_id": case["cell_id"],
                    "ordinal": len(entries),
                    "discovery_case_id": case["case_id"],
                    "input_hashes": case["inputs"],
                }
            )
    return {"entries": entries, "discovery_case_ids": [c["case_id"] for c in cases]}


def frozen_plan(discovery):
    plan = copy.deepcopy(discovery.plan)
    plan["selection"]["corpus_hash"] = content_hash(corpus_from(discovery.cases))
    return plan


def mutant_outcome(controls, faults, name):
    if any(c["status"] == "fail" or c["reason"] == "PROTOCOL_REJECTION" for c in controls):
        return "control_failed"
    if not controls or not all(c["status"] == "pass" for c in controls):
        return "not_run"
    if any(c["status"] == "pass" for c in faults):
        return "survived"
    if faults and all(
        c["status"] == "fail" and c["failure_fingerprint"]["assertion_id"] == name for c in faults
    ):
        return "killed"
    return "not_run"


def relations_from(plan, cases, observed):
    relations = []
    for cell in plan["cells"]:
        identity = cell["cell_id"]
        selected = {key: [c for c in cases[key] if c["cell_id"] == identity] for key in LEDGERS}
        valid = sum(
            c["status"] in ("pass", "fail")
            and bool(c["calls"])
            and all(call["state"] == "completed" for call in c["calls"])
            for c in selected["candidate"]
        )
        reason = disposition(cell)
        applicability = "applicable"
        if reason:
            status = "not_run" if reason.startswith("DEFERRED_") else "skip"
            applicability = "applicable" if status == "not_run" else "unobservable"
        elif any(
            c["status"] == "fail" for key in ("discovery", "candidate") for c in selected[key]
        ):
            status, reason = "fail", "ASSERTION_FAILED"
        elif valid < cell["budget"]["required_valid_examples"] or any(
            c["status"] != "pass" for key in ("discovery", "candidate") for c in selected[key]
        ):
            status, reason = "not_run", "INCOMPLETE_OR_UNDER_BUDGET"
        else:
            status, reason = "pass", None
        relations.append(
            {
                "cell_id": identity,
                "applicability": applicability,
                "reason": reason,
                "status": status,
                "premise_results": premise_results(
                    cell,
                    "unobservable" if applicability == "unobservable" else "true",
                    reason if applicability == "unobservable" else None,
                ),
                "actual": {
                    "observed_body_entries": observed[identity],
                    "internal_draws": None,
                    "internal_rejections": None,
                    "executed_shrink_calls": None,
                    "valid_examples": valid,
                    "engine_evaluations": {
                        key: sum(
                            call["state"] != "not_run" for c in selected[key] for call in c["calls"]
                        )
                        for key in LEDGERS
                    },
                },
                "case_ids": [
                    c["case_id"] for key in ("discovery", "candidate") for c in selected[key]
                ],
            }
        )
    return relations


def reduce_report(plan, relations, mutants, execution):
    def outcome(selected):
        ids = {r["cell_id"] for r in selected}
        relevant = [m for m in mutants if m["target_cell_id"] in ids]
        if any(r["status"] == "fail" for r in selected) or any(
            m["status"] in ("survived", "control_failed") for m in relevant
        ):
            return "failed"
        if (
            not selected
            or execution["state"] != "complete"
            or any(r["status"] != "pass" for r in selected)
            or any(m["status"] != "killed" for m in relevant)
        ):
            return "not_run"
        return "passed"

    complete = (
        execution["state"] == "complete"
        and bool(relations)
        and all(r["status"] in ("pass", "fail") for r in relations)
        and all(m["status"] != "not_run" for m in mutants)
    )
    evaluated = any(r["actual"]["valid_examples"] for r in relations)
    purposes = {c["cell_id"]: c["purpose"] for c in plan["cells"]}
    return {
        "coverage": "complete" if complete else "partial" if evaluated else "none",
        "outcome": outcome(relations),
        "purpose_outcomes": {
            p: outcome([r for r in relations if purposes[r["cell_id"]] == p])
            for p in plan["purposes"]
        },
    }


def toolchain():
    return {
        "python_version": platform.python_version(),
        "hypothesis_version": importlib.metadata.version("hypothesis"),
        "pytest_version": importlib.metadata.version("pytest"),
        "uv_lock_sha256": sha256((ROOT / "uv.lock").read_bytes()),
    }


def replay(
    discovery,
    *,
    implementation,
    engine=core.run_analytic,
    mutant_factory=mutant,
    execution_kind="illustration",
    operational=None,
    sink=None,
):
    if execution_kind == "actual_suite_run":
        require(
            engine is core.run_analytic and mutant_factory is mutant,
            "Actual execution requires the committed engines",
        )
        check_implementation(implementation, actual=True)
    plan = frozen_plan(discovery)
    corpus = corpus_from(discovery.cases)
    recorder = Recorder(
        objects=Objects(discovery.objects), interrupted=discovery.interrupted, sink=sink
    )
    recorder.ledgers["discovery"] = copy.deepcopy(discovery.cases)
    cells = {c["cell_id"]: c for c in plan["cells"]}
    for entry in corpus["entries"]:
        bundles = [
            validate_execution_bundle(recorder.objects.get(h))
            for h in entry["input_hashes"]
            if recorder.objects.values[h]["kind"] == "bundle"
        ]
        exercise(
            recorder,
            cells[entry["cell_id"]],
            bundles,
            "candidate",
            engine,
            entry["discovery_case_id"],
        )
    mutants = []
    for cell in plan["cells"]:
        for name in cell["required_mutants"]:
            control_cases, fault_cases = [], []
            faulty = mutant_factory(name)
            for entry in corpus["entries"]:
                if entry["cell_id"] != cell["cell_id"]:
                    continue
                bundles = [
                    validate_execution_bundle(recorder.objects.get(h))
                    for h in entry["input_hashes"]
                    if recorder.objects.values[h]["kind"] == "bundle"
                ]
                control_cases.append(
                    exercise(recorder, cell, bundles, "mutant", engine, entry["discovery_case_id"])
                )
                fault_cases.append(
                    exercise(
                        recorder,
                        cell,
                        bundles,
                        "mutant",
                        faulty,
                        entry["discovery_case_id"],
                        control=control_cases[-1],
                    )
                )
            status = mutant_outcome(control_cases, fault_cases, name)
            mutants.append(
                {
                    "mutant_id": name,
                    "implementation_git_commit": implementation,
                    "target_cell_id": cell["cell_id"],
                    "mode": cell["modes"][0],
                    "status": status,
                    "control_case_ids": [c["case_id"] for c in control_cases],
                    "mutant_case_ids": [c["case_id"] for c in fault_cases],
                    "rejection_assertion_id": name if status == "killed" else None,
                    "reason": None if status == "killed" else "MUTANT_" + status.upper(),
                }
            )
    relations = relations_from(plan, recorder.ledgers, discovery.observed)
    execution = {
        "state": "interrupted" if recorder.interrupted else "complete",
        "stop_reason": "INCOMPLETE_EXECUTION" if recorder.interrupted else None,
        "ledger_count": sum(len(c) for c in recorder.ledgers.values()),
    }
    result = {
        "format": FORMAT,
        "execution_kind": execution_kind,
        "input_kind": "synthetic_fixture",
        "engine": as_json(core.engine_identity()),
        "model": as_json(core.engine_identity().model),
        "implementation_git_commit": implementation,
        "assumptions": as_json(physical_assumptions()),
        "suite": {
            "id": ENTRYPOINT,
            "version": "1",
            "git_commit": implementation,
            "entrypoint": ENTRYPOINT,
            "plan_hash": content_hash(plan),
        },
        "toolchain": toolchain(),
        "discovery_plan": copy.deepcopy(discovery.plan),
        "plan": plan,
        "execution": execution,
        "corpus": corpus,
        "cases": recorder.ledgers,
        "relations": relations,
        "mutants": mutants,
        "objects": recorder.objects.export(),
        "reduction": reduce_report(plan, relations, mutants, execution),
    }
    if operational is not None:
        operational.extend(recorder.operational)
    return result


def keys(value, fields, label):
    require(isinstance(value, dict) and set(value) == set(fields.split()), label + " fields")


def integer(value, label):
    require(type(value) is int and value >= 0, label + " must be a nonnegative integer")


def validate_objects(entries):
    require(isinstance(entries, list), "Objects must be ordered")
    identities = [o.get("hash") for o in entries]
    require(identities == sorted(set(identities)), "Duplicate/unordered objects")
    store = Objects()
    for obj in entries:
        keys(obj, "hash kind value", "Object")
        kind, raw = obj["kind"], obj["value"]
        if kind == "diagnostic":
            data = base64.b64decode(raw, validate=True)
            identity = store.add(kind, data)
        else:
            require(
                kind in ("hardware", "request", "bundle", "job", "result"), "Unknown object kind"
            )
            if kind == "hardware":
                HardwareSpec.model_validate(raw)
            elif kind == "request":
                CharacterizationRequest.model_validate(raw)
            elif kind == "bundle":
                validate_execution_bundle(raw)
            elif kind == "job":
                EngineJob.model_validate(raw)
            elif kind == "result":
                EngineResult.model_validate(raw)
            identity = store.add(kind, raw)
        require(identity == obj["hash"], "Object hash mismatch")
    return store


def validate_case(case, cell, ledger, ordinal, objects, control=None, *, preparation=None):
    keys(
        case,
        "case_id cell_id ordinal stage origin_case_id status reason inputs results calls "
        "premise_results assertion_id failure_fingerprint",
        "Case",
    )
    integer(case["ordinal"], "ordinal")
    require(
        case["ordinal"] == ordinal and case["case_id"] == f"{ledger}:{cell['cell_id']}:{ordinal}",
        "Case identity/order",
    )
    require(case["stage"] == ("discovery" if ledger == "discovery" else "replay"), "Case stage")
    require(case["assertion_id"] == cell["relation_id"], "Assertion binding")
    require(case["status"] in ("pass", "fail", "skip", "not_run"), "Case status")
    require((case["reason"] is None) == (case["status"] == "pass"), "Case reason")
    bundles = [
        objects.parsed_bundle(h)
        for h in case["inputs"]
        if objects.values.get(h, {}).get("kind") == "bundle"
    ]
    require(bool(bundles), "Case missing input bundle")
    for identity in case["inputs"]:
        objects.get(identity)
    validate_inputs(cell, bundles)
    bound_jobs = expected_jobs(cell, bundles, preparation=preparation)
    require(len(case["calls"]) <= len(bound_jobs), "Unexpected engine calls")
    returned = []
    for index, call in enumerate(case["calls"]):
        keys(call, "job_hash result_hash diagnostic_hash state", "Call")
        require(call["state"] in ("completed", "error", "not_run"), "Call state")
        job = EngineJob.model_validate(objects.get(call["job_hash"], "job"))
        require(job == bound_jobs[index], "Job/input implementation binding mismatch")
        require(job.engine == core.engine_identity(), "Engine identity mismatch")
        if call["state"] == "completed":
            require(call["diagnostic_hash"] is None, "Completed diagnostic")
            result = EngineResult.model_validate(objects.get(call["result_hash"], "result"))
            require(
                result.job_hash == job.job_hash
                and result.engine == job.engine
                and result.fidelity_detail == job.fidelity_detail,
                "Result/input binding mismatch",
            )
            returned.append(result)
        else:
            require(call["result_hash"] is None, "Noncompleted result")
            diagnostic = strict_json_loads(
                base64.b64decode(objects.get(call["diagnostic_hash"], "diagnostic"), validate=True)
            )
            require(
                diagnostic["code"]
                in ("ENGINE_EXCEPTION", "INVALID_ENGINE_OUTPUT", "INVOCATION_CAP"),
                "Unknown error diagnostic",
            )
    require(
        case["results"]
        == [c["result_hash"] for c in case["calls"] if c["result_hash"] is not None],
        "Result ordering",
    )
    expected_premises = (
        control["premise_results"]
        if control is not None
        else observed_premises(cell, bundles, returned if len(returned) == len(bound_jobs) else [])
    )
    require(case["premise_results"] == expected_premises, "Case premises")
    if len(returned) == len(bound_jobs):
        try:
            if any(p["state"] != "true" for p in expected_premises):
                raise PremiseFalse()
            check_relation(cell, bound_jobs, returned)
        except PremiseFalse:
            require(
                case["status"] == "skip"
                and case["reason"] == "BOUND_PREMISE_FALSE"
                and case["failure_fingerprint"] is None,
                "False premise promoted",
            )
        except AssertionError as exc:
            expected = {
                "assertion_id": (str(exc) or assertion_name(cell)).split(":")[0],
                "observed": {"results": case["results"]},
            }
            require(
                case["status"] == "fail" and case["failure_fingerprint"] == expected,
                "Observed counterexample erased or mislabeled",
            )
        except (ValueError, TypeError):
            require(
                case["status"] == "not_run" and case["reason"] == "PROTOCOL_REJECTION",
                "Protocol error mislabeled",
            )
        else:
            require(
                case["status"] == "pass" and case["failure_fingerprint"] is None,
                "Case assertion outcome mismatch",
            )
    elif (
        relation_name(cell).startswith("producer.")
        and case["status"] == "fail"
        and not case["calls"]
    ):
        failure = case["failure_fingerprint"]
        keys(failure, "assertion_id observed", "Producer failure")
        keys(failure["observed"], "results producer_outputs", "Producer observation")
        require(
            failure["assertion_id"] == "producer_replay_binding"
            and failure["observed"]["results"] == [],
            "Producer pre-engine failure",
        )
        actual = [objects.parsed_bundle(h) for h in failure["observed"]["producer_outputs"]]
        require(
            len(actual) == len(bundles) and actual != bundles,
            "Producer counterexample missing or erased",
        )
    else:
        require(
            bool(case["calls"]) and case["calls"][-1]["state"] in ("error", "not_run"),
            "Missing calls without a recorded stop",
        )
        require(
            case["status"] == "not_run" and case["failure_fingerprint"] is None,
            "Incomplete calls cannot pass or fabricate a failure",
        )
    for bundle in bundles:
        require(
            objects.get(bundle.intent.hardware_spec_hash, "hardware")
            == as_json(bundle.hardware_spec),
            "Hardware closure",
        )
        request = request_for(bundle)
        require(
            objects.get(content_hash(request), "request") == as_json(request), "Request closure"
        )


def validate_report(
    value, *, expected_plan, expected_corpus, expected_implementation, allow_illustration=False
):
    """Authenticate a standalone report. Never execute an engine or grant eligibility."""
    r = strict_json_loads(canonical_json(value))
    keys(
        r,
        "format execution_kind input_kind engine model implementation_git_commit assumptions "
        "suite toolchain discovery_plan plan execution corpus cases relations mutants "
        "objects reduction",
        "Report",
    )
    require(r["format"] == FORMAT and r["input_kind"] == "synthetic_fixture", "Report format")
    require(r["execution_kind"] in ("actual_suite_run", "illustration"), "Execution kind")
    require(
        allow_illustration or r["execution_kind"] == "actual_suite_run",
        "Illustration is not actual",
    )
    require(r["implementation_git_commit"] == expected_implementation, "Implementation expectation")
    require(canonical_json(r["plan"]) == canonical_json(expected_plan), "Plan expectation")
    require(canonical_json(r["corpus"]) == canonical_json(expected_corpus), "Corpus expectation")
    require(
        r["engine"] == as_json(core.engine_identity()), "Engine implementation identity mismatch"
    )
    require(r["model"] == r["engine"]["model"], "Model identity mismatch")
    EngineIdentity.model_validate(r["engine"])
    verify_identity(AssumptionSet.model_validate(r["assumptions"]), "assumptions_hash")
    require(r["assumptions"] == as_json(physical_assumptions()), "Assumptions identity mismatch")
    keys(r["suite"], "id version git_commit entrypoint plan_hash", "Suite")
    keys(
        r["toolchain"],
        "python_version hypothesis_version pytest_version uv_lock_sha256",
        "Toolchain",
    )
    require(r["toolchain"] == toolchain(), "Toolchain identity mismatch")
    require(
        r["suite"]["git_commit"] == expected_implementation
        and r["suite"]["entrypoint"] == ENTRYPOINT,
        "Suite implementation binding",
    )
    require(r["suite"]["plan_hash"] == content_hash(r["plan"]), "Plan hash mismatch")
    require(
        r["plan"]["selection"]["corpus_hash"] == content_hash(r["corpus"]), "Corpus hash mismatch"
    )
    discovery_plan = copy.deepcopy(r["plan"])
    discovery_plan["selection"]["corpus_hash"] = None
    require(r["discovery_plan"] == discovery_plan, "Discovery plan changed after outcomes")
    if r["plan"]["profile_id"] == "illustration-skipped-queue":
        require(r["execution_kind"] == "illustration", "Illustration profile cannot be actual")
        expected = read_json(ROOT / "docs/reviews/U3-U0006-report-example.json")
        require(r == expected, "Illustration differs from accepted complete example")
        return r["reduction"]
    require(
        canonical_json(discovery_plan) == canonical_json(profile(r["plan"]["profile_id"])),
        "Registered profile coverage/domain changed",
    )
    require(r["suite"]["id"] == ENTRYPOINT and r["suite"]["version"] == "1", "Suite version")
    if r["execution_kind"] == "actual_suite_run":
        check_implementation(expected_implementation, actual=True)
    keys(r["execution"], "state stop_reason ledger_count", "Execution")
    require(r["execution"]["state"] in ("complete", "interrupted"), "Execution state")
    require(
        (r["execution"]["stop_reason"] is None) == (r["execution"]["state"] == "complete"),
        "Execution stop reason",
    )
    integer(r["execution"]["ledger_count"], "ledger_count")
    keys(r["cases"], "discovery candidate mutant", "Cases")
    require(
        r["execution"]["ledger_count"] == sum(len(v) for v in r["cases"].values()),
        "Missing/duplicate cases",
    )
    objects = validate_objects(r["objects"])
    preparation = _ValidationPreparation()
    cells = {c["cell_id"]: c for c in r["plan"]["cells"]}
    all_cases = {}
    raw_cases = {c["case_id"]: c for group in r["cases"].values() for c in group}
    controls_by_fault = {}
    for m in r["mutants"]:
        require(len(m["control_case_ids"]) == len(m["mutant_case_ids"]), "Mutant pair arity")
        for control_id, fault_id in zip(m["control_case_ids"], m["mutant_case_ids"], strict=True):
            require(control_id in raw_cases, "Missing mutant control")
            controls_by_fault[fault_id] = raw_cases[control_id]
    for ledger in LEDGERS:
        for index, case in enumerate(r["cases"][ledger]):
            require(case["cell_id"] in cells, "Unplanned case")
            require(case["case_id"] not in all_cases, "Duplicate case")
            validate_case(
                case,
                cells[case["cell_id"]],
                ledger,
                index,
                objects,
                controls_by_fault.get(case["case_id"]),
                preparation=preparation,
            )
            if ledger == "discovery":
                require(case["origin_case_id"] is None, "Discovery origin")
            all_cases[case["case_id"]] = case
    require(
        canonical_json(r["corpus"]) == canonical_json(corpus_from(r["cases"]["discovery"])),
        "Missing/reordered discovery cases",
    )
    entries = r["corpus"]["entries"]
    candidate = r["cases"]["candidate"]
    require(len(candidate) == len(entries), "Missing candidate case")
    for case, entry in zip(candidate, entries, strict=True):
        require(
            case["cell_id"] == entry["cell_id"]
            and case["inputs"] == entry["input_hashes"]
            and case["origin_case_id"] == entry["discovery_case_id"],
            "Replay/corpus binding",
        )
    expected_mutants, used = [], []
    for cell in cells.values():
        for name in cell["required_mutants"]:
            expected_mutants.append((cell["cell_id"], name))
    require(
        [(m["target_cell_id"], m["mutant_id"]) for m in r["mutants"]] == expected_mutants,
        "Missing/duplicate required mutant",
    )
    for m in r["mutants"]:
        keys(
            m,
            "mutant_id implementation_git_commit target_cell_id mode status control_case_ids "
            "mutant_case_ids rejection_assertion_id reason",
            "Mutant",
        )
        cell = cells[m["target_cell_id"]]
        require(
            m["implementation_git_commit"] == expected_implementation
            and m["mode"] == cell["modes"][0],
            "Mutant implementation/mode binding",
        )
        selected = [e for e in entries if e["cell_id"] == cell["cell_id"]]
        groups = []
        for key in ("control_case_ids", "mutant_case_ids"):
            ids = m[key]
            require(len(ids) == len(selected), "Missing mutant/control case")
            group = []
            for identity, entry in zip(ids, selected, strict=True):
                require(
                    identity in all_cases and identity.startswith("mutant:"), "Mutant case closure"
                )
                case = all_cases[identity]
                require(
                    case["cell_id"] == cell["cell_id"]
                    and case["inputs"] == entry["input_hashes"]
                    and case["origin_case_id"] == entry["discovery_case_id"],
                    "Mutant/control input binding",
                )
                used.append(identity)
                group.append(case)
            groups.append(group)
        status = mutant_outcome(*groups, m["mutant_id"])
        require(
            m["status"] == status
            and m["rejection_assertion_id"] == (m["mutant_id"] if status == "killed" else None),
            "Mutant discrimination mismatch",
        )
        require(
            m["reason"] == (None if status == "killed" else "MUTANT_" + status.upper()),
            "Mutant reason",
        )
    require(
        len(used) == len(set(used)) and set(used) == {c["case_id"] for c in r["cases"]["mutant"]},
        "Unassigned/shared mutant cases",
    )
    observed = {}
    require(len(r["relations"]) == len(cells), "Missing relation")
    for relation, cell in zip(r["relations"], cells.values(), strict=True):
        keys(
            relation,
            "cell_id applicability reason status premise_results actual case_ids",
            "Relation",
        )
        require(relation["cell_id"] == cell["cell_id"], "Relation ordering")
        actual = relation["actual"]
        keys(
            actual,
            "observed_body_entries internal_draws internal_rejections executed_shrink_calls "
            "valid_examples engine_evaluations",
            "Actual",
        )
        for key in ("observed_body_entries", "valid_examples"):
            integer(actual[key], key)
        for key in ("internal_draws", "internal_rejections", "executed_shrink_calls"):
            require(actual[key] is None, "Unavailable internal count invented")
        keys(actual["engine_evaluations"], "discovery candidate mutant", "Engine counts")
        for count in actual["engine_evaluations"].values():
            integer(count, "engine_evaluations")
            require(count <= cell["budget"]["max_engine_invocations"], "Invocation budget exceeded")
        observed[cell["cell_id"]] = actual["observed_body_entries"]
        require(
            observed[cell["cell_id"]]
            >= sum(c["cell_id"] == cell["cell_id"] for c in r["cases"]["discovery"]),
            "Body count understated",
        )
    require(
        r["relations"] == relations_from(r["plan"], r["cases"], observed),
        "Relation outcome/count mismatch",
    )
    require(
        r["reduction"] == reduce_report(r["plan"], r["relations"], r["mutants"], r["execution"]),
        "Coverage/outcome reduction mismatch",
    )
    used_objects = set()
    for case in all_cases.values():
        used_objects.update(case["inputs"])
        for call in case["calls"]:
            used_objects.update(
                h
                for h in (call["job_hash"], call["result_hash"], call["diagnostic_hash"])
                if h is not None
            )
        if case["failure_fingerprint"] is not None:
            used_objects.update(case["failure_fingerprint"]["observed"].get("producer_outputs", []))
    for identity in list(used_objects):
        if objects.values[identity]["kind"] == "bundle":
            bundle = objects.parsed_bundle(identity)
            used_objects.update(
                (bundle.intent.hardware_spec_hash, content_hash(request_for(bundle)))
            )
    require(used_objects == set(objects.values), "Unreferenced report objects")
    invoked = sum(
        rel["actual"]["engine_evaluations"][key] for rel in r["relations"] for key in LEDGERS
    )
    require(
        bool(candidate) and invoked > 0 or r["execution_kind"] != "actual_suite_run",
        "Empty actual-run claim",
    )
    return r["reduction"]


def write_json(path, value):
    Path(path).write_text(canonical_json(value), encoding="utf-8")


def generate(profile_id, output):
    implementation = require_committed()
    plan = profile(profile_id)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "discovery-plan.json", plan)
    started = time.time()

    def sink(kind, data):
        # Report-relevant call/object journal only; no source checkpoint or framework draws.
        with (output / "execution.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(canonical_json({"event": kind, "value": data}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    sink("phase_started", {"phase": "discovery"})
    discovery = discover(plan, sink=sink)
    write_json(output / "corpus.json", corpus_from(discovery.cases))
    plan = frozen_plan(discovery)
    write_json(output / "plan.json", plan)
    write_json(
        output / "discovery.json",
        {"cases": discovery.cases, "objects": discovery.objects, "observed": discovery.observed},
    )
    receipts, stable = [], []
    for index in (1, 2):
        sink("phase_started", {"phase": "replay", "attempt": index})
        begin = time.time()
        operational = []
        value = replay(
            discovery,
            implementation=implementation,
            execution_kind="actual_suite_run",
            operational=operational,
            sink=sink,
        )
        data = canonical_json(value)
        path = output / f"report-{index}.json"
        path.write_text(data, encoding="utf-8")
        validate_report(
            value,
            expected_plan=plan,
            expected_corpus=corpus_from(discovery.cases),
            expected_implementation=implementation,
        )
        stable.append(sha256(data))
        receipts.append(
            {
                "attempt": index,
                "report_sha256": stable[-1],
                "started_unix_s": begin,
                "elapsed_s": time.time() - begin,
                "host": platform.node(),
                "invocation": [
                    sys.executable,
                    "-m",
                    ENTRYPOINT,
                    "generate",
                    "--profile",
                    profile_id,
                    "--output",
                    str(output),
                ],
                "operational_errors": discovery.operational + operational,
                "nightly": "not_run",
                "nightly_url": None,
                "outcome": value["reduction"],
            }
        )
        write_json(output / f"receipt-{index}.json", receipts[-1])
    write_json(
        output / "receipt.json",
        {
            "implementation_git_commit": implementation,
            "elapsed_s": time.time() - started,
            "identical": stable[0] == stable[1],
            "runs": receipts,
        },
    )
    require(stable[0] == stable[1], "Qualifying replay bytes differ; both attempts retained")
    return receipts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    gen = commands.add_parser("generate")
    gen.add_argument("--profile", required=True)
    gen.add_argument("--output", type=Path, required=True)
    val = commands.add_parser("validate")
    val.add_argument("--report", type=Path, required=True)
    val.add_argument("--expected-plan", type=Path, required=True)
    val.add_argument("--expected-corpus", type=Path, required=True)
    val.add_argument("--expected-implementation", required=True)
    args = parser.parse_args(argv)
    if args.command == "generate":
        result = generate(args.profile, args.output)
    else:
        result = validate_report(
            read_json(args.report),
            expected_plan=read_json(args.expected_plan),
            expected_corpus=read_json(args.expected_corpus),
            expected_implementation=args.expected_implementation,
        )
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
