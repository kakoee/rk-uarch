"""Read-only Stage 2 prose/premise checks; not an analytic corpus or review verdict."""

import sys
from fractions import Fraction
from pathlib import Path

REQUIRED = {
    "B-F2": ("`head/embed` (16 bytes)", "`layers/kv` (32 bytes)",
             "base/slower clock", "MEMORY_ONLY_EMBEDDING"),
    "B-F4": ("v1 native-checklist “Stage scope and refusal”",
             "v1 native-checklist “Stage progression”", "v1 native-checklist lines 68–70",
             "v1 README lines 165–169", "T/G3b", "no unconditional runner prerequisite"),
    "B-F7": ("**DMA replacement:**", "**Clock replacement:**", "H-DMA:", "H-CLOCK:",
             "in_flight_end = in_flight_start + issued_bytes - completed_bytes",
             "T/k <= T' <= T", "a tie alone is insufficient"),
}


def check_text(text: str, finding: str) -> None:
    for phrase in REQUIRED[finding]:
        assert phrase in text, (finding, phrase)


def check_existing_fixture(root: Path) -> None:
    # Explicit private-export sources; no ambient import paths or producer calls.
    sys.path[:0] = [str(root), str(root / "src"), str(root / "contract")]
    import rkuarch.engines.analytic.core as core
    import validation.strategies as strategies
    from validation.analytic_checks import COUNTS, FIELDS

    assert Path(core.__file__).resolve().is_relative_to(root)
    assert Path(strategies.FIXTURE).resolve().is_relative_to(root)
    per_phase = {}
    for job in strategies.jobs(strategies.fixed_bundle("aggregate")):
        result = core.run_analytic(job)
        assert tuple(getattr(result.counts, f) for f in FIELDS) == COUNTS[job.point.query.phase]
        rows = [(op.id, op.counts.matrix_ops, op.counts.vector_ops,
                 op.counts.memory_read_bytes + op.counts.memory_write_bytes)
                for op in result.per_op]
        memory_only = {name: b for name, m, v, b in rows if m == v == 0 and b > 0}
        assert memory_only == {"head/embed": 16, "layers/kv": 32}
        per_phase[job.point.query.phase] = memory_only
    assert set(per_phase) == {"decode", "prefill"}
    print("Existing fixture memory-only operators:", per_phase)


def check_math() -> None:
    # Independently worked counterexamples, arbitrary consistent units; no chip facts.
    k = 2
    compute, memory = Fraction(8), Fraction(6)
    assert max(compute / k, memory) < max(compute, memory)
    # Memory only dominates after the speed-up: T'=6 != T=8.
    assert max(compute, memory) / max(compute / k, memory) == Fraction(4, 3)
    # A tie at the faster clock gives exactly k, not a strict smaller speedup.
    assert max(compute, 4) / max(compute / k, 4) == k
    # Base-clock memory dominance gives equality at both clocks.
    assert max(compute, 10) == max(compute / k, 10)
    # A positive fixed memory-only term breaks exact whole-query reciprocal scaling.
    assert (compute / k + 16 + 32) * k != compute + 16 + 32
    # Transfer balance and allocation accounting cannot be replaced by operand reads.
    assert 32 + 128 - 64 == 96
    dma_in, repeated_operand_reads, produced_output = 16, 32, 8
    assert dma_in != repeated_operand_reads + produced_output
    # Finite population: [0,4) and [2,6) over [1,5) have overlaps 3+3.
    assert (4 - 1) + (5 - 2) == 6
    print("Clock, DMA/reuse and finite-window counterexamples passed")


if __name__ == "__main__":
    source = Path(sys.argv[1]).resolve()
    text = Path(sys.argv[2]).read_text()
    for finding in REQUIRED:
        check_text(text, finding)
    check_math()
    check_existing_fixture(source)
    print("B-F2/B-F4/B-F7 proposal checks passed; no acceptance implied")
