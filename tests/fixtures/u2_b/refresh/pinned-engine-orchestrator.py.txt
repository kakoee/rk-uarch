"""Run lifecycle: validate, resolve fidelity map, dispatch, aggregate, propagate badges.

Sprints 1 and 2 (P1b, P3).

    run(config, plan, workload, seed) -> RunResult
    validate_system(config, components, plan=None) -> list[str]

Pure, per rk/engine/README.md invariant 1: no file I/O, no network, no wall-clock, no
globals, no async. The component library was read before we got here — that is
`rk/components/loader.py`'s job, and it is why the descriptors arrive as an argument.

Deterministic, per invariant 2: same seed, identical bytes. At R0 nothing is random at
all, so the seed changes nothing today; it is taken and recorded anyway, so that P5's
replicated DES is a change in behaviour rather than a change in signature.

**Loud failure over silent degradation.** build-spec §2.4 forbids exactly one thing
outright: answering a question other than the one asked, without saying so. A config that
asks for a fidelity level this engine has no model for therefore raises here, naming the
prompt that lands it — R1 is P5's — rather than quietly running the level below.
Everything the models *do* run but run crudely comes back as a warning instead, because
the run is still the run that was asked for.

**Two entry points, one set of checks.** `validate_system()` is the engine's second public
function (build-spec §5, boundary 2). It answers the questions that need no workload, and
it RETURNS them rather than raising, because the S3 builder validates a system the user is
mid-edit on and a stack trace is not an answer to "you removed a GPU". Every check it
performs is the same code `run()` performs — the two differ in what they DO with the
answer, never in what the answer is, and `tests/unit/test_validate_system.py` compares
their wording to prove it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from typing import Any, Final

import numpy as np

from rk import ENGINE_VERSION
from rk.engine import registry
from rk.engine.channel_diagnostics import build_diagnostics, integrate_runtime
from rk.engine.f0 import cost as f0_cost
from rk.engine.f0 import fabric as f0_fabric
from rk.engine.f0 import links as f0_links
from rk.engine.f0 import memory as f0_memory
from rk.engine.f0 import power as f0_power
from rk.engine.f0.compute import (
    Accelerator,
    PhaseRoofline,
    UnsupportedPrecision,
    decode_roofline,
    iteration_cost,
    kv_bytes,
    prefill_roofline,
)
from rk.engine.f1 import agentic as f1_agentic
from rk.engine.f1 import serving as f1_serving
from rk.provenance import (
    Calibration,
    ComputeFidelity,
    MemoryFidelity,
    Metric,
    NetworkFidelity,
    RuntimeFidelity,
    SourcedValue,
    combine,
)
from rk.schema import (
    ComponentDescriptor,
    ComponentKind,
    ComponentRole,
    ExecutionPlan,
    FidelityMap,
    FidelityMapEntry,
    FidelityOverride,
    ParamOverride,
    RequestE2E,
    RunResult,
    RuntimeTimeline,
    RuntimeTimelineSample,
    ScalarEfficiency,
    ScopeNode,
    SloTargetVerdict,
    SloVerdict,
    SystemConfig,
    WorkloadSpec,
    effective_fidelity,
)
from rk.schema.channels import AvailableQuantity

# Imported from the submodules, not from `rk.schema`, because `rk/schema/__init__.py` does
# not re-export these three — the ADR 0015 schema PR added the shapes and not the
# re-exports. rk/engine/f0/ already reaches into `rk.schema.components` and
# `rk.schema.workloads` the same way, so this is the house style and not a workaround, but
# the omission is worth a human's eye: every other public schema name is on `rk.schema`.
# Proposed and stopped, per CLAUDE.md's lane rule — no agent edits rk/schema/ mid-task.
from rk.schema.components import SplitEfficiency
from rk.schema.execution import Precision, PrecisionFormat
from rk.schema.feasibility import (
    CandidateOutcome,
    PhysicalCheck,
    PhysicalFeasibility,
    PhysicalStatus,
    physical_status,
)
from rk.schema.power import DvfsParameters, PowerDiagnostic
from rk.schema.results import EpisodeMetrics
from rk.schema.workloads import WorkloadClass

__all__ = [
    "EngineError",
    "RequestStream",
    "UnimplementedFidelity",
    "run",
    "preflight",
    "evaluate_candidate",
    "validate_system",
]

# seed -> the arrival stream that seed produces. Re-exported from `f1.serving` so a caller
# wiring `run(..., requests=...)` has one name to import alongside `run` itself.
RequestStream = f1_serving.RequestStream


class EngineError(RuntimeError):
    """A run this engine will not perform, and why."""


class UnimplementedFidelity(EngineError):
    """The config asked for a fidelity level with no model behind it (build-spec §2.4).

    A distinct type because this is the one failure that must never be caught and
    downgraded into a warning: silently running the level below is what §2.4 forbids.
    """


# ADR 0015 §2. The library param each `PrecisionFormat` member reads its dense peak from,
# and the unit that param must be in. **ONE ENTRY PER MEMBER, AND EXACTLY THAT SET** — the
# mapping is what keeps the enum and the library in agreement, and both directions are
# asserted in tests/unit/test_precision.py.
#
# The float formats are quoted in TFLOPS and the integer ones in TOPS, because that is what
# the datasheets print; `f0.compute.INTEGER_FORMATS` carries the same split for the
# conversion side. Units live in the NAMES, per CLAUDE.md invariant 7, so the param name and
# the unit gate agree by construction.
#
# A component declares the SUBSET its datasheet actually prints. Declaring none of a format
# is not a gap to be filled with a stub — it is the hardware not having it, and a plan
# asking for it is refused by name (`compute.UnsupportedPrecision`). The A100 has no FP8
# (Hopper introduced it) and neither the A100 nor the H100 datasheet prints an FP4 row.
PEAK_PARAMS_BY_FORMAT: Final[Mapping[PrecisionFormat, tuple[str, str]]] = {
    PrecisionFormat.FP32: ("fp32_tflops", "TFLOPS"),
    PrecisionFormat.TF32: ("tf32_tflops", "TFLOPS"),
    PrecisionFormat.BF16: ("bf16_tflops", "TFLOPS"),
    PrecisionFormat.FP16: ("fp16_tflops", "TFLOPS"),
    PrecisionFormat.FP8: ("fp8_tflops", "TFLOPS"),
    PrecisionFormat.INT8: ("int8_tops", "TOPS"),
    PrecisionFormat.FP4: ("fp4_tflops", "TFLOPS"),
    PrecisionFormat.INT4: ("int4_tops", "TOPS"),
}


# Datasheet units, as the library YAMLs write them. A mismatch is caught rather than
# converted: converting is a named function (CLAUDE.md invariant 7), and a silent
# reinterpretation of GB/s as TB/s is a 1000x error that looks like a modelling choice.
#
# The S1 entries (`hbm_bw`, `hbm_capacity`, `tdp`) keep the names build-spec §2.3.1 and
# ADR 0006 fixed for them. Everything P3 adds puts the unit in the NAME as well, per
# CLAUDE.md invariant 7, so the two checks agree by construction rather than by care.
#
# THE PER-PRECISION PEAKS ARE NOT LISTED BY HAND. They are spliced in below from
# `PEAK_PARAMS_BY_FORMAT`, which is keyed on `PrecisionFormat` itself — so the whitelist is
# TOTAL over the enum by construction rather than by care, and a member added to the schema
# cannot be reachable by a plan and missing from the unit gate at the same time.
# tests/unit/test_precision.py asserts the round trip in both directions (ADR 0015 §7.6
# item 2 — which is also why there is no `fp64_tflops`: `PrecisionFormat` has no FP64
# member, so a declared fp64 peak would be loaded, unit-checked and then unreachable by any
# plan. A dead number in a library whose whole point is that numbers are accountable.
# Adding FP64 is a schema PR, not a library edit.)
_EXPECTED_UNITS = {
    "hbm_bw": "TB/s",
    "hbm_capacity": "GB",
    "tdp": "W",
    "usd_per_hr": "USD/hr",
    # ScalarEfficiency's one term, and SplitEfficiency's two. All three are the same
    # dimensionless realized-vs-peak ratio; they differ in WHICH roof they multiply, which
    # is a fact about the model and not about the unit (ADR 0015 §3).
    "execution_model.value": "ratio",
    "execution_model.compute": "ratio",
    "execution_model.memory": "ratio",
    # memory tiers
    "capacity_gb": "GB",
    "bw_gb_per_s": "GB/s",
    "latency_ns": "ns",
    "added_latency_ns": "ns",
    # links
    "latency_us": "us",
    # fabric
    "port_bw_gb_per_s": "GB/s",
    "port_latency_us": "us",
    "nodes_per_switch": "count",
    "oversubscription_ratio": "ratio",
    # rack: limits and economics
    "power_envelope_kw": "kW",
    "cooling_cap_kw": "kW",
    "power_overhead_fraction": "ratio",
    "capex_usd": "USD",
    "amortization_years": "yr",
    "usd_per_kwh": "USD/kWh",
    "utilization": "ratio",
    # one entry per PrecisionFormat member — see the note above the dict
    **{param: unit for param, unit in PEAK_PARAMS_BY_FORMAT.values()},
}

# **CONDITIONAL SINCE P5, AND NEVER REMOVED.** ADR 0003 §9 said "P5 removes the p50==p99
# warning" and build-spec §2.3.3 said "until the R1 DES lands in P5"; both are corrected in
# place, and the correction is that P5 makes this CONDITIONAL on the effective runtime
# level. An R0 run still has no distribution after P5 — R1 is a rung added beside R0, not
# one that replaces it (build-spec §2.3.2 implements both) — so an R0 run still leads with
# this sentence. Only an R1 run, which has real percentiles, may omit it.
_P50_P99_WARNING = (
    "p50 and p99 are identical because runtime fidelity is R0 (analytical): there is no "
    "distribution to take percentiles of. Select runtime R1 for the DES, which produces "
    "one (P5)."
)

# The R1 counterpart. It leads an R1 run's warnings for the same reason the R0 one leads
# an R0 run's: the single most misreadable thing about the number directly above it. A p99
# out of a DES is an ESTIMATE of a p99 — it came from finitely many seeded arrivals — and
# a reader who takes it for a measured tail has been misled by us, not by the model.
_R1_PERCENTILE_ESTIMATE_WARNING = (
    "these percentiles come from the R1 discrete-event simulation over {replications} "
    "seeded replication(s); the first simulated replication completed {requests} "
    "request(s): A P99 FROM THIS ENGINE IS AN "
    "ESTIMATE OF A P99, not a measured tail. {interval} The scheduler modelled is FCFS "
    "admission with continuous batching, prefill-priority steps and largest-KV preemption; "
    "speculative decoding, chunked prefill, prefix reuse and prefill/decode disaggregation "
    "are not modelled (docs/decisions/deferred.md)."
)
_R1_NO_INTERVAL = (
    "replications=1, so ci95_low and ci95_high are null on every metric — one draw has no "
    "sampling distribution and an interval computed from it would claim a replication "
    "study nobody ran. Raise WorkloadSpec.replications to get one."
)
_R1_INTERVAL_IS_NORMAL = (
    "The reported interval is a NORMAL approximation across those replications and is "
    "therefore optimistic at this count — a t-interval would be wider. "
    "It describes seeded simulation variation, not hardware uncertainty or model accuracy."
)

# P5 item 3. Emitted on a synthetic run and NEVER on a trace-driven one, because a trace's
# arrivals are real recorded timestamps and warning about them would be false. The gate is
# `workload.generator is not None`, which `WorkloadSpec._exactly_one_request_source`
# already makes exclusive with `trace_ref` — no new flag was needed to tell the two apart.
#
# BOTH HALVES ARE NAMED, deliberately. An unbadged distributional claim under a headline
# number is the same defect as an unbadged metric one level up, and the tail is thin for
# two independent reasons: nobody declared the arrival process, and the token counts do not
# vary at all.
_SYNTHETIC_STREAM_WARNING = (
    "the arrival stream is SYNTHETIC, so the tail above is thinner than a real one, for "
    "two reasons that compound. (1) The arrival process is a Poisson draw at "
    "{rate} req/s — `SyntheticGenerator` declares a rate and no process, so the "
    "distribution behind this p99 is the generator's choice and not the workload's "
    "declaration. (2) prompt_tokens={prompt} and output_tokens={output} are FIXED for "
    "every request, so arrival timing is the ONLY source of spread: a real workload's "
    "spread in prompt length and generation length is absent, and both lengthen tails. "
    "Compare this p99 against a trace-driven run before treating it as a tail estimate."
)

# ADR 0003 §7.4's wording, verbatim, for the case it still describes: network STUB, where
# collectives really are free. At N0 the collective is priced and this warning is replaced
# by one that says what it cost and out of what numbers.
_TP_WARNING = (
    "collective cost is not modelled at C0 — tp>1 throughput is an UPPER BOUND. "
    "N0 link and fabric models land in P3 (sprint 2)."
)

# ADR 0015 §3 and kernel-efficiency.md §10.4. Every entry in the library is a
# `ScalarEfficiency` and will be until someone measures an achieved-vs-spec HBM bandwidth
# figure, so this fires on every run in the repo today — which is the point. Without it the
# split ships complete, tested and silently inert, and 100% of runs go on dividing by raw
# datasheet bandwidth: an undeclared, unbadged claim that real HBM achieves 100% of spec,
# which nothing does.
#
# Deliberately the same shape as the tdp warning below ("declare no tdp and contribute 0 W
# ... That is an omission, not a measurement of zero"), because it is the same class of
# thing: a 1.0 nobody chose, wearing the clothes of a 1.0 somebody measured.
#
# THE SECOND SENTENCE STATES A REASON AND THE REASON HAS TO BE THE TRUE ONE. Until
# 2026-09-18 it read "nothing in the library does yet, because nobody has measured one"
# while `rk/components/loader.py` refused `kind: split_efficiency` outright — so the true
# reason was that the entry would not load, and a reader arriving with a measurement in
# hand would have been sent to look for evidence rather than at a closed parser. P14 S3
# lane A finding F1 opened the parser; this sentence now says where a measurement goes.
_MEMORY_ROOF_UNSCALED_WARNING = (
    "{ids} carry a scalar_efficiency execution model, which scales the COMPUTE roof only "
    "(kernel-efficiency.md §3) — so the memory roof ran at 100% of datasheet bandwidth. "
    "That is an omission, not a measurement of 1.0: no real HBM achieves spec. A "
    "split_efficiency entry declares a memory term and badges it, and the library loader "
    "builds one; nothing in the library declares one yet, because nobody has measured an "
    "achieved-vs-spec HBM bandwidth figure (ADR 0015 §3 forbids inventing one to close an "
    "oracle gap)."
)

# P3b task 5. Every number in this repository's documents, screenshots and fixtures was
# produced at fp16/fp16, so a reader comparing a run against them needs to know which they
# are looking at. Names BOTH formats even when only one moved, because "fp8" alone does not
# say whether the KV cache came with it.
_NON_FP16_PRECISION_WARNING = (
    "this run used precision compute={compute}, kv_cache={kv_cache}, and NOT the fp16/fp16 "
    "that every number in this repo's documents, screenshots and fixtures was produced at. "
    "Weights and the compute roof are sized at {compute}; the KV cache, its bandwidth and "
    "the M0 capacity gate at {kv_cache}. Compare against a published rk-sim figure only if "
    "it was produced at the same two formats."
)

_MEMORY_NETWORK_STUB_WARNING = (
    "memory and network ran at STUB: no KV-capacity check, no link or fabric cost. "
    "Weights and KV are assumed to fit, and every transfer between devices is free. "
    "M0 and N0 are built (P3) — declare them to use them."
)

# Tie-break order when two links declare the same bandwidth, so the choice is
# deterministic (rk/engine/README.md invariant 2) rather than dependent on the order the
# filesystem yielded the YAMLs in. On-package first, then scale-up, then the host bus.
_LINK_TIE_BREAK = (
    ComponentRole.APU_UNIFIED,
    ComponentRole.NVLINK_C2C,
    ComponentRole.UALINK,
    ComponentRole.PCIE,
)


@dataclass(frozen=True)
class _Instance:
    """One (component, count) slot in the scope tree, with its descriptor resolved.

    `fidelity` is the EFFECTIVE map for this component — its own override where set,
    the system default elsewhere (ADR 0011 §1). Everything downstream reads this rather
    than `config.fidelity`, so "what level did this component run at" has one answer.

    `override` is the raw override, kept alongside the resolved map because the engine owes
    two different behaviours to the same unrunnable level: a system DEFAULT a component
    cannot honour degrades to STUB with a warning, an explicit OVERRIDE raises. Without
    this field the resolved map cannot tell the two apart. See rk/engine/registry.py.
    """

    component_id: str
    count: int
    descriptor: ComponentDescriptor
    fidelity: FidelityMap
    override: FidelityOverride | None

    def asked_for(self, axis: str) -> bool:
        """Did the user set this axis on THIS component, rather than inherit the default?"""
        return self.override is not None and getattr(self.override, axis) is not None


@dataclass(frozen=True)
class _AxisOutcome:
    """What actually ran for one component on one axis, and why if it is not what was asked.

    `level` is what the fidelity map row reports. `degraded_from` is set only when the
    system default asked for something this component's kind cannot run — the case that
    becomes a warning rather than an error.
    """

    level: str
    degraded_from: str | None = None
    reason: str | None = None
    # True when the component's KIND has no model on this axis at any level (a link does
    # not compute); False when the kind has one and this component lacks the params it
    # reads. The first is structural and uninteresting, the second is actionable.
    structural: bool = False


# --------------------------------------------------------------------------------------
# 1 · validate — the checks, each with exactly one implementation
# --------------------------------------------------------------------------------------


def _missing_component_ids(
    config: SystemConfig, components: Mapping[str, ComponentDescriptor]
) -> list[str]:
    """Component ids the config references and the library does not hold."""
    return sorted({cid for cid in config.component_ids() if cid not in components})


def _missing_components_message(config: SystemConfig, missing: list[str]) -> str:
    return (
        f"system {config.id!r} references component(s) {missing} that are not in the "
        f"loaded library. Ids come from the library YAMLs; check the spelling or the "
        f"library path."
    )


def _flatten(
    config: SystemConfig, components: Mapping[str, ComponentDescriptor]
) -> list[_Instance]:
    """Every component instance in the tree, depth-first, in declaration order.

    Counts for one id are summed, so a component slotted into two nodes is one entry —
    the fidelity map has one row per component, not one per slot.
    """
    counts: dict[str, int] = {}
    overrides: dict[str, FidelityOverride | None] = {}
    params: dict[str, tuple[ParamOverride, ...]] = {}

    def walk(node: ScopeNode) -> None:
        for slot in node.components:
            counts[slot.component_id] = counts.get(slot.component_id, 0) + slot.count
            # Safe to overwrite: SystemConfig._one_override_per_component_id has already
            # refused any config where two slots of one id disagree, so every write here
            # writes the same value. Since ADR 0026 that rule covers `params` too.
            overrides[slot.component_id] = slot.fidelity
            params[slot.component_id] = slot.params
        for child in node.children:
            walk(child)

    walk(config.root)

    missing = _missing_component_ids(config, components)
    if missing:
        raise EngineError(_missing_components_message(config, missing))
    return [
        _Instance(
            cid,
            count,
            _with_param_overrides(components[cid], params[cid]),
            effective_fidelity(config.fidelity, overrides[cid]),
            overrides[cid],
        )
        for cid, count in counts.items()
    ]


# Matches USER_SOURCE in web/src/lib/params.ts verbatim, so a value edited in the browser
# and the same value arriving through the API read identically wherever a source is shown.
_USER_EDIT_SOURCE: Final = "user — typed in the Builder inspector, not sourced"

# ADR 0027's rule, applied to `run()`'s warnings rather than only to `validate_system()`'s
# — its own §4 question 4, and P14 S3 lane A finding F2.
#
# WHY A SENTINEL AND NOT THE BADGE ITSELF. The sentences that quote a latency are built in
# `_dispatch_and_aggregate` and `_warn_about_the_slo`, and the latency badge is not known
# until `run()` has the aggregate, the network view and (at R1) the serving stack — worst-of
# over all of them. A sentence that named a grade computed from a SUBSET of those
# contributors would print a badge STRONGER than the metric's, which is invariant 3 broken
# by the fix for invariant 2 — the exact defect ADR 0027 records itself nearly shipping.
#
# So the sentence leaves a slot and `run()` fills it once, from the same `latency_badge`
# the Metric carries. One value, two surfaces, no arithmetic in between.
# `tests/unit/test_engine_prose_provenance.py` asserts no slot ever survives into a
# RunResult and that the grade in the prose is the grade on the metric.
_LATENCY_BADGE_SLOT: Final = "\x00latency-badge\x00"

# The reconciliation clause a STUB-grade figure owes the reader, in the shape
# `EnvelopeViolation.as_warning` established: at `stub` the metric card renders an em dash
# reading "read it as absent", so a sentence printing the figure to one decimal with no
# grade tells the reader the opposite thing about the same number.
_LATENCY_STUB_CLAUSE: Final = (
    " Those latencies are STUB-grade: they are the same figures the latency metrics "
    "report, and where a metric card shows one the card reads it as absent."
)
_LATENCY_STUB_SLOT: Final = "\x00latency-stub-clause\x00"


def _stamp_latency_provenance(warnings: list[str], badge: Calibration) -> None:
    """Fill every latency-grade slot with the badge the latency metrics actually carry.

    Called once in `run()`, after `latency_badge` exists and before the warnings are
    frozen onto the result. Mutates in place because the caller's list is the one that
    ships.
    """
    clause = _LATENCY_STUB_CLAUSE if badge is Calibration.STUB else ""
    warnings[:] = [
        warning.replace(_LATENCY_BADGE_SLOT, badge.value).replace(
            _LATENCY_STUB_SLOT, clause
        )
        for warning in warnings
    ]


def _stamp_slo_actuals(verdict: SloVerdict, metrics: Mapping[str, Metric]) -> SloVerdict:
    """Give every target the METRIC it judged, in place of a provisional copy of its value.

    The companion of `_stamp_latency_provenance` and called beside it, for the same reason:
    `_warn_about_the_slo` runs before the latency badge is combined, so it builds each
    `actual` as a STUB-badged value and this replaces it with the `RunResult` field
    `metric_field` names. After this, the verdict's number and the metric card's number are
    one object — same value, unit, badge, contributors and interval — so the Results SLO
    panel cannot contradict the card it sits beside. ADR 0036 §1.

    Rebuilt through the constructor rather than `model_copy(update=...)`, so the unit check
    on `SloTargetVerdict` actually runs on the stamped value instead of being bypassed.

    A verdict naming a field this run did not produce is an `EngineError` and not a silent
    pass: leaving the provisional in place would ship a STUB-badged number that looks like a
    metric and is not one.
    """
    if not verdict.targets:
        return verdict
    stamped: list[SloTargetVerdict] = []
    for target in verdict.targets:
        metric = metrics.get(target.metric_field)
        if metric is None:
            raise EngineError(
                f"the SLO verdict names {target.metric_field!r}, which this run did not "
                f"produce as a latency metric ({', '.join(sorted(metrics))}). A verdict "
                f"whose number cannot be traced to the metric it judged is not a verdict."
            )
        stamped.append(
            SloTargetVerdict(
                metric_field=target.metric_field,
                target_ms=target.target_ms,
                actual=metric,
                met=target.met,
            )
        )
    return SloVerdict(
        targets=tuple(stamped),
        met=verdict.met,
        certifiable=verdict.certifiable,
        caveat=verdict.caveat,
    )


# The DES's scheduler when no component in the system describes it. Entered into badge
# propagation like `f0.fabric.contention_scalar`, and STUB rather than ESTIMATED because
# unlike the fabric scalar there is no model here to grade — R1 went on simulating a
# vLLM-shaped continuous-batching scheduler off `plan.batching` and `plan.kv` with nothing
# in the config claiming that is what the system runs. P14 S3 lane A finding F12, ADR 0028.
_UNNAMED_SCHEDULER_CONTRIBUTOR: Final = "f1.serving.unnamed_scheduler"
_UNNAMED_SCHEDULER_BADGE: Final[Calibration] = Calibration.STUB

# The second element of the load balancer's seed pair (`_one_replicas_share`). Its only job
# is to be a constant nothing else uses, so the balancer's draws cannot coincide with the
# arrival stream's own. Changing it reshuffles which arrivals land on the simulated replica
# and therefore moves every multi-replica R1 number — it is an ENGINE_VERSION bump, not a
# tuning knob.
_LOAD_BALANCER_SEED_STREAM: Final = 0x1B_A1_A1_CE


def _with_param_overrides(
    descriptor: ComponentDescriptor, overrides: tuple[ParamOverride, ...]
) -> ComponentDescriptor:
    """Substitute a user's typed values into a library descriptor. ADR 0026.

    **This is the only place it happens, and it is inside the engine on purpose.** The HTTP
    layer would be the easy place to put it, and then `rk run`, `rk calibrate`, `rk oracle`
    and P9a's sweep — every caller that never touches a browser — would reach the models
    with the library's badge on a number the library did not supply. Invariant 3 has to be
    enforced where every caller passes.

    The badge is DERIVED, never carried: `combine([ESTIMATED, original.provenance])`. Being
    worst-of, that flips a `measured` or `spec_derived` value to `estimated` and leaves a
    `stub` a stub — typing over no evidence creates none. `ParamOverride` has no provenance
    field, so there is nothing here that could say otherwise.

    An override naming a parameter the component does not declare is an ERROR, not a new
    parameter. The library entry is what says which numbers a part has; accepting an unknown
    name would let a typo reach a model as silence (S2's rung 2), and would let a user
    invent a field the engine reads by accident.
    """
    if not overrides:
        return descriptor
    unknown = sorted({o.name for o in overrides} - set(descriptor.params))
    if unknown:
        raise EngineError(
            f"component {descriptor.id!r}: parameter override(s) {unknown} name parameters "
            f"this component does not declare. It has: "
            f"{', '.join(sorted(descriptor.params))}. An override edits a number the part "
            f"has; it cannot add one, because nothing downstream would read it."
        )
    edited = dict(descriptor.params)
    for override in overrides:
        original = edited[override.name]
        provenance = combine([Calibration.ESTIMATED, original.provenance])
        edited[override.name] = SourcedValue(
            value=override.value,
            unit=override.unit,
            provenance=provenance,
            # A STUB carries no source, and `SourcedValue` refuses one: "a stub is the
            # absence of evidence". Typing over an unsourced number leaves it unsourced,
            # which is the same answer lane B's userEditedParam gives in the browser.
            source=None if provenance is Calibration.STUB else _USER_EDIT_SOURCE,
            date=None,
        )
    return descriptor.model_copy(update={"params": edited})


def _hostless_system_problems(
    config: SystemConfig, components: Mapping[str, ComponentDescriptor]
) -> list[str]:
    """Accelerators with no host CPU anywhere in the tree — silent until P14 S3 lane A F13.

    Check 7's own example is "32 accelerators and no CPU". Adding two Xeons to that system
    changed nothing measurable: the same `ttft_p50_ms` to four decimals, the same badge,
    a byte-identical contributor list, and no warning appearing or disappearing. That is
    DEFENSIBLE on the modelling side — CPU analytical service time is unbuilt, so a host
    that is present contributes nothing either — and it is exactly why the absence has to
    be said rather than inferred from silence. A user composing a rack of bare GPUs in the
    Builder gets a full latency distribution and a throughput off a machine that cannot
    boot, and the nearest existing sentence ("CPU analytical service time … is still
    unbuilt") is attached to components the system HAS, so it never fires for a system
    that has none.

    **It is a note, not an error, and the wording keeps that straight.** No number here is
    wrong by a stated amount; what is missing is a part every real deployment has, whose
    cost this prototype does not model. Naming it as a config error would claim a
    quantitative consequence nobody has measured — ADR 0019's line, applied to a
    composition fact instead of to a stub capacity.

    Structural, so `validate_system()` says it while the user is still editing, from the
    same computation the run uses.
    """
    roles: set[ComponentRole] = set()

    def walk(node: ScopeNode) -> None:
        for slot in node.components:
            descriptor = components.get(slot.component_id)
            if descriptor is not None:
                roles.add(descriptor.role)
        for child in node.children:
            walk(child)

    walk(config.root)
    if ComponentRole.ACCELERATOR not in roles or ComponentRole.CPU in roles:
        return []
    return [
        "this system slots accelerators and NO host CPU anywhere in the tree. Every "
        "number here is unchanged by that, which is the point of saying it: CPU "
        "analytical service time is unbuilt, so a host contributes nothing to these "
        "metrics whether or not one is present — a rack of bare accelerators and the "
        "same rack with two CPUs produce byte-identical results. Read the numbers as "
        "the accelerators' own, not as a machine's. Tokenisation, sampling, request "
        "handling and the scheduler's own work run on a host this configuration does "
        "not have, and an agentic workload's tool time is host time (P8a)."
    ]


def _link_placement_problems(
    config: SystemConfig, components: Mapping[str, ComponentDescriptor]
) -> list[str]:
    """Links slotted where no accelerator is — which N0 will price a collective over anyway.

    P14 S3 lane B, finding F2. A system with 32 H100s in `node.0` and `link.ualink.v1` in
    `node.1` had `node.0`'s tp=8 collectives priced over the UALink, and nothing anywhere
    said the link and the accelerators were in different nodes: TPOT 8.151 ms against
    7.071 ms with NVLink in the same node and 5.625 ms with no link at all.

    **This warns; it does not re-pick the link.** `_network_view` chooses the fastest
    declared link system-wide, and that rule is load-bearing — it is what makes P3
    acceptance test 2 a property ("removing a link can only ever leave a slower-or-equal
    one") rather than a coincidence. Restricting the choice to co-located links would need
    a model of what is connected to what, and topology inference is out of scope
    (build-spec §1.3, and P4b's guardrails name it explicitly). So the engine keeps
    answering the question it can answer and says what the answer rests on — ADR 0019's
    rule, and the same move ADR 0025 made for the capacity ceiling.

    **The direction is not fixed, which is why the sentence states the placement rather
    than a correction.** Borrowing a SLOWER link than the accelerators really have makes
    the run pessimistic; borrowing a faster one makes it optimistic. In the reported case
    the borrowed UALink was slower than a co-located NVLink would have been. A reader
    cannot adjust for it without knowing which, so the warning names the scopes and lets
    them see it.

    Structural, so it needs no workload and no plan: `validate_system()` emits it while the
    user is still editing, which is the half lane B asked for — P4b forbids the browser
    from adding a check of its own.
    """
    accelerator_scopes: dict[str, list[str]] = {}
    link_scopes: dict[str, list[str]] = {}

    def walk(node: ScopeNode) -> None:
        for slot in node.components:
            descriptor = components.get(slot.component_id)
            if descriptor is None:
                continue  # `_missing_component_ids` already reports this
            if descriptor.role is ComponentRole.ACCELERATOR:
                accelerator_scopes.setdefault(slot.component_id, []).append(node.id)
            elif descriptor.kind is ComponentKind.LINK:
                link_scopes.setdefault(slot.component_id, []).append(node.id)
        for child in node.children:
            walk(child)

    walk(config.root)
    if not accelerator_scopes or not link_scopes:
        return []

    holding_accelerators = {scope for scopes in accelerator_scopes.values() for scope in scopes}
    problems: list[str] = []
    for link_id, scopes in sorted(link_scopes.items()):
        if set(scopes) & holding_accelerators:
            continue
        where = ", ".join(sorted(set(scopes)))
        accelerators = ", ".join(sorted(holding_accelerators))
        problems.append(
            f"{link_id} is slotted in {where}, which holds no accelerator; the "
            f"accelerators are in {accelerators}. At N0 the engine prices tensor-parallel "
            f"collectives over the FASTEST declared link in the system and has no model of "
            f"what is connected to what (topology inference is out of scope, build-spec "
            f"§1.3), so this link can be charged for a collective it could not carry. The "
            f"direction is not fixed: a borrowed link slower than the real one makes the "
            f"run pessimistic, a faster one makes it optimistic. Slot a link in the node "
            f"that holds the accelerators, or read any tp>1 latency here as resting on a "
            f"link placement the engine did not check."
        )
    return problems


def _scope_role_problems(config: SystemConfig) -> list[str]:
    """Structural problems in the scope tree that `ScopeNode`'s own validator cannot see.

    `ScopeNode` already refuses a role that is neither `node` nor `rack`. What it cannot
    check is NESTING, because a node validates without knowing its parent:

      * a rack inside a node inverts the hierarchy, and `power_kw_per_rack` would then sum
        a scope that contains racks;
      * a root that is not a rack means the metric named `power_kw_per_rack` is reporting
        some other scope's draw, which the run already warns about and which the builder
        should be able to see before running anything.

    ADR 0011 §4 is why there is no third case: `datacenter`/`site` does not exist, the tree
    tops out at one rack, and a builder that accepted three would emit four confident
    metrics over a topology with no model behind it.
    """
    problems: list[str] = []
    if config.root.role is not ComponentRole.RACK:
        problems.append(
            f"power_kw_per_rack sums the whole scope tree, but its root {config.root.id!r} "
            f"is a {config.root.role.value}, not a rack. The number is that scope's draw; "
            f"the field name says rack. ADR 0011 §4 tops the tree out at one rack, which "
            f"is also where it should start."
        )

    def walk(node: ScopeNode, ancestors: tuple[str, ...]) -> None:
        for child in node.children:
            if child.role is ComponentRole.RACK and node.role is ComponentRole.NODE:
                problems.append(
                    f"rack {child.id!r} is nested inside node {node.id!r}, which inverts "
                    f"the hierarchy: a node lives in a rack, never the other way round. "
                    f"Every scope-level number computed over {node.id!r} would then be "
                    f"summing racks."
                )
            walk(child, (*ancestors, node.id))

    walk(config.root, ())
    return problems


def _replica_shape(plan: ExecutionPlan, accelerator_count: int) -> tuple[int, int, str | None]:
    """(devices per replica, replicas, message) for a plan against an accelerator count.

    THE ONE COMPUTATION, TWO BEHAVIOURS case build-spec §5 boundary 2 names explicitly.
    `run()` raises on the message; `validate_system()` returns it. Reducing a node below
    what `tp` asks for is the single most likely edit a user makes in the builder, and a
    mid-run stack trace is not an answer to it — but a run that cannot shard the model
    across devices that are not there has no number to report either, so it still raises.

    `replicas` is 0 when the plan does not fit; callers that raise never read it, and
    callers that warn must not divide by it.
    """
    devices_per_replica = plan.parallelism.tp * plan.parallelism.pp
    if accelerator_count < devices_per_replica:
        return (
            devices_per_replica,
            0,
            f"the plan asks for tp={plan.parallelism.tp} x pp={plan.parallelism.pp} = "
            f"{devices_per_replica} accelerators per replica, but the system has "
            f"{accelerator_count}. A model cannot be sharded across devices that are not "
            f"there.",
        )
    return devices_per_replica, accelerator_count // devices_per_replica, None


def _check_fidelity_is_implemented(
    fidelity: FidelityMap, where: str, *, compute_stub_ok: bool = False
) -> None:
    """Refuse a level this ENGINE has no model for, naming the prompt that lands it.

    This is gate 1 of the two rk/engine/registry.py's docstring describes: *is this level
    built at all, today*. `rk/schema/fidelity.py` already gated these against what the
    PROTOTYPE will implement; this is the narrower question the engine alone can answer,
    and the gap between the two is exactly where a silent degradation would hide.

    Since P3 that gap is one level wide: R1. Which level is unbuilt is no longer written
    out here — `registry.unbuilt()` answers it from the same table that says what IS built,
    so the two cannot drift (ADR 0003 §9).

    Takes a resolved `FidelityMap` rather than the config, because since ADR 0011 §1 there
    is no single answer for a system: the default and every component's override each have
    to pass this gate. `where` names whose levels these are, so the refusal points at the
    component the user actually set rather than at the system in general.

    `compute_stub_ok` is the one place the two callers genuinely differ. As a SYSTEM
    default, compute STUB means no device runs a model and the run has no throughput to
    report, so it stays refused. As a per-component OVERRIDE it is the entire point of the
    feature — "claim nothing about this part" — so it is honoured; the case where it leaves
    the system with no accelerator at all is caught in `run()`, which says exactly that.
    """
    if fidelity.compute is ComputeFidelity.STUB and not compute_stub_ok:
        raise UnimplementedFidelity(
            f"{where}: compute fidelity 'STUB' as a system default means no device runs a "
            f"model, and a run with no compute model has no throughput to report. Ask for "
            f"C0, or stub individual components with a per-instance override (ADR 0011 §1)."
        )
    for axis in registry.AXES:
        level = registry.resolve_axis(fidelity, axis)
        if level in registry.implemented_in_table(axis):
            continue
        unbuilt = registry.unbuilt(axis, level)
        if unbuilt is not None:
            raise UnimplementedFidelity(
                f"{where}: {axis} fidelity {level!r} is not implemented yet — "
                f"{unbuilt.lands_in}. It passes schema validation because the prototype "
                f"will implement it, but no model exists behind it today, and reporting a "
                f"cruder answer under its name is the one thing build-spec §2.4 forbids "
                f"outright."
            )
        raise UnimplementedFidelity(  # pragma: no cover — schema.fidelity refuses these first
            f"{where}: {axis} fidelity {level!r} has no model in this engine and no row in "
            f"rk/engine/registry.py."
        )


def _axis_outcome(instance: _Instance, axis: str) -> _AxisOutcome:
    """What runs for one component on one axis — gate 2 of registry.py's two.

    Raises `UnimplementedFidelity` when the user OVERRODE this axis on this component and
    the component cannot honour it. Degrades to STUB, with a reason, when the level came
    from the system DEFAULT. The asymmetry is registry.py's central decision and the
    reasoning lives there.
    """
    asked = registry.resolve_axis(instance.fidelity, axis)
    stub = registry.stub_level(axis)
    if asked == stub:
        return _AxisOutcome(level=stub)

    kind = instance.descriptor.kind
    entry = registry.lookup(kind, axis, asked)
    if entry is None or not entry.implemented:
        reason = (
            f"no {axis} model is registered for kind {kind.value!r} at any level: "
            f"{', '.join(sorted(registry.registered_levels(kind, axis)))}"
        )
        return _refuse_or_degrade(instance, axis, asked, stub, reason, structural=True)

    absent = registry.missing_params(entry, instance.descriptor)
    if absent:
        reason = (
            f"the {axis} model at {asked} reads {list(entry.requires)} and "
            f"{instance.component_id!r} declares none of {list(absent)}"
        )
        return _refuse_or_degrade(instance, axis, asked, stub, reason)

    return _AxisOutcome(level=asked)


def _refuse_or_degrade(
    instance: _Instance,
    axis: str,
    asked: str,
    stub: str,
    reason: str,
    *,
    structural: bool = False,
) -> _AxisOutcome:
    if instance.asked_for(axis):
        raise UnimplementedFidelity(
            f"component {instance.component_id!r}: the config overrides its {axis} fidelity "
            f"to {asked!r}, and this engine cannot run that on it — {reason}. An override "
            f"names one part and one level, so answering with a different one quietly is "
            f"the silent degradation build-spec §2.4 forbids. Ask for STUB to claim nothing "
            f"about this part, or drop the override and let the system default apply."
        )
    return _AxisOutcome(
        level=stub, degraded_from=asked, reason=reason, structural=structural
    )


def _sourced(instance: _Instance, param: str) -> SourcedValue:
    """One param off a component, unit-checked, or a loud refusal."""
    value = instance.descriptor.params.get(param)
    if value is None:
        raise EngineError(
            f"component {instance.component_id!r} declares no {param!r} parameter, which "
            f"the C0 roofline needs. Add it to the library YAML as a SourcedValue — or as "
            f"provenance: stub with source: null if it cannot be sourced."
        )
    return _require_unit(instance.component_id, param, value)


def _require_unit(component_id: str, param: str, value: SourcedValue) -> SourcedValue:
    expected = _EXPECTED_UNITS[param]
    if value.unit != expected:
        raise EngineError(
            f"component {component_id!r}: {param} is in {value.unit!r}, expected "
            f"{expected!r}. Units live in names and converting is a named function "
            f"(CLAUDE.md invariant 7) — this engine will not guess a conversion."
        )
    return value


def _peaks(instance: _Instance) -> dict[PrecisionFormat, SourcedValue]:
    """Every per-precision peak this component declares, unit-checked, keyed by format.

    **Every declared peak is unit-checked, not just the one the plan selected.** An
    `fp8_tflops` mislabelled "TOPS" is wrong whether or not today's plan happens to read
    it, and catching it only on the run that selects it makes a library defect look like a
    property of the plan.

    A component declares a SUBSET. Absence is a real answer about real hardware — the A100
    has no FP8 row on its datasheet because Ampere has no FP8 — so this returns what is
    there and `Accelerator.peak_op_per_s` refuses by name for what is not (ADR 0015 §2).
    """
    peaks: dict[PrecisionFormat, SourcedValue] = {}
    for fmt, (param, _unit) in PEAK_PARAMS_BY_FORMAT.items():
        declared = instance.descriptor.params.get(param)
        if declared is None:
            continue
        peaks[fmt] = _require_unit(instance.component_id, param, declared)
    return peaks


def _efficiencies(instance: _Instance) -> tuple[SourcedValue, SourcedValue | None]:
    """The compute efficiency, and the memory one if this component declares a second.

    Returns `(compute, memory_or_None)`. `None` is the `ScalarEfficiency` case and means
    "memory roof unscaled", which is what `ScalarEfficiency` has always meant
    (kernel-efficiency.md §3) — NOT a measured 1.0. The caller turns that distinction into
    a warning; it must not be flattened here, because `None` and `1.0` are the same
    arithmetic and different claims.
    """
    execution_model = instance.descriptor.execution_model
    if execution_model is None:  # pragma: no cover — ComponentDescriptor already refuses this
        raise EngineError(
            f"component {instance.component_id!r} has no execution_model; without it the "
            f"roofline would run at peak FLOPs (build-spec §2.3.4)."
        )
    if isinstance(execution_model, SplitEfficiency):
        return (
            _require_unit(
                instance.component_id, "execution_model.compute", execution_model.compute
            ),
            _require_unit(
                instance.component_id, "execution_model.memory", execution_model.memory
            ),
        )
    return (
        _require_unit(
            instance.component_id, "execution_model.value", execution_model.value
        ),
        None,
    )


def _accelerator(
    instance: _Instance, precision: Precision
) -> tuple[Accelerator, tuple[str, ...], Calibration]:
    """Unwrap the roofline inputs at the precision the plan asked for, with their badges.

    **The selection happens here, at dispatch** (ADR 0015 §2): the component declares every
    peak its datasheet prints, and `precision.compute` picks one. A precision the component
    does not declare is refused by name, before anything is computed — see
    `compute.UnsupportedPrecision`.

    **Only the SELECTED peak becomes a contributor and a badge input.** A contributor naming
    a param the run did not read is the finding-B4 defect, and a badge weakened by a number
    nothing spent would be a badge describing the library rather than the metric.
    """
    peaks = _peaks(instance)
    if not peaks:
        declared = ", ".join(param for param, _ in PEAK_PARAMS_BY_FORMAT.values())
        raise EngineError(
            f"component {instance.component_id!r} declares no per-precision peak at all, "
            f"which the C0 roofline needs. Add one of {declared} to the library YAML as a "
            f"SourcedValue — or as provenance: stub with source: null if it cannot be "
            f"sourced."
        )
    bandwidth = _sourced(instance, "hbm_bw")
    compute_efficiency, memory_efficiency = _efficiencies(instance)

    accelerator = Accelerator(
        peak_tera_op_per_s_by_format={fmt: sv.value for fmt, sv in peaks.items()},
        hbm_bw_tb_per_s=bandwidth.value,
        compute_efficiency=compute_efficiency.value,
        # A ScalarEfficiency leaves the memory roof unscaled. That 1.0 is an OMISSION and
        # the run says so — see `_memory_roof_unscaled_warning`.
        memory_efficiency=1.0 if memory_efficiency is None else memory_efficiency.value,
    )
    # Ask for the selected peak now, so an unsupported precision is refused before any
    # number exists rather than part-way through an aggregate.
    try:
        accelerator.peak_op_per_s(precision.compute)
    except UnsupportedPrecision as exc:
        raise EngineError(f"component {instance.component_id!r}: {exc}") from exc

    # ONLY the selected peak's badge and name travel out. The others were unit-checked
    # and then deliberately dropped: a badge weakened by a number the run never spent would
    # describe the library rather than the metric.
    peak_param, _unit = PEAK_PARAMS_BY_FORMAT[precision.compute]
    efficiencies = [compute_efficiency]
    if memory_efficiency is not None:
        efficiencies.append(memory_efficiency)
    contributors = (
        f"{instance.component_id}.{peak_param}",
        f"{instance.component_id}.hbm_bw",
        f"{instance.component_id}.execution_model",
    )
    badge = combine(
        [
            peaks[precision.compute].provenance,
            bandwidth.provenance,
            *(value.provenance for value in efficiencies),
        ]
    )
    return accelerator, contributors, badge


# --------------------------------------------------------------------------------------
# 2 · resolve the fidelity map
# --------------------------------------------------------------------------------------


# Resource dispatch axes. Runtime dispatch resolves once for the run; ADR 0038 scopes
# its Fidelity Map label to the selected stack and participating compute accelerators.
# A CPU or link does not run a serving scheduler merely because its costs were read.
_COMPONENT_AXES: tuple[str, ...] = ("compute", "memory", "network")


def _outcomes(instances: list[_Instance]) -> dict[str, dict[str, _AxisOutcome]]:
    """Per component, per axis: what actually ran. Raises on an unhonourable override."""
    return {
        instance.component_id: {
            axis: _axis_outcome(instance, axis) for axis in _COMPONENT_AXES
        }
        for instance in instances
    }


def _degradations(
    instance: _Instance, row: dict[str, _AxisOutcome]
) -> tuple[list[str], list[str]]:
    """One component's degraded axes, split into the two kinds. `(specific, structural)`.

    Two kinds, and only one of them is surprising. That a `link` has no compute model is
    STRUCTURAL — it is the shape of the prototype, it is visible in the fidelity map, and
    nobody is going to fix it. That a Xeon does not carry the params the M0 model reads is
    SPECIFIC: actionable, and the thing a reader needs spelled out.

    Extracted from `_fidelity_map` in S3 so `validate_system()` can report the same
    sentences BEFORE a run (S2 lane B's cross-lane item 2). One computation, two
    behaviours, exactly as `_replica_shape` and `_envelope_warnings` already are — a second
    implementation of this would be a second answer to "what will actually run", which is
    the one question the Fidelity Map panel exists to answer.
    """
    specific: list[str] = []
    structural: list[str] = []
    for axis in _COMPONENT_AXES:
        outcome = row[axis]
        if outcome.degraded_from is None:
            continue
        if outcome.structural:
            structural.append(f"{instance.component_id} {axis}")
        else:
            specific.append(
                f"{instance.component_id} {axis}: asked {outcome.degraded_from}, ran "
                f"{outcome.level} — {outcome.reason}"
            )
    return specific, structural


def _degradation_summary(degraded: list[str], structural: list[str]) -> list[str]:
    """The two prose paragraphs `run()` emits for degraded axes. Same words for both callers."""
    warnings: list[str] = []
    if degraded:
        # The system default asked for more than a component's own parameters support. Not
        # an error: a default means "the best you have on each part". Not silent either,
        # which is the whole distinction — see rk/engine/registry.py.
        warnings.append(
            f"the system fidelity default asked for a level some components do not carry "
            f"the parameters for, and those axes ran at STUB instead: "
            f"{'; '.join(sorted(degraded))}. This is a DEFAULT being applied as far as it "
            f"goes, not a request being ignored — a per-instance override asking the same "
            f"thing would be an error, because an override names one part and one level."
        )
    if structural:
        warnings.append(
            f"these component/axis pairs have no model at any level, so their fidelity map "
            f"rows read STUB whatever the system default asks for: "
            f"{', '.join(sorted(structural))}. That is the shape of the prototype rather "
            f"than a gap in this config — a link does not compute and a CPU carries no "
            f"memory of its own (rk/engine/registry.py)."
        )
    return warnings


def _fidelity_map(
    instances: list[_Instance],
    outcomes: dict[str, dict[str, _AxisOutcome]],
    accelerator_ids: frozenset[str],
    network: _NetworkView,
    runtime: _RuntimeChoice,
    host_cpu_ids: frozenset[str] = frozenset(),
) -> tuple[tuple[FidelityMapEntry, ...], list[str]]:
    """One row per component: what actually ran for it, and how well calibrated it is.

    "What actually ran", not "what was asked for" — which since P3 is a per-axis answer
    rather than a per-component one. A Xeon in an M0 system reports `memory: STUB`, because
    a CPU carries no memory the M0 model can read; the DDR beside it reports `memory: M0`.
    Before P3 every row's memory and network columns were the literal constant STUB, which
    is the failure ADR 0011 §1 describes: a per-component panel rendering a constant.

    The calibration column is worst-of over everything the component declares, including
    parameters this run never read. That is deliberate: it answers "how well do we know
    this part", not "how well do we know the numbers we happened to use".
    """
    entries: list[FidelityMapEntry] = []
    modelless: list[str] = []
    user_stubbed: list[str] = []
    degraded: list[str] = []
    structural: list[str] = []

    for instance in instances:
        row = outcomes[instance.component_id]

        # An override to STUB on the compute axis is the user saying "claim nothing about
        # this part", and it wins over the fact that a model exists for it.
        overridden_to_stub = instance.fidelity.compute is ComputeFidelity.STUB
        runs_a_model = instance.component_id in accelerator_ids
        if overridden_to_stub and instance.descriptor.role is ComponentRole.ACCELERATOR:
            user_stubbed.append(instance.component_id)
        if not runs_a_model:
            modelless.append(instance.component_id)

        specific, structural_pairs = _degradations(instance, row)
        degraded.extend(specific)
        structural.extend(structural_pairs)

        badges = [value.provenance for value in instance.descriptor.params.values()]
        if instance.descriptor.execution_model is not None:
            badges.extend(
                v.provenance for _, v in instance.descriptor.execution_model.sourced_values
            )

        entries.append(
            FidelityMapEntry(
                component_id=instance.component_id,
                compute=ComputeFidelity(
                    row["compute"].level if runs_a_model else ComputeFidelity.STUB
                ),
                memory=MemoryFidelity(row["memory"].level),
                # N0 ONLY IF IT PRICED SOMETHING. A component can be declared at N0 and
                # feed nothing — the switch has no consumer, and a link that loses the
                # bandwidth race carries no traffic. Reporting N0 for those made this map
                # claim a model ran that never ran, which is the exact thing its own
                # docstring promises it does not do (P14 S2 finding B4).
                network=(
                    NetworkFidelity(row["network"].level)
                    if instance.component_id in network.priced_ids
                    else NetworkFidelity.STUB
                ),
                # ADR 0038: costs from a link do not mean it ran a scheduler.
                runtime=(
                    runtime.level
                    if (runs_a_model or instance.component_id == runtime.decided_by
                        or instance.component_id in host_cpu_ids)
                    else RuntimeFidelity.STUB
                ),
                calibration=combine(badges),
            )
        )

    warnings: list[str] = []
    runtime_stubbed = [e.component_id for e in entries if e.runtime is RuntimeFidelity.STUB]
    if runtime_stubbed:
        warnings.append(
            f"{', '.join(sorted(runtime_stubbed))} have runtime STUB in the Fidelity Map: "
            "they did not run a serving scheduler. Runtime describes the participating "
            "accelerators and selected serving stack, not every component contributing "
            "an analytical cost (ADR 0038)."
        )
    if modelless:
        warnings.append(
            f"{', '.join(sorted(modelless))} ran at compute fidelity STUB: this engine "
            f"models only role=accelerator at C0, so these components contributed their "
            f"power draw, and their memory or network parameters where those axes ran, and "
            f"nothing else. CPU analytical service time — which is what makes an agentic "
            f"workload move — is still unbuilt."
        )
    if user_stubbed:
        # A user-set STUB is a deliberate choice and has to be legible as one. Without
        # this line it is indistinguishable in the output from a component the engine
        # never had a model for, and the run would silently drop a device the config
        # still lists (ADR 0011 §5.4).
        warnings.append(
            f"{', '.join(sorted(user_stubbed))} could have run at C0 but was overridden "
            f"to compute fidelity STUB in the config. That is a deliberate choice and it "
            f"is honoured: the device contributes its power draw and nothing else, so "
            f"throughput is reported as if it were not there. Badges are unaffected — "
            f"fidelity and calibration are separate axes."
        )
    warnings.extend(_degradation_summary(degraded, []))
    if network.unpriced:
        detail = "; ".join(f"{cid} — {why}" for cid, why in network.unpriced)
        warnings.append(
            f"declared at network N0 and PRICED NOTHING, so their fidelity map rows read "
            f"STUB and none of their parameters appears in any metric's contributors: "
            f"{detail}. Removing them from the config would change no number. They are "
            f"listed because a component that is present, configured and inert is a thing "
            f"the run has to say out loud."
        )
    warnings.extend(_degradation_summary([], structural))
    return tuple(entries), warnings


# --------------------------------------------------------------------------------------
# 3 · dispatch — M0 memory, N0 links and fabric
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _MemoryView:
    """Every tier the run may place bytes in, with the badges that came with them."""

    tiers: tuple[f0_memory.MemoryTier, ...]
    # No aggregate badge: capacity checks and the P7 spill-latency consumer
    # propagate the particular inputs they use.
    contributors: tuple[str, ...]
    on_package_ids: tuple[str, ...]
    slottable_ids: tuple[str, ...]
    cxl_ids: tuple[str, ...] = ()
    # compute_resources at M0 whose on-package memory was deliberately NOT pooled, because
    # they run no model. Named in a warning so the exclusion is legible (finding B3).
    excluded_ids: tuple[str, ...] = ()
    # Tiers whose CAPACITY parameter is `provenance: stub` — an unsourced placeholder that
    # is nonetheless deciding a pass/fail gate. See `_capacity_warnings`, S2 finding F3 and
    # ADR 0019.
    stub_capacity_ids: tuple[str, ...] = ()
    stub_capacity_bytes: float = 0.0


def _memory_view(
    instances: list[_Instance],
    outcomes: dict[str, dict[str, _AxisOutcome]],
    running_accelerator_ids: frozenset[str],
) -> _MemoryView:
    """Build the M0 tier list from whatever ran at M0.

    Two sources, and ADR 0011 §3 is the whole reason they are separate:

      ON-PACKAGE   a `compute_resource` that declares `hbm_capacity`/`hbm_bw` **and is one
                   of the devices actually running the model**. This memory belongs to the
                   accelerator and is never a slottable part, so it enters here and nowhere
                   else — an `hbm` `memory_space` instance would be the same silicon counted
                   twice, which is why `reject_on_package_slots` refuses one outright before
                   this function is reached.

                   **The running-device filter is P14 S2 finding B3.** Without it, ANY
                   compute_resource at M0 carrying HBM joined the pool — including a
                   `role: asic` placeholder the roofline never runs on, and a second
                   accelerator type overridden to compute STUB. Slotting an unrelated
                   accelerator then turned `MEMORY CAPACITY EXCEEDED` into a passing run:
                   a model declared resident in memory no device executing it can address.
                   That is ADR 0011 §3's composition error arriving by a route
                   `reject_on_package_slots` does not cover, and badges cannot catch it
                   because every parameter involved is correctly sourced.
      SLOTTABLE    a `memory_space` with role `ddr` or `cxl_pool`: memory that is a real
                   composition choice.

    A tier's capacity and bandwidth are multiplied by the instance count, because eight
    H100s hold eight times 80 GB. Latency is not: latency does not add up over parallel
    devices, and multiplying it would be a units error wearing a plausible face.
    """
    tiers: list[f0_memory.MemoryTier] = []
    contributors: list[str] = []
    badges: list[Calibration] = []
    on_package: list[str] = []
    slottable: list[str] = []
    excluded: list[str] = []
    # The capacity gate is a PASS/FAIL, and a badge cannot travel on a boolean — which is
    # exactly why an unsourced capacity is dangerous here in a way it is not on a metric.
    # Recorded per tier so `_capacity_warnings` can ask what the verdict would be without
    # them. ADR 0019.
    stub_capacity: list[str] = []
    stub_capacity_bytes = 0.0

    for instance in instances:
        if outcomes[instance.component_id]["memory"].level != MemoryFidelity.M0:
            continue
        cid = instance.component_id
        if instance.descriptor.kind is ComponentKind.COMPUTE_RESOURCE:
            if cid not in running_accelerator_ids:
                # Its HBM is real and it is not this run's memory. See the docstring.
                excluded.append(cid)
                continue
            capacity = _sourced(instance, "hbm_capacity")
            bandwidth = _sourced(instance, "hbm_bw")
            tiers.append(
                f0_memory.MemoryTier(
                    name=cid,
                    capacity_bytes=f0_memory.gb_to_bytes(capacity.value) * instance.count,
                    # hbm_bw is TB/s on this param, per ADR 0006 and the unit gate above.
                    bw_byte_per_s=bandwidth.value * 1e12 * instance.count,
                    latency_s=0.0,
                )
            )
            contributors.extend([f"{cid}.hbm_capacity", f"{cid}.hbm_bw"])
            badges.extend([capacity.provenance, bandwidth.provenance])
            on_package.append(cid)
            if capacity.provenance is Calibration.STUB:
                stub_capacity.append(cid)
                stub_capacity_bytes += (
                    f0_memory.gb_to_bytes(capacity.value) * instance.count
                )
            continue

        capacity = _sourced(instance, "capacity_gb")
        bandwidth = _sourced(instance, "bw_gb_per_s")
        latency = instance.descriptor.params.get("latency_ns")
        added = instance.descriptor.params.get("added_latency_ns")
        latency_ns = 0.0
        if latency is not None:
            _require_unit(cid, "latency_ns", latency)
            latency_ns += latency.value
            contributors.append(f"{cid}.latency_ns")
            badges.append(latency.provenance)
        if added is not None:
            # build-spec §1.3's "CXL pooled tier: STUB + latency knob". ADDED, so it is
            # summed onto the tier's own latency rather than replacing it.
            _require_unit(cid, "added_latency_ns", added)
            latency_ns += added.value
            contributors.append(f"{cid}.added_latency_ns")
            badges.append(added.provenance)
        tiers.append(
            f0_memory.MemoryTier(
                name=cid,
                capacity_bytes=f0_memory.gb_to_bytes(capacity.value) * instance.count,
                bw_byte_per_s=f0_memory.gb_per_s_to_byte_per_s(bandwidth.value)
                * instance.count,
                latency_s=f0_memory.ns_to_s(latency_ns),
            )
        )
        contributors.extend([f"{cid}.capacity_gb", f"{cid}.bw_gb_per_s"])
        badges.extend([capacity.provenance, bandwidth.provenance])
        slottable.append(cid)
        if capacity.provenance is Calibration.STUB:
            stub_capacity.append(cid)
            stub_capacity_bytes += f0_memory.gb_to_bytes(capacity.value) * instance.count

    return _MemoryView(
        tiers=tuple(tiers),
        contributors=tuple(contributors),
        on_package_ids=tuple(sorted(on_package)),
        slottable_ids=tuple(sorted(slottable)),
        cxl_ids=tuple(i.component_id for i in instances
                      if i.descriptor.role is ComponentRole.CXL_POOL),
        excluded_ids=tuple(sorted(excluded)),
        stub_capacity_ids=tuple(sorted(stub_capacity)),
        stub_capacity_bytes=stub_capacity_bytes,
    )


@dataclass(frozen=True)
class _NetworkView:
    """The link a collective runs over, and — separately — what merely sat there.

    `priced_ids` is the honest half. A component may be declared at N0 and still feed no
    number: the switch has no consumer at all (nothing calls the fabric model), and a link
    that loses the bandwidth race is never asked for a transfer. Both used to be reported
    as `network: N0` in the fidelity map, and the switch's four params were listed as
    contributors to five metrics — while deleting the switch changed no number to the last
    bit (P14 S2 finding B4).

    That is the contributor list, which is the audit trail this whole product rests on,
    naming parameters that touched nothing. ADR 0009 §5's rule — a badge nothing computed
    is a badge nothing has checked — applied to provenance rather than to a badge. So the
    view now records what was PRICED and what was only DECLARED, and the caller reports
    them differently.
    """

    link: f0_links.Link | None
    fabric: f0_fabric.Fabric | None
    contributors: tuple[str, ...]
    badge: Calibration
    # Components whose parameters actually fed a number this run.
    priced_ids: frozenset[str] = frozenset()
    # Components at N0 that fed nothing, and why — named in a warning.
    unpriced: tuple[tuple[str, str], ...] = ()


def _network_view(
    instances: list[_Instance], outcomes: dict[str, dict[str, _AxisOutcome]]
) -> _NetworkView:
    """Pick the link a tensor-parallel collective runs over, and the fabric above it.

    **The FASTEST declared link wins, ties broken by role.** A real collective library
    routes over the best path available, and — more to the point here — choosing by
    bandwidth is what makes P3 acceptance test 2 a property rather than a coincidence:
    removing a link can only ever leave a slower-or-equal one, so "removing NVLink never
    lowers TP communication time" holds for ANY set of bandwidths. A fixed role ordering
    does not have that guarantee; a config whose PCIe outran its NVLink would violate it,
    and the engine would be asserting a preference over the numbers it was given.

    Every link bandwidth in the shipped library is a STUB (listed in P3's report), so which
    link wins in practice today is decided by placeholders. That is stated in the run's
    collective warning, which names the link it priced over, rather than hidden behind a
    rule that looks principled.

    A system with no link at N0 gets `link=None`, and the caller warns that collectives
    were free. That is the STUB behaviour arrived at honestly rather than by default: the
    user asked for N0 and there is nothing in the system for N0 to price.
    """
    candidates: list[_Instance] = []
    fabric_instance: _Instance | None = None
    for instance in instances:
        if outcomes[instance.component_id]["network"].level != NetworkFidelity.N0:
            continue
        if instance.descriptor.kind is ComponentKind.LINK:
            candidates.append(instance)
        elif instance.descriptor.kind is ComponentKind.FORWARDING_ELEMENT:
            if fabric_instance is None:
                fabric_instance = instance

    contributors: list[str] = []
    badges: list[Calibration] = []
    unpriced: list[tuple[str, str]] = []
    priced: set[str] = set()

    link: f0_links.Link | None = None
    if candidates:
        def rank(instance: _Instance) -> tuple[float, int, str]:
            bandwidth = _sourced(instance, "bw_gb_per_s")
            tie = (
                _LINK_TIE_BREAK.index(instance.descriptor.role)
                if instance.descriptor.role in _LINK_TIE_BREAK
                else len(_LINK_TIE_BREAK)
            )
            return (-bandwidth.value, tie, instance.component_id)

        chosen = min(candidates, key=rank)
        bandwidth = _sourced(chosen, "bw_gb_per_s")
        latency = _sourced(chosen, "latency_us")
        link = f0_links.Link.from_datasheet_units(
            name=chosen.component_id,
            bw_gb_per_s=bandwidth.value,
            latency_us=latency.value,
            role=chosen.descriptor.role,
        )
        contributors.extend(
            [f"{chosen.component_id}.bw_gb_per_s", f"{chosen.component_id}.latency_us"]
        )
        badges.extend([bandwidth.provenance, latency.provenance])
        priced.add(chosen.component_id)
        for other in candidates:
            if other.component_id != chosen.component_id:
                unpriced.append(
                    (
                        other.component_id,
                        f"a faster link was present, so every collective ran over "
                        f"{chosen.component_id} and this one carried nothing",
                    )
                )

    fabric: f0_fabric.Fabric | None = None
    if fabric_instance is not None:
        cid = fabric_instance.component_id
        port_bw = _sourced(fabric_instance, "port_bw_gb_per_s")
        port_latency = _sourced(fabric_instance, "port_latency_us")
        nodes = fabric_instance.descriptor.params.get("nodes_per_switch")
        oversub = fabric_instance.descriptor.params.get("oversubscription_ratio")
        nodes_value = 1.0
        oversub_value = 1.0
        if nodes is not None:
            _require_unit(cid, "nodes_per_switch", nodes)
            nodes_value = nodes.value
        if oversub is not None:
            _require_unit(cid, "oversubscription_ratio", oversub)
            oversub_value = oversub.value
        fabric = f0_fabric.Fabric.from_datasheet_units(
            name=cid,
            port_bw_gb_per_s=port_bw.value,
            port_latency_us=port_latency.value,
            nodes_per_switch=nodes_value,
            oversubscription_ratio=oversub_value,
        )
        # ITS PARAMS ARE DELIBERATELY *NOT* CONTRIBUTORS. The object is built — its units
        # are checked and a malformed switch still fails loudly — but no model consumes it,
        # so nothing it declares fed any number. Listing it would be a false audit trail.
        # Wiring the scale-out path is a modelling decision this sprint did not take: with
        # the scope tree topped out at one rack (ADR 0011 §4) and no node-boundary notion in
        # `_collectives`, nothing decides when a collective crosses the fabric rather than
        # the link, and `nodes_per_switch` has no consumer.
        unpriced.append(
            (
                cid,
                "no model consumes a forwarding_element: the scale-out path in "
                "f0/fabric.py (scale_out_transfer_time_s) has no caller, so this switch's "
                "bandwidth, latency and topology fed no number in this run",
            )
        )

    if link is not None:
        # The contention scalar is the model's own claim and enters propagation like
        # f0.power.sum_of_tdp does. It can only ever weaken (CLAUDE.md invariant 3).
        # Gated on the LINK and not on the fabric: the scalar multiplies a collective, and
        # with no link there is no collective for it to have multiplied.
        contributors.append(f0_fabric.FABRIC_MODEL_CONTRIBUTOR)
        badges.append(f0_fabric.FABRIC_MODEL_BADGE)

    return _NetworkView(
        link=link,
        fabric=fabric,
        contributors=tuple(contributors),
        badge=combine(badges) if badges else Calibration.STUB,
        priced_ids=frozenset(priced),
        unpriced=tuple(sorted(unpriced)),
    )


# --------------------------------------------------------------------------------------
# 4 · aggregate
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Collectives:
    """What tensor parallelism and MoE routing cost, per phase. Seconds."""

    prefill_s: float
    decode_step_s: float
    moe_prefill_s: float
    moe_decode_step_s: float
    over: str | None

    @property
    def total_prefill_s(self) -> float:
        return self.prefill_s + self.moe_prefill_s

    @property
    def total_decode_step_s(self) -> float:
        return self.decode_step_s + self.moe_decode_step_s


_NO_COLLECTIVES = _Collectives(0.0, 0.0, 0.0, 0.0, None)


def _collectives(
    network: _NetworkView,
    workload: WorkloadSpec,
    plan: ExecutionPlan,
    seq_len_tokens: int,
    batch: int,
) -> _Collectives:
    """Price the all-reduces tensor parallelism buys, and MoE's one extra term.

    **This is what retires ADR 0003 §7.4's UPPER BOUND warning.** Until N0 the engine
    divided by `tp` and said the number was optimistic by an unmodelled amount; the amount
    is now modelled, out of the link the system actually declares.

    Two all-reduces per transformer layer, each over the activation tensor — `links.py`
    holds that accounting and the reasoning for it. Prefill reduces over the whole prompt;
    decode reduces over one token, so its message is tiny and its cost is dominated by the
    per-collective latency, which is exactly why `allreduce_count` keeps the collectives
    separate instead of folding them into one message.

    MoE adds ONE more term and nothing else (CLAUDE.md invariant 9, build-spec §2.3.5). It
    is keyed to `parallelism.ep`, because that is the only thing in the schema that says
    how many ways the experts are spread; at ep=1 every expert is local and the term is
    zero. Expert placement, routing and imbalance are NOT modelled and are not started.
    """
    link = network.link
    if link is None:
        return _NO_COLLECTIVES

    model = workload.model
    ranks = plan.parallelism.tp
    count = f0_links.allreduce_count(model)
    prefill_s = f0_fabric.collective_time_s(
        link, f0_links.allreduce_bytes(model, seq_len_tokens, batch), ranks, count
    )
    decode_s = f0_fabric.collective_time_s(
        link, f0_links.allreduce_bytes(model, 1, batch), ranks, count
    )

    moe_prefill_s = 0.0
    moe_decode_s = 0.0
    if model.n_experts > 0 and plan.parallelism.ep > 1:
        moe_prefill_s = f0_fabric.moe_all_to_all_time_s(
            link,
            f0_links.allreduce_bytes(model, seq_len_tokens, batch),
            plan.parallelism.ep,
            model.n_layers,
        )
        moe_decode_s = f0_fabric.moe_all_to_all_time_s(
            link,
            f0_links.allreduce_bytes(model, 1, batch),
            plan.parallelism.ep,
            model.n_layers,
        )

    return _Collectives(
        prefill_s=prefill_s,
        decode_step_s=decode_s,
        moe_prefill_s=moe_prefill_s,
        moe_decode_step_s=moe_decode_s,
        over=link.name,
    )


@dataclass(frozen=True)
class _CollectiveCoefficients:
    """`_collectives`, decomposed into the affine function it already is.

    `collective_time_s` is `collectives * (steps*alpha + steps/ranks * bytes/beta) * C`
    and `allreduce_bytes` is linear in (tokens x batch), so the whole tp collective cost of
    one iteration is exactly

        fixed_s  +  s_per_message_token * m

    where m is the iteration's MESSAGE TOKENS: the total prompt tokens for a prefill, the
    batch size for a decode step. The MoE all-to-all is priced with the same ring model, so
    it folds into the same two numbers rather than needing a third.

    **THIS EXISTS BECAUSE A CONSTANT WAS WRONG BY 58x.** `_dispatch_and_aggregate` prices
    the collective once, at `max_batch` x `prompt_tokens`, which is right for R0 — R0 IS a
    saturated batch. The DES's prefill iterations usually carry one request, and charging
    them the batch-64 message (669 ms on 8xH100 over NVLink, against a true 11.6 ms) more
    than halves the node's modelled throughput. Every input to that number is correctly
    sourced and badged, so nothing downstream could have caught it. ADR 0018 §2.

    The coefficients are read off `f0` directly rather than fitted from two evaluations of
    `_collectives`: a fit would keep agreeing with a model that had stopped being affine.
    `tests/unit/test_runtime_r1.py` compares them against `_collectives` across batches, so
    a non-affine term added upstream fails here rather than being silently linearised.
    """

    fixed_s: float
    s_per_message_token: float

    def at(self, message_tokens: int) -> float:
        """What an iteration reducing this many tokens of activation pays. Seconds."""
        return self.fixed_s + self.s_per_message_token * message_tokens


_NO_COLLECTIVE_COEFFICIENTS = _CollectiveCoefficients(0.0, 0.0)


def _collective_coefficients(
    network: _NetworkView, workload: WorkloadSpec, plan: ExecutionPlan
) -> _CollectiveCoefficients:
    """The alpha and beta of this system's tp collectives, per iteration and per token.

    Same inputs, same link and same contention scalar as `_collectives` — this is that
    function's cost model read as a line rather than sampled at one point. A system with no
    link at N0 gets zeros, exactly as `_collectives` gets `_NO_COLLECTIVES`, and the run
    warns that every collective was free.
    """
    link = network.link
    if link is None:
        return _NO_COLLECTIVE_COEFFICIENTS

    model = workload.model
    ranks = plan.parallelism.tp
    count = f0_links.allreduce_count(model)
    one_token_bytes = f0_links.allreduce_bytes(model, 1, 1)

    fixed_s = f0_fabric.collective_time_s(link, 0.0, ranks, count)
    per_token_s = (
        f0_fabric.collective_time_s(link, one_token_bytes, ranks, count) - fixed_s
    )

    # MoE's one extra term (CLAUDE.md invariant 9), affine in the same bytes and therefore
    # summed into the same two coefficients rather than tracked separately.
    if model.n_experts > 0 and plan.parallelism.ep > 1:
        moe_fixed_s = f0_fabric.moe_all_to_all_time_s(
            link, 0.0, plan.parallelism.ep, model.n_layers
        )
        fixed_s += moe_fixed_s
        per_token_s += (
            f0_fabric.moe_all_to_all_time_s(
                link, one_token_bytes, plan.parallelism.ep, model.n_layers
            )
            - moe_fixed_s
        )

    return _CollectiveCoefficients(fixed_s=fixed_s, s_per_message_token=per_token_s)


@dataclass(frozen=True)
class _Aggregate:
    """Everything the metrics are built from, after the models have run.

    `ttft_ms`, `tpot_ms` and `throughput_output_tok_per_s` are the ANALYTICAL answers
    always — this object is what `_dispatch_and_aggregate` produced. When the effective
    runtime level is R1, `run()` computes a `_Latency` from the DES beside it and reports
    that instead; the analytical numbers stay here rather than being overwritten, because
    the DES's per-iteration cost is built from the same `prefill`/`decode`/`collectives`
    and losing them would leave the R1 badge unable to name what fed it.
    """

    prefill: PhaseRoofline
    decode: PhaseRoofline
    ttft_ms: float
    tpot_ms: float
    throughput_output_tok_per_s: float
    replicas: int
    batch: int
    collectives: _Collectives
    # The R0 verdict (ADR 0022). Empty when the effective runtime level is R1, because the
    # SLO is then judged against the DES's real p99 in `run()` instead — checking here as
    # well would compare one target against two different numbers in one result.
    slo: SloVerdict = SloVerdict()


def _dispatch_and_aggregate(
    plan: ExecutionPlan,
    workload: WorkloadSpec,
    accelerator: Accelerator,
    accelerator_count: int,
    network: _NetworkView,
    network_is_stub: bool,
    runtime_level: RuntimeFidelity,
    warnings: list[str],
    dvfs: DvfsParameters | None = None,
    hbm_kv_bytes: float | None = None,
    spill_latency_s: float = 0.0,
) -> _Aggregate:
    """Run the C0 roofline once, add the N0 collective cost, then scale out over the tree.

    Three scaling steps, and each owes the reader something:

    *tp* divides the per-device compute time (ADR 0003 §7.4) and then ADDS the collective
    the sharding pays for. At network STUB the second half does not happen and the run
    emits ADR 0003 §7.4's warning verbatim, because at STUB the number really is an upper
    bound. At N0 the collective is priced and a different warning says what it cost.

    *replicas* multiplies throughput by how many independent tp-groups the accelerators in
    the tree make up. Without it the run would divide node-wide power by one group's
    throughput and report an energy-per-token several times too high — power counts every
    device in the tree, so throughput has to as well.

    **This function runs at BOTH runtime levels and its answer is R0's answer at both.**
    An R1 run needs the roofline anyway — `IterationCost` is built out of the same
    accelerator and the same `_collectives`, and the DES's per-iteration cost is this
    arithmetic evaluated on a live batch instead of on `max_batch` at a fixed context. So
    `runtime_level` does not select a model here; it selects which SENTENCES the run says
    about itself, because three of the warnings below describe things R0 does not do and
    R1 does. `run()` replaces the latency and throughput values afterwards when the DES
    ran, and an R0 run reaches the end of this function with the numbers it always had.
    """
    point = workload.analytical_lengths

    parallelism = plan.parallelism
    devices_per_replica, replicas, problem = _replica_shape(plan, accelerator_count)
    if problem is not None:
        raise EngineError(problem)

    seq_len_tokens = point.prompt_tokens
    # PER REPLICA, both of them. `max_batch` and `max_tokens_in_flight` come off one
    # Batching object and are read the same way: each replica runs its own scheduler with
    # its own batch. That is why throughput multiplies by `replicas` while the token-budget
    # check below does not — the budget is per replica too.
    batch = plan.batching.max_batch

    prefill = prefill_roofline(
        workload.model, accelerator, seq_len_tokens, batch, plan.precision
    )
    decode = decode_roofline(
        workload.model, accelerator, seq_len_tokens, batch, plan.precision
    )

    collectives = _collectives(network, workload, plan, seq_len_tokens, batch)
    live_cost = replace(iteration_cost(workload.model, accelerator, plan.precision,
                                      tp=parallelism.tp),
                        hbm_kv_bytes=hbm_kv_bytes, spill_latency_s=spill_latency_s)
    spill_s = live_cost.spill_s(seq_len_tokens * batch)
    if dvfs is not None:
        roofs = []
        for roof, comm, extra in ((prefill, collectives.total_prefill_s, 0.0),
                                  (decode, collectives.total_decode_step_s, spill_s)):
            operating = f0_power.operating_point(roof.compute_time_s / parallelism.tp,
                roof.memory_time_s / parallelism.tp, comm + extra, dvfs)
            f = operating.frequency_ratio
            roofs.append(replace(roof, compute_time_s=roof.compute_time_s / f,
                memory_time_s=roof.memory_time_s / f ** dvfs.bandwidth_exponent.value))
        prefill, decode = roofs
    decode = replace(decode, extra_delay_s=spill_s * parallelism.tp)

    # ADR 0003 §7.4: ideal linear scaling in tp for the compute, plus what the sharding
    # actually costs on the wire.
    ttft_s = prefill.time_s / parallelism.tp + collectives.total_prefill_s
    tpot_s = decode.time_s / parallelism.tp + collectives.total_decode_step_s
    # ADR 0024: the cycle is prefill THEN decode, so the batch's output tokens are divided
    # by the whole cycle and not by the decode step alone. Until that ADR this read
    # `replicas * batch / tpot_s`, which charged the accelerator for generating tokens and
    # not for reading the prompts they answer — a decode-only rate wearing the name of a
    # system throughput, which is build-spec §2.4's forbidden substitution. `prefill.time_s`
    # is the WHOLE BATCH's prefill (prefill_roofline's docstring), so it is already the
    # per-cycle term: a number that was computed and discarded is now spent.
    output_tokens = point.output_tokens
    cycle_s = ttft_s + output_tokens * tpot_s
    throughput = replicas * batch * output_tokens / cycle_s

    # The workload declares a request stream; R0 models a saturated steady state instead.
    # At R1 the DES consumes that stream request by request, so the sentence is untrue and
    # is not emitted — this is the concrete thing the level buys, stated by its absence.
    if runtime_level is RuntimeFidelity.R0:
        generator = workload.generator
        stream_description = (
            f"n_requests={generator.n_requests} and arrival_rate_req_per_s="
            f"{generator.arrival_rate_req_per_s} were read and not used. "
            if generator is not None
            else "the trace was read and its arrivals and per-request lengths were not used "
                 "beyond the separately declared analytical_point. "
        )
        warnings.append(
            f"the workload's request stream is not modelled at R0: {stream_description}"
            f"Throughput is a "
            f"saturated steady state at max_batch={batch}: one cycle prefills the whole "
            f"batch ({ttft_s * 1e3:.1f} ms) and then decodes {output_tokens} tokens "
            f"({output_tokens * tpot_s * 1e3:.1f} ms) "
            f"[provenance: {_LATENCY_BADGE_SLOT}], every slot full, no scheduling gap "
            f"and no overlap between the two — an upper bound, not a prediction (ADR 0024). "
            f"TPOT is evaluated at a fixed context of {seq_len_tokens} tokens, so KV growth "
            f"across the {output_tokens} generated tokens is ignored. Arrival, queueing and "
            f"batch occupancy are what runtime R1 models (P5) — select it."
        )
        if batch > 1:
            # ADR 0024's "what this does NOT fix". The number is about to get more
            # attention now that throughput pays for prefill, and it is the same term.
            warnings.append(
                f"ttft_p50_ms is the WHOLE BATCH's prefill at R0 ({ttft_s * 1e3:.1f} ms "
                f"[provenance: {_LATENCY_BADGE_SLOT}] for "
                f"{batch} sequences), not one request's wait. For a synchronous batch that "
                f"is honest — every request in it does get its first token then — but it is "
                f"not the per-request TTFT a Server latency target means, and it GROWS with "
                f"max_batch rather than shrinking. Runtime R1 is what produces a per-request "
                f"distribution (ADR 0024).{_LATENCY_STUB_SLOT}"
            )

    model = workload.model
    if model.n_experts > 0:
        warnings.append(
            f"{model.name!r} is MoE ({model.n_experts} experts, "
            f"{model.experts_per_token} per token): active_params drives compute and "
            f"bandwidth, total_params only capacity (build-spec §2.3.5). Expert routing, "
            f"placement and load imbalance are not modelled, so these numbers assume "
            f"perfectly balanced routing."
        )

    _warn_about_collectives(
        parallelism.tp, collectives, network_is_stub, ttft_s, tpot_s, model, plan, warnings
    )

    if parallelism.pp > 1:
        warnings.append(
            f"pipeline parallelism (pp={parallelism.pp}) is not modelled at C0: the "
            f"{devices_per_replica} devices per replica are treated as capacity only, and "
            f"pipeline bubbles, stage imbalance and the extra activation transfers are all "
            f"absent. Every latency here is optimistic by an unmodelled amount."
        )
    if parallelism.ep > 1 and (model.n_experts == 0 or collectives.over is None):
        warnings.append(
            f"expert parallelism (ep={parallelism.ep}) has no effect on these numbers: "
            f"there is no MoE model in this workload or no link to price its all-to-all."
        )
    if replicas > 1:
        warnings.append(
            f"throughput assumes {replicas} independent replicas of {devices_per_replica} "
            f"accelerator(s) each, every one running its own batch of max_batch={batch} "
            f"(batching is per replica, not system-wide). Host, memory-system and fabric "
            f"contention between them is not modelled at C0, so this is an UPPER BOUND."
        )
    if accelerator_count % devices_per_replica:
        warnings.append(
            f"{accelerator_count % devices_per_replica} of {accelerator_count} "
            f"accelerators are left over by tp x pp = {devices_per_replica} and produce "
            f"no throughput. They still draw power, so energy_j_per_token counts them."
        )
    if parallelism.dp != replicas:
        warnings.append(
            f"the plan declares dp={parallelism.dp} but the system's {accelerator_count} "
            f"accelerators make up {replicas} replica(s) at tp x pp = "
            f"{devices_per_replica}. The hardware count won: dp is not what the engine "
            f"counted."
        )

    tokens_in_flight = batch * seq_len_tokens
    over_budget = tokens_in_flight > plan.batching.max_tokens_in_flight
    if runtime_level is RuntimeFidelity.R0 and over_budget:
        # R1 enforces this budget at admission, so the warning is R0's alone.
        warnings.append(
            f"max_batch={batch} at {seq_len_tokens} prompt tokens puts "
            f"{tokens_in_flight} tokens in flight, over the plan's own "
            f"max_tokens_in_flight={plan.batching.max_tokens_in_flight}. R0 is an ideal "
            f"scheduler and does not enforce the budget — it was not clamped. Runtime R1 "
            f"enforces it at admission (P5)."
        )
    if runtime_level is RuntimeFidelity.R0 and workload.replications > 1:
        warnings.append(
            f"replications={workload.replications} has no effect at R0: the analytical "
            f"model is deterministic, so every replication returns the same numbers. "
            f"Replication is what runtime R1 spends its seeds on (P5)."
        )

    # At R1 the SLO is checked against the DES's real p99 instead, after it has run — see
    # `run()`. Checking here as well would compare the same target against two different
    # numbers in one result.
    slo = (
        _warn_about_the_slo(workload, ttft_s * 1e3, tpot_s * 1e3, warnings)
        if runtime_level is RuntimeFidelity.R0
        else SloVerdict()
    )

    return _Aggregate(
        slo=slo,
        prefill=prefill,
        decode=decode,
        ttft_ms=ttft_s * 1e3,
        tpot_ms=tpot_s * 1e3,
        throughput_output_tok_per_s=throughput,
        replicas=replicas,
        batch=batch,
        collectives=collectives,
    )


def _warn_about_collectives(
    tp: int,
    collectives: _Collectives,
    network_is_stub: bool,
    ttft_s: float,
    tpot_s: float,
    model: object,
    plan: ExecutionPlan,
    warnings: list[str],
) -> None:
    """Say what tensor parallelism cost, or say that nothing charged it.

    Three cases, and each is a different claim about the number above it:

      network STUB       ADR 0003 §7.4's warning, verbatim. Lane B renders it as a banner,
                         so the text is part of the contract rather than a phrasing choice.
      N0, no link        the user asked for N0 and the system declares no link for it to
                         price. Free transfers again, but arrived at by an omission in the
                         config rather than by a declared STUB, so it says so differently.
      N0, priced         what it cost and what share of the answer it is.
    """
    if tp <= 1:
        # A tp=1 group runs no all-reduce — but an MoE all-to-all is keyed to `ep`, not to
        # `tp`, so it can be charged here while every all-reduce term is zero. Returning
        # unconditionally used to make that cost silent (P14 S2 finding B5): TTFT moved by
        # a quarter and the run said nothing, which is the build-spec §2.4 failure inverted
        # — a cost silently ADDED rather than a model silently dropped.
        if collectives.moe_prefill_s > 0.0 or collectives.moe_decode_step_s > 0.0:
            _warn_about_moe_all_to_all(collectives, plan, warnings)
        return
    if network_is_stub:
        warnings.append(_TP_WARNING)
        return
    if collectives.over is None:
        warnings.append(
            f"network fidelity is N0 but no link in this system ran at N0, so every tp={tp} "
            f"collective was free and the throughput above is an UPPER BOUND — the same "
            f"number network: STUB would have produced. Either no link is slotted, or every "
            f"one that is has been overridden to network: STUB. Slot a link (pcie, "
            f"nvlink_c2c, ualink or apu_unified) at N0 to charge it. (The wording used to "
            f"say the system declared no link at all, which was untrue of the override "
            f"case — P14 S2.)"
        )
        return
    share_prefill = collectives.total_prefill_s / ttft_s if ttft_s > 0 else 0.0
    share_decode = collectives.total_decode_step_s / tpot_s if tpot_s > 0 else 0.0
    warnings.append(
        f"tp={tp} collectives were priced at N0 over {collectives.over}: "
        f"{collectives.total_prefill_s * 1e3:.3f} ms of TTFT ({share_prefill:.1%}) and "
        f"{collectives.total_decode_step_s * 1e3:.3f} ms of every decode step "
        f"({share_decode:.1%}). The model is alpha-beta with a single contention scalar "
        f"(f0/fabric.py) — no congestion, no in-network reduction, no overlap with compute, "
        f"which N1 flow-level would add and which is deferred (build-spec §1.3). Compute "
        f"and communication are charged SERIALLY here, so a stack that overlaps them beats "
        f"this number."
    )
    if getattr(model, "n_experts", 0) > 0 and plan.parallelism.ep > 1:
        _warn_about_moe_all_to_all(collectives, plan, warnings)


def _warn_about_moe_all_to_all(
    collectives: _Collectives, plan: ExecutionPlan, warnings: list[str]
) -> None:
    """Say what the MoE all-to-all cost, and say what the engine does NOT know about `ep`.

    The second half is P14 S2 finding B5, and it is a contradiction rather than a crudeness:
    `_replica_shape` computes `devices_per_replica = tp * pp` and ignores `ep`, while this
    term charges a collective over `ep` ranks. So the same run simultaneously says the
    experts are spread `ep` ways (and pays for it) and that each device holds a whole
    replica (and multiplies throughput and capacity by that). Both cannot be true.

    It is warned about rather than resolved because resolving it is a modelling decision —
    either `ep` devices sit inside a replica (`devices_per_replica = tp * pp * ep`, which
    moves throughput AND capacity sizing) or `ep` must divide `tp` — and build-spec §1.3
    defers expert placement, which is the thing that would decide it. An unannounced
    contradiction is the defect; a stated one is a known limit.
    """
    warnings.append(
        f"MoE all-to-all was charged as one extra collective term over {collectives.over} "
        f"at ep={plan.parallelism.ep}: {collectives.moe_prefill_s * 1e3:.3f} ms of TTFT and "
        f"{collectives.moe_decode_step_s * 1e3:.3f} ms per decode step, priced with the "
        f"same ring cost model as an all-reduce and multiplied by the fabric's ESTIMATED "
        f"contention scalar. Expert placement, routing and straggler imbalance are not "
        f"modelled (build-spec §2.3.5), so this term is a floor."
    )
    warnings.append(
        f"AND THE ENGINE IS INCONSISTENT ABOUT ep={plan.parallelism.ep}: it charges an "
        f"{plan.parallelism.ep}-rank all-to-all above, but counts only tp x pp = "
        f"{plan.parallelism.tp * plan.parallelism.pp} devices per replica, so the replica "
        f"count, the throughput multiplier and the capacity requirement are all computed as "
        f"though the experts were NOT spread. Both cannot be true. Whether ep devices sit "
        f"inside a replica or are replicas is an unresolved modelling decision (build-spec "
        f"§1.3 defers expert placement); until it is taken, treat any ep>1 run as carrying "
        f"an unmodelled inconsistency rather than as an answer."
    )


def _warn_about_the_slo(
    workload: WorkloadSpec,
    ttft_ms: float,
    tpot_ms: float,
    warnings: list[str],
    runtime_level: RuntimeFidelity = RuntimeFidelity.R0,
) -> SloVerdict:
    """Say whether a declared SLO was met, and what kind of number said so.

    build-spec §2.6 lists "SLO violated" among the Results screen's constraint banners, and
    `RunResult.warnings` is where that banner reads it. Engine README invariant 5: a
    constraint violation becomes a warning, never a silent clamp.

    Since ADR 0022 it ALSO returns the verdict as a `SloVerdict`, and both call sites put it
    on the `RunResult`. The warning text is unchanged — it is what the banner reads today —
    but a sentence cannot be sorted, filtered or exported, so a sweep point could not be
    marked infeasible and a comparison could not be ranked by feasibility. `certifiable`
    carries the distinction the next paragraph describes, into every screen that shows it.

    The comparison is honest about what it is comparing, and P5 changes what there is to be
    honest ABOUT. At R0 the "p99" is the analytical p50 — there is no distribution — so a
    target expressed as a p99 is checked against a number that is not one, and the warning
    says so rather than implying a tail measurement the engine did not make. At R1 it is a
    real percentile out of the DES, and the caveat becomes the one that is true there: it
    is an ESTIMATE of a tail from finitely many seeded arrivals, and nothing enforces the
    SLO either way — no admission control turns requests away to protect it.
    """
    estimated_at = (
        "R0 has no admission control and no scheduler to respond to an SLO — the run was "
        "neither clamped nor rejected — and the p99 being compared is the analytical p50 "
        "(see the R0 percentile warning above). Runtime R1 is what makes an SLO "
        "measurable, though still not enforced."
        if runtime_level is not RuntimeFidelity.R1
        else "the p99 compared here is the R1 DES's estimate of a p99 across replications, "
        "not a measured tail; and nothing enforced the SLO — the scheduler has admission "
        "control for KV and for its token budget, and none for a latency target, so no "
        "request was turned away to protect it."
    )
    targets = [
        (name, target, actual)
        for name, target, actual in (
            ("ttft_p99_ms", workload.slo.ttft_p99_ms, ttft_ms),
            ("tpot_p99_ms", workload.slo.tpot_p99_ms, tpot_ms),
        )
        if target is not None
    ]
    # `certifiable` is the honest half (ADR 0022 §2): a real percentile only exists at R1.
    # At R0 the number wearing the p99's name is the analytical p50, so a met target is not
    # a measured pass and the UI must not render it as one.
    certifiable = runtime_level is RuntimeFidelity.R1
    if not targets:
        return SloVerdict(certifiable=certifiable)

    # PROVISIONAL, AND STUB ON PURPOSE. The latency badge is combined near the end of
    # `run()` from the compute, network and serving contributors, and this function is one
    # of the places that runs before it exists — the same ordering that made ADR 0027's
    # prose carry a slot rather than a grade. `_stamp_slo_actuals()` replaces each of these
    # with the RunResult metric `metric_field` names, so the verdict and the metric card
    # are one object. Starting at STUB means a missed stamp can only ever weaken a badge,
    # never improve one (CLAUDE.md invariant 3). ADR 0036 §1.
    verdicts = tuple(
        SloTargetVerdict(
            metric_field=name,
            target_ms=target,
            actual=Metric(
                value=actual, unit="ms", badge=Calibration.STUB, contributors=()
            ),
            met=actual <= target,
        )
        for name, target, actual in targets
    )
    violations = [(name, target, actual) for name, target, actual in targets if actual > target]
    if violations:
        # ADR 0027: `actual` IS a RunResult latency metric, quoted here in its own unit, so
        # the sentence states the grade that metric carries. `target` is the workload's own
        # declaration — it defines the run rather than claiming anything about the world —
        # and stays bare, the same line ADR 0027 draws for composition counts.
        detail = ", ".join(
            f"{name} is {actual:.1f} ms [provenance: {_LATENCY_BADGE_SLOT}] against a "
            f"declared {target:.10g} ms target"
            for name, target, actual in violations
        )
        caveat = estimated_at
        warnings.append(f"SLO VIOLATED: {detail}. {caveat}{_LATENCY_STUB_SLOT}")
        return SloVerdict(targets=verdicts, met=False, certifiable=certifiable, caveat=caveat)

    detail = ", ".join(f"{name} <= {target:.10g} ms" for name, target, _ in targets)
    caveat = f"nothing enforces it: {estimated_at}"
    warnings.append(
        f"the workload declares an SLO ({detail}) and it was MET, but nothing enforces "
        f"it: {estimated_at}"
    )
    return SloVerdict(targets=verdicts, met=True, certifiable=certifiable, caveat=caveat)


# --------------------------------------------------------------------------------------
# 5 · power, envelope and cost
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Derived:
    """A metric's value with the two things that must travel beside it."""

    value: float
    contributors: tuple[str, ...]
    badge: Calibration


@dataclass(frozen=True)
class _Economics:
    """The scope-level numbers a rack declares: its limits and its money.

    Read off `hierarchy_scope` components, because a rack's envelope belongs to the rack
    and not to any part inside it. Every field falls back to the value that changes
    nothing — no overhead, no ceiling, no capex — so a system that declares no rack
    component behaves exactly as it did before P3 rather than acquiring invented limits.
    """

    overhead_fraction: float
    capex_usd: float
    amortization_years: float
    usd_per_kwh: float
    utilization: float
    max_kw: float | None
    cooling_cap_kw: float | None
    contributors: tuple[str, ...]
    badges: tuple[Calibration, ...]
    envelope_source: str | None
    envelope_conflict: str | None
    # Which economics inputs no component declared. Each fell back to a Python literal that
    # carries no SourcedValue. _power_and_cost explicitly floors TCO to STUB when any
    # are missing, because unrelated envelope/TDP evidence cannot justify these defaults.
    undeclared: tuple[str, ...] = ()
    overhead_source: SourcedValue | None = None
    overhead_contributor: str | None = None


def _economics(config: SystemConfig, instances: list[_Instance]) -> _Economics:
    """Collect the rack-level limits and prices, and say where the envelope came from.

    **Two places can declare an envelope, and that has to be resolved in the open.**
    `SystemConfig.power_envelope` is what the RUN declares; a `hierarchy_scope` component's
    `power_envelope_kw` is what the PART is rated for. The run's declaration wins — it is
    the more specific statement, and it is the one the builder edits — and when both exist
    and disagree the run says so rather than silently preferring one.
    """
    overhead = 0.0
    overhead_source = None
    overhead_contributor = None
    capex = 0.0
    amortization = 1.0
    usd_per_kwh = 0.0
    utilization = 1.0
    declared: set[str] = set()
    component_max_kw: float | None = None
    component_cooling_kw: float | None = None
    contributors: list[str] = []
    badges: list[Calibration] = []

    for instance in instances:
        cid = instance.component_id
        capex_param = instance.descriptor.params.get("capex_usd")
        if capex_param is not None:
            _require_unit(cid, "capex_usd", capex_param)
            declared.add("capex_usd")
            capex += capex_param.value * instance.count
            contributors.append(f"{cid}.capex_usd")
            badges.append(capex_param.provenance)
        if instance.descriptor.kind is not ComponentKind.HIERARCHY_SCOPE:
            continue
        for name, setter in (
            ("power_overhead_fraction", "overhead"),
            ("amortization_years", "amortization"),
            ("usd_per_kwh", "usd_per_kwh"),
            ("utilization", "utilization"),
            ("power_envelope_kw", "max_kw"),
            ("cooling_cap_kw", "cooling_kw"),
        ):
            param = instance.descriptor.params.get(name)
            if param is None:
                continue
            _require_unit(cid, name, param)
            declared.add(name)
            contributors.append(f"{cid}.{name}")
            badges.append(param.provenance)
            if setter == "overhead":
                overhead = param.value
                overhead_source = param
                overhead_contributor = f'{cid}.power_overhead_fraction'
            elif setter == "amortization":
                amortization = param.value
            elif setter == "usd_per_kwh":
                usd_per_kwh = param.value
            elif setter == "utilization":
                utilization = param.value
            elif setter == "max_kw":
                component_max_kw = param.value
            else:
                component_cooling_kw = param.value

    if config.economics is not None and config.economics.overhead_fraction is not None:
        overhead_source = config.economics.overhead_fraction
        overhead = overhead_source.value
        overhead_contributor = 'economics.overhead_fraction'
        contributors.append(overhead_contributor)
        badges.append(overhead_source.provenance)
        declared.add('power_overhead_fraction')
    envelope_source: str | None = None
    conflict: str | None = None
    max_kw = component_max_kw
    cooling_kw = component_cooling_kw
    if component_max_kw is not None or component_cooling_kw is not None:
        envelope_source = "the rack component's rating"
    if config.power_envelope is not None:
        declared_max = config.power_envelope.max_kw
        declared_cooling = config.power_envelope.cooling_cap_kw
        _require_unit(config.id, "power_envelope_kw", _as_kw(declared_max))
        _require_unit(config.id, "cooling_cap_kw", _as_kw(declared_cooling))
        contributors.extend(
            [f"{config.id}.power_envelope.max_kw", f"{config.id}.power_envelope.cooling_cap_kw"]
        )
        badges.extend([declared_max.provenance, declared_cooling.provenance])
        if component_max_kw is not None and component_max_kw != declared_max.value:
            conflict = (
                f"two envelopes disagree: the config declares max_kw="
                f"{declared_max.value} kW while a rack component is rated "
                f"{component_max_kw} kW. The config's declaration won, because it is what "
                f"this run asked for; the component's rating is what the part can take."
            )
        max_kw = declared_max.value
        cooling_kw = declared_cooling.value
        envelope_source = "SystemConfig.power_envelope"

    return _Economics(
        overhead_fraction=overhead,
        overhead_source=overhead_source,
        overhead_contributor=overhead_contributor,
        capex_usd=capex,
        amortization_years=amortization,
        usd_per_kwh=usd_per_kwh,
        utilization=utilization,
        max_kw=max_kw,
        cooling_cap_kw=cooling_kw,
        contributors=tuple(contributors),
        badges=tuple(badges),
        envelope_source=envelope_source,
        envelope_conflict=conflict,
        undeclared=tuple(
            name
            for name in (
                "power_overhead_fraction",
                "capex_usd",
                "amortization_years",
                "usd_per_kwh",
                "utilization",
            )
            if name not in declared
        ),
    )


def _as_kw(value: SourcedValue) -> SourcedValue:
    """`PowerEnvelope`'s fields are SourcedValues whose unit the schema does not pin.

    Returned unchanged; it exists so `_require_unit` has something to check and so the
    kW assumption is stated in one place rather than assumed in three.
    """
    return value


def _component_power_kw(instances: list[_Instance], warnings: list[str]) -> _Derived:
    """Sum of tdp x count over the tree, before overhead. kW."""
    tdp_by_count: list[tuple[float, int]] = []
    contributors: list[str] = []
    badges: list[Calibration] = []
    without_tdp: list[str] = []

    for instance in instances:
        tdp = instance.descriptor.params.get("tdp")
        if tdp is None:
            without_tdp.append(instance.component_id)
            continue
        _require_unit(instance.component_id, "tdp", tdp)
        tdp_by_count.append((tdp.value, instance.count))
        contributors.append(f"{instance.component_id}.tdp")
        badges.append(tdp.provenance)

    if without_tdp:
        warnings.append(
            f"{', '.join(sorted(without_tdp))} declare no tdp and contribute 0 W to "
            f"power_kw_per_rack. That is an omission, not a measurement of zero."
        )
    if not tdp_by_count:
        warnings.append(
            "no component in this system declares a tdp: power_kw_per_rack is 0.0 as a "
            "placeholder, not as a prediction, and energy_j_per_token inherits it."
        )
    return _Derived(
        value=f0_power.rack_power_kw(tdp_by_count),
        contributors=tuple(contributors),
        badge=combine(badges) if badges else Calibration.STUB,
    )


def _power_and_cost(
    instances: list[_Instance],
    economics: _Economics,
    throughput: float,
    warnings: list[str],
) -> tuple[_Derived, _Derived, _Derived, _Derived]:
    """Rack power (kW), energy per token (J/tok), $/Mtok and TCO ($/yr).

    Each comes back with its contributors and its badge, because a number that cannot say
    what fed it has no business leaving the engine.
    """
    component = _component_power_kw(instances, warnings)
    total_kw = f0_power.total_power_kw(component.value, economics.overhead_fraction)
    if economics.overhead_fraction == 0.0:
        warnings.append(
            "power_kw_per_rack includes NO node overhead: fans, PSU conversion loss, NICs "
            "and storage are unaccounted, because ADR 0006 §4 could not read a node-level "
            "figure out of a primary source and a guessed percentage would be worse than a "
            "stated omission. The sum is therefore wrong in two directions at once — TDP "
            "is a ceiling (too high) and the chassis is missing (too low)."
        )

    hourly_cost = 0.0
    cost_contributors: list[str] = []
    cost_badges: list[Calibration] = []
    for instance in instances:
        rate = instance.descriptor.params.get("usd_per_hr")
        if rate is None:
            continue
        _require_unit(instance.component_id, "usd_per_hr", rate)
        hourly_cost += rate.value * instance.count
        cost_contributors.append(f"{instance.component_id}.usd_per_hr")
        cost_badges.append(rate.provenance)

    if not cost_contributors:
        warnings.append(
            "no component in this system declares usd_per_hr: usd_per_mtok is 0.0 as a "
            "placeholder, not as a price. ADR 0006 §3 explains why an hourly rate is not "
            "sourceable — it needs a dated quote."
        )
    elif hourly_cost == 0.0:
        warnings.append(
            f"the declared usd_per_hr values ({', '.join(sorted(cost_contributors))}) sum "
            f"to 0.0, so usd_per_mtok is 0.0 — a placeholder, not a price. ADR 0006 §3: an "
            f"hourly rate needs a dated quote, which is why the demo's rates are stubs."
        )

    # The sum-of-TDP model is itself a contributor, at ESTIMATED: a datasheet TDP is a
    # ceiling ("Up to 700W", ADR 0006 §1.1), so a rack of spec_derived TDPs still does not
    # make a spec_derived prediction of draw. Combining can only weaken (invariant 3).
    overhead_sources = ([(economics.overhead_contributor, economics.overhead_source)]
        if economics.overhead_source is not None and economics.overhead_contributor is not None
        else [])
    power = _Derived(
        value=total_kw,
        contributors=(*component.contributors, f0_power.POWER_MODEL_CONTRIBUTOR,
                      *((overhead_sources[-1][0],) if overhead_sources else ())),
        badge=combine([component.badge, f0_power.POWER_MODEL_BADGE,
                       *([overhead_sources[-1][1].provenance] if overhead_sources else [])]),
    )
    energy = _Derived(
        value=f0_power.energy_j_per_token(power.value, throughput) if throughput > 0 else 0,
        contributors=power.contributors,
        badge=power.badge if throughput > 0 else Calibration.STUB,
    )
    cost = _Derived(
        value=f0_cost.usd_per_mtok(hourly_cost, throughput) if throughput > 0 else 0,
        contributors=tuple(cost_contributors),
        badge=combine(cost_badges) if cost_badges and throughput > 0 else Calibration.STUB,
    )
    tco_value = f0_cost.tco_usd_per_year(
        capex_usd=economics.capex_usd,
        amortization_years=economics.amortization_years,
        power_kw=power.value,
        usd_per_kwh=economics.usd_per_kwh,
        utilization=economics.utilization,
    )
    if economics.contributors:
        tco = _Derived(
            value=tco_value,
            contributors=(*economics.contributors, *power.contributors),
            badge=(Calibration.STUB if economics.undeclared
                   else combine([*economics.badges, power.badge])),
        )
        if economics.undeclared:
            warnings.append(
                f"tco_usd_per_year is STUB because {list(economics.undeclared)} are "
                f"UNDECLARED by any component. Its arithmetic uses engine defaults: "
                f"capex_usd and usd_per_kwh = 0.0, amortization_years = 1, utilization "
                f"= 1.0 and power_overhead_fraction = 0.0 where missing. These are "
                f"placeholders, not sourced economic evidence; power envelopes and TDP "
                f"cannot establish prices. Declare the missing inputs on a hierarchy_scope "
                f"component to make all inputs visible."
            )
        elif economics.capex_usd == 0.0 and economics.usd_per_kwh == 0.0:
            warnings.append(
                f"tco_usd_per_year returned 0.0 because declared capex_usd and "
                f"usd_per_kwh are both 0.0. The resulting badge is {tco.badge.value}; "
                f"the shipped library prices are STUB placeholders (ADR 0006 §3 — "
                f"a price needs a dated quote)."
            )
    else:
        # NO component declared capex, a power price, or an amortization period. The model
        # ran and returned 0.0 out of nothing, and `combine([])` badges exactly that case
        # STUB — a derived number that cannot name a single contributor has no evidence
        # behind it, and badging it ESTIMATED because the power term happened to be
        # ESTIMATED would be a badge improved by an accident of arithmetic.
        tco = _Derived(value=tco_value, contributors=(), badge=combine([]))
        warnings.append(
            "no component in this system declares capex_usd, usd_per_kwh or "
            "amortization_years, so tco_usd_per_year is 0.0 with no contributors at all — "
            "a placeholder, not a projection, and STUB-badged for exactly that reason. "
            "Slot a rack component carrying the economics to get a real TCO line."
        )
    return power, energy, cost, tco


def _envelope_warnings(
    power_kw: float, economics: _Economics, draw_badge: Calibration, *,
    busy_contributors: tuple[str, ...] | None = None,
) -> list[str]:
    """Envelope and cooling violations as prose. THE one implementation, two callers.

    `run()` appends these to `RunResult.warnings`; `validate_system()` returns them. A test
    asserts the two produce identical strings for the same config, so a second
    implementation cannot drift in unnoticed (ADR 0009 §5's rule, applied to a check
    instead of to a badge).

    `draw_badge` travels with the number for ADR 0027's reason: prose is the one surface
    where `<Badged>` is not there to state provenance, so the sentence states it itself.
    """
    warnings = [
        violation.as_warning(draw_badge, busy_contributors=busy_contributors)
        for violation in f0_power.check_envelope(
            power_kw, economics.max_kw, economics.cooling_cap_kw
        )
    ]
    if economics.envelope_conflict is not None:
        warnings.append(economics.envelope_conflict)
    if economics.max_kw is None and economics.cooling_cap_kw is None:
        warnings.append(
            f"no power envelope is declared, so the modelled draw of {power_kw:.3f} kW "
            f"[provenance: {draw_badge.value}] was not checked against anything. That "
            f"is not the same as passing: an unchecked "
            f"configuration and a configuration within its limits look identical in every "
            f"other output. Declare SystemConfig.power_envelope, or slot a rack component "
            f"that carries power_envelope_kw and cooling_cap_kw."
        )
    return warnings


def _declared_power_limit(config: SystemConfig, instances: list[_Instance],
                          name: str, param: str) -> tuple[str, Metric | None]:
    """Resolve limit evidence with the same config-over-rack precedence everywhere."""
    path = f'system.power_envelope.{name}'
    source = None
    if config.power_envelope is not None:
        source = getattr(config.power_envelope, name)
    else:
        for instance in instances:
            if (instance.descriptor.kind is ComponentKind.HIERARCHY_SCOPE
                    and param in instance.descriptor.params):
                source = instance.descriptor.params[param]
                path = f'system.root.components[{instance.component_id}].params.{param}'
    return path, (None if source is None else Metric(
        value=source.value, unit='kW', badge=source.provenance, contributors=(path,)))


def _busy_subtotal_warnings(config: SystemConfig, instances: list[_Instance],
                            subtotal: Metric) -> list[str]:
    """A known subtotal can prove a modelled violation, never a complete-draw pass."""
    warnings = []
    subtotal_kw = f0_power.w_to_kw(subtotal.value)
    for name, param in (('max_kw', 'power_envelope_kw'), ('cooling_cap_kw', 'cooling_cap_kw')):
        _, limit = _declared_power_limit(config, instances, name, param)
        if (limit is None or limit.badge is Calibration.STUB
                or subtotal.badge is Calibration.STUB or subtotal_kw <= limit.value):
            continue
        warnings.append(
            f'POWER ENVELOPE VIOLATED: the known busy-draw subtotal is '
            f'{subtotal_kw:.3f} kW [provenance: {subtotal.badge.value}] against a declared '
            f'{param} of {limit.value:.3f} kW [provenance: {limit.badge.value}]. '
            f'Draw contributors: {", ".join(subtotal.contributors)}. '
            f'Limit contributors: {", ".join(limit.contributors)}. '
            'Missing/STUB additive draw terms can only add to this model subtotal. '
            'Complete rack power remains unavailable; this is not a measured breach. '
            'The run was NOT clamped.')
    return warnings


# --------------------------------------------------------------------------------------
# 6 · the lifecycle
# --------------------------------------------------------------------------------------


def _running_accelerators(instances: list[_Instance]) -> list[_Instance]:
    """The accelerators that actually run the roofline. THE one definition of "how many".

    Role AND effective compute fidelity, both. A component overridden to compute STUB is one
    the user asked us to claim nothing about, so it produces no throughput and cannot host a
    shard — and it therefore must not be counted when `tp x pp` is checked against the
    hardware.

    **This function exists because `run()` and `validate_system()` counted differently, and
    so reached opposite verdicts on the same config** (P14 S2 finding B1). `run()` filtered
    on fidelity; `validate_system()` filtered on role alone, so a system whose accelerators
    were stubbed out validated clean and then raised on Run. That is precisely the builder
    failure mode build-spec §5 boundary 2 asks `validate_system()` to prevent, so the count
    is defined once, here, and both callers read it.
    """
    return [
        i
        for i in instances
        if i.descriptor.role is ComponentRole.ACCELERATOR
        and i.fidelity.compute is not ComputeFidelity.STUB
    ]


def _accelerators(instances: list[_Instance], config: SystemConfig) -> list[_Instance]:
    """The devices the C0 roofline runs on, or a refusal saying why there are none.

    Effective fidelity, not role, decides: a component the config overrides to compute
    STUB is one the user asked us to claim nothing about, and quietly costing it anyway
    would make the warning `_fidelity_map` emits untrue.
    """
    running = _running_accelerators(instances)
    if not running:
        stubbed = sorted(
            i.component_id
            for i in instances
            if i.descriptor.role is ComponentRole.ACCELERATOR
        )
        if stubbed:
            raise EngineError(
                f"system {config.id!r} has accelerators ({', '.join(stubbed)}) but every "
                f"one of them is overridden to compute fidelity STUB, so nothing is left "
                f"for the C0 roofline to run on. Stubbing the only device that can "
                f"produce throughput does not produce a throughput of zero — it produces "
                f"no answer, which is why this is an error and not a warning."
            )
        raise EngineError(
            f"system {config.id!r} has no component with role=accelerator, so there is "
            f"nothing for the C0 roofline to run on."
        )
    if len(running) > 1:
        listed = ", ".join(sorted(i.component_id for i in running))
        raise EngineError(
            f"system {config.id!r} mixes {len(running)} accelerator types ({listed}). "
            f"The C0 roofline models one homogeneous device; a heterogeneous placement is "
            f"a scheduling question, and scheduling is the R1 DES's (P5)."
        )
    return running


def _slotted_roles(
    config: SystemConfig, components: Mapping[str, ComponentDescriptor]
) -> tuple[tuple[str, ComponentRole], ...]:
    """(component_id, role) for every instance the config slots and the library holds."""
    return tuple(
        (cid, components[cid].role) for cid in config.component_ids() if cid in components
    )


def _memory_roof_unscaled_ids(accelerators: list[_Instance]) -> tuple[str, ...]:
    """Which running accelerators leave the memory roof unscaled. See the warning template.

    Keyed on `ScalarEfficiency` rather than on `memory_efficiency == 1.0`, and the
    distinction is the whole warning: a `SplitEfficiency` that someone deliberately
    declares as 1.0 has made a claim and badged it, while a `ScalarEfficiency` has made no
    claim at all and gets 1.0 by default. Same arithmetic, different epistemic status, and
    only the second one is an omission worth saying out loud.
    """
    return tuple(
        sorted(
            {
                instance.component_id
                for instance in accelerators
                if isinstance(instance.descriptor.execution_model, ScalarEfficiency)
            }
        )
    )


def _stub_capacity_warnings(
    view: _MemoryView, fit: f0_memory.CapacityFit
) -> list[str]:
    """Say when a capacity PASS was decided by a number nobody sourced. S2 finding F3.

    **THE GATE IS A BOOLEAN, AND A BADGE CANNOT TRAVEL ON A BOOLEAN.** Everywhere else in
    this engine an unsourced input weakens the metric it feeds, and the reader sees a grey
    chip. `capacity_fit` returns pass/fail, so a `cxl_pool` whose `capacity_gb` is
    `provenance: stub` can turn MEMORY CAPACITY EXCEEDED — a HARD config error, build-spec
    §1.3 — into a passing run, with every parameter correctly badged and nothing anywhere
    going grey. That is `_memory_view`'s own finding-B3 defect arriving by a second route.

    **THE DECISION (ADR 0019): the stub capacity COUNTS, and the pass says what it rests on.**
    Lane B offered two options and had no view between them. Excluding stub-badged capacity
    from the pool was rejected because it answers "we do not know how big this tier is" with
    "it does not fit", which is a different claim and a confident one — and it is a claim
    the engine would make about a part the user deliberately slotted. Counting it and
    saying so keeps the engine's answer to the question actually asked while refusing to
    let the answer look better-evidenced than it is.

    **QUANTIFIED, not "rests on a stub".** The warning re-runs the verdict with the
    unsourced tiers removed. Only the case that actually changes the answer gets the loud
    sentence, so a system with plenty of sourced headroom and one stubbed tier is not
    nagged about a number that decided nothing — which is the difference between a warning
    a reader acts on and one they learn to scroll past.
    """
    if not view.stub_capacity_ids:
        return []
    named = ", ".join(view.stub_capacity_ids)
    sourced_bytes = fit.available_bytes - view.stub_capacity_bytes
    if fit.required_bytes <= sourced_bytes:
        return [
            f"{named} contribute {view.stub_capacity_bytes / 1e9:.1f} GB of "
            f"UNSOURCED capacity to the check above (provenance: stub). The verdict does "
            f"not depend on them — the run still fits in the "
            f"{sourced_bytes / 1e9:.1f} GB that is sourced — so this is a note, not a "
            f"warning."
        ]
    return [
        f"THIS CONFIGURATION FITS ONLY BECAUSE OF UNSOURCED CAPACITY. {named} declare "
        f"{view.stub_capacity_bytes / 1e9:.1f} GB with provenance: stub, and without them "
        f"the run needs {fit.required_bytes / 1e9:.1f} GB against "
        f"{sourced_bytes / 1e9:.1f} GB sourced — short by "
        f"{(fit.required_bytes - sourced_bytes) / 1e9:.1f} GB. A capacity failure is a HARD "
        f"config error (build-spec §1.3) and this one was averted by a placeholder. The "
        f"gate is a pass/fail, so no badge can carry that fact and this sentence is the "
        f"only thing that does. Source those capacities, or treat this system as unproven "
        f"rather than as fitting. ADR 0019."
    ]


def _capacity_shortfall_is_fatal(
    fit: f0_memory.CapacityFit, runtime_level: RuntimeFidelity
) -> bool:
    """Is a capacity shortfall a hard config error, or a ceiling the scheduler enforces?

    ADR 0025 splits one claim into two, because `CapacityFit` was already carrying them
    apart:

    * **Weights must fit at every level.** No scheduler rescues a model with no room to be
      resident, and this is the case build-spec §1.3 means.
    * **KV sized at `max_batch x prompt_tokens` is a worst-case OCCUPANCY assumption.** At
      R1 the DES enforces its block pool at admission and never reaches that state, so
      refusing on it answers a narrower question than the one asked — ADR 0019's rule,
      applied in the other direction. At R0 there is nothing to enforce it and `batch` IS
      the reported steady state, so it stays fatal.
    """
    if fit.weight_bytes > fit.available_bytes:
        return True
    return runtime_level is not RuntimeFidelity.R1


def _capacity_warnings(
    view: _MemoryView,
    workload: WorkloadSpec,
    seq_len_tokens: int,
    batch: int,
    replicas: int,
    plan: ExecutionPlan,
    runtime_level: RuntimeFidelity = RuntimeFidelity.R0,
) -> tuple[list[str], f0_memory.CapacityFit | None]:
    """The M0 capacity check, as prose. Returns ([], None) when memory ran at STUB.

    A capacity failure is a HARD config error (build-spec §1.3) and `run()` raises on it.
    It is reported here as a message so `validate_system()` could return the same sentence
    if it ever had a workload to compute one with — which it does not, deliberately: item
    8's "NOT capacity fit" is exactly this, because weight residency and KV sizing need a
    ModelSpec and faking one with a default model would answer a question nobody asked.
    """
    if not view.tiers:
        return [], None
    fit = f0_memory.capacity_fit(
        workload.model,
        view.tiers,
        seq_len_tokens,
        batch,
        plan.precision,
        replicas=replicas,
    )
    warnings: list[str] = []
    if not fit.fits:
        shortfall = (
            f"{replicas} replica(s) need {fit.required_bytes / 1e9:.1f} GB "
            f"({fit.weight_bytes / 1e9:.1f} GB of resident weights at total_params, "
            f"{fit.kv_bytes / 1e9:.1f} GB of KV at batch={batch} x "
            f"{seq_len_tokens} tokens) and the declared tiers "
            f"({', '.join(fit.tiers)}) hold {fit.available_bytes / 1e9:.1f} GB. Short "
            f"by {-fit.headroom_bytes / 1e9:.1f} GB."
        )
        if _capacity_shortfall_is_fatal(fit, runtime_level):
            return [f"MEMORY CAPACITY EXCEEDED: {shortfall}"], fit
        # ADR 0025: the weights fit and the DES enforces the KV pool at admission, so the
        # only thing that does not fit is an assumption the modelled runtime never makes.
        return (
            [
                f"KV CEILING EXCEEDED, AND THE RUN PROCEEDED: {shortfall} The weights fit "
                f"({fit.weight_bytes / 1e9:.1f} GB of "
                f"{fit.available_bytes / 1e9:.1f} GB); what does not is the M0 pre-flight "
                f"sizing, which assumes all {batch} slots of max_batch are occupied at "
                f"{seq_len_tokens} tokens at once. The R1 DES enforces the KV block pool at "
                f"ADMISSION and so never reaches that state, which is why this is a ceiling "
                f"rather than a gate here — at R0, with nothing to enforce it, the same "
                f"shortfall is a hard error. Read the DES's own KV warnings for what it "
                f"actually admitted (ADR 0025)."
            ],
            fit,
        )
    growth = (
        "growth across the generated tokens is not modelled at R0, so a run that fits here "
        "can still run out mid-generation"
        if runtime_level is not RuntimeFidelity.R1
        else "the R1 DES accounts KV growth per token against its own block pool, so this "
        "pre-flight sizing is a ceiling check and the DES's admission control is what "
        "actually enforces it"
    )
    warnings.append(
        f"M0 capacity check passed: {fit.required_bytes / 1e9:.1f} GB needed against "
        f"{fit.available_bytes / 1e9:.1f} GB declared across {', '.join(fit.tiers)} "
        f"({fit.utilization:.1%} used). Weights are sized at total_params and KV at a FIXED "
        f"context of {seq_len_tokens} tokens — {growth}."
    )
    warnings.extend(_stub_capacity_warnings(view, fit))
    if view.slottable_ids:
        warnings.append(
            f"the slottable memory tiers ({', '.join(view.slottable_ids)}) contribute their "
            "capacity to the fit. P7 places KV HBM-first, then in a declared CXL tier; "
            "its latency knob adds a spill-fraction penalty to decode. DDR placement "
            "and memory queues remain unmodelled."
        )
    named = tuple(plan.kv.placement_order)
    if named and view.on_package_ids and named != ("hbm",):
        warnings.append(
            f"execution_plan.kv.placement_order names {list(named)}, and M0 does not act on "
            f"it: every KV byte is charged against the aggregate capacity above regardless "
            f"of the order. The field is read and not used, which is stated here rather "
            f"than left to be discovered."
        )
    return warnings, fit


# --------------------------------------------------------------------------------------
# 5b · runtime R1 — the serving DES (P5)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _RuntimeChoice:
    """Which runtime level this run executes at, and what decided it.

    ADR 0011 §1's resolution rule, applied to the one axis that is a property of the RUN
    rather than of a part: `instance.fidelity ?? system.fidelity`. A system that slots a
    `kind: runtime` component takes that component's effective level, because that is the
    serving stack whose behaviour is being simulated; a system that slots none falls
    through to the system default, which is how every scenario written before P5 keeps
    resolving to exactly the level it always did.

    `decided_by` is carried so the fidelity-map warning can name the component, rather
    than saying "R1" and leaving the reader to find out where it came from.
    """

    level: RuntimeFidelity
    decided_by: str | None


def _runtime_choice(instances: list[_Instance], config: SystemConfig) -> _RuntimeChoice:
    """The effective runtime level for the run. Dispatch reads this and nothing else.

    **Dispatch is on the LEVEL, never on "does f1 exist yet".** R0 and R1 are both built
    (build-spec §2.3.2), both have a registry row with a model behind it, and the
    serving-stack library entry declares `fidelity_available: [R0, R1]` so a user picks per
    component instance. An R0 run after P5 returns exactly the analytical numbers it
    returned before P5.
    """
    stacks = [i for i in instances if i.descriptor.kind is ComponentKind.RUNTIME]
    if not stacks:
        return _RuntimeChoice(level=config.fidelity.runtime, decided_by=None)
    if len(stacks) > 1:
        listed = ", ".join(sorted(i.component_id for i in stacks))
        raise EngineError(
            f"system {config.id!r} slots {len(stacks)} serving stacks ({listed}). A run "
            f"executes one scheduler, so two stacks would need a rule for which requests "
            f"go to which — that is a placement question, and placement is deferred "
            f"(ADR 0011 §2). Slot one."
        )
    return _RuntimeChoice(level=stacks[0].fidelity.runtime, decided_by=stacks[0].component_id)


@dataclass(frozen=True)
class _Number:
    """A metric's value with the interval the replications produced, or None for both."""

    value: float
    ci95_low: float | None
    ci95_high: float | None

    @classmethod
    def scaled(cls, estimate: f1_serving.Estimate, factor: float) -> _Number:
        """One `Estimate` in the metric's unit: `factor` is 1e3 for ms, `replicas` for tok/s."""
        return cls(
            value=estimate.value * factor,
            ci95_low=None if estimate.ci95_low is None else estimate.ci95_low * factor,
            ci95_high=None if estimate.ci95_high is None else estimate.ci95_high * factor,
        )


@dataclass(frozen=True)
class _Served:
    """The five numbers the DES replaces, plus the run it got them from."""

    ttft_p50_ms: _Number
    ttft_p99_ms: _Number
    tpot_p50_ms: _Number
    tpot_p99_ms: _Number
    throughput_output_tok_per_s: _Number
    result: f1_serving.ServingResult
    episodes: tuple[f1_agentic.EpisodeReplication, ...] = ()


def _agentic_host(config: SystemConfig, plan: ExecutionPlan, workload: WorkloadSpec,
                  instances: list[_Instance], runtime: _RuntimeChoice) -> Metric | None:
    """Resolve the finite core-equivalent pool; shared by preflight and execution."""
    if workload.workload_class is not WorkloadClass.AGENTIC:
        return None
    if runtime.level is not RuntimeFidelity.R1:
        raise EngineError('agentic workloads require R1; analytical episodes are unsupported')
    if workload.agentic_profile is None or workload.episode_horizon_s is None:
        raise EngineError('agentic workloads require agentic_profile and episode_horizon_s')
    devices = sum(i.count for i in _running_accelerators(instances))
    devices_per_replica, replicas, problem = _replica_shape(plan, devices)
    if problem:
        raise EngineError(problem)
    if replicas != 1:
        raise EngineError('agentic execution currently requires exactly one accelerator replica; '
                          'representative-replica extrapolation cannot report exact episode counts')
    if config.vcpus_per_gpu is not None:
        return Metric(value=config.vcpus_per_gpu * devices_per_replica, unit='count',
                      badge=Calibration.ESTIMATED,
                      contributors=('system.vcpus_per_gpu', 'input.composition',
                                    'model.runtime.r1.host_core_equivalents'))
    cpus = [i for i in instances if i.descriptor.role is ComponentRole.CPU]
    if not cpus or any('cores' not in i.descriptor.params for i in cpus):
        raise EngineError('agentic host capacity requires vcpus_per_gpu or sourced CPU cores')
    values = [i.descriptor.params['cores'] for i in cpus]
    if any(v.unit != 'count' or v.value <= 0 or not v.value.is_integer() for v in values):
        raise EngineError('host CPU cores must be positive integers with unit count')
    return Metric(value=sum(v.value * i.count for i, v in zip(cpus, values, strict=True)),
                  unit='count', badge=combine([Calibration.ESTIMATED,
                                              *(v.provenance for v in values)]),
                  contributors=(*(f'{i.component_id}.cores' for i in cpus),
                                'model.runtime.r1.host_core_equivalents'))


def _episode_metrics(runs: tuple[f1_agentic.EpisodeReplication, ...], badge: Calibration,
                     contributors: tuple[str, ...], warnings: list[str]) -> EpisodeMetrics | None:
    if not runs:
        return None
    empty = any(not r.samples for r in runs)
    if empty:
        warnings.append('At least one replication has no completed episodes inside the horizon; '
                        'episode latency and decomposition are unavailable zero STUB placeholders, '
                        'not percentiles. Started and completed counts remain distinct.')
    warnings.append('Episode counts are means across replications. Episode latency uses completed '
                    'episodes only; censoring at the horizon can bias latency downward. The four '
                    'terms are completed-episode mean shares scaled to E2E p50, then averaged '
                    'across replications. Scaled remote wait can vary with the p50/mean ratio '
                    'or completion censoring even when each episode\'s raw wait is unchanged.')
    metrics = {}
    for name, estimate in f1_agentic.episode_estimates(runs).items():
        no_samples = empty and not name.startswith('episodes_')
        metrics[name] = Metric(
            value=estimate.value, unit='count' if name.startswith('episodes_') else 'ms',
            badge=Calibration.STUB if no_samples else badge,
            contributors=(*contributors, 'model.runtime.r1.agentic.no_completed_samples')
                         if no_samples else contributors,
            ci95_low=estimate.ci95_low, ci95_high=estimate.ci95_high)
    return EpisodeMetrics(**metrics)


def _kv_pool_bytes_per_replica(
    view: _MemoryView, workload: WorkloadSpec, plan: ExecutionPlan, replicas: int
) -> float | None:
    """Bytes one replica has left for KV after its weights are resident. None at memory STUB.

    P7 admits KV against HBM plus declared CXL capacity. Weights must remain in
    HBM; `_spill_inputs` enforces that prerequisite. DDR is not a KV placement
    tier. The shared F0 iteration cost charges the declared CXL spill latency.

    Divided by `replicas` for the same reason `capacity_fit` multiplies by it: each replica
    holds its own weights and its own cache, and the tiers are the system's total.
    """
    on_package = tuple(tier for tier in view.tiers if tier.name in view.on_package_ids)
    if not on_package:
        return None
    total_bytes = sum(tier.capacity_bytes for tier in view.tiers
                      if tier.name in (*view.on_package_ids, *view.cxl_ids))
    weights = f0_memory.weight_residency_bytes(workload.model, plan.precision.compute)
    return total_bytes / replicas - weights


def _serve(
    plan: ExecutionPlan,
    workload: WorkloadSpec,
    aggregate: _Aggregate,
    accelerator: Accelerator,
    memory_view: _MemoryView,
    network: _NetworkView,
    requests: RequestStream,
    seed: int,
    warnings: list[str],
    dvfs: DvfsParameters | None = None,
    hbm_kv_bytes: float | None = None,
    spill_latency_s: float = 0.0,
    host_cores: float | None = None,
) -> _Served:
    """Run the R1 DES and turn its replications into the five numbers R0 computed directly.

    **The DES is handed ten floats and never sees the model.** `iteration_cost` lifts the
    roofline's coefficients out of exactly the same `accelerator` and `precision` the
    analytical path used, so f1/ cannot re-derive a FLOP count (CLAUDE.md invariant 8) and
    the two paths cannot disagree about what an iteration costs.
    tests/unit/test_iteration_cost.py is what keeps that true.

    The collective arrives as two COEFFICIENTS and not as the analytical path's two
    constants, because the analytical constants are priced at `max_batch` and a DES
    iteration is usually much smaller — see `_CollectiveCoefficients`, and ADR 0018 §2 for
    the 58x this was measured to be worth.
    """
    coefficients = _collective_coefficients(network, workload, plan)
    cost = iteration_cost(
        workload.model,
        accelerator,
        plan.precision,
        tp=plan.parallelism.tp,
        collective_fixed_s=coefficients.fixed_s,
        collective_s_per_message_token=coefficients.s_per_message_token,
    )
    cost = replace(cost, dvfs=dvfs, hbm_kv_bytes=hbm_kv_bytes,
                   spill_latency_s=spill_latency_s)

    pool_bytes = _kv_pool_bytes_per_replica(
        memory_view, workload, plan, aggregate.replicas
    )
    bytes_per_block = cost.kv_byte_per_context_token * plan.kv.block_size
    kv_pool_blocks: int | None
    if pool_bytes is None:
        kv_pool_blocks = None
        warnings.append(
            "the R1 DES ran with an UNBOUNDED KV pool: no component declares on-package "
            "memory this run could size one from, so admission was never blocked by "
            "capacity and no request was ever preempted. Every queueing delay below is "
            "batch-slot and scheduler contention only. Declare memory: M0 on an "
            "accelerator carrying hbm_capacity to get the real pool — KV pressure is one "
            "of the two things this level exists to show."
        )
    else:
        kv_pool_blocks = int(pool_bytes // bytes_per_block)
        if kv_pool_blocks < 1:
            weight_gb = (
                f0_memory.weight_residency_bytes(workload.model, plan.precision.compute)
                / 1e9
            )
            raise EngineError(
                f"after {weight_gb:.1f} GB of resident weights, each replica has "
                f"{pool_bytes / 1e9:.1f} GB left for KV — less than one "
                f"{plan.kv.block_size}-token block ({bytes_per_block / 1e6:.1f} MB at "
                f"precision.kv_cache={plan.precision.kv_cache.value}). A serving stack that "
                f"can hold no KV at all can admit nothing, so there is no latency to report."
            )

    params = f1_serving.ServingParams(
        cost=cost,
        max_batch=plan.batching.max_batch,
        max_tokens_in_flight=plan.batching.max_tokens_in_flight,
        block_size_tokens=plan.kv.block_size,
        kv_pool_blocks=kv_pool_blocks,
    )
    # THE DES SIMULATES ONE REPLICA, SO IT MUST BE OFFERED ONE REPLICA'S ARRIVALS.
    # `requests` is the stream offered to the WHOLE system, and the throughput below is
    # multiplied by `replicas` — so handing the whole stream to one simulated replica and
    # then crediting it N times reports both a latency N replicas' load produces and a
    # throughput N times what the workload contains. P14 S3 lane A finding F6, ADR 0028.
    served_stream = _one_replicas_share(requests, aggregate.replicas)
    episode_runs: tuple[f1_agentic.EpisodeReplication, ...] = ()
    try:
        if workload.agentic_profile is not None:
            assert host_cores is not None and workload.episode_horizon_s is not None
            episode_runs = tuple(f1_agentic.simulate_episode(
                served_stream(seed + i), params, workload.agentic_profile, host_cores,
                workload.episode_horizon_s, seed + i) for i in range(workload.replications))
            result = f1_serving.summarize(tuple(r.serving for r in episode_runs))
        else:
            result = f1_serving.replicate(served_stream, params, seed, workload.replications)
    except f1_serving.ServingError as exc:
        raise EngineError(f"the R1 serving simulation will not run: {exc}") from exc

    if result.total_completed_requests == 0 and not episode_runs:
        raise EngineError(
            "the R1 simulated replica completed no requests in any replication. "
            "An empty stream or a small stream routed entirely to other replicas has "
            "no latency or positive throughput to report. Use a larger workload or "
            "inspect the replica allocation."
        )
    _warn_about_what_the_des_saw(result, params, plan, aggregate.replicas, warnings)

    return _Served(
        ttft_p50_ms=_Number.scaled(result.ttft_p50_s, 1e3),
        ttft_p99_ms=_Number.scaled(result.ttft_p99_s, 1e3),
        tpot_p50_ms=_Number.scaled(result.tpot_p50_s, 1e3),
        tpot_p99_ms=_Number.scaled(result.tpot_p99_s, 1e3),
        # PER REPLICA out of the DES, multiplied here — the same scaling R0 applies, and
        # for the same reason: each replica runs its own scheduler over its own batch.
        throughput_output_tok_per_s=_Number.scaled(
            result.throughput_output_tok_per_s, float(aggregate.replicas)
        ),
        result=result,
        episodes=episode_runs,
    )


def _one_replicas_share(stream: RequestStream, replicas: int) -> RequestStream:
    """The arrivals ONE replica sees, out of a stream offered to the whole system.

    THE SPLIT IS THE LOAD BALANCER, AND IT HAS TO EXIST SOMEWHERE. `WorkloadSpec` declares
    one arrival process for the system; `f1` simulates one replica and knows nothing about
    how many there are; and `_serve` multiplies the result by `replicas`. Without a split
    in between, a 4-replica system reported 1.69x the output tokens its own workload
    contained while reporting the p50 TTFT of a single replica absorbing all four replicas'
    arrivals — two numbers in one result that contradict each other. P14 S3 lane A finding
    F6; ADR 0028 carries the reproduction.

    RANDOM ASSIGNMENT, NOT ROUND-ROBIN, and the difference is the whole tail. Splitting a
    Poisson process by assigning each arrival independently and uniformly to one of N
    replicas yields N independent Poisson processes of rate lambda/N — the thinning
    property — so the sub-stream this returns has the SHAPE the workload declared, at the
    rate one replica actually sees. Round-robin would hand replica 0 every Nth arrival,
    whose interarrival gaps are Erlang-N: smoother than Poisson, and smoother in exactly
    the direction that flatters a p99. R1 exists to show the tail, so the tail is the one
    thing the split may not quietly improve.

    WHAT THIS MODELS, STATED SO IT IS NOT MISTAKEN FOR MORE. A perfect stateless random
    balancer over identical replicas with independent queues. It does not model
    least-loaded routing (which would be better than this), session affinity or a hot
    shard (both worse), or any cross-replica scheduling — `_warn_about_what_the_des_saw`
    says so on every multi-replica run rather than leaving it here.

    `replicas == 1` returns the caller's own factory unchanged, so a single-replica run
    draws exactly the arrivals it drew before this function existed and no committed
    number moves.
    """
    if replicas <= 1:
        return stream

    def share(replication_seed: int) -> Iterable[f1_serving.Request]:
        # A SECOND DRAW FROM THE SAME SEED WOULD BE THE SAME DRAW. The stream was built
        # from `replication_seed`, so `default_rng(replication_seed)` here would walk the
        # identical bit sequence and correlate each arrival's gap with its own routing
        # decision. Seeding from the pair puts the balancer on an independent SeedSequence
        # stream while keeping the whole thing a pure function of the run's seed
        # (CLAUDE.md invariants 4 and 5).
        rng = np.random.default_rng([replication_seed, _LOAD_BALANCER_SEED_STREAM])
        return (
            request
            for request in stream(replication_seed)
            if int(rng.integers(replicas)) == 0
        )

    return share


def _warn_about_what_the_des_saw(
    result: f1_serving.ServingResult,
    params: f1_serving.ServingParams,
    plan: ExecutionPlan,
    replicas: int,
    warnings: list[str],
) -> None:
    """Say what the scheduler actually did, in the numbers a reader would otherwise infer.

    Blocked admissions and preemptions are not warnings about a defect — they are the run
    reporting the mechanism behind its own tail. A p99 TTFT that is high because the KV
    pool ran out and a p99 that is high because `max_batch` is small are the same number
    and different problems, and only one of them is fixed by buying memory.
    """
    first = result.first
    blocked = result.total_blocked_admissions
    if params.kv_pool_blocks is not None:
        peak = max(first.timeline.kv_blocks_in_use, default=0)
        warnings.append(
            f"the R1 KV pool held {params.kv_pool_blocks} blocks of "
            f"{params.block_size_tokens} tokens ({params.kv_bytes_per_block / 1e6:.1f} MB "
            f"each at precision.kv_cache={plan.precision.kv_cache.value}) per replica, and "
            f"had a sampled maximum of {peak} in use "
            f"({peak / params.kv_pool_blocks:.1%}) in replication zero. Admission "
            f"blocked {blocked} time(s) and {result.total_preemptions} request(s) were "
            f"preempted (largest-KV victim, recomputed on re-admission). Prefix reuse is "
            f"NOT modelled, so every block is charged to exactly one request — a real "
            f"stack sharing a system prompt across a batch would fit more."
        )
    if replicas > 1:
        warnings.append(
            f"the DES simulated ONE of {replicas} replicas: the workload's arrival stream "
            f"was split across them by a stateless uniform random balancer, this replica's "
            f"share was simulated, and its throughput was multiplied by {replicas}. The "
            f"split preserves the declared arrival process (thinning a Poisson stream "
            f"leaves a Poisson stream at 1/{replicas} the rate), so the tail below is one "
            f"replica's real tail and not a smoothed one. What is NOT modelled: "
            f"least-loaded or affinity routing, a hot shard, and any cross-replica "
            f"scheduling — a real balancer is worse than uniform random in some of those "
            f"directions and better in others, so read this as the balanced case rather "
            f"than as a bound in either direction."
        )
    if any(not replication.completed_requests for replication in result.replications):
        warnings.append(
            "At least one simulated replication completed no requests. The existing "
            "TTFT/TPOT and throughput aggregation includes its zero placeholders, so "
            "those estimates do not describe populated replicas alone. Request E2E is "
            "unavailable; use a larger workload before interpreting these estimates."
        )
    if first.completed_requests and not first.tpot_s:
        warnings.append(
            "no TPOT sample exists: every request generated a single token, which comes "
            "out of prefill, so there is no inter-token gap to measure. tpot_p50_ms and "
            "tpot_p99_ms are 0.0 as a consequence of the workload, not as a measurement."
        )


@dataclass(frozen=True)
class _CoreRun:
    result: RunResult
    episodes: tuple[f1_agentic.EpisodeReplication, ...]


def _run_core(
    config: SystemConfig, plan: ExecutionPlan, workload: WorkloadSpec, seed: int, *,
    components: Mapping[str, ComponentDescriptor], requests: RequestStream | None = None,
) -> RunResult:
    """Private metrics-only entry point; resolve legacy inputs before P7 accounting."""
    if config.economics is None:
        from rk.engine.economics_runtime import prepare
        try:
            resolved, components = prepare(config, components)
        except ValueError as exc:
            raise EngineError(str(exc)) from exc
        config = resolved.system
    return _simulate_core(config, plan, workload, seed,
                          components=components, requests=requests).result


def _simulate_core(
    config: SystemConfig,
    plan: ExecutionPlan,
    workload: WorkloadSpec,
    seed: int,
    *,
    components: Mapping[str, ComponentDescriptor],
    requests: RequestStream | None = None,
) -> _CoreRun:
    """Run one configuration and return its nine metrics, badged.

    config       WHERE — the scope tree, its components and the fidelity levels asked for
    plan         HOW — parallelism, batching, KV policy, collectives
    workload     WHAT — model architecture, request source, SLO, replications
    seed         every randomness source in the engine takes it. R0 has none; at R1 it
                 seeds the arrival streams — replication i is drawn at `seed + i`
    components   the library, already read from disk by rk/components/loader.py. Passed in
                 rather than loaded here, because the engine does no I/O
    requests     `seed -> Iterable[(arrival_time_s, prompt_tokens, output_tokens)]`, and
                 **required at runtime R1**. See below.

    **WHY THE REQUEST STREAM IS AN ARGUMENT AND NOT SOMETHING THIS MODULE BUILDS.**
    rk/README.md layers the package strictly: *"`calibration` and `workloads` sit beside
    `engine` and may import it; `engine` may never import them."* Every generator and
    loader that can produce an arrival stream lives in `rk/workloads/` — lane B's — and the
    arrival process is theirs to own, so a Poisson generator living under `rk/engine/`
    would be a workload added by touching engine code, which is precisely what the
    iterator contract exists to avoid (rk/workloads/README.md). The stream therefore
    arrives as a FACTORY over the seed, `rk/cli.py` wires lane B's generator into it, and
    `tests/unit/test_engine_layering.py` asserts the import ban is still real rather than
    a comment. An R1 run without one is refused by name — it is not run at R0 instead.

    Raises `UnimplementedFidelity` rather than answering a different question than the one
    asked, and `EngineError` for a config this engine cannot run at all. Everything it
    *can* run but runs crudely comes back in `RunResult.warnings`.
    """
    # -- validate ----------------------------------------------------------------------
    _check_fidelity_is_implemented(config.fidelity, f"system {config.id!r}")

    # Validated inputs require a declared point for traces (ADR 0037). Keep a named
    # failure for callers bypassing Pydantic validation with model_copy/model_construct.
    try:
        point = workload.analytical_lengths
    except ValueError as exc:
        raise EngineError(str(exc)) from exc

    instances = _flatten(config, components)
    for instance in instances:
        if instance.override is not None:
            _check_fidelity_is_implemented(
                instance.fidelity,
                f"component {instance.component_id!r}",
                compute_stub_ok=True,
            )

    # WHICH RUNTIME LEVEL ACTUALLY RUNS. `instance.fidelity ?? system.fidelity`, resolved
    # once, read by the dispatch below and by every warning that differs between the two
    # levels. Dispatch is on the LEVEL and never on "does f1 exist yet".
    runtime = _runtime_choice(instances, config)

    host = _agentic_host(config, plan, workload, instances, runtime)

    # ADR 0011 §3, option (a): on-package memory is never a slottable part, and slotting it
    # is an error rather than an addition. Runs before anything sums a capacity.
    try:
        f0_memory.reject_on_package_slots(_slotted_roles(config, components))
    except f0_memory.OnPackageMemorySlotted as exc:
        raise EngineError(str(exc)) from exc

    accelerators = _accelerators(instances, config)
    accelerator_instance = accelerators[0]
    accelerator, compute_contributors, compute_badge = _accelerator(
        accelerator_instance, plan.precision
    )

    # -- resolve the fidelity map ------------------------------------------------------
    # The network view is built FIRST, because the map may not report N0 for a component
    # that priced nothing and only the view knows which those are (finding B4).
    outcomes = _outcomes(instances)
    network_view = _network_view(instances, outcomes)
    fidelity_map, warnings = _fidelity_map(
        instances,
        outcomes,
        frozenset(i.component_id for i in accelerators),
        network_view,
        runtime,
        host_cpu_ids=frozenset(i.component_id for i in instances
                              if host is not None and config.vcpus_per_gpu is None
                              and i.descriptor.role is ComponentRole.CPU),
    )

    # R0 has no distribution, so metrics 2-5 come back in identical pairs. Emitting that
    # silently is the single worst bug this repo can ship, so it leads the warnings on
    # every R0 run — INCLUDING every R0 run after P5 (build-spec §2.3.3). P5 made this
    # conditional on the level that actually ran; it did not remove it. An R1 run leads
    # with `_R1_PERCENTILE_ESTIMATE_WARNING` instead, inserted once the DES has run and
    # can say how many replications and requests are behind the number.
    if runtime.level is not RuntimeFidelity.R1:
        warnings.insert(0, _P50_P99_WARNING)

    # These two DESCRIBE the system default; they do not dispatch on it. Every model
    # dispatch below reads `instance.fidelity` — the effective map — and the fidelity map
    # rows are built from that (ADR 0011 §1, and P3 item 9's "grep for config.fidelity when
    # you are done"). What these decide is which SENTENCE the run says about itself, and
    # "you declared STUB" and "you declared N0 and slotted nothing for it to price" are
    # different situations that need different advice.
    memory_is_stub = config.fidelity.memory is MemoryFidelity.STUB
    network_is_stub = config.fidelity.network is NetworkFidelity.STUB
    if memory_is_stub and network_is_stub:
        warnings.append(_MEMORY_NETWORK_STUB_WARNING)
    elif memory_is_stub:
        warnings.append(
            "memory ran at STUB: there is no KV-capacity check, so weights and KV are "
            "assumed to fit whatever the system declares. M0 is built (P3) — declare it."
        )
    elif network_is_stub:
        warnings.append(
            "network ran at STUB: every transfer between devices is free, including the "
            "collectives tensor parallelism pays for. N0 is built (P3) — declare it."
        )

    # ADR 0015. Two claims the run would otherwise make silently: which precision produced
    # these numbers, and that the memory roof was not scaled by anything.
    if plan.precision != Precision():
        warnings.append(
            _NON_FP16_PRECISION_WARNING.format(
                compute=plan.precision.compute.value,
                kv_cache=plan.precision.kv_cache.value,
            )
        )
    unscaled = _memory_roof_unscaled_ids(accelerators)
    if unscaled:
        warnings.append(_MEMORY_ROOF_UNSCALED_WARNING.format(ids=", ".join(unscaled)))

    if workload.trace_ref is not None:
        warnings.append(
            f"analytical_point declares prompt_tokens={point.prompt_tokens}, "
            f"output_tokens={point.output_tokens} [provenance: user-declared workload "
            f"inputs, not measured hardware]; the trace did not choose these lengths. "
            f"They size the analytical roofline, collective terms, R0 cycle throughput "
            f"and M0 KV ceiling at max_batch={plan.batching.max_batch}. R0 latency uses "
            f"this declared point; the R1 DES uses each trace request's own lengths and "
            f"arrivals. No direction of error is claimed (ADR 0037)."
        )

    # -- dispatch and aggregate --------------------------------------------------------
    if config.vcpus_per_gpu is not None and host is None:
        warnings.append('vcpus_per_gpu declares host allocation for the P8a handoff; '
                        'P7 models no host CPU queue or host-latency effect.')
    memory_view = _memory_view(
        instances, outcomes, frozenset(i.component_id for i in accelerators)
    )

    _, replica_count, shape_problem = _replica_shape(plan, sum(i.count for i in accelerators))
    if shape_problem:
        raise EngineError(shape_problem)
    hbm_kv_bytes, spill_latency_s = _spill_inputs(
        memory_view, instances, workload, plan, replica_count)
    dvfs = config.economics.dvfs if config.economics else None
    if dvfs is not None:
        dvfs_sources = [getattr(dvfs, name) for name in type(dvfs).model_fields
                        if getattr(dvfs, name) is not None]
        compute_badge = combine([compute_badge, Calibration.ESTIMATED,
                                 *(source.provenance for source in dvfs_sources)])
        compute_contributors += tuple(f'economics.dvfs.{name}'
                                      for name in type(dvfs).model_fields
                                      if getattr(dvfs, name) is not None)
    if hbm_kv_bytes is not None:
        # HBM capacity selects the spill fraction, including the no-spill branch.
        # Retain the existing conservative slottable-tier provenance floor.
        spill_sources = [(f'{i.component_id}.{name}', value)
                         for i in instances
                         for name, value in i.descriptor.params.items()
                         if (i.component_id in memory_view.on_package_ids
                             and name == 'hbm_capacity')
                         or (i.component_id in memory_view.slottable_ids
                             and name in {'capacity_gb', 'latency_ns', 'added_latency_ns'})]
        compute_badge = combine([compute_badge, *(v.provenance for _, v in spill_sources)])
        compute_contributors += tuple(name for name, _ in spill_sources)

    aggregate = _dispatch_and_aggregate(
        plan,
        workload,
        accelerator,
        accelerator_count=sum(i.count for i in accelerators),
        network=network_view,
        network_is_stub=network_is_stub,
        runtime_level=runtime.level,
        warnings=warnings,
        dvfs=dvfs, hbm_kv_bytes=hbm_kv_bytes, spill_latency_s=spill_latency_s,
    )

    capacity_warnings, fit = _capacity_warnings(
        memory_view,
        workload,
        point.prompt_tokens,
        aggregate.batch,
        aggregate.replicas,
        plan,
        runtime_level=runtime.level,
    )
    if (
        fit is not None
        and not fit.fits
        and _capacity_shortfall_is_fatal(fit, runtime.level)
    ):
        # build-spec §1.3: "capacity failures are hard config errors". Not a warning, and
        # not a slower answer — a configuration that cannot hold its own weights has no
        # performance to report. Since ADR 0025 the KV half of that sum is a CEILING at R1
        # rather than a gate, because the DES enforces the block pool at admission; the
        # predicate is where the two cases are told apart.
        raise EngineError(capacity_warnings[0])
    warnings.extend(capacity_warnings)
    if memory_view.excluded_ids:
        warnings.append(
            f"{', '.join(memory_view.excluded_ids)} declare on-package memory that was NOT "
            f"added to the capacity pool, because they run no model in this run — a "
            f"role=asic part, or an accelerator overridden to compute STUB. Their HBM is "
            f"real and it is not memory the executing devices can address, so counting it "
            f"would declare the model resident in memory nothing running it can reach "
            f"(ADR 0011 §3's composition error, by a different route)."
        )
    if not memory_is_stub and not memory_view.tiers:
        warnings.append(
            "memory fidelity is M0 but no component in this system declares memory the "
            "model can read, so no capacity check ran. An accelerator carries its own "
            "hbm_capacity/hbm_bw (ADR 0011 §3) and a ddr or cxl_pool tier carries "
            "capacity_gb/bw_gb_per_s; this system has neither."
        )

    # -- runtime R1: the DES, after the capacity gate has had its say ------------------
    # After, deliberately: a configuration that cannot hold its own weights has no
    # performance to report at either level, and raising that first means an R1 run and an
    # R0 run refuse the same config with the same sentence.
    served = None
    if runtime.level is RuntimeFidelity.R1:
        if requests is None:
            raise EngineError(
                "runtime fidelity is R1, and no request stream was supplied. The DES "
                "consumes an iterator of (arrival_time_s, prompt_tokens, output_tokens) "
                "and the engine may not build one itself — every generator and loader "
                "lives in rk/workloads/, which rk/engine/ may not import (rk/README.md). "
                "Pass requests=<seed -> stream>; `rk run` wires "
                "rk.workloads.generators.poisson_stream in for a synthetic workload. This "
                "is refused rather than quietly answered at R0, which would report an "
                "analytical number under R1's name (build-spec §2.4)."
            )
        served = _serve(
            plan,
            workload,
            aggregate,
            accelerator,
            memory_view,
            network_view,
            requests,
            seed,
            warnings,
            dvfs=dvfs, hbm_kv_bytes=hbm_kv_bytes, spill_latency_s=spill_latency_s,
            host_cores=None if host is None else host.value,
        )
        if workload.generator is not None and host is not None:
            warnings.append('Synthetic Poisson arrivals are episode arrivals; initial prompt and '
                            'per-turn output lengths come from the generator. Turns grow context '
                            'and draw profile durations independently from the replication seed. '
                            'The feedback-driven LLM turn arrivals are not declared Poisson.')
        elif workload.generator is not None:
            # SYNTHETIC ONLY. A trace's arrivals are real recorded timestamps and warning
            # about them would be false; `_exactly_one_request_source` makes this gate
            # exact without a new flag (P5 item 3).
            warnings.append(
                _SYNTHETIC_STREAM_WARNING.format(
                    rate=workload.generator.arrival_rate_req_per_s,
                    prompt=workload.generator.prompt_tokens,
                    output=workload.generator.output_tokens,
                )
            )
        warnings.insert(
            0,
            _R1_PERCENTILE_ESTIMATE_WARNING.format(
                replications=workload.replications,
                requests=served.result.first.completed_requests,
                interval=(
                    _R1_NO_INTERVAL
                    if workload.replications < 2
                    else _R1_INTERVAL_IS_NORMAL
                ),
            ),
        )
        if workload.trace_ref is not None and host is not None:
            warnings.append('Trace timestamps and initial lengths are replayed as episode inputs. '
                            'Seeded profile turns and durations still vary across replications; '
                            'their intervals describe input sampling, not hardware accuracy.')
        elif workload.trace_ref is not None:
            warnings.append(
                "Trace replications replay the same recording without resampling: a "
                "single replica is deterministic and a zero-width interval does not "
                "establish accuracy or population uncertainty. With multiple replicas, "
                "seeded routing can change the selected replica's requests; its interval "
                "describes routing variation, not hardware uncertainty or model accuracy."
            )
        # The SLO is checked against the DES's REAL p99 rather than against an analytical
        # p50 wearing a p99's name — which is the sentence `_warn_about_the_slo` has been
        # apologising for since P1b.
        # Check sample eligibility before emitting either a verdict or its prose.
        # A provisional comparison against zero placeholders must not survive as
        # a "MET" warning after the agentic verdict becomes unavailable.
        if host is not None and any(
            target is not None and any(not getattr(r, samples)
                                       for r in served.result.replications)
            for target, samples in ((workload.slo.ttft_p99_ms, 'ttft_s'),
                                    (workload.slo.tpot_p99_ms, 'tpot_s'))
        ):
            caveat = ('Agentic request SLO is unavailable: at least one replication has no '
                      'samples for a requested latency target inside the horizon.')
            slo_verdict = SloVerdict(certifiable=False, caveat=caveat)
            warnings.append(caveat)
        else:
            slo_verdict = _warn_about_the_slo(
                workload,
                served.ttft_p99_ms.value,
                served.tpot_p99_ms.value,
                warnings,
                runtime_level=runtime.level,
            )
    else:
        slo_verdict = aggregate.slo

    for warning in _scope_role_problems(config):
        warnings.append(warning)
    # F2: the collective above may have been priced over a link in a node holding no
    # accelerator. One computation, two behaviours — `validate_system()` says it before
    # there is a workload, and the run says it beside the number it affected.
    for warning in _link_placement_problems(config, components):
        warnings.append(warning)
    # F13: a system with no host at all. Structural, so it is the same sentence
    # `validate_system()` emits while the user is still editing.
    warnings.extend(_hostless_system_problems(config, components))

    economics = _economics(config, instances)
    # energy_j_per_token and usd_per_mtok are power-or-price DIVIDED BY THROUGHPUT, so
    # they have to divide by the throughput this run actually reports. Feeding them the
    # analytical figure on an R1 run would put an R0 denominator under an R1 headline.
    throughput = (
        aggregate.throughput_output_tok_per_s
        if served is None
        else served.throughput_output_tok_per_s.value
    )
    power, energy, cost, tco = _power_and_cost(
        instances, economics, throughput, warnings
    )
    if config.economics is None or config.economics.power_model == 'tdp_ceiling':
        warnings.extend(_envelope_warnings(power.value, economics, power.badge))

    serving_overrides = _serving_override_warning(instances)
    if serving_overrides is not None:
        warnings.append(serving_overrides)

    # -- propagate badges --------------------------------------------------------------
    # Worst-of-contributors, every time, and never improved on the way out (invariant 3).
    # The network's badge joins the latency and throughput metrics because the collective
    # time is now part of them: at N0 with a stubbed link, a latency is no better than the
    # link parameters that priced its all-reduce.
    #
    # A network that priced nothing contributes NOTHING, not a STUB. "No collective was
    # charged" is a fidelity fact and it is reported in the warnings and in the fidelity
    # map; routing it into `combine()` would badge a latency worse because of the LEVEL it
    # ran at, and fidelity and calibration are separate axes (CLAUDE.md invariant 10,
    # ADR 0011 §5.4). Only a network that actually fed the number may weaken it.
    # build-spec §2.3.5 asks for the all-to-all multiplier badged ESTIMATED *by name*. It
    # is added only when a MoE all-to-all was actually charged — a contributor that names a
    # term the run did not compute is the finding-B4 defect in miniature.
    moe_contributors: tuple[str, ...] = ()
    moe_charged = (
        aggregate.collectives.moe_prefill_s > 0.0
        or aggregate.collectives.moe_decode_step_s > 0.0
    )
    if moe_charged:
        moe_contributors = (f0_fabric.MOE_MODEL_CONTRIBUTOR,)

    # AT R1 THE SERVING STACK'S OWN PARAMETERS JOIN THE LATENCY BADGE, because at R1 they
    # fed it: the scheduler this run simulated is the one that component declares. P5 item
    # 5's "badged worst-of (serving params, compute inputs)", and it can only ever weaken
    # (invariant 3). At R0 nothing reads the serving entry — the run says so separately in
    # `_serving_override_warning` — so nothing of it enters here, which is the same
    # finding-B4 rule the network view follows: only a component that actually fed the
    # number may weaken it.
    serving_contributors, serving_badges = _serving_stack_provenance(
        instances, runtime, served is not None
    )
    if served is not None and runtime.decided_by is None:
        # Said out loud as well as badged. The badge stops the number from getting BETTER
        # for having less behind it; this sentence is how a reader learns why a run they
        # asked for at R1 is graded as though nothing described its scheduler. ADR 0028.
        warnings.append(
            f"runtime R1 ran on a system that slots NO serving stack, so the "
            f"continuous-batching scheduler this DES simulated — FCFS admission, a KV "
            f"block pool, largest-KV preemption — is not declared by any component here. "
            f"The level came from the system fidelity default. Its parameters were taken "
            f"from the ExecutionPlan (batching, kv) and the shape from the engine, so the "
            f"latency and throughput carry {_UNNAMED_SCHEDULER_CONTRIBUTOR} at "
            f"provenance: stub and can be graded no better. Slot a runtime component "
            f"declaring fidelity_available: [R0, R1] to say which stack this is."
        )

    latency_contributors = (
        *compute_contributors,
        *network_view.contributors,
        *moe_contributors,
        *serving_contributors,
    )
    network_badges = [compute_badge, network_view.badge]
    if moe_contributors:
        network_badges.append(f0_fabric.FABRIC_MODEL_BADGE)
    latency_badge = combine(
        [
            *(network_badges if network_view.contributors else [compute_badge]),
            *serving_badges,
        ]
    )

    if host is not None:
        profile = workload.agentic_profile
        assert profile is not None
        latency_contributors = (*latency_contributors, *host.contributors, *profile.contributors,
                                'model.runtime.r1.agentic.uniform_partial_iteration')
        latency_badge = combine([latency_badge, host.badge, profile.badge])
        warnings.extend([
            'Agentic execution uses an ideal processor-sharing host core-equivalent pool '
            '[provenance: estimated model; parameter badges propagate]. CPU residence includes '
            'sharing slowdown; remote wait consumes no host CPU or accelerator. '
            'Host power retains the declared ceiling/static model; no CPU utilization law exists.',
            'Agentic request TTFT, TPOT and request E2E describe individual LLM turns. '
            'Episode latency is in RunResult.episodes. No prompt or tool-result caching is '
            'modelled, so llm_ms is pessimistic wherever a real deployment caches. '
            'No retries or episode failures are modelled, so episode counts are optimistic '
            'against a stack with a failure rate; counts do not measure successful tasks.',
            'Agentic measurement ends at drain or the declared horizon, whichever comes first. '
            'Partial iterations charge a '
            'linear elapsed fraction of F0 work/energy [provenance: estimated uniform progress], '
            'without completing a token. Idle GPU time includes remote waits.',
        ])
        if config.vcpus_per_gpu is not None:
            warnings.append('Explicit vcpus_per_gpu allocation overrides installed CPU core '
                            'inventory as ideal core-equivalents; SMT and physical host placement '
                            'are not modelled [provenance: estimated].')
        if profile.split_provenance is Calibration.STUB:
            warnings.append('The CPU/remote-wait split is assumed, not measured '
                            '[provenance: stub]; adding cores cannot shorten remote waits.')
        if profile.second_model_as_tool:
            warnings.append('A second model\'s forward pass is charged as tool time, not '
                            'contention for shared HBM bandwidth; generation TPOT is optimistic '
                            'when that model is co-located [provenance: estimated assumption].')

    def compute_metric(unit: str, reported: tuple[float, _Number | None]) -> Metric:
        value, interval = reported
        return Metric(
            value=value,
            unit=unit,
            badge=latency_badge,
            contributors=latency_contributors,
            ci95_low=None if interval is None else interval.ci95_low,
            ci95_high=None if interval is None else interval.ci95_high,
        )

    # R0's four latency fields are one number reported twice; R1's are four different
    # numbers with intervals. `served is None` is the only place that choice is made.
    latency: dict[str, tuple[float, _Number | None]] = (
        {
            "ttft_p50_ms": (aggregate.ttft_ms, None),
            "ttft_p99_ms": (aggregate.ttft_ms, None),
            "tpot_p50_ms": (aggregate.tpot_ms, None),
            "tpot_p99_ms": (aggregate.tpot_ms, None),
            "throughput_output_tok_per_s": (aggregate.throughput_output_tok_per_s, None),
        }
        if served is None
        else {
            "ttft_p50_ms": (served.ttft_p50_ms.value, served.ttft_p50_ms),
            "ttft_p99_ms": (served.ttft_p99_ms.value, served.ttft_p99_ms),
            "tpot_p50_ms": (served.tpot_p50_ms.value, served.tpot_p50_ms),
            "tpot_p99_ms": (served.tpot_p99_ms.value, served.tpot_p99_ms),
            "throughput_output_tok_per_s": (
                served.throughput_output_tok_per_s.value,
                served.throughput_output_tok_per_s,
            ),
        }
    )

    # Built once and read twice: by the result, and by the SLO verdict, which must carry
    # the same objects rather than a second copy of the same values (ADR 0036 §1).
    latency_metrics: dict[str, Metric] = {
        "throughput_output_tok_per_s": compute_metric(
            "tok/s", latency["throughput_output_tok_per_s"]
        ),
        "ttft_p50_ms": compute_metric("ms", latency["ttft_p50_ms"]),
        "ttft_p99_ms": compute_metric("ms", latency["ttft_p99_ms"]),
        "tpot_p50_ms": compute_metric("ms", latency["tpot_p50_ms"]),
        "tpot_p99_ms": compute_metric("ms", latency["tpot_p99_ms"]),
    }
    if host is not None and served is not None:
        for name, samples in (('ttft', 'ttft_s'), ('tpot', 'tpot_s')):
            if any(not getattr(r, samples) for r in served.result.replications):
                for quantile in ('p50', 'p99'):
                    key = f'{name}_{quantile}_ms'
                    latency_metrics[key] = latency_metrics[key].model_copy(update={
                        'badge': Calibration.STUB,
                        'contributors': (*latency_contributors, 'model.runtime.r1.no_samples')})
    # Stamp after no-sample overrides. A shared prose slot uses the weakest final
    # metric grade, so prose can never be stronger than any latency it quotes.
    _stamp_latency_provenance(warnings, min(m.badge for m in latency_metrics.values()))
    slo_verdict = _stamp_slo_actuals(slo_verdict, latency_metrics)

    request_e2e: RequestE2E | None
    if served is None:
        request_e2e = RequestE2E(
            kind="analytical",
            analytical_ms=compute_metric("ms", (
                aggregate.ttft_ms + (point.output_tokens - 1) * aggregate.tpot_ms, None
            )),
        )
        warnings.append(
            "Request E2E is an analytical duration at the declared lengths: prefill "
            "emits the first token, followed by output_tokens - 1 decode steps at fixed "
            "context. It excludes arrival/queueing delays and context growth; it is not "
            "a percentile and has no confidence interval (ADR 0038)."
        )
    elif served.result.e2e_p50_s is None or served.result.e2e_p99_s is None:
        request_e2e = None
        warnings.append(
            "Request E2E is unavailable: at least one simulated replication completed "
            "no requests, so it has no completion samples. A zero latency or an "
            "interval formed by dropping that replication would be misleading."
        )
    else:
        e2e_p50 = _Number.scaled(served.result.e2e_p50_s, 1e3)
        e2e_p99 = _Number.scaled(served.result.e2e_p99_s, 1e3)
        request_e2e = RequestE2E(
            kind="simulated",
            p50_ms=compute_metric("ms", (e2e_p50.value, e2e_p50)),
            p99_ms=compute_metric("ms", (e2e_p99.value, e2e_p99)),
        )

    if served is not None and served.episodes and config.economics is None:
        raise EngineError('episode normalization requires resolved economics')
    power_diagnostic, busy_draw, busy_subtotal = _p7_power(
        config, plan, workload, instances, accelerator,
        aggregate, served, hbm_kv_bytes, spill_latency_s, power, latency_badge,
        latency_contributors, network_view)
    if config.economics is not None and config.economics.power_model != 'tdp_ceiling':
        from rk.schema.channels import Available
        if isinstance(busy_draw, Available):
            warnings.extend(_envelope_warnings(f0_power.w_to_kw(busy_draw.metric.value),
                economics, busy_draw.metric.badge,
                busy_contributors=busy_draw.metric.contributors))
        else:
            warnings.append('Power/cooling envelope busy draw is unavailable: ' + busy_draw.reason)
            if busy_subtotal is not None:
                warnings.extend(_busy_subtotal_warnings(config, instances, busy_subtotal))
    diagnostics = build_diagnostics(
        config, plan, workload, accelerator_instance.component_id,
        aggregate.prefill, aggregate.decode, network_view.link,
        (aggregate.collectives.total_prefill_s, aggregate.collectives.total_decode_step_s),
        compute_badge, compute_contributors, network_view.badge, network_view.contributors,
    )
    if served is not None:
        diagnostics = integrate_runtime(diagnostics, served.result.replications,
                                        config, plan, workload, network_view.link,
                                        latency_badge, latency_contributors)
    result = RunResult(
        episodes=_episode_metrics(() if served is None else served.episodes,
                                  latency_badge, latency_contributors, warnings),
        power_diagnostic=power_diagnostic,
        diagnostics=diagnostics,
        request_e2e=request_e2e,
        runtime_timeline=(None if served is None else _runtime_timeline(
            served.result.first, aggregate.replicas, instances, memory_view,
            latency_badge, latency_contributors,
        )),
        throughput_output_tok_per_s=latency_metrics["throughput_output_tok_per_s"],
        ttft_p50_ms=latency_metrics["ttft_p50_ms"],
        ttft_p99_ms=latency_metrics["ttft_p99_ms"],
        tpot_p50_ms=latency_metrics["tpot_p50_ms"],
        tpot_p99_ms=latency_metrics["tpot_p99_ms"],
        power_kw_per_rack=Metric(
            value=power.value, unit="kW", badge=power.badge, contributors=power.contributors
        ),
        # Energy and cost are both power-or-price divided by throughput, so both inherit
        # the roofline's contributors and cannot be badged better than it.
        energy_j_per_token=Metric(
            value=energy.value,
            unit="J/tok",
            badge=combine([energy.badge, latency_badge]),
            contributors=(*energy.contributors, *latency_contributors),
        ),
        usd_per_mtok=Metric(
            value=cost.value,
            unit="USD/Mtok",
            badge=combine([cost.badge, latency_badge]),
            contributors=(*cost.contributors, *latency_contributors),
        ),
        tco_usd_per_year=Metric(
            value=tco.value,
            unit="USD/yr",
            badge=tco.badge,
            contributors=tco.contributors,
        ),
        warnings=tuple(warnings),
        slo=slo_verdict,
        fidelity_map=fidelity_map,
        seed=seed,
        replications=workload.replications,
        engine_version=ENGINE_VERSION,
        config_hash=config.config_hash,
        plan_hash=plan.plan_hash,
        workload_hash=workload.workload_hash,
    )
    return _CoreRun(result, () if served is None else served.episodes)


def _serving_stack_provenance(
    instances: list[_Instance],
    runtime: _RuntimeChoice,
    des_ran: bool,
) -> tuple[tuple[str, ...], list[Calibration]]:
    """The serving stack's contributors and badges, and only when the DES actually ran.

    Returns `((), [])` at R0 — where nothing in the engine reads a serving-stack parameter
    — and everything the stack declares at R1. A contributor naming a param the run did
    not read is the finding-B4 defect; so is a badge weakened by one.

    ALL of its params, not a chosen subset: the scheduler this level simulates is that
    component's, and its `kv_block_size` is as much a claim about the stack as the
    `kernel_efficiency` overrides are. Every one of them is `provenance: stub` today (see
    the library YAML's header, which says why and that it stays that way), so an R1 run's
    latency badge is STUB — as an R0 run's already is, for the accelerator's own reasons.

    AND A SYSTEM WITH NO SERVING STACK AT ALL IS THE WEAKEST CASE, NOT THE STRONGEST.
    Until P14 S3 lane A finding F12 this returned `((), [])` for it, so deleting the stack
    from a system left the DES running, the millisecond identical, and the badge one rung
    BETTER — `estimated` where the stack's stub params had made it `stub`. That is
    CLAUDE.md invariant 3 exactly backwards: it rewarded removing the component that
    carries the uncertainty. The scheduler does not stop being simulated when nothing
    describes it; it stops being NAMED, which is strictly less evidence, so the run
    contributes `_UNNAMED_SCHEDULER_CONTRIBUTOR` at STUB and says so in prose. ADR 0028.
    """
    if not des_ran:
        return (), []
    if runtime.decided_by is None:
        return (_UNNAMED_SCHEDULER_CONTRIBUTOR,), [_UNNAMED_SCHEDULER_BADGE]
    stack = next(i for i in instances if i.component_id == runtime.decided_by)
    contributors = tuple(
        f"{stack.component_id}.{name}" for name in sorted(stack.descriptor.params)
    )
    badges = [value.provenance for value in stack.descriptor.params.values()]
    if stack.descriptor.execution_model is not None:
        badges.extend(
            v.provenance for _, v in stack.descriptor.execution_model.sourced_values
        )
    return contributors, badges


def _serving_override_warning(instances: list[_Instance]) -> str | None:
    """Announce a serving stack's kernel_efficiency overrides, which nothing applies.

    P3 asks which wins when a serving override and a compute_resource's `execution_model`
    both apply. The answer this engine implements: **the compute_resource's own
    `execution_model`, always** — nothing reads the serving entry's overrides, because
    selecting one needs a (vendor, model_class) pair and the schema has neither field.
    Matching on a substring of a component id would be the engine deciding by accident,
    which is precisely what must not happen.

    An input accepted, read by nothing and announced by nothing is finding F5's shape
    (ADR 0011 §2). So it is announced. Retiring this needs `vendor` on
    `ComponentDescriptor` and `model_class` on `ModelSpec` — a schema PR at a sprint
    boundary with both founders (ADR 0003 §8), proposed rather than taken here.
    """
    declaring = sorted(
        instance.component_id
        for instance in instances
        if instance.descriptor.kind is ComponentKind.RUNTIME
        and any(name.startswith("kernel_efficiency") for name in instance.descriptor.params)
    )
    if not declaring:
        return None
    return (
        f"{', '.join(declaring)} declares per-(vendor, model_class) kernel_efficiency "
        f"overrides, and NOTHING APPLIED THEM. The accelerator's own execution_model is "
        f"the only efficiency the roofline read. Selecting an override needs a vendor and "
        f"a model class, and ComponentDescriptor has no `vendor` field and ModelSpec no "
        f"`model_class` — matching on a substring of a component id would be the engine "
        f"choosing by accident. The overrides are declarative until that schema change "
        f"lands; this line exists so they are not silently authoritative."
    )


# --------------------------------------------------------------------------------------
# 7 · validate_system — the engine's second public function (build-spec §5, boundary 2)
# --------------------------------------------------------------------------------------


def _degradation_warnings(instances: list[_Instance]) -> list[str]:
    """Which axes will degrade, said before a run rather than only after one.

    `validate_system()`'s half of S2 cross-lane item 2. It cannot raise — the builder calls
    it on a system the user is mid-edit on — so the one case `_outcomes` DOES raise on, an
    explicit per-instance override the component cannot honour, is caught and reported as
    the sentence it would have raised. That is the module's standing rule applied once
    more: `run()` refuses, `validate_system()` reports, from one computation.
    """
    try:
        outcomes = _outcomes(instances)
    except UnimplementedFidelity as exc:
        return [
            f"this system cannot be run as written: {exc} Reported here rather than raised "
            f"because the system is being validated, not run; orchestrator.run() on these "
            f"same inputs raises UnimplementedFidelity with the same sentence."
        ]

    degraded: list[str] = []
    structural: list[str] = []
    for instance in instances:
        specific, structural_pairs = _degradations(instance, outcomes[instance.component_id])
        degraded.extend(specific)
        structural.extend(structural_pairs)
    return _degradation_summary(degraded, structural)


def validate_system(
    config: SystemConfig,
    components: Mapping[str, ComponentDescriptor],
    plan: ExecutionPlan | None = None,
) -> list[str]:
    """Everything wrong with a system that can be known WITHOUT a workload. Never raises.

    config       the system being edited
    components   the loaded library
    plan         optional. Supplied, the plan-versus-system checks run too.

    Returns warnings in a stable order — group (a) first, then group (b) — so a UI can
    diff two calls and a test can compare wording.

    **Why this returns rather than raises, and why that is not a softer standard.** The S3
    builder (P4b) validates a system the user is mid-edit on, before there is a workload to
    run it against. Reducing a node below what `tp` asks for is the single most likely edit
    anyone makes, and a stack trace is not an answer to it. `run()` still raises on exactly
    the same condition, from exactly the same computation — `_replica_shape` — because a
    run that cannot shard a model across devices that are not there has no number to
    report. One rule, two behaviours, deliberately.

    **(a) With config alone**
      * component ids the library does not hold
      * on-package memory slotted as a standalone part (ADR 0011 §3)
      * **per-axis fidelity degradation: which components will run below the level the
        system default asks for, and why.** Added in S3 at lane B's request (S2's
        `docs/reviews/S2-lane-B-response.md`, Cross-lane item 2): the resolved level used to
        exist only inside a `RunResult`, so the Builder could only show the truth AFTER a
        run and its fidelity chip over-claimed until then. The sentences are the ones
        `run()` emits, from `_degradation_summary` — one computation, two behaviours.
      * the power envelope: a TDP sum against a ceiling needs no workload and no plan
      * scope-role validity: a root that is not a rack, a rack nested inside a node
      * **link placement: a link slotted in a scope that holds no accelerator**, which N0
        will nonetheless price a tensor-parallel collective over (P14 S3 lane B, F2). Added
        at lane B's request in S3 — the builder cannot add a check of its own (P4b), so a
        borrowed link was invisible until this sentence existed

    **(b) With a plan supplied**
      * `parallelism.tp * parallelism.pp` against the accelerator count

    **NOT capacity fit, and that omission is deliberate.** Weight residency needs
    `total_params` and KV sizing needs the whole `ModelSpec`, so capacity stays in `run()`
    where the workload exists. Faking it with a default model would answer a question
    nobody asked, in the one place a user is most likely to trust the answer.

    Nothing in S2 consumes this beyond its unit test: it is the seam P4b builds on, and
    lane B may not reach into `rk/engine/` to write it themselves (build-spec §5).
    """
    warnings: list[str] = []

    # -- (a) config alone --------------------------------------------------------------
    missing = _missing_component_ids(config, components)
    if missing:
        warnings.append(_missing_components_message(config, missing))

    try:
        f0_memory.reject_on_package_slots(_slotted_roles(config, components))
    except f0_memory.OnPackageMemorySlotted as exc:
        warnings.append(str(exc))

    warnings.extend(_scope_role_problems(config))
    warnings.extend(_link_placement_problems(config, components))
    warnings.extend(_hostless_system_problems(config, components))

    # The envelope check needs the instances, which need every id to resolve. When some do
    # not, the draw would be computed over a subset and would understate itself — so it is
    # skipped and said to be skipped, rather than reported as a number that is quietly
    # missing a component.
    if missing:
        warnings.append(
            "the power envelope was NOT checked, because the components above are missing "
            "from the library and their draw cannot be counted. A sum over what happens to "
            "resolve would understate the rack and would look like a passing check."
        )
        return warnings

    # **EVERYTHING BELOW IS GUARDED, BECAUSE THIS FUNCTION PROMISES NOT TO RAISE.**
    # `_economics` and `_component_power_kw` both call `_require_unit`, which raises on a
    # library YAML whose param is in the wrong unit — and the LOADER does not check units,
    # only the engine does, so a perfectly loadable library is a live vector (P14 S2
    # finding B2). The builder is this function's caller and cannot handle an exception, so
    # the refusal becomes a warning here and stays a raise in `run()`: same rule, two
    # behaviours, which is this function's whole contract.
    try:
        instances = _flatten(config, components)
        warnings.extend(_degradation_warnings(instances))
        economics = _economics(config, instances)
        swallowed: list[str] = []
        component = _component_power_kw(instances, swallowed)
        total_kw = f0_power.total_power_kw(component.value, economics.overhead_fraction)
        # The SAME badge `_power_and_cost` puts on `power_kw_per_rack`, and not
        # `component.badge` alone: the sum-of-TDP model is itself a contributor at
        # ESTIMATED, so the draw can never be better graded than that. Passing the
        # component's own badge here would print a grade STRONGER than the metric's in the
        # one sentence ADR 0027 added to state the grade — invariant 3, inside the fix for
        # invariant 2. `test_validate_system_returns_the_very_text_the_run_produces` is
        # what catches it, which is the reason that test compares strings and not shapes.
        draw_badge = combine([component.badge, f0_power.POWER_MODEL_BADGE])
        warnings.extend(_envelope_warnings(total_kw, economics, draw_badge))
    except EngineError as exc:
        warnings.append(
            f"this system cannot be costed or power-checked as written: {exc} The power "
            f"envelope was NOT checked. orchestrator.run() raises EngineError on these same "
            f"inputs; validation reports it instead, because a system being edited has to "
            f"stay renderable."
        )
        return warnings

    # -- (b) with a plan ---------------------------------------------------------------
    if plan is not None:
        # THE SAME COUNT `run()` USES — `_running_accelerators`, not a role filter. See
        # that function: counting differently here is what made the two disagree.
        accelerator_count = sum(i.count for i in _running_accelerators(instances))
        _, _, problem = _replica_shape(plan, accelerator_count)
        if problem is not None:
            warnings.append(
                f"{problem} This is returned as a warning rather than raised because the "
                f"system is being validated, not run; orchestrator.run() on these same "
                f"inputs raises EngineError with the same sentence."
            )
    return warnings


# Full-input front door for direct evaluation and future sweeps. ADR 0039.
def preflight(
    config: SystemConfig,
    plan: ExecutionPlan,
    workload: WorkloadSpec,
    *,
    components: Mapping[str, ComponentDescriptor],
) -> PhysicalFeasibility:
    """Check declared physical limits without executing requests or judging an SLO."""
    checks: list[PhysicalCheck] = []

    def add(path: str, rule: str, status: PhysicalStatus, reason: str,
            unit: str = 'count', required: Metric | None = None,
            limit: Metric | None = None) -> None:
        checks.append(PhysicalCheck(input_path=path, scope=config.root.id, rule=rule,
                                    status=status, reason=reason, unit=unit,
                                    required=required, limit=limit))

    def finish() -> PhysicalFeasibility:
        rows = tuple(checks)
        return PhysicalFeasibility(checks=rows, status=physical_status(rows))

    missing = _missing_component_ids(config, components)
    if missing:
        add('system.root.components', 'component_resolution', 'unsupported',
            _missing_components_message(config, missing))
        return finish()
    from rk.engine.economics_runtime import prepare
    try:
        resolved, components = prepare(config, components)
        config = resolved.system
    except ValueError as exc:
        add('system.economics', 'economics_resolution', 'unsupported', str(exc))
        return finish()
    instances = _flatten(config, components)
    try:
        _check_fidelity_is_implemented(config.fidelity, 'system.fidelity')
    except UnimplementedFidelity as exc:
        add('system.fidelity', 'implemented_fidelity', 'unsupported', str(exc))
        return finish()
    for instance in instances:
        try:
            if instance.override is not None:
                _check_fidelity_is_implemented(instance.fidelity, instance.component_id,
                                              compute_stub_ok=True)
            _outcomes([instance])
        except UnimplementedFidelity as exc:
            add('system.root.components', 'implemented_fidelity', 'unsupported', str(exc))
    if checks:
        return finish()
    try:
        f0_memory.reject_on_package_slots(_slotted_roles(config, components))
    except f0_memory.OnPackageMemorySlotted as exc:
        add('system.root.components', 'on_package_memory', 'invalid', str(exc))
        return finish()
    accelerators = _running_accelerators(instances)
    if len(accelerators) != 1:
        add('system.root.components', 'accelerator_model', 'unsupported',
            'The roofline requires exactly one participating accelerator type.')
        return finish()
    count = sum(i.count for i in accelerators)
    devices, replicas, problem = _replica_shape(plan, count)
    add('execution_plan.parallelism', 'replica_devices',
        'invalid' if problem else 'valid', problem or 'Declared devices can host a replica.',
        required=Metric(value=devices, unit='count', badge=Calibration.ESTIMATED,
                        contributors=('input.composition',)),
        limit=Metric(value=count, unit='count', badge=Calibration.ESTIMATED,
                        contributors=('input.composition',)))
    if problem:
        return finish()
    # Inspect the same peak map as dispatch; do not catch generic EngineError.
    if plan.precision.compute not in _peaks(accelerators[0]):
        add('execution_plan.precision.compute', 'precision_support', 'unsupported',
            f'{accelerators[0].component_id} declares no {plan.precision.compute} peak.')
        return finish()
    _accelerator(accelerators[0], plan.precision)
    runtime = _runtime_choice(instances, config)
    try:
        _agentic_host(config, plan, workload, instances, runtime)
    except EngineError as exc:
        add('workload.agentic_profile', 'agentic_execution', 'unsupported', str(exc))
        return finish()
    view = _memory_view(instances, _outcomes(instances),
                        frozenset(i.component_id for i in accelerators))
    try:
        _spill_inputs(view, instances, workload, plan, replicas)
    except EngineError as exc:
        add('system.root', 'kv_tier_placement', 'unsupported', str(exc))
        return finish()
    if not view.tiers:
        add('system.fidelity.memory', 'memory_capacity', 'unknown',
            'No participating M0 capacity; weight and KV fit are unknown.', 'bytes')
    else:
        fit = f0_memory.capacity_fit(workload.model, view.tiers,
                                    workload.analytical_lengths.prompt_tokens,
                                    plan.batching.max_batch, plan.precision, replicas=replicas)
        capacity_params = [
            (i.component_id, name, i.descriptor.params[name])
            for i in instances for name in ('hbm_capacity', 'capacity_gb')
            if i.component_id in fit.tiers and name in i.descriptor.params
        ]
        capacity_badge = combine([p.provenance for _, _, p in capacity_params])
        limit = Metric(value=fit.available_bytes, unit='bytes', badge=capacity_badge,
                       contributors=tuple(f'{cid}.{name}' for cid, name, _ in capacity_params))
        def memory_required(value: float) -> Metric:
            return Metric(value=value, unit='bytes', badge=Calibration.ESTIMATED,
                          contributors=('workload.model', 'execution_plan.precision',
                                        'model.m0.capacity'))
        add('workload.model.total_params', 'weight_residency',
            'invalid' if fit.weight_bytes > fit.available_bytes else 'valid',
            'All total_params weights must reside in declared pooled memory at every runtime.',
            'bytes', memory_required(fit.weight_bytes), limit)
        fatal = not fit.fits and _capacity_shortfall_is_fatal(fit, runtime.level)
        add('execution_plan.batching.max_batch', 'kv_ceiling',
            'invalid' if fatal else 'valid',
            ('R1 admission enforces KV allocation; this is a worst-case occupancy ceiling.'
             if runtime.level is RuntimeFidelity.R1 else
             'R0 requires weights plus KV at max_batch and declared prompt length to fit.'),
            'bytes', memory_required(fit.required_bytes), limit)

    if runtime.level is RuntimeFidelity.R1:
        # Admission can manage max-batch overcommit, but cannot allocate even one block
        # from an empty/sub-block pool. Use exactly _serve's pool and block arithmetic;
        # HBM+CXL may supply KV; DDR cannot. Weights must still fit HBM.
        pool_bytes = _kv_pool_bytes_per_replica(view, workload, plan, replicas)
        block_bytes = kv_bytes(workload.model, 1, 1, plan.precision.kv_cache) * plan.kv.block_size
        weights_bytes = f0_memory.weight_residency_bytes(workload.model, plan.precision.compute)
        pool_limit = None
        pool_status: PhysicalStatus = 'unknown'
        if pool_bytes is not None:
            capacity_sources = [
                (f'{i.component_id}.{name}', _sourced(i, name))
                for i in instances
                for name in ('hbm_capacity' if i.component_id in view.on_package_ids
                             else 'capacity_gb',)
                if i.component_id in (*view.on_package_ids, *view.cxl_ids)
            ]
            pool_limit = Metric(
                value=pool_bytes + weights_bytes, unit='bytes',
                badge=combine([p.provenance for _, p in capacity_sources]),
                contributors=tuple(name for name, _ in capacity_sources),
            )
            pool_status = 'invalid' if int(pool_bytes // block_bytes) < 1 else 'valid'
        add('execution_plan.kv.block_size', 'kv_minimum_pool', pool_status,
            ('R1 requires HBM-resident weights and HBM/CXL room for at '
             'least one KV block per replica. Ordinary '
             'max-batch overcommit remains admission-controlled.' if pool_limit is not None
             else 'No participating on-package capacity; R1 KV pool size is unknown.'),
            'bytes', Metric(
                value=weights_bytes + block_bytes, unit='bytes', badge=Calibration.ESTIMATED,
                contributors=('workload.model', 'execution_plan.precision',
                              'execution_plan.kv.block_size', 'model.m0.capacity'),
            ), pool_limit)

        if workload.agentic_profile is not None:
            growth_status: PhysicalStatus = 'unknown'
            growth_reason = ('Actual episode stream lengths are unavailable to preflight; '
                             'the analytical point is not a bound. Execution checks every '
                             'selected episode before drawing turns.')
            if workload.generator is not None:
                try:
                    f1_agentic.check_episode_capacity(
                        workload.agentic_profile, workload.generator.prompt_tokens,
                        workload.generator.output_tokens, episode_index=0,
                        block_size_tokens=plan.kv.block_size,
                        kv_pool_blocks=(None if pool_bytes is None
                                        else int(pool_bytes // block_bytes)),
                        max_tokens_in_flight=plan.batching.max_tokens_in_flight)
                except f1_serving.ServingError as exc:
                    growth_status, growth_reason = 'invalid', str(exc)
                else:
                    growth_status = 'unknown' if pool_bytes is None else 'valid'
                    growth_reason = (
                        'Declared generator lengths at turns_max fit the per-turn token '
                        'budget and KV pool.' if pool_bytes is not None else
                        'Declared generator lengths at turns_max fit the token budget, '
                        'but the KV pool capacity is unknown.')
            add('workload.agentic_profile', 'agentic_context_growth', growth_status, growth_reason)

    economics = _economics(config, instances)
    component = _component_power_kw(instances, [])
    overhead_sources = [
        (i.component_id, i.descriptor.params['power_overhead_fraction'])
        for i in instances if i.descriptor.kind is ComponentKind.HIERARCHY_SCOPE
        and 'power_overhead_fraction' in i.descriptor.params
    ]
    overhead_badges = [overhead_sources[-1][1].provenance] if overhead_sources else []
    overhead_contributors = (
        (f'{overhead_sources[-1][0]}.power_overhead_fraction',) if overhead_sources else ()
    )
    if economics.overhead_source is not None and economics.overhead_contributor is not None:
        overhead_badges = [economics.overhead_source.provenance]
        overhead_contributors = (economics.overhead_contributor,)
    draw = Metric(value=f0_power.total_power_kw(component.value, economics.overhead_fraction),
                  unit='kW', badge=combine([component.badge, f0_power.POWER_MODEL_BADGE,
                                           *overhead_badges]),
                  contributors=(*component.contributors, *overhead_contributors,
                                'model.power.tdp_ceiling'))
    # Unknown chassis overhead can only add to this independently badged subtotal.
    without_overhead = Metric(value=component.value, unit='kW',
        badge=combine([component.badge, f0_power.POWER_MODEL_BADGE]),
        contributors=(*component.contributors, 'model.power.tdp_ceiling'))
    incomplete = any('tdp' not in i.descriptor.params for i in instances)
    incomplete |= 'power_overhead_fraction' in economics.undeclared
    if config.economics is not None and config.economics.dvfs is not None:
        law = config.economics.dvfs
        point = f0_power.operating_point(1, 0, 0, law)
        chip_count = sum(i.count for i in accelerators)
        nonaccelerator_w = sum(i.descriptor.params['tdp'].value * i.count
            for i in instances if i not in accelerators and 'tdp' in i.descriptor.params)
        law_sources = [getattr(law, name) for name in type(law).model_fields
                       if getattr(law, name) is not None]
        without_overhead = Metric(value=(chip_count * point.watts + nonaccelerator_w) / 1000,
            unit='kW', badge=combine([without_overhead.badge,
                                      *(s.provenance for s in law_sources)]),
            contributors=(*without_overhead.contributors, 'model.p7.dvfs.design_bound'))
        draw = Metric(value=f0_power.total_power_kw(
            (chip_count * point.watts + nonaccelerator_w) / 1000, economics.overhead_fraction),
            unit='kW', badge=combine([draw.badge, *(s.provenance for s in law_sources)]),
            contributors=(*draw.contributors, 'model.p7.dvfs.design_bound'))
        if not point.converged:
            add('system.economics.dvfs.power_cap_w', 'dvfs_cap', 'unknown',
                'The declared cap cannot be reached within the declared frequency range.')
    elif config.economics is not None and config.economics.power_model == 'channel_energy':
        draw = draw.model_copy(update={'badge': Calibration.STUB})
        without_overhead = without_overhead.model_copy(update={'badge': Calibration.STUB})
        incomplete = True
    for name, param, rule in (('max_kw', 'power_envelope_kw', 'power_envelope'),
                              ('cooling_cap_kw', 'cooling_cap_kw', 'cooling_envelope')):
        path, power_limit = _declared_power_limit(config, instances, name, param)
        state: PhysicalStatus = 'unknown'
        reason = 'Missing or STUB limit, or incomplete draw inputs; no proven envelope pass.'
        if power_limit is not None and power_limit.badge is not Calibration.STUB:
            if (without_overhead.badge is not Calibration.STUB
                    and without_overhead.value > power_limit.value):
                state = 'invalid'
                reason = ('Declared design draw already exceeds the envelope without chassis '
                          'overhead, which can only add draw; no clamp applied.')
            elif draw.badge is not Calibration.STUB and draw.value > power_limit.value:
                state = 'invalid'
                reason = 'Declared TDP-sum design draw exceeds the envelope; no clamp applied.'
            elif draw.badge is not Calibration.STUB and not incomplete:
                state = 'valid'
                reason = 'Declared TDP-sum design draw is within this envelope.'
        add(path, rule, state, reason, 'kW', draw, power_limit)
    return finish()


def evaluate_candidate(
    config: SystemConfig,
    plan: ExecutionPlan,
    workload: WorkloadSpec,
    seed: int,
    *,
    components: Mapping[str, ComponentDescriptor],
    requests: RequestStream | None = None,
) -> CandidateOutcome:
    """Retain rejected inputs and checks, never fabricate metrics or catch engine bugs."""
    physical = preflight(config, plan, workload, components=components)
    result = None
    if physical.status not in ('invalid', 'unsupported'):
        result = run(config, plan, workload, seed, components=components, requests=requests)
    return CandidateOutcome(system=config, plan=plan, workload=workload, seed=seed,
                            engine_version=ENGINE_VERSION, feasibility=physical,
                            status=physical.status, result=result)


def _runtime_timeline(
    first: f1_serving.Replication,
    replicas: int,
    instances: list[_Instance],
    memory_view: _MemoryView,
    latency_badge: Calibration,
    latency_contributors: tuple[str, ...],
) -> RuntimeTimeline:
    """Expose existing replication-zero samples without simulating or resampling (0046)."""
    raw = first.timeline
    capacities = [
        (i.component_id, _sourced(i, "hbm_capacity"))
        for i in instances if i.component_id in memory_view.on_package_ids
    ]
    contributors = (
        *latency_contributors,
        *(f"{cid}.hbm_capacity" for cid, _ in capacities),
        "model.runtime.r1.timeline",
    )
    badges = [latency_badge, Calibration.ESTIMATED, *(p.provenance for _, p in capacities)]
    if raw.kv_pool_blocks is None:
        badges.append(Calibration.STUB)
        contributors = (*contributors, "model.runtime.r1.unbounded_kv_pool")
    badge = combine(badges)

    def metric(value: float, unit: str) -> Metric:
        return Metric(value=value, unit=unit, badge=badge, contributors=contributors)

    occupancy = raw.kv_occupancy
    return RuntimeTimeline(
        replication_seed=first.seed,
        replica_count=replicas,
        origin_s=metric(0.0, "s"),
        sample_interval_s=metric(raw.sample_interval_s, "s"),
        makespan_s=metric(first.makespan_s, "s"),
        kv_pool_blocks=(None if raw.kv_pool_blocks is None else
                        metric(raw.kv_pool_blocks, "blocks")),
        samples=tuple(
            RuntimeTimelineSample(
                at_s=metric(index * raw.sample_interval_s, "s"),
                gpu_busy_ratio=metric(busy, "ratio"),
                kv_blocks_in_use=metric(blocks, "blocks"),
                kv_occupancy_ratio=(None if occupancy is None else
                                    metric(occupancy[index], "ratio")),
            )
            for index, (busy, blocks) in enumerate(
                zip(raw.gpu_busy, raw.kv_blocks_in_use, strict=True)
            )
        ),
    )


def run(config: SystemConfig, plan: ExecutionPlan, workload: WorkloadSpec, seed: int, *,
        components: Mapping[str, ComponentDescriptor],
        requests: RequestStream | None = None) -> RunResult:
    """Resolve canonical economics before running; preserve both input identities."""
    from rk.engine.economics_runtime import (
        episode_cost_normalization,
        explicit_cost,
        headline,
        prepare,
        repair_overhead,
    )
    from rk.schema.economics_artifact import EconomicsArtifact

    try:
        resolved, library = prepare(config, components)
    except ValueError as exc:
        raise EngineError(str(exc)) from exc
    try:
        core = _simulate_core(resolved.system, plan, workload, seed,
                              components=library, requests=requests)
    except ValueError as exc:
        raise EngineError(str(exc)) from exc
    result = repair_overhead(core.result, resolved.system)
    assert resolved.system.economics is not None
    if resolved.system.economics.power_model != 'tdp_ceiling':
        assert result.power_diagnostic is not None
        from rk.schema.channels import Available
        draw = result.power_diagnostic.rack_it_w
        result = result.model_copy(update={
            'power_kw_per_rack': (draw.metric.model_copy(update={
                'value': draw.metric.value / 1000, 'unit': 'kW'})
                if isinstance(draw, Available) else headline(draw, 'kW')),
            'energy_j_per_token': headline(result.power_diagnostic.energy_j_per_token, 'J/tok'),
        })
        view = _economics(resolved.system, _flatten(resolved.system, library))
        if resolved.system.economics.basis == 'legacy_rental':
            tco_value = f0_cost.tco_usd_per_year(view.capex_usd, view.amortization_years,
                result.power_kw_per_rack.value, view.usd_per_kwh, view.utilization)
            result = result.model_copy(update={'tco_usd_per_year': Metric(
                value=tco_value, unit='USD/yr', badge=Calibration.STUB if view.undeclared else
                combine([result.power_kw_per_rack.badge, *view.badges]),
                contributors=(*view.contributors, *result.power_kw_per_rack.contributors))})
    diagnostic = explicit_cost(result, resolved.system, power_complete=(
        result.power_diagnostic is not None
        and result.power_diagnostic.identity.coverage == 'complete'))
    updates: dict[str, Any] = {'economics_artifact': EconomicsArtifact(
        migration=resolved.migration, legacy_hash=resolved.legacy_hash,
        resolved_hash=resolved.resolved_hash, resolved_system=resolved.system,
        library_snapshot=resolved.library), 'cost_diagnostic': diagnostic}
    if diagnostic is not None and diagnostic.basis != 'legacy_rental':
        updates['usd_per_mtok'] = headline(diagnostic.usd_per_mtok, 'USD/Mtok')
        updates['tco_usd_per_year'] = headline(diagnostic.tco_usd_per_year, 'USD/yr')
    if core.episodes:
        if diagnostic is None or result.episodes is None:
            raise EngineError('episode normalization requires a computed cost '
                              'diagnostic and counts')
        count = result.episodes.episodes_completed
        updates['episode_cost_normalization'] = episode_cost_normalization(
            core.episodes, diagnostic.basis, count.badge, count.contributors,
            price_window_id=diagnostic.window_id)
    return result.model_copy(update=updates)


def _spill_inputs(view: _MemoryView, instances: list[_Instance], workload: WorkloadSpec,
                  plan: ExecutionPlan, replicas: int) -> tuple[float | None, float]:
    cxl_ids = {i.component_id for i in instances if i.descriptor.role is ComponentRole.CXL_POOL}
    cxl = [t for t in view.tiers if t.name in cxl_ids]
    if not cxl:
        return None, 0.0
    if len(cxl) > 1:
        raise EngineError('P7 supports one CXL tier; multiple latency choices are unsupported')
    tier = next(i for i in instances if i.component_id == cxl[0].name)
    if not any(name in tier.descriptor.params for name in ('latency_ns', 'added_latency_ns')):
        raise EngineError(f'{tier.component_id}: P7 KV spill requires explicit '
                          'latency_ns or added_latency_ns; missing timing is not zero')
    hbm = sum(t.capacity_bytes for t in view.tiers if t.name in view.on_package_ids) / replicas
    weights = f0_memory.weight_residency_bytes(workload.model, plan.precision.compute)
    if hbm < weights:
        raise EngineError('P7 KV spill requires weights resident in HBM; offload is unsupported')
    return hbm - weights, cxl[0].latency_s


def _p7_power(config: SystemConfig, plan: ExecutionPlan, workload: WorkloadSpec,
              instances: list[_Instance], accelerator: Accelerator, aggregate: _Aggregate,
              served: _Served | None, hbm_kv_bytes: float | None, spill_latency_s: float,
              legacy_power: _Derived, badge: Calibration, contributors: tuple[str, ...],
              network: _NetworkView) -> tuple[PowerDiagnostic, AvailableQuantity, Metric | None]:
    from rk.engine.f0.channels import available
    from rk.schema.channels import PowerIdentity, Unavailable
    from rk.schema.power import PowerDiagnostic

    economics = config.economics
    assert economics is not None
    law = economics.dvfs
    active_chips = _running_accelerators(instances)
    chips = sum(i.count for i in active_chips)
    repeats = workload.analytical_lengths.output_tokens
    duration = ((aggregate.ttft_ms + repeats * aggregate.tpot_ms) / 1000 if served is None else
                sum(r.makespan_s for r in served.result.replications))
    tokens = (aggregate.replicas * aggregate.batch * repeats if served is None else
              sum(r.completed_output_tokens for r in served.result.replications)
              * aggregate.replicas)
    window = 'r0_legacy_cycle' if served is None else 'r1_pooled_replication_makespans'
    converged = True
    dynamic_j, static_j = 0.0, legacy_power.value * 1000 * duration
    per_chip_w = None
    busy_w = 0.0
    subtotal_w = 0.0
    subtotal_badges: list[Calibration] = []
    subtotal_contributors: tuple[str, ...] = ()
    omissions = []
    if law is not None:
        if served is None:
            coefficients = _collective_coefficients(network, workload, plan)
            cost = replace(iteration_cost(workload.model, accelerator, plan.precision,
                tp=plan.parallelism.tp, collective_fixed_s=coefficients.fixed_s,
                collective_s_per_message_token=coefficients.s_per_message_token),
                dvfs=law, hbm_kv_bytes=hbm_kv_bytes, spill_latency_s=spill_latency_s)
            batch = aggregate.batch
            context = workload.analytical_lengths.prompt_tokens * batch
            p = cost.power_point(cost.prefill_counts(context,
                batch * workload.analytical_lengths.prompt_tokens ** 2), context)
            d = cost.power_point(cost.decode_counts(batch, context), batch, cost.spill_s(context))
            assert p is not None and d is not None
            dynamic_j = p.dynamic_j + repeats * d.dynamic_j
            busy_w = max(p.watts, d.watts if repeats else 0) * chips
            converged = p.converged and d.converged
        else:
            dynamic_j = sum(r.dynamic_j_per_chip for r in served.result.replications)
            busy_w = max(r.max_busy_w_per_chip for r in served.result.replications) * chips
            converged = all(r.power_converged for r in served.result.replications)
        # Keep known additive evidence separate from the unavailable total. A STUB
        # operating point (or a failed solve) cannot establish accelerator draw.
        if converged and duration > 0 and tokens > 0 and badge is not Calibration.STUB:
            subtotal_w = busy_w
            subtotal_badges.append(badge)
            subtotal_contributors = contributors
        static_j = law.idle_w.value * duration
        per_chip_w = (dynamic_j + static_j) / duration if duration else 0
        dynamic_j *= chips
        static_j *= chips
        for instance in instances:
            if instance in active_chips:
                continue
            tdp = instance.descriptor.params.get('tdp')
            if tdp is not None:
                static_j += tdp.value * instance.count * duration
                busy_w += tdp.value * instance.count
                if tdp.provenance is not Calibration.STUB:
                    subtotal_w += tdp.value * instance.count
                    subtotal_badges.append(tdp.provenance)
                    subtotal_contributors += (f'{instance.component_id}.tdp',)
                badge = combine([badge, tdp.provenance])
                contributors += (f'{instance.component_id}.tdp',)
            elif instance.descriptor.kind not in {ComponentKind.HIERARCHY_SCOPE,
                                                   ComponentKind.RUNTIME}:
                omissions.append(f'{instance.component_id}: missing nonaccelerator draw')
        overhead = economics.overhead_fraction
        if economics.legacy and overhead is None:
            entries = [r.quantity for r in economics.legacy.values
                       if r.name == 'power_overhead_fraction']
            overhead = entries[-1] if entries else None
        if overhead is None or overhead.provenance is Calibration.STUB:
            omissions.append('missing/STUB chassis overhead')
        elif subtotal_badges:
            subtotal_w *= 1 + overhead.value
            subtotal_badges.append(overhead.provenance)
            subtotal_contributors += ('economics.overhead_fraction',)
        if overhead is not None:
            static_j *= 1 + overhead.value
            dynamic_j *= 1 + overhead.value
            busy_w *= 1 + overhead.value
            badge = combine([badge, overhead.provenance])
            contributors += ('economics.overhead_fraction',)
    else:
        badge = combine([badge, legacy_power.badge])
        contributors = (*contributors, *legacy_power.contributors)
        # The legacy ceiling has no dynamic/static decomposition.
        omissions.append('TDP ceiling is not an integrated operating-power model')
    if economics.power_model == 'channel_energy':
        omissions.append('partial representative-rank channel ledger has no rack total')
    if not converged:
        omissions.append('DVFS cap unattainable or bounded solver did not converge')
    if duration <= 0 or tokens <= 0:
        omissions.append('no completed output/window')
    if badge is Calibration.STUB:
        omissions.append('STUB model contributor')
    contributors = tuple(dict.fromkeys((*contributors, 'model.p7.power')))
    total_j = dynamic_j + static_j
    watts = total_j / duration if duration else 0
    pue = economics.owned.pue if economics.owned else None

    def q(value: float, unit: str) -> AvailableQuantity:
        return (Unavailable(unit=unit, reason='; '.join(omissions), contributors=contributors)
                if omissions else available(value, unit, contributors, badge))

    facility = (Unavailable(unit='W', reason='IT draw or PUE unavailable')
                if omissions or pue is None or pue.provenance is Calibration.STUB else
                available(watts * pue.value, 'W', (*contributors, 'economics.owned.pue'),
                          combine([badge, pue.provenance])))
    busy_subtotal = (Metric(value=subtotal_w, unit='W',
        badge=combine([Calibration.ESTIMATED, *subtotal_badges]),
        contributors=tuple(dict.fromkeys((*subtotal_contributors, 'model.p7.power'))))
        if subtotal_badges else None)
    return PowerDiagnostic(identity=PowerIdentity(model=economics.power_model,
        formula_version='p7-v1', coverage='partial' if omissions else 'complete',
        contributors=contributors), window_id=window, per_chip_w=(
            Unavailable(unit='W', reason='no utilization per-chip draw')
            if per_chip_w is None else q(per_chip_w, 'W')),
        rack_it_w=q(watts, 'W'), facility_w=facility, dynamic_j=q(dynamic_j, 'J'),
        static_j=q(static_j, 'J'), duration_s=available(duration, 's', contributors, badge),
        delivered_tokens=available(tokens, 'token', contributors, badge),
        energy_j_per_token=q(total_j / tokens if tokens else 0, 'J/tok'),
        converged=converged, omissions=tuple(omissions)), q(busy_w, 'W'), busy_subtotal
