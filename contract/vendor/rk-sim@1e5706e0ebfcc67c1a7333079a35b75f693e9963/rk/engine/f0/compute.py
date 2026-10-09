"""Roofline prefill/decode model. Sprint 1 (P1).

C0: one transformer forward pass on one accelerator, as `max(compute_time, memory_time)`
per phase. The formulas are ADR 0003 §7.2's and are not re-derived here; this module is
where they live, and `f1/` asks this module what an iteration costs rather than
re-deriving FLOPs of its own (CLAUDE.md invariant 8).

The crossover is returned EXPLICITLY rather than left to be inferred: every phase carries
`machine_balance_flop_per_byte`, its own achieved `arithmetic_intensity_flop_per_byte`,
and a `bound_by` reading 'compute' or 'memory'. ADR 0003 §7.2 asks for the regime to be
inspectable, because "which side of the roofline was I on" is the first question anyone
asks of a number that looks wrong.

**Precision is an INPUT as of ADR 0015 §1**, and every function that sizes a byte or picks
a peak takes it explicitly. It used to be fp16 throughout via two named constants; those
are `bytes_per_element(fmt)` now.

ADR 0003 §7.3 ("Precision is fixed at fp16 = 2 bytes") and build-spec §1.3's deferred list
BOTH STILL SAY OTHERWISE AS OF P3B, and neither is amended — ADR 0015 §4 lists them as
downstream of this change and they are a human's to edit (CLAUDE.md's propose-and-stop
rule). If you are reading either of those and this module, THIS MODULE IS THE CURRENT
BEHAVIOUR. Nothing here defaults to
fp16 — a `Precision` defaults, in the schema, where a reader can see it, and a plan asking
for fp8 and silently receiving fp16 numbers would still be an authoritative-looking answer
to a different question (build-spec §2.4).

Units live in names (CLAUDE.md invariant 7) and in every signature below. Conversion out
of datasheet units happens in the named functions at the top and nowhere else.

NOT modelled here, deliberately: collectives and any tp>1 communication cost (N0, P3 —
the orchestrator divides by tp and warns), pipeline bubbles, expert routing and imbalance
(build-spec §2.3.5), sparsity (§1.3), and kernel selection.

**ACTIVATION MEMORY TRAFFIC IS NOT COUNTED AT ALL, and it is the largest known gap in
`bytes_moved`.** `prefill_bytes` and `decode_bytes` are weights + KV and nothing else
(ADR 0003 §7.2). S2 finding F1 measured the uncounted floor at **>=171.8 GB against 161.5
GB counted** on the demo prefill — the omission is larger than everything included, and it
is not merely a shaded number: `bytes_moved` sets `arithmetic_intensity_flop_per_byte`, so
it can flip a regime label. Recorded, with its reason for being out of P3b's scope, in
ADR 0015 §7.3 — it is a memory-model change and not precision wiring. Making the byte
count precision-aware did NOT make it complete.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

from rk.engine.f0.power import OperatingPoint, operating_point
from rk.schema.execution import Precision, PrecisionFormat
from rk.schema.power import DvfsParameters
from rk.schema.workloads import ModelSpec

__all__ = [
    "BYTES_PER_ELEMENT",
    "CAUSAL_ATTENTION_FACTOR",
    "INTEGER_FORMATS",
    "Accelerator",
    "BoundBy",
    "IterationCost",
    "PhaseRoofline",
    "UnsupportedPrecision",
    "bytes_per_element",
    "decode_flops",
    "decode_bytes",
    "decode_roofline",
    "iteration_cost",
    "kv_bytes",
    "prefill_flops",
    "prefill_bytes",
    "prefill_roofline",
    "tb_per_s_to_byte_per_s",
    "tflops_to_flop_per_s",
    "tops_to_op_per_s",
    "weight_bytes",
]

# ADR 0015 §1. This replaces `BYTES_PER_WEIGHT_FP16` and `BYTES_PER_KV_ELEM_FP16`, which
# were both the literal 2 and both fp16 by ADR 0003 §7.3 — now amended.
#
# **TOTAL OVER `PrecisionFormat`, and deliberately so.** Every member has an entry and
# `bytes_per_element` has no default branch, so a format added to the enum later fails
# loudly at the lookup instead of silently inheriting some neighbour's width. That
# totality is asserted in tests/unit/test_precision.py rather than left to care.
#
# **`tf32` is 4, and it is the one a reader will get wrong.** TF32 is a 19-BIT FORMAT
# (1 sign + 8 exponent + 10 mantissa) held in a 32-bit slot: its saving is in the
# multiplier array, not in memory, so it stores exactly as wide as fp32. (ADR 0015 §1 and
# P3b's first draft both said "19-bit mantissa"; the mantissa is 10 bits and the whole
# format is 19. The byte count is unaffected — ADR 0015 §7.2.)
#
# fp4 and int4 are 0.5, PACKED — two elements to a byte. That is why the return type is
# `float` and not `int`, and it is not an accident of the annotation.
BYTES_PER_ELEMENT: Final[Mapping[PrecisionFormat, float]] = {
    PrecisionFormat.FP32: 4.0,
    PrecisionFormat.TF32: 4.0,
    PrecisionFormat.BF16: 2.0,
    PrecisionFormat.FP16: 2.0,
    PrecisionFormat.FP8: 1.0,
    PrecisionFormat.INT8: 1.0,
    PrecisionFormat.FP4: 0.5,
    PrecisionFormat.INT4: 0.5,
}

# Which formats a datasheet quotes in TOPS rather than TFLOPS, and therefore which named
# converter `Accelerator.peak_op_per_s` reaches for. Both conversions are x1e12, and they
# are still two functions because they are two unit pairs (CLAUDE.md invariant 7) — the
# library param names carry the same split: `int8_tops`, `int4_tops`, everything else
# `*_tflops`.
INTEGER_FORMATS: Final[frozenset[PrecisionFormat]] = frozenset(
    {PrecisionFormat.INT8, PrecisionFormat.INT4}
)


class UnsupportedPrecision(ValueError):
    """The plan asked for a precision this accelerator does not declare a peak for.

    Its own exception type so the orchestrator can re-raise it as an `EngineError` from
    one implementation, the way `memory.OnPackageMemorySlotted` already does.

    **It is a refusal and not a fall-back.** Resolving fp8 to "the nearest supported
    format" would be build-spec §2.4's forbidden answer-to-a-different-question, and it is
    not a warning either, because without a peak there is no compute roof and therefore no
    number to warn about. ADR 0015 §2 — which also notes that refusing is the stricter
    form of the "Requested vs Resolved" surface, since it puts no number on screen at all.
    """


def bytes_per_element(fmt: PrecisionFormat) -> float:
    """Storage width of one element in `fmt`, bytes. See `BYTES_PER_ELEMENT`.

    A bare subscript, with no `.get(..., default)` and no `else` branch: a `PrecisionFormat`
    member with no entry must raise here rather than be given some plausible width.
    """
    return BYTES_PER_ELEMENT[fmt]

# ADR 0007, option B, accepted 2026-09-02. Prefill attention is charged at HALF the full
# S² because every model this simulator targets is decoder-only and causally masked: a
# token attends only to its predecessors, so roughly half the score matrix is never
# computed. FlashAttention's own FLOP accounting does exactly this — "with causal masking,
# this number is divided by 2" — and its kernel skips those blocks outright.
#
# THE REJECTED OPTION, recorded here so the next reader meets a decision and not an
# omission: option A was to keep the full S², which ADR 0003 §7.2 originally implied by
# saying nothing either way. It is the conservative choice (it overestimates prefill), but
# it diverges ~12% at long context from GenZ and llm-analysis, which P3 cross-checks
# against — an investigation whose answer is already written down. Set this to 1.0 to get
# option A back; nothing else needs to change. Full reasoning and sources:
# docs/decisions/0007-causal-masking-in-the-prefill-attention-term.md
#
# Decode is deliberately NOT affected: its attention term is linear in context because one
# new token attends over all S past keys. There is no triangle there to halve.
CAUSAL_ATTENTION_FACTOR: Final[float] = 0.5

BoundBy = Literal["compute", "memory"]


# --------------------------------------------------------------------------------------
# Unit conversion — named functions, per CLAUDE.md invariant 7
# --------------------------------------------------------------------------------------


def tflops_to_flop_per_s(tflops: float) -> float:
    """TFLOP/s -> FLOP/s. Decimal, not binary: 1 TFLOP/s = 1e12 FLOP/s.

    The parameter was `fp16_tflops` until ADR 0015 §1 made precision an input; the
    conversion never was fp16-specific.
    """
    return tflops * 1e12


def tops_to_op_per_s(tops: float) -> float:
    """TOP/s -> OP/s. Decimal: 1 TOP/s = 1e12 OP/s.

    The integer twin of `tflops_to_flop_per_s`, and a separate function because TOPS and
    TFLOPS are separate units that happen to share a prefix (CLAUDE.md invariant 7). An
    int8 GEMM's cost is counted in the same `flops` field the roofline divides — the
    operations are integer operations, and `INTEGER_FORMATS` records which formats those
    are.
    """
    return tops * 1e12


def tb_per_s_to_byte_per_s(hbm_bw_tb_per_s: float) -> float:
    """TB/s -> byte/s. Decimal, as every memory datasheet quotes it: 1 TB/s = 1e12 B/s."""
    return hbm_bw_tb_per_s * 1e12


# --------------------------------------------------------------------------------------
# What the roofline needs from the hardware
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Accelerator:
    """The accelerator numbers the C0 roofline reads, already unwrapped.

    Plain floats on purpose: `SourcedValue` is how a number *enters the system* (the
    loader's job), and by the time the orchestrator has checked the units and recorded the
    contributors, what the formula needs is arithmetic. The badges do not travel in here —
    they travel alongside, in the orchestrator, and are what the Metric carries out.

    peak_tera_op_per_s_by_format
        One peak per `PrecisionFormat` THE COMPONENT DECLARES — not per member of the
        enum. A part that declares no fp8 peak has no fp8 entry, and asking for one is
        `UnsupportedPrecision` rather than a fall-back (ADR 0015 §2). The A100 is exactly
        that case and it is not hypothetical: Hopper introduced FP8, Ampere has none, and
        neither part has FP4.

        TFLOPS for the float formats, TOPS for `INTEGER_FORMATS`; `peak_op_per_s` picks
        the converter. **DENSE, every one of them.** Sparsity is not modelled (build-spec
        §1.3), so a with-sparsity figure silently doubles the compute roof and halves every
        compute-bound answer. The H100 datasheet prints ONLY the with-sparsity figure on
        its starred rows and dense must be halved out of it; the A100 prints
        `dense | with-sparsity` as a pair and the left cell is already dense. Getting that
        backwards on either sheet is ADR 0006 §2 and ADR 0013 §2 — and ADR 0015 §7.7
        records an outside tool that made exactly this error on exactly these two
        documents, 2x on all five H100 rows.

    hbm_bw_tb_per_s
        TB/s, the device's own memory bandwidth. The DATASHEET figure, unscaled.

    compute_efficiency
        Ratio in (0, 1] multiplying the COMPUTE roof and nothing else. This is
        `ScalarEfficiency.value` — the weakest number in the repo (build-spec §2.3.4) —
        under its historical meaning, unchanged.

        IT IS A COMPUTE-BOUND EFFICIENCY, NOT A BLENDED ONE, and that distinction is
        load-bearing. For a compute-bound phase the model's achieved-vs-peak IS this
        constant exactly; for a memory-bound phase a low achieved-vs-peak already falls out
        of the memory roof with nothing configured. Fit this against a decode or
        whole-workload utilisation measurement and the memory bound is counted twice — the
        model then predicts badly for a reason that looks like calibration.
        docs/decisions/kernel-efficiency.md §3.

    memory_efficiency
        Ratio in (0, 1] multiplying the MEMORY roof and nothing else — the second half of
        `SplitEfficiency`, kernel-efficiency.md §5 option C, taken in ADR 0015 §3.

        **A `ScalarEfficiency` component passes 1.0 here, and that 1.0 is an OMISSION, not
        a measurement.** It is what `ScalarEfficiency` has always meant — "compute-bound
        only, memory roof unscaled" — and reading it as a blend now would silently change
        every shipped entry's answer. But it does claim that real HBM achieves 100% of
        spec bandwidth, which nothing does, so the orchestrator emits a run-time warning
        naming it on any run that passes 1.0 from a `ScalarEfficiency`. Every library entry
        is still `ScalarEfficiency` after P3b, correctly — there is nothing to source yet
        — so that warning fires on every run in the repo, which is the point of it
        (kernel-efficiency.md §10.4).

        §8's ban on fitting applies here exactly as to `compute_efficiency`. And note the
        direction, so the temptation is visible: rk-sim's decode is already SLOWER than
        GenZ (+9.38%), so a physically meaningful value below 1 WIDENS that gap rather than
        closing it (0.90 takes it to +21.53%). Closing it would need a value above 1, which
        is not a thing. This term is justified by physics, not by an oracle delta's sign.
    """

    peak_tera_op_per_s_by_format: Mapping[PrecisionFormat, float]
    hbm_bw_tb_per_s: float
    compute_efficiency: float
    memory_efficiency: float

    def __post_init__(self) -> None:
        # A defensive copy, so a caller mutating the mapping it passed cannot change what
        # a frozen dataclass reports. The frozen-ness is otherwise only skin deep.
        object.__setattr__(
            self, "peak_tera_op_per_s_by_format", dict(self.peak_tera_op_per_s_by_format)
        )
        if not self.peak_tera_op_per_s_by_format:
            raise ValueError(
                "an accelerator declaring no peak for any precision has no compute roof "
                "at all. Declare at least one of the per-precision peak params."
            )
        for fmt, peak in self.peak_tera_op_per_s_by_format.items():
            if peak <= 0:
                raise ValueError(f"{fmt.value} peak must be positive, got {peak!r}")
        if self.hbm_bw_tb_per_s <= 0:
            raise ValueError(f"hbm_bw_tb_per_s must be positive, got {self.hbm_bw_tb_per_s!r}")
        for name, ratio in (
            ("compute_efficiency", self.compute_efficiency),
            ("memory_efficiency", self.memory_efficiency),
        ):
            if not 0 < ratio <= 1:
                raise ValueError(
                    f"{name} must lie in (0, 1], got {ratio!r}. It is a realized-vs-peak "
                    f"ratio; above 1 claims more than the silicon has and 0 makes its roof "
                    f"infinite."
                )

    @property
    def declared_formats(self) -> tuple[PrecisionFormat, ...]:
        """Every precision this part declares a peak for, in `PrecisionFormat` order.

        Enum order rather than sorted-by-name, so a refusal message lists formats widest
        first and reads the way the datasheet's own table does.
        """
        return tuple(
            fmt for fmt in PrecisionFormat if fmt in self.peak_tera_op_per_s_by_format
        )

    def peak_op_per_s(self, fmt: PrecisionFormat) -> float:
        """Dense peak for `fmt`, OP/s. What the silicon can do at that precision.

        Raises `UnsupportedPrecision` naming what this part DOES declare. See that class:
        refusing is the decision, not an implementation convenience.
        """
        tera = self.peak_tera_op_per_s_by_format.get(fmt)
        if tera is None:
            declared = ", ".join(f.value for f in self.declared_formats)
            raise UnsupportedPrecision(
                f"this accelerator declares no peak for {fmt.value!r}. It declares: "
                f"{declared}. The compute roof has no value without a peak, so there is "
                f"no number to report and nothing to warn about — and resolving to the "
                f"nearest supported format would answer a different question than the one "
                f"asked (build-spec §2.4, ADR 0015 §2). Ask for a precision this part "
                f"declares, or run it on a part that has one."
            )
        return tops_to_op_per_s(tera) if fmt in INTEGER_FORMATS else tflops_to_flop_per_s(tera)

    def effective_op_per_s(self, fmt: PrecisionFormat) -> float:
        """Peak x compute_efficiency, OP/s. What a real stack gets (build-spec §2.3.4)."""
        return self.peak_op_per_s(fmt) * self.compute_efficiency

    @property
    def hbm_byte_per_s(self) -> float:
        """Datasheet memory bandwidth, byte/s. Unscaled — see `effective_byte_per_s`."""
        return tb_per_s_to_byte_per_s(self.hbm_bw_tb_per_s)

    @property
    def effective_byte_per_s(self) -> float:
        """Bandwidth x memory_efficiency, byte/s. What the memory roof actually divides by.

        At `memory_efficiency == 1.0` this IS `hbm_byte_per_s`, bit for bit, which is why
        every `ScalarEfficiency` entry in the library produces the answers it always did.
        """
        return self.hbm_byte_per_s * self.memory_efficiency

    def machine_balance_flop_per_byte(self, fmt: PrecisionFormat) -> float:
        """The crossover at `fmt`: effective OP/s per effective byte/s (ADR 0003 §7.2).

        A phase whose arithmetic intensity is above this is compute-bound; below it,
        memory-bound. **Both efficiencies are inside it deliberately** — the crossover a
        real stack experiences sits somewhere other than the datasheet's, and it moves with
        whichever roof was derated. It also moves with `fmt`: a narrower format buys
        compute throughput without buying bandwidth, so it pushes the crossover up.
        """
        return self.effective_op_per_s(fmt) / self.effective_byte_per_s


# --------------------------------------------------------------------------------------
# The answer for one phase
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PhaseRoofline:
    """One phase's cost, with the regime that produced it.

    Everything derived is a property, so the stored fields cannot drift out of agreement
    with each other: `time_s` IS `max(compute_time_s, memory_time_s)`, never a third
    number that was supposed to equal it.
    """

    phase: Literal["prefill", "decode"]
    flops: float
    bytes_moved: float
    compute_time_s: float
    memory_time_s: float
    machine_balance_flop_per_byte: float
    extra_delay_s: float = 0.0

    @property
    def time_s(self) -> float:
        """The roofline answer: seconds, whichever roof binds."""
        return max(self.compute_time_s, self.memory_time_s) + self.extra_delay_s

    @property
    def time_ms(self) -> float:
        """The same answer in milliseconds — the unit every latency metric reports."""
        return self.time_s * 1e3

    @property
    def arithmetic_intensity_flop_per_byte(self) -> float:
        """Achieved intensity. Compare against `machine_balance_flop_per_byte`."""
        return self.flops / self.bytes_moved

    @property
    def bound_by(self) -> BoundBy:
        """'compute' or 'memory' — which roof produced `time_s`.

        Derived from the TIME comparison, not from the intensity one, because `time_s` is
        the number being reported and this label has to describe it. A phase whose reported
        time came off the memory roof must never be labelled compute-bound, whatever the
        intensity says.

        The two views agree everywhere except within about one ULP of the exact crossover.
        `flops/(peak·eff) >= bytes/bw` and `flops/bytes >= (peak·eff)/bw` are one
        inequality in algebra and two different roundings in IEEE-754, so arbitrarily close
        to the crossover they can disagree by a last-place bit —
        tests/unit/test_roofline_edges.py pins a reachable case. Where they disagree the
        regime is genuinely indeterminate, and this field answers the half of the question
        that has an observable answer.

        Ties report 'compute'.
        """
        return "compute" if self.compute_time_s >= self.memory_time_s else "memory"

    @property
    def compute_utilization(self) -> float:
        """Fraction of the phase the compute units are busy. In [0, 1] by construction."""
        return self.compute_time_s / self.time_s

    @property
    def memory_utilization(self) -> float:
        """Fraction of the phase the memory system is busy. In [0, 1] by construction."""
        return self.memory_time_s / self.time_s


# --------------------------------------------------------------------------------------
# The formulas — ADR 0003 §7.1 and §7.2, transcribed, not re-derived
# --------------------------------------------------------------------------------------


def weight_bytes(model: ModelSpec, compute_format: PrecisionFormat) -> float:
    """Bytes of weights read per forward pass. active_params, never total.

    MoE is active-vs-total and nothing more (build-spec §2.3.5): only the routed experts
    execute, so only they are read. `total_params` is a capacity question, not a
    bandwidth one.

    **Sized at `precision.compute`, because that field covers weights too.** A stack
    running fp8 GEMMs holds fp8 weights. W8A16 — quantized weights with higher-precision
    compute — is NOT modelled; ADR 0015 §1 records it as the first thing `Precision` would
    need to grow, and it is a third field there rather than a redesign here.
    """
    return float(model.active_params) * bytes_per_element(compute_format)


def kv_bytes(
    model: ModelSpec,
    seq_len_tokens: int,
    batch: int,
    kv_format: PrecisionFormat,
) -> float:
    """KV-cache bytes at context length `seq_len_tokens` for `batch` sequences.

    ADR 0003 §7.1: 2 · n_layers · kv_heads · head_dim · S · B · bytes_per_element(kv).
    The leading 2 is K and V; `kv_heads` (not `n_heads`) is what makes this GQA-correct,
    and `head_dim = d_model // n_heads` is exact because ModelSpec validates divisibility.

    **`kv_format` is `precision.kv_cache`, and it moves independently of the compute
    format.** That separation is the whole of ADR 0015's item 3: item 1 alone moves only
    the compute roof, which decode is not bound by. This is the one term that moves the
    memory roof's byte count, and it sizes the M0 capacity gate too — so fp8 KV roughly
    halves what the cache costs to hold as well as what it costs to read.
    """
    return (
        2.0
        * model.n_layers
        * model.kv_heads
        * model.head_dim
        * seq_len_tokens
        * batch
        * bytes_per_element(kv_format)
    )


def prefill_flops(model: ModelSpec, seq_len_tokens: int, batch: int) -> float:
    """FLOPs to prefill `batch` prompts of `seq_len_tokens` tokens.

    2·P_active·S·B  +  4·n_layers·d_model·S²·B·CAUSAL_ATTENTION_FACTOR

    The second term is attention, quadratic in context, and is the term a long-context
    prefill lives or dies by. ADR 0003 §7.2 fixed everything here except the causal
    factor, on which it was silent; ADR 0007 settled that at 0.5 — see the constant.
    """
    dense = 2.0 * model.active_params * seq_len_tokens * batch
    attention = (
        4.0
        * model.n_layers
        * model.d_model
        * seq_len_tokens**2
        * batch
        * CAUSAL_ATTENTION_FACTOR
    )
    return dense + attention


def prefill_bytes(
    model: ModelSpec,
    seq_len_tokens: int,
    batch: int,
    precision: Precision,
) -> float:
    """Bytes moved during prefill: weights read + KV written (ADR 0003 §7.2).

    Weights at `precision.compute`, KV at `precision.kv_cache`. **Activations are not
    counted, and this is weights + KV and nothing else** — see the module docstring and
    ADR 0015 §7.3. Precision-aware is not the same as complete.
    """
    return weight_bytes(model, precision.compute) + kv_bytes(
        model, seq_len_tokens, batch, precision.kv_cache
    )


def decode_flops(model: ModelSpec, seq_len_tokens: int, batch: int) -> float:
    """FLOPs for ONE decode step at context length `seq_len_tokens` (ADR 0003 §7.2).

    2·P_active·B  +  4·n_layers·d_model·S·B — linear in context, because one new token
    attends over S existing ones.

    CAUSAL_ATTENTION_FACTOR does NOT appear here, and its absence is deliberate: with a
    single query position there is no upper triangle to skip. ADR 0007 §"Impact".
    """
    dense = 2.0 * model.active_params * batch
    attention = 4.0 * model.n_layers * model.d_model * seq_len_tokens * batch
    return dense + attention


def decode_bytes(
    model: ModelSpec,
    seq_len_tokens: int,
    batch: int,
    precision: Precision,
) -> float:
    """Bytes moved during one decode step: weights read + KV read (ADR 0003 §7.2).

    Weights at `precision.compute`, KV at `precision.kv_cache`. Activations are not
    counted here either — module docstring, ADR 0015 §7.3.
    """
    return weight_bytes(model, precision.compute) + kv_bytes(
        model, seq_len_tokens, batch, precision.kv_cache
    )


def _roofline(
    phase: Literal["prefill", "decode"],
    flops: float,
    bytes_moved: float,
    accelerator: Accelerator,
    compute_format: PrecisionFormat,
) -> PhaseRoofline:
    """t = max(flops / (peak·compute_eff), bytes / (bw·memory_eff)). Seconds.

    The two roofs take DIFFERENT efficiencies as of ADR 0015 §3, and that asymmetry is the
    point: one scalar could not reach the memory-bound phase at all (kernel-efficiency.md
    §10.2 measured decode bit-identical across a 10x sweep of the compute term). A
    `ScalarEfficiency` component arrives here with `memory_efficiency == 1.0`, so its
    memory roof is unscaled and its answers are exactly the ones it always gave.
    """
    return PhaseRoofline(
        phase=phase,
        flops=flops,
        bytes_moved=bytes_moved,
        compute_time_s=flops / accelerator.effective_op_per_s(compute_format),
        memory_time_s=bytes_moved / accelerator.effective_byte_per_s,
        machine_balance_flop_per_byte=accelerator.machine_balance_flop_per_byte(
            compute_format
        ),
    )


def prefill_roofline(
    model: ModelSpec,
    accelerator: Accelerator,
    seq_len_tokens: int,
    batch: int,
    precision: Precision,
) -> PhaseRoofline:
    """Prefill cost for one forward pass on ONE accelerator.

    model            architecture; active_params drives compute, kv_heads drives KV bytes
    accelerator      per-precision peaks, TB/s and the two efficiency ratios
    seq_len_tokens   prompt length S, tokens
    batch            number of sequences B in the batch
    precision        `compute` picks the peak AND the weight width; `kv_cache` the KV width

    Returns a PhaseRoofline whose `time_ms` is the whole batch's prefill time in ms and
    whose `bound_by` says which roof produced it. tp is NOT applied here: dividing by
    tensor parallelism is the orchestrator's job, because it owes a warning with it
    (ADR 0003 §7.4).

    Raises `UnsupportedPrecision` if the part declares no peak for `precision.compute`.
    `precision.kv_cache` needs no peak and can never raise here — it sizes bytes only.
    """
    _check_shape(seq_len_tokens, batch)
    return _roofline(
        "prefill",
        prefill_flops(model, seq_len_tokens, batch),
        prefill_bytes(model, seq_len_tokens, batch, precision),
        accelerator,
        precision.compute,
    )


def decode_roofline(
    model: ModelSpec,
    accelerator: Accelerator,
    seq_len_tokens: int,
    batch: int,
    precision: Precision,
) -> PhaseRoofline:
    """Cost of ONE decode step on ONE accelerator — i.e. time per output token.

    model            architecture; active_params drives compute, kv_heads drives KV bytes
    accelerator      per-precision peaks, TB/s and the two efficiency ratios
    seq_len_tokens   context length S already in the KV cache, tokens
    batch            number of sequences B decoding together
    precision        `compute` picks the peak AND the weight width; `kv_cache` the KV width

    Returns a PhaseRoofline whose `time_ms` is TPOT in ms for the batch. Throughput is
    `batch / time_s` and is the orchestrator's to assemble, along with the replica count.

    Raises `UnsupportedPrecision` if the part declares no peak for `precision.compute`.
    """
    _check_shape(seq_len_tokens, batch)
    return _roofline(
        "decode",
        decode_flops(model, seq_len_tokens, batch),
        decode_bytes(model, seq_len_tokens, batch, precision),
        accelerator,
        precision.compute,
    )


def _check_shape(seq_len_tokens: int, batch: int) -> None:
    if seq_len_tokens < 1:
        raise ValueError(f"seq_len_tokens must be at least 1, got {seq_len_tokens!r}")
    if batch < 1:
        raise ValueError(f"batch must be at least 1, got {batch!r}")


# --------------------------------------------------------------------------------------
# The same formulas, rearranged for a loop — P5
# --------------------------------------------------------------------------------------
#
# WHY THIS EXISTS, in one paragraph, because "a dataclass of coefficients" looks like
# premature optimization until you know what it buys.
#
# The R1 DES prices one iteration per event, thousands of times per run. CLAUDE.md
# invariant 8 forbids it from re-deriving FLOPs, and the naive way to obey that is to call
# `decode_roofline` inside the loop. P5 forbids THAT too, and the fact that makes both
# possible at once is a property of the formulas above: decode cost depends on the batch's
# context lengths ONLY through their sum. Writing T = sum(S_i) and Q = sum(S_i^2) over the
# requests in the batch,
#
#     decode_flops  = 2*P_active*B          +  (4*n_layers*d_model) * T
#     decode_bytes  = weight_bytes          +  k * T
#     prefill_flops = 2*P_active*T          +  (4*n_layers*d_model*CAUSAL) * Q
#     prefill_bytes = weight_bytes          +  k * T
#            with k = 2*n_layers*kv_heads*head_dim*bytes_per_element(kv_cache)
#
# THE COLLECTIVE TERM IS AFFINE IN THE SAME WAY, AND IT HAS TO BE. P5 specified two
# collective SCALARS — one per phase, priced once and charged to every iteration. Measured
# on the demo node that is wrong by 58x on the case the DES actually has: the orchestrator
# prices the prefill all-reduce at `max_batch` x `prompt_tokens` (669 ms on 8xH100 over
# NVLink at batch 64), and a DES prefill iteration usually admits ONE request, whose real
# collective is 11.6 ms. Charging the batch-64 constant to it more than halves the node's
# modelled throughput, and the error is invisible because every input to it is correct.
#
# The fix is the one P5 itself anticipated — "a later sprint that adds a term makes the
# struct GAIN A FIELD, not get replaced" — arriving now instead of later, and it costs no
# net field. `links.ring_allreduce_time_s` is `steps*alpha + steps/ranks * bytes/beta` and
# `allreduce_bytes` is linear in (tokens x batch), so the whole collective is exactly
#
#     collective(m) = collective_fixed_s + collective_s_per_message_token * m
#
# where m is the iteration's MESSAGE TOKENS: the total prompt tokens T for a prefill, and
# the batch size B for a decode step (one new token per sequence). One affine function,
# two scalars, both phases — so the struct still carries ten floats and the seam is
# unchanged. ADR 0018 §2.
#
# Every coefficient there is a scalar known before the first event fires. Three things
# fall out of lifting them into a struct:
#
#   INVARIANT 8 BECOMES STRUCTURAL. `f1/` never sees `n_layers`, `d_model` or
#   `active_params`, so it CANNOT re-derive a FLOP count. The invariant stops depending on
#   anyone's restraint and starts depending on what is reachable.
#
#   tp AND THE COLLECTIVE TERM GET ONE HOME. `orchestrator._dispatch_and_aggregate` used
#   to write `prefill.time_s / parallelism.tp + collectives.total_prefill_s` inline, and
#   the DES needs exactly that arithmetic every iteration. Folded in here it is written
#   once. The orchestrator supplies the two collective numbers from its own `_collectives`;
#   this module stays ignorant of the network, as it must (see the module docstring).
#
#   IT IS THE SEAM. A future native-code DES receives ten floats and evaluates them
#   locally — no per-event FFI back into Python and no second copy of the roofline in
#   another language.
#
# THE LIMIT: the closed form is exact only while cost is linear in (batch, total_context).
# A later sprint that adds a term makes this struct GAIN A FIELD; it does not get replaced.
# tests/unit/test_iteration_cost.py asserts the equivalence over a grid of
# (batch, context, precision, tp) with `==` and not `approx` — see that file for why exact
# equality is the right assertion and what it would mean for it to need a tolerance.


@dataclass(frozen=True)
class IterationCounts:
    """Unsharded work at the live R1 batch; None is omitted, never zero.

    Internal arithmetic only. Export through ChannelCount/Metric with coverage.
    """

    matrix_ops: float
    memory_read_bytes: float
    memory_write_bytes: float | None
    vector_ops: None = None

    @property
    def modelled_memory_bytes(self) -> float:
        return self.memory_read_bytes + (self.memory_write_bytes or 0.0)


@dataclass(frozen=True)
class IterationCost:
    """One iteration's cost as ten scalars, for a loop that may not call back into f0.

    Built by `iteration_cost()`; never assembled by hand, because the coefficients are the
    roofline's and belong to this module. Everything is per REPLICA and per iteration.

    dense_flop_per_seq
        2*P_active. Multiplies the batch size in decode, and the token TOTAL in prefill —
        the same coefficient in both, which is what `2*P_active*B` and `2*P_active*S*B`
        have in common once S*B is written as T.
    attention_flop_per_context_token
        4*n_layers*d_model. Decode's attention term, linear in context because one new
        token attends over all S past keys.
    prefill_attention_flop_per_token_squared
        the same 4*n_layers*d_model times `CAUSAL_ATTENTION_FACTOR`. Prefill's attention
        term is quadratic, so it multiplies Q = sum(S_i^2) rather than T. The causal factor
        lives here and NOT in the decode coefficient, exactly as in `prefill_flops` and
        `decode_flops` — there is no triangle to halve when there is one query position
        (ADR 0007).
    weight_bytes
        active_params at `precision.compute`. Read once per iteration whatever the batch is,
        which is the whole reason decode is memory-bound at small batch.
    kv_byte_per_context_token
        k = 2*n_layers*kv_heads*head_dim*bytes_per_element(kv_cache) — the KV bytes ONE
        token of context costs. **This is `kv_bytes(model, 1, 1, kv_format)` and not a
        literal 2 times anything** (ADR 0015 §1): `f1/serving.py` sizes its KV blocks off
        this field, so an fp8 KV cache halves the byte cost of a block and therefore
        doubles how many blocks fit in the same pool.
    flop_per_s / byte_per_s
        the accelerator's two EFFECTIVE rates, already scaled by their own efficiency
        terms. Two separate numbers because ADR 0015 §3 split the efficiency scalar in two
        and the roofs no longer share a derate.
    tp
        tensor parallelism. Divides the roofline time, per ADR 0003 §7.4.
    collective_fixed_s
        the alpha term: what one iteration's all-reduces cost with a zero-length message.
        Paid once per iteration whatever the batch, because the latency of 2*n_layers
        separate collectives does not depend on how much they carry.
    collective_s_per_message_token
        the beta term, per MESSAGE TOKEN — the total prompt tokens T for a prefill, the
        batch size B for a decode step (one new token per sequence). See the block above
        for why this is a coefficient and not a constant, and what the constant cost.

    Both come from the orchestrator's `_collective_coefficients`, and both are 0.0 at
    network STUB, where the run separately warns that the number is an upper bound.
    """

    dense_flop_per_seq: float
    attention_flop_per_context_token: float
    prefill_attention_flop_per_token_squared: float
    weight_bytes: float
    kv_byte_per_context_token: float
    flop_per_s: float
    byte_per_s: float
    tp: int
    collective_fixed_s: float
    collective_s_per_message_token: float
    dvfs: DvfsParameters | None = None
    hbm_kv_bytes: float | None = None
    spill_latency_s: float = 0.0

    def __post_init__(self) -> None:
        if self.flop_per_s <= 0:
            raise ValueError(f"flop_per_s must be positive, got {self.flop_per_s!r}")
        if self.byte_per_s <= 0:
            raise ValueError(f"byte_per_s must be positive, got {self.byte_per_s!r}")
        if self.tp < 1:
            raise ValueError(f"tp must be at least 1, got {self.tp!r}")
        for name, seconds in (
            ("collective_fixed_s", self.collective_fixed_s),
            ("collective_s_per_message_token", self.collective_s_per_message_token),
        ):
            if seconds < 0:
                raise ValueError(f"{name} must not be negative, got {seconds!r}")

    def collective_s(self, message_tokens: int) -> float:
        """What this iteration's tp collectives cost. Seconds.

        `message_tokens` is the width of the activation being reduced, in tokens: sum of
        the prompt lengths for a prefill, and the batch size for a decode step. One
        function for both phases, because `links.ring_allreduce_time_s` does not care
        which phase produced the message.
        """
        return self.collective_fixed_s + self.collective_s_per_message_token * message_tokens

    # -- decode ------------------------------------------------------------------------

    def decode_flops(self, batch: int, total_context_tokens: int) -> float:
        """FLOPs for one decode step over a batch holding `total_context_tokens` in total.

        `total_context_tokens` is sum(S_i) across the batch, NOT S x B: the whole point of
        this shape is that a continuous-batching scheduler holds requests at different
        context lengths and the roofline signature cannot express that.
        """
        return (
            self.dense_flop_per_seq * batch
            + self.attention_flop_per_context_token * total_context_tokens
        )

    def decode_bytes(self, total_context_tokens: int) -> float:
        """Bytes moved by one decode step: weights read once + the whole batch's KV read."""
        return self.weight_bytes + self.kv_byte_per_context_token * total_context_tokens

    def decode_s(self, batch: int, total_context_tokens: int) -> float:
        """Seconds for one decode step: max of the two roofs, over tp, plus the collective.

        The collective's message is ONE token per sequence, so its width is `batch` —
        which is why a decode step's collective barely grows with the batch and is
        dominated by the per-collective latency.
        """
        counts = self.decode_counts(batch, total_context_tokens)
        return self._time_s(
            counts.matrix_ops, counts.modelled_memory_bytes,
            self.collective_s(batch) + self.spill_s(total_context_tokens),
        )

    def spill_s(self, total_context_tokens: int) -> float:
        """One declared latency penalty weighted by HBM-first KV spill fraction."""
        needed = self.kv_byte_per_context_token * total_context_tokens
        if self.hbm_kv_bytes is None or needed <= self.hbm_kv_bytes or needed <= 0:
            return 0.0
        return (needed - self.hbm_kv_bytes) / needed * self.spill_latency_s

    def power_point(self, counts: IterationCounts, message_tokens: int,
                    extra_s: float = 0.0) -> OperatingPoint | None:
        if self.dvfs is None:
            return None
        return operating_point(counts.matrix_ops / self.flop_per_s / self.tp,
            counts.modelled_memory_bytes / self.byte_per_s / self.tp,
            self.collective_s(message_tokens) + extra_s, self.dvfs)

    # -- prefill -----------------------------------------------------------------------

    def prefill_flops(
        self, total_prompt_tokens: int, sum_of_squared_prompt_tokens: int
    ) -> float:
        """FLOPs to prefill a group of prompts.

        total_prompt_tokens              T = sum(S_i)
        sum_of_squared_prompt_tokens     Q = sum(S_i^2), which the quadratic attention term
                                         needs and which T alone cannot recover

        There is no `batch` argument, and its absence is the formula and not an oversight:
        `prefill_flops` has no term in B that is not already a term in T.
        """
        return (
            self.dense_flop_per_seq * total_prompt_tokens
            + self.prefill_attention_flop_per_token_squared * sum_of_squared_prompt_tokens
        )

    def prefill_bytes(self, total_prompt_tokens: int) -> float:
        """Bytes moved by a prefill: weights read once + the KV the prompts write."""
        return self.weight_bytes + self.kv_byte_per_context_token * total_prompt_tokens

    def prefill_s(
        self, total_prompt_tokens: int, sum_of_squared_prompt_tokens: int
    ) -> float:
        """Seconds to prefill a group of prompts. Same shape as `decode_s`.

        The collective's message covers every prompt position, so its width is
        `total_prompt_tokens` — which is why a prefill's collective is bandwidth-dominated
        where a decode step's is latency-dominated, and why charging one constant to both
        sizes was wrong by 58x on the demo node.
        """
        counts = self.prefill_counts(total_prompt_tokens, sum_of_squared_prompt_tokens)
        return self._time_s(
            counts.matrix_ops, counts.modelled_memory_bytes,
            self.collective_s(total_prompt_tokens),
        )

    def prefill_counts(self, total_prompt_tokens: int,
                       sum_of_squared_prompt_tokens: int) -> IterationCounts:
        """Shared ledger evaluated at live T and Q; prefill writes KV."""
        return IterationCounts(
            self.prefill_flops(total_prompt_tokens, sum_of_squared_prompt_tokens),
            self.weight_bytes, self.kv_byte_per_context_token * total_prompt_tokens,
        )

    def decode_counts(self, batch: int, total_context_tokens: int) -> IterationCounts:
        """Shared ledger evaluated at live batch/context; decode writes omitted."""
        return IterationCounts(
            self.decode_flops(batch, total_context_tokens),
            self.decode_bytes(total_context_tokens), None,
        )

    # -- the one place the roofline is evaluated ----------------------------------------

    def _time_s(self, flops: float, bytes_moved: float, collective_s: float) -> float:
        """max(compute roof, memory roof) / tp + collective. Seconds.

        The division and the addition are in THIS order and not folded, because that is
        the order `_dispatch_and_aggregate` evaluates them in and the equivalence test
        asserts bit equality. Changing the order here moves every committed golden.
        """
        if self.dvfs is not None:
            return operating_point(flops / self.flop_per_s / self.tp,
                bytes_moved / self.byte_per_s / self.tp, collective_s, self.dvfs).duration_s
        return max(flops / self.flop_per_s, bytes_moved / self.byte_per_s) / self.tp + (
            collective_s
        )


def iteration_cost(
    model: ModelSpec,
    accelerator: Accelerator,
    precision: Precision,
    *,
    tp: int = 1,
    collective_fixed_s: float = 0.0,
    collective_s_per_message_token: float = 0.0,
) -> IterationCost:
    """Lift the roofline's coefficients out of `model` and `accelerator`, once per run.

    model                    architecture. `active_params` drives compute and weight bytes,
                             `kv_heads`/`head_dim` the KV coefficient — the same reads
                             `prefill_flops`, `decode_flops` and `kv_bytes` make.
    accelerator              per-precision peaks, bandwidth and the two efficiency ratios
    precision                `compute` picks the peak AND the weight width; `kv_cache` the
                             KV width, which is what sizes a DES block (ADR 0015 §1)
    tp                       tensor parallelism; divides the roofline time (ADR 0003 §7.4)
    collective_fixed_s       the collectives' alpha term, seconds per iteration
    collective_s_per_message_token
                             their beta term, seconds per token of reduced activation.
                             Both come from the orchestrator's `_collective_coefficients`;
                             this module does not know the network exists.

    Raises `UnsupportedPrecision` if the part declares no peak for `precision.compute` —
    at BUILD time, before any event fires, which is the same refusal `_accelerator` makes
    and for the same reason (ADR 0015 §2).
    """
    if tp < 1:
        raise ValueError(f"tp must be at least 1, got {tp!r}")
    return IterationCost(
        dense_flop_per_seq=2.0 * model.active_params,
        attention_flop_per_context_token=4.0 * model.n_layers * model.d_model,
        prefill_attention_flop_per_token_squared=(
            4.0 * model.n_layers * model.d_model * CAUSAL_ATTENTION_FACTOR
        ),
        weight_bytes=weight_bytes(model, precision.compute),
        # ONE token of context, ONE sequence — `kv_bytes` itself, never a literal 2.
        kv_byte_per_context_token=kv_bytes(model, 1, 1, precision.kv_cache),
        flop_per_s=accelerator.effective_op_per_s(precision.compute),
        byte_per_s=accelerator.effective_byte_per_s,
        tp=tp,
        collective_fixed_s=collective_fixed_s,
        collective_s_per_message_token=collective_s_per_message_token,
    )
