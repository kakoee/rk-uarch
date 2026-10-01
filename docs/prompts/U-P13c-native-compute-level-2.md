# U-P13c · U7 · Lane A — Native compute level 2: SRAM bank conflicts and DMA interleave

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, src/rkuarch/mapping/README.md, build-spec §2.4
and §2.8, ADR U0011, U0012.

TASK: compute at level 2, the last piece the composite rule needs for C2.

1. Compute level 2: SRAM bank conflicts, from the mapping's buffer placement (core,
   offset_bytes, bank), and DMA/compute interleaving at cycle timestamps, still O(1–10)
   events per tensor job wherever no conflict occurs. sram_bank_conflict_stall_ratio and
   dma_compute_overlap_ratio are filled at this level.
2. Shared SRAM: engine support is deferred until after U8. A spec with a shared_sram is run
   with that field listed as unrepresented, fidelity_detail.shared_sram = "unrepresented",
   and the table warns.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at compute level 2.
2. Conflicts bite: a placement that puts two concurrently read operands in one bank is
   slower than one that spreads them, at equal bytes; at compute level 1 the two are
   identical, and the test asserts both halves.
3. A spec with a shared_sram reports it as unrepresented and is refused C2, with the reason.
4. Determinism: byte-identical at 1 and N workers; sanitizer build clean.

GUARDRAILS: No threads yet. Keep compute level 1: it is the fast mode. Do not model the
shared SRAM in this prompt.

ADR: none here; U-P13d's U0013 records this level.
```
