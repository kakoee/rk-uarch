# rk-uarch — a microarchitecture-level simulator of one chip, feeding rk-sim

## What this is
A harness around simulation engines (analytic, a pinned published fork, and our own native
C++ engine) that produces characterization tables rk-sim reads as the C2 compute answer.
The product is the honesty: every row carries its fidelity, its evidence, and the
stipulations it is conditional on. Detail is not accuracy.

## Commands
- test: `uv run pytest -q` · fast: `make test-fast` (excludes nightly, silicon, native)
- typecheck: `uv run mypy src contract` · lint: `uv run ruff check`
- native: `make native` · `make native-test` (Linux box / engine container)
- table: `uv run uarch table <spec> --model <name> --precision <fmt> --engine analytic|fork|native`
- report: `uv run uarch report <table>` · study: `uv run uarch study <studyspec>`
- vendor rk-sim: `make vendor-rk SHA=<sha> RK=<path>` (humans only)

## Invariants (violating these = stop and ask)
1. Never import `rk`. rk-sim is read only through contract/vendor/, and only in tests.
2. Every hardware number is a SourcedValue with kind claim|stipulation. A claim needs a source
   (or is provenance: stub with source: null). A stipulation needs a rationale and is allowed
   only in hw/designs/ (design_status: proposed). Never invent a claim.
3. Units live in names (_s, _ps, _bytes, _hz, _ratio, _w, _pj). Cycles never leave engines/
   or native/. next_edge() is the only time↔cycle conversion.
4. A table is a pure function of (request, uarch version). Same inputs → same bytes, at any
   worker or thread count. New randomness takes the request seed.
5. A row is one chip's shard, one iteration, all layers, without inter-chip collectives.
6. A C2 result faster than its own U-C0 roofline is a bug, not a finding.
7. Verified is not validated. L0–L2 evidence never lifts a model above stub. Nothing may
   raise a badge. A proposed design is never above estimated.
8. Error is "unknown", never zero. Never fill ci95 from a deterministic run.
9. C2 only when every shared resource is at level 2 or 1+ts and sync is exact (or approx(Q)
   covered by a measured curve). Otherwise report the lower composite.
10. Files under validation/L3_silicon/*/predictions/ are committed before any result exists
    and are never edited. check_ordering enforces it.
11. tests/golden/expected/ changes only via `make golden-update` + a docs/decisions/U*.md.
12. third_party/ changes only as numbered patches; licences only from the allow-list.

## Don't
- Don't add a workload IR or an ONNX import path. Workloads = rk-sim ModelSpec + ModelShape.
- Don't add mapping search, SIMD, GPU, MPI, optimistic sync, a simulation compiler, or a web UI.
- Don't tune any model parameter to pass an L2 or L3 comparison. Record the gap.
- Don't add dependencies beyond pyproject.toml / native/CMakeLists.txt without asking.
- Don't read rk-sim's docs/vision/ unless a prompt names a section; never edit rk-sim, except
  in U-P19 and U-P20, which run inside rk-sim under its own rules.

## Vocabulary
kind: claim | stipulation · design_status: proposed | reference
per-subsystem levels 0 | 1 | 1+ts | 2 (3 = reference only) → composite C0/C1/C2 for rk-sim
calibration: measured > spec_derived > estimated > stub (rk-sim's), worst of claims
L0 invariants · L0m metamorphic · L1 limits · L2 differential · L3 same-class silicon · L4 target
Never call this codebase or its engine "DES" (that is rk-sim's R1), "F2" or "C2".

## Workflow
- Prompts live in docs/prompts/. One task per session. Write the acceptance tests first.
- Lanes (CODEOWNERS is authoritative): A = src/rkuarch/{hw,workload,mapping,engines,table},
  native/, third_party/, containers/, cli.py. B = hw/, src/rkuarch/{provenance,report,study},
  validation/, measure/, scripts/, .github/workflows/.
  Both humans: contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.
- Agents propose and stop on contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.
